"""Local in-process ingest of Questys File.ashx docs (v2 — throttled + DB-init).

v1 lessons:
- File.ashx requires a Questys session cookie (Search/Default.aspx GET sets it).
- After ~5 rapid downloads Questys throttles and returns a 14-byte response.
- The webhook-flow's _persist_tier1_result requires init_db() — calling
  it directly from a fresh process needs explicit DB init.

v2:
- init_db() before any pipeline call.
- Throttle: 3 sec between requests + 20 sec pause every 10 downloads.
- Retry tiny responses (< 1000 bytes from a non-html content-type) with
  60-sec backoff up to 3 attempts.
- Hard reject login-page HTML responses by content sniff.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

# CRITICAL: init_db before importing webhook helpers
from oraculus_di_auditor.db.session import init_db

init_db()

from curl_cffi import requests  # noqa: E402

from oraculus_di_auditor.interface.routes.webhook import (  # noqa: E402
    _dedup_check,
    _persist_tier1_result,
    _record_seen_hash,
    _run_tier1_pipeline,
)

UA = "chrome131"
QUESTYS_BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
JURISDICTION = "tulare-county"
MANIFEST = "_questys_harvested_ids.json"
LOG_PATH = "_questys_local_ingest_log.json"
EXT_FILTER = {".pdf", ".doc", ".docx", ".html", ".htm", ".tif", ".tiff"}

PAUSE_BETWEEN_DOWNLOADS_SEC = 3.0
LONG_PAUSE_EVERY_N = 10
LONG_PAUSE_SEC = 20.0

RETRY_BACKOFF_SEC = 60.0
MAX_RETRIES = 3
LOGIN_PAGE_MAX_BYTES = 60_000
MIN_REAL_FILE_BYTES = 1000  # below this is suspicious for PDF/DOC/TIFF


def is_login_page(content_type: str, body: bytes) -> bool:
    ct = (content_type or "").lower()
    if "text/html" not in ct:
        return False
    if len(body) > LOGIN_PAGE_MAX_BYTES:
        return False
    head = body[:8000].lower()
    return any(
        m in head
        for m in (
            b"login.aspx",
            b"<title>login",
            b"questys solutions",
            b"sign in",
        )
    )


def looks_like_real_file(content_type: str, body: bytes) -> bool:
    """True iff this looks like a non-trivial document of the expected type."""
    if len(body) < MIN_REAL_FILE_BYTES:
        return False
    ct = (content_type or "").lower()
    # If server says it's HTML and it's small, it's probably an error
    if "text/html" in ct and not body.lower().lstrip().startswith(b"<!doctype html"):
        return False
    return True


def fetch_with_retry(sess, url, ext_hint=""):
    """GET with retry on suspicious tiny responses."""
    last_resp = None
    for attempt in range(MAX_RETRIES):
        try:
            r = sess.get(url, timeout=60, allow_redirects=True)
        except Exception as exc:
            return None, f"network error: {exc}"
        last_resp = r
        ct = r.headers.get("content-type", "")
        if r.status_code != 200:
            return r, f"http {r.status_code}"
        if is_login_page(ct, r.content):
            return r, "login_page"
        if looks_like_real_file(ct, r.content):
            return r, "ok"
        # Suspicious tiny response — back off and retry
        print(
            f"    retry {attempt+1}/{MAX_RETRIES}: got {len(r.content)}B "
            f"ct={ct} — sleeping {RETRY_BACKOFF_SEC}s"
        )
        time.sleep(RETRY_BACKOFF_SEC)
    return (
        last_resp,
        f"persistent_tiny_response ({len(last_resp.content) if last_resp else 0}B)",
    )


def load_manifest():
    return json.loads(Path(MANIFEST).read_text(encoding="utf-8-sig"))["ids"]


def load_log():
    if Path(LOG_PATH).exists():
        try:
            return json.loads(Path(LOG_PATH).read_text(encoding="utf-8-sig"))
        except Exception:
            return {}
    return {}


def save_log(log):
    Path(LOG_PATH).write_text(json.dumps(log, indent=2), encoding="utf-8")


def main():
    manifest = load_manifest()
    log = load_log()

    # Resume: only skip rows that are TRULY done (completed + non-tiny bytes)
    todo = []
    for did, meta in manifest.items():
        prev = log.get(did)
        if (
            prev
            and prev.get("status") == "completed"
            and prev.get("bytes", 0) > MIN_REAL_FILE_BYTES
        ):
            continue
        ext = "." + (meta.get("ext") or "").lower()
        if ext not in EXT_FILTER:
            continue
        todo.append((did, meta))

    print(f"manifest: {len(manifest)} IDs  |  resume log: {len(log)} entries")
    print(
        f"to ingest: {len(todo)} (skipped {len(log) - sum(1 for d, _ in todo if d in log)} truly-done)"
    )

    if not todo:
        return

    sess = requests.Session(impersonate=UA)
    r = sess.get(QUESTYS_BASE + "Search/Default.aspx", timeout=30)
    print(
        f"session warmup: {r.status_code} ({len(r.content)}B)  cookies: {len(sess.cookies)}"
    )

    start = time.time()
    completed = 0
    findings_total = 0
    rejected_login = 0
    download_failed = 0

    for i, (did, meta) in enumerate(todo, 1):
        fn = meta.get("filename") or f"questys_{did}.{meta.get('ext', 'bin')}"
        ext = meta.get("ext", "")
        url = f"{QUESTYS_BASE}File.ashx?id={did}&v=1"

        # Throttling between downloads
        if i > 1:
            time.sleep(PAUSE_BETWEEN_DOWNLOADS_SEC)
            if (i - 1) % LONG_PAUSE_EVERY_N == 0:
                print(f"  -- long pause {LONG_PAUSE_SEC}s after {i-1} downloads --")
                time.sleep(LONG_PAUSE_SEC)

        r, status = fetch_with_retry(sess, url, ext_hint=ext)
        if status != "ok":
            if status == "login_page":
                rejected_login += 1
                log[did] = {
                    "status": "rejected_login_page",
                    "bytes": len(r.content) if r else 0,
                    "filename": fn,
                    "ext": ext,
                }
            else:
                download_failed += 1
                log[did] = {
                    "status": "download_failed",
                    "reason": status,
                    "bytes": len(r.content) if r else 0,
                    "filename": fn,
                    "ext": ext,
                }
            print(f"  [{i:>3}/{len(todo)}] id={did} fn={fn[:50]:<50}  FAIL: {status}")
            save_log(log)
            continue

        sha256 = hashlib.sha256(r.content).hexdigest()
        if _dedup_check(sha256):
            log[did] = {
                "status": "already_seen",
                "sha256": sha256,
                "filename": fn,
                "ext": ext,
                "bytes": len(r.content),
            }
            print(
                f"  [{i:>3}/{len(todo)}] id={did} fn={fn[:50]:<50}  dedup ({len(r.content)}B)"
            )
            continue

        try:
            result = _run_tier1_pipeline(
                file_bytes=r.content, filename=fn, jurisdiction_id=JURISDICTION
            )
        except Exception as exc:
            log[did] = {
                "status": "pipeline_failed",
                "error": str(exc)[:200],
                "bytes": len(r.content),
                "filename": fn,
                "ext": ext,
            }
            print(
                f"  [{i:>3}/{len(todo)}] id={did} fn={fn[:50]:<50}  PIPELINE ERR: {exc}"
            )
            save_log(log)
            continue

        try:
            doc_id = (result.get("document") or {}).get("document_id")
            _record_seen_hash(
                sha256=sha256, document_id=doc_id, jurisdiction_id=JURISDICTION
            )
            _persist_tier1_result(
                sha256=sha256, filename=fn, jurisdiction_id=JURISDICTION, result=result
            )
        except Exception as exc:
            print(f"  [{i:>3}/{len(todo)}] id={did}  persist warn: {exc}")

        findings_count = (result.get("findings") or {}).get("count", 0)
        score = result.get("recursive_scalar_score", 1.0)
        completed += 1
        findings_total += findings_count
        log[did] = {
            "status": "completed",
            "sha256": sha256,
            "filename": fn,
            "ext": ext,
            "bytes": len(r.content),
            "findings": findings_count,
            "score": score,
        }
        print(
            f"  [{i:>3}/{len(todo)}] id={did} fn={fn[:50]:<50}  "
            f"OK {len(r.content):>9}B findings={findings_count} score={score:.3f}"
        )

        if i % 5 == 0:
            save_log(log)

    save_log(log)
    elapsed = time.time() - start
    print()
    print("=== DONE ===")
    print(f"  completed:         {completed}")
    print(f"  download failed:   {download_failed}")
    print(f"  login-page reject: {rejected_login}")
    print(f"  total findings:    {findings_total}")
    print(f"  elapsed:           {elapsed:.0f}s ({elapsed/60:.1f} min)")


if __name__ == "__main__":
    sys.exit(main() or 0)
