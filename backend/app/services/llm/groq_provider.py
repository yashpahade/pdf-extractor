"""Groq LLM adapter using the official groq SDK."""

import logging
import time

from groq import AsyncGroq, APIError

from app.core.config import get_settings
from app.services.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

SUMMARIZE_SYSTEM = (
    "You are an expert document summarizer. Produce a clear, well-structured "
    "summary that captures all key points. Use markdown formatting with headings "
    "and bullet points where appropriate. Be concise but thorough."
)

CHAT_SYSTEM = (
    "You are a helpful assistant. Answer the user's question based ONLY on the "
    "provided context. If the answer is not in the context, say so. "
    "Be precise and cite relevant parts of the context."
)


class GroqProvider(LLMProvider):
    """Adapter for the Groq API."""

    def __init__(self) -> None:
        settings = get_settings()
        keys = [k.strip() for k in settings.groq_api_key.split(",") if k.strip()]
        if not keys:
            keys = ["dummy"]
        self._clients = [AsyncGroq(api_key=k) for k in keys]
        self._model = settings.groq_model
        self._current_index = 0

    def _get_client(self):
        client = self._clients[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._clients)
        return client

    @property
    def name(self) -> str:
        return "groq"

    async def summarize(self, text: str, instruction: str | None = None) -> LLMResponse:
        system = instruction or SUMMARIZE_SYSTEM
        user_msg = f"Summarize the following text:\n\n{text}"

        return await self._call(system=system, user=user_msg)

    async def chat(self, query: str, context: str) -> LLMResponse:
        user_msg = f"Context:\n{context}\n\nQuestion: {query}"
        return await self._call(system=CHAT_SYSTEM, user=user_msg)

    async def describe_image(self, image_bytes: bytes, media_type: str) -> LLMResponse:
        raise NotImplementedError("Groq does not support image input")

    async def _call(self, system: str, user: str) -> LLMResponse:
        start = time.time()
        try:
            response = await self._get_client().chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
        except APIError as exc:
            logger.error("Groq API error: %s", exc)
            raise

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            provider="groq",
            model=self._model,
            latency_ms=self._elapsed_ms(start),
        )
