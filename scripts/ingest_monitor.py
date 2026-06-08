"""ingest_monitor.py — Live dashboard for bulk_ingest.py progress.

Queries oraculus_audit.db every 30 seconds and prints a per-jurisdiction
summary table. Run in a second terminal window while bulk_ingest.py runs.

Usage:
    python scripts/ingest_monitor.py
    python scripts/ingest_monitor.py --interval 60
    python scripts/ingest_monitor.py --once
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _REPO_ROOT / "oraculus_audit.db"


# ---------------------------------------------------------------------------
# DB helpers — raw sqlite3 so this script has zero heavy imports
# ---------------------------------------------------------------------------


def _query(sql: str) -> list[sqlite3.Row]:
    if not _DB_PATH.exists():
        return []
    try:
        con = sqlite3.connect(str(_DB_PATH), timeout=5)
        con.row_factory = sqlite3.Row
        rows = con.execute(sql).fetchall()
        con.close()
        return rows
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

_COL_J = 22
_COL_D = 7
_COL_F = 10
_COL_S = 9
_COL_L = 30
_RULE_WIDTH = _COL_J + _COL_D + _COL_F + _COL_S + _COL_L + 10


def _render() -> None:
    # Per-jurisdiction aggregates
    juris_rows = _query(
        """
        SELECT
            d.jurisdiction,
            COUNT(DISTINCT d.id)                AS docs,
            COALESCE(SUM(a.anomaly_count), 0)   AS findings,
            ROUND(AVG(a.scalar_score), 3)       AS avg_score
        FROM documents d
        LEFT JOIN analyses a ON a.document_id = d.document_id
        GROUP BY d.jurisdiction
        ORDER BY docs DESC
        """
    )

    # Top detector layer per jurisdiction
    layer_rows = _query(
        """
        SELECT d.jurisdiction, an.layer, COUNT(*) AS cnt
        FROM anomalies an
        JOIN analyses  a  ON a.id           = an.analysis_id
        JOIN documents d  ON d.document_id  = a.document_id
        WHERE an.layer IS NOT NULL AND an.layer != ''
        GROUP BY d.jurisdiction, an.layer
        """
    )
    top_layer: dict[str, str] = {}
    for lr in layer_rows:
        j, layer, cnt = lr["jurisdiction"] or "unknown", lr["layer"], lr["cnt"]
        if j not in top_layer:
            top_layer[j] = (layer, cnt)
        elif cnt > top_layer[j][1]:
            top_layer[j] = (layer, cnt)
    top_layer = {k: v[0] for k, v in top_layer.items()}

    # Severity breakdown (global)
    sev_rows = _query(
        "SELECT severity, COUNT(*) AS cnt FROM anomalies "
        "WHERE severity IS NOT NULL GROUP BY severity"
    )
    sev = {r["severity"]: r["cnt"] for r in sev_rows}

    # Recent documents ingested
    recent = _query(
        """
        SELECT d.jurisdiction, d.title, a.anomaly_count, a.analysis_timestamp
        FROM documents d
        JOIN analyses a ON a.document_id = d.document_id
        ORDER BY a.analysis_timestamp DESC
        LIMIT 5
        """
    )

    total_docs = sum(r["docs"] for r in juris_rows)
    total_findings = sum(r["findings"] for r in juris_rows)

    os.system("cls" if os.name == "nt" else "clear")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  ODIA Ingest Monitor  --  {now}")
    print(f"  DB: {_DB_PATH}")
    print()

    hdr = (
        f"  {'Jurisdiction':<{_COL_J}} "
        f"{'Docs':>{_COL_D}} "
        f"{'Findings':>{_COL_F}}  "
        f"{'Avg Score':>{_COL_S}}  "
        f"{'Top Detector':<{_COL_L}}"
    )
    print(hdr)
    print("  " + "-" * _RULE_WIDTH)

    for r in juris_rows:
        j = (r["jurisdiction"] or "unknown")[:_COL_J]
        score = f"{r['avg_score']:.3f}" if r["avg_score"] is not None else "—"
        tl = top_layer.get(r["jurisdiction"] or "unknown", "—")[:_COL_L]
        print(
            f"  {j:<{_COL_J}} "
            f"{r['docs']:>{_COL_D}} "
            f"{r['findings']:>{_COL_F}}  "
            f"{score:>{_COL_S}}  "
            f"{tl:<{_COL_L}}"
        )

    print("  " + "-" * _RULE_WIDTH)
    print(f"  {'TOTAL':<{_COL_J}} {total_docs:>{_COL_D}} {total_findings:>{_COL_F}}")
    print()

    h = sev.get("high", 0)
    m = sev.get("medium", 0)
    lo = sev.get("low", 0)
    print(f"  Severity  high={h:,}  medium={m:,}  low={lo:,}")
    print()

    if recent:
        print("  Recent (last 5 ingested):")
        for rec in recent:
            j = (rec["jurisdiction"] or "?")[:14]
            title = (rec["title"] or "?")[:38]
            ts = (rec["analysis_timestamp"] or "")[:16]
            print(
                f"    {j:<14}  {title:<38}  "
                f"{rec['anomaly_count']:>4} findings  {ts}"
            )
        print()

    print("  Ctrl+C to exit")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Live ingest monitor for ODIA")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="SEC",
        help="Refresh interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print once and exit (no auto-refresh)",
    )
    args = parser.parse_args()

    if not _DB_PATH.exists():
        print(f"DB not found: {_DB_PATH}")
        print("Run bulk_ingest.py first to populate it.")
        sys.exit(1)

    if args.once:
        _render()
        return

    try:
        while True:
            _render()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n  Monitor stopped.")


if __name__ == "__main__":
    main()
