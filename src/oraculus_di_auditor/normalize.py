"""Text normalization and chunking module.

Author: Marcus A. Sanchez
Date: 2025-11-12
Updated: 2025-11-13 (GitHub Copilot Agent - Phase 6)
"""

from typing import Any


def chunk_text(
    text: str, chunk_size: int = 2000, overlap: int = 200
) -> list[dict[str, Any]]:
    """Break text into overlapping chunks with metadata.

    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters (default: 2000)
        overlap: Number of overlapping characters between chunks (default: 200)

    Returns:
        List of chunk dictionaries with text and metadata

    Note:
        - Default chunk_size increased to 2000 chars for better semantic coherence
        - Overlap ensures context preservation across chunk boundaries
        - Each chunk is stripped of leading/trailing whitespace
    """
    assert overlap < chunk_size, "Overlap must be less than chunk_size"

    chunks = []
    start = 0
    length = len(text)
    idx = 0

    while start < length:
        end = min(length, start + chunk_size)
        segment = text[start:end]

        # Trim whitespace for cleaner chunks
        segment = segment.strip()

        if segment:  # Only add non-empty chunks
            chunk = {
                "chunk_id": f"chunk_{idx}",
                "text": segment,
                "start": start,
                "end": end,
                "length": len(segment),
            }
            chunks.append(chunk)
            idx += 1

        # Move forward, ensuring we always make progress
        next_start = end - overlap
        if next_start <= start:
            # Prevent infinite loop: if overlap is too large, just move to end
            start = end
        else:
            start = next_start

    return chunks


def normalize_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Normalize a document into canonical format with chunks.

    Args:
        doc: Raw document dictionary

    Returns:
        Normalized document with chunks
    """
    text = doc.get("text", "")
    chunks = chunk_text(text)

    normalized = {
        "id": doc.get("id", "unknown"),
        "title": doc.get("title", ""),
        "source": doc.get("source", ""),
        "date": doc.get("date", ""),
        "text": text,
        "citations": doc.get("citations", []),
        "chunks": chunks,
        "chunk_count": len(chunks),
    }

    return normalized
