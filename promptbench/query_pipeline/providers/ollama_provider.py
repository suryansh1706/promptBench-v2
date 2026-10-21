"""Ollama REST provider for models already installed on a local server."""

import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .base import BaseLLMProvider
from ...core.types import ModelResponse


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name="qwen2.5:7b", temperature=0.0, seed=42,
                 base_url=None, max_tokens=512, timeout=180.0):
        super().__init__(model_name=model_name, temperature=temperature, seed=seed)
        self.base_url = (base_url or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
        if "://" not in self.base_url:
            self.base_url = "http://" + self.base_url
        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Ollama host must be an HTTP(S) server URL without credentials.")
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.model_digest = None

    def available_models(self):
        """Read installed tags; this never pulls or downloads a model."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload.get("models", [])
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise ValueError(f"Cannot connect to Ollama at {self.base_url}. Start `ollama serve` and try again.") from error

    def validate_model_available(self):
        models = self.available_models()
        requested = self.model_name if ":" in self.model_name else f"{self.model_name}:latest"
        for model in models:
            if model.get("name") in {self.model_name, requested} or model.get("model") in {self.model_name, requested}:
                self.model_digest = model.get("digest")
                return
        installed = ", ".join(model.get("name", "") for model in models) or "none"
        raise ValueError(f"Ollama model '{self.model_name}' is not installed. Installed models: {installed}. Select an installed tag; PromptBench does not download models.")

    def generate_response(self, prompt_text, system_prompt, prompt_id):
        payload = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt_text}],
            "stream": False,
            "think": False,
            "options": {"temperature": self.temperature, "seed": self.seed, "num_predict": self.max_tokens},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/chat", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data.get("error"):
                raise ValueError(data["error"])
            raw_text = data.get("message", {}).get("content") or ""
            if not raw_text.strip():
                raise ValueError("Ollama returned an empty answer. Increase the output token limit or use a non-thinking model.")
            decision, score = self.parse_decision_and_score(raw_text)
            finish_reason = data.get("done_reason")
            return ModelResponse(
                response_id=f"ollama_{prompt_id}_{time.time_ns()}", prompt_id=prompt_id,
                provider="ollama", model_name=data.get("model", self.model_name), raw_text=raw_text,
                extracted_decision=decision, extracted_score=score,
                latency_ms=(time.monotonic() - started) * 1000,
                temperature=self.temperature, seed=self.seed,
                metadata={"model_version": self.model_digest or data.get("model"),
                          "model_digest": self.model_digest, "requested_model": self.model_name,
                          "server_url": self.base_url, "think": False, "finish_reason": finish_reason,
                          "error": "Generation stopped at the output token limit; response is incomplete."
                          if finish_reason == "length" else None,
                          "usage": {"prompt_tokens": data.get("prompt_eval_count"), "completion_tokens": data.get("eval_count")},
                          "total_duration_ns": data.get("total_duration")},
            )
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as error:
            message = str(error)
            if isinstance(error, urllib.error.HTTPError):
                try:
                    message = json.loads(error.read().decode("utf-8")).get("error", message)
                except (ValueError, OSError):
                    pass
            return ModelResponse(
                response_id=f"ollama_error_{prompt_id}", prompt_id=prompt_id, provider="ollama",
                model_name=self.model_name, raw_text=f"Ollama request failed: {message}",
                extracted_decision="ERROR", temperature=self.temperature, seed=self.seed,
                latency_ms=(time.monotonic() - started) * 1000, metadata={"error": message},
            )
