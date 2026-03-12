"""Tests for text normalization module.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

from oraculus_di_auditor.normalize import chunk_text, normalize_document


def test_chunk_text_basic():
    """Test basic text chunking."""
    text = "A" * 1000
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert len(chunks) > 0
    assert chunks[0]["start"] == 0
    assert chunks[0]["length"] <= 100


def test_chunk_text_overlap():
    """Test that chunks overlap correctly."""
    text = "ABCDEFGHIJ" * 10  # 100 chars
    chunks = chunk_text(text, chunk_size=30, overlap=10)

    # Should have multiple chunks with overlap
    assert len(chunks) >= 3
    # Second chunk should start at (30 - 10) = 20
    assert chunks[1]["start"] == 20


def test_chunk_text_empty():
    """Test chunking empty text."""
    chunks = chunk_text("", chunk_size=100, overlap=10)
    # Empty text produces no chunks
    assert len(chunks) == 0


def test_normalize_document():
    """Test document normalization."""
    doc = {
        "id": "test-doc-1",
        "title": "Test Document",
        "text": "This is test text " * 50,  # About 900 chars
        "citations": ["42 U.S.C. 1983"],
    }

    normalized = normalize_document(doc)

    assert normalized["id"] == "test-doc-1"
    assert normalized["title"] == "Test Document"
    assert len(normalized["chunks"]) > 0
    assert normalized["chunk_count"] == len(normalized["chunks"])
    assert normalized["citations"] == ["42 U.S.C. 1983"]


def test_normalize_document_minimal():
    """Test normalizing document with minimal fields."""
    doc = {"text": "Short text"}

    normalized = normalize_document(doc)

    assert normalized["id"] == "unknown"
    assert normalized["title"] == ""
    assert normalized["text"] == "Short text"
    assert len(normalized["chunks"]) == 1
