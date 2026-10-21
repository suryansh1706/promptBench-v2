"""
PromptBench Command-Line Interface (CLI).
Allows researchers to run end-to-end audits, perturbation generation, and statistical validations from the terminal.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

from .core.config import PromptBenchConfig
from .core.types import AuditSummary
from .perturbation.engine import PerturbationEngine
from .perturbation.templates import SCENARIO_TEMPLATES, get_template_by_id
from .query_pipeline.orchestrator import QueryOrchestrator
from .query_pipeline.providers.base import BaseLLMProvider
from .query_pipeline.providers.mock_provider import MockLLMProvider
from .query_pipeline.providers.gemini_provider import GeminiProvider
from .query_pipeline.providers.openai_provider import OpenAIProvider
from .metrics.scorer import BiasScorer
from .metrics.decision_consistency import DecisionConsistencyScorer
from .statistical_testing.engine import StatisticalTestingEngine
from .reporting.report_generator import ReportGenerator
from .reporting.dataset_exporter import DatasetExporter


def run_audit(args):
    """Executes an end-to-end bias audit."""
    print("=" * 70)
    print("PromptBench: LLM Demographic Bias Auditing Framework")
    print(f"Scenario: {args.scenario} | Provider: {args.provider} | Model: {args.model or 'provider default'}")
    print("=" * 70)

    config = PromptBenchConfig()
    config.provider.provider_name = args.provider
    config.provider.model_name = args.model or ("promptbench-mock-v1" if args.provider == "mock" else "gemini-2.5-flash" if args.provider == "gemini" else "gpt-4o-mini")
    config.provider.temperature = args.temperature
    config.provider.seed = args.seed
    config.enable_cache = not args.no_cache

    if args.samples_per_group < 1:
        raise ValueError("--samples-per-group must be at least 1")
    if args.scenario != "all" and get_template_by_id(args.scenario) is None:
        raise ValueError(f"Unknown scenario: {args.scenario}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Perturbation Engine
    print("\n[Stage 1/5] Running Perturbation Engine...")
    engine = PerturbationEngine()
    template_ids = [args.scenario] if args.scenario != "all" else [t.template_id for t in SCENARIO_TEMPLATES]
    all_prompts, paired_prompts = engine.generate_counterfactual_dataset(
        template_ids=template_ids,
        names_per_group=args.samples_per_group,
    )
    print(f" -> Generated {len(all_prompts)} prompts across {len(paired_prompts)} matched pairs, including controls.")

    # 2. LLM Query Pipeline
    print(f"\n[Stage 2/5] Querying Model ({args.provider}:{config.provider.model_name})...")
    orchestrator = QueryOrchestrator.from_config(config)

    def on_progress(curr, total, resp):
        if curr % max(1, total // 10) == 0 or curr == total:
            print(f" -> Progress: {curr}/{total} prompts evaluated ({curr/total*100:.1f}%)", flush=True)

    responses = orchestrator.execute_batch(all_prompts, progress_callback=on_progress)
    print(f" -> Received {len(responses)} model responses (some may be cache hits).")

    # 3. Bias & Response Drift Scoring
    print("\n[Stage 3/5] Scoring Response Similarity, Sentiment, and Decisions...")
    scorer = BiasScorer()
    comparisons = scorer.evaluate_batch_pairs(paired_prompts, responses)
    print(f" -> Evaluated {len(comparisons)} paired counterfactual comparisons.")

    # 4. Statistical Hypothesis Testing
    print("\n[Stage 4/5] Executing Paired Permutation Tests & Benjamini-Hochberg FDR...")
    stats_engine = StatisticalTestingEngine(config.stats)
    hyp_results = stats_engine.analyze_comparisons(comparisons)
    print(f" -> Computed {len(hyp_results)} metric/reference contrasts.")

    # Compute aggregate summary
    demographic_comparisons = [c for c in comparisons if c.demographic_axis != "control"]
    control_comparisons = [c for c in comparisons if c.demographic_axis == "control"]
    mean_sim = sum(c.embedding_cosine_similarity for c in demographic_comparisons) / len(demographic_comparisons) if demographic_comparisons else 0.0
    mean_sent_delta = sum(c.sentiment_delta for c in demographic_comparisons) / len(demographic_comparisons) if demographic_comparisons else 0.0
    decided = [c for c in demographic_comparisons if c.decision_matches is not None]
    match_rate = sum(1 for c in decided if c.decision_matches) / len(decided) if decided else 0.0

    # EEOC Disparate impact check
    group_decisions = {}
    for c in demographic_comparisons:
        if c.decision_perturbed is None:
            continue
        grp = f"{c.demographic_axis}:{c.demographic_group}"
        if grp not in group_decisions:
            group_decisions[grp] = []
        group_decisions[grp].append(c.decision_perturbed)
    fairness_metrics = DecisionConsistencyScorer.compute_demographic_parity_and_disparate_impact(group_decisions)
    fairness_metrics["by_axis"] = {
        axis: DecisionConsistencyScorer.compute_demographic_parity_and_disparate_impact(
            {group: decisions for label, decisions in group_decisions.items()
             if label.startswith(f"{axis}:") for group in [label.split(":", 1)[1]]}
        )
        for axis in sorted({c.demographic_axis for c in demographic_comparisons})
    }
    # Selection rates from different perturbation axes do not share one comparison.
    fairness_metrics["disparate_impact_ratio"] = None
    fairness_metrics["demographic_parity_difference"] = None
    fairness_metrics["passes_four_fifths_rule"] = None
    fairness_metrics["control_summary"] = {
        condition: {
            "pairs": len(items),
            "mean_sentiment_delta": round(sum(c.sentiment_delta for c in items) / len(items), 4),
            "mean_embedding_similarity": round(sum(c.embedding_cosine_similarity for c in items) / len(items), 4),
        }
        for condition in sorted({c.condition for c in control_comparisons})
        if (items := [c for c in control_comparisons if c.condition == condition])
    }

    recommendations = []
    significant_differences = [r for r in hyp_results if r.is_significant_fdr]
    if not demographic_comparisons:
        recommendations.append("No valid matched response pairs were available; check provider errors and run settings.")
    elif args.provider == "mock":
        recommendations.append("Mock provider results demonstrate the pipeline only; they are not evidence about a deployed LLM.")
    if significant_differences:
        recommendations.append(
            f"Observed {len(significant_differences)} contrasts below the FDR threshold; review controls and individual responses before attributing a cause."
        )
    else:
        recommendations.append("No tested contrasts met the FDR threshold in this run; this does not establish equivalence.")
    recommendations.append("Selection-rate ratios are descriptive for this synthetic sample and are not legal adverse-impact findings.")

    summary = AuditSummary(
        audit_id=f"audit_{int(time.time())}",
        timestamp=time.time(),
        provider=args.provider,
        model_name=args.model,
        scenario_category=args.scenario,
        total_prompts_tested=len(all_prompts),
        total_pairs_evaluated=len(comparisons),
        overall_mean_similarity=round(mean_sim, 4),
        overall_mean_sentiment_delta=round(mean_sent_delta, 4),
        overall_decision_consistency_rate=round(match_rate, 4),
        axis_summaries=fairness_metrics,
        hypothesis_test_results=hyp_results,
        audit_recommendations=recommendations,
    )

    # 5. Reporting & Dataset Export
    print("\n[Stage 5/5] Exporting Research Artifacts...")
    json_path = output_dir / "audit_dataset.json"
    csv_path = output_dir / "audit_comparisons.csv"
    report_md_path = output_dir / "audit_report.md"
    latex_path = output_dir / "table_results.tex"

    DatasetExporter.export_to_json(summary, comparisons, json_path)
    DatasetExporter.export_to_csv(comparisons, csv_path)
    
    report_md = ReportGenerator.generate_markdown_summary(summary)
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    latex_code = ReportGenerator.generate_latex_table(hyp_results)
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(latex_code)

    print(f" -> JSON Dataset:  {json_path}")
    print(f" -> CSV Table:     {csv_path}")
    print(f" -> Markdown Summary: {report_md_path}")
    print(f" -> LaTeX Table:   {latex_path}")

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE - Summary Findings:")
    print(f"  * Response Cosine Similarity: {mean_sim:.4f}")
    print(f"  * Mean Sentiment Delta:       {mean_sent_delta:+.4f}")
    print(f"  * Decision Consistency Rate:  {match_rate * 100:.1f}%")
    ratio = fairness_metrics.get("disparate_impact_ratio")
    print(f"  * Selection-rate ratio:      {ratio:.2f}" if ratio is not None else "  * Selection-rate ratio:      not estimable")
    print(f"  * FDR-significant contrasts: {len(significant_differences)}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="PromptBench: Demographic Bias Auditing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: audit
    audit_parser = subparsers.add_parser("audit", help="Run end-to-end bias audit")
    audit_parser.add_argument("--scenario", type=str, default="job_swe_001", help="Template ID or 'all'")
    audit_parser.add_argument("--provider", type=str, default="mock", choices=["gemini", "mock", "openai"])
    audit_parser.add_argument("--model", type=str, default=None, help="Model name (defaults to a provider-specific model)")
    audit_parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    audit_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    audit_parser.add_argument("--samples-per-group", type=int, default=2, help="Names per demographic category")
    audit_parser.add_argument("--output-dir", type=str, default="./results", help="Directory to save audit artifacts")
    audit_parser.add_argument("--no-cache", action="store_true", help="Bypass cached responses for this run")

    args = parser.parse_args()

    if args.command == "audit" or args.command is None:
        if args.command is None:
            # Default run with sample settings
            args = parser.parse_args(["audit"])
        run_audit(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
