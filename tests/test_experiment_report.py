"""An experiment overview links separate domains and labels incomplete work."""
import json
from pathlib import Path
import tempfile
import unittest
from promptbench.reporting.experiment_report import write_experiment_overview


class TestExperimentOverview(unittest.TestCase):
    def test_pending_domains_and_derived_model_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "hiring").mkdir()
            payload = {"summary": {"model_name": "test-local-model", "axis_summaries": {
                "response_quality": {"requests": 2, "usable_responses": 2, "matched_pairs_generated": 1, "valid_pairs": 1},
                "run_execution": {"settings": {"response_profile": "test-profile", "max_tokens": 99, "samples_per_group": 2}}}},
                "comparisons": [{"template_id": "seed-one", "condition": "NAME", "decision_matches": True}]}
            (root / "hiring" / "audit_dataset.json").write_text(json.dumps(payload))
            (root / "loan").mkdir()
            (root / "loan" / "run_manifest.json").write_text(json.dumps({"planned_requests": 7}))
            (root / "loan" / "responses.private.jsonl").write_text('PRIVATE RAW RESPONSE\n')
            path = write_experiment_overview(root)
            text = path.read_text()
            for expected in ("Completed domains: 1 / 3", "test-local-model", "test-profile", "2 samples per group", "1 of 7", "Pending", 'href="hiring/results.html"', "not pooled"):
                self.assertIn(expected, text)
            self.assertNotIn("PRIVATE RAW RESPONSE", text)
            self.assertNotIn("qwen2.5:7b", text)
            self.assertTrue((root / "hiring" / "results.html").exists())
