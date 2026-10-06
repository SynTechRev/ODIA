"""CONTRA entity deep-dive report — all documents, findings by axis, CASI distribution.

Generates a per-entity analytical profile useful for synthesis prep, chain membership
decisions, and acquisition targeting.

Usage:
    python scripts/contra_entity_deep.py --entity "Snap Inc."
    python scripts/contra_entity_deep.py --entity "Rokt Pte. Ltd." --json-out snap_deep.json
    python scripts/contra_entity_deep.py --top 10          # top 10 entities by avg CASI
    python scripts/contra_entity_deep.py --all             # every entity in corpus
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"

_AXES = [
    "data_extraction_depth",
    "modification_and_consent",
    "procedural_adhesion",
    "remedy_foreclosure",
    "enforcement_cost_asymmetry",
]
_AXIS_SHORT = {
    "data_extraction_depth": "DED",
    "modification_and_consent": "MC",
    "procedural_adhesion": "PA",
    "remedy_foreclosure": "RF",
    "enforcement_cost_asymmetry": "ECA",
}

_CASI_BANDS = [
    (81, 100, "Foreclosure Regime"),
    (61, 80, "Severe"),
    (41, 60, "Substantial"),
    (21, 40, "Elevated"),
    (0, 20, "Baseline"),
]


def _band(score: int | float) -> str:
    for lo, hi, label in _CASI_BANDS:
        if lo <= score <= hi:
            return label
    return "?"


def _casi_bar(score: int | float, width: int = 20) -> str:
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def entity_deep(db_path: str, entity_name: str) -> dict:
    from sqlalchemy import create_engine, text

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    with engine.connect() as conn:
        # Entity metadata
        ent = conn.execute(
            text("""
            SELECT entity_id, canonical_name, corporate_family, created_at
            FROM commercial_entities WHERE canonical_name = :name
        """),
            {"name": entity_name},
        ).fetchone()

        if not ent:
            return {"error": f"Entity not found: {entity_name}"}

        entity_id = ent[0]

        # All documents
        docs = conn.execute(
            text("""
            SELECT cd.document_hash, cd.doc_type, cd.version_label, cd.effective_date,
                   cs.aggregate, cs.data_extraction_depth, cs.modification_and_consent,
                   cs.procedural_adhesion, cs.remedy_foreclosure, cs.enforcement_cost_asymmetry
            FROM commercial_documents cd
            LEFT JOIN casi_scores cs ON cs.document_hash = cd.document_hash
            WHERE cd.entity_id = :eid
            ORDER BY cs.aggregate DESC NULLS LAST
        """),
            {"eid": entity_id},
        ).fetchall()

        # Findings by axis and severity
        findings_by_axis = conn.execute(
            text("""
            SELECT cf.scoring_axis, cf.severity, COUNT(*) as cnt
            FROM contra_findings cf
            JOIN commercial_documents cd ON cd.document_hash = cf.document_hash
            WHERE cd.entity_id = :eid AND cf.scoring_axis IS NOT NULL
            GROUP BY cf.scoring_axis, cf.severity
            ORDER BY cf.scoring_axis, cf.severity
        """),
            {"eid": entity_id},
        ).fetchall()

        # Top findings by severity
        top_findings = conn.execute(
            text("""
            SELECT cf.sub_detector, cf.doctrinal_anchor, cf.severity, cf.scoring_axis,
                   cd.doc_type, cd.version_label
            FROM contra_findings cf
            JOIN commercial_documents cd ON cd.document_hash = cf.document_hash
            WHERE cd.entity_id = :eid
            ORDER BY
                CASE cf.severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2 ELSE 3 END,
                cf.scoring_axis
            LIMIT 25
        """),
            {"eid": entity_id},
        ).fetchall()

    # Aggregate doc stats
    doc_records = []
    casi_scores = [d[4] for d in docs if d[4] is not None]
    for d in docs:
        doc_records.append(
            {
                "doc_type": d[1],
                "version_label": d[2],
                "effective_date": str(d[3]) if d[3] else None,
                "casi": d[4],
                "band": _band(d[4]) if d[4] is not None else None,
                "axes": {
                    "data_extraction_depth": d[5],
                    "modification_and_consent": d[6],
                    "procedural_adhesion": d[7],
                    "remedy_foreclosure": d[8],
                    "enforcement_cost_asymmetry": d[9],
                },
            }
        )

    # Axis rollup
    axis_rollup: dict[str, dict] = {
        ax: {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
        for ax in _AXES
    }
    for row in findings_by_axis:
        ax, sev, cnt = row
        if ax in axis_rollup:
            axis_rollup[ax]["total"] += cnt
            if sev in axis_rollup[ax]:
                axis_rollup[ax][sev] += cnt

    return {
        "entity_name": ent[1],
        "corporate_family": ent[2],
        "doc_count": len(docs),
        "avg_casi": round(sum(casi_scores) / len(casi_scores), 1)
        if casi_scores
        else None,
        "max_casi": max(casi_scores) if casi_scores else None,
        "min_casi": min(casi_scores) if casi_scores else None,
        "total_findings": sum(v["total"] for v in axis_rollup.values()),
        "axis_rollup": axis_rollup,
        "documents": doc_records,
        "top_findings": [
            {
                "sub_detector": f[0],
                "doctrinal_anchor": f[1],
                "severity": f[2],
                "axis": f[3],
                "doc_type": f[4],
                "version_label": f[5],
            }
            for f in top_findings
        ],
    }


def print_deep(profile: dict) -> None:
    if "error" in profile:
        print(f"ERROR: {profile['error']}")
        return

    e = profile["entity_name"]
    fam = f"  [{profile['corporate_family']}]" if profile["corporate_family"] else ""
    avg = profile["avg_casi"]
    mx = profile["max_casi"]
    band_str = _band(avg) if avg is not None else "N/A"

    print(f"\n{'━'*72}")
    print(f"  {e}{fam}")
    print(
        f"  {profile['doc_count']} docs | {profile['total_findings']} findings | "
        f"AvgCASI {avg or '---'} ({band_str}) | MaxCASI {mx or '---'}"
    )

    if avg is not None:
        print(f"  [{_casi_bar(avg)}] {avg}/100")

    print("\n  Axis coverage:")
    print(f"  {'Axis':<30} {'Total':>6} {'CRIT':>5} {'HIGH':>5} {'MED':>5} {'LOW':>5}")
    print(f"  {'─'*56}")
    for ax in _AXES:
        r = profile["axis_rollup"][ax]
        active = "✓" if r["total"] > 0 else "✗"
        print(
            f"  {active} {_AXIS_SHORT[ax]:<4} {ax[:24]:<24} "
            f"{r['total']:>6} {r['critical']:>5} {r['high']:>5} {r['medium']:>5} {r['low']:>5}"
        )

    if profile["documents"]:
        print(f"\n  Documents ({profile['doc_count']}):")
        print(f"  {'Type':<22} {'CASI':>5} {'Band':<14} {'Label'}")
        print(f"  {'─'*70}")
        for d in profile["documents"][:20]:
            casi_str = str(d["casi"]) if d["casi"] is not None else "---"
            band_str2 = d["band"] or "---"
            label = (d["version_label"] or d["doc_type"] or "")[:35]
            print(
                f"  {(d['doc_type'] or '')[:22]:<22} {casi_str:>5} {band_str2:<14} {label}"
            )
        if profile["doc_count"] > 20:
            print(
                f"  ... {profile['doc_count'] - 20} more (use --json-out for full list)"
            )

    if profile["top_findings"]:
        print("\n  Top findings (up to 25 by severity):")
        print(f"  {'SEV':<8} {'Axis':<4} {'Issue'[:55]}")
        print(f"  {'─'*70}")
        for f in profile["top_findings"]:
            sev = f["severity"].upper()[:8] if f["severity"] else "?"
            ax = _AXIS_SHORT.get(f["axis"], "?") if f["axis"] else "?"
            anchor = (f["doctrinal_anchor"] or f["sub_detector"] or "")[:55]
            print(f"  {sev:<8} {ax:<4} {anchor}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CONTRA entity deep-dive profile")
    parser.add_argument("--entity", default=None, help="Exact canonical entity name")
    parser.add_argument(
        "--top", type=int, default=None, help="Top N entities by avg CASI"
    )
    parser.add_argument(
        "--all", action="store_true", help="Profile all entities in corpus"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args()

    from sqlalchemy import create_engine, text

    engine = create_engine(
        f"sqlite:///{args.db_path}", connect_args={"check_same_thread": False}
    )

    if args.entity:
        entities = [args.entity]
    elif args.top or args.all:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                SELECT ce.canonical_name, AVG(cs.aggregate) as avg_casi
                FROM commercial_entities ce
                LEFT JOIN commercial_documents cd ON cd.entity_id = ce.entity_id
                LEFT JOIN casi_scores cs ON cs.document_hash = cd.document_hash
                GROUP BY ce.canonical_name
                HAVING COUNT(cd.document_hash) > 0
                ORDER BY avg_casi DESC NULLS LAST
            """)
            ).fetchall()
        entities = (
            [r[0] for r in rows[: args.top]] if args.top else [r[0] for r in rows]
        )
    else:
        parser.print_help()
        sys.exit(0)

    all_profiles = []
    for ename in entities:
        profile = entity_deep(args.db_path, ename)
        print_deep(profile)
        all_profiles.append(profile)

    if args.json_out and all_profiles:
        out = Path(args.json_out)
        data = all_profiles[0] if len(all_profiles) == 1 else all_profiles
        out.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        print(f"\nJSON saved: {out}")


if __name__ == "__main__":
    main()
