"""End-to-end Map-Reduce document summarization pipeline."""

import logging
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.db.models.usage_log import UsageLog
from app.services.chunker import RecursiveCharacterSplitter
from app.services.llm.provider_manager import ProviderManager, UsageStats
from app.services.parser import document_parser, ParsedDocument
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)
settings = get_settings()


class SummarizationPipeline:
    """Orchestrates: Parse → Chunk → Map (Groq) → Reduce (Gemini) → Store."""

    def __init__(self) -> None:
        self._provider = ProviderManager()
        self._chunker = RecursiveCharacterSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    async def process_document(
        self, doc: Document, file_path: Path, session: AsyncSession
    ) -> None:
        """Full pipeline: parse, chunk, summarize, store."""
        start = time.time()
        total_stats = UsageStats()

        try:
            # Update status
            doc.status = "processing"
            await session.commit()

            # 1. Parse
            logger.info("Parsing document %d: %s", doc.id, doc.filename)
            parsed = document_parser.parse(file_path, doc.media_type)
            doc.page_count = parsed.page_count

            full_text = parsed.full_text

            # If image with no OCR text, use Gemini Vision
            if not full_text and doc.media_type.startswith("image/"):
                logger.info("Using Gemini Vision for image %d", doc.id)
                image_bytes = file_path.read_bytes()
                vision_text, vision_stats = await self._provider.describe_image(
                    image_bytes, doc.media_type
                )
                full_text = vision_text
                total_stats.total_prompt_tokens += vision_stats.total_prompt_tokens
                total_stats.total_completion_tokens += vision_stats.total_completion_tokens
                total_stats.total_latency_ms += vision_stats.total_latency_ms
                total_stats.calls.extend(vision_stats.calls)

            if not full_text:
                doc.status = "failed"
                doc.error_message = "No text could be extracted from the document."
                await session.commit()
                return

            # 2. Chunk
            text_chunks = self._chunker.split(full_text)
            logger.info("Document %d split into %d chunks", doc.id, len(text_chunks))

            # 3. Store chunks in DB and ChromaDB
            chunk_contents = [c.content for c in text_chunks]
            chunk_ids = [f"doc_{doc.id}_chunk_{c.index}" for c in text_chunks]

            # Store in ChromaDB for retrieval
            vector_store.add_chunks(
                doc_id=doc.id,
                chunks=chunk_contents,
                chunk_ids=chunk_ids,
            )

            # Store in SQLite
            for tc in text_chunks:
                db_chunk = Chunk(
                    document_id=doc.id,
                    chunk_index=tc.index,
                    content=tc.content,
                    token_count=len(tc.content) // 4,  # rough estimate
                    chroma_id=f"doc_{doc.id}_chunk_{tc.index}",
                )
                session.add(db_chunk)

            # 4. Summarize
            if len(text_chunks) <= 3:
                # Small document — direct summarize with Gemini
                logger.info("Small document %d — direct summarization", doc.id)
                combined = "\n\n".join(chunk_contents)
                summary, reduce_stats = await self._provider.reduce_summarize([combined])
                total_stats.total_prompt_tokens += reduce_stats.total_prompt_tokens
                total_stats.total_completion_tokens += reduce_stats.total_completion_tokens
                total_stats.total_latency_ms += reduce_stats.total_latency_ms
                total_stats.calls.extend(reduce_stats.calls)
            else:
                # Map-Reduce
                logger.info("Map-Reduce for document %d (%d chunks)", doc.id, len(text_chunks))

                # Map: parallel chunk summaries via Groq
                partial_summaries, map_stats = await self._provider.map_summarize(
                    chunk_contents
                )
                total_stats.total_prompt_tokens += map_stats.total_prompt_tokens
                total_stats.total_completion_tokens += map_stats.total_completion_tokens
                total_stats.total_latency_ms += map_stats.total_latency_ms
                total_stats.calls.extend(map_stats.calls)

                # Update chunk summaries in DB
                for i, ps in enumerate(partial_summaries):
                    # We'll update chunks later if needed
                    pass

                # Reduce: merge via Gemini
                summary, reduce_stats = await self._provider.reduce_summarize(
                    partial_summaries
                )
                total_stats.total_prompt_tokens += reduce_stats.total_prompt_tokens
                total_stats.total_completion_tokens += reduce_stats.total_completion_tokens
                total_stats.total_latency_ms += reduce_stats.total_latency_ms
                total_stats.calls.extend(reduce_stats.calls)

            # 5. Store results
            elapsed_ms = int((time.time() - start) * 1000)
            doc.summary = summary
            doc.status = "completed"
            doc.tokens_used = total_stats.total_tokens
            doc.provider_used = total_stats.providers_used
            doc.processing_time_ms = elapsed_ms

            # Log usage per call
            for call in total_stats.calls:
                usage_log = UsageLog(
                    document_id=doc.id,
                    provider=call.provider,
                    model=call.model,
                    prompt_tokens=call.prompt_tokens,
                    completion_tokens=call.completion_tokens,
                    task_type="summarize",
                )
                session.add(usage_log)

            await session.commit()
            logger.info(
                "Document %d summarized: %d tokens, %dms",
                doc.id,
                total_stats.total_tokens,
                elapsed_ms,
            )

        except Exception as exc:
            logger.exception("Summarization failed for document %d", doc.id)
            doc.status = "failed"
            doc.error_message = str(exc)[:500]
            await session.commit()


# Module-level singleton
summarization_pipeline = SummarizationPipeline()
