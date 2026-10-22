"""Presentation and UI checks, skipped when optional UI dependencies are absent."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from promptbench.perturbation.templates import SCENARIO_TEMPLATES

ROOT = Path(__file__).resolve().parent.parent
HAS_CHARTS = importlib.util.find_spec("matplotlib") is not None and importlib.util.find_spec("pandas") is not None
HAS_STREAMLIT = importlib.util.find_spec("streamlit") is not None


@unittest.skipUnless(HAS_CHARTS, "Presentation dependencies are not installed")
class TestPresentationFigures(unittest.TestCase):
    def test_incomplete_figure_and_missing_scores_are_explicit(self):
        from promptbench.reporting.dashboard_charts import comparison_frame, presentation_figure, figure_png
        records = [{"condition": "NAME", "demographic_axis": "ethnicity", "demographic_group": "Name cue", "template_id": "one", "score_delta": None, "sentiment_delta": .02, "decision_matches": None}]
        frame = comparison_frame(records)
        self.assertTrue(frame["Score change"].isna().all())
        figure = presentation_figure(records, "local-model", "ollama", {"expected_pairs": 20, "valid_pairs": 1})
        text = " ".join(item.get_text() for item in figure.texts)
        self.assertIn("INCOMPLETE RUN", text)
        self.assertIn("1/20", text)
        self.assertIn("One template", text)
        self.assertIn("Unavailable", text)
        self.assertTrue(figure_png(figure).startswith(b"\x89PNG"))

    def test_minimized_dataset_to_png(self):
        from promptbench.reporting.dashboard_charts import presentation_from_dataset
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "audit.json", Path(directory) / "summary.png"
            source.write_text(json.dumps({"summary": {"provider": "mock", "model_name": "demo"}, "comparisons": []}))
            presentation_from_dataset(source, output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG"))

    def test_cli_quality_fields_mark_incomplete_slide(self):
        from promptbench.reporting.dashboard_charts import presentation_from_dataset
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "partial.json", Path(directory) / "partial.png"
            source.write_text(json.dumps({"summary": {"provider": "gemini", "model_name": "test",
                "axis_summaries": {"response_quality": {"matched_pairs_generated": 20,
                    "valid_pairs": 1, "failed_or_blocked_responses": 2}}},
                "comparisons": [{"condition": "NAME", "demographic_axis": "ethnicity",
                    "demographic_group": "Cue", "template_id": "one", "score_delta": 0,
                    "sentiment_delta": 0, "decision_matches": True}]}))
            presentation_from_dataset(source, output)
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG"))


@unittest.skipUnless(HAS_STREAMLIT and HAS_CHARTS, "Streamlit presentation dependencies are not installed")
class TestDashboard(unittest.TestCase):
    def test_mock_views_filters_and_presentation_download(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
        self.assertEqual(len(at.exception), 0)
        labels = [button.label for button in at.get("download_button")]
        self.assertIn("Download presentation summary (.png)", labels)
        self.assertIn("Download contrast chart (.png)", labels)
        self.assertTrue(any("One scenario template" in message.value for message in at.info))
        next(s for s in at.selectbox if s.label == "Result metric").select("Sentiment change").run(timeout=60)
        self.assertEqual(len(at.exception), 0)
        at.sidebar.selectbox[0].select("all").run(timeout=60)
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(next(m.value for m in at.metric if m.label == "Scenario templates"), str(len(SCENARIO_TEMPLATES)))

    def test_mock_workflow_filters_inspector_custom_and_exports(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
        def select(label, value):
            next(s for s in at.selectbox if s.label == label).select(value).run(timeout=60)
            self.assertEqual(len(at.exception), 0)
        select("Demographic axis", "Gender")
        select("Result metric", "Lexical similarity")
        select("Calibration metric", "Sentiment change")
        select("Condition family", "SES")
        select("Comparison reference", "SHAM")
        select("Select Counterfactual Pair to Inspect", 1)
        self.assertTrue(next(t for t in at.text_area if t.label == "Variant Model Response").value)
        next(b for b in at.button if "Run custom audit" in b.label).click().run(timeout=60)
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(any("Successfully evaluated" in item.value for item in at.success))
        labels = [button.label for button in at.get("download_button")]
        for label in ("Download JSON dataset", "Download CSV comparisons"):
            self.assertIn(label, labels)
        next(c for c in at.checkbox if c.label == "Include raw prompts and responses in JSON").check().run(timeout=60)
        self.assertEqual(len(at.exception), 0)

    def test_completed_experiment_is_available_in_dashboard_navigation(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
        self.assertEqual(len(at.exception), 0)
        labels = [tab.label for tab in at.tabs]
        self.assertIn("Larger experiment", labels)
        self.assertEqual(next(m.value for m in at.metric if m.label == "Usable local responses"), "232 / 232")
        self.assertEqual(next(m.value for m in at.metric if m.label == "Valid matched comparisons"), "228 / 228")
        self.assertIn("Treatment decision changes", [metric.label for metric in at.metric])
        self.assertEqual(len(at.get("iframe")), 3)

    def test_local_selection_waits_without_inference(self):
        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
        with patch("promptbench.query_pipeline.providers.ollama_provider.OllamaProvider.available_models", return_value=[{"name": "qwen2.5:7b"}]), patch("promptbench.query_pipeline.providers.ollama_provider.OllamaProvider.generate_response") as generate:
            at.sidebar.selectbox[1].select("ollama").run(timeout=60)
        self.assertEqual(len(at.exception), 0)
        generate.assert_not_called()
        self.assertTrue(any("Run / refresh audit" in message.value for message in at.info))


if __name__ == "__main__":
    unittest.main()
