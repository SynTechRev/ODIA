"""post_large_packets.py — Post already-downloaded large Visalia agenda packets to ODIA.

These are the 9 files that visalia_scrape.py skipped because they exceeded 20 MB.
They were downloaded to %TEMP%\\visalia_pdfs\\ and are ready to post.

Each file runs the full Tier 1 audit pipeline — expect 3-10 minutes per file.

Usage:
    .venv\\Scripts\\python scripts\\post_large_packets.py
"""

from __future__ import annotations

import http.client
import json
import mimetypes
import os
import sys
from pathlib import Path

PORT = 8000
WEBHOOK_PATH = "/api/v1/webhook/ingest-and-analyze"
JURISDICTION = "visalia"
TEMP_DIR = Path(os.environ.get("TEMP", "C:\\Temp")) / "visalia_pdfs"


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


def post_file(file_path: Path, token: str) -> dict:
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

    conn = http.client.HTTPConnection("127.0.0.1", PORT, timeout=600)
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
    token = _read_token()

    large_files = sorted(
        [f for f in TEMP_DIR.glob("*.pdf") if f.stat().st_size > 20 * 1024 * 1024],
        key=lambda f: f.stat().st_size,
    )

    if not large_files:
        print(f"No files > 20 MB found in {TEMP_DIR}")
        return

    print(f"Found {len(large_files)} large agenda packets to post\n")

    success = failed = already_seen = 0
    for i, f in enumerate(large_files, 1):
        mb = f.stat().st_size / 1024 / 1024
        print(
            f"[{i}/{len(large_files)}] {f.name} ({mb:.1f} MB) — posting...", flush=True
        )
        try:
            resp = post_file(f, token)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            failed += 1
            continue

        if resp.get("already_seen"):
            print("  ALREADY_SEEN")
            already_seen += 1
        elif resp.get("status") == "ok":
            count = (resp.get("findings") or {}).get("count", "?")
            print(f"  OK — {count} findings")
            success += 1
        else:
            print(f"  FAILED: {resp}")
            failed += 1

    print("\n==== Done ====")
    print(f"New:          {success}")
    print(f"Already seen: {already_seen}")
    print(f"Failed:       {failed}")
    if success > 0:
        print("\nNext: .venv\\Scripts\\python scripts\\build_rag_index.py")


if __name__ == "__main__":
    main()
