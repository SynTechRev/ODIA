"""
export_mas_corpus.py — Export ODIA audit DB to Opus-readable JSON files.

Produces a set of structured JSON files in data/mas_export/ that can be
uploaded directly to a Claude.ai project folder for MAS synthesis by an
Opus model.  Uses only stdlib sqlite3 — no SQLAlchemy required.

Usage:
    python scripts/export_mas_corpus.py
    python scripts/export_mas_corpus.py --jurisdiction fresno-pd
    python scripts/export_mas_corpus.py --db "C:/path/to/oraculus_audit.db"
    python scripts/export_mas_corpus.py --out data/mas_export

Output files (full export — no --jurisdiction flag):
    CORPUS_INDEX.json              — master stats across all jurisdictions
    SEVERITY_MATRIX.json           — severity x layer heatmap
    CROSS_JURISDICTION_PATTERNS.json — finding patterns present in 2+ jurisdictions
    {jurisdiction}_MAS.json        — full per-jurisdiction finding detail

Output files (single-jurisdiction export — --jurisdiction specified):
    {jurisdiction}_MAS.json        — full finding detail for that jurisdiction only
    (corpus-wide files are skipped; use full export to regenerate those)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# DB path defaults
# ---------------------------------------------------------------------------
DEFAULT_DB_PATHS = [
    Path(r"C:\Users\yahua\AppData\Local\Programs\ODIA\oraculus_audit.db"),
    Path(__file__).parent.parent / "oraculus_audit.db",
]


def find_db() -> Path:
    for p in DEFAULT_DB_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Could not find oraculus_audit.db. "
        "Pass --db explicitly: python scripts/export_mas_corpus.py --db <path>"
    )


# ---------------------------------------------------------------------------
# Core export logic
# ---------------------------------------------------------------------------

def export(db_path: Path, out_dir: Path, jurisdiction: str | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row

    print(f"Connected: {db_path}")
    print(f"Output:    {out_dir}")
    if jurisdiction:
        print(f"Filter:    jurisdiction = {jurisdiction!r}")

    # ------------------------------------------------------------------
    # 1. Load findings — optionally filtered to a single jurisdiction
    # ------------------------------------------------------------------
    print("Loading findings...")
    if jurisdiction:
        rows = con.execute("""
            SELECT
                d.jurisdiction,
                d.document_id,
                d.title,
                d.document_type,
                d.authority,
                d.version_date,
                al.scalar_score,
                al.anomaly_count,
                al.summary       AS analysis_summary,
                al.engine_version,
                am.anomaly_id,
                am.issue,
                am.severity,
                am.layer,
                am.details_json
            FROM anomalies am
            JOIN analyses   al ON al.id            = am.analysis_id
            JOIN documents  d  ON d.document_id    = al.document_id
            WHERE d.jurisdiction = ?
            ORDER BY al.scalar_score DESC, am.severity
        """, (jurisdiction,)).fetchall()
    else:
        rows = con.execute("""
            SELECT
                d.jurisdiction,
                d.document_id,
                d.title,
                d.document_type,
                d.authority,
                d.version_date,
                al.scalar_score,
                al.anomaly_count,
                al.summary       AS analysis_summary,
                al.engine_version,
                am.anomaly_id,
                am.issue,
                am.severity,
                am.layer,
                am.details_json
            FROM anomalies am
            JOIN analyses   al ON al.id            = am.analysis_id
            JOIN documents  d  ON d.document_id    = al.document_id
            ORDER BY d.jurisdiction, al.scalar_score DESC, am.severity
        """).fetchall()

    print(f"Loaded {len(rows):,} finding rows")
    if jurisdiction and len(rows) == 0:
        available = [r[0] for r in con.execute(
            "SELECT DISTINCT jurisdiction FROM documents ORDER BY jurisdiction"
        ).fetchall()]
        print(f"ERROR: No findings for jurisdiction {jurisdiction!r}.")
        print(f"Available jurisdictions: {', '.join(available)}")
        con.close()
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Bucket rows by jurisdiction
    # ------------------------------------------------------------------
    by_jur: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_jur[r["jurisdiction"] or "unknown"].append(dict(r))

    # ------------------------------------------------------------------
    # 3. Per-jurisdiction files
    # ------------------------------------------------------------------
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    jurisdiction_summaries = []
    cross_jur_pattern_counts: Counter = Counter()   # anomaly_id -> set of jurs
    cross_jur_pattern_jurs: dict[str, set] = defaultdict(set)

    for jur, findings in sorted(by_jur.items()):
        # Severity breakdown
        sev_counts: Counter = Counter(f["severity"] for f in findings)
        # Layer breakdown
        layer_counts: Counter = Counter(f["layer"] for f in findings)
        # Unique documents
        unique_docs = {f["document_id"] for f in findings}
        # Average scalar score
        scores = [f["scalar_score"] for f in findings if f["scalar_score"] is not None]
        avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0
        # Top anomaly types by count
        anomaly_type_counts: Counter = Counter(f["anomaly_id"] for f in findings)
        top_anomaly_types = [
            {"anomaly_id": aid, "count": cnt}
            for aid, cnt in anomaly_type_counts.most_common(20)
        ]

        # Group findings by document for readable output
        doc_map: dict[str, dict] = {}
        for f in findings:
            did = f["document_id"]
            if did not in doc_map:
                doc_map[did] = {
                    "document_id": did,
                    "title": f["title"],
                    "document_type": f["document_type"],
                    "authority": f["authority"],
                    "version_date": f["version_date"],
                    "scalar_score": f["scalar_score"],
                    "anomaly_count": f["anomaly_count"],
                    "analysis_summary": f["analysis_summary"],
                    "findings": [],
                }
            # Parse details_json safely
            details = {}
            if f["details_json"]:
                try:
                    details = json.loads(f["details_json"])
                except (json.JSONDecodeError, TypeError):
                    details = {"raw": f["details_json"]}

            doc_map[did]["findings"].append({
                "anomaly_id": f["anomaly_id"],
                "issue": f["issue"],
                "severity": f["severity"],
                "layer": f["layer"],
                "details": details,
            })

        # Sort documents by scalar_score desc
        documents = sorted(
            doc_map.values(),
            key=lambda d: d["scalar_score"] or 0.0,
            reverse=True,
        )

        # Track cross-jurisdiction patterns
        for aid in anomaly_type_counts:
            cross_jur_pattern_jurs[aid].add(jur)

        summary = {
            "jurisdiction": jur,
            "document_count": len(unique_docs),
            "finding_count": len(findings),
            "avg_scalar_score": avg_score,
            "severity_breakdown": {
                "critical": sev_counts.get("critical", 0),
                "high":     sev_counts.get("high",     0),
                "medium":   sev_counts.get("medium",   0),
                "low":      sev_counts.get("low",      0),
            },
            "layer_breakdown": dict(layer_counts.most_common()),
            "top_anomaly_types": top_anomaly_types,
        }
        jurisdiction_summaries.append(summary)

        out = {
            "export_timestamp": datetime.now().isoformat(),
            "jurisdiction": jur,
            "summary": summary,
            "documents": documents,
        }

        fname = out_dir / f"{jur.lower().replace(' ', '_').replace('/', '-')}_MAS.json"
        fname.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        size_kb = fname.stat().st_size // 1024
        print(f"  [{jur}] {len(unique_docs):,} docs / {len(findings):,} findings -> {fname.name} ({size_kb} KB)")

    # ------------------------------------------------------------------
    # 4. Corpus-wide files — skipped when --jurisdiction is set
    # ------------------------------------------------------------------
    if jurisdiction:
        con.close()
        print(f"\n{'-'*60}")
        print(f"Single-jurisdiction export complete")
        print(f"{'-'*60}")
        fname = out_dir / f"{jurisdiction.lower().replace(' ', '_').replace('/', '-')}_MAS.json"
        size_kb = fname.stat().st_size // 1024 if fname.exists() else 0
        print(f"  {fname.name}  ({size_kb:,} KB)")
        print(f"\nNote: CORPUS_INDEX, SEVERITY_MATRIX, CROSS_JURISDICTION_PATTERNS")
        print(f"      not regenerated (they span all jurisdictions).")
        print(f"      Run without --jurisdiction to rebuild corpus-wide files.")
        return

    # ------------------------------------------------------------------
    # 4. CORPUS_INDEX.json
    # ------------------------------------------------------------------
    total_docs = sum(s["document_count"] for s in jurisdiction_summaries)
    total_findings = sum(s["finding_count"] for s in jurisdiction_summaries)
    total_critical = sum(s["severity_breakdown"]["critical"] for s in jurisdiction_summaries)
    total_high = sum(s["severity_breakdown"]["high"] for s in jurisdiction_summaries)

    # Sort jurisdictions by finding_count desc for the index
    jurisdiction_summaries.sort(key=lambda s: s["finding_count"], reverse=True)

    corpus_index = {
        "export_timestamp": datetime.now().isoformat(),
        "db_path": str(db_path),
        "totals": {
            "jurisdictions": len(jurisdiction_summaries),
            "documents": total_docs,
            "findings": total_findings,
            "critical_findings": total_critical,
            "high_findings": total_high,
        },
        "jurisdictions": jurisdiction_summaries,
        "note": (
            "TCPD corpus comprises public-facing meeting records only (CCP, JJDPC, MJJCC "
            "divisions). Procurement contracts, SEU operational records, and grant "
            "applications are not publicly disclosed — expected via CPRA-004 response. "
            "All other Tulare County jurisdictions are complete."
        ),
    }

    idx_path = out_dir / "CORPUS_INDEX.json"
    idx_path.write_text(json.dumps(corpus_index, indent=2, default=str), encoding="utf-8")
    print(f"\nCorpus index -> {idx_path.name} ({idx_path.stat().st_size // 1024} KB)")

    # ------------------------------------------------------------------
    # 5. SEVERITY_MATRIX.json — severity × layer heatmap
    # ------------------------------------------------------------------
    print("Building severity matrix...")
    sev_layer_rows = con.execute("""
        SELECT
            d.jurisdiction,
            am.severity,
            am.layer,
            COUNT(*) as count
        FROM anomalies am
        JOIN analyses al ON al.id = am.analysis_id
        JOIN documents d  ON d.document_id = al.document_id
        GROUP BY d.jurisdiction, am.severity, am.layer
        ORDER BY d.jurisdiction, am.severity, am.layer
    """).fetchall()

    matrix: dict[str, dict] = defaultdict(lambda: defaultdict(dict))
    all_layers: set = set()
    for r in sev_layer_rows:
        jur = r["jurisdiction"] or "unknown"
        matrix[jur][r["severity"]][r["layer"]] = r["count"]
        all_layers.add(r["layer"])

    sev_matrix_out = {
        "export_timestamp": datetime.now().isoformat(),
        "description": (
            "Severity × Layer finding counts per jurisdiction. "
            "Use to identify which detector layers are driving each jurisdiction's risk profile."
        ),
        "layers": sorted(all_layers),
        "matrix": {jur: dict(sev_data) for jur, sev_data in matrix.items()},
    }

    mat_path = out_dir / "SEVERITY_MATRIX.json"
    mat_path.write_text(json.dumps(sev_matrix_out, indent=2, default=str), encoding="utf-8")
    print(f"Severity matrix -> {mat_path.name} ({mat_path.stat().st_size // 1024} KB)")

    # ------------------------------------------------------------------
    # 6. CROSS_JURISDICTION_PATTERNS.json
    # ------------------------------------------------------------------
    print("Building cross-jurisdiction patterns...")

    # Only patterns that appear in 2+ jurisdictions
    multi_jur = {
        aid: sorted(jurs)
        for aid, jurs in cross_jur_pattern_jurs.items()
        if len(jurs) >= 2
    }

    # For each multi-jur pattern, get the canonical issue text and per-jur counts
    pattern_details = []
    for aid, jurs in sorted(multi_jur.items(), key=lambda x: -len(x[1])):
        row = con.execute("""
            SELECT am.issue, am.severity, am.layer, COUNT(*) as total_count
            FROM anomalies am
            WHERE am.anomaly_id = ?
            GROUP BY am.issue, am.severity, am.layer
            ORDER BY total_count DESC
            LIMIT 1
        """, (aid,)).fetchone()

        if not row:
            continue

        # Per-jurisdiction count
        per_jur = {}
        for jur in jurs:
            cnt_row = con.execute("""
                SELECT COUNT(*) as cnt
                FROM anomalies am
                JOIN analyses al ON al.id = am.analysis_id
                JOIN documents d  ON d.document_id = al.document_id
                WHERE am.anomaly_id = ? AND d.jurisdiction = ?
            """, (aid, jur)).fetchone()
            per_jur[jur] = cnt_row["cnt"] if cnt_row else 0

        pattern_details.append({
            "anomaly_id": aid,
            "issue": row["issue"],
            "severity": row["severity"],
            "layer": row["layer"],
            "jurisdiction_count": len(jurs),
            "jurisdictions": jurs,
            "per_jurisdiction_count": per_jur,
            "total_occurrences": sum(per_jur.values()),
        })

    # Sort by (jurisdiction_count desc, total_occurrences desc)
    pattern_details.sort(key=lambda p: (-p["jurisdiction_count"], -p["total_occurrences"]))

    cross_jur_out = {
        "export_timestamp": datetime.now().isoformat(),
        "description": (
            "Anomaly patterns present in 2 or more jurisdictions, sorted by breadth "
            "(jurisdiction_count) then volume. These represent systemic failures "
            "across the Tulare County jurisdiction landscape rather than isolated incidents."
        ),
        "pattern_count": len(pattern_details),
        "patterns": pattern_details,
    }

    cj_path = out_dir / "CROSS_JURISDICTION_PATTERNS.json"
    cj_path.write_text(json.dumps(cross_jur_out, indent=2, default=str), encoding="utf-8")
    print(f"Cross-jurisdiction patterns -> {cj_path.name} ({cj_path.stat().st_size // 1024} KB)")

    # ------------------------------------------------------------------
    # 7. Final summary
    # ------------------------------------------------------------------
    con.close()
    all_files = list(out_dir.glob("*.json"))
    total_kb = sum(f.stat().st_size for f in all_files) // 1024
    print(f"\n{'-'*60}")
    print(f"Export complete: {len(all_files)} files, {total_kb:,} KB total")
    print(f"Output: {out_dir.resolve()}")
    print()
    print("Files to upload to Claude.ai project folder:")
    for f in sorted(all_files):
        size_kb = f.stat().st_size // 1024
        print(f"  {f.name:55s}  {size_kb:>6,} KB")
    print()
    print("Upload order for Opus MAS synthesis:")
    print("  1. CORPUS_INDEX.json           (start here — gives full landscape)")
    print("  2. CROSS_JURISDICTION_PATTERNS.json (systemic patterns)")
    print("  3. SEVERITY_MATRIX.json        (risk heatmap by layer)")
    print("  4. Per-jurisdiction *_MAS.json files (detail level)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Export ODIA audit DB for Opus MAS synthesis")
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to oraculus_audit.db (auto-detected if omitted)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/mas_export"),
        help="Output directory (default: data/mas_export)",
    )
    parser.add_argument(
        "--jurisdiction",
        type=str,
        default=None,
        help=(
            "Export only this jurisdiction (e.g. fresno-pd, fresnocounty). "
            "Omit to export all jurisdictions and rebuild corpus-wide files."
        ),
    )
    args = parser.parse_args()

    db_path = args.db or find_db()
    if not db_path.exists():
        print(f"ERROR: DB not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    export(db_path, args.out, jurisdiction=args.jurisdiction)


if __name__ == "__main__":
    main()
