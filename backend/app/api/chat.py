"""Chat API route — Q&A over documents using ChromaDB retrieval + LLM."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document
from app.db.models.usage_log import UsageLog
from app.db.session import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm.provider_manager import ProviderManager
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat_with_document(
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Answer a question about a document using semantic retrieval + LLM."""
    # Verify document exists and is completed
    doc = await session.get(Document, body.document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not ready (status: {doc.status})",
        )

    # Retrieve relevant chunks from ChromaDB
    similar_chunks = vector_store.query_similar(
        query=body.query,
        doc_id=body.document_id,
        top_k=5,
    )

    if not similar_chunks:
        raise HTTPException(
            status_code=400,
            detail="No content found for this document. Try re-uploading.",
        )

    # Build context from retrieved chunks
    context_texts = [chunk["content"] for chunk in similar_chunks]
    context = "\n\n---\n\n".join(context_texts)

    # Get answer from LLM
    provider = ProviderManager()
    answer, stats = await provider.chat_with_context(
        query=body.query,
        context=context,
    )

    # Log usage
    for call in stats.calls:
        usage_log = UsageLog(
            document_id=body.document_id,
            provider=call.provider,
            model=call.model,
            prompt_tokens=call.prompt_tokens,
            completion_tokens=call.completion_tokens,
            task_type="chat",
        )
        session.add(usage_log)
    await session.commit()

    return ChatResponse(
        answer=answer,
        context_chunks=context_texts,
        tokens_used=stats.total_tokens,
        provider=stats.providers_used,
    )
