"""triage_agent.py — Ranked review queue from oraculus_audit.db findings.

Scores every document by its finding profile and outputs a prioritized list
of documents that need human attention. Score formula weights critical and
high-severity findings most heavily while rewarding coverage across multiple
detector layers (cross-layer anomalies are harder to explain away).

Priority score (0-100):
    base   = critical*4 + high*2 + medium*1 + low*0.25
    layers = unique layers with findings (breadth bonus)
    score  = min(100, base * (1 + layers * 0.1)) * (1 - scalar_score)

Usage:
    python scripts/triage_agent.py
    python scripts/triage_agent.py --top 25
    python scripts/triage_agent.py --jurisdiction tulare
    python scripts/triage_agent.py --severity high     (docs with >= 1 high finding)
    python scripts/triage_agent.py --layer surveillance  (docs that hit that layer)
    python scripts/triage_agent.py --csv                  (also write CSV)
    python scripts/triage_agent.py --json                 (also write JSON)
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _REPO_ROOT / "oraculus_audit.db"
_OUT_DIR = _REPO_ROOT / "data" / "triage"

_SEVERITY_WEIGHTS = {"critical": 4.0, "high": 2.0, "medium": 1.0, "low": 0.25}


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(_DB_PATH), timeout=10)
    con.row_factory = sqlite3.Row
    return con


def _load_documents(
    con: sqlite3.Connection,
    jurisdiction: str | None,
    severity_filter: str | None,
    layer_filter: str | None,
) -> list[dict]:
    """Load documents with their aggregated finding profiles."""
    where_parts = ["1=1"]
    params: list[str] = []
    if jurisdiction:
        where_parts.append("d.jurisdiction = ?")
        params.append(jurisdiction)

    rows = con.execute(
        f"""
        SELECT
            d.document_id, d.title, d.jurisdiction, d.document_type,
            a.id AS analysis_id, a.scalar_score, a.anomaly_count,
            a.analysis_timestamp
        FROM documents d
        JOIN analyses a ON a.document_id = d.document_id
        WHERE {' AND '.join(where_parts)}
        """,
        params,
    ).fetchall()

    results: list[dict] = []
    for row in rows:
        findings = con.execute(
            """
            SELECT severity, layer, issue, anomaly_id
            FROM anomalies WHERE analysis_id = ?
            """,
            (row["analysis_id"],),
        ).fetchall()

        if not findings:
            continue

        # Apply filters
        if severity_filter and not any(
            f["severity"] == severity_filter for f in findings
        ):
            continue
        if layer_filter and not any(f["layer"] == layer_filter for f in findings):
            continue

        # Severity counts
        sev: dict[str, int] = {}
        layers_hit: set[str] = set()
        top_issues: list[str] = []
        for f in findings:
            s = f["severity"] or "low"
            sev[s] = sev.get(s, 0) + 1
            if f["layer"]:
                layers_hit.add(f["layer"])
            # Collect top critical/high issues for the summary
            if f["severity"] in ("critical", "high") and len(top_issues) < 3:
                top_issues.append(f["issue"] or "")

        # Priority score
        base = sum(_SEVERITY_WEIGHTS.get(s, 0) * c for s, c in sev.items())
        breadth_bonus = 1 + len(layers_hit) * 0.1
        scalar = row["scalar_score"] or 1.0
        priority = min(100.0, base * breadth_bonus * (1 - scalar))

        results.append(
            {
                "priority": round(priority, 2),
                "document_id": row["document_id"],
                "title": (row["title"] or "Untitled")[:80],
                "jurisdiction": row["jurisdiction"] or "unknown",
                "document_type": row["document_type"] or "?",
                "scalar_score": round(scalar, 3),
                "anomaly_count": row["anomaly_count"],
                "critical": sev.get("critical", 0),
                "high": sev.get("high", 0),
                "medium": sev.get("medium", 0),
                "low": sev.get("low", 0),
                "layers_hit": sorted(layers_hit),
                "layer_count": len(layers_hit),
                "top_issues": top_issues,
                "analysis_timestamp": row["analysis_timestamp"] or "",
            }
        )

    results.sort(key=lambda r: r["priority"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

_COL_RANK = 5
_COL_SCORE = 8
_COL_J = 16
_COL_TITLE = 42
_COL_CNT = 7
_COL_SEV = 18


def _render_table(docs: list[dict], top: int) -> None:
    subset = docs[:top]
    total = len(docs)

    print(f"\n  ODIA Triage Queue  --  Top {min(top, total)} of {total} documents")
    print(f"  DB: {_DB_PATH}\n")

    hdr = (
        f"  {'#':>{_COL_RANK}}  "
        f"{'Score':>{_COL_SCORE}}  "
        f"{'Jurisdiction':<{_COL_J}}  "
        f"{'Title':<{_COL_TITLE}}  "
        f"{'Findings':>{_COL_CNT}}  "
        f"Sev (C/H/M/L)"
    )
    rule = "  " + "-" * (
        _COL_RANK + _COL_SCORE + _COL_J + _COL_TITLE + _COL_CNT + _COL_SEV + 14
    )
    print(hdr)
    print(rule)

    for i, doc in enumerate(subset, 1):
        sev_str = f"{doc['critical']}/{doc['high']}/{doc['medium']}/{doc['low']}"
        print(
            f"  {i:>{_COL_RANK}}  "
            f"{doc['priority']:>{_COL_SCORE}.1f}  "
            f"{doc['jurisdiction']:<{_COL_J}}  "
            f"{doc['title']:<{_COL_TITLE}}  "
            f"{doc['anomaly_count']:>{_COL_CNT}}  "
            f"{sev_str}"
        )
        if doc["top_issues"]:
            for issue in doc["top_issues"]:
                print(f"  {'':{_COL_RANK + _COL_SCORE + 4}}  > {issue[:72]}")
        print()

    print(rule)
    # Jurisdiction breakdown
    juris_counts: dict[str, int] = {}
    for d in docs:
        juris_counts[d["jurisdiction"]] = juris_counts.get(d["jurisdiction"], 0) + 1
    print("\n  By jurisdiction (all flagged docs):")
    for j, c in sorted(juris_counts.items(), key=lambda x: -x[1]):
        print(f"    {j:<25} {c:>5}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ranked triage queue from oraculus_audit.db"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        metavar="N",
        help="Show top N documents (default: 20)",
    )
    parser.add_argument("--jurisdiction", default=None, metavar="SLUG")
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        default=None,
        help="Only include documents that have at least one finding at this severity",
    )
    parser.add_argument(
        "--layer",
        default=None,
        metavar="LAYER",
        help="Only include documents that triggered this detector layer",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        metavar="N",
        help="Minimum priority score to include (default: 0)",
    )
    parser.add_argument("--csv", action="store_true", help="Write results to CSV")
    parser.add_argument("--json", action="store_true", help="Write results to JSON")
    parser.add_argument(
        "--out", default=None, metavar="DIR", help=f"Output dir (default: {_OUT_DIR})"
    )
    args = parser.parse_args()

    if not _DB_PATH.exists():
        sys.exit(f"DB not found: {_DB_PATH}")

    con = _connect()
    docs = _load_documents(con, args.jurisdiction, args.severity, args.layer)
    con.close()

    if args.min_score:
        docs = [d for d in docs if d["priority"] >= args.min_score]

    _render_table(docs, args.top)

    if args.csv or args.json:
        out_dir = Path(args.out) if args.out else _OUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{args.jurisdiction}" if args.jurisdiction else ""

        if args.csv:
            csv_path = out_dir / f"odia_triage{suffix}_{ts}.csv"
            fields = [
                "priority",
                "jurisdiction",
                "title",
                "document_id",
                "document_type",
                "scalar_score",
                "anomaly_count",
                "critical",
                "high",
                "medium",
                "low",
                "layer_count",
                "top_issues",
            ]
            with csv_path.open("w", newline="", encoding="utf-8") as cf:
                writer = csv.DictWriter(cf, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for d in docs:
                    row = dict(d)
                    row["top_issues"] = " | ".join(d["top_issues"])
                    writer.writerow(row)
            print(f"\n  CSV  -> {csv_path}")

        if args.json:
            json_path = out_dir / f"odia_triage{suffix}_{ts}.json"
            json_path.write_text(
                json.dumps(docs[: args.top], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"  JSON -> {json_path}")


if __name__ == "__main__":
    main()
