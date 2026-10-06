"""Document API routes — upload, list, get, delete."""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.db.models.usage_log import UsageLog
from app.db.session import get_session, AsyncSessionLocal
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/bmp",
    "image/tiff",
}


async def _run_summarization(doc_id: int, file_path: Path) -> None:
    """Run summarization in a background task with its own DB session."""
    # Import here to avoid circular imports at module load
    from app.services.summarizer import summarization_pipeline

    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        if doc is None:
            logger.error("Document %d not found for summarization", doc_id)
            return
        await summarization_pipeline.process_document(doc, file_path, session)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Upload a document and start background summarization."""
    # Validate file type
    media_type = file.content_type or ""
    if media_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {media_type}. "
            f"Accepted: PDF, DOCX, PNG, JPG, WEBP.",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > settings.upload_max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file_size} bytes). "
            f"Maximum: {settings.upload_max_bytes} bytes.",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Save file to disk
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Create DB record first to get the ID
    doc = Document(
        filename=file.filename or "untitled",
        media_type=media_type,
        file_size_bytes=file_size,
        status="uploading",
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    # Save with ID-prefixed filename to avoid collisions
    safe_name = f"{doc.id}_{doc.filename}"
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)

    # Update status
    doc.status = "processing"
    await session.commit()

    logger.info(
        "Uploaded document %d: %s (%s, %d bytes)",
        doc.id,
        doc.filename,
        media_type,
        file_size,
    )

    # Start background summarization
    asyncio.create_task(_run_summarization(doc.id, file_path))

    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    session: AsyncSession = Depends(get_session),
) -> DocumentListResponse:
    """List all documents, newest first."""
    result = await session.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    docs = list(result.scalars().all())

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Get a single document by ID."""
    doc = await session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Delete a document and all associated data."""
    doc = await session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from ChromaDB
    vector_store.delete_document(doc_id)

    # Delete chunks and usage logs (cascade should handle this, but be explicit)
    chunks = await session.execute(
        select(Chunk).where(Chunk.document_id == doc_id)
    )
    for chunk in chunks.scalars():
        await session.delete(chunk)

    usage_logs = await session.execute(
        select(UsageLog).where(UsageLog.document_id == doc_id)
    )
    for log in usage_logs.scalars():
        await session.delete(log)

    # Delete uploaded file
    safe_name = f"{doc.id}_{doc.filename}"
    file_path = settings.upload_dir / safe_name
    if file_path.exists():
        file_path.unlink()

    # Delete document record
    await session.delete(doc)
    await session.commit()

    logger.info("Deleted document %d: %s", doc_id, doc.filename)
    return {"status": "deleted"}
