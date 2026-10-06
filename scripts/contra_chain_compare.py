"""CONTRA cross-chain comparison — side-by-side CIFU table across all defined chains.

Computes all chains from compute_cifu.py._CIFU_CHAINS, sorts by CIFU score desc,
and prints a structured comparison table plus axis heatmap and analytical summary.

Usage:
    python scripts/contra_chain_compare.py
    python scripts/contra_chain_compare.py --json-out data/chain_comparison.json
    python scripts/contra_chain_compare.py --markdown   # output as markdown table
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"

_AXIS_SHORT = {
    "data_extraction_depth": "DED",
    "modification_and_consent": "MC",
    "procedural_adhesion": "PA",
    "remedy_foreclosure": "RF",
    "enforcement_cost_asymmetry": "ECA",
}
_AXES = list(_AXIS_SHORT.keys())

_BAND_CHAR = {
    "Foreclosure Regime": "██",
    "Severe Exposure": "▓▓",
    "Substantial Exposure": "▒▒",
    "Elevated Exposure": "░░",
    "Baseline Exposure": "  ",
}


def _load_chains():
    cifu_path = _REPO_ROOT / "scripts" / "compute_cifu.py"
    spec = importlib.util.spec_from_file_location("compute_cifu", cifu_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._CIFU_CHAINS, mod.compute, mod._band


def run_comparison(db_path: str) -> list[dict]:
    chains, compute_fn, band_fn = _load_chains()
    results = []
    for chain_id in chains:
        try:
            r = compute_fn(db_path, chain_id)
            results.append(r)
        except Exception as exc:
            print(f"  WARNING: chain '{chain_id}' failed: {exc}", file=sys.stderr)
    results.sort(key=lambda r: r["cifu_score"], reverse=True)
    return results


def print_table(results: list[dict]) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\nC.O.N.T.R.A. Cross-Chain Comparison — {ts}")
    print(f"{'Corpus: contra_corpus.db':>72}")
    print("=" * 100)

    # Header
    axis_hdr = "  ".join(_AXIS_SHORT[a] for a in _AXES)
    print(
        f"\n  {'Chain':<38} {'CIFU':>5}  {'Band':<20}  {'N':>3}  {'Docs':>5}  {axis_hdr}"
    )
    print(f"  {'─'*38} {'─'*5}  {'─'*20}  {'─'*3}  {'─'*5}  {'─'*22}")

    total_docs = 0
    total_findings = 0

    for r in results:
        # Build axis depth bar per axis (fraction of entities active)
        n = r["n_entities"]
        axis_cells = []
        for ax in _AXES:
            ax_detail = next((d for d in r["axis_detail"] if d["axis"] == ax), None)
            cnt = ax_detail["entity_count"] if ax_detail else 0
            pct = cnt / n if n > 0 else 0
            if pct >= 0.9:
                cell = "███"
            elif pct >= 0.7:
                cell = "██░"
            elif pct >= 0.5:
                cell = "█░░"
            elif pct > 0:
                cell = "░░░"
            else:
                cell = "   "
            axis_cells.append(cell)

        docs_total = sum(m.get("docs", 0) for m in r["members"])
        anchor_docs = r["members"][0].get("docs", 0) if r["members"] else 0
        docs_total += anchor_docs
        total_docs += docs_total

        band_str = r["band"][:20]
        bar = _BAND_CHAR.get(r["band"], "  ")
        axis_str = "  ".join(axis_cells)
        v2_str = f"v2:{r.get('cifu_v2_score', '?')}"

        print(
            f"  {r['chain_name'][:38]:<38} {r['cifu_score']:>5.1f}  {bar} {band_str:<18}  "
            f"{r['n_entities']:>3}  {docs_total:>5}  {axis_str}  {v2_str}"
        )

    print(f"\n  {'─'*100}")
    print(
        "\n  Legend: DED=Data Extraction  MC=Modification+Consent  PA=Procedural Adhesion"
    )
    print("          RF=Remedy Foreclosure  ECA=Enforcement Cost Asymmetry")
    print("          ███=90%+ entities active  ██░=70%+  █░░=50%+  ░░░=any  ___=none")

    # Axis summary across all chains
    print(f"\n{'─'*100}")
    print(f"\n  Axis penetration across all {len(results)} chains:")
    for ax in _AXES:
        chains_active = sum(
            1
            for r in results
            if any(d["active"] for d in r["axis_detail"] if d["axis"] == ax)
        )
        print(
            f"    {_AXIS_SHORT[ax]:<4} active in {chains_active}/{len(results)} chains"
        )

    # Top entities by impact
    print(f"\n{'─'*100}")
    print("\n  Chain-crossing entities (appear in 2+ chains):")
    entity_chains: dict[str, list[str]] = {}
    for r in results:
        for m in r["members"]:
            entity_chains.setdefault(m["entity_name"], []).append(r["chain_name"][:25])
    anchor_entities = {
        r["members"][0]["entity_name"] if r["members"] else "" for r in results
    }
    cross = {e: chains for e, chains in entity_chains.items() if len(chains) >= 2}
    for entity, chain_names in sorted(
        cross.items(), key=lambda x: len(x[1]), reverse=True
    ):
        print(f"    {entity[:40]:<40} → {', '.join(chain_names)}")

    print()


def print_markdown(results: list[dict]) -> None:
    print("# CONTRA Cross-Chain CIFU Comparison")
    print(f"\n*Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*\n")
    print("| Chain | CIFU | Band | N | DED | MC | PA | RF | ECA |")
    print("|-------|------|------|---|-----|----|----|----|----|")
    for r in results:
        n = r["n_entities"]

        def pct(ax):
            d = next((x for x in r["axis_detail"] if x["axis"] == ax), None)
            return f"{d['entity_count']}/{n}" if d else "0"

        print(
            f"| {r['chain_name']} | **{r['cifu_score']}** | {r['band']} | {n} | "
            f"{pct('data_extraction_depth')} | {pct('modification_and_consent')} | "
            f"{pct('procedural_adhesion')} | {pct('remedy_foreclosure')} | "
            f"{pct('enforcement_cost_asymmetry')} |"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="CONTRA cross-chain CIFU comparison")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    print("Computing all chains...", flush=True)
    results = run_comparison(args.db_path)

    if args.markdown:
        print_markdown(results)
    else:
        print_table(results)

    if args.json_out:
        out = Path(args.json_out)
        out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        print(f"JSON saved: {out}")


if __name__ == "__main__":
    main()
