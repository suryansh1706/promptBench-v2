"""Generate transparent Markdown and LaTeX summaries for Calibrated Audit audits."""

from datetime import datetime, timezone
from typing import List

from ..core.types import AuditSummary, HypothesisTestResult


def _ci_text(result: HypothesisTestResult) -> str:
    low, high = result.bootstrap_ci_95
    return f"[{low:+.3f}, {high:+.3f}]" if low is not None and high is not None else "N/A"


def _tex(value: str) -> str:
    return (str(value).replace("\\", r"\textbackslash{}")
            .replace("&", r"\&").replace("%", r"\%").replace("_", r"\_"))


class ReportGenerator:
    """Produce descriptive reports without overstating statistical evidence."""

    @staticmethod
    def generate_latex_table(results: List[HypothesisTestResult]) -> str:
        lines = [
            r"\begin{table*}[t]",
            r"\centering",
            r"\caption{Matched response contrasts with multiple-comparison correction.}",
            r"\label{tab:promptbench_results}",
            r"\small",
            r"\begin{tabular}{lllllcccccc}",
            r"\toprule",
            r"Axis & Subgroup & Metric & Reference & Condition & Templates & $\Delta$ & Effect $d$ & Raw $p$ & BH $p$ & 95\% CI \\",
            r"\midrule",
        ]
        for result in results:
            effect = f"{result.effect_size_cohens_d:+.2f}" if result.effect_size_cohens_d is not None else "N/A"
            star = r"$^{*}$" if result.is_significant_fdr else ""
            lines.append(
                f"{_tex(result.demographic_axis)} & {_tex(result.target_group)} & {_tex(result.metric_tested)} & "
                f"{_tex(result.calibration_reference)} & {_tex(result.condition)} & {result.sample_size} & "
                f"{result.observed_difference:+.4f} & {effect} & {result.raw_p_value:.4f} & "
                f"{result.benjamini_hochberg_p_value:.4f}{star} & {_ci_text(result)} \\\\"
            )
        lines += [
            r"\bottomrule",
            r"\multicolumn{11}{l}{\footnotesize $^{*}$FDR-adjusted $p<0.05$; a measured difference does not identify a causal bias.} \\",
            r"\end{tabular}",
            r"\end{table*}",
        ]
        return "\n".join(lines)

    @staticmethod
    def generate_markdown_summary(summary: AuditSummary) -> str:
        date = datetime.fromtimestamp(summary.timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            "# Calibrated Audit Audit Report",
            f"**Audit ID:** `{summary.audit_id}`  ",
            f"**Evaluated Model:** `{summary.model_name}` ({summary.provider})  ",
            f"**Scenario Domain:** `{summary.scenario_category}`  ",
            f"**Audit Date:** {date}  ",
            f"**Provider type:** {'Synthetic mock (pipeline demonstration)' if summary.provider == 'mock' else 'Live model'}  ",
            "",
            "## Metrics overview",
            f"- **Prompts generated:** {summary.total_prompts_tested}",
            f"- **Matched pairs evaluated, including controls:** {summary.total_pairs_evaluated}",
            f"- **Mean response cosine similarity, demographic pairs:** `{summary.overall_mean_similarity:.4f}`",
            f"- **Mean sentiment delta, demographic pairs:** `{summary.overall_mean_sentiment_delta:+.4f}`",
            f"- **Decision consistency, parsed demographic pairs:** `{summary.overall_decision_consistency_rate * 100:.1f}%`",
            "",
        ]
        quality = summary.axis_summaries.get("response_quality", {})
        if quality:
            lines += [
                "## Response quality",
                f"- **Usable responses:** {quality['usable_responses']} / {quality['requests']}",
                f"- **Failed or blocked responses:** {quality['failed_or_blocked_responses']}",
                f"- **Valid matched pairs:** {quality['valid_pairs']} / {quality['matched_pairs_generated']}",
                f"- **Excluded pairs:** {quality['excluded_pairs']}",
                "Metrics below describe only valid pairs; an incomplete run is not a complete model audit.",
                "",
            ]
        lines += [
            "## Calibration controls",
            "IDENTICAL repeats the exact prompt to estimate response noise. SHAM uses a neutral surface edit to estimate generic prompt sensitivity.",
            "",
        ]
        controls = summary.axis_summaries.get("control_summary", {})
        if controls:
            lines += ["| Condition | Pairs | Mean sentiment delta | Mean response similarity |",
                      "| :--- | ---: | ---: | ---: |"]
            for condition, values in controls.items():
                lines.append(f"| {condition} | {values['pairs']} | {values['mean_sentiment_delta']:+.4f} | {values['mean_embedding_similarity']:.4f} |")
        else:
            lines.append("No valid control pairs were available in this run.")

        by_axis = summary.axis_summaries.get("by_axis", {})
        if by_axis:
            lines += ["", "### Selection rates by perturbation axis", "",
                      "| Axis | Group | Selection rate | Excluded responses |",
                      "| :--- | :--- | ---: | ---: |"]
            for axis, metrics in by_axis.items():
                for group, rate in metrics.get("selection_rates", {}).items():
                    excluded = metrics.get("excluded_decision_counts", {}).get(group, 0)
                    lines.append(f"| {axis} | {group} | {rate:.3f} | {excluded} |")

        lines += [
            "",
            "## Statistical tests",
            "Tests summarize matched response differences. A significant result identifies a measured difference under the test assumptions. Review controls, response extraction, sample size, and scoring instruments before attributing a cause.",
            "",
            "| Axis | Subgroup | Metric | Reference | Condition | Templates | Pairs | Delta | Permutation p | BH FDR p | 95% CI | FDR result |",
            "| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |",
        ]
        for result in summary.hypothesis_test_results:
            significant = "Below 0.05" if result.is_significant_fdr else "Not below 0.05"
            lines.append(
                f"| {result.demographic_axis} | {result.target_group} | {result.metric_tested} | "
                f"{result.calibration_reference} | {result.condition} | {result.sample_size} | "
                f"{result.observation_count} | {result.observed_difference:+.4f} | "
                f"{result.permutation_p_value:.4f} | {result.benjamini_hochberg_p_value:.4f} | "
                f"{_ci_text(result)} | {significant} |"
            )
        notes = sorted({r.inference_note for r in summary.hypothesis_test_results if r.inference_note})
        if notes:
            lines += ["", "### Inference notes", ""]
            lines += [f"- {note}" for note in notes]
        lines += ["", "## Interpretation and next steps", ""]
        lines += [f"- {recommendation}" for recommendation in summary.audit_recommendations]
        return "\n".join(lines) + "\n"
