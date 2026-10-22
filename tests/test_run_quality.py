"""Quality summaries disclose compliance and duplication without raw answer text."""
import json
from pathlib import Path
import tempfile
import unittest
from promptbench.reporting.run_quality import summarize_response_journal


class TestRunQuality(unittest.TestCase):
    def test_aggregates_duplicate_ids_cache_hits_length_and_status(self):
        row = {"prompt_id": "same", "response_id": "same", "raw_text": "[DECISION: ACCEPT] [SCORE: 90] " + "privateword " * 26,
               "extracted_decision": "ACCEPT", "extracted_score": 90, "cache_hit": True,
               "status": "refusal", "metadata": {"finish_reason": "stop", "usage": {"completion_tokens": 40}}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "responses.private.jsonl"
            path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
            summary = summarize_response_journal(path)
        self.assertEqual(summary["duplicate_prompt_ids"], 1)
        self.assertEqual(summary["duplicate_response_ids"], 1)
        self.assertEqual(summary["cache_hits"], 2)
        self.assertEqual(summary["errors"], 2)
        self.assertEqual(summary["justifications_over_25_words"], 2)
        self.assertEqual(summary["completion_tokens_total"], 80)
        self.assertNotIn("privateword", json.dumps(summary))
        self.assertNotIn("raw_text", summary)
