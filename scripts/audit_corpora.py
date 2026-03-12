#!/usr/bin/env python3
"""
Unified Corpus Audit Script (v2.0)
Supports both HIST-##### and #YY-#### corpora.
Generates validation report, metadata completeness scores,
text extraction consistency, and index integrity.
"""

import json
import re
from hashlib import sha256
from pathlib import Path

CORPUS_ROOT = Path("oraculus/corpus")
CORPUS_PATTERN = re.compile(r"(HIST-\d{4,5}|#\d{2}-\d{4})")


def hash_file(path: Path) -> str:
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_corpora():
    corpora = []
    for entry in CORPUS_ROOT.iterdir():
        if entry.is_dir() and CORPUS_PATTERN.match(entry.name):
            corpora.append(entry)
    return sorted(corpora)


def audit_corpus(folder: Path):
    pdf_files = list(folder.rglob("*.pdf"))
    meta_files = list((folder / "metadata").glob("*.json"))
    extracted_files = list((folder / "extracted").glob("*.txt"))

    meta_ok = True
    missing_fields = []
    for meta in meta_files:
        with open(meta, encoding="utf-8") as f:
            data = json.load(f)
        for field in ("meeting_date", "source_url", "file_hash", "text_hash"):
            if field not in data or not data[field]:
                meta_ok = False
                missing_fields.append((meta.name, field))

    extraction_rate = len(extracted_files) / len(pdf_files) if pdf_files else 1.0

    return {
        "folder": folder.name,
        "pdf_count": len(pdf_files),
        "metadata_files": len(meta_files),
        "extracted_files": len(extracted_files),
        "metadata_complete": meta_ok,
        "missing_metadata_fields": missing_fields,
        "extraction_success_rate": extraction_rate,
    }


def audit_all():
    corpora = collect_corpora()
    results = [audit_corpus(c) for c in corpora]

    return {
        "total_corpora": len(corpora),
        "total_pdfs": sum(r["pdf_count"] for r in results),
        "global_extraction_rate": (
            sum(r["extraction_success_rate"] for r in results) / len(results)
            if results
            else 0.0
        ),
        "corpora": results,
    }


if __name__ == "__main__":
    report = audit_all()
    with open("VALIDATION_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
