"""Abstract base for LLM providers."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    provider: str = ""
    model: str = ""
    latency_ms: int = 0

    def __post_init__(self) -> None:
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class LLMProvider(ABC):
    """Interface that every LLM provider adapter must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'groq', 'gemini')."""

    @abstractmethod
    async def summarize(self, text: str, instruction: str | None = None) -> LLMResponse:
        """Summarize the given text."""

    @abstractmethod
    async def chat(self, query: str, context: str) -> LLMResponse:
        """Answer a question given context text."""

    @abstractmethod
    async def describe_image(self, image_bytes: bytes, media_type: str) -> LLMResponse:
        """Describe / extract text from an image (multimodal)."""

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        return int((time.time() - start) * 1000)
