"""Presentation and UI checks, skipped when optional UI dependencies are absent."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.assertEqual(next(m.value for m in at.metric if m.label == "Scenario templates"), "4")

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
