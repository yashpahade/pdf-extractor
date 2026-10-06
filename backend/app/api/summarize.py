"""Summarize API routes — re-summarize and status check."""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.document import Document
from app.db.session import get_session, AsyncSessionLocal
from app.schemas.document import DocumentResponse, ResummarizeRequest

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


async def _run_resummarization(doc_id: int, file_path: Path) -> None:
    """Run re-summarization in a background task."""
    from app.services.summarizer import summarization_pipeline

    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        if doc is None:
            return
        await summarization_pipeline.process_document(doc, file_path, session)


@router.post("/{doc_id}/resummarize", response_model=DocumentResponse)
async def resummarize_document(
    doc_id: int,
    body: ResummarizeRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Re-trigger summarization for an existing document."""
    doc = await session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status == "processing":
        raise HTTPException(
            status_code=409, detail="Document is already being processed"
        )

    # Reset state
    doc.status = "processing"
    doc.summary = None
    doc.error_message = None
    doc.tokens_used = 0
    doc.provider_used = None
    doc.processing_time_ms = None
    await session.commit()
    await session.refresh(doc)

    # Find the uploaded file
    safe_name = f"{doc.id}_{doc.filename}"
    file_path = settings.upload_dir / safe_name

    if not file_path.exists():
        doc.status = "failed"
        doc.error_message = "Original file not found on disk."
        await session.commit()
        raise HTTPException(status_code=404, detail="Original file not found")

    # Start background task
    asyncio.create_task(_run_resummarization(doc.id, file_path))

    return DocumentResponse.model_validate(doc)


@router.get("/{doc_id}/status", response_model=DocumentResponse)
async def document_status(
    doc_id: int,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Check the processing status of a document."""
    doc = await session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)
