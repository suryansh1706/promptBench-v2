"""
Abstract Base Class and Parser for LLM Query Providers in PromptBench.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any
import re
import time
from ...core.types import ModelResponse, PerturbedPrompt


class BaseLLMProvider(ABC):
    """Abstract interface defining required methods for all LLM providers."""

    def __init__(self, model_name: str, temperature: float = 0.0, seed: int = 42):
        self.model_name = model_name
        self.temperature = temperature
        self.seed = seed

    @abstractmethod
    def generate_response(
        self,
        prompt_text: str,
        system_prompt: str,
        prompt_id: str,
    ) -> ModelResponse:
        """Executes a single prompt request against the underlying model."""
        pass

    @staticmethod
    def parse_decision_and_score(text: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Extracts structured decision categories and numerical scores from raw LLM output.
        Supported decision tokens: ACCEPT, REJECT, INTERVIEW, APPROVED, DENIED, COSIGNER, REVIEW
        """
        decision: Optional[str] = None
        score: Optional[float] = None

        # Only parse a single recognized structured token, or an explicit decision
        # line. Searching arbitrary prose for 'hire' misreads 'do not hire'.
        known = {"ACCEPT", "REJECT", "INTERVIEW", "APPROVED", "DENIED", "COSIGNER", "REVIEW", "PASS", "FAIL", "HIRE", "HOLD"}
        match_dec = re.search(r"\[DECISION:\s*([A-Za-z]+)\s*\]", text, re.IGNORECASE)
        if match_dec and match_dec.group(1).upper() in known:
            decision = match_dec.group(1).upper()
        else:
            labeled = re.search(r"(?:^|\n)\s*(?:decision|recommendation|determination)\s*:\s*([A-Za-z]+)\s*(?:[.\n]|$)", text, re.IGNORECASE)
            if labeled and labeled.group(1).upper() in known:
                decision = labeled.group(1).upper()
        pattern = r"(?:\[)?(?:SCORE|RATING):\s*([+-]?\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?))?"
        match_score = re.search(pattern, text, re.IGNORECASE)
        if match_score and not text[match_score.end():].lstrip().startswith("-"):
            value = float(match_score.group(1))
            denominator = float(match_score.group(2)) if match_score.group(2) else 100.0
            if denominator > 0 and 0 <= value <= denominator:
                score = value / denominator * 100.0
        return decision, score
