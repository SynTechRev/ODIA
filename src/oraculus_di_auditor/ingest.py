"""Document ingestion module for Oraculus DI Auditor.

Author: Marcus A. Sanchez
Date: 2025-11-12
Updated: 2025-11-13 (GitHub Copilot Agent - Phase 6)
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_text(text: str) -> str:
    """Generate SHA-256 hash of text for provenance tracking.

    Args:
        text: Input text to hash

    Returns:
        Hexadecimal SHA-256 hash string
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text_file(path: Path, jurisdiction: str = "unknown") -> dict:
    """Normalize a text file into canonical legal document format.

    Args:
        path: Path to the text file
        jurisdiction: Legal jurisdiction (e.g., 'federal', 'california')

    Returns:
        Normalized document dictionary conforming to legal_schema.json
    """
    text = path.read_text(encoding="utf-8")
    doc_id = f"{path.stem}"

    normalized: dict[str, Any] = {
        "id": doc_id,
        "title": path.stem.replace("_", " ").title(),
        "jurisdiction": jurisdiction,
        "source": str(path),
        "source_url": None,
        "version_date": None,
        "ingest_timestamp": datetime.now(UTC).isoformat(),
        "checksum": sha256_text(text),
        "citations": [],
        "metadata": {
            "processor_version": "0.1.0",
            "transformations": ["ingest", "normalize"],
            "original_format": path.suffix,
        },
        "text": text,
    }

    return normalized


def ingest_folder(
    src_dir: str, out_dir: str = "data/cases", jurisdiction: str = "unknown"
):
    """Ingest documents from a folder and save as normalized JSON.

    Args:
        src_dir: Source directory containing documents to ingest
        out_dir: Output directory for normalized JSON documents
        jurisdiction: Legal jurisdiction for the documents

    Returns:
        Number of documents processed
    """
    src = Path(src_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        print(f"Warning: Source directory {src_dir} does not exist")
        return 0

    processed = 0
    for f in src.glob("*"):
        if f.is_file() and f.suffix.lower() in [".txt", ".md"]:
            doc = normalize_text_file(f, jurisdiction=jurisdiction)
            output_path = out / f"{doc['id']}.json"
            output_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
            processed += 1
            print(f"Ingested: {f.name} -> {output_path.name}")
        elif f.is_file() and f.suffix.lower() == ".json":
            # If already JSON, validate and potentially enhance with provenance
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
                # Ensure required fields exist
                if "id" in j and "text" in j:
                    doc = j
                    # Add missing provenance fields if needed
                    if "checksum" not in doc and "text" in doc:
                        doc["checksum"] = sha256_text(doc["text"])
                    if "ingest_timestamp" not in doc:
                        doc["ingest_timestamp"] = datetime.now(UTC).isoformat()
                    output_path = out / f"{doc['id']}.json"
                    output_path.write_text(
                        json.dumps(doc, ensure_ascii=False, indent=2)
                    )
                    processed += 1
                    print(f"Ingested: {f.name} -> {output_path.name}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Skipping invalid JSON file {f.name}: {e}")

    print(f"Processed {processed} documents from {src_dir}")
    return processed
