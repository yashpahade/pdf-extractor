"""Recursive character text splitter — no external dependency."""

from dataclasses import dataclass


@dataclass
class TextChunk:
    """A single chunk of text with its index."""
    index: int
    content: str
    char_count: int = 0

    def __post_init__(self) -> None:
        self.char_count = len(self.content)


class RecursiveCharacterSplitter:
    """Splits text into overlapping chunks using a hierarchy of separators."""

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def split(self, text: str) -> list[TextChunk]:
        """Split text into chunks with overlap."""
        if not text.strip():
            return []

        raw_chunks = self._split_recursive(text, self.separators)
        merged = self._merge_chunks(raw_chunks)

        return [
            TextChunk(index=i, content=chunk)
            for i, chunk in enumerate(merged)
            if chunk.strip()
        ]

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using the separator hierarchy."""
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            # No more separators — force split at chunk_size
            return self._force_split(text)

        sep = separators[0]
        remaining_seps = separators[1:]

        parts = text.split(sep)
        result: list[str] = []
        current = ""

        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    result.append(current)
                # If this single part is too large, split it further
                if len(part) > self.chunk_size:
                    result.extend(self._split_recursive(part, remaining_seps))
                    current = ""
                else:
                    current = part

        if current:
            result.append(current)

        return result

    def _force_split(self, text: str) -> list[str]:
        """Force split when no separator works."""
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if end < len(text) else end
        return chunks

    def _merge_chunks(self, chunks: list[str]) -> list[str]:
        """Merge small chunks and add overlap."""
        if not chunks:
            return []

        result: list[str] = []
        current = chunks[0]

        for chunk in chunks[1:]:
            if len(current) + len(chunk) <= self.chunk_size:
                current = f"{current}\n{chunk}"
            else:
                result.append(current.strip())
                # Add overlap from end of previous chunk
                overlap_text = current[-self.chunk_overlap:] if len(current) > self.chunk_overlap else ""
                current = f"{overlap_text}{chunk}" if overlap_text else chunk

        if current.strip():
            result.append(current.strip())

        return result
