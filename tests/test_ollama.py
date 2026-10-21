"""Ollama wire-format checks; these tests never load/download a real model."""
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from promptbench.core.config import PromptBenchConfig
from promptbench.query_pipeline.orchestrator import QueryOrchestrator
from promptbench.query_pipeline.providers.ollama_provider import OllamaProvider


def response(payload):
    result = MagicMock()
    result.read.return_value = json.dumps(payload).encode("utf-8")
    result.__enter__.return_value = result
    return result


class TestOllamaProvider(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_chat_payload_and_parsed_response(self, urlopen):
        urlopen.return_value = response({"model": "qwen2.5:7b", "message": {"content": "[DECISION: ACCEPT]\n[SCORE: 88/100]"}, "done": True, "done_reason": "stop", "prompt_eval_count": 50, "eval_count": 22})
        provider = OllamaProvider(model_name="qwen2.5:7b", base_url="http://127.0.0.1:11434", max_tokens=128)
        answer = provider.generate_response("Applicant", "Evaluator", "local_1")
        self.assertEqual(answer.provider, "ollama")
        self.assertEqual(answer.extracted_decision, "ACCEPT")
        self.assertEqual(answer.extracted_score, 88)
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertEqual(payload["options"], {"temperature": 0.0, "seed": 42, "num_predict": 128})
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(answer.metadata["usage"]["completion_tokens"], 22)
        urlopen.return_value = response({"model": "qwen2.5:7b", "message": {"content": "[DECISION: ACCEPT]"}, "done_reason": "length"})
        truncated = provider.generate_response("Applicant", "Evaluator", "local_truncated")
        self.assertIn("output token limit", truncated.metadata["error"])

    @patch("urllib.request.urlopen")
    def test_model_preflight_records_digest_without_download(self, urlopen):
        urlopen.return_value = response({"models": [{"name": "qwen2.5:7b", "digest": "model-sha"}]})
        provider = OllamaProvider(model_name="qwen2.5:7b", base_url="localhost:11434")
        provider.validate_model_available()
        self.assertEqual(provider.model_digest, "model-sha")
        self.assertEqual(urlopen.call_count, 1)
        self.assertTrue(urlopen.call_args.args[0].endswith("/api/tags"))

    @patch("urllib.request.urlopen")
    def test_missing_model_fails_without_downloading(self, urlopen):
        urlopen.return_value = response({"models": []})
        with self.assertRaisesRegex(ValueError, "not installed"):
            OllamaProvider(base_url="http://localhost:11434").validate_model_available()
        self.assertEqual(urlopen.call_count, 1)

    @patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused"))
    def test_stopped_server_has_actionable_message(self, urlopen):
        provider = OllamaProvider(base_url="http://localhost:11434")
        with self.assertRaisesRegex(ValueError, "ollama serve"):
            provider.available_models()
        result = provider.generate_response("Applicant", "Evaluator", "failed")
        self.assertEqual(result.extracted_decision, "ERROR")
        self.assertTrue(result.metadata["error"])

    @patch("urllib.request.urlopen")
    def test_empty_and_http_errors_are_not_valid_answers(self, urlopen):
        provider = OllamaProvider(base_url="http://localhost:11434")
        urlopen.return_value = response({"message": {"content": "", "thinking": "hidden reasoning"}})
        self.assertEqual(provider.generate_response("Applicant", "Evaluator", "empty").extracted_decision, "ERROR")
        urlopen.side_effect = urllib.error.HTTPError("http://localhost:11434/api/chat", 404, "Not Found", {}, io.BytesIO(b'{"error":"model missing"}'))
        result = provider.generate_response("Applicant", "Evaluator", "missing")
        self.assertEqual(result.metadata["error"], "model missing")

    @patch("urllib.request.urlopen")
    def test_factory_uses_sequential_local_queries(self, urlopen):
        urlopen.return_value = response({"models": [{"name": "qwen2.5:7b", "digest": "model-sha"}]})
        with tempfile.TemporaryDirectory() as directory:
            config = PromptBenchConfig(cache_dir=Path(directory))
            config.provider.provider_name = "ollama"
            config.provider.model_name = "qwen2.5:7b"
            config.max_concurrency = 8
            orchestrator = QueryOrchestrator.from_config(config)
            self.assertIsInstance(orchestrator.provider, OllamaProvider)
            self.assertEqual(orchestrator.max_workers, 1)


if __name__ == "__main__":
    unittest.main()
