"""Google Gemini LLM adapter using the google-genai SDK."""

import base64
import logging
import time

from google import genai
from google.genai import types

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


class GeminiProvider(LLMProvider):
    """Adapter for Google Gemini API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    @property
    def name(self) -> str:
        return "gemini"

    async def summarize(self, text: str, instruction: str | None = None) -> LLMResponse:
        system = instruction or SUMMARIZE_SYSTEM
        user_msg = f"Summarize the following text:\n\n{text}"

        return await self._call(system=system, user_parts=[user_msg])

    async def chat(self, query: str, context: str) -> LLMResponse:
        user_msg = f"Context:\n{context}\n\nQuestion: {query}"
        return await self._call(system=CHAT_SYSTEM, user_parts=[user_msg])

    async def describe_image(self, image_bytes: bytes, media_type: str) -> LLMResponse:
        """Use Gemini Vision to extract text from an image."""
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=media_type)
        text_part = (
            "Extract ALL text from this image. If it contains a document, "
            "reproduce the text content faithfully. If it is a diagram or photo, "
            "describe what you see in detail."
        )

        return await self._call(
            system="You are an expert OCR and image analysis assistant.",
            user_parts=[text_part, image_part],
        )

    async def _call(
        self, system: str, user_parts: list
    ) -> LLMResponse:
        start = time.time()

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_parts,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.3,
                    max_output_tokens=4096,
                ),
            )
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise

        content = response.text or ""
        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count if usage else 0
        completion_tokens = usage.candidates_token_count if usage else 0

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            provider="gemini",
            model=self._model,
            latency_ms=self._elapsed_ms(start),
        )
