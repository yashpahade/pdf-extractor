"""Pydantic schemas for chat API request/response models."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Q&A request over a specific document."""

    query: str
    document_id: int


class ChatResponse(BaseModel):
    """Q&A response with answer, context, and usage stats."""

    answer: str
    context_chunks: list[str]
    tokens_used: int = 0
    provider: str = ""
