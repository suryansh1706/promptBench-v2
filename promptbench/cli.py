"""
Calibrated Audit Command-Line Interface (CLI).
Allows researchers to run end-to-end audits, perturbation generation, and statistical validations from the terminal.
"""

import argparse
import sys
import time
import platform
from dataclasses import replace
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
from .statistical_testing.corrections import MultipleTestingCorrection
from .reporting.report_generator import ReportGenerator
from .reporting.dataset_exporter import DatasetExporter


def _run_single_audit(args):
    """Executes an end-to-end bias audit."""
    print("=" * 70)
    print("Calibrated Audit: LLM Demographic Bias Auditing Framework")
    print(f"Scenario: {args.scenario} | Provider: {args.provider} | Model: {args.model}")
    print("=" * 70)

    config = PromptBenchConfig()
    config.provider.provider_name = args.provider
    config.provider.model_name = args.model
    config.provider.temperature = args.temperature
    config.provider.seed = args.seed

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Perturbation Engine
    print("\n[Stage 1/5] Running Perturbation Engine...")
    engine = PerturbationEngine()
    template_ids = [args.scenario] if args.scenario != "all" else [t.template_id for t in SCENARIO_TEMPLATES]
    base_prompts, base_pairs = engine.generate_counterfactual_dataset(
        template_ids=template_ids,
        names_per_group=args.samples_per_group,
    )
    all_prompts, paired_prompts = [], []
    for rep_index in range(args.reps):
        clones = {p.prompt_id: replace(p, prompt_id=f"{p.prompt_id}__rep{rep_index}", metadata={**p.metadata, "rep_index": rep_index + (args.reps if p.metadata.get("condition") == "IDENTICAL" else 0)}) for p in base_prompts}
        all_prompts.extend(clones.values())
        paired_prompts.extend((clones[b.prompt_id], clones[v.prompt_id]) for b, v in base_pairs)
    print(f" -> Generated {len(all_prompts)} prompts across {len(paired_prompts)} counterfactual pairs.")

    # 2. LLM Query Pipeline
    print(f"\n[Stage 2/5] Querying Model ({args.provider}:{args.model})...")
    orchestrator = QueryOrchestrator.from_config(config)

    def on_progress(curr, total, resp):
        if curr % max(1, total // 10) == 0 or curr == total:
            print(f" -> Progress: {curr}/{total} prompts evaluated ({curr/total*100:.1f}%)", flush=True)

    responses = orchestrator.execute_batch(all_prompts, progress_callback=on_progress)
    print(f" -> Completed {len(responses)} LLM queries.")
    group_by_prompt = {p.prompt_id: str(p.metadata.get("group", "baseline")) for p in all_prompts}
    excluded = {}
    for response in responses.values():
        if response.status != "ok":
            key = f"{group_by_prompt.get(response.prompt_id, 'unknown')}:{response.status}"
            excluded[key] = excluded.get(key, 0) + 1
    failed_count = sum(excluded.values())
    for response in responses.values():
        if response.status != "ok":
            print(f"FINAL FAILURE [{response.status}] {response.prompt_id}", flush=True)
    if responses and failed_count / len(responses) > 0.10:
        try:
            QueryOrchestrator.assert_acceptable_response_rate(responses)
        except RuntimeError as exc:
            raise RuntimeError(f"{exc} Final failures by group/status: {excluded}") from exc

    # 3. Bias & Response Drift Scoring
    print("\n[Stage 3/5] Scoring Semantic, Sentiment, and Decision Disparities...")
    scorer = BiasScorer(use_transformer_embeddings=True, embedding_model=args.embedding_model)
    comparisons = scorer.evaluate_batch_pairs(paired_prompts, responses)
    print(f" -> Evaluated {len(comparisons)} paired counterfactual comparisons.")

    # 4. Statistical Hypothesis Testing
    print("\n[Stage 4/5] Executing Paired Permutation Tests & Benjamini-Hochberg FDR...")
    stats_engine = StatisticalTestingEngine(config.stats)
    hyp_results = stats_engine.analyze_comparisons(comparisons)
    print(f" -> Completed {len(hyp_results)} group/metric tests.")

    # Compute aggregate summary
    demographic_comparisons = [c for c in comparisons if c.condition == "demographic"]
    mean_sim = sum(c.embedding_cosine_similarity for c in demographic_comparisons) / len(demographic_comparisons) if demographic_comparisons else 1.0
    mean_sent_delta = sum(c.sentiment_delta for c in demographic_comparisons) / len(demographic_comparisons) if demographic_comparisons else 0.0
    match_rate = sum(1 for c in demographic_comparisons if c.decision_matches) / len(demographic_comparisons) if demographic_comparisons else 1.0

    # EEOC Disparate impact check
    group_decisions = {}
    for c in demographic_comparisons:
        grp = c.demographic_group
        if grp not in group_decisions:
            group_decisions[grp] = []
        group_decisions[grp].append(c.decision_perturbed)
    fairness_metrics = DecisionConsistencyScorer.compute_demographic_parity_and_disparate_impact(group_decisions)
    demographic = demographic_comparisons
    calibration = {}
    for condition in ("IDENTICAL", "SHAM"):
        controls = [c for c in comparisons if c.condition == condition]
        for metric, fn in {
            "sentiment_delta_abs": lambda c: abs(c.sentiment_delta),
            "semantic_drift": lambda c: 1.0 - c.embedding_cosine_similarity,
            "score_delta_abs": lambda c: abs(c.score_delta) if c.score_delta is not None else None,
            "decision_flip": lambda c: float(not c.decision_matches),
        }.items():
            vals = sorted(v for c in controls if (v := fn(c)) is not None)
            if not vals:
                continue
            threshold = vals[min(len(vals) - 1, int(0.95 * len(vals)))]
            demo_vals = [v for c in demographic if (v := fn(c)) is not None]
            calibration[f"{metric}_vs_{condition.lower()}_p95"] = {
                "threshold": threshold,
                "fraction_demographic_exceeding": sum(v > threshold for v in demo_vals) / len(demo_vals) if demo_vals else None,
                "control_n": len(vals), "demographic_n": len(demo_vals),
            }
    fairness_metrics["calibration"] = calibration

    recommendations = []
    if not fairness_metrics.get("passes_four_fifths_rule", True):
        recommendations.append(
            f"The observed disparate-impact ratio ({fairness_metrics['disparate_impact_ratio']:.2f}) is below the 0.80 four-fifths screening heuristic; this is not a legal finding."
        )
    significant_biases = [r for r in hyp_results if r.is_significant_fdr]
    if significant_biases:
        recommendations.append(
            f"{len(significant_biases)} subgroup comparisons were flagged after Benjamini-Hochberg correction; interpret as exploratory results for this run only."
        )
    else:
        recommendations.append("No subgroup comparisons were flagged at the configured threshold in this run; this does not establish invariance.")

    summary = AuditSummary(
        audit_id=f"audit_{int(time.time())}",
        timestamp=time.time(),
        provider=args.provider,
        model_name=orchestrator.provider.model_name,
        scenario_category=args.scenario,
        total_prompts_tested=len(all_prompts),
        total_pairs_evaluated=len(comparisons),
        total_demographic_pairs=len(demographic_comparisons),
        total_control_pairs=sum(1 for c in comparisons if c.condition != "demographic"),
        overall_mean_similarity=round(mean_sim, 4),
        overall_mean_sentiment_delta=round(mean_sent_delta, 4),
        overall_decision_consistency_rate=round(match_rate, 4),
        axis_summaries=fairness_metrics,
        hypothesis_test_results=hyp_results,
        audit_recommendations=recommendations,
        excluded_response_counts=excluded,
        run_metadata={"provider": args.provider, "model": orchestrator.provider.model_name, "temperature": args.temperature,
                      "seed": args.seed, "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "package_version": config.version, "python_version": platform.python_version(), "reps": args.reps,
                      "embedding_model": args.embedding_model, "embedding_backend": scorer.embedding_scorer.backend,
                      "embedding_fallback_reason": scorer.embedding_scorer.fallback_reason,
                      "mixed_effects": stats_engine.mixed_effects_result},
    )

    # 5. Reporting & Dataset Export
    print("\n[Stage 5/5] Exporting Research Artifacts...")
    json_path = output_dir / "audit_dataset.json"
    csv_path = output_dir / "audit_comparisons.csv"
    report_md_path = output_dir / "audit_report.md"
    latex_path = output_dir / "table_results.tex"

    DatasetExporter.export_to_json(summary, comparisons, json_path)
    DatasetExporter.export_to_csv(comparisons, csv_path, hyp_results, summary.run_metadata)
    
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
    print(f"  * Semantic Cosine Similarity: {mean_sim:.4f}")
    print(f"  * Mean Sentiment Delta:       {mean_sent_delta:+.4f}")
    print(f"  * Decision Consistency Rate:  {match_rate * 100:.1f}%")
    print(f"  * Disparate Impact Ratio:     {fairness_metrics.get('disparate_impact_ratio', 1.0):.2f}")
    print(f"  * Tests flagged after BH FDR:  {len(significant_biases)}")
    print("=" * 70)
    return summary, comparisons, hyp_results, output_dir


def run_audit(args):
    """Run one audit or dispatch a comma-separated list of provider:model pairs."""
    models = getattr(args, "models", "")
    if not models:
        return _run_single_audit(args)
    completed_runs = []
    for item in models.split(","):
        provider, sep, model = item.strip().partition(":")
        if not sep or provider not in {"gemini", "mock", "openai"} or not model:
            raise ValueError("model entries must use provider:model (gemini, mock, or openai)")
        item_args = argparse.Namespace(**vars(args))
        item_args.provider, item_args.model = provider, model
        item_args.output_dir = str(Path(args.output_dir) / f"{provider}_{model.replace('/', '_')}")
        completed_runs.append(_run_single_audit(item_args))

    # Apply one FDR family across every model and metric in this multi-model run.
    test_refs = [(run_index, result_index, result)
                 for run_index, (_, _, results, _) in enumerate(completed_runs)
                 for result_index, result in enumerate(results)
                 if result.raw_p_value is not None]
    if test_refs:
        p_values = [result.raw_p_value for _, _, result in test_refs]
        bh_values, bh_significant = MultipleTestingCorrection.benjamini_hochberg(p_values, alpha=0.05)
        bonf_values, bonf_significant = MultipleTestingCorrection.bonferroni(p_values, alpha=0.05)
        for offset, (run_index, _, result) in enumerate(test_refs):
            result.benjamini_hochberg_p_value = bh_values[offset]
            result.bonferroni_p_value = bonf_values[offset]
            result.is_significant_fdr = bh_significant[offset]
            result.is_significant_bonferroni = bonf_significant[offset]
    for summary, comparisons, results, output_dir in completed_runs:
        summary.audit_recommendations = [r for r in summary.audit_recommendations
            if "subgroup comparisons were flagged" not in r and "No subgroup comparisons" not in r]
        if test_refs:
            summary.audit_recommendations.append("Benjamini-Hochberg correction was applied across all testable metrics and models in this multi-model run.")
        else:
            summary.audit_recommendations.append("No group/metric comparisons had enough non-degenerate samples for inference across the requested models.")
    for summary, comparisons, results, output_dir in completed_runs:
        DatasetExporter.export_to_json(summary, comparisons, output_dir / "audit_dataset.json")
        DatasetExporter.export_to_csv(comparisons, output_dir / "audit_comparisons.csv", results, summary.run_metadata)
        (output_dir / "audit_report.md").write_text(ReportGenerator.generate_markdown_summary(summary), encoding="utf-8")
        (output_dir / "table_results.tex").write_text(ReportGenerator.generate_latex_table(results), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Calibrated Audit: Demographic Bias Auditing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: audit
    audit_parser = subparsers.add_parser("audit", help="Run end-to-end bias audit")
    audit_parser.add_argument("--scenario", type=str, default="job_swe_001", help="Template ID or 'all'")
    audit_parser.add_argument("--provider", type=str, default="gemini", choices=["gemini", "mock", "openai"])
    audit_parser.add_argument("--model", type=str, default="gemini-1.5-flash", help="Model name")
    audit_parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    audit_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    audit_parser.add_argument("--samples-per-group", type=int, default=2, help="Names per demographic category")
    audit_parser.add_argument("--reps", type=int, default=5, help="Repeated queries per prompt (replicates)")
    audit_parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2", help="Sentence-transformer model ID")
    audit_parser.add_argument("--models", default="", help="Comma-separated provider:model pairs")
    audit_parser.add_argument("--output-dir", type=str, default="./results", help="Directory to save audit artifacts")

    args = parser.parse_args()

    if args.command == "audit" or args.command is None:
        if args.command is None:
            # Default run with sample settings
            args = parser.parse_args(["audit"])
        if args.reps < 1:
            parser.error("--reps must be at least 1")
        run_audit(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
