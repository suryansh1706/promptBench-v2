"""
Google Gemini API Provider for PromptBench.
Uses standard HTTP/REST with exponential backoff, full jitter, and detailed error parsing.
"""

import os
import json
import time
import random
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from .base import BaseLLMProvider
from ...core.types import ModelResponse


class GeminiProvider(BaseLLMProvider):
    """
    Direct REST integration with Google Gemini (user-selected model IDs).
    Implements exponential backoff with full jitter to handle rate limits (HTTP 429).
    """

    def __init__(
        self,
        model_name: str = "gemini-3.5-flash-lite",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        seed: int = 42,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        max_tokens: int = 512,
    ):
        super().__init__(model_name=model_name, temperature=temperature, seed=seed)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_tokens = max_tokens

    def generate_response(
        self,
        prompt_text: str,
        system_prompt: str,
        prompt_id: str,
    ) -> ModelResponse:
        """Sends request to Google Gemini API with exponential backoff and jitter."""
        if not self.api_key:
            raise ValueError(
                "Gemini API key is missing. Set GEMINI_API_KEY environment variable "
                "or pass api_key to GeminiProvider."
            )

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt_text}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "seed": self.seed,
            }
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
            "User-Agent": "PromptBench-Auditor/1.0",
        }

        start_time = time.time()
        last_error = None

        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(endpoint, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=35) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    
                    # Extract candidate text
                    candidates = resp_data.get("candidates", [])
                    raw_text = ""
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        raw_text = "".join(p.get("text", "") for p in parts)
                    elif resp_data.get("promptFeedback", {}).get("blockReason"):
                        block_reason = resp_data["promptFeedback"]["blockReason"]
                        raw_text = f"BLOCKED: Prompt was filtered by safety filters ({block_reason})."
                    else:
                        raw_text = "ERROR: No response candidates returned."

                    latency_ms = (time.time() - start_time) * 1000.0
                    decision, score = self.parse_decision_and_score(raw_text)
                    finish_reason = candidates[0].get("finishReason") if candidates else None
                    error = raw_text if raw_text.startswith(("ERROR:", "BLOCKED:")) else None
                    if finish_reason == "MAX_TOKENS":
                        error = "Generation stopped at the output token limit; response is incomplete."

                    return ModelResponse(
                        response_id=f"gemini_{prompt_id}_{int(time.time()*1000)}",
                        prompt_id=prompt_id,
                        provider="gemini",
                        model_name=self.model_name,
                        raw_text=raw_text,
                        extracted_decision=decision,
                        extracted_score=score,
                        latency_ms=latency_ms,
                        temperature=self.temperature,
                        seed=self.seed,
                        metadata={"attempt": attempt + 1, "usage": resp_data.get("usageMetadata", {}),
                                  "requested_model": self.model_name, "model_version": resp_data.get("modelVersion"),
                                  "finish_reason": finish_reason, "error": error},
                    )

            except urllib.error.HTTPError as e:
                error_body = ""
                try:
                    error_body = e.read().decode("utf-8", errors="ignore")
                    parsed_err = json.loads(error_body)
                    if "error" in parsed_err and "message" in parsed_err["error"]:
                        error_body = parsed_err["error"]["message"]
                except Exception:
                    pass
                last_error = f"HTTP {e.code}: {e.reason} ({error_body})" if error_body else f"HTTP {e.code}: {e.reason}"

                # Break immediately for auth or bad request errors (no retry needed)
                if e.code in (400, 401, 403, 404):
                    break

                backoff_cap = min(self.max_delay, self.base_delay * (2 ** attempt))
                sleep_duration = random.uniform(0, backoff_cap)
                if attempt + 1 < self.max_retries:
                    time.sleep(sleep_duration)

            except (urllib.error.URLError, TimeoutError) as e:
                last_error = str(e)
                backoff_cap = min(self.max_delay, self.base_delay * (2 ** attempt))
                sleep_duration = random.uniform(0, backoff_cap)
                if attempt + 1 < self.max_retries:
                    time.sleep(sleep_duration)

            except Exception as e:
                last_error = str(e)
                break

        # Fallback failure response
        latency_ms = (time.time() - start_time) * 1000.0
        return ModelResponse(
            response_id=f"gemini_err_{prompt_id}",
            prompt_id=prompt_id,
            provider="gemini",
            model_name=self.model_name,
            raw_text=f"Gemini API Error: {str(last_error)}",
            extracted_decision="ERROR",
            extracted_score=None,
            latency_ms=latency_ms,
            temperature=self.temperature,
            seed=self.seed,
            metadata={"error": str(last_error)},
        )
