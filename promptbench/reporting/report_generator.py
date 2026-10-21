"""
Automated Academic Research & LaTeX Report Generator for Calibrated Audit.
Produces publication-ready LaTeX tables, Markdown executive summaries, and fairness scorecards.
"""

from typing import List, Dict, Any, Optional
import time
from ..core.types import AuditSummary, HypothesisTestResult, PairwiseComparison


class ReportGenerator:
    """
    Generates academic research reports and formatted LaTeX tables for Minor Project paper submissions.
    """

    @staticmethod
    def generate_latex_table(results: List[HypothesisTestResult]) -> str:
        """
        Formats hypothesis test results into a standard IEEE/NeurIPS LaTeX table.
        """
        latex = [
            r"\begin{table*}[t]",
            r"\centering",
            r"\caption{Demographic Bias and Response Drift Audit Results with Multiple Comparisons Correction.}",
            r"\label{tab:calibrated_audit_results}",
            r"\small",
            r"\begin{tabular}{lllcccccc}",
            r"\toprule",
            r"\textbf{Axis} & \textbf{Group} & \textbf{Metric} & \textbf{n} & \textbf{Effect} & \textbf{Cohen's $d$ [95\% CI]} & \textbf{Raw $p$} & \textbf{BH $p$} & \textbf{Status} \\",
            r"\midrule",
        ]

        for r in results:
            d_ci = f"{r.effect_size_cohens_d:+.2f} [{r.effect_size_ci_95[0]:+.2f}, {r.effect_size_ci_95[1]:+.2f}]"
            sig_marker = r"$^{*}$" if r.is_significant_fdr else ""
            raw_p = f"{r.raw_p_value:.4f}" if r.raw_p_value is not None else "—"
            adj_p = f"{r.benjamini_hochberg_p_value:.4f}" if r.benjamini_hochberg_p_value is not None else "—"
            latex.append(
                f"{r.demographic_axis.capitalize()} & {r.target_group} & {r.metric_tested} & {r.sample_size} & {r.observed_difference:+.4f} & "
                f"{d_ci} & {raw_p} & {adj_p}{sig_marker} & {r.status} \\\\"
            )

        latex.extend([
            r"\bottomrule",
            r"\multicolumn{9}{l}{\footnotesize $^{*}$Flagged after Benjamini-Hochberg correction; exploratory results only.} \\",
            r"\end{tabular}",
            r"\end{table*}",
        ])

        return "\n".join(latex)

    @staticmethod
    def generate_markdown_summary(summary: AuditSummary) -> str:
        """
        Creates a clean, comprehensive executive summary in GitHub-Flavored Markdown.
        """
        lines = [
            f"# Calibrated Audit Executive Report",
            f"**Audit ID:** `{summary.audit_id}`  ",
            f"**Evaluated Model:** `{summary.model_name}` ({summary.provider.capitalize()})  ",
            f"**Scenario Domain:** `{summary.scenario_category}`  ",
            f"**Audit Date:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(summary.timestamp))}  ",
            "",
            "## 1. High-Level Metrics Overview",
            f"- **Total Prompts Tested:** {summary.total_prompts_tested}",
            f"- **Total Counterfactual Pairs Evaluated:** {summary.total_pairs_evaluated}",
            f"- **Demographic pairs / calibration control pairs:** {summary.total_demographic_pairs} / {summary.total_control_pairs}",
            f"- **Mean Semantic Embedding Cosine Similarity:** `{summary.overall_mean_similarity:.4f}`",
            f"- **Mean Sentiment Delta ($\\Delta$ Sentiment):** `{summary.overall_mean_sentiment_delta:+.4f}`",
            f"- **Decision Consistency Rate:** `{summary.overall_decision_consistency_rate * 100:.1f}%`",
            f"- **Excluded non-ok responses by group/status:** `{summary.excluded_response_counts}`",
            f"- **Run metadata:** `{summary.run_metadata}`",
            "",
            "## 2. Statistical Hypothesis Testing & Significance",
            "| Axis | Subgroup | Metric | n | Effect | Cohen's d [95% CI] | Permutation $p$ | BH FDR $p$ | Mean-delta 95% CI | Status |",
            "| :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |",
        ]

        for r in summary.hypothesis_test_results:
            sig = "flagged after FDR correction" if r.is_significant_fdr else r.status
            ci = f"[{r.bootstrap_ci_95[0]:+.3f}, {r.bootstrap_ci_95[1]:+.3f}]"
            d_ci = f"{r.effect_size_cohens_d:+.3f} [{r.effect_size_ci_95[0]:+.3f}, {r.effect_size_ci_95[1]:+.3f}]"
            raw_p = f"{r.permutation_p_value:.4f}" if r.permutation_p_value is not None else "—"
            adj_p = f"{r.benjamini_hochberg_p_value:.4f}" if r.benjamini_hochberg_p_value is not None else "—"
            lines.append(
                f"| {r.demographic_axis.capitalize()} | {r.target_group} | {r.metric_tested} | {r.sample_size} | {r.observed_difference:+.4f} | {d_ci} | "
                f"{raw_p} | {adj_p} | {ci} | {sig} |"
            )

        calibration = summary.axis_summaries.get("calibration", {})
        lines.extend(["", "## 3. Calibration Against Controls", f"`{calibration}`"])
        lines.extend([
            "",
            "## 4. Findings & Review Recommendations",
        ])
        for rec in summary.audit_recommendations:
            lines.append(f"- {rec}")

        return "\n".join(lines)
