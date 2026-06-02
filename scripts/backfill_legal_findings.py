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

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".html", ".htm", ".xml"}


def _has_legal_findings(db, analysis_id: int) -> bool:
    return (
        db.query(Anomaly)
        .filter(Anomaly.analysis_id == analysis_id)
        .filter(Anomaly.layer.in_(LEGAL_LAYERS))
        .first()
        is not None
    )


def _find_matching_doc(db, file_path: Path) -> Document | None:
    """Find the DB Document whose title matches the file's stem or name."""
    name = file_path.name
    stem = file_path.stem
    # Try exact filename match first, then stem
    doc = db.query(Document).filter(Document.title == name).first()
    if doc is None:
        doc = db.query(Document).filter(Document.title.like(f"%{stem}%")).first()
    return doc


def _extract_text(file_path: Path) -> str | None:
    """Extract text from a source file using the ingestion engine."""
    try:
        doc = ingest_document(str(file_path))
        return doc.get("text") or doc.get("content") or ""
    except Exception:  # noqa: BLE001
        return None


def backfill(
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
