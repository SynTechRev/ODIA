"""Legacy document folder ingestion helpers (pre-C.O.N.T.R.A.).

Preserved for backward compatibility: oraculus_di_auditor.ingest.ingest_folder
was previously served by a top-level ingest.py module. The C.O.N.T.R.A. Phase G
work promoted `ingest` to a package; this file carries the legacy implementation.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text_file(path: Path, jurisdiction: str = "unknown") -> dict:
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
    """Ingest documents from a folder and save as normalized JSON."""
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
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
                if "id" in j and "text" in j:
                    doc = j
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
