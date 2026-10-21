"""Export metrics and request provenance, with raw text excluded by default."""

import csv
import hashlib
import json
from pathlib import Path
from typing import List

from ..core.types import PairwiseComparison, AuditSummary


class DatasetExporter:
    """Create reviewable research data; raw prompts/responses require explicit opt-in."""

    @staticmethod
    def comparison_record(comparison: PairwiseComparison, include_raw_text: bool = False):
        row = comparison.to_dict()
        if not include_raw_text:
            row.pop("base_response_text", None)
            row.pop("perturbed_response_text", None)
        row["replicate"] = comparison.perturbed_prompt.metadata.get("replicate")
        row["similarity_method"] = comparison.similarity_method
        row["sentiment_method"] = "promptbench_custom_lexicon_v1"
        for prefix, prompt, response in (
            ("base", comparison.base_prompt, comparison.base_response),
            ("perturbed", comparison.perturbed_prompt, comparison.perturbed_response),
        ):
            row[f"{prefix}_provenance"] = {
                "response_id": response.response_id,
                "provider": response.provider,
                "model_name": response.model_name,
                "temperature": response.temperature,
                "seed": response.seed,
                "timestamp": response.timestamp,
                "cache_hit": response.cache_hit,
                "cache_bypass": bool(prompt.metadata.get("bypass_cache")),
                "prompt_sha256": hashlib.sha256(prompt.rendered_prompt.encode("utf-8")).hexdigest(),
                "system_prompt_sha256": hashlib.sha256(prompt.system_prompt.encode("utf-8")).hexdigest(),
                "response_sha256": hashlib.sha256(response.raw_text.encode("utf-8")).hexdigest(),
                "model_version": response.metadata.get("model_version"),
                "system_fingerprint": response.metadata.get("system_fingerprint"),
                "usage": response.metadata.get("usage"),
            }
            if include_raw_text:
                row[f"{prefix}_prompt_text"] = prompt.rendered_prompt
                row[f"{prefix}_system_prompt"] = prompt.system_prompt
        return row

    @staticmethod
    def export_to_json(summary: AuditSummary, comparisons: List[PairwiseComparison], output_path: Path,
                       include_raw_text: bool = False):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "2.0",
            "raw_text_included": include_raw_text,
            "privacy_note": "Metrics export; group labels and identifiers still require review before sharing.",
            "summary": summary.to_dict(),
            "comparisons": [DatasetExporter.comparison_record(c, include_raw_text) for c in comparisons],
        }
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, allow_nan=False)

    @staticmethod
    def export_to_jsonl(comparisons: List[PairwiseComparison], output_path: Path,
                        include_raw_text: bool = False):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            for comparison in comparisons:
                file.write(json.dumps(DatasetExporter.comparison_record(comparison, include_raw_text), allow_nan=False) + "\n")

    @staticmethod
    def export_to_csv(comparisons: List[PairwiseComparison], output_path: Path):
        """CSV contains metrics only, with a header even when no pairs succeeded."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "pair_id", "template_id", "scenario_category", "condition", "replicate", "demographic_axis",
            "demographic_group", "baseline_group", "embedding_cosine_similarity",
            "similarity_method", "sentiment_method", "sentiment_base", "sentiment_perturbed", "sentiment_delta",
            "decision_base", "decision_perturbed", "decision_matches",
            "score_base", "score_perturbed", "score_delta", "lexical_jaccard_similarity", "token_length_delta",
        ]
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for comparison in comparisons:
                writer.writerow(DatasetExporter.comparison_record(comparison))
