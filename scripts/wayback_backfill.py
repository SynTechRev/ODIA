"""CONTRA Wayback backfill — retrieve historical snapshots for corpus documents.

Walks commercial_documents rows where wayback_url IS NULL and source_url IS NOT NULL,
queries the Wayback CDX API for the closest snapshot to the document's effective_date,
and writes the snapshot URL back to the DB row.

Priority targets (year-mark historical retrieval):
  - Google ToS 2002-2006 (27-year version chain gap)
  - Google Privacy 2016-2017
  - AT&T ToS 2017-2022

Usage:
    python scripts/wayback_backfill.py
    python scripts/wayback_backfill.py --entity "Google LLC"
    python scripts/wayback_backfill.py --dry-run
    python scripts/wayback_backfill.py --limit 20
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_CDX_API = "https://web.archive.org/cdx/search/cdx"
_USER_AGENT = "ODIA-CONTRA-WaybackBackfill/3.9 (SynTechRev research; contact codicalcalculus@gmail.com)"
_PAUSE_PER_REQUEST = 2.0
_LONG_PAUSE_EVERY = 50
_LONG_PAUSE_SEC = 20


def _engine(db_path: str):
    from sqlalchemy import create_engine
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def _cdx_lookup(source_url: str, target_date: datetime | None) -> str | None:
    """Query Wayback CDX API for closest snapshot. Returns snapshot URL or None."""
    try:
        import requests
    except ImportError:
        print("  ERROR: requests not installed — pip install requests", file=sys.stderr)
        return None

    ts = target_date.strftime("%Y%m%d%H%M%S") if target_date else "20250101000000"

    params = {
        "url": source_url,
        "output": "json",
        "limit": 1,
        "fl": "timestamp,statuscode",
        "filter": "statuscode:200",
        "closest": ts,
        "fastLatest": "true",
    }

    try:
        resp = requests.get(
            _CDX_API,
            params=params,
            headers={"User-Agent": _USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        rows = resp.json()
        if len(rows) < 2:  # first row is header
            return None
        # rows[1] = [timestamp, statuscode]
        timestamp = rows[1][0]
        encoded = requests.utils.quote(source_url, safe="/:@=?&%+#")
        return f"https://web.archive.org/web/{timestamp}/{encoded}"
    except Exception as exc:
        print(f"  CDX error for {source_url[:60]}: {exc}", file=sys.stderr)
        return None


def backfill(
    db_path: str,
    entity_filter: str | None,
    dry_run: bool,
    limit: int | None,
) -> None:
    from sqlalchemy.orm import sessionmaker

    from oraculus_di_auditor.db.models import CommercialDocument, CommercialEntity

    engine = _engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    query = (
        session.query(CommercialDocument)
        .filter(
            CommercialDocument.wayback_url.is_(None),
            CommercialDocument.source_url.isnot(None),
        )
    )

    if entity_filter:
        entity = session.query(CommercialEntity).filter_by(
            canonical_name=entity_filter
        ).first()
        if not entity:
            print(f"Entity not found: {entity_filter}")
            session.close()
            return
        query = query.filter(CommercialDocument.entity_id == entity.entity_id)

    if limit:
        query = query.limit(limit)

    docs = query.all()
    print(f"Documents needing Wayback URL: {len(docs)}")

    if not docs:
        print("Nothing to do.")
        session.close()
        return

    updated = 0
    failed = 0
    failed_log: list[dict] = []

    for i, doc in enumerate(docs, 1):
        label = f"[{i:>3}/{len(docs)}]"
        effective = doc.effective_date
        url = doc.source_url

        if dry_run:
            print(f"  DRY RUN {label} {url[:80]}")
            continue

        snapshot = _cdx_lookup(url, effective)

        if snapshot:
            doc.wayback_url = snapshot
            print(f"  OK  {label} {url[:60]}")
            print(f"          -> {snapshot[:80]}")
            updated += 1
        else:
            failed += 1
            failed_log.append({
                "document_hash": doc.document_hash,
                "source_url": url,
                "effective_date": effective.isoformat() if effective else None,
            })
            print(f"  MISS {label} {url[:60]}")

        # Commit every 10 rows so progress survives interruption
        if i % 10 == 0:
            session.commit()

        time.sleep(_PAUSE_PER_REQUEST)
        if i % _LONG_PAUSE_EVERY == 0:
            print(f"  Pausing {_LONG_PAUSE_SEC}s (polite pacing)...")
            time.sleep(_LONG_PAUSE_SEC)

    if not dry_run:
        session.commit()

    if failed_log:
        log_path = Path("cache/wayback_failed.json")
        log_path.parent.mkdir(exist_ok=True)
        log_path.write_text(
            json.dumps(failed_log, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nFailed lookups logged to: {log_path}")

    print(f"\n-- Wayback Backfill Results --")
    print(f"  Updated : {updated}")
    print(f"  No snapshot found : {failed}")
    session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="CONTRA Wayback URL backfill")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--entity", default=None, help="Restrict to one entity name")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Max docs to process")
    args = parser.parse_args()

    backfill(
        db_path=args.db_path,
        entity_filter=args.entity,
        dry_run=args.dry_run,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
