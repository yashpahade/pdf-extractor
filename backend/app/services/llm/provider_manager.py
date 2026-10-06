"""Smart LLM routing with automatic failover between Groq and Gemini."""

import asyncio
import logging
from dataclasses import dataclass, field

from app.services.llm.base import LLMProvider, LLMResponse
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """Aggregated usage across all calls in a pipeline run."""
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_latency_ms: int = 0
    calls: list[LLMResponse] = field(default_factory=list)

    def record(self, response: LLMResponse) -> None:
        self.total_prompt_tokens += response.prompt_tokens
        self.total_completion_tokens += response.completion_tokens
        self.total_latency_ms += response.latency_ms
        self.calls.append(response)

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def providers_used(self) -> str:
        providers = {c.provider for c in self.calls}
        return ",".join(sorted(providers))


class ProviderManager:
    """Routes LLM tasks to the optimal provider with automatic failover.

    Strategy:
    - Map phase (chunk summaries): Groq first (fast, free) → Gemini fallback
    - Reduce phase (final merge): Gemini first (quality) → Groq fallback
    - Image description: Gemini only (multimodal)
    - Chat/Q&A: Groq first (speed) → Gemini fallback
    """

    def __init__(self) -> None:
        self._groq = GroqProvider()
        self._gemini = GeminiProvider()
        self._semaphore = asyncio.Semaphore(2)  # 2 concurrent calls (1 for each API key)

    async def map_summarize(
        self, chunks: list[str], instruction: str | None = None
    ) -> tuple[list[str], UsageStats]:
        """Summarize each chunk sequentially to respect rate limits."""
        stats = UsageStats()

        async def _summarize_one(chunk: str) -> str:
            async with self._semaphore:
                # Add delay between map calls to pace requests
                await asyncio.sleep(2)
                return await self._with_failover(
                    primary=self._groq,
                    fallback=self._gemini,
                    method="summarize",
                    stats=stats,
                    text=chunk,
                    instruction=instruction,
                )

        summaries = []
        for c in chunks:
            try:
                res = await _summarize_one(c)
                summaries.append(res)
            except Exception as e:
                logger.error("Chunk failed: %s", e)
                summaries.append("[Chunk could not be summarized due to API limits]")

        return summaries, stats

    async def reduce_summarize(
        self, partial_summaries: list[str], instruction: str | None = None
    ) -> tuple[str, UsageStats]:
        """Merge partial summaries into a final summary using Gemini."""
        stats = UsageStats()
        combined = "\n\n---\n\n".join(
            f"**Section {i + 1}:**\n{s}" for i, s in enumerate(partial_summaries)
        )

        reduce_instruction = (
            instruction
            or (
                "You are given multiple section summaries of a document. "
                "Merge them into a single, coherent, well-structured summary. "
                "Remove redundancy, maintain logical flow, and use markdown "
                "formatting. The final summary should read as a standalone document."
            )
        )

        content = await self._with_failover(
            primary=self._gemini,
            fallback=self._groq,
            method="summarize",
            stats=stats,
            text=combined,
            instruction=reduce_instruction,
        )

        return content, stats

    async def chat_with_context(
        self, query: str, context: str
    ) -> tuple[str, UsageStats]:
        """Answer a question using retrieved context."""
        stats = UsageStats()

        content = await self._with_failover(
            primary=self._groq,
            fallback=self._gemini,
            method="chat",
            stats=stats,
            query=query,
            context=context,
        )

        return content, stats

    async def describe_image(
        self, image_bytes: bytes, media_type: str
    ) -> tuple[str, UsageStats]:
        """Extract text from an image using Gemini Vision."""
        stats = UsageStats()

        try:
            response = await self._gemini.describe_image(image_bytes, media_type)
            stats.record(response)
            return response.content, stats
        except Exception:
            logger.exception("Gemini image description failed")
            raise

    async def _with_failover(
        self,
        primary: LLMProvider,
        fallback: LLMProvider,
        method: str,
        stats: UsageStats,
        **kwargs,
    ) -> str:
        """Try primary provider, fall back to secondary on failure, with retries for rate limits."""
        for attempt in range(3):
            try:
                response = await getattr(primary, method)(**kwargs)
                stats.record(response)
                return response.content
            except Exception as exc:
                if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    logger.warning("%s hit Rate Limit (429). Waiting before retry %d", primary.name, attempt + 1)
                    await asyncio.sleep(10 * (attempt + 1))
                    continue
                logger.warning("%s failed on %s: %s", primary.name, method, exc)
                break  # Not a rate limit, break to fallback
        
        # If primary completely fails, try fallback
        for attempt in range(3):
            try:
                response = await getattr(fallback, method)(**kwargs)
                stats.record(response)
                return response.content
            except Exception as fallback_exc:
                if "429" in str(fallback_exc) or "RESOURCE_EXHAUSTED" in str(fallback_exc):
                    logger.warning("%s hit Rate Limit (429). Waiting before retry %d", fallback.name, attempt + 1)
                    await asyncio.sleep(10 * (attempt + 1))
                    continue
                logger.exception("Both providers failed for %s", method)
                raise Exception(f"{primary.name} failed | {fallback.name} failed with: {fallback_exc}")
        
        raise Exception(f"Both providers exhausted retries due to Rate Limits (429)")
