"""export_training_data.py — Export oraculus_audit.db as supervised fine-tuning data.

Generates JSONL in the messages format (compatible with Unsloth, Axolotl,
OpenAI fine-tune API, and llama.cpp) plus an optional CSV for human review.

Two export modes:

  reports (default)
    One record per document with >= min_findings findings. The "user" turn
    contains the document's metadata and its raw findings list; the
    "assistant" turn is a structured audit report derived from those
    findings. Teaches the model to synthesize structured data into a
    readable compliance narrative.

  explanations
    One record per individual finding. The "user" turn asks for a plain-
    language explanation of the finding; the "assistant" turn is generated
    from the issue text and details fields. Teaches the model to translate
    technical audit findings into citizen-readable language.

Usage:
    python scripts/export_training_data.py
    python scripts/export_training_data.py --mode explanations
    python scripts/export_training_data.py --mode reports --min-findings 3
    python scripts/export_training_data.py --jurisdiction tulare
    python scripts/export_training_data.py --csv
    python scripts/export_training_data.py --stats
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
_OUT_DIR = _REPO_ROOT / "data" / "training"

_SYSTEM_PROMPT = (
    "You are ODIA (Oraculus Decimus Intellect Analyst), a forensic audit AI "
    "specialized in California public agency compliance. You analyze government "
    "documents for fiscal irregularities, CPRA violations, surveillance overreach, "
    "procurement anomalies, and constitutional implications. Your findings are "
    "specific, evidence-grounded, and written for both legal professionals and "
    "informed members of the public."
)

# Layer labels — mirrors explainer.py
_LAYER_LABELS: dict[str, str] = {
    "l1_statutory_applicability": "Statutory Applicability",
    "l2_procedural_compliance": "Procedural Compliance",
    "l3_exemption_misapplication": "Exemption Misapplication",
    "l4_ministerial_duty": "Ministerial Duty",
    "l5_federal_grant_compliance": "Federal Grant Compliance",
    "l6_constitutional_implication": "Constitutional Implication",
    "l7_regulatory_authority": "Regulatory Authority",
    "l8_case_law_currency": "Case-Law Currency",
    "l9_recodification": "Recodification",
    "l10_balancing_test": "Balancing Test",
    "administrative": "Administrative Integrity",
    "fiscal": "Fiscal Integrity",
    "surveillance": "Surveillance Oversight",
    "governance": "Governance",
    "procurement": "Procurement",
    "scope": "Scope & Authorization",
    "signature": "Signature & Execution",
    "grant_funding_trails": "Grant Funding Trails",
    "grant_compliance": "Grant Compliance",
    "vote_date_alignment": "Vote & Date Alignment",
}


# ---------------------------------------------------------------------------
# DB helpers — raw sqlite3 (no ORM needed for a read-only export)
# ---------------------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(_DB_PATH), timeout=10)
    con.row_factory = sqlite3.Row
    return con


def _fetch_documents(
    con: sqlite3.Connection,
    jurisdiction: str | None,
    min_findings: int,
) -> list[sqlite3.Row]:
    where = f"a.anomaly_count >= {min_findings}"
    params: list[str] = []
    if jurisdiction:
        where += " AND d.jurisdiction = ?"
        params.append(jurisdiction)
    return con.execute(
        f"""
        SELECT
            d.document_id, d.title, d.jurisdiction, d.document_type,
            a.id AS analysis_id, a.anomaly_count, a.scalar_score,
            a.engine_version, a.analysis_timestamp
        FROM documents d
        JOIN analyses a ON a.document_id = d.document_id
        WHERE {where}
        ORDER BY d.jurisdiction, a.anomaly_count DESC
        """,
        params,
    ).fetchall()


def _fetch_findings(con: sqlite3.Connection, analysis_id: int) -> list[sqlite3.Row]:
    return con.execute(
        """
        SELECT anomaly_id, issue, severity, layer, details_json
        FROM anomalies
        WHERE analysis_id = ?
        ORDER BY
            CASE severity
                WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                WHEN 'medium'   THEN 2 ELSE 3
            END,
            layer
        """,
        (analysis_id,),
    ).fetchall()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _layer_label(layer: str) -> str:
    return _LAYER_LABELS.get(layer, layer.replace("_", " ").title())


def _fmt_details(details_json: str) -> str:
    try:
        d = json.loads(details_json or "{}")
    except Exception:
        return ""
    parts = []
    for k, v in d.items():
        if v is None or v == [] or v == {}:
            continue
        key = k.replace("_", " ").capitalize()
        if isinstance(v, list):
            parts.append(f"{key}: {', '.join(str(x) for x in v[:5])}")
        elif isinstance(v, dict):
            parts.append(f"{key}: {json.dumps(v, ensure_ascii=False)[:120]}")
        else:
            parts.append(f"{key}: {v}")
    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Report output (assistant turn for "reports" mode)
# ---------------------------------------------------------------------------


def _report_output(doc: sqlite3.Row, findings: list[sqlite3.Row]) -> str:
    lines: list[str] = []
    j = (doc["jurisdiction"] or "unknown").title()
    score = doc["scalar_score"] or 0.0

    lines.append(f"AUDIT REPORT -- {doc['title']}")
    lines.append(
        f"Jurisdiction: {j}  |  Type: {doc['document_type'].upper()}"
        f"  |  Score: {score:.3f}  |  Findings: {len(findings)}"
    )
    lines.append("")

    by_sev: dict[str, list[sqlite3.Row]] = {}
    for f in findings:
        by_sev.setdefault(f["severity"] or "low", []).append(f)

    for sev in ("critical", "high", "medium", "low"):
        group = by_sev.get(sev, [])
        if not group:
            continue
        lines.append(f"[{sev.upper()} -- {len(group)} finding(s)]")
        for f in group:
            details = _fmt_details(f["details_json"] or "{}")
            lines.append(f"  * {f['issue']}")
            lines.append(f"    Detector: {_layer_label(f['layer'] or '')}")
            if details:
                lines.append(f"    {details}")
        lines.append("")

    if score < 0.8:
        lines.append(
            "SUMMARY: Significant compliance concerns requiring review "
            "before approval or reliance."
        )
    elif score < 0.95:
        lines.append(
            "SUMMARY: Moderate compliance issues that should be reviewed "
            "and resolved."
        )
    else:
        lines.append("SUMMARY: Minor notes -- document is generally well-formed.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Explanation output (assistant turn for "explanations" mode)
# ---------------------------------------------------------------------------


def _explanation_output(doc: sqlite3.Row, finding: sqlite3.Row) -> str:
    sev = (finding["severity"] or "low").lower()
    layer = _layer_label(finding["layer"] or "")
    details = _fmt_details(finding["details_json"] or "{}")

    sev_phrase = {
        "critical": "a critical compliance violation",
        "high": "a serious compliance issue",
        "medium": "a moderate compliance concern",
        "low": "a minor compliance note",
    }.get(sev, "a compliance issue")

    lines = [
        f"This finding represents {sev_phrase} in the area of {layer}.",
        "",
        f"Issue: {finding['issue']}",
    ]
    if details:
        lines.append(f"Supporting detail: {details}")
    lines.extend(
        [
            "",
            "Why this matters: Public agencies are required to follow established "
            "procedures, statutory requirements, and fiscal controls. When documents "
            "show gaps in these areas, it may indicate unauthorized expenditures, "
            "procedural shortcuts, or unreviewed commitments that affect public "
            "accountability.",
        ]
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Record builders
# ---------------------------------------------------------------------------


def _report_record(doc: sqlite3.Row, findings: list[sqlite3.Row]) -> dict:
    user = (
        f"Analyze the following public agency document record and produce a "
        f"structured compliance audit report.\n\n"
        f"Document: {doc['title']}\n"
        f"Jurisdiction: {(doc['jurisdiction'] or 'unknown').title()}\n"
        f"Type: {doc['document_type'].upper()}\n"
        f"Findings detected: {len(findings)}\n\n"
        f"Raw findings:\n"
        + json.dumps(
            [
                {
                    "id": f["anomaly_id"],
                    "issue": f["issue"],
                    "severity": f["severity"],
                    "layer": f["layer"],
                    "details": json.loads(f["details_json"] or "{}"),
                }
                for f in findings
            ],
            indent=2,
            ensure_ascii=False,
        )
    )
    return {
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": _report_output(doc, findings)},
        ],
        "metadata": {
            "document_id": doc["document_id"],
            "jurisdiction": doc["jurisdiction"],
            "scalar_score": doc["scalar_score"],
            "finding_count": len(findings),
            "export_type": "report",
        },
    }


def _explanation_record(doc: sqlite3.Row, finding: sqlite3.Row) -> dict:
    user = (
        f"Explain the following audit finding in plain language for a member "
        f"of the public. The document is from "
        f"{(doc['jurisdiction'] or 'unknown').title()} "
        f"({doc['document_type'].upper()}).\n\n"
        f"Finding:\n"
        + json.dumps(
            {
                "id": finding["anomaly_id"],
                "issue": finding["issue"],
                "severity": finding["severity"],
                "layer": finding["layer"],
                "details": json.loads(finding["details_json"] or "{}"),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return {
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": _explanation_output(doc, finding)},
        ],
        "metadata": {
            "document_id": doc["document_id"],
            "jurisdiction": doc["jurisdiction"],
            "anomaly_id": finding["anomaly_id"],
            "severity": finding["severity"],
            "layer": finding["layer"],
            "export_type": "explanation",
        },
    }


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def _print_stats(con: sqlite3.Connection) -> None:
    total_docs = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    total_findings = con.execute("SELECT COUNT(*) FROM anomalies").fetchone()[0]
    juris = con.execute(
        "SELECT jurisdiction, COUNT(*) c FROM documents "
        "GROUP BY jurisdiction ORDER BY c DESC"
    ).fetchall()
    layers = con.execute(
        "SELECT layer, COUNT(*) c FROM anomalies "
        "GROUP BY layer ORDER BY c DESC LIMIT 12"
    ).fetchall()
    sevs = con.execute(
        "SELECT severity, COUNT(*) c FROM anomalies GROUP BY severity"
    ).fetchall()

    print(f"\nDB: {_DB_PATH}")
    print(f"Documents : {total_docs:,}")
    print(f"Findings  : {total_findings:,}")
    print("\nBy jurisdiction:")
    for r in juris:
        print(f"  {(r[0] or 'unknown'):<28} {r[1]:>6,}")
    print("\nTop detector layers:")
    for r in layers:
        print(f"  {(r[0] or '?'):<35} {r[1]:>6,}")
    print("\nSeverity:")
    for r in sevs:
        print(f"  {(r[0] or '?'):<12} {r[1]:>6,}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:  # noqa: C901
    parser = argparse.ArgumentParser(
        description="Export oraculus_audit.db as SFT training data"
    )
    parser.add_argument(
        "--mode",
        choices=["reports", "explanations"],
        default="reports",
        help="Export mode (default: reports)",
    )
    parser.add_argument("--jurisdiction", default=None, metavar="SLUG")
    parser.add_argument(
        "--min-findings",
        type=int,
        default=1,
        metavar="N",
        help="Minimum findings per document (default: 1)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        metavar="N",
        help="Cap output at N records, 0 = unlimited",
    )
    parser.add_argument(
        "--csv", action="store_true", help="Also write a CSV for human review"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Print DB statistics and exit"
    )
    parser.add_argument("--out", default=None, metavar="DIR")
    args = parser.parse_args()

    if not _DB_PATH.exists():
        sys.exit(f"DB not found: {_DB_PATH}")

    con = _connect()

    if args.stats:
        _print_stats(con)
        con.close()
        return

    out_dir = Path(args.out) if args.out else _OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{args.jurisdiction}" if args.jurisdiction else ""
    jsonl_path = out_dir / f"odia_sft_{args.mode}{suffix}_{ts}.jsonl"
    csv_path = out_dir / f"odia_sft_{args.mode}{suffix}_{ts}.csv"

    docs = _fetch_documents(con, args.jurisdiction, args.min_findings)
    print(
        f"Exporting {args.mode} from {len(docs):,} documents "
        f"(min_findings={args.min_findings}) ..."
    )

    written = 0
    csv_rows: list[dict] = []

    with jsonl_path.open("w", encoding="utf-8") as jf:
        for doc in docs:
            if args.max_records and written >= args.max_records:
                break
            findings = _fetch_findings(con, doc["analysis_id"])
            if not findings:
                continue

            if args.mode == "reports":
                rec = _report_record(doc, findings)
                jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                written += 1
                if args.csv:
                    csv_rows.append(
                        {
                            "document_id": doc["document_id"],
                            "jurisdiction": doc["jurisdiction"],
                            "title": doc["title"],
                            "finding_count": len(findings),
                            "scalar_score": doc["scalar_score"],
                        }
                    )
            else:
                for finding in findings:
                    if args.max_records and written >= args.max_records:
                        break
                    rec = _explanation_record(doc, finding)
                    jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    written += 1
                    if args.csv:
                        csv_rows.append(
                            {
                                "document_id": doc["document_id"],
                                "jurisdiction": doc["jurisdiction"],
                                "anomaly_id": finding["anomaly_id"],
                                "severity": finding["severity"],
                                "layer": finding["layer"],
                                "issue": (finding["issue"] or "")[:120],
                            }
                        )

    con.close()
    print(f"Wrote {written:,} records  ->  {jsonl_path}")

    if args.csv and csv_rows:
        with csv_path.open("w", newline="", encoding="utf-8") as cf:
            writer = csv.DictWriter(cf, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"CSV              ->  {csv_path}")

    summary = {
        "export_timestamp": ts,
        "mode": args.mode,
        "jurisdiction_filter": args.jurisdiction,
        "min_findings": args.min_findings,
        "records_written": written,
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path) if args.csv else None,
    }
    summary_path = out_dir / f"odia_sft_{args.mode}{suffix}_{ts}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary          ->  {summary_path}")


if __name__ == "__main__":
    main()
