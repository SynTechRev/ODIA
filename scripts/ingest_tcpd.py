"""ingest_tcpd.py — Harvest Tulare County BOS meeting agendas via PrimeGov.

Tulare County migrated from Questys CMX to PrimeGov (Granicus) for meeting
management. This script harvests Board of Supervisors PDF agendas going back
to 2006 and posts each to ODIA's webhook for full Tier 1 analysis and DB
persistence.

BOS meeting packets contain budget items, contracts, and board-approved
agreements for all county departments including the Probation Department.

Usage:
    # Backend must be running on port 8000 first:
    # .venv\\Scripts\\python -m uvicorn oraculus_di_auditor.interface.api:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log

    .venv\\Scripts\\python scripts\\ingest_tcpd.py --dry-run        # list meetings
    .venv\\Scripts\\python scripts\\ingest_tcpd.py --years 2026     # one year only
    .venv\\Scripts\\python scripts\\ingest_tcpd.py                  # full harvest
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

PORTAL_URL = "https://tularecounty.primegov.com"
BOS_COMMITTEE_ID = 25  # Board of Supervisors committee ID in PrimeGov
JURISDICTION = "tcpd"
WEBHOOK_PORT = 18741  # desktop app backend; use --port 8000 for dev server
WEBHOOK_PATH = "/api/v1/webhook/ingest-and-analyze"
CACHE_DIR = _REPO_ROOT / "cache" / "tcpd_primegov"


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
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="jurisdiction_id"\r\n\r\n'
            f"{JURISDICTION}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
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
    parser = argparse.ArgumentParser(description="Harvest TCPD/BOS docs from PrimeGov")
    parser.add_argument(
        "--dry-run", action="store_true", help="List meetings, don't download"
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        metavar="YEAR",
        help="Restrict to specific years (e.g. --years 2026 2025)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=WEBHOOK_PORT,
        help="Backend port (default 18741 = desktop; use 8000 for dev server)",
    )
    args = parser.parse_args()
    webhook_port = args.port

    try:
        from oraculus_di_auditor.adapters.primegov_adapter import PrimeGovAdapter
    except ImportError as exc:
        print(f"ERROR: {exc}\nRun: pip install -e '.[dev]'")
        sys.exit(1)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"TCPD/BOS PrimeGov harvest — portal: {PORTAL_URL}")
    print(f"Committee ID: {BOS_COMMITTEE_ID} (Board of Supervisors)")
    print(f"Cache dir: {CACHE_DIR}")
    if args.years:
        print(f"Years filter: {args.years}")
    print()

    adapter = PrimeGovAdapter(
        portal_url=PORTAL_URL,
        committee_id=BOS_COMMITTEE_ID,
        cache_dir=CACHE_DIR,
        pause_sec=2.0,
    )

    print("Loading PrimeGov session + CSRF token...")
    if not adapter.warm_session():
        print("ERROR: could not load CSRF token from PrimeGov portal")
        sys.exit(1)

    print("Listing available years...")
    if args.years:
        years = args.years
    else:
        years = adapter.get_available_years()
        print(f"Available years: {years}")

    print(f"Listing BOS meeting documents for {len(years)} year(s)...")
    docs = adapter.list_meeting_docs(years=years)
    print(f"Found {len(docs)} PDF agenda documents\n")

    if args.dry_run:
        for doc in docs[:30]:
            print(
                f"  meetingId={doc.meeting_id}  compiledFileId={doc.compiled_file_id}"
                f"  date={doc.meeting_date}  {doc.template_name}"
            )
        if len(docs) > 30:
            print(f"  ... and {len(docs) - 30} more")
        print(
            f"\n[dry-run] {len(docs)} docs found. Remove --dry-run to download + ingest."
        )
        return

    token = _read_token()
    success = failed = already_seen = 0

    for i, doc in enumerate(docs, 1):
        print(
            f"[{i}/{len(docs)}] {doc.meeting_date} meetingId={doc.meeting_id}"
            f" compiledFileId={doc.compiled_file_id}",
            end="  ",
            flush=True,
        )

        dl = adapter.download(doc)
        if dl is None:
            print("DOWNLOAD_FAILED")
            failed += 1
            continue

        local = CACHE_DIR / f"tcpd_{doc.meeting_id}_{doc.compiled_file_id}.pdf"
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
