"""Document Ingestion Engine for Oraculus-DI-Auditor (Phase 4).

Provides multi-format document ingestion, text extraction, and metadata generation.
Supports PDF, HTML, and plain text with document segmentation and hash generation.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None  # type: ignore

try:
    from pdf2image import convert_from_path  # type: ignore

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    convert_from_path = None  # type: ignore

try:
    import pytesseract  # type: ignore

    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None  # type: ignore

try:
    from html.parser import HTMLParser

    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    HTMLParser = object  # type: ignore

# Threshold below which pypdf's text-layer output is considered "empty"
# and the OCR fallback is attempted. Scanned PDFs typically return a few
# stray characters from image metadata; 100 non-whitespace chars is the
# point where a real text layer is almost certainly present.
_OCR_MIN_TEXT_LENGTH = 100


class HTMLTextExtractor(HTMLParser):  # type: ignore
    """Extract text content from HTML."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.ignore_tags = {"script", "style", "meta", "link"}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def get_text(self) -> str:
        return " ".join(self.text_parts)


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from PDF file.

    First attempts pypdf's native text-layer extraction. When that
    yields fewer than ``_OCR_MIN_TEXT_LENGTH`` non-whitespace characters
    the document is assumed to be scanned / image-only and the OCR
    fallback is invoked (``pdf2image`` + ``pytesseract``). If OCR
    libraries or binaries are unavailable the pypdf result (possibly
    empty) is returned without raising, so callers see graceful
    degradation rather than a hard failure on scanned documents.

    Args:
        file_path: Path to PDF file.

    Returns:
        Extracted text content, best-effort across the two strategies.

    Raises:
        ImportError: If pypdf itself is not installed.
        FileNotFoundError: If ``file_path`` does not exist.
    """
    if not PYPDF_AVAILABLE:
        raise ImportError(
            "PyPDF is required for PDF extraction. Install with: pip install pypdf"
        )

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    # Text-layer extraction via pypdf.
    text = ""
    try:
        reader = PdfReader(str(file_path))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(t for t in text_parts if t)
    except Exception as exc:  # noqa: BLE001 - fall through to OCR
        logger.warning("pypdf text-layer extraction failed for %s: %s", file_path, exc)

    # If the text layer is near-empty the PDF is likely scanned. Attempt
    # OCR via pdf2image + pytesseract. Requires Tesseract + Poppler
    # binaries, which bundled_binaries.configure_bundled_binaries() wires
    # up under the PyInstaller desktop bundle; otherwise they must be on
    # the system PATH.
    if len(text.strip()) < _OCR_MIN_TEXT_LENGTH:
        try:
            ocr_text = _ocr_pdf_fallback(file_path)
            if len(ocr_text.strip()) > len(text.strip()):
                return ocr_text
        except ImportError as exc:
            logger.info("OCR fallback unavailable for %s: %s", file_path, exc)
        except Exception as exc:  # noqa: BLE001 - never propagate OCR errors
            logger.warning("OCR fallback failed for %s: %s", file_path, exc)

    return text


def _ocr_pdf_fallback(file_path: Path) -> str:
    """Rasterise each PDF page and run Tesseract OCR over the images.

    Raises ImportError when either ``pdf2image`` or ``pytesseract`` is
    absent; the caller converts that into a graceful degradation.
    """
    if not (PDF2IMAGE_AVAILABLE and PYTESSERACT_AVAILABLE):
        raise ImportError(
            "OCR fallback requires pdf2image and pytesseract. "
            "Install with: pip install pdf2image pytesseract "
            "(also requires system Tesseract and Poppler binaries)"
        )
    poppler_path = os.environ.get("POPPLER_PATH") or None
    images = convert_from_path(str(file_path), dpi=300, poppler_path=poppler_path)
    return "\n\n".join(pytesseract.image_to_string(img) for img in images)


def extract_text_from_html(content: str) -> str:
    """Extract text from HTML content.

    Args:
        content: HTML string content

    Returns:
        Extracted text content
    """
    if not HTML_AVAILABLE:
        # Fallback to basic regex-based stripping when HTMLParser is unavailable
        # Note: This is a best-effort approach for simple HTML. Edge cases with
        # malformed tags (e.g., "</script\t\n>") may not be handled perfectly,
        # but this fallback is only used when the proper HTMLParser is unavailable.
        # For production use, ensure HTMLParser is available (it's in stdlib).
        # Security note: We're only extracting text for analysis, not executing
        # any code, so the risk from imperfect tag matching is minimal.
        text = re.sub(
            r"<script[^>]*>.*?</script\s*>",
            "",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(
            r"<style[^>]*>.*?</style\s*>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(r"<[^>]+>", " ", text)
        return " ".join(text.split())

    extractor = HTMLTextExtractor()
    extractor.feed(content)
    return extractor.get_text()


def extract_text_from_html_file(file_path: str | Path) -> str:
    """Extract text from HTML file.

    Args:
        file_path: Path to HTML file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"HTML file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    return extract_text_from_html(content)


def extract_text_from_file(file_path: str | Path) -> str:
    """Extract text from plain text file.

    Args:
        file_path: Path to text file

    Returns:
        File content

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    with open(file_path, encoding="utf-8", errors="replace") as f:
        return f.read()


def segment_text(text: str, max_length: int = 2000, overlap: int = 200) -> list[str]:
    """Segment text into chunks with overlap for analysis.

    Args:
        text: Text to segment
        max_length: Maximum length of each segment (default: 2000 chars)
        overlap: Overlap between segments (default: 200 chars)

    Returns:
        List of text segments
    """
    if len(text) <= max_length:
        return [text]

    segments = []
    start = 0

    while start < len(text):
        end = start + max_length

        # If this is not the last segment, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence ending within the last 200 chars
            last_part = text[max(start, end - 200) : end]
            sentence_end = max(
                last_part.rfind("."), last_part.rfind("!"), last_part.rfind("?")
            )

            if sentence_end >= 0:
                end = max(start, end - 200) + sentence_end + 1

        segments.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end

    return segments


def compute_file_hash(file_path: str | Path) -> str:
    """Compute SHA-256 hash of file.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of file hash

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def compute_text_hash(text: str) -> str:
    """Compute SHA-256 hash of text content.

    Args:
        text: Text content

    Returns:
        Hex digest of text hash
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ingest_document(file_path: str | Path, **metadata) -> dict[str, Any]:
    """Ingest a document file and extract text and metadata.

    This is the main entry point for document ingestion.
    Automatically detects file format and applies appropriate extraction.

    Args:
        file_path: Path to document file
        **metadata: Additional metadata fields to include

    Returns:
        Document dict with:
        {
            "text": str,  # Extracted text
            "segments": list[str],  # Text segments
            "metadata": {
                "source_path": str,
                "file_name": str,
                "file_size_bytes": int,
                "format": str,  # pdf, html, txt
                "hash": str,  # SHA-256 hash
                "ingestion_timestamp": str,  # ISO 8601
                "char_count": int,
                "segment_count": int,
                **metadata  # Any additional metadata passed
            }
        }

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect format from extension
    ext = file_path.suffix.lower()

    # Extract text based on format
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        format_name = "pdf"
    elif ext in [".html", ".htm"]:
        text = extract_text_from_html_file(file_path)
        format_name = "html"
    elif ext in [".txt", ".text", ".md"]:
        text = extract_text_from_file(file_path)
        format_name = "txt"
    else:
        # Try as plain text
        try:
            text = extract_text_from_file(file_path)
            format_name = "txt"
        except UnicodeDecodeError as e:
            raise ValueError(f"Unsupported file format: {ext}") from e

    # Segment text
    segments = segment_text(text)

    # Compute hash
    file_hash = compute_file_hash(file_path)

    # Build metadata
    doc_metadata = {
        "source_path": str(file_path.absolute()),
        "file_name": file_path.name,
        "file_size_bytes": file_path.stat().st_size,
        "format": format_name,
        "hash": file_hash,
        "ingestion_timestamp": datetime.now(UTC).isoformat(),
        "char_count": len(text),
        "segment_count": len(segments),
        **metadata,
    }

    return {
        "text": text,
        "segments": segments,
        "metadata": doc_metadata,
    }


def ingest_text(text: str, **metadata) -> dict[str, Any]:
    """Ingest raw text content (no file).

    Args:
        text: Text content to ingest
        **metadata: Additional metadata fields

    Returns:
        Document dict similar to ingest_document but without file-based metadata
    """
    # Segment text
    segments = segment_text(text)

    # Compute hash
    text_hash = compute_text_hash(text)

    # Build metadata
    doc_metadata = {
        "source_path": "direct-text",
        "format": "txt",
        "hash": text_hash,
        "ingestion_timestamp": datetime.now(UTC).isoformat(),
        "char_count": len(text),
        "segment_count": len(segments),
        **metadata,
    }

    return {
        "text": text,
        "segments": segments,
        "metadata": doc_metadata,
    }


__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_html",
    "extract_text_from_html_file",
    "extract_text_from_file",
    "segment_text",
    "compute_file_hash",
    "compute_text_hash",
    "ingest_document",
    "ingest_text",
]
