"""CONTRA harvest — reads discover_entity_urls.py output and ingests matching documents.

Bridges the gap between discover_entity_urls.py (which writes cache/{slug}/discovered_urls.json)
and the full CONTRA ingest pipeline. Filters discovered URLs by doc-type keywords, fetches
each one, and calls ingest_commercial_document() on the result.

Workflow:
    1. python scripts/discover_entity_urls.py --batch entities.json
    2. python scripts/harvest_discovered_urls.py --dry-run
    3. python scripts/harvest_discovered_urls.py

Usage:
    python scripts/harvest_discovered_urls.py
    python scripts/harvest_discovered_urls.py --slug verizon_communications
    python scripts/harvest_discovered_urls.py --dry-run
    python scripts/harvest_discovered_urls.py --limit 10
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_CACHE_DIR = Path("cache")
_USER_AGENT = "ODIA-CONTRA-Harvest/3.9 (SynTechRev research; contact codicalcalculus@gmail.com)"
_PAUSE_PER_REQUEST = 3.0
_LONG_PAUSE_EVERY = 100
_LONG_PAUSE_SEC = 30
_CHECKPOINT_EVERY = 5

# URL keyword → doc_type mapping (ordered: first match wins)
_DOC_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"arbitrat|dispute|aaa|jams|notice.of.dispute|demand", re.I), "arbitration"),
    (re.compile(r"eula|end.user.licen|software.licen", re.I), "eula"),
    (re.compile(r"privacy|ccpa|gdpr|hipaa|data.collection|cookie", re.I), "privacy_notice"),
    (re.compile(r"terms.of.service|terms.of.use|subscriber.agreement|customer.agreement"
                r"|service.agreement|tos|tou|legal", re.I), "tos"),
]

_REJECT_PATTERNS = re.compile(
    r"apache.licen|w3c.process|law.enforcement|lumen|puc.document"
    r"|annual.report|press.release|investor|earnings|proxy",
    re.I,
)


def _infer_doc_type(url: str, label: str = "") -> str | None:
    text = f"{url} {label}"
    if _REJECT_PATTERNS.search(text):
        return None  # signal: skip this URL
    for pattern, doc_type in _DOC_TYPE_PATTERNS:
        if pattern.search(text):
            return doc_type
    return "tos"  # default


def _fetch(url: str) -> bytes | None:
    try:
        import requests
        resp = requests.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            timeout=30,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return resp.content
    except Exception as exc:
        print(f"    FETCH ERROR: {exc}", file=sys.stderr)
        return None


def _load_checkpoint(slug: str) -> set[str]:
    cp = _CACHE_DIR / slug / "harvest_checkpoint.json"
    if cp.exists():
        return set(json.loads(cp.read_text(encoding="utf-8")).get("done", []))
    return set()


def _save_checkpoint(slug: str, done: set[str]) -> None:
    cp = _CACHE_DIR / slug / "harvest_checkpoint.json"
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(
        json.dumps({"done": sorted(done)}, indent=2),
        encoding="utf-8",
    )


def _find_discovered_files(slug_filter: str | None) -> list[Path]:
    if not _CACHE_DIR.exists():
        return []
    if slug_filter:
        target = _CACHE_DIR / slug_filter / "discovered_urls.json"
        return [target] if target.exists() else []
    return sorted(_CACHE_DIR.glob("*/discovered_urls.json"))


def harvest(
    db_path: str,
    slug_filter: str | None,
    dry_run: bool,
    limit: int | None,
) -> None:
    discovered_files = _find_discovered_files(slug_filter)
    if not discovered_files:
        print("No discovered_urls.json files found.")
        print("Run: python scripts/discover_entity_urls.py --batch entities.json")
        return

    print(f"Found {len(discovered_files)} discovered_urls.json file(s).\n")

    from sqlalchemy.orm import sessionmaker
    from oraculus_di_auditor.ingest.commercial import ingest_commercial_document

    def _engine(p: str):
        from sqlalchemy import create_engine
        return create_engine(f"sqlite:///{p}", connect_args={"check_same_thread": False})

    engine = _engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    total_ok = 0
    total_dup = 0
    total_skip = 0
    total_err = 0
    all_failed: list[dict] = []

    count = 0

    for disc_file in discovered_files:
        slug = disc_file.parent.name
        data: dict = json.loads(disc_file.read_text(encoding="utf-8"))

        entity_name: str = data.get("entity_name", slug.replace("_", " ").title())
        urls: list[dict] = data.get("urls", [])

        checkpoint = _load_checkpoint(slug)
        remaining = [u for u in urls if u.get("url") not in checkpoint]

        print(f"-- {entity_name} ({slug}) --")
        print(f"   {len(urls)} discovered, {len(remaining)} not yet harvested\n")

        for entry in remaining:
            if limit and count >= limit:
                break

            url = entry.get("url", "")
            label = entry.get("label", "")
            doc_type = _infer_doc_type(url, label)

            if doc_type is None:
                print(f"  SKIP (reject pattern) {url[:70]}")
                checkpoint.add(url)
                total_skip += 1
                continue

            print(f"  [{doc_type:<16}] {url[:70]}")

            if dry_run:
                total_ok += 1
                count += 1
                continue

            raw = _fetch(url)
            if raw is None:
                all_failed.append({"entity_name": entity_name, "url": url, "doc_type": doc_type})
                total_err += 1
                checkpoint.add(url)
                _save_checkpoint(slug, checkpoint)
                time.sleep(_PAUSE_PER_REQUEST)
                continue

            suffix = ".pdf" if raw[:4] == b"%PDF" else ".html"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(raw)
                tmp_path = Path(tmp.name)

            try:
                result = ingest_commercial_document(
                    source_path=tmp_path,
                    entity_name=entity_name,
                    doc_type=doc_type,
                    session=session,
                    source_url=url,
                    source_tier="t1",
                )
                if result.skipped_duplicate:
                    print(f"    DUP")
                    total_dup += 1
                else:
                    print(
                        f"    OK  CASI={result.casi_aggregate} [{result.casi_band}] "
                        f"{result.total_findings} findings"
                    )
                    total_ok += 1
            except Exception as exc:
                print(f"    INGEST ERROR: {exc}", file=sys.stderr)
                all_failed.append({"entity_name": entity_name, "url": url, "doc_type": doc_type, "error": str(exc)})
                total_err += 1
            finally:
                tmp_path.unlink(missing_ok=True)

            checkpoint.add(url)
            count += 1

            if count % _CHECKPOINT_EVERY == 0:
                _save_checkpoint(slug, checkpoint)

            time.sleep(_PAUSE_PER_REQUEST)
            if count % _LONG_PAUSE_EVERY == 0:
                print(f"  Pausing {_LONG_PAUSE_SEC}s (polite pacing)...")
                time.sleep(_LONG_PAUSE_SEC)

        _save_checkpoint(slug, checkpoint)

        if limit and count >= limit:
            print(f"\nLimit of {limit} reached.")
            break

    if all_failed:
        fail_path = Path("cache/harvest_failed.json")
        fail_path.parent.mkdir(exist_ok=True)
        fail_path.write_text(
            json.dumps(all_failed, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nFailed URLs written to: {fail_path}")

    session.close()

    print(f"\n-- Harvest Results {'(DRY RUN) ' if dry_run else ''}--")
    print(f"  Ingested   : {total_ok}")
    print(f"  Duplicates : {total_dup}")
    print(f"  Skipped    : {total_skip}")
    print(f"  Errors     : {total_err}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Harvest and ingest URLs discovered by discover_entity_urls.py"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--slug", default=None, help="Process only this cache slug")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Max URLs to process across all entities")
    args = parser.parse_args()

    harvest(
        db_path=args.db_path,
        slug_filter=args.slug,
        dry_run=args.dry_run,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
