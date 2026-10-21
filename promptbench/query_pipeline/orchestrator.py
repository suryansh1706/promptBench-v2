"""
Query Orchestrator for PromptBench.
Manages concurrent batch querying, progress reporting, and deterministic cache lookups.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from typing import List, Dict, Optional, Callable, Any
import time
from .providers.base import BaseLLMProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.mock_provider import MockLLMProvider
from .providers.ollama_provider import OllamaProvider
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
                max_tokens=config.provider.max_tokens,
            )
        elif provider_name == "openai":
            provider = OpenAIProvider(
                model_name=config.provider.model_name,
                temperature=config.provider.temperature,
                seed=config.provider.seed,
                max_retries=config.max_retries,
                base_delay=config.backoff_base_seconds,
                max_delay=config.backoff_max_seconds,
                max_tokens=config.provider.max_tokens,
            )
        elif provider_name == "ollama":
            provider = OllamaProvider(
                model_name=config.provider.model_name, temperature=config.provider.temperature,
                seed=config.provider.seed, max_tokens=config.provider.max_tokens,
                base_url=getattr(config.provider, "ollama_base_url", None),
                timeout=getattr(config.provider, "request_timeout_seconds", 180.0),
            )
            provider.validate_model_available()
        elif provider_name == "mock":
            provider = MockLLMProvider(
                model_name=config.provider.model_name,
                temperature=config.provider.temperature,
                seed=config.provider.seed,
            )

        else:
            raise ValueError(f"Unknown provider: {provider_name}")

        # Optimize concurrency: live APIs use 3 concurrent workers to respect free tier RPM limits
        effective_workers = (1 if isinstance(provider, OllamaProvider) else
                             config.max_concurrency if isinstance(provider, MockLLMProvider) else min(config.max_concurrency, 3))

        return cls(
            provider=provider,
            cache=cache,
            max_workers=effective_workers,
        )

    def _query_single_prompt(self, prompt: PerturbedPrompt) -> ModelResponse:
        """Processes a single prompt through cache lookup or provider query."""
        # 1. Check cache if available
        cache_key = None
        if self.cache and not prompt.metadata.get("bypass_cache", False):
            cache_key = self.cache.generate_key(
                rendered_prompt=prompt.rendered_prompt,
                system_prompt=prompt.system_prompt,
                provider=self.provider.__class__.__name__,
                model_name=self.provider.model_name,
                temperature=self.provider.temperature,
                seed=self.provider.seed,
            )
            cached_resp = self.cache.get(cache_key)
            if cached_resp:
                return replace(cached_resp, prompt_id=prompt.prompt_id)

        # 2. Invoke provider
        response = self.provider.generate_response(
            prompt_text=prompt.rendered_prompt,
            system_prompt=prompt.system_prompt,
            prompt_id=prompt.prompt_id,
        )

        # 3. Store in cache
        if self.cache and cache_key and response.extracted_decision != "ERROR" and not response.metadata.get("error"):
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
                resp = self._safe_query(p)
                responses[p.prompt_id] = resp
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total, resp)
            return responses

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_prompt = {
                executor.submit(self._safe_query, p): p for p in prompts
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
                    )
                
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total, responses[prompt.prompt_id])

        return responses

    def _safe_query(self, prompt: PerturbedPrompt) -> ModelResponse:
        try:
            return self._query_single_prompt(prompt)
        except Exception as error:
            return ModelResponse(
                response_id=f"error_{prompt.prompt_id}", prompt_id=prompt.prompt_id,
                provider=self.provider.__class__.__name__, model_name=self.provider.model_name,
                raw_text=f"Request failed: {error}", extracted_decision="ERROR",
                metadata={"error": str(error)},
            )
