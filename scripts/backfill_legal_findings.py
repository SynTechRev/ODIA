"""Backfill legal findings for existing DB documents from source files.

Reads document source files (PDF, TXT, HTML) from a corpus directory,
matches them to DB Document rows by filename/title, runs L-1 through L-10
legal detectors, and persists findings as Anomaly rows.

This is a one-time catch-up script for corpora ingested before the odia_legal
pipeline was wired into analyze_document() (v3.8.0). Subsequent document
ingests produce legal findings automatically via the audit engine.

NOTE: The Document model does not store raw text — only metadata and
anomaly findings are kept. To backfill, you must supply the original
source files via --corpus-dir.

Usage:
    python scripts/backfill_legal_findings.py --corpus-dir /path/to/pdfs
    python scripts/backfill_legal_findings.py --corpus-dir /path/to/pdfs --dry-run
    python scripts/backfill_legal_findings.py --corpus-dir /path/to/pdfs --limit 100
    python scripts/backfill_legal_findings.py --corpus-dir /path/to/pdfs --force
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from odia_legal.pipeline import (  # noqa: E402
    LEGAL_DETECTOR_MODULES,
    run_legal_detectors,
)
from oraculus_di_auditor.db.models import Analysis, Anomaly, Document  # noqa: E402
from oraculus_di_auditor.db.session import get_db, init_db  # noqa: E402
from oraculus_di_auditor.ingestion.engine import ingest_document  # noqa: E402

LEGAL_LAYERS = {m.split(".")[-1] for m in LEGAL_DETECTOR_MODULES}

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".html", ".htm", ".xml", ".docx", ".doc"}

# Reuse bulk_ingest's text cache — avoids re-extracting all 9k+ PDFs
_CACHE_DIR = REPO_ROOT / ".text_cache"


def _cache_key(path: Path) -> str:
    stat = path.stat()
    raw = f"{path.resolve()}|{stat.st_mtime}|{stat.st_size}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _bulk_ingest_doc_id(path: Path) -> str:
    """Compute document_id using the same algorithm as bulk_ingest.py."""
    h = hashlib.sha256(str(path).encode()).hexdigest()[:12]
    return f"{path.stem[:40]}_{h}"


def _has_legal_findings(db, analysis_id: int) -> bool:
    return (
        db.query(Anomaly)
        .filter(Anomaly.analysis_id == analysis_id)
        .filter(Anomaly.layer.in_(LEGAL_LAYERS))
        .first()
        is not None
    )


def _find_matching_doc(db, file_path: Path) -> Document | None:
    """Find the DB Document matching this file.

    Priority:
    1. document_id computed from file path (matches bulk_ingest exactly)
    2. Normalized title match (bulk_ingest stores "Stem Words Title-Cased")
    3. LIKE fallback on first 30 chars of normalized stem
    """
    # 1. Exact document_id match — most reliable when corpus paths are identical
    doc_id = _bulk_ingest_doc_id(file_path)
    doc = db.query(Document).filter(Document.document_id == doc_id).first()
    if doc is not None:
        return doc

    # 2. Normalized title (bulk_ingest: stem.replace("_"," ").replace("-"," ").title())
    stem_norm = file_path.stem.replace("_", " ").replace("-", " ").title()
    doc = db.query(Document).filter(Document.title == stem_norm).first()
    if doc is not None:
        return doc

    # 3. LIKE fallback on the raw stem and normalized stem
    stem_raw = file_path.stem
    for pattern in (stem_norm[:40], stem_raw[:40], file_path.name):
        doc = db.query(Document).filter(Document.title.like(f"%{pattern[:30]}%")).first()
        if doc is not None:
            return doc
    return None


def _extract_text(file_path: Path) -> str | None:
    """Return text for file_path, using bulk_ingest's cache when available."""
    # Fast path — reuse already-extracted cache from bulk_ingest
    cache_file = _CACHE_DIR / (_cache_key(file_path) + ".txt")
    if cache_file.exists():
        text = cache_file.read_text(encoding="utf-8", errors="replace")
        return text.strip() or None

    # Slow path — call ingestion engine (re-extracts from source)
    try:
        doc = ingest_document(str(file_path))
        return doc.get("text") or doc.get("content") or ""
    except Exception:  # noqa: BLE001
        return None


def backfill(  # noqa: C901
    corpus_dir: Path,
    *,
    dry_run: bool = False,
    limit: int | None = None,
    force: bool = False,
    verbose: bool = True,
) -> dict[str, int]:
    """Run the backfill from source files in corpus_dir."""
    if not corpus_dir.exists():
        print(f"ERROR: corpus directory not found: {corpus_dir}", file=sys.stderr)
        sys.exit(1)

    init_db()
    stats = {
        "files_found": 0,
        "files_no_db_match": 0,
        "files_skipped_already_done": 0,
        "files_no_text": 0,
        "files_processed": 0,
        "findings_added": 0,
        "errors": 0,
    }

    source_files = sorted(
        f for f in corpus_dir.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if limit:
        source_files = source_files[:limit]

    stats["files_found"] = len(source_files)
    if verbose:
        print(f"Found {len(source_files)} source files in {corpus_dir}")
        if dry_run:
            print("DRY RUN — no changes will be written.")
        print()

    for i, file_path in enumerate(source_files, 1):
        with get_db() as db:
            doc = _find_matching_doc(db, file_path)
            if doc is None:
                stats["files_no_db_match"] += 1
                continue

            analysis = (
                db.query(Analysis)
                .filter(Analysis.document_id == doc.document_id)
                .order_by(Analysis.analysis_timestamp.desc())
                .first()
            )
            if analysis is None:
                stats["files_no_db_match"] += 1
                continue

            if not force and _has_legal_findings(db, analysis.id):
                stats["files_skipped_already_done"] += 1
                continue

        text = _extract_text(file_path)
        if not text or not text.strip():
            stats["files_no_text"] += 1
            continue

        try:
            findings = run_legal_detectors({"text": text})
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            if verbose:
                print(f"  [ERROR] {file_path.name}: {exc}")
            continue

        if not dry_run and findings:
            with get_db() as db:
                for finding in findings:
                    anomaly = Anomaly(
                        analysis_id=analysis.id,
                        anomaly_id=finding.get("id", "unknown"),
                        issue=finding.get("issue", ""),
                        severity=finding.get("severity", "low"),
                        layer=finding.get("layer", "unknown"),
                        details_json=json.dumps(finding.get("details", {})),
                    )
                    db.add(anomaly)
                db.commit()

        stats["files_processed"] += 1
        stats["findings_added"] += len(findings)

        if verbose and (i % 100 == 0 or i == len(source_files)):
            print(
                f"  [{i}/{len(source_files)}] {file_path.name!r} "
                f"— {len(findings)} findings"
                f"{' (dry run)' if dry_run else ''}"
            )

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill odia_legal findings from source files into DB"
    )
    parser.add_argument(
        "--corpus-dir",
        required=True,
        metavar="DIR",
        help="Directory containing source PDF/TXT/HTML files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run detectors but do not write to DB",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if document already has legal findings",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file output",
    )
    args = parser.parse_args()

    stats = backfill(
        corpus_dir=Path(args.corpus_dir),
        dry_run=args.dry_run,
        limit=args.limit,
        force=args.force,
        verbose=not args.quiet,
    )

    print()
    print("Backfill complete:")
    print(f"  Source files found        : {stats['files_found']}")
    print(f"  No DB match               : {stats['files_no_db_match']}")
    print(f"  Already had legal findings: {stats['files_skipped_already_done']}")
    print(f"  No text extracted         : {stats['files_no_text']}")
    print(f"  Processed                 : {stats['files_processed']}")
    print(f"  Legal findings added      : {stats['findings_added']}")
    if stats["errors"]:
        print(f"  Errors                    : {stats['errors']}")
    if args.dry_run:
        print("  (dry run — nothing written)")


if __name__ == "__main__":
    main()
