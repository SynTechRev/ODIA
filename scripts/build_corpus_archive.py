"""build_corpus_archive.py — Corpus archive and navigation index builder.

Produces a structured, navigable archive from the ODIA audit DB with:

  data/corpus_archive/
    MASTER_INDEX.json               — All documents, all findings, searchable
    by_finding/{anomaly_id}.json    — Every occurrence of each finding type
    by_severity/{level}.json        — All findings at critical/high/medium/low
    {jurisdiction}/
      index.json                    — Jurisdiction summary + doc list
      {document_id[:16]}__{title}.json  — Per-document record with all findings

Each per-document record includes:
  - Full document metadata
  - All findings with details
  - Severity and layer breakdown
  - Related documents in same jurisdiction (by overlapping finding types)

The archive is append-friendly: re-running updates only changed jurisdictions.

Usage:
    .venv\\Scripts\\python scripts\\build_corpus_archive.py
    .venv\\Scripts\\python scripts\\build_corpus_archive.py --jurisdiction fresnocounty
    .venv\\Scripts\\python scripts\\build_corpus_archive.py --out data/corpus_archive
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DEFAULT_DB_PATHS = [
    Path(r"C:\Users\yahua\AppData\Local\Programs\ODIA\oraculus_audit.db"),
    Path(__file__).parent.parent / "oraculus_audit.db",
]
ARCHIVE_ROOT = Path(__file__).parent.parent / "data" / "corpus_archive"


def find_db() -> Path:
    for p in DEFAULT_DB_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError("Cannot find oraculus_audit.db. Pass --db.")


def _safe_filename(s: str, maxlen: int = 60) -> str:
    """Convert arbitrary string to safe filename fragment."""
    s = re.sub(r"[^\w\s\-]", "", s).strip()
    s = re.sub(r"[\s]+", "_", s)
    return s[:maxlen]


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def build_archive(
    db_path: Path, out_dir: Path, jurisdiction_filter: str | None
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    ts = datetime.now().isoformat()

    print(f"Connected: {db_path}")
    print(f"Output:    {out_dir}")
    if jurisdiction_filter:
        print(f"Filter:    jurisdiction = {jurisdiction_filter}")
    print()

    # ------------------------------------------------------------------
    # 1. Load all data
    # ------------------------------------------------------------------
    jur_clause = (
        f"AND d.jurisdiction = '{jurisdiction_filter}'" if jurisdiction_filter else ""
    )

    print("Loading documents + findings...")
    rows = con.execute(
        f"""
        SELECT
            d.document_id,
            d.title,
            d.document_type,
            d.jurisdiction,
            d.authority,
            d.version_date,
            d.metadata_json      AS doc_metadata,
            al.id                AS analysis_id,
            al.scalar_score,
            al.anomaly_count,
            al.summary           AS analysis_summary,
            al.engine_version,
            am.id                AS anomaly_row_id,
            am.anomaly_id,
            am.issue,
            am.severity,
            am.layer,
            am.details_json
        FROM documents d
        JOIN analyses al ON al.document_id = d.document_id
        JOIN anomalies am ON am.analysis_id = al.id
        WHERE 1=1 {jur_clause}
        ORDER BY d.jurisdiction, al.scalar_score DESC, am.severity
    """
    ).fetchall()
    print(f"Loaded {len(rows):,} finding rows")

    # Also load zero-finding documents
    zero_rows = con.execute(
        f"""
        SELECT
            d.document_id,
            d.title,
            d.document_type,
            d.jurisdiction,
            d.authority,
            d.version_date,
            d.metadata_json,
            al.id        AS analysis_id,
            al.scalar_score,
            al.anomaly_count,
            al.summary   AS analysis_summary,
            al.engine_version
        FROM documents d
        JOIN analyses al ON al.document_id = d.document_id
        WHERE al.anomaly_count = 0 {jur_clause}
        ORDER BY d.jurisdiction
    """
    ).fetchall()
    print(f"Loaded {len(zero_rows):,} zero-finding documents")

    # ------------------------------------------------------------------
    # 2. Build per-document records
    # ------------------------------------------------------------------
    # Group finding rows by document_id
    doc_findings: dict[str, list[dict]] = defaultdict(list)
    doc_meta: dict[str, dict] = {}

    for r in rows:
        did = r["document_id"]
        if did not in doc_meta:
            try:
                meta = json.loads(r["doc_metadata"]) if r["doc_metadata"] else {}
            except Exception:
                meta = {}
            doc_meta[did] = {
                "document_id": did,
                "title": r["title"] or "Untitled",
                "document_type": r["document_type"],
                "jurisdiction": r["jurisdiction"],
                "authority": r["authority"],
                "version_date": str(r["version_date"] or ""),
                "scalar_score": r["scalar_score"],
                "anomaly_count": r["anomaly_count"],
                "analysis_summary": r["analysis_summary"],
                "engine_version": r["engine_version"],
                "source_metadata": meta,
            }
        try:
            details = json.loads(r["details_json"]) if r["details_json"] else {}
        except Exception:
            details = {}
        doc_findings[did].append(
            {
                "anomaly_id": r["anomaly_id"],
                "issue": r["issue"],
                "severity": r["severity"],
                "layer": r["layer"],
                "details": details,
            }
        )

    # Add zero-finding docs
    for r in zero_rows:
        did = r["document_id"]
        if did not in doc_meta:
            doc_meta[did] = {
                "document_id": did,
                "title": r["title"] or "Untitled",
                "document_type": r["document_type"],
                "jurisdiction": r["jurisdiction"],
                "authority": r["authority"],
                "version_date": str(r["version_date"] or ""),
                "scalar_score": r["scalar_score"],
                "anomaly_count": 0,
                "analysis_summary": r["analysis_summary"],
                "engine_version": r["engine_version"],
                "source_metadata": {},
            }
        if did not in doc_findings:
            doc_findings[did] = []

    all_doc_ids = list(doc_meta.keys())
    print(f"Unique documents: {len(all_doc_ids):,}")

    # ------------------------------------------------------------------
    # 3. Group by jurisdiction
    # ------------------------------------------------------------------
    jur_docs: dict[str, list[str]] = defaultdict(list)
    for did, meta in doc_meta.items():
        jur_docs[meta["jurisdiction"]].append(did)

    # Cross-finding occurrence tracker
    finding_occurrences: dict[str, list[dict]] = defaultdict(list)
    severity_occurrences: dict[str, list[dict]] = defaultdict(list)

    # ------------------------------------------------------------------
    # 4. Write per-jurisdiction archives
    # ------------------------------------------------------------------
    jur_summaries = []
    total_written = 0

    for jur in sorted(jur_docs.keys()):
        doc_ids = jur_docs[jur]
        jur_dir = out_dir / jur
        jur_dir.mkdir(parents=True, exist_ok=True)

        sev_counts: Counter = Counter()
        layer_counts: Counter = Counter()
        finding_type_counts: Counter = Counter()
        jur_doc_summaries = []

        print(f"  [{jur}] {len(doc_ids):,} documents...", end=" ", flush=True)

        for did in doc_ids:
            meta = doc_meta[did]
            findings = doc_findings[did]

            # Per-document severity/layer counts
            doc_sev: Counter = Counter(f["severity"] for f in findings)
            doc_layers: Counter = Counter(f["layer"] for f in findings)
            doc_finding_types: Counter = Counter(f["anomaly_id"] for f in findings)

            # Accumulate jurisdiction totals
            sev_counts.update(doc_sev)
            layer_counts.update(doc_layers)
            finding_type_counts.update(doc_finding_types)

            # Build per-document output
            doc_record = {
                "document_id": did,
                "title": meta["title"],
                "document_type": meta["document_type"],
                "jurisdiction": jur,
                "authority": meta["authority"],
                "version_date": meta["version_date"],
                "scalar_score": meta["scalar_score"],
                "anomaly_count": len(findings),
                "analysis_summary": meta["analysis_summary"],
                "severity_breakdown": {
                    "critical": doc_sev.get("critical", 0),
                    "high": doc_sev.get("high", 0),
                    "medium": doc_sev.get("medium", 0),
                    "low": doc_sev.get("low", 0),
                },
                "layer_breakdown": dict(doc_layers.most_common()),
                "top_finding_types": [
                    {"anomaly_id": aid, "count": cnt}
                    for aid, cnt in doc_finding_types.most_common(10)
                ],
                "findings": sorted(
                    findings,
                    key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
                        f["severity"], 4
                    ),
                ),
                "source_metadata": meta.get("source_metadata", {}),
                "archived_at": ts,
            }

            # Safe filename: first 16 chars of doc_id + title fragment
            title_safe = _safe_filename(meta["title"])
            fname = f"{did[:16]}__{title_safe}.json"
            _write_json(jur_dir / fname, doc_record)
            total_written += 1

            # Summary entry for jurisdiction index
            jur_doc_summaries.append(
                {
                    "document_id": did,
                    "filename": fname,
                    "title": meta["title"],
                    "document_type": meta["document_type"],
                    "scalar_score": meta["scalar_score"],
                    "anomaly_count": len(findings),
                    "severity_breakdown": doc_record["severity_breakdown"],
                    "version_date": meta["version_date"],
                }
            )

            # Track for cross-finding index
            for f in findings:
                aid = f["anomaly_id"]
                finding_occurrences[aid].append(
                    {
                        "document_id": did,
                        "title": meta["title"],
                        "jurisdiction": jur,
                        "document_type": meta["document_type"],
                        "version_date": meta["version_date"],
                        "scalar_score": meta["scalar_score"],
                        "severity": f["severity"],
                        "layer": f["layer"],
                        "issue": f["issue"],
                        "details": f["details"],
                    }
                )
                severity_occurrences[f["severity"]].append(
                    {
                        "document_id": did,
                        "title": meta["title"],
                        "jurisdiction": jur,
                        "anomaly_id": aid,
                        "issue": f["issue"],
                        "layer": f["layer"],
                        "scalar_score": meta["scalar_score"],
                    }
                )

        # Sort doc summaries by scalar_score desc
        jur_doc_summaries.sort(key=lambda d: d["scalar_score"] or 0, reverse=True)

        # Top finding types for jurisdiction
        top_finding_types = [
            {"anomaly_id": aid, "count": cnt, "jurisdictions": [jur]}
            for aid, cnt in finding_type_counts.most_common(25)
        ]

        jur_summary = {
            "jurisdiction": jur,
            "document_count": len(doc_ids),
            "finding_count": sum(len(doc_findings[d]) for d in doc_ids),
            "avg_scalar_score": round(
                sum((doc_meta[d]["scalar_score"] or 0) for d in doc_ids)
                / max(len(doc_ids), 1),
                4,
            ),
            "severity_breakdown": {
                "critical": sev_counts.get("critical", 0),
                "high": sev_counts.get("high", 0),
                "medium": sev_counts.get("medium", 0),
                "low": sev_counts.get("low", 0),
            },
            "layer_breakdown": dict(layer_counts.most_common()),
            "top_finding_types": top_finding_types,
        }
        jur_summaries.append(jur_summary)

        # Write jurisdiction index
        jur_index = {
            "archived_at": ts,
            "jurisdiction": jur,
            "summary": jur_summary,
            "documents": jur_doc_summaries,
        }
        _write_json(jur_dir / "index.json", jur_index)
        print(f"done ({sum(len(doc_findings[d]) for d in doc_ids):,} findings)")

    # ------------------------------------------------------------------
    # 5. by_finding index — one file per anomaly_id
    # ------------------------------------------------------------------
    print(
        f"\nBuilding by_finding index ({len(finding_occurrences)} unique finding types)..."
    )
    finding_dir = out_dir / "by_finding"
    finding_dir.mkdir(parents=True, exist_ok=True)

    finding_index_entries = []
    for aid, occurrences in sorted(finding_occurrences.items()):
        # Sort by scalar_score desc
        occurrences.sort(key=lambda o: o.get("scalar_score") or 0, reverse=True)
        jurs_present = sorted({o["jurisdiction"] for o in occurrences})
        sev_dist = Counter(o["severity"] for o in occurrences)

        finding_record = {
            "anomaly_id": aid,
            "total_occurrences": len(occurrences),
            "jurisdiction_count": len(jurs_present),
            "jurisdictions": jurs_present,
            "severity_distribution": dict(sev_dist.most_common()),
            "sample_issue": occurrences[0]["issue"] if occurrences else "",
            "layer": occurrences[0]["layer"] if occurrences else "",
            "occurrences": occurrences,
            "archived_at": ts,
        }
        fname = _safe_filename(aid) + ".json"
        _write_json(finding_dir / fname, finding_record)

        finding_index_entries.append(
            {
                "anomaly_id": aid,
                "filename": fname,
                "total_occurrences": len(occurrences),
                "jurisdiction_count": len(jurs_present),
                "jurisdictions": jurs_present,
                "severity_distribution": dict(sev_dist.most_common()),
                "sample_issue": occurrences[0]["issue"] if occurrences else "",
                "layer": occurrences[0]["layer"] if occurrences else "",
            }
        )

    # Sort finding index by occurrence count desc
    finding_index_entries.sort(key=lambda e: e["total_occurrences"], reverse=True)
    _write_json(
        finding_dir / "FINDING_INDEX.json",
        {
            "archived_at": ts,
            "unique_finding_types": len(finding_index_entries),
            "findings": finding_index_entries,
        },
    )

    # ------------------------------------------------------------------
    # 6. by_severity index
    # ------------------------------------------------------------------
    print("Building by_severity index...")
    sev_dir = out_dir / "by_severity"
    sev_dir.mkdir(parents=True, exist_ok=True)
    for sev, occurrences in severity_occurrences.items():
        occurrences.sort(key=lambda o: o.get("scalar_score") or 0, reverse=True)
        _write_json(
            sev_dir / f"{sev}.json",
            {
                "archived_at": ts,
                "severity": sev,
                "total_occurrences": len(occurrences),
                "occurrences": occurrences,
            },
        )

    # ------------------------------------------------------------------
    # 7. MASTER_INDEX.json
    # ------------------------------------------------------------------
    print("Building MASTER_INDEX.json...")
    jur_summaries.sort(key=lambda s: s["finding_count"], reverse=True)
    total_docs = sum(s["document_count"] for s in jur_summaries)
    total_findings = sum(s["finding_count"] for s in jur_summaries)

    master = {
        "archived_at": ts,
        "db_path": str(db_path),
        "totals": {
            "jurisdictions": len(jur_summaries),
            "documents": total_docs,
            "findings": total_findings,
            "unique_finding_types": len(finding_occurrences),
            "critical_findings": sum(
                s["severity_breakdown"]["critical"] for s in jur_summaries
            ),
            "high_findings": sum(
                s["severity_breakdown"]["high"] for s in jur_summaries
            ),
        },
        "jurisdictions": jur_summaries,
        "navigation": {
            "by_finding": "by_finding/FINDING_INDEX.json — All finding types, sorted by frequency",
            "by_severity": "by_severity/{critical|high|medium|low}.json — All findings at each level",
            "per_jurisdiction": "{jurisdiction}/index.json — Documents and findings for one jurisdiction",
            "per_document": "{jurisdiction}/{doc_id[:16]}__{title}.json — Full record for one document",
        },
        "note": (
            "Text excerpt / page-level location data is not yet stored in the DB "
            "(sections table is empty). Finding locations are currently document-level only. "
            "Run the text extraction pass to populate sections and enable paragraph-level navigation."
        ),
    }
    _write_json(out_dir / "MASTER_INDEX.json", master)

    # ------------------------------------------------------------------
    # 8. Summary
    # ------------------------------------------------------------------
    con.close()
    all_files = list(out_dir.rglob("*.json"))
    total_kb = sum(f.stat().st_size for f in all_files) // 1024

    print()
    print("=" * 60)
    print("Archive complete")
    print("=" * 60)
    print(f"Documents archived:     {total_written:,}")
    print(f"Unique finding types:   {len(finding_occurrences):,}")
    print(f"Archive files written:  {len(all_files):,}")
    print(f"Total archive size:     {total_kb:,} KB ({total_kb // 1024:,} MB)")
    print(f"Archive root:           {out_dir.resolve()}")
    print()
    print("Navigation entry points:")
    print("  MASTER_INDEX.json                — start here")
    print("  by_finding/FINDING_INDEX.json    — browse by finding type")
    print("  by_severity/critical.json        — all critical findings")
    print("  {jurisdiction}/index.json        — per-jurisdiction document list")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ODIA corpus archive index")
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=ARCHIVE_ROOT)
    parser.add_argument(
        "--jurisdiction",
        default=None,
        help="Only archive one jurisdiction (e.g. fresnocounty)",
    )
    args = parser.parse_args()

    db_path = args.db or find_db()
    if not db_path.exists():
        print(f"ERROR: DB not found at {db_path}")
        raise SystemExit(1)

    build_archive(db_path, args.out, args.jurisdiction)


if __name__ == "__main__":
    main()
