"""CONTRA per-entity ingest driver — Tranche 1 / Design Elements 1-8.

Reads the discovered_urls.json manifest produced by discover_entity_urls.py,
fetches each URL, and ingests it into contra_corpus.db via the CONTRA ingest
pipeline.  Implements all eight Fresno-pattern design elements:

  1  Progress checkpoint to cache/{slug}/progress.json every 5 items
  2  Resume: restart skips already-processed URLs (no flag required)
  3  SHA-256 dedup at ingest layer (platform rejects duplicates)
  4  Polite pacing: 3s/request, 30s pause every 100 items
  5  Failure logging to cache/{slug}/failed.json
  6  CLI: --dry-run, --max-items, --entity-slug, --doc-type filter
  7  User-Agent identifies the request source
  8  Calls ingest_commercial_document() directly (local mode)
     or POSTs to ODIA webhook URL (--webhook-url mode)

Usage:
    python scripts/ingest_commercial_entity.py --entity-slug google
    python scripts/ingest_commercial_entity.py --entity-slug att_mobility --dry-run
    python scripts/ingest_commercial_entity.py --entity-slug jpmorgan_chase --max-items 10
    python scripts/ingest_commercial_entity.py --entity-slug comcast --webhook-url http://localhost:8000/webhook/upload
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests as http_requests

log = logging.getLogger("contra.ingest_entity")

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_USER_AGENT = (
    "ODIA-CONTRA-IngestPipeline/G.1 (SynTechRev research; "
    "commercial-contract-corpus; https://github.com/SynTechRev/ODIA)"
)
_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_PAUSE_PER_REQUEST = 3.0
_LONG_PAUSE_EVERY = 100
_LONG_PAUSE_SEC = 30
_CHECKPOINT_EVERY = 5


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _http_session() -> http_requests.Session:
    s = http_requests.Session()
    s.headers["User-Agent"] = _USER_AGENT
    return s


def _load_progress(slug: str) -> dict:
    prog_file = Path("cache") / slug / "progress.json"
    if prog_file.exists():
        return json.loads(prog_file.read_text(encoding="utf-8"))
    return {"processed_urls": [], "ok": 0, "dup": 0, "err": 0}


def _save_progress(slug: str, progress: dict) -> None:
    prog_file = Path("cache") / slug / "progress.json"
    prog_file.parent.mkdir(parents=True, exist_ok=True)
    prog_file.write_text(json.dumps(progress, indent=2), encoding="utf-8")


def _log_failure(slug: str, url: str, error: str) -> None:
    fail_file = Path("cache") / slug / "failed.json"
    fail_file.parent.mkdir(parents=True, exist_ok=True)
    existing: list = []
    if fail_file.exists():
        existing = json.loads(fail_file.read_text(encoding="utf-8"))
    existing.append({"url": url, "error": error, "ts": datetime.now(UTC).isoformat()})
    fail_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def _fetch_url(session: http_requests.Session, url: str) -> tuple[bytes, str, str]:
    """Fetch URL. Returns (raw_bytes, content_type, final_url)."""
    resp = session.get(url, timeout=30, allow_redirects=True)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", ""), str(resp.url)


def _infer_doc_type_from_url(url: str) -> tuple[str, float]:
    """Fast heuristic doc_type from URL before text extraction."""
    import re
    url_lower = url.lower().replace("-", " ").replace("_", " ").replace("/", " ")
    rules = [
        ("arbitration", ["arbitration", "dispute form", "notice of dispute", "adr"]),
        ("eula", ["end user license", "eula", "software license", "program license"]),
        ("privacy_notice", ["privacy", "ccpa", "gdpr", "cookie", "tracking", "hipaa", "notice at collection"]),
        ("tos", ["terms", "conditions", "subscriber", "customer agreement", "service agreement", "user agreement"]),
    ]
    for doc_type, keywords in rules:
        for kw in keywords:
            if kw in url_lower:
                return doc_type, 0.70
    return "tos", 0.25


def _ingest_local(
    raw_bytes: bytes,
    source_url: str,
    entity_name: str,
    doc_type: str,
    db_path: Path,
    session_db,
) -> dict:
    """Call ingest_commercial_document() directly."""
    import tempfile
    from oraculus_di_auditor.ingest.commercial import ingest_commercial_document

    suffix = ".pdf" if b"%PDF" in raw_bytes[:8] else ".txt"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw_bytes)
        tmp_path = Path(tmp.name)

    try:
        result = ingest_commercial_document(
            source_path=tmp_path,
            entity_name=entity_name,
            doc_type=doc_type,
            session=session_db,
            source_url=source_url,
            fetch_wayback=False,
            source_tier="T1",
        )
        return {
            "status": "dup" if result.skipped_duplicate else "ok",
            "casi": result.casi_aggregate if not result.skipped_duplicate else None,
            "band": result.casi_band if not result.skipped_duplicate else None,
            "findings": result.total_findings if not result.skipped_duplicate else None,
        }
    finally:
        tmp_path.unlink(missing_ok=True)


def _ingest_webhook(
    raw_bytes: bytes,
    source_url: str,
    entity_name: str,
    doc_type: str,
    webhook_url: str,
) -> dict:
    """POST raw bytes to ODIA webhook endpoint."""
    import io
    resp = http_requests.post(
        webhook_url,
        files={"file": ("document.pdf", io.BytesIO(raw_bytes), "application/octet-stream")},
        data={
            "entity_name": entity_name,
            "doc_type": doc_type,
            "source_url": source_url,
            "source_tier": "T1",
        },
        timeout=120,
        headers={"User-Agent": _USER_AGENT},
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "status": data.get("status", "ok"),
        "casi": data.get("casi_aggregate"),
        "band": data.get("casi_band"),
        "findings": data.get("total_findings"),
    }


def run_entity_ingest(
    entity_slug: str,
    entity_name: str,
    db_path: Path,
    dry_run: bool = False,
    max_items: int | None = None,
    doc_type_filter: str | None = None,
    webhook_url: str | None = None,
) -> None:
    cache_dir = Path("cache") / entity_slug
    discovered_file = cache_dir / "discovered_urls.json"

    if not discovered_file.exists():
        log.error(
            "No discovered_urls.json for '%s'. Run discover_entity_urls.py first.",
            entity_slug,
        )
        sys.exit(1)

    manifest_data = json.loads(discovered_file.read_text(encoding="utf-8"))
    urls = manifest_data.get("urls", [])
    if not entity_name:
        entity_name = manifest_data.get("entity_name", entity_slug)

    if doc_type_filter:
        urls = [u for u in urls if _infer_doc_type_from_url(u["url"])[0] == doc_type_filter]

    progress = _load_progress(entity_slug)
    processed_set = set(progress.get("processed_urls", []))
    remaining = [u for u in urls if u["url"] not in processed_set]

    if max_items:
        remaining = remaining[:max_items]

    log.info(
        "%s: %d total URLs, %d already done, %d to process",
        entity_name,
        len(urls),
        len(processed_set),
        len(remaining),
    )

    if not remaining:
        log.info("Nothing to ingest. All URLs already processed.")
        return

    http_sess = _http_session()

    if not dry_run and not webhook_url:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from oraculus_di_auditor.db.models import Base, CasiScore, CommercialDocument
        from oraculus_di_auditor.db.models import CommercialDocumentProvenance, CommercialEntity
        from oraculus_di_auditor.db.models import CommercialEntityAlias, CommercialDocumentVersionChain
        from oraculus_di_auditor.db.models import ContraFinding, S128196Case, TosdrClassification

        engine = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
        )
        contra_tables = [
            CommercialEntity.__table__, CommercialEntityAlias.__table__,
            CommercialDocument.__table__, CommercialDocumentProvenance.__table__,
            CommercialDocumentVersionChain.__table__, ContraFinding.__table__,
            CasiScore.__table__, S128196Case.__table__, TosdrClassification.__table__,
        ]
        Base.metadata.create_all(engine, tables=contra_tables)
        Session = sessionmaker(bind=engine)
        db_session = Session()
    else:
        db_session = None

    for i, url_entry in enumerate(remaining, 1):
        url = url_entry["url"]
        doc_type, _ = _infer_doc_type_from_url(url)
        prefix = f"[{i:>3}/{len(remaining)}] {entity_name} - {url[-55:]}"

        if dry_run:
            print(f"  DRY   {prefix} -> {doc_type}")
            progress["processed_urls"].append(url)
            progress["ok"] = progress.get("ok", 0) + 1
            if i % _CHECKPOINT_EVERY == 0:
                _save_progress(entity_slug, progress)
            continue

        try:
            raw_bytes, content_type, final_url = _fetch_url(http_sess, url)
            log.debug("Fetched %d bytes from %s", len(raw_bytes), final_url)

            if webhook_url:
                result = _ingest_webhook(raw_bytes, final_url, entity_name, doc_type, webhook_url)
            else:
                result = _ingest_local(raw_bytes, final_url, entity_name, doc_type, db_path, db_session)

            status = result["status"]
            if status == "dup":
                print(f"  DUP   {prefix}")
                progress["dup"] = progress.get("dup", 0) + 1
            else:
                print(f"  OK    {prefix} -> CASI {result['casi']} [{result['band']}] | {result['findings']} findings")
                progress["ok"] = progress.get("ok", 0) + 1

            progress["processed_urls"].append(url)

        except Exception as exc:
            log.warning("ERR %s: %s", url, exc)
            print(f"  ERR   {prefix} -> {exc}")
            progress["err"] = progress.get("err", 0) + 1
            _log_failure(entity_slug, url, str(exc))

        if i % _CHECKPOINT_EVERY == 0:
            _save_progress(entity_slug, progress)

        if i % _LONG_PAUSE_EVERY == 0:
            log.info("Long pause %ds at item %d...", _LONG_PAUSE_SEC, i)
            time.sleep(_LONG_PAUSE_SEC)
        else:
            time.sleep(_PAUSE_PER_REQUEST)

    _save_progress(entity_slug, progress)

    if db_session:
        db_session.close()

    print(f"\n-- {entity_name} Ingest Results --")
    print(f"  OK  : {progress.get('ok', 0)}")
    print(f"  DUP : {progress.get('dup', 0)}")
    print(f"  ERR : {progress.get('err', 0)}")
    if not dry_run:
        print(f"\nRun: python scripts/contra_query.py --entity \"{entity_name}\"")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    parser = argparse.ArgumentParser(description="CONTRA per-entity ingest driver")
    parser.add_argument("--entity-slug", required=True, help="entity_id_slug matching cache/{slug}/discovered_urls.json")
    parser.add_argument("--entity-name", default=None, help="Canonical entity name (read from manifest if omitted)")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--webhook-url", default=None, help="POST to ODIA webhook instead of calling pipeline directly")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument("--doc-type", default=None, choices=["tos", "privacy_notice", "eula", "arbitration"])
    args = parser.parse_args()

    run_entity_ingest(
        entity_slug=args.entity_slug,
        entity_name=args.entity_name or "",
        db_path=Path(args.db_path),
        dry_run=args.dry_run,
        max_items=args.max_items,
        doc_type_filter=args.doc_type,
        webhook_url=args.webhook_url,
    )


if __name__ == "__main__":
    main()
