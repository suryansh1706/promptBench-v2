"""Exploratory tests on template-level paired deltas and control contrasts.

Repeated names/cues sharing a baseline are nested within a scenario template.
We average these observations before resampling, so their count cannot inflate n.
"""

import math
from collections import defaultdict
from typing import List, Optional

from .permutation import PermutationTest
from .bootstrap import BootstrapCI
from .corrections import MultipleTestingCorrection
from .non_parametric import NonParametricTests
from ..core.types import PairwiseComparison, HypothesisTestResult
from ..core.config import StatisticalConfig


class StatisticalTestingEngine:
    def __init__(self, config: Optional[StatisticalConfig] = None):
        self.config = config or StatisticalConfig()
        self.perm_test = PermutationTest(resamples=self.config.permutation_resamples)
        self.bootstrap = BootstrapCI(resamples=self.config.bootstrap_resamples,
                                     confidence_level=self.config.confidence_interval_level)

    def analyze_comparisons(self, comparisons: List[PairwiseComparison]) -> List[HypothesisTestResult]:
        """Test template means; compare each treatment to baseline and available controls.

        Template aggregation mitigates shared-baseline pseudoreplication. The fixed,
        small scenario set still does not support population-level fairness claims.
        """
        grouped = defaultdict(list)
        controls = defaultdict(list)
        for c in comparisons:
            grouped[(c.condition, c.demographic_axis, c.demographic_group)].append(c)
            if c.condition in {"IDENTICAL", "SHAM"}:
                controls[c.condition].append(c)
        results = []
        for (condition, axis, group), comps in sorted(grouped.items()):
            references = ["baseline"]
            if condition not in {"IDENTICAL", "SHAM"}:
                references += [c for c in ("IDENTICAL", "SHAM") if controls[c]]
            for metric, delta_attr, base_attr, target_attr in (
                ("Sentiment delta", "sentiment_delta", "sentiment_base", "sentiment_perturbed"),
                ("Score delta", "score_delta", "score_base", "score_perturbed"),
            ):
                for reference in references:
                    buckets = defaultdict(list)
                    for c in comps:
                        value = getattr(c, delta_attr)
                        if value is not None and math.isfinite(value):
                            buckets[c.template_id].append(c)
                    control_means = defaultdict(list)
                    if reference != "baseline":
                        for c in controls[reference]:
                            value = getattr(c, delta_attr)
                            if value is not None and math.isfinite(value):
                                control_means[c.template_id].append(value)
                    deltas, bases, targets = [], [], []
                    count = 0
                    for template_id, bucket in sorted(buckets.items()):
                        if reference != "baseline" and template_id not in control_means:
                            continue
                        delta = sum(getattr(c, delta_attr) for c in bucket) / len(bucket)
                        base = sum(getattr(c, base_attr) for c in bucket) / len(bucket)
                        target = sum(getattr(c, target_attr) for c in bucket) / len(bucket)
                        if reference != "baseline":
                            base = sum(control_means[template_id]) / len(control_means[template_id])
                            target = delta
                            delta -= base
                        deltas.append(delta)
                        bases.append(base)
                        targets.append(target)
                        count += len(bucket)
                    if not deltas:
                        continue
                    n = len(deltas)
                    observed = sum(deltas) / n
                    if n < 2:
                        perm_p, wilcox_p = 1.0, None
                        ci = [None, None]
                        note = "Descriptive only: fewer than two scenario templates; no uncertainty interval or inferential claim."
                    else:
                        _, perm_p, _ = self.perm_test.test_paired_differences(deltas)
                        _, low, high = self.bootstrap.compute_ci_mean(deltas)
                        ci = [low, high]
                        _, wilcox_p = NonParametricTests.wilcoxon_signed_rank(deltas)
                        note = "Exploratory template-level inference; fixed scenarios are not a random population sample."
                    variance = sum((d - observed) ** 2 for d in deltas) / (n - 1) if n > 1 else 0.0
                    # Paired Cohen's dz uses the same deltas as the test. Undefined
                    # zero-variance effects are represented as missing, never as zero.
                    effect = observed / math.sqrt(variance) if variance > 0 else None
                    results.append(HypothesisTestResult(
                        comparison_id=f"ht_{condition}_{axis}_{group}_{metric}_{reference}".replace(" ", "_"),
                        demographic_axis=axis, baseline_group=comps[0].baseline_group if reference == "baseline" else reference,
                        target_group=group, metric_tested=metric, sample_size=n,
                        baseline_mean=round(sum(bases) / n, 4), target_mean=round(sum(targets) / n, 4),
                        observed_difference=round(observed, 4), effect_size_cohens_d=round(effect, 4) if effect is not None else None,
                        permutation_p_value=perm_p, wilcoxon_p_value=wilcox_p, raw_p_value=perm_p,
                        bootstrap_ci_95=ci, condition=condition, calibration_reference=reference,
                        observation_count=count, inference_note=note,
                    ))
        if results:
            p_values = [r.raw_p_value for r in results]
            bh_p, bh_sig = MultipleTestingCorrection.benjamini_hochberg(p_values, alpha=self.config.alpha_significance_level)
            bonf_p, bonf_sig = MultipleTestingCorrection.bonferroni(p_values, alpha=self.config.alpha_significance_level)
            for i, result in enumerate(results):
                result.benjamini_hochberg_p_value, result.is_significant_fdr = bh_p[i], bh_sig[i]
                result.bonferroni_p_value, result.is_significant_bonferroni = bonf_p[i], bonf_sig[i]
        return results
