"""Pydantic schemas for document API request/response models."""

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Single document with all metadata."""

    id: int
    filename: str
    media_type: str
    file_size_bytes: int
    status: str
    page_count: int | None = None
    summary: str | None = None
    error_message: str | None = None
    tokens_used: int = 0
    provider_used: str | None = None
    processing_time_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""

    documents: list[DocumentResponse]
    total: int


class ResummarizeRequest(BaseModel):
    """Optional custom instruction for re-summarization."""

    instruction: str | None = None
