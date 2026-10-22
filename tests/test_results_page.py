"""Portable report checks: missing data, escaped labels, and aggregate-only output."""
import json
from pathlib import Path
import tempfile
import unittest
from promptbench.reporting.results_page import write_results_page


class TestResultsPage(unittest.TestCase):
    def test_report_preserves_missing_values_and_excludes_raw_text(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "audit.json", Path(directory) / "report.html"
            source.write_text(json.dumps({"summary": {"model_name": "<unsafe>", "provider": "ollama", "axis_summaries": {"response_quality": {"requests": 3, "failed_or_blocked_responses": 1, "excluded_pairs": 1}}}, "comparisons": [{"template_id": "one", "condition": "NAME", "demographic_axis": "ethnicity", "demographic_group": "A", "score_delta": None, "decision_matches": None, "base_response_text": "PRIVATE ANSWER", "raw_prompt": "PRIVATE PROMPT"}], "api_key": "PRIVATE KEY"}))
            write_results_page(source, output)
            text = output.read_text()
            self.assertIn("&lt;unsafe&gt;", text)
            self.assertIn("Unavailable", text)
            self.assertIn("Incomplete run", text)
            self.assertIn("one observed scenario", text)
            for private in ("PRIVATE ANSWER", "PRIVATE PROMPT", "PRIVATE KEY"):
                self.assertNotIn(private, text)

    def test_empty_export_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "audit.json", Path(directory) / "report.html"
            source.write_text('{}')
            write_results_page(source, output)
            self.assertIn("Unavailable", output.read_text())

    def test_decision_consistency_uses_parsed_treatments_only(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "audit.json", Path(directory) / "report.html"
            source.write_text(json.dumps({"summary": {"overall_decision_consistency_rate": 1.0}, "comparisons": [
                {"condition": "NAME", "decision_matches": False, "score_delta": -5},
                {"condition": "NAME", "decision_matches": None},
                {"condition": "IDENTICAL", "decision_matches": True}]}))
            write_results_page(source, output)
            text = output.read_text()
            self.assertIn("<strong>0.0%</strong>", text)
            self.assertIn("Observed score changes", text)
            self.assertIn('role="img"', text)

    def test_live_style_findings_controls_and_before_after_are_data_derived(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "audit.json", Path(directory) / "report.html"
            def row(condition, axis, group, delta, decision="ACCEPT"):
                return {"template_id": "one", "condition": condition, "demographic_axis": axis,
                        "demographic_group": group, "score_delta": delta, "score_base": 90,
                        "score_perturbed": 90 + delta, "decision_base": "ACCEPT",
                        "decision_perturbed": decision, "decision_matches": decision == "ACCEPT"}
            source.write_text(json.dumps({"summary": {"timestamp": 0, "axis_summaries": {"response_quality": {"valid_pairs": 5, "matched_pairs_generated": 5}}}, "comparisons": [
                row("NAME", "ethnicity", "Name", 0), row("SES", "socioeconomic_status", "High", 5),
                row("SES", "socioeconomic_status", "Low", -5, "INTERVIEW"),
                row("SHAM", "control", "Sham", 5), row("IDENTICAL", "control", "Identical", 0)]}))
            write_results_page(source, output)
            text = output.read_text()
            for expected in ("1 of 3 parsed treatment pairs changed", "90 → 95", "90 → 85",
                             "ACCEPT → INTERVIEW", "as large as or larger", "scores were unchanged",
                             "01 Jan 1970 · 05:30 IST", "<strong>5 / 5</strong>"):
                self.assertIn(expected, text)
            self.assertNotIn("min-width:600px", text)
