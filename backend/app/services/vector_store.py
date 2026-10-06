"""ChromaDB vector store — stores document chunks for semantic retrieval."""

import logging

from chromadb import ClientAPI, Collection, PersistentClient
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages a ChromaDB collection for document chunk embeddings."""

    def __init__(self) -> None:
        self._client: ClientAPI | None = None
        self._collection: Collection | None = None

    def initialize(self) -> None:
        """Create/connect to persistent ChromaDB."""
        settings = get_settings()
        settings.chroma_persist_directory.mkdir(parents=True, exist_ok=True)
        self._client = PersistentClient(
            path=str(settings.chroma_persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB initialized at %s", settings.chroma_persist_directory)

    def heartbeat(self) -> bool:
        """Check if ChromaDB is responsive."""
        if self._client is None:
            raise RuntimeError("Vector store has not been initialized")
        return self._client.heartbeat() > 0

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            raise RuntimeError("Vector store has not been initialized")
        return self._collection

    def add_chunks(
        self,
        doc_id: int,
        chunks: list[str],
        chunk_ids: list[str],
    ) -> None:
        """Add document chunks to the vector store.

        ChromaDB will auto-embed using its default sentence-transformer model.
        """
        if not chunks:
            return

        metadatas = [{"document_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

        self.collection.add(
            ids=chunk_ids,
            documents=chunks,
            metadatas=metadatas,
        )
        logger.info("Added %d chunks for document %d to ChromaDB", len(chunks), doc_id)

    def query_similar(
        self,
        query: str,
        doc_id: int | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Find the most similar chunks to a query."""
        where_filter = {"document_id": doc_id} if doc_id is not None else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )

        chunks: list[dict] = []
        if results["documents"] and results["documents"][0]:
            for i, doc_text in enumerate(results["documents"][0]):
                chunks.append({
                    "id": results["ids"][0][i] if results["ids"] else "",
                    "content": doc_text,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })

        return chunks

    def delete_document(self, doc_id: int) -> None:
        """Delete all chunks for a document from ChromaDB."""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": doc_id},
            )
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(
                    "Deleted %d chunks for document %d from ChromaDB",
                    len(results["ids"]),
                    doc_id,
                )
        except Exception:
            logger.exception("Failed to delete chunks for document %d", doc_id)


# Module-level singleton
vector_store = VectorStore()
