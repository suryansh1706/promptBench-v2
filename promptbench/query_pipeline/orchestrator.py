"""
Query Orchestrator for PromptBench.
Manages concurrent batch querying, progress reporting, and deterministic cache lookups.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Any
import time
from .providers.base import BaseLLMProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.mock_provider import MockLLMProvider
from ..core.types import PerturbedPrompt, ModelResponse
from ..core.cache import ResponseCache
from ..core.config import PromptBenchConfig


class QueryOrchestrator:
    """
    Coordinates batch querying of LLMs with automatic deduplication,
    deterministic caching, and multi-threaded worker pools.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        cache: Optional[ResponseCache] = None,
        max_workers: int = 4,
    ):
        self.provider = provider
        self.cache = cache
        self.max_workers = max_workers

    @staticmethod
    def assert_acceptable_response_rate(responses: Dict[str, ModelResponse], threshold: float = 0.10) -> None:
        """Stop an audit when failed, empty, or refused outputs exceed the allowed fraction."""
        failed = sum(response.status != "ok" for response in responses.values())
        if responses and failed / len(responses) > threshold:
            raise RuntimeError(f"Audit stopped: {failed}/{len(responses)} responses were non-ok (> {threshold:.0%}).")

    @classmethod
    def from_config(cls, config: PromptBenchConfig) -> "QueryOrchestrator":
        """Factory method to construct orchestrator directly from PromptBenchConfig."""
        cache = ResponseCache(cache_dir=config.cache_dir) if config.enable_cache else None
        
        provider_name = config.provider.provider_name.lower()
        if provider_name == "gemini":
            provider = GeminiProvider(
                model_name=config.provider.model_name,
                temperature=config.provider.temperature,
                seed=config.provider.seed,
                max_retries=config.max_retries,
                base_delay=config.backoff_base_seconds,
                max_delay=config.backoff_max_seconds,
            )
        elif provider_name == "openai":
            provider = OpenAIProvider(
                model_name=config.provider.model_name,
                temperature=config.provider.temperature,
                seed=config.provider.seed,
                max_retries=config.max_retries,
                base_delay=config.backoff_base_seconds,
                max_delay=config.backoff_max_seconds,
            )
        else:
            provider = MockLLMProvider(
                model_name=config.provider.model_name,
                temperature=config.provider.temperature,
                seed=config.provider.seed,
            )

        # Optimize concurrency: live APIs use 3 concurrent workers to respect free tier RPM limits
        effective_workers = config.max_concurrency if isinstance(provider, MockLLMProvider) else min(config.max_concurrency, 3)

        return cls(
            provider=provider,
            cache=cache,
            max_workers=effective_workers,
        )

    def _query_single_prompt(self, prompt: PerturbedPrompt) -> ModelResponse:
        """Processes a single prompt through cache lookup or provider query."""
        # 1. Check cache if available
        cache_key = None
        if self.cache:
            cache_key = self.cache.generate_key(
                rendered_prompt=prompt.rendered_prompt,
                system_prompt=prompt.system_prompt,
                provider=self.provider.model_name.split("-")[0],
                model_name=self.provider.model_name,
                temperature=self.provider.temperature,
                seed=self.provider.seed,
                rep_index=int(prompt.metadata.get("rep_index", 0)),
            )
            cached_resp = self.cache.get(cache_key)
            if cached_resp:
                return cached_resp

        # 2. Invoke provider
        response = None
        attempts = max(1, min(int(getattr(self.provider, "max_retries", 3)), 3))
        last_error = None
        for _ in range(attempts):
            try:
                response = self.provider.generate_response(
                    prompt_text=prompt.rendered_prompt,
                    system_prompt=prompt.system_prompt,
                    prompt_id=prompt.prompt_id,
                )
            except Exception as exc:
                last_error = exc
                continue
            text = response.raw_text.strip().lower()
            if response.extracted_decision != "ERROR" and text and not text.startswith("api error"):
                break

        if response is None:
            response = ModelResponse(
                response_id=f"error_{prompt.prompt_id}", prompt_id=prompt.prompt_id,
                provider=getattr(self.provider, "provider_name", "unknown"),
                model_name=self.provider.model_name, raw_text=f"ERROR after retries: {last_error}",
                extracted_decision="ERROR", status="error",
            )

        lowered = response.raw_text.strip().lower()
        if not lowered:
            response.status = "empty"
        elif any(term in lowered for term in ("i cannot help", "i can't help", "i am unable to", "i cannot provide", "i cannot assist", "i can't assist", "unable to assist", "blocked:", "safety filters")):
            response.status = "refusal"
        elif response.extracted_decision == "ERROR" or lowered.startswith("fatal execution error"):
            response.status = "error"

        # 3. Store in cache
        if self.cache and cache_key and response.status == "ok":
            self.cache.set(cache_key, response)

        return response

    def execute_batch(
        self,
        prompts: List[PerturbedPrompt],
        progress_callback: Optional[Callable[[int, int, ModelResponse], None]] = None,
    ) -> Dict[str, ModelResponse]:
        """
        Executes batch queries concurrently across prompts.
        
        Returns:
            Dictionary mapping prompt_id -> ModelResponse.
        """
        responses: Dict[str, ModelResponse] = {}
        total = len(prompts)
        completed_count = 0

        # Optimization: Sequential execution if mock provider (fast enough) or 1 worker
        if isinstance(self.provider, MockLLMProvider) or self.max_workers <= 1:
            for p in prompts:
                resp = self._query_single_prompt(p)
                responses[p.prompt_id] = resp
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total, resp)
            return responses

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_prompt = {
                executor.submit(self._query_single_prompt, p): p for p in prompts
            }

            for future in as_completed(future_to_prompt):
                prompt = future_to_prompt[future]
                try:
                    resp = future.result()
                    responses[prompt.prompt_id] = resp
                except Exception as e:
                    # Capture unhandled thread exceptions
                    responses[prompt.prompt_id] = ModelResponse(
                        response_id=f"fatal_err_{prompt.prompt_id}",
                        prompt_id=prompt.prompt_id,
                        provider="unknown",
                        model_name=self.provider.model_name,
                        raw_text=f"FATAL Execution Error: {str(e)}",
                        extracted_decision="ERROR",
                        extracted_score=None,
                        latency_ms=0.0,
                        status="error",
                    )
                
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total, responses[prompt.prompt_id])

        return responses
