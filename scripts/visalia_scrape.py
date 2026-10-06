"""visalia_scrape.py — Windows-native port of visalia_ingest.sh.

Fetches all document links from Visalia's CivicPlus AgendaCenter, downloads
each PDF, and POSTs it to ODIA's webhook/ingest-and-analyze endpoint.

Functional parity with visalia_ingest.sh but runs on Windows without WSL.
Requires the ODIA backend to be running on port 8000:

    .venv\\Scripts\\python -m uvicorn oraculus_di_auditor.interface.api:create_app \\
        --factory --host 127.0.0.1 --port 8000 --no-access-log

Usage:
    .venv\\Scripts\\python scripts\\visalia_scrape.py
    .venv\\Scripts\\python scripts\\visalia_scrape.py --port 18741  # desktop backend
    .venv\\Scripts\\python scripts\\visalia_scrape.py --dry-run     # list links only
    .venv\\Scripts\\python scripts\\visalia_scrape.py --max 10      # first 10 docs only
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

JURISDICTION = "visalia"
PORTAL = (
    "https://www.visalia.gov/AgendaCenter/Search/"
    "?term=&CIDs=all&startDate=&endDate=&dateRange=&dateSelector="
)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
MAX_BYTES = 20 * 1024 * 1024  # 20 MB cap (agenda packets deferred)
MIN_BYTES = 1_000  # < 1 KB = challenge page, not PDF
THROTTLE_SEC = 1.0


def _read_token() -> str:
    """Read webhook token from file or environment."""
    env_token = os.environ.get("ODIA_WEBHOOK_TOKEN", "").strip()
    if env_token:
        return env_token

    appdata = os.environ.get("APPDATA", "")
    token_path = Path(appdata) / "ODIA" / "webhook_token"
    if token_path.exists():
        token = token_path.read_text(encoding="utf-8").strip()
        if token:
            return token

    print(
        f"ERROR: No webhook token found. Set ODIA_WEBHOOK_TOKEN or create {token_path}"
    )
    sys.exit(1)


def _fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _extract_links(html: str) -> list[str]:
    """Extract unique /AgendaCenter/ViewFile/... hrefs and prepend base URL."""
    raw = re.findall(r'href="(/AgendaCenter/ViewFile/[^"]+)"', html)
    seen: set[str] = set()
    links = []
    for path in raw:
        full = f"https://www.visalia.gov{path}"
        if full not in seen:
            seen.add(full)
            links.append(full)
    return links


def _download(url: str, dest: Path) -> int | None:
    """Download URL to dest. Returns byte count or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return len(data)
    except Exception as exc:
        print(f"DOWNLOAD_FAILED: {exc}")
        return None


def _post_to_webhook(
    token: str, file_path: Path, jurisdiction: str, webhook_url: str
) -> dict:
    """Multipart POST file to the webhook. Returns parsed JSON response."""
    import http.client
    import json
    import mimetypes
    import urllib.parse

    boundary = "ODIAboundary1234567890"
    content_type = f"multipart/form-data; boundary={boundary}"

    file_bytes = file_path.read_bytes()
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/pdf"

    body_parts = []
    # jurisdiction_id field
    body_parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="jurisdiction_id"\r\n\r\n'
        f"{jurisdiction}\r\n"
    )
    # file field
    body_parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    )
    body = (
        "".join(body_parts).encode("utf-8")
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )

    parsed = urllib.parse.urlparse(webhook_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=120)
    conn.request(
        "POST",
        parsed.path,
        body=body,
        headers={
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
            "X-ODIA-Webhook-Token": token,
        },
    )
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except Exception:
        return {"error": raw[:200], "status_code": resp.status}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", type=int, default=8000, help="Backend port (default 8000)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="List links only, no downloads"
    )
    parser.add_argument(
        "--max", type=int, default=0, help="Max documents to process (0=all)"
    )
    args = parser.parse_args()

    webhook_url = f"http://127.0.0.1:{args.port}/api/v1/webhook/ingest-and-analyze"
    work_dir = Path(os.environ.get("TEMP", "C:\\Temp")) / "visalia_pdfs"
    work_dir.mkdir(parents=True, exist_ok=True)

    token = _read_token()
    print("==== Visalia autonomous ingest (Python/Windows) ====")
    print(f"Token:    {token[:8]}...")
    print(f"Work dir: {work_dir}")
    print(f"Webhook:  {webhook_url}")
    print()

    print(">>> Fetching AgendaCenter search page...")
    try:
        html = _fetch_html(PORTAL)
    except Exception as exc:
        print(f"ERROR fetching portal: {exc}")
        sys.exit(1)
    print(f"    Got {len(html)} bytes of HTML")

    print(">>> Extracting document links...")
    links = _extract_links(html)
    total = len(links)
    print(f"    Found {total} unique document links")
    if total == 0:
        print("ERROR: 0 links — page structure may have changed")
        sys.exit(1)

    if args.dry_run:
        for i, url in enumerate(links, 1):
            print(f"  [{i:3d}] {url}")
        print(f"\n[dry-run] {total} links found. Remove --dry-run to download.")
        return

    if args.max:
        links = links[: args.max]
        print(f"    Capped at {args.max} documents (--max flag)")

    success = failed = already_seen = 0

    for i, url in enumerate(links, 1):
        # Build a stable filename from the URL
        parts = url.rsplit("/", 2)
        doc_type = parts[-2].lower() if len(parts) >= 2 else "doc"
        doc_id = parts[-1].lstrip("_")
        local = work_dir / f"{JURISDICTION}_{doc_type}_{doc_id}.pdf"

        print(
            f"[{i:3d}/{len(links)}] {doc_type}_{doc_id[:30]:<30}", end="  ", flush=True
        )

        nbytes = _download(url, local)
        if nbytes is None:
            failed += 1
            continue

        if nbytes < MIN_BYTES:
            print(f"TOO_SMALL ({nbytes} bytes — likely challenge page)")
            failed += 1
            local.unlink(missing_ok=True)
            continue

        if nbytes > MAX_BYTES:
            print(f"TOO_LARGE_SKIPPED ({nbytes:,} bytes — agenda packet, deferred)")
            failed += 1
            continue

        resp = _post_to_webhook(token, local, JURISDICTION, webhook_url)

        if resp.get("already_seen"):
            print(f"ALREADY_SEEN ({nbytes:,} bytes)")
            already_seen += 1
        elif resp.get("status") == "ok":
            count = (resp.get("findings") or {}).get("count", "?")
            print(f"OK ({nbytes:,} bytes, {count} findings)")
            success += 1
        else:
            print(f"POST_FAILED: {str(resp)[:100]}")
            failed += 1

        time.sleep(THROTTLE_SEC)

    print()
    print("==== Done ====")
    print(f"Success (new):   {success}")
    print(f"Already seen:    {already_seen}")
    print(f"Failed/skipped:  {failed}")
    print(f"Total processed: {i} / {len(links)}")
    print(f"\nPDFs cached at:  {work_dir}")


if __name__ == "__main__":
    main()
