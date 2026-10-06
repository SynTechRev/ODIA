"""ingest_tcpd.py — Harvest Tulare County Probation Department records via Questys.

Searches the Tulare County public document portal for records related to
the Probation Department, then posts each to ODIA's webhook for full
Tier 1 analysis and DB persistence.

The portal URL is the same one used for the tulare-county corpus (95 docs).
TCPD budget items, contracts, and board-approved agreements surface in BOS
agenda packets when searched with probation-specific terms.

Usage:
    # Backend must be running on port 8000 first:
    # .venv\\Scripts\\python -m uvicorn oraculus_di_auditor.interface.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log

    .venv\\Scripts\\python scripts\\ingest_tcpd.py --dry-run   # list what would be harvested
    .venv\\Scripts\\python scripts\\ingest_tcpd.py             # full harvest + ingest
"""

from __future__ import annotations

import argparse
import http.client
import json
import mimetypes
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

PORTAL_URL = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
JURISDICTION = "tcpd"
WEBHOOK_PORT = 18741  # desktop app backend; use --port 8000 for dev server
WEBHOOK_PATH = "/api/v1/webhook/ingest-and-analyze"
CACHE_DIR = _REPO_ROOT / "cache" / "tcpd_questys"

# Search terms targeting Probation Department records in the BOS portal
TCPD_SEARCH_TERMS = (
    # Core department terms
    "probation",
    "juvenile",
    "delinquency",
    "detention",
    "youth",
    "rehabilitation",
    "parole",
    "supervision",
    "reentry",
    "offender",
    "corrections",
    # Statutory programs — major TCPD funding streams
    "AB109",
    "AB 109",
    "SB678",
    "SB 678",
    "Prop 47",
    "realignment",
    "PRCS",  # Post-Release Community Supervision
    "pretrial",
    "diversion",
    # Technology / surveillance
    "electronic monitoring",
    "GPS monitoring",
    "ankle monitor",
    "body camera",
    "day reporting",  # Day Reporting Center
    "DRC",
    # Vendors known to contract with CA probation depts
    "Geo",  # The GEO Group — private corrections/reentry
    "GEO Group",
    "CoreCivic",
    "BI Incorporated",  # ankle monitoring (part of GEO)
    "SCRAM",  # alcohol monitoring
    "Vigilant",  # ALPR crossover
    # Budget / finance terms that surface BOS-approved TCPD items
    "community corrections",
    "county probation",
    "probation department",
    "mandatory supervision",
    "mental health court",
    "drug court",
    "substance abuse",
    "recidivism",
    "SB 82",  # Drug courts funding
    "Title IV-E",  # Federal foster care / juvenile justice funding
)


def _read_token() -> str:
    env_token = os.environ.get("ODIA_WEBHOOK_TOKEN", "").strip()
    if env_token:
        return env_token
    token_path = Path(os.environ.get("APPDATA", "")) / "ODIA" / "webhook_token"
    if token_path.exists():
        token = token_path.read_text(encoding="utf-8").strip()
        if token:
            return token
    print(f"ERROR: No webhook token at {token_path}")
    sys.exit(1)


def _post_file(file_path: Path, token: str, port: int = WEBHOOK_PORT) -> dict:
    boundary = "ODIAboundary1234567890"
    file_bytes = file_path.read_bytes()
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/pdf"
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="jurisdiction_id"\r\n\r\n'
            f"{JURISDICTION}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode()
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=300)
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
        return {"error": raw[:300], "http_status": resp.status}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--port",
        type=int,
        default=WEBHOOK_PORT,
        help="Backend port (default 18741 = desktop app; use 8000 for dev server)",
    )
    args = parser.parse_args()
    webhook_port = args.port

    try:
        from oraculus_di_auditor.adapters.questys_adapter import QuestysAdapter
    except ImportError as exc:
        print(f"ERROR: {exc}\nRun: pip install -e '.[dev]'")
        sys.exit(1)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"TCPD Questys harvest — portal: {PORTAL_URL}")
    print(f"Search terms: {len(TCPD_SEARCH_TERMS)}")
    print(f"Cache dir: {CACHE_DIR}")
    print()

    adapter = QuestysAdapter(
        portal_url=PORTAL_URL,
        cache_dir=CACHE_DIR,
        search_terms=TCPD_SEARCH_TERMS,
        pause_sec=3.0,
    )

    print("Warming Questys session...")
    adapter.warm_session()

    print("Harvesting document IDs...")
    catalog = adapter.harvest_ids()
    print(f"Found {len(catalog)} unique documents\n")

    if args.dry_run:
        for doc_id, meta in list(catalog.items())[:20]:
            print(
                f"  id={doc_id}  {meta.filename}  (via: {', '.join(meta.found_via[:2])})"
            )
        if len(catalog) > 20:
            print(f"  ... and {len(catalog) - 20} more")
        print(
            f"\n[dry-run] {len(catalog)} docs found. Remove --dry-run to download + ingest."
        )
        return

    token = _read_token()
    success = failed = already_seen = 0

    for i, (doc_id, meta) in enumerate(catalog.items(), 1):
        print(
            f"[{i}/{len(catalog)}] id={doc_id} {meta.filename[:50]}",
            end="  ",
            flush=True,
        )

        dl = adapter.download(doc_id)
        if dl is None:
            print("DOWNLOAD_FAILED")
            failed += 1
            continue

        # Save to cache
        ext = meta.ext or "pdf"
        local = CACHE_DIR / f"tcpd_{doc_id}.{ext}"
        local.write_bytes(dl.content)

        resp = _post_file(local, token, port=webhook_port)
        if resp.get("already_seen"):
            print(f"ALREADY_SEEN ({len(dl.content):,} bytes)")
            already_seen += 1
        elif resp.get("status") == "ok":
            count = (resp.get("findings") or {}).get("count", "?")
            print(f"OK ({len(dl.content):,} bytes, {count} findings)")
            success += 1
        else:
            print(f"POST_FAILED: {resp}")
            failed += 1

    print("\n==== Done ====")
    print(f"New:          {success}")
    print(f"Already seen: {already_seen}")
    print(f"Failed:       {failed}")
    if success > 0:
        print("\nNext: .venv\\Scripts\\python scripts\\build_rag_index.py")


if __name__ == "__main__":
    main()
