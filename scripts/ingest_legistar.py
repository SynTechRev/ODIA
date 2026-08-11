"""ingest_legistar.py — Full Legistar corpus ingest into ODIA.

Paginates through all matters on a Legistar instance, downloads every
attachment, and POSTs each to ODIA's webhook for Tier 1 analysis.

Designed for multi-day operation:
  - Progress is checkpointed to cache/<client>/progress.json every 50 matters.
  - On restart, already-processed matter IDs are skipped automatically.
  - ODIA's SHA-256 dedup handles file-level deduplication.
  - Polite pacing: 1s between attachment list calls, 30s every 100 matters.

Usage:
    # Dry run — list matters only, no downloads:
    .venv\\Scripts\\python scripts\\ingest_legistar.py --client fresnocounty --dry-run

    # Full ingest (desktop backend default, port 18741):
    .venv\\Scripts\\python scripts\\ingest_legistar.py --client fresnocounty

    # Resume from where it stopped (reads progress.json automatically):
    .venv\\Scripts\\python scripts\\ingest_legistar.py --client fresnocounty

    # Test run — first 20 matters only:
    .venv\\Scripts\\python scripts\\ingest_legistar.py --client fresnocounty --max-matters 20

    # Dev server:
    .venv\\Scripts\\python scripts\\ingest_legistar.py --client fresnocounty --port 8000

    # Date-range filter (ISO dates):
    .venv\\Scripts\\python scripts\\ingest_legistar.py --client fresnocounty --start 2020-01-01

NSU PROTOCOL: No date range or keyword filter by default. Full corpus.
"""

from __future__ import annotations

import argparse
import http.client
import json
import mimetypes
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests as _requests

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

LEGISTAR_API = "https://webapi.legistar.com/v1/{client}/"
WEBHOOK_PORT = 18741
WEBHOOK_PATH = "/api/v1/webhook/ingest-and-analyze"
CACHE_ROOT = _REPO_ROOT / "cache"

# Pacing — be polite to the public API
PAUSE_BETWEEN_MATTERS = 1.0  # seconds between attachment-list API calls
PAUSE_LONG_EVERY_N = 100  # long pause every N matters
PAUSE_LONG_SEC = 30.0  # long pause duration
PAUSE_BETWEEN_DOWNLOADS = 0.5  # seconds between file downloads
CHECKPOINT_EVERY_N = 50  # save progress.json every N matters

# File size limits
MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB — skip anything larger
MIN_FILE_BYTES = 1_000  # < 1 KB = challenge/redirect page

API_TIMEOUT = 30  # Legistar API request timeout
DL_TIMEOUT = 120  # file download timeout
WEBHOOK_TIMEOUT = 300


def _read_token() -> str:
    env_token = os.environ.get("ODIA_WEBHOOK_TOKEN", "").strip()
    if env_token:
        return env_token
    token_path = Path(os.environ.get("APPDATA", "")) / "ODIA" / "webhook_token"
    if token_path.exists():
        token = token_path.read_text(encoding="utf-8").strip()
        if token:
            return token
    print(f"ERROR: No webhook token found at {token_path}")
    print("       Set ODIA_WEBHOOK_TOKEN env var or ensure the token file exists.")
    sys.exit(1)


def _legistar_get(url: str, params: dict | None = None) -> list | dict:
    """Single Legistar API request with one retry on transient error."""
    for attempt in range(3):
        try:
            r = _requests.get(url, params=params, timeout=API_TIMEOUT)
            if r.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"\n  [rate-limited] sleeping {wait}s...", flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    return []


def _list_all_matters(
    client: str, start_date: str | None, end_date: str | None
) -> list[dict]:
    """Paginate through all matters, optionally filtered by date range."""
    base = LEGISTAR_API.format(client=client)
    url = base + "matters"
    all_matters: list[dict] = []
    skip = 0

    filters = []
    if start_date:
        filters.append(f"MatterIntroDate ge datetime'{start_date}'")
    if end_date:
        filters.append(f"MatterIntroDate le datetime'{end_date}'")
    filter_str = " and ".join(filters) if filters else None

    page = 0
    while True:
        page += 1
        params: dict = {"$top": 1000, "$skip": skip}
        if filter_str:
            params["$filter"] = filter_str
        batch = _legistar_get(url, params=params)
        if not batch:
            break
        all_matters.extend(batch)
        print(
            f"  Fetched page {page}: {len(batch)} matters (total so far: {len(all_matters)})"
        )
        if len(batch) < 1000:
            break
        skip += 1000
        time.sleep(0.3)

    return all_matters


def _get_attachments(client: str, matter_id: int | str) -> list[dict]:
    base = LEGISTAR_API.format(client=client)
    url = base + f"matters/{matter_id}/attachments"
    try:
        return _legistar_get(url) or []
    except Exception as exc:
        print(f"\n  [att-error] matter {matter_id}: {exc}")
        return []


def _download(url: str, dest: Path) -> bool:
    """Download url to dest. Returns True on success."""
    try:
        r = _requests.get(url, timeout=DL_TIMEOUT, stream=True)
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        total = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=16384):
                f.write(chunk)
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    print(
                        f"\n  [skip] {dest.name} exceeds {MAX_FILE_BYTES // 1024 // 1024} MB cap"
                    )
                    dest.unlink(missing_ok=True)
                    return False
        if total < MIN_FILE_BYTES:
            dest.unlink(missing_ok=True)
            return False
        return True
    except Exception as exc:
        dest.unlink(missing_ok=True)
        print(f"\n  [dl-error] {url[:60]}: {exc}")
        return False


def _post_to_webhook(file_path: Path, jurisdiction: str, token: str, port: int) -> dict:
    boundary = "ODIAboundary1234567890"
    file_bytes = file_path.read_bytes()
    mime = mimetypes.guess_type(str(file_path))[0] or "application/pdf"
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="jurisdiction_id"\r\n\r\n'
            f"{jurisdiction}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=WEBHOOK_TIMEOUT)
    conn.request(
        "POST",
        WEBHOOK_PATH,
        body=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "X-ODIA-Webhook-Token": token,
        },
    )
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except Exception:
        return {"error": raw[:200], "http_status": resp.status}


def _load_progress(progress_path: Path) -> dict:
    if progress_path.exists():
        try:
            return json.loads(progress_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "processed_matter_ids": [],
        "stats": {
            "matters_processed": 0,
            "attachments_found": 0,
            "files_new": 0,
            "files_already_seen": 0,
            "files_failed": 0,
            "files_skipped": 0,
        },
        "started_at": datetime.now().isoformat(),
        "last_updated": None,
    }


def _save_progress(progress_path: Path, progress: dict) -> None:
    progress["last_updated"] = datetime.now().isoformat()
    progress_path.write_text(
        json.dumps(progress, indent=2, default=str),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest full Legistar corpus into ODIA (NSU protocol — no filters)"
    )
    parser.add_argument(
        "--client",
        default="fresnocounty",
        help="Legistar client ID (default: fresnocounty)",
    )
    parser.add_argument(
        "--jurisdiction",
        default=None,
        help="ODIA jurisdiction_id (default: same as --client)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=WEBHOOK_PORT,
        help=f"Backend port (default {WEBHOOK_PORT}; use 8000 for dev server)",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Start date filter ISO8601 e.g. 2020-01-01 (NSU: omit for full corpus)",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="End date filter ISO8601 (NSU: omit for full corpus)",
    )
    parser.add_argument(
        "--max-matters",
        type=int,
        default=None,
        help="Stop after N matters (for testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List matters only — no downloads or webhook posts",
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep downloaded files in cache after POSTing (default: delete after POST)",
    )
    args = parser.parse_args()

    client = args.client.lower().strip()
    jurisdiction = args.jurisdiction or client
    webhook_port = args.port
    cache_dir = CACHE_ROOT / f"{client}_legistar"
    cache_dir.mkdir(parents=True, exist_ok=True)
    progress_path = cache_dir / "progress.json"
    log_path = cache_dir / "ingest.log"

    print("Legistar ingest — NSU protocol")
    print(f"Client:       {client}")
    print(f"Jurisdiction: {jurisdiction}")
    print(f"Cache:        {cache_dir}")
    print(f"Progress:     {progress_path}")
    if args.start or args.end:
        print(f"Date filter:  {args.start or '*'} -> {args.end or '*'}")
    else:
        print("Date filter:  NONE (full corpus)")
    print()

    # Load or init progress
    progress = _load_progress(progress_path)
    processed_ids: set[int] = set(progress["processed_matter_ids"])
    stats = progress["stats"]

    if processed_ids:
        print(f"Resuming: {len(processed_ids)} matters already processed.")
        print(
            f"  New: {stats['files_new']}  Seen: {stats['files_already_seen']}  Failed: {stats['files_failed']}"
        )
        print()

    # Fetch matter list
    print("Fetching matter list from Legistar API...")
    matters = _list_all_matters(client, args.start, args.end)
    print(f"\nTotal matters available: {len(matters)}")

    # Filter already-processed
    pending = [
        m for m in matters if (m.get("MatterId") or m.get("Id")) not in processed_ids
    ]
    print(f"Already processed:       {len(matters) - len(pending)}")
    print(f"Remaining:               {len(pending)}")

    if args.max_matters:
        pending = pending[: args.max_matters]
        print(f"[--max-matters={args.max_matters}] capped to {len(pending)}")

    if args.dry_run:
        print("\n[dry-run] Sample of pending matters:")
        for m in pending[:20]:
            mid = m.get("MatterId") or m.get("Id")
            title = (m.get("MatterTitle") or "?")[:80]
            mtype = m.get("MatterTypeName", "?")
            print(f"  [{mid}] [{mtype}] {title}")
        if len(pending) > 20:
            print(f"  ... and {len(pending) - 20} more")
        print(f"\n[dry-run] {len(pending)} matters pending. Remove --dry-run to begin.")
        return

    if not pending:
        print("Nothing to do — all matters already processed.")
        return

    token = _read_token()

    # Open log file
    log_f = open(log_path, "a", encoding="utf-8")

    def log(msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        log_f.write(line + "\n")
        log_f.flush()

    log(f"--- Session start: {len(pending)} matters to process ---")
    log(f"Client: {client} | Jurisdiction: {jurisdiction} | Port: {webhook_port}")

    print(f"\nStarting ingest — {len(pending)} matters remaining.")
    print(f"Log: {log_path}")
    print(
        f"Estimated time: {len(pending) * 1.5 / 3600:.1f}+ hours (varies by attachment count)"
    )
    print()

    matters_this_session = 0
    for i, matter in enumerate(pending, 1):
        matter_id = matter.get("MatterId") or matter.get("Id")
        title = (matter.get("MatterTitle") or "?")[:70]
        mtype = matter.get("MatterTypeName", "?")

        print(f"[{i}/{len(pending)}] id={matter_id} | {title}")

        # Get attachments
        attachments = _get_attachments(client, matter_id)
        stats["attachments_found"] += len(attachments)

        if not attachments:
            log(f"MATTER {matter_id} | no attachments | {title[:60]}")
            processed_ids.add(matter_id)
            stats["matters_processed"] += 1
            matters_this_session += 1
            # Checkpoint
            if matters_this_session % CHECKPOINT_EVERY_N == 0:
                progress["processed_matter_ids"] = list(processed_ids)
                _save_progress(progress_path, progress)
            time.sleep(PAUSE_BETWEEN_MATTERS)
            continue

        print(f"  {len(attachments)} attachment(s)", end="", flush=True)

        for att in attachments:
            url = att.get("MatterAttachmentHyperlink") or att.get("Hyperlink") or ""
            att_name = (
                att.get("MatterAttachmentName") or att.get("Name") or "attachment"
            )
            if not url:
                continue

            # Derive filename
            from urllib.parse import urlparse as _up

            url_path = _up(url).path
            fname = Path(url_path).name or f"matter_{matter_id}_att.pdf"
            if not Path(fname).suffix:
                fname += ".pdf"
            local = cache_dir / fname

            # Download
            if not local.exists():
                ok = _download(url, local)
                if not ok:
                    stats["files_skipped"] += 1
                    print(" S", end="", flush=True)
                    log(f"SKIP {matter_id} | {att_name[:50]} | {url[:80]}")
                    continue
                time.sleep(PAUSE_BETWEEN_DOWNLOADS)

            # POST to webhook
            try:
                resp = _post_to_webhook(local, jurisdiction, token, webhook_port)
            except Exception as exc:
                print(" E", end="", flush=True)
                log(f"POST_ERR {matter_id} | {att_name[:50]} | {exc}")
                stats["files_failed"] += 1
                continue
            finally:
                if not args.keep_files and local.exists():
                    local.unlink(missing_ok=True)

            if resp.get("already_seen"):
                print(" .", end="", flush=True)
                stats["files_already_seen"] += 1
                log(f"SEEN {matter_id} | {att_name[:50]}")
            elif resp.get("status") == "ok":
                count = (resp.get("findings") or {}).get("count", "?")
                print(f" +{count}", end="", flush=True)
                stats["files_new"] += 1
                log(f"OK {matter_id} | {count} findings | {att_name[:50]}")
            else:
                print(" F", end="", flush=True)
                stats["files_failed"] += 1
                log(f"FAIL {matter_id} | {resp} | {att_name[:50]}")

        print()  # newline after attachment dots

        processed_ids.add(matter_id)
        stats["matters_processed"] += 1
        matters_this_session += 1

        # Checkpoint every N matters
        if matters_this_session % CHECKPOINT_EVERY_N == 0:
            progress["processed_matter_ids"] = list(processed_ids)
            _save_progress(progress_path, progress)
            print(
                f"  [checkpoint] {matters_this_session} matters this session | "
                f"new={stats['files_new']} seen={stats['files_already_seen']} "
                f"failed={stats['files_failed']}"
            )

        # Long pause every 100 matters
        if matters_this_session % PAUSE_LONG_EVERY_N == 0:
            print(f"  [polite pause {PAUSE_LONG_SEC:.0f}s]", flush=True)
            time.sleep(PAUSE_LONG_SEC)
        else:
            time.sleep(PAUSE_BETWEEN_MATTERS)

    # Final save
    progress["processed_matter_ids"] = list(processed_ids)
    _save_progress(progress_path, progress)
    log_f.close()

    print()
    print("=" * 60)
    print("Session complete")
    print("=" * 60)
    print(f"Matters processed (this session): {matters_this_session}")
    print(f"Total processed (all sessions):   {stats['matters_processed']}")
    print(f"Attachments found:   {stats['attachments_found']}")
    print(f"Files new:           {stats['files_new']}")
    print(f"Files already seen:  {stats['files_already_seen']}")
    print(f"Files skipped:       {stats['files_skipped']}")
    print(f"Files failed:        {stats['files_failed']}")
    print()
    if stats["files_new"] > 0:
        print("Next steps:")
        print("  1. Rebuild RAG index:")
        print("     .venv\\Scripts\\python scripts\\build_rag_index.py")
        print("  2. Re-export MAS corpus:")
        print("     .venv\\Scripts\\python scripts\\export_mas_corpus.py")


if __name__ == "__main__":
    main()
