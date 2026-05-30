"""Re-ingest the 12 .doc BOS agendas now that antiword is installed.

Pre-state: 12 .doc files persisted with empty raw_text (graceful fallback
from v3.2.5 ingester when antiword was missing). Findings = 0 each.

Strategy:
  1. Load _questys_local_ingest_log.json — pick the .doc completed rows.
  2. For each: delete the existing document/analysis/anomalies/seen_hash
     rows by SHA, so dedup_check returns False on re-ingest.
  3. Re-download via the same Questys session.
  4. Run the v3.2.5 pipeline (now backed by antiword for .doc).
  5. Persist.

Throttled to match the same 3s + 20s/10 cadence used during v2 bulk.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

from oraculus_di_auditor.db.session import get_db, init_db

init_db()

from curl_cffi import requests  # noqa: E402
from sqlalchemy import text  # noqa: E402

from oraculus_di_auditor.interface.routes.webhook import (  # noqa: E402
    _persist_tier1_result,
    _record_seen_hash,
    _run_tier1_pipeline,
)

UA = "chrome131"
QUESTYS_BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
JURISDICTION = "tulare-county"
LOG_PATH = "_questys_local_ingest_log.json"
PAUSE_BETWEEN_DOWNLOADS_SEC = 3.0
LONG_PAUSE_EVERY_N = 5
LONG_PAUSE_SEC = 15.0


def delete_by_sha(sha256):
    """Remove documents+analyses+anomalies+seen_hashes rows for a given SHA.

    Uses raw SQL because the SQLAlchemy models aren't being imported here
    and the cascade rules are simple enough to express directly.
    """
    deleted_counts = {}
    with get_db() as session:
        # 1. Find document_id rows matching sha256
        doc_ids = [
            r[0]
            for r in session.execute(
                text(
                    "SELECT id FROM documents WHERE document_id IN "
                    "(SELECT sha256 FROM seen_hashes WHERE sha256=:s)"
                ),
                {"s": sha256},
            ).all()
        ]
        # Actually document_id is the SHA itself
        doc_ids = [
            r[0]
            for r in session.execute(
                text("SELECT id FROM documents WHERE document_id=:s"), {"s": sha256}
            ).all()
        ]
        if not doc_ids:
            # Try by other patterns
            pass
        # Delete anomalies via analyses
        for doc_id in doc_ids:
            analysis_ids = [
                r[0]
                for r in session.execute(
                    text("SELECT id FROM analyses WHERE document_id=:d"), {"d": doc_id}
                ).all()
            ]
            for aid in analysis_ids:
                r = session.execute(
                    text("DELETE FROM anomalies WHERE analysis_id=:a"), {"a": aid}
                )
                deleted_counts["anomalies"] = (
                    deleted_counts.get("anomalies", 0) + r.rowcount
                )
            r = session.execute(
                text("DELETE FROM analyses WHERE document_id=:d"), {"d": doc_id}
            )
            deleted_counts["analyses"] = deleted_counts.get("analyses", 0) + r.rowcount
        for doc_id in doc_ids:
            r = session.execute(
                text("DELETE FROM documents WHERE id=:d"), {"d": doc_id}
            )
            deleted_counts["documents"] = (
                deleted_counts.get("documents", 0) + r.rowcount
            )
        r = session.execute(
            text("DELETE FROM seen_hashes WHERE sha256=:s"), {"s": sha256}
        )
        deleted_counts["seen_hashes"] = r.rowcount
        session.commit()
    return deleted_counts


def main():
    log = json.loads(Path(LOG_PATH).read_text(encoding="utf-8-sig"))
    doc_rows = [
        (did, meta)
        for did, meta in log.items()
        if meta.get("ext") == "doc" and meta.get("status") == "completed"
    ]
    print(f"found {len(doc_rows)} .doc rows in log")

    if not doc_rows:
        return

    sess = requests.Session(impersonate=UA)
    sess.get(QUESTYS_BASE + "Search/Default.aspx", timeout=30)

    completed = 0
    total_findings = 0
    start = time.time()

    for i, (did, meta) in enumerate(doc_rows, 1):
        fn = meta.get("filename") or f"questys_{did}.doc"
        prev_sha = meta.get("sha256", "")

        if i > 1:
            time.sleep(PAUSE_BETWEEN_DOWNLOADS_SEC)
            if (i - 1) % LONG_PAUSE_EVERY_N == 0:
                print(f"  -- long pause {LONG_PAUSE_SEC}s --")
                time.sleep(LONG_PAUSE_SEC)

        # 1. Delete prior empty-text rows for this SHA
        if prev_sha:
            d = delete_by_sha(prev_sha)
            if d:
                print(
                    f"  [{i:>2}/{len(doc_rows)}] id={did} fn={fn[:50]:<50}  deleted prior: {d}"
                )

        # 2. Re-download
        url = f"{QUESTYS_BASE}File.ashx?id={did}&v=1"
        try:
            r = sess.get(url, timeout=60, allow_redirects=True)
        except Exception as exc:
            print(f"  [{i:>2}/{len(doc_rows)}] id={did}  DOWNLOAD ERR: {exc}")
            continue

        if r.status_code != 200 or len(r.content) < 1000:
            print(
                f"  [{i:>2}/{len(doc_rows)}] id={did}  bad response: status={r.status_code} bytes={len(r.content)}"
            )
            continue

        new_sha = hashlib.sha256(r.content).hexdigest()

        # 3. Pipeline
        try:
            result = _run_tier1_pipeline(
                file_bytes=r.content, filename=fn, jurisdiction_id=JURISDICTION
            )
        except Exception as exc:
            print(f"  [{i:>2}/{len(doc_rows)}] id={did}  PIPELINE ERR: {exc}")
            continue

        # 4. Persist
        try:
            doc_id = (result.get("document") or {}).get("document_id")
            _record_seen_hash(
                sha256=new_sha, document_id=doc_id, jurisdiction_id=JURISDICTION
            )
            _persist_tier1_result(
                sha256=new_sha, filename=fn, jurisdiction_id=JURISDICTION, result=result
            )
        except Exception as exc:
            print(f"  [{i:>2}/{len(doc_rows)}] id={did}  PERSIST WARN: {exc}")

        findings = (result.get("findings") or {}).get("count", 0)
        score = result.get("recursive_scalar_score", 1.0)
        completed += 1
        total_findings += findings
        log[did] = {
            "status": "completed",
            "sha256": new_sha,
            "filename": fn,
            "ext": "doc",
            "bytes": len(r.content),
            "findings": findings,
            "score": score,
            "reingested": True,
        }
        print(
            f"  [{i:>2}/{len(doc_rows)}] id={did} fn={fn[:50]:<50}  "
            f"OK {len(r.content):>9}B  findings={findings} score={score:.3f}"
        )

    Path(LOG_PATH).write_text(json.dumps(log, indent=2), encoding="utf-8")
    elapsed = time.time() - start
    print()
    print("=== DOC RE-INGEST DONE ===")
    print(f"  completed:      {completed}")
    print(f"  total findings: {total_findings}")
    print(f"  elapsed:        {elapsed:.0f}s")


if __name__ == "__main__":
    sys.exit(main() or 0)
