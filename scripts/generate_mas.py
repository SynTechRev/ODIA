"""generate_mas.py — CLI Master Audit Summary generator.

Queries oraculus_audit.db for a jurisdiction's documents and anomaly findings,
then renders a structured Markdown MAS document. No API server or UI required.

Usage:
    python scripts/generate_mas.py --jurisdiction visalia
    python scripts/generate_mas.py --jurisdiction tcso --min-severity medium
    python scripts/generate_mas.py --jurisdiction all
    python scripts/generate_mas.py --jurisdiction visalia --stats-only
    python scripts/generate_mas.py --list

Output: data/mas/{jurisdiction}_mas_{timestamp}.md
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DB_PATH = _REPO_ROOT / "oraculus_audit.db"
_OUT_DIR = _REPO_ROOT / "data" / "mas"

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("generate_mas")

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_SEVERITY_LABELS = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}

_LAYER_LABELS: dict[str, str] = {
    "fiscal": "Fiscal Irregularities",
    "constitutional": "Constitutional Implications",
    "surveillance": "Surveillance Overreach",
    "procurement": "Procurement Timeline",
    "cross_reference": "Cross-Jurisdiction",
    "l1_statutory_applicability": "L-1 Statutory Applicability",
    "l2_procedural_compliance": "L-2 Procedural Compliance",
    "l3_exemption_misapplication": "L-3 Exemption Misapplication",
    "l4_ministerial_duty": "L-4 Ministerial Duty",
    "l5_federal_grant_compliance": "L-5 Federal Grant Compliance",
    "l6_constitutional_implication": "L-6 Constitutional Implication",
    "l7_public_participation": "L-7 Public Participation",
    "l8_data_privacy": "L-8 Data Privacy",
    "l9_inter_agency_coordination": "L-9 Inter-Agency Coordination",
    "l10_enforcement_action": "L-10 Enforcement Action",
}


def _label(layer: str) -> str:
    return _LAYER_LABELS.get(layer, layer.replace("_", " ").title())


def _connect() -> sqlite3.Connection:
    if not _DB_PATH.exists():
        sys.exit(f"ERROR: database not found: {_DB_PATH}")
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _list_jurisdictions(conn: sqlite3.Connection) -> list[tuple[str, int, int]]:
    rows = conn.execute(
        """
        SELECT d.jurisdiction,
               COUNT(DISTINCT d.id) AS doc_count,
               COUNT(an.id)         AS finding_count
        FROM   documents d
        LEFT JOIN analyses  al ON al.document_id = d.document_id
        LEFT JOIN anomalies an ON an.analysis_id = al.id
        GROUP BY d.jurisdiction
        ORDER BY doc_count DESC
        """
    ).fetchall()
    return [(r["jurisdiction"], r["doc_count"], r["finding_count"]) for r in rows]


def _fetch_docs(conn: sqlite3.Connection, jurisdiction: str) -> list[sqlite3.Row]:
    if jurisdiction == "all":
        return conn.execute(
            "SELECT * FROM documents ORDER BY jurisdiction, title"
        ).fetchall()
    return conn.execute(
        "SELECT * FROM documents WHERE jurisdiction = ? ORDER BY title",
        (jurisdiction,),
    ).fetchall()


def _fetch_anomalies(
    conn: sqlite3.Connection,
    doc_ids: list[str],
    min_severity: str,
) -> list[sqlite3.Row]:
    threshold = _SEVERITY_ORDER.get(min_severity, 2)
    placeholders = ",".join("?" * len(doc_ids))
    rows = conn.execute(
        f"""
        SELECT an.anomaly_id, an.issue, an.severity, an.layer, an.details_json,
               al.document_id, al.scalar_score, d.title, d.jurisdiction
        FROM   anomalies an
        JOIN   analyses  al ON al.id = an.analysis_id
        JOIN   documents d  ON d.document_id = al.document_id
        WHERE  d.document_id IN ({placeholders})
        """,
        doc_ids,
    ).fetchall()
    return [r for r in rows if _SEVERITY_ORDER.get(r["severity"], 2) <= threshold]


def _render(
    jurisdiction: str,
    docs: list[sqlite3.Row],
    anomalies: list[sqlite3.Row],
    min_severity: str,
) -> str:
    now = datetime.now(UTC)
    ts = now.strftime("%Y-%m-%d %H:%M UTC")
    display = jurisdiction.upper() if jurisdiction != "all" else "ALL JURISDICTIONS"

    # --- aggregate stats ---
    sev_counts: Counter[str] = Counter(r["severity"] for r in anomalies)
    layer_counts: Counter[str] = Counter(r["layer"] for r in anomalies)
    doc_type_counts: Counter[str] = Counter(r["document_type"] for r in docs)

    # top findings per layer (high severity first, then medium)
    by_layer: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in anomalies:
        by_layer[r["layer"]].append(r)
    for layer in by_layer:
        by_layer[layer].sort(key=lambda x: _SEVERITY_ORDER.get(x["severity"], 2))

    # scalar score stats
    scores = []
    for d in docs:
        row = None
        try:
            pass
        except Exception:
            pass
    # re-query scores cleanly
    doc_id_set = {d["document_id"] for d in docs}

    high_docs = [r for r in anomalies if r["severity"] == "high"]
    high_doc_ids = list({r["document_id"] for r in high_docs})[:20]

    lines: list[str] = []

    lines += [
        f"# Master Audit Summary — {display}",
        f"**Generated:** {ts}  ",
        "**ODIA Version:** 3.8.x  ",
        f"**Minimum Severity Filter:** {min_severity.upper()}  ",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Documents Audited | {len(docs):,} |",
        f"| Total Findings | {len(anomalies):,} |",
        f"| High Severity | {sev_counts.get('high', 0):,} |",
        f"| Medium Severity | {sev_counts.get('medium', 0):,} |",
        f"| Low Severity | {sev_counts.get('low', 0):,} |",
        f"| Detector Layers Active | {len(layer_counts)} |",
        "",
    ]

    # severity bar
    total = len(anomalies) or 1
    h_pct = round(sev_counts.get("high", 0) / total * 100)
    m_pct = round(sev_counts.get("medium", 0) / total * 100)
    l_pct = 100 - h_pct - m_pct
    lines += [
        "### Finding Severity Distribution",
        "",
        f"- 🔴 High:   {sev_counts.get('high', 0):>6,}  ({h_pct}%)",
        f"- 🟡 Medium: {sev_counts.get('medium', 0):>6,}  ({m_pct}%)",
        f"- 🟢 Low:    {sev_counts.get('low', 0):>6,}  ({l_pct}%)",
        "",
    ]

    # document type breakdown
    lines += [
        "### Document Type Breakdown",
        "",
        "| Type | Count |",
        "|------|-------|",
    ]
    for dtype, cnt in doc_type_counts.most_common():
        lines.append(f"| {dtype.upper()} | {cnt:,} |")
    lines.append("")

    # findings by detector layer
    lines += [
        "---",
        "",
        "## Findings by Detector Layer",
        "",
    ]
    for layer, count in layer_counts.most_common():
        layer_label = _label(layer)
        layer_rows = by_layer[layer]
        h = sum(1 for r in layer_rows if r["severity"] == "high")
        m = sum(1 for r in layer_rows if r["severity"] == "medium")
        l = sum(1 for r in layer_rows if r["severity"] == "low")
        lines += [
            f"### {layer_label}",
            "",
            f"**Total:** {count:,}  |  🔴 High: {h}  |  🟡 Medium: {m}  |  🟢 Low: {l}",
            "",
        ]
        # Top 5 high-severity examples from this layer
        examples = [r for r in layer_rows if r["severity"] == "high"][:5]
        if not examples:
            examples = layer_rows[:3]
        if examples:
            lines.append("**Representative findings:**")
            lines.append("")
            for ex in examples:
                sev_badge = _SEVERITY_LABELS.get(ex["severity"], ex["severity"].upper())
                title_str = (ex["title"] or "Untitled")[:70]
                issue_str = (ex["issue"] or "")[:200]
                jur = ex["jurisdiction"] if jurisdiction == "all" else ""
                jur_str = f" [{jur}]" if jur else ""
                lines += [
                    f"- **[{sev_badge}]{jur_str}** `{ex['anomaly_id']}`",
                    f"  *{title_str}*",
                    f"  {issue_str}",
                    "",
                ]

    # high severity document list
    if high_doc_ids:
        lines += [
            "---",
            "",
            "## High-Severity Documents (sample — top 20)",
            "",
            "| Jurisdiction | Title | High Findings |",
            "|-------------|-------|--------------|",
        ]
        doc_high_counts: Counter[str] = Counter(
            r["document_id"] for r in anomalies if r["severity"] == "high"
        )
        doc_map = {d["document_id"]: d for d in docs}
        for doc_id, hcount in doc_high_counts.most_common(20):
            d = doc_map.get(doc_id)
            if not d:
                continue
            title = (d["title"] or "Untitled")[:60]
            jur = d["jurisdiction"] or ""
            lines.append(f"| {jur} | {title} | {hcount} |")
        lines.append("")

    # recommendations
    lines += [
        "---",
        "",
        "## Audit Recommendations",
        "",
    ]
    recs: list[str] = []
    if sev_counts.get("high", 0) > 0:
        recs.append(
            f"**Immediate Review Required** — {sev_counts['high']:,} high-severity findings "
            "identified. Legal counsel and department heads should be briefed on flagged documents."
        )
    if layer_counts.get("fiscal", 0) > 50:
        recs.append(
            f"**Fiscal Audit** — {layer_counts['fiscal']:,} fiscal irregularities detected. "
            "Recommend independent financial review of contracts and expenditure authorization chains."
        )
    if layer_counts.get("surveillance", 0) > 20:
        recs.append(
            f"**Surveillance Policy Review** — {layer_counts['surveillance']:,} surveillance-related "
            "findings. Recommend Civil Liberties Impact Assessment under AB 481 framework."
        )
    if layer_counts.get("procurement", 0) > 20:
        recs.append(
            f"**Procurement Compliance** — {layer_counts['procurement']:,} procurement timeline "
            "anomalies. Review bid documentation and competitive solicitation records."
        )
    if any(k.startswith("l") for k in layer_counts):
        recs.append(
            "**CPRA Compliance** — Legal layer detectors flagged potential public records "
            "access violations. Cross-reference with CPRA request logs."
        )
    if not recs:
        recs.append(
            "No critical patterns identified at the selected severity threshold. "
            "Continue routine monitoring."
        )
    for rec in recs:
        lines += [f"- {rec}", ""]

    # footer
    lines += [
        "---",
        "",
        f"*This report was generated automatically by ODIA v3.8.x on {ts}. "
        "All findings are derived from document text analysis and should be reviewed "
        "by qualified legal or compliance personnel before formal action is taken.*",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(
        prog="generate_mas",
        description="Generate a Master Audit Summary from oraculus_audit.db.",
    )
    p.add_argument(
        "--jurisdiction",
        default=None,
        metavar="SLUG",
        help="Jurisdiction slug (e.g. visalia, tcso, all). Use --list to see options.",
    )
    p.add_argument(
        "--min-severity",
        default="low",
        choices=["high", "medium", "low"],
        help="Minimum finding severity to include (default: low = all findings)",
    )
    p.add_argument(
        "--stats-only",
        action="store_true",
        help="Print summary stats to console without writing a file",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="List available jurisdictions and exit",
    )
    p.add_argument(
        "--output-dir",
        default=str(_OUT_DIR),
        metavar="DIR",
        help=f"Output directory (default: {_OUT_DIR})",
    )
    args = p.parse_args()

    conn = _connect()

    if args.list:
        jurisdictions = _list_jurisdictions(conn)
        print(f"\n{'Jurisdiction':<30} {'Docs':>8} {'Findings':>10}")
        print("-" * 52)
        for jur, docs, findings in jurisdictions:
            print(f"{jur:<30} {docs:>8,} {findings:>10,}")
        print()
        conn.close()
        return

    if not args.jurisdiction:
        p.print_help()
        conn.close()
        sys.exit(1)

    jurisdiction = args.jurisdiction.lower().strip()
    docs = _fetch_docs(conn, jurisdiction)

    if not docs:
        sys.exit(
            f"ERROR: no documents found for jurisdiction '{jurisdiction}'. "
            "Run --list to see available jurisdictions."
        )

    doc_ids = [d["document_id"] for d in docs]
    anomalies = _fetch_anomalies(conn, doc_ids, args.min_severity)
    conn.close()

    logger.info(
        "Jurisdiction: %s | docs: %d | findings (>=%s): %d",
        jurisdiction,
        len(docs),
        args.min_severity,
        len(anomalies),
    )

    if args.stats_only:
        from collections import Counter

        sev = Counter(r["severity"] for r in anomalies)
        layer = Counter(r["layer"] for r in anomalies)
        print(f"\nDocs: {len(docs):,}  |  Findings: {len(anomalies):,}")
        print(f"High: {sev['high']:,}  Medium: {sev['medium']:,}  Low: {sev['low']:,}")
        print("\nBy layer:")
        for lyr, cnt in layer.most_common():
            print(f"  {_label(lyr):<40} {cnt:>6,}")
        print()
        return

    markdown = _render(jurisdiction, docs, anomalies, args.min_severity)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{jurisdiction}_mas_{ts}.md"
    out_path.write_text(markdown, encoding="utf-8")

    logger.info("MAS written → %s", out_path)
    logger.info(
        "  %d docs | %d findings | %d layers",
        len(docs),
        len(anomalies),
        len({r["layer"] for r in anomalies}),
    )


if __name__ == "__main__":
    main()
