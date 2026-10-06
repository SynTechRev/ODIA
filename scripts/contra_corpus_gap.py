"""CONTRA corpus gap analyzer — coverage report against chain definitions.

Reads _CIFU_CHAINS from compute_cifu.py, queries contra_corpus.db, and reports:
  - Which chain members have zero docs
  - Which CASI axes are silent per member
  - What the CIFU impact of filling each gap would be
  - Prioritized ingest queue ranked by analytical value

Usage:
    python scripts/contra_corpus_gap.py
    python scripts/contra_corpus_gap.py --chain uber_worker_full
    python scripts/contra_corpus_gap.py --chain uber_consumer_full --json-out gap_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

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

# CIFU impact of adding one entity to a chain with N members and breadth B:
#   If the new entity adds a new axis: breadth_gain = 1/5 * 50
#   If it deepens an existing axis: depth_gain = (1/N) / B * 50
# We approximate marginal impact as the expected delta.


def _compute_gap(db_path: str, chain_id: str | None) -> dict:
    # Import chain definitions from compute_cifu.py
    import importlib.util

    cifu_path = _REPO_ROOT / "scripts" / "compute_cifu.py"
    spec = importlib.util.spec_from_file_location("compute_cifu", cifu_path)
    cifu_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cifu_mod)
    chains = cifu_mod._CIFU_CHAINS

    if chain_id and chain_id not in chains:
        print(
            f"ERROR: chain '{chain_id}' not defined. Available: {list(chains.keys())}"
        )
        sys.exit(1)

    target_chains = {chain_id: chains[chain_id]} if chain_id else chains

    from sqlalchemy import create_engine, text

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    with engine.connect() as conn:
        # Build entity → {docs, axes, avg_casi, max_casi, findings} map from DB
        rows = conn.execute(
            text("""
            SELECT
                ce.canonical_name,
                COUNT(DISTINCT cd.document_hash) AS docs,
                AVG(cs.aggregate)               AS avg_casi,
                MAX(cs.aggregate)               AS max_casi,
                COUNT(DISTINCT cf.id)           AS findings
            FROM commercial_entities ce
            LEFT JOIN commercial_documents cd ON cd.entity_id = ce.entity_id
            LEFT JOIN casi_scores cs ON cs.document_hash = cd.document_hash
            LEFT JOIN contra_findings cf ON cf.document_hash = cd.document_hash
            GROUP BY ce.canonical_name
        """)
        ).fetchall()

        entity_stats: dict[str, dict] = {}
        for row in rows:
            entity_stats[row[0]] = {
                "docs": int(row[1] or 0),
                "avg_casi": round(float(row[2]), 1) if row[2] else None,
                "max_casi": int(row[3]) if row[3] else None,
                "findings": int(row[4] or 0),
            }

        # Build entity → set of active axes
        axis_rows = conn.execute(
            text("""
            SELECT ce.canonical_name, cf.scoring_axis
            FROM contra_findings cf
            JOIN commercial_documents cd ON cd.document_hash = cf.document_hash
            JOIN commercial_entities ce ON ce.entity_id = cd.entity_id
            WHERE cf.scoring_axis IS NOT NULL
        """)
        ).fetchall()

        entity_axes: dict[str, set] = {}
        for ename, axis in axis_rows:
            entity_axes.setdefault(ename, set()).add(axis)

    results = {}
    for cid, chain in target_chains.items():
        anchor = chain["anchor"]
        members = [(anchor, "anchor", "")] + list(chain["members"])
        n = len(members)

        gap_members = []
        present_members = []

        for name, rel, note in members:
            stats = entity_stats.get(
                name, {"docs": 0, "avg_casi": None, "max_casi": None, "findings": 0}
            )
            axes_active = sorted(entity_axes.get(name, set()))
            axes_silent = [a for a in _AXES if a not in axes_active]

            member_rec = {
                "entity_name": name,
                "relationship": rel,
                "docs": stats["docs"],
                "avg_casi": stats["avg_casi"],
                "max_casi": stats["max_casi"],
                "findings": stats["findings"],
                "axes_active": axes_active,
                "axes_active_count": len(axes_active),
                "axes_silent": axes_silent,
                "axes_silent_count": len(axes_silent),
                "in_db": name in entity_stats,
            }

            if stats["docs"] == 0 or not axes_active:
                gap_members.append(member_rec)
            else:
                present_members.append(member_rec)

        # Chain-level axis coverage
        chain_axis_depth: dict[str, int] = {}
        for ax in _AXES:
            chain_axis_depth[ax] = sum(
                1 for name, _, _ in members if ax in entity_axes.get(name, set())
            )

        active_axes = {ax: d for ax, d in chain_axis_depth.items() if d > 0}
        breadth = len(active_axes)
        depth_pct = (
            (sum(d / n for d in active_axes.values()) / breadth) if breadth > 0 else 0.0
        )
        current_cifu = round((breadth / 5 * 50) + (depth_pct * 50), 1)

        # CIFU potential if all gaps filled (all members have all 5 axes)
        potential_depth = 1.0  # all N entities active on all 5 axes
        potential_cifu = round((1.0 * 50) + (potential_depth * 50), 1)
        gap_cifu_delta = round(potential_cifu - current_cifu, 1)

        results[cid] = {
            "chain_name": chain["name"],
            "n_members": n,
            "current_cifu": current_cifu,
            "potential_cifu": potential_cifu,
            "gap_cifu_delta": gap_cifu_delta,
            "present_members": len(present_members),
            "gap_members": len(gap_members),
            "chain_breadth": breadth,
            "chain_depth_pct": round(depth_pct * 100, 1),
            "axis_coverage": {
                ax: {
                    "entities_active": chain_axis_depth[ax],
                    "depth_pct": round(chain_axis_depth[ax] / n * 100, 1),
                }
                for ax in _AXES
            },
            "gap_member_list": gap_members,
            "present_member_list": present_members,
        }

    return results


def _print_report(results: dict) -> None:
    print(
        f"\nC.O.N.T.R.A. Corpus Gap Analysis — {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    print("=" * 72)

    for cid, r in results.items():
        print(f"\n{'━'*72}")
        print(f"  Chain: {r['chain_name']}  [{cid}]")
        print(
            f"  Members: {r['n_members']} total | {r['present_members']} present | {r['gap_members']} gap"
        )
        print(f"  Current CIFU: {r['current_cifu']} / 100")
        print(f"  Potential CIFU (all gaps filled): {r['potential_cifu']} / 100")
        print(f"  Gap CIFU delta: +{r['gap_cifu_delta']}")
        print(
            f"  Chain breadth: {r['chain_breadth']}/5 axes | Depth: {r['chain_depth_pct']}%"
        )

        print("\n  Axis coverage:")
        for ax in _AXES:
            cov = r["axis_coverage"][ax]
            bar_filled = int(cov["depth_pct"] / 10)
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            print(
                f"    {_AXIS_SHORT[ax]:<4} [{bar}] {cov['depth_pct']:>5.1f}%  "
                f"({cov['entities_active']}/{r['n_members']} entities)"
            )

        if r["gap_member_list"]:
            print(
                f"\n  GAP MEMBERS ({r['gap_members']} — no corpus docs or all axes silent):"
            )
            print(f"  {'Entity':<35} {'Docs':>5} {'MaxCASI':>7} {'Silent Axes':>12}")
            print(f"  {'─'*63}")
            for m in r["gap_member_list"]:
                in_db = "" if m["in_db"] else " [NOT IN DB]"
                silent = ",".join(_AXIS_SHORT[a] for a in m["axes_silent"]) or "—"
                casi_str = str(m["max_casi"]) if m["max_casi"] is not None else "—"
                print(
                    f"  {m['entity_name'][:34]:<35} {m['docs']:>5} {casi_str:>7} {silent:>12}{in_db}"
                )

        if r["present_member_list"]:
            print(f"\n  PRESENT MEMBERS ({r['present_members']}):")
            print(
                f"  {'Entity':<35} {'Docs':>4} {'AvgCASI':>7} {'Axes':>5} {'Silent':>20}"
            )
            print(f"  {'─'*70}")
            for m in r["present_member_list"]:
                silent = ",".join(_AXIS_SHORT[a] for a in m["axes_silent"]) or "—"
                avg_str = f"{m['avg_casi']:.1f}" if m["avg_casi"] is not None else "—"
                print(
                    f"  {m['entity_name'][:34]:<35} {m['docs']:>4} {avg_str:>7} "
                    f"  {m['axes_active_count']}/5 {silent:>20}"
                )

    print(f"\n{'━'*72}")
    print("\nIngest priority order (by analytical impact):")
    all_gaps: list[tuple[str, str, dict]] = []
    for cid, r in results.items():
        for m in r["gap_member_list"]:
            all_gaps.append((cid, r["chain_name"][:30], m))

    # Sort: 0-doc + not-in-DB first, then by silent axis count desc
    all_gaps.sort(
        key=lambda x: (x[2]["docs"] == 0, not x[2]["in_db"], x[2]["axes_silent_count"]),
        reverse=True,
    )

    for i, (cid, chain_short, m) in enumerate(all_gaps[:20], 1):
        note = " ← NOT IN DB, needs entity creation" if not m["in_db"] else ""
        print(f"  {i:>2}. [{chain_short:<30}] {m['entity_name'][:40]}{note}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CONTRA corpus gap analysis against chain definitions"
    )
    parser.add_argument(
        "--chain", default=None, help="Specific chain ID (default: all chains)"
    )
    parser.add_argument(
        "--db-path", default=_DEFAULT_DB, help="Path to contra_corpus.db"
    )
    parser.add_argument(
        "--json-out", default=None, help="Save JSON report to this path"
    )
    args = parser.parse_args()

    results = _compute_gap(args.db_path, args.chain)
    _print_report(results)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(
            json.dumps(results, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"JSON report saved: {out_path}")


if __name__ == "__main__":
    main()
