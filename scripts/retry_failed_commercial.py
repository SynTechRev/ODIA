"""CONTRA retry — exponential-backoff retry for failed.json entries.

Reads cache/{entity_slug}/failed.json files (produced by ingest_commercial_entity.py),
retries each failed URL with exponential backoff, and re-ingests successfully retrieved
documents through the full CONTRA pipeline.

Usage:
    python scripts/retry_failed_commercial.py
    python scripts/retry_failed_commercial.py --entity-slug att_inc
    python scripts/retry_failed_commercial.py --dry-run
    python scripts/retry_failed_commercial.py --max-retries 5
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_CACHE_DIR = Path("cache")
_USER_AGENT = "ODIA-CONTRA-Retry/3.9 (SynTechRev research; contact codicalcalculus@gmail.com)"

_BASE_DELAY = 4.0      # seconds before first retry
_MAX_DELAY = 120.0     # cap on exponential backoff
_DEFAULT_MAX_RETRIES = 4


def _engine(db_path: str):
    from sqlalchemy import create_engine
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def _fetch_with_backoff(url: str, max_retries: int) -> bytes | None:
    """Fetch URL with exponential backoff. Returns raw bytes or None."""
    try:
        import requests
    except ImportError:
        print("ERROR: requests not installed — pip install requests", file=sys.stderr)
        return None

    delay = _BASE_DELAY
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": _USER_AGENT},
                timeout=30,
                allow_redirects=True,
            )
            resp.raise_for_status()
            return resp.content
        except Exception as exc:
            if attempt == max_retries:
                print(f"    FAIL after {max_retries} attempts: {exc}", file=sys.stderr)
                return None
            print(f"    attempt {attempt}/{max_retries} failed ({exc}); retrying in {delay:.0f}s")
            time.sleep(delay)
            delay = min(delay * 2, _MAX_DELAY)

    return None


def _find_failed_files(slug_filter: str | None) -> list[Path]:
    if not _CACHE_DIR.exists():
        return []
    if slug_filter:
        target = _CACHE_DIR / slug_filter / "failed.json"
        return [target] if target.exists() else []
    return sorted(_CACHE_DIR.glob("*/failed.json"))


def retry_all(
    db_path: str,
    slug_filter: str | None,
    dry_run: bool,
    max_retries: int,
) -> None:
    failed_files = _find_failed_files(slug_filter)
    if not failed_files:
        print("No failed.json files found under cache/.")
        return

    print(f"Found {len(failed_files)} failed.json file(s).\n")

    total_ok = 0
    total_still_failed = 0
    still_failed_by_slug: dict[str, list[dict]] = {}

    from sqlalchemy.orm import sessionmaker
    engine = _engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    for failed_path in failed_files:
        slug = failed_path.parent.name
        entries: list[dict] = json.loads(failed_path.read_text(encoding="utf-8"))
        print(f"-- {slug} ({len(entries)} failures) --")

        still_failed: list[dict] = []

        for entry in entries:
            url = entry.get("url", "")
            entity_name = entry.get("entity_name", slug)
            doc_type = entry.get("doc_type", "tos")
            version_label = entry.get("version_label")
            effective_date_str = entry.get("effective_date")

            print(f"  Retrying: {url[:80]}")

            if dry_run:
                print(f"    DRY RUN - would retry {url}")
                continue

            raw = _fetch_with_backoff(url, max_retries)
            if raw is None:
                still_failed.append(entry)
                total_still_failed += 1
                continue

            # Write to temp file and ingest
            import tempfile
            suffix = ".pdf" if raw[:4] == b"%PDF" else ".txt"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(raw)
                tmp_path = Path(tmp.name)

            try:
                from datetime import datetime as _dt
                from oraculus_di_auditor.ingest.commercial import ingest_commercial_document

                effective_date = None
                if effective_date_str:
                    try:
                        effective_date = _dt.fromisoformat(effective_date_str).replace(tzinfo=UTC)
                    except ValueError:
                        pass

                result = ingest_commercial_document(
                    source_path=tmp_path,
                    entity_name=entity_name,
                    doc_type=doc_type,
                    session=session,
                    effective_date=effective_date,
                    version_label=version_label,
                    source_url=url,
                    source_tier="t1",
                )
                print(f"    OK  CASI={result.casi_aggregate} [{result.casi_band}] {result.total_findings} findings")
                total_ok += 1
            except Exception as exc:
                print(f"    INGEST ERROR: {exc}", file=sys.stderr)
                still_failed.append(entry)
                total_still_failed += 1
            finally:
                tmp_path.unlink(missing_ok=True)

            time.sleep(3.0)

        if still_failed:
            still_failed_by_slug[slug] = still_failed
            # Overwrite failed.json with only the still-failing entries
            if not dry_run:
                failed_path.write_text(
                    json.dumps(still_failed, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                print(f"  Updated {failed_path} ({len(still_failed)} still failing)")
        else:
            if not dry_run:
                failed_path.unlink()
                print(f"  All retried — removed {failed_path}")

    session.close()

    print(f"\n-- Retry Results --")
    print(f"  Recovered  : {total_ok}")
    print(f"  Still failed: {total_still_failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CONTRA retry failed commercial ingest entries")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--entity-slug", default=None, help="Restrict to one cache slug (e.g. att_inc)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-retries", type=int, default=_DEFAULT_MAX_RETRIES)
    args = parser.parse_args()

    retry_all(
        db_path=args.db_path,
        slug_filter=args.entity_slug,
        dry_run=args.dry_run,
        max_retries=args.max_retries,
    )


if __name__ == "__main__":
    main()
