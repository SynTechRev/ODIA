"""Tests for ingestion engine (Phase 4).

Tests document ingestion, text extraction, and metadata generation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from oraculus_di_auditor.ingestion import (
    compute_file_hash,
    compute_text_hash,
    extract_text_from_file,
    extract_text_from_html,
    extract_text_from_html_file,
    ingest_document,
    ingest_text,
    segment_text,
)

try:
    from oraculus_di_auditor.ingestion import extract_text_from_pdf

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def test_extract_text_from_html():
    """Test HTML text extraction."""
    html = """
    <html>
    <head><title>Test</title></head>
    <body>
        <h1>Header</h1>
        <p>This is a paragraph.</p>
        <script>alert('test');</script>
        <p>Another paragraph.</p>
    </body>
    </html>
    """

    text = extract_text_from_html(html)
    assert "Header" in text
    assert "This is a paragraph." in text
    assert "Another paragraph." in text
    assert "alert" not in text  # Script content should be excluded


def test_extract_text_from_html_file():
    """Test HTML file text extraction."""
    html_content = (
        "<html><body><h1>Test Document</h1><p>Content here.</p></body></html>"
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        temp_path = f.name

    try:
        text = extract_text_from_html_file(temp_path)
        assert "Test Document" in text
        assert "Content here." in text
    finally:
        Path(temp_path).unlink()


def test_extract_text_from_file():
    """Test plain text file extraction."""
    content = "This is a test document.\nWith multiple lines.\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        text = extract_text_from_file(temp_path)
        assert text == content
        assert "test document" in text
        assert "multiple lines" in text
    finally:
        Path(temp_path).unlink()


def test_extract_text_from_file_not_found():
    """Test error handling for non-existent file."""
    with pytest.raises(FileNotFoundError):
        extract_text_from_file("/nonexistent/file.txt")


def test_segment_text_short():
    """Test text segmentation with short text."""
    text = "Short text that doesn't need segmentation."
    segments = segment_text(text, max_length=100)

    assert len(segments) == 1
    assert segments[0] == text


def test_segment_text_long():
    """Test text segmentation with long text."""
    # Create text longer than max_length
    text = "Sentence one. " * 200  # ~2800 characters
    segments = segment_text(text, max_length=1000, overlap=100)

    assert len(segments) > 1
    assert all(len(seg) <= 1100 for seg in segments)  # Allow for overlap
    # Check overlap - last part of one segment should appear in next
    assert segments[0][-50:] in segments[1] or segments[0][-100:] in segments[1]


def test_segment_text_at_sentence_boundaries():
    """Test that segmentation respects sentence boundaries."""
    text = "First sentence. " + ("Middle sentence. " * 100) + "Last sentence."
    segments = segment_text(text, max_length=500)

    # All segments should end with a period (sentence boundary)
    for seg in segments[:-1]:  # All but last (which may not end with period)
        assert seg.rstrip().endswith(".")


def test_compute_text_hash():
    """Test text hash computation."""
    text = "Test content for hashing."
    hash1 = compute_text_hash(text)

    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 produces 64-character hex string

    # Same text should produce same hash
    hash2 = compute_text_hash(text)
    assert hash1 == hash2

    # Different text should produce different hash
    hash3 = compute_text_hash("Different content.")
    assert hash1 != hash3


def test_compute_file_hash():
    """Test file hash computation."""
    content = "File content for hashing."

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        hash1 = compute_file_hash(temp_path)

        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256

        # Same file should produce same hash
        hash2 = compute_file_hash(temp_path)
        assert hash1 == hash2
    finally:
        Path(temp_path).unlink()


def test_compute_file_hash_not_found():
    """Test error handling for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash("/nonexistent/file.txt")


def test_ingest_text():
    """Test ingesting raw text."""
    text = "This is test content for ingestion. Multiple sentences here."
    result = ingest_text(text, title="Test Document", author="Test Author")

    assert result["text"] == text
    assert isinstance(result["segments"], list)
    assert len(result["segments"]) >= 1
    assert isinstance(result["metadata"], dict)

    # Check metadata
    metadata = result["metadata"]
    assert metadata["source_path"] == "direct-text"
    assert metadata["format"] == "txt"
    assert "hash" in metadata
    assert "ingestion_timestamp" in metadata
    assert metadata["char_count"] == len(text)
    assert metadata["segment_count"] == len(result["segments"])
    assert metadata["title"] == "Test Document"
    assert metadata["author"] == "Test Author"


def test_ingest_text_segmentation():
    """Test that ingest_text properly segments long text."""
    long_text = "This is a sentence. " * 200
    result = ingest_text(long_text)

    assert len(result["segments"]) > 1
    assert result["metadata"]["segment_count"] > 1


def test_ingest_document_txt():
    """Test ingesting plain text document."""
    content = "Document content for testing.\nMultiple lines.\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = ingest_document(temp_path, document_type="test")

        assert result["text"] == content
        assert len(result["segments"]) >= 1

        metadata = result["metadata"]
        assert metadata["format"] == "txt"
        assert metadata["file_name"] == Path(temp_path).name
        assert "file_size_bytes" in metadata
        assert "hash" in metadata
        assert metadata["document_type"] == "test"
    finally:
        Path(temp_path).unlink()


def test_ingest_document_html():
    """Test ingesting HTML document."""
    html = "<html><body><h1>Test</h1><p>Content</p></body></html>"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        temp_path = f.name

    try:
        result = ingest_document(temp_path)

        assert "Test" in result["text"]
        assert "Content" in result["text"]
        assert result["metadata"]["format"] == "html"
    finally:
        Path(temp_path).unlink()


def test_ingest_document_not_found():
    """Test error handling for non-existent document."""
    with pytest.raises(FileNotFoundError):
        ingest_document("/nonexistent/document.txt")


def test_ingest_document_unsupported_format():
    """Test that unsupported binary formats can still be attempted as text."""
    # Create a binary file
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
        f.write(b"\x00\x01\x02\x03")
        temp_path = f.name

    try:
        # Binary files will be read with 'replace' error handling
        # so they won't raise an error, just produce garbled text
        result = ingest_document(temp_path)
        # Should succeed but with garbled/replaced content
        assert result["metadata"]["format"] == "txt"
    finally:
        Path(temp_path).unlink()


@pytest.mark.skipif(not PDF_AVAILABLE, reason="PyPDF not available")
def test_extract_text_from_pdf_not_found():
    """Test error handling for non-existent PDF."""
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf("/nonexistent/document.pdf")


def test_ingest_document_with_custom_metadata():
    """Test that custom metadata is preserved."""
    content = "Test content."

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        result = ingest_document(
            temp_path,
            title="Custom Title",
            author="Author Name",
            jurisdiction="federal",
            custom_field="custom_value",
        )

        metadata = result["metadata"]
        assert metadata["title"] == "Custom Title"
        assert metadata["author"] == "Author Name"
        assert metadata["jurisdiction"] == "federal"
        assert metadata["custom_field"] == "custom_value"
    finally:
        Path(temp_path).unlink()


def test_html_extractor_ignores_scripts_and_styles():
    """Test that HTML extractor properly filters out scripts and styles."""
    html = """
    <html>
    <head>
        <style>body { color: red; }</style>
        <script>console.log('test');</script>
    </head>
    <body>
        <p>Visible content</p>
        <script>alert('Should not appear');</script>
        <style>.test { display: none; }</style>
    </body>
    </html>
    """

    text = extract_text_from_html(html)
    assert "Visible content" in text
    assert "color: red" not in text
    assert "console.log" not in text
    assert "alert" not in text
    assert "display: none" not in text
