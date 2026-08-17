"""CONTRA batch ingest — process a manifest JSON into a dedicated contra_corpus.db.

This script reads the manifest produced by contra_scan.py and ingests each document
through the full CONTRA pipeline into a SEPARATE SQLite database (contra_corpus.db),
keeping it isolated from oraculus_audit.db (the government audit records).

Usage:
    # Quick start — scan and ingest in one step:
    python scripts/contra_scan.py --out contra_manifest.json
    python scripts/contra_batch_ingest.py --manifest contra_manifest.json

    # Dry run (no DB writes):
    python scripts/contra_batch_ingest.py --manifest contra_manifest.json --dry-run

    # Single entity only:
    python scripts/contra_batch_ingest.py --manifest contra_manifest.json --entity "Google LLC"

    # Skip entities already in DB:
    python scripts/contra_batch_ingest.py --manifest contra_manifest.json --skip-duplicates

DB location:
    Defaults to D:\\CONTRA Contract Corpus\\contra_corpus.db
    Override with --db-path or CONTRA_DATABASE_URL env var.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Ensure the src package is on the path when run from repo root
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))


def _build_contra_engine(db_path: Path):
    """Create a SQLAlchemy engine bound ONLY to the CONTRA tables."""
    from sqlalchemy import create_engine

    db_url = os.environ.get("CONTRA_DATABASE_URL") or f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return engine


def _init_contra_db(engine) -> None:
    """Create all CONTRA tables in the target DB if they don't already exist."""
    from oraculus_di_auditor.db.models import (
        Base,
        CasiScore,
        CommercialDocument,
        CommercialDocumentProvenance,
        CommercialDocumentVersionChain,
        CommercialEntity,
        CommercialEntityAlias,
        ContraFinding,
        S128196Case,
        TosdrClassification,
    )

    contra_tables = [
        CommercialEntity.__table__,
        CommercialEntityAlias.__table__,
        CommercialDocument.__table__,
        CommercialDocumentProvenance.__table__,
        CommercialDocumentVersionChain.__table__,
        ContraFinding.__table__,
        CasiScore.__table__,
        S128196Case.__table__,
        TosdrClassification.__table__,
    ]
    Base.metadata.create_all(engine, tables=contra_tables)


def _seed_entity_registry(session, manifest: list[dict]) -> dict[str, str]:
    """Ensure every entity in the manifest exists in commercial_entities.

    Returns mapping of entity_name → entity_id.
    """
    from oraculus_di_auditor.db.models import CommercialEntity

    seen: dict[str, str] = {}
    for entry in manifest:
        name = entry["entity_name"]
        if name in seen:
            continue
        existing = session.query(CommercialEntity).filter_by(canonical_name=name).first()
        if existing:
            seen[name] = existing.entity_id
            continue

        slug = entry.get("entity_id_slug") or name.lower().replace(" ", "_")
        entity_id = f"contra:{slug}"
        row = CommercialEntity(
            entity_id=entity_id,
            canonical_name=name,
            corporate_family=entry.get("corporate_family"),
            in_contra_corpus=True,
            in_tulare_priority_list=False,
        )
        session.add(row)
        seen[name] = entity_id

    session.commit()
    return seen


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).replace(tzinfo=UTC)
    except ValueError:
        return None


def _run_batch(
    manifest: list[dict],
    session,
    entity_id_map: dict[str, str],
    dry_run: bool,
    output_dir: Path | None,
) -> dict:
    from oraculus_di_auditor.ingest.commercial import ingest_commercial_document

    results = {
        "ok": 0,
        "skipped_duplicate": 0,
        "skipped_missing_file": 0,
        "errors": 0,
        "error_details": [],
    }

    total = len(manifest)
    for i, entry in enumerate(manifest, 1):
        file_path = Path(entry["file_path"])
        entity_name = entry["entity_name"]
        doc_type = entry["doc_type"]

        prefix = f"[{i:>3}/{total}] {entity_name} - {file_path.name[:55]}"

        if not file_path.exists():
            print(f"  SKIP (file missing): {prefix}")
            results["skipped_missing_file"] += 1
            continue

        if dry_run:
            date_str = entry.get("effective_date") or ""
            print(f"  DRY   {prefix} -> {doc_type} {date_str}")
            results["ok"] += 1
            continue

        try:
            result = ingest_commercial_document(
                source_path=file_path,
                entity_name=entity_name,
                doc_type=doc_type,
                session=session,
                effective_date=_parse_date(entry.get("effective_date")),
                version_label=entry.get("version_label"),
                source_url=entry.get("source_url"),
                output_dir=output_dir,
                fetch_wayback=False,  # disable during batch — too slow
                source_tier=entry.get("source_tier", "T1"),
            )

            if result.skipped_duplicate:
                print(f"  DUP   {prefix}")
                results["skipped_duplicate"] += 1
            else:
                band = result.casi_band
                agg = result.casi_aggregate
                findings = result.total_findings
                print(f"  OK    {prefix} -> CASI {agg} [{band}] | {findings} findings")
                results["ok"] += 1

        except Exception as exc:
            print(f"  ERR   {prefix} -> {exc}")
            results["errors"] += 1
            results["error_details"].append(
                {"file": str(file_path), "error": str(exc)}
            )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-ingest CONTRA corpus manifest into contra_corpus.db"
    )
    parser.add_argument("--manifest", required=True, help="Path to contra_manifest.json")
    parser.add_argument(
        "--db-path",
        default=r"D:\CONTRA Contract Corpus\contra_corpus.db",
        help="Path for the CONTRA SQLite database",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for analytical card DOCX output (optional)",
    )
    parser.add_argument(
        "--entity",
        default=None,
        help="Process only this entity (exact canonical name match)",
    )
    parser.add_argument(
        "--doc-type",
        default=None,
        help="Process only this doc_type (tos, privacy_notice, arbitration, eula)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without writing to DB",
    )
    parser.add_argument(
        "--skip-review",
        action="store_true",
        help="Also ingest entries flagged needs_review=true (default: skip them)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest: list[dict] = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"Loaded {len(manifest)} entries from {manifest_path}")

    # Filter
    if not args.skip_review:
        before = len(manifest)
        manifest = [e for e in manifest if not e.get("needs_review")]
        skipped_review = before - len(manifest)
        if skipped_review:
            print(f"  Skipped {skipped_review} entries flagged needs_review=True")
            print("  Run with --skip-review to include them")

    if args.entity:
        manifest = [e for e in manifest if e["entity_name"] == args.entity]
        print(f"  Filtered to entity '{args.entity}': {len(manifest)} entries")

    if args.doc_type:
        manifest = [e for e in manifest if e["doc_type"] == args.doc_type]
        print(f"  Filtered to doc_type '{args.doc_type}': {len(manifest)} entries")

    if not manifest:
        print("Nothing to ingest after filters.")
        return

    db_path = Path(args.db_path)
    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.dry_run:
        print(f"\nDRY RUN - target DB would be: {db_path}\n")
    else:
        print(f"\nTarget DB: {db_path}")
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)

    # Build engine + session
    from sqlalchemy.orm import sessionmaker

    engine = _build_contra_engine(db_path)

    if not args.dry_run:
        print("Initialising schema...")
        _init_contra_db(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed entities
    if not args.dry_run:
        print("Seeding entity registry...")
        entity_id_map = _seed_entity_registry(session, manifest)
        print(f"  {len(entity_id_map)} entities ready in DB")
    else:
        entity_id_map = {}

    print(f"\nIngesting {len(manifest)} documents...\n")
    t0 = time.monotonic()

    results = _run_batch(manifest, session, entity_id_map, args.dry_run, output_dir)

    elapsed = time.monotonic() - t0
    print(f"\n-- Results ({'DRY RUN ' if args.dry_run else ''}{elapsed:.1f}s) --")
    print(f"  OK:               {results['ok']}")
    print(f"  Duplicate (skip): {results['skipped_duplicate']}")
    print(f"  Missing file:     {results['skipped_missing_file']}")
    print(f"  Errors:           {results['errors']}")

    if results["error_details"]:
        err_path = Path("contra_ingest_errors.json")
        err_path.write_text(
            json.dumps(results["error_details"], indent=2), encoding="utf-8"
        )
        print(f"  Error details written to: {err_path}")

    session.close()

    if not args.dry_run and results["ok"] > 0:
        print(f"\nDB written to: {db_path}")
        print("Run: python scripts/contra_query.py to inspect results")


if __name__ == "__main__":
    main()
