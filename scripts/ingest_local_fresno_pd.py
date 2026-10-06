"""ingest_local_fresno_pd.py — Bulk ingest manually-collected Fresno PD corpus.

POSTs every PDF in the FRES-ODIA folder to ODIA's webhook for Tier 1
analysis and DB persistence.

Corpus contains:
  - Fresno PD Annual Reports (2011-2024)
  - Monthly crime statistics (2014-2020)
  - Bias-Based Profiling Reviews (2016-2024)
  - AB 481 Military Equipment Reports (2025)
  - Policy Manual (July 16, 2026, Redacted)
  - Policy 706 (Military Equipment Funding, Acquisition and Use)
  - Use of Force 2024 Year-End Report
  - Legistar keyword-search agendas and minutes (Flock Safety / Axon)
  - ADA Compliance Reports (2016)
  - Personnel Survey (2018)

Jurisdiction: fresno-pd (City of Fresno / Fresno Police Department)
Distinct from: fresnocounty (Fresno County BOS corpus, already ingested)

Known large files (allow extra time):
  AnnualReport2011.pdf     ~31.6 MB
  AnnualReport2012.pdf     ~28.4 MB
  AnnualReport2013.pdf     ~34.5 MB
  AnnualReport2014.pdf     ~21.7 MB
  2018-Annual-Report.pdf   ~17.9 MB
  PolicyManual-7-16-26_Redacted.pdf  ~15.3 MB

Usage:
    # Desktop backend must be running first (port 18741):
    .venv\\Scripts\\python scripts\\ingest_local_fresno_pd.py --dry-run
    .venv\\Scripts\\python scripts\\ingest_local_fresno_pd.py

    # Dev server:
    .venv\\Scripts\\python scripts\\ingest_local_fresno_pd.py --port 8000
"""

from __future__ import annotations

import argparse
import http.client
import json
import mimetypes
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

JURISDICTION = "fresno-pd"
WEBHOOK_PORT = 18741
WEBHOOK_PATH = "/api/v1/webhook/ingest-and-analyze"

SOURCE_DIR = Path(r"C:\Users\yahua\O.D.I.A. Arcade\O.D.I.A\FRES-ODIA")

# Files above this size get a longer timeout (seconds)
LARGE_FILE_THRESHOLD_MB = 10
TIMEOUT_STANDARD = 300
TIMEOUT_LARGE = 600
MAX_FILE_SIZE_MB = 50


def _read_token() -> str:
    import os

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

    size_mb = file_path.stat().st_size / (1024 * 1024)
    timeout = TIMEOUT_LARGE if size_mb >= LARGE_FILE_THRESHOLD_MB else TIMEOUT_STANDARD

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
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
        description="Ingest Fresno PD manually-collected corpus into ODIA"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="List files without POSTing"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=WEBHOOK_PORT,
        help=f"Backend port (default {WEBHOOK_PORT})",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE_DIR,
        help="Folder containing FRES-ODIA documents",
    )
    args = parser.parse_args()

    source = args.source
    if not source.exists():
        print(f"ERROR: Source folder not found: {source}")
        sys.exit(1)

    # Collect all PDFs in flat directory, sorted by name
    all_pdfs = sorted(source.glob("*.pdf"))

    # Partition by size for reporting
    large = [
        f
        for f in all_pdfs
        if f.stat().st_size / (1024 * 1024) >= LARGE_FILE_THRESHOLD_MB
    ]
    oversized = [
        f for f in all_pdfs if f.stat().st_size / (1024 * 1024) >= MAX_FILE_SIZE_MB
    ]
    ingestible = [f for f in all_pdfs if f not in oversized]

    total_mb = sum(f.stat().st_size for f in ingestible) / (1024 * 1024)

    print("Fresno PD local corpus ingest")
    print(f"Jurisdiction: {JURISDICTION}")
    print(f"Source:       {source}")
    print(f"Files found:  {len(all_pdfs)} PDFs total")
    print(f"  Ingestible: {len(ingestible)}  ({total_mb:.1f} MB)")
    print(f"  Large (>{LARGE_FILE_THRESHOLD_MB} MB, extended timeout): {len(large)}")
    if oversized:
        print(f"  SKIPPED (>{MAX_FILE_SIZE_MB} MB): {len(oversized)}")
        for f in oversized:
            print(f"    {f.name}")
    print()

    if args.dry_run:
        print(f"{'File':<60}  {'MB':>6}  {'Timeout':>8}")
        print("-" * 80)
        for f in ingestible:
            size_mb = f.stat().st_size / (1024 * 1024)
            timeout = (
                TIMEOUT_LARGE
                if size_mb >= LARGE_FILE_THRESHOLD_MB
                else TIMEOUT_STANDARD
            )
            flag = " [LARGE]" if size_mb >= LARGE_FILE_THRESHOLD_MB else ""
            print(f"{f.name[:60]:<60}  {size_mb:>6.1f}  {timeout:>6}s{flag}")
        print(
            f"\n[dry-run] {len(ingestible)} files would be ingested. Remove --dry-run to proceed."
        )
        return

    token = _read_token()

    success = already_seen = failed = 0
    failed_files: list[str] = []

    for i, f in enumerate(ingestible, 1):
        size_mb = f.stat().st_size / (1024 * 1024)
        is_large = size_mb >= LARGE_FILE_THRESHOLD_MB
        label = f.name[:58]
        size_tag = f"[{size_mb:.1f} MB]" if is_large else f"({size_mb:.1f} MB)"
        print(
            f"[{i:3d}/{len(ingestible)}] {label:<58} {size_tag}", end="  ", flush=True
        )

        try:
            resp = _post_file(f, token, port=args.port)
        except Exception as exc:
            print(f"ERROR: {exc}")
            failed += 1
            failed_files.append(f.name)
            continue

        if resp.get("already_seen"):
            print("ALREADY_SEEN")
            already_seen += 1
        elif resp.get("status") == "ok":
            count = (resp.get("findings") or {}).get("count", "?")
            print(f"OK  ({count} findings)")
            success += 1
        else:
            err = str(resp)[:120]
            print(f"FAILED: {err}")
            failed += 1
            failed_files.append(f.name)

    # Summary
    print(f"\n{'='*60}")
    print("Fresno PD ingest complete")
    print(f"{'='*60}")
    print(f"  New / analyzed:  {success}")
    print(f"  Already seen:    {already_seen}")
    print(f"  Failed:          {failed}")
    if failed_files:
        print("\n  Failed files:")
        for name in failed_files:
            print(f"    {name}")

    if success > 0:
        print("\nNext steps:")
        print("  1. Rebuild RAG index (includes fresnocounty + fresno-pd):")
        print("     .venv\\Scripts\\python scripts\\build_rag_index.py")
        print("  2. Re-export MAS corpus for fresno-pd:")
        print(
            "     .venv\\Scripts\\python scripts\\export_mas_corpus.py --jurisdiction fresno-pd"
        )


if __name__ == "__main__":
    main()
