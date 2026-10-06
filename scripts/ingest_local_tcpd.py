"""ingest_local_tcpd.py — Bulk ingest locally-collected TCPD documents.

POSTs every PDF in the TCPD-ODIA corpus folder to ODIA's webhook for
Tier 1 analysis and DB persistence.  The folder is organized into three
division subdirectories that mirror the TCPD website structure:

    CCP/    Community Corrections Partnership (AB 109 realignment oversight)
    JJDPC/  Juvenile Justice and Delinquency Prevention Commission
    MJJCC/  Multi-agency Juvenile Justice Coordinating Committee

ODIA's SHA-256 dedup will mark any documents already ingested from the
prior Questys harvest as already_seen.

Usage:
    # Desktop backend must be running first (port 18741 default):
    .venv\\Scripts\\python scripts\\ingest_local_tcpd.py --dry-run
    .venv\\Scripts\\python scripts\\ingest_local_tcpd.py

    # Dev server on port 8000:
    .venv\\Scripts\\python scripts\\ingest_local_tcpd.py --port 8000
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

JURISDICTION = "tcpd"
WEBHOOK_PORT = 18741
WEBHOOK_PATH = "/api/v1/webhook/ingest-and-analyze"

# Local corpus folder — organized by division
SOURCE_DIR = Path(r"C:\Users\yahua\O.D.I.A. Arcade\O.D.I.A\TCPD-ODIA")

# Divisions to ingest, in order. The folder name is used in progress output.
DIVISIONS = ["CCP", "JJDPC", "MJJCC"]


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
    parser = argparse.ArgumentParser(
        description="Ingest locally-collected TCPD corpus into ODIA"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be ingested without POSTing",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=WEBHOOK_PORT,
        help=f"Backend port (default {WEBHOOK_PORT} = desktop; 8000 = dev server)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE_DIR,
        help="Root folder containing CCP/ JJDPC/ MJJCC/ subdirectories",
    )
    args = parser.parse_args()

    source = args.source
    if not source.exists():
        print(f"ERROR: Source folder not found: {source}")
        sys.exit(1)

    # Collect files per division
    division_files: dict[str, list[Path]] = {}
    for div in DIVISIONS:
        div_path = source / div
        if not div_path.exists():
            print(f"  WARN: Division folder not found, skipping: {div_path}")
            division_files[div] = []
            continue
        pdfs = sorted(div_path.glob("*.pdf"))
        division_files[div] = pdfs

    total_files = sum(len(f) for f in division_files.values())
    print("TCPD local corpus ingest")
    print(f"Source:     {source}")
    print(f"Divisions:  {', '.join(DIVISIONS)}")
    print("Files found:")
    for div, files in division_files.items():
        print(f"  {div:6s}  {len(files):3d} PDFs")
    print(f"  {'TOTAL':6s}  {total_files:3d} PDFs")
    print()

    if args.dry_run:
        for div, files in division_files.items():
            print(f"[{div}]")
            for f in files:
                size_kb = f.stat().st_size // 1024
                print(f"  {f.name[:70]:<70s}  {size_kb:>5,} KB")
        print(f"\n[dry-run] {total_files} files found. Remove --dry-run to ingest.")
        return

    token = _read_token()
    webhook_port = args.port

    # Per-division counters
    totals = {"success": 0, "already_seen": 0, "failed": 0}
    div_results: dict[str, dict] = {}

    file_num = 0
    for div, files in division_files.items():
        div_success = div_already = div_failed = 0
        print(f"\n--- {div} ({len(files)} files) ---")

        for f in files:
            file_num += 1
            size_kb = f.stat().st_size // 1024
            label = f.name[:55]
            print(
                f"[{file_num}/{total_files}] {label:<55s} ({size_kb:>5,} KB)",
                end="  ",
                flush=True,
            )

            try:
                resp = _post_file(f, token, port=webhook_port)
            except Exception as exc:
                print(f"ERROR: {exc}")
                div_failed += 1
                totals["failed"] += 1
                continue

            if resp.get("already_seen"):
                print("ALREADY_SEEN")
                div_already += 1
                totals["already_seen"] += 1
            elif resp.get("status") == "ok":
                count = (resp.get("findings") or {}).get("count", "?")
                print(f"OK  ({count} findings)")
                div_success += 1
                totals["success"] += 1
            else:
                print(f"FAILED: {resp}")
                div_failed += 1
                totals["failed"] += 1

        div_results[div] = {
            "files": len(files),
            "success": div_success,
            "already_seen": div_already,
            "failed": div_failed,
        }

    # Summary
    print(f"\n{'='*60}")
    print("TCPD ingest complete")
    print(f"{'='*60}")
    print(f"{'Division':<10}  {'Files':>6}  {'New':>6}  {'Seen':>6}  {'Failed':>6}")
    print(f"{'-'*42}")
    for div, r in div_results.items():
        print(
            f"{div:<10}  {r['files']:>6}  {r['success']:>6}  {r['already_seen']:>6}  {r['failed']:>6}"
        )
    print(f"{'-'*42}")
    print(
        f"{'TOTAL':<10}  {total_files:>6}  {totals['success']:>6}  {totals['already_seen']:>6}  {totals['failed']:>6}"
    )

    if totals["success"] > 0:
        print("\nNext steps:")
        print("  1. Rebuild RAG index:")
        print("     .venv\\Scripts\\python scripts\\build_rag_index.py")
        print("  2. Re-export MAS corpus:")
        print("     .venv\\Scripts\\python scripts\\export_mas_corpus.py")


if __name__ == "__main__":
    main()
