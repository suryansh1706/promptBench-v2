"""
Master Statistical Testing Engine for Calibrated Audit.
Executes paired permutation tests, bootstrap CIs, and Benjamini-Hochberg FDR adjustments.
"""

from typing import List, Dict, Tuple, Optional, Any
from .permutation import PermutationTest
from .bootstrap import BootstrapCI
from .corrections import MultipleTestingCorrection
from .non_parametric import NonParametricTests
from ..core.types import PairwiseComparison, HypothesisTestResult
from ..core.config import StatisticalConfig
import logging
from statistics import NormalDist


class StatisticalTestingEngine:
    """
    Coordinates rigorous hypothesis testing across all demographic comparisons in an audit.
    """

    def __init__(self, config: Optional[StatisticalConfig] = None):
        self.config = config or StatisticalConfig()
        self.perm_test = PermutationTest(resamples=self.config.permutation_resamples)
        self.bootstrap = BootstrapCI(
            resamples=self.config.bootstrap_resamples,
            confidence_level=self.config.confidence_interval_level,
        )
        self.mixed_effects_result = None

    @staticmethod
    def estimate_paired_sample_size(effect_size: float, alpha: float = 0.05, power: float = 0.8) -> int:
        """Approximate paired sample size for a two-sided normal-theory test."""
        if effect_size <= 0 or not 0 < alpha < 1 or not 0 < power < 1:
            raise ValueError("effect_size must be positive and alpha/power must be between 0 and 1")
        normal = NormalDist()
        return int(__import__("math").ceil(((normal.inv_cdf(1-alpha/2) + normal.inv_cdf(power)) / effect_size) ** 2))

    @staticmethod
    def fit_mixed_effects(comparisons: List[PairwiseComparison]) -> Dict[str, Any]:
        """Fit the requested exploratory random-intercepts model, or return a logged fallback reason."""
        try:
            import pandas as pd
            import statsmodels.formula.api as smf
            rows = [{"outcome": c.score_delta if c.score_delta is not None else (c.embedding_cosine_similarity - 1.0), "condition": getattr(c, "condition", "demographic"),
                     "model": c.perturbed_response.model_name, "template": c.template_id,
                     "name": c.perturbed_prompt.demographic_profile.name} for c in comparisons]
            data = pd.DataFrame(rows)
            if len(data) < 5:
                raise ValueError("fewer than five observations")
            model = smf.mixedlm("outcome ~ C(condition) + C(model)", data,
                                groups=data["template"], vc_formula={"name": "0 + C(name)"})
            fit = model.fit(reml=False, method="lbfgs", disp=False)
            if not fit.converged:
                raise RuntimeError("optimizer did not converge")
            return {"status": "ok", "formula": "outcome ~ condition + model + (1|template) + (1|name)",
                    "params": {k: float(v) for k, v in fit.params.items()}, "pvalues": {k: float(v) for k, v in fit.pvalues.items()}}
        except Exception as exc:
            logging.warning("Mixed-effects fit failed; using paired permutation tests: %s", exc)
            return {"status": "fallback_permutation", "reason": str(exc)}

    def analyze_comparisons(
        self, comparisons: List[PairwiseComparison]
    ) -> List[HypothesisTestResult]:
        """
        Runs comprehensive hypothesis tests for each demographic subgroup vs baseline.
        """
        # Correct across every demographic group and primary metric in this run.
        grouped: Dict[Tuple[str, str], List[PairwiseComparison]] = {}
        for c in comparisons:
            if getattr(c, "condition", "demographic") != "demographic":
                continue
            grouped.setdefault((c.demographic_axis, c.demographic_group), []).append(c)

        preliminary_results: List[HypothesisTestResult] = []
        raw_p_values: List[float] = []
        tested_indices: List[int] = []
        for (axis, group), comps in grouped.items():
            baseline_label = comps[0].baseline_group
            metric_values = {
                "decision_flip_rate": [float(not c.decision_matches) for c in comps],
                "score_delta": [c.score_delta for c in comps if c.score_delta is not None],
                "embedding_similarity_delta": [c.embedding_cosine_similarity - 1.0 for c in comps],
                "sentiment_delta_secondary": [c.sentiment_delta for c in comps],
            }
            for metric_name, values in metric_values.items():
                if not values:
                    continue
                mean_value = sum(values) / len(values)
                variance = sum((x - mean_value) ** 2 for x in values) / (len(values) - 1) if len(values) > 1 else 0.0
                degenerate = variance == 0.0
                insufficient_n = len(values) < 2
                if degenerate or insufficient_n:
                    obs_diff, perm_p = round(mean_value, 4), 1.0
                else:
                    obs_diff, perm_p, _ = self.perm_test.test_paired_differences(values)
                _, ci_low, ci_high = self.bootstrap.compute_ci_mean(values)
                _, wilcox_p = NonParametricTests.wilcoxon_signed_rank(values)
                effect_d, d_ci_low, d_ci_high = self.bootstrap.compute_ci_paired_cohens_d(values)
                preliminary_results.append(HypothesisTestResult(
                    comparison_id=f"ht_{axis}_{group.replace(' ', '_').lower()}_{metric_name}",
                    demographic_axis=axis, baseline_group=baseline_label,
                    target_group=group, metric_tested=metric_name,
                    sample_size=len(values), baseline_mean=0.0,
                    target_mean=round(mean_value, 4), observed_difference=obs_diff,
                    effect_size_cohens_d=effect_d,
                    wilcoxon_p_value=None if degenerate or insufficient_n else wilcox_p,
                    raw_p_value=None if degenerate or insufficient_n else perm_p,
                    permutation_p_value=None if degenerate or insufficient_n else perm_p,
                    bootstrap_ci_95=[ci_low, ci_high],
                    effect_size_ci_95=[d_ci_low, d_ci_high],
                    status="insufficient_n" if insufficient_n else ("degenerate" if degenerate else "ok"),
                ))
                if not degenerate and not insufficient_n:
                    tested_indices.append(len(preliminary_results) - 1)
                    raw_p_values.append(perm_p)

        if not preliminary_results:
            return []

        self.mixed_effects_result = self.fit_mixed_effects(comparisons)
        # 5. Apply Benjamini-Hochberg False Discovery Rate (FDR) and Bonferroni adjustments
        if not raw_p_values:
            return preliminary_results
        bh_p_vals, bh_sig = MultipleTestingCorrection.benjamini_hochberg(
            raw_p_values, alpha=self.config.alpha_significance_level
        )
        bonf_p_vals, bonf_sig = MultipleTestingCorrection.bonferroni(
            raw_p_values, alpha=self.config.alpha_significance_level
        )

        for offset, i in enumerate(tested_indices):
            res = preliminary_results[i]
            res.benjamini_hochberg_p_value = bh_p_vals[offset]
            res.bonferroni_p_value = bonf_p_vals[offset]
            res.is_significant_fdr = bh_sig[offset]
            res.is_significant_bonferroni = bonf_sig[offset]

        return preliminary_results
