"""Legislative document loader for Oraculus DI Auditor."""

import hashlib
import json
import pathlib
from datetime import UTC, datetime


def load_legislation(path: str, validate: bool = False) -> dict:
    """Load and validate legislative document from JSON, text, or PDF.

    Args:
        path: Path to the legislative document file
        validate: If True, validate against canonical schema (not implemented yet)

    Returns:
        Dictionary with loaded document data

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file format is not supported
    """
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No file found at {path}")

    # Read raw content for hashing
    raw_bytes = p.read_bytes()
    content_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Parse based on file extension
    if p.suffix == ".json":
        data = json.loads(raw_bytes.decode("utf-8"))
    elif p.suffix == ".txt":
        data = {"raw_text": raw_bytes.decode("utf-8")}
    elif p.suffix == ".pdf":
        data = _load_pdf(p)
    else:
        raise ValueError(f"Unsupported file format: {p.suffix}")

    # Add provenance metadata if not already present
    if "provenance" not in data:
        data["provenance"] = {
            "source": str(p.absolute()),
            "hash": content_hash,
            "verified_on": datetime.now(UTC).isoformat(),
        }

    return data


def _load_pdf(path: pathlib.Path) -> dict:
    """Extract text content from PDF file.

    Args:
        path: Path to the PDF file

    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        from pypdf import PdfReader  # type: ignore[reportMissingTypeStubs]
    except Exception as e:  # pragma: no cover - import-time error path
        raise ValueError("PDF support requires the 'pypdf' package") from e

    reader = PdfReader(str(path))
    text_content = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            text_content.append(f"[Page {page_num}]\n{text}")

    return {
        "raw_text": "\n\n".join(text_content),
        "metadata": {
            "num_pages": len(reader.pages),
            "format": "pdf",
        },
    }


def _populate_sections_and_optional_fields(normalized: dict, data: dict) -> None:
    """Populate sections and optional metadata fields into normalized dict."""
    if "sections" in data:
        normalized["sections"] = data["sections"]
    elif "raw_text" in data:
        normalized["sections"] = [{"section_id": "raw", "content": data["raw_text"]}]

    for field in ["authority", "jurisdiction", "version_date", "signatory"]:
        if field in data:
            normalized[field] = data[field]

    if "provenance" in data:
        normalized["provenance"] = data["provenance"]
    else:
        normalized["provenance"] = {
            "source": "unknown",
            "hash": hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest(),
            "verified_on": datetime.now(UTC).isoformat(),
        }

    for field in ["references", "metadata"]:
        if field in data:
            normalized[field] = data[field]


def normalize_document(data: dict, document_id: str | None = None) -> dict:
    """Normalize document to canonical schema format.

    Args:
        data: Raw document data
        document_id: Optional document ID (auto-generated if not provided)

    Returns:
        Normalized document following canonical legal schema
    """
    if document_id is None:
        content_str = json.dumps(data, sort_keys=True)
        hash_prefix = hashlib.sha256(content_str.encode()).hexdigest()[:12]
        document_id = f"doc-{hash_prefix}"

    normalized = {
        "document_id": document_id,
        "title": data.get("title", "Untitled Document"),
        "document_type": data.get("document_type", data.get("type", "act")),
    }

    _populate_sections_and_optional_fields(normalized, data)
    return normalized
