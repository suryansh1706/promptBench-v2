"""
Dataset Exporter for PromptBench.
Exports standardized, reusable, and anonymized benchmark datasets in JSON, JSONL, and CSV formats.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..core.types import PairwiseComparison, AuditSummary, HypothesisTestResult


class DatasetExporter:
    """
    Exports audit benchmark datasets for open-science AI safety research.
    """

    @staticmethod
    def export_to_json(
        summary: AuditSummary,
        comparisons: List[PairwiseComparison],
        output_path: Path,
    ):
        """Exports the full audit run and all pairwise comparisons to a structured JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "summary": summary.to_dict(),
            "comparisons": [c.to_dict() for c in comparisons],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @staticmethod
    def export_to_jsonl(comparisons: List[PairwiseComparison], output_path: Path):
        """Exports comparisons as streaming JSON Lines."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for c in comparisons:
                f.write(json.dumps(c.to_dict()) + "\n")

    @staticmethod
    def export_to_csv(comparisons: List[PairwiseComparison], output_path: Path,
                      hypothesis_results: Optional[List[HypothesisTestResult]] = None,
                      run_metadata: Optional[Dict[str, Any]] = None):
        """Exports tabular metrics as a flat CSV file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not comparisons:
            return

        fieldnames = [
            "pair_id", "template_id", "scenario_category", "model_name", "provider", "condition", "demographic_axis",
            "demographic_group", "baseline_group", "embedding_cosine_similarity",
            "sentiment_base", "sentiment_perturbed", "sentiment_delta",
            "decision_base", "decision_perturbed", "decision_matches",
            "decision_flip",
            "score_base", "score_perturbed", "score_delta",
            "lexical_jaccard_similarity", "token_length_delta", "base_status", "perturbed_status",
            "group_effect_sizes", "temperature", "seed", "date_utc", "package_version"
        ]

        effects = {}
        for result in hypothesis_results or []:
            effects.setdefault((result.demographic_axis, result.target_group), []).append({
                "metric": result.metric_tested, "n": result.sample_size,
                "cohens_d": result.effect_size_cohens_d,
                "effect_size_ci_95": result.effect_size_ci_95,
                "permutation_p_value": result.permutation_p_value,
                "bh_fdr_p_value": result.benjamini_hochberg_p_value,
                "status": result.status,
            })

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for c in comparisons:
                row = c.to_dict()
                row["group_effect_sizes"] = json.dumps(effects.get((c.demographic_axis, c.demographic_group), []))
                row.update({key: (run_metadata or {}).get(key) for key in ("temperature", "seed", "date_utc", "package_version")})
                writer.writerow(row)
