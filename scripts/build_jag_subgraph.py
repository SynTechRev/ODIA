#!/usr/bin/env python3
"""Day 8: Build and export the JAG anti-supplanting knowledge graph.

Reads oraculus_audit.db, builds the subgraph, and writes:
  data/graphs/jag_anti_supplanting.json  -- node-link JSON
  data/graphs/jag_anti_supplanting.html  -- pyvis interactive visualization

Usage:
  python -I scripts/build_jag_subgraph.py
  python -I scripts/build_jag_subgraph.py --db oraculus_audit.db --out-dir data/graphs
  python -I scripts/build_jag_subgraph.py --json-only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oraculus_di_auditor.knowledge_graph.jag_subgraph import (
    build_jag_subgraph,
    export_graph_html,
    export_graph_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build JAG anti-supplanting knowledge graph"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("oraculus_audit.db"),
        help="Path to oraculus_audit.db",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/graphs"),
        help="Output directory for graph files",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Export JSON only, skip HTML visualization",
    )
    args = parser.parse_args()

    if not args.db.exists():
        print(f"ERROR: database not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    print(f"Building JAG subgraph from {args.db}...")
    subgraph = build_jag_subgraph(args.db)
    stats = subgraph.stats()

    print("Graph built:")
    print(f"  Nodes: {stats['nodes']}")
    print(f"  Edges: {stats['edges']}")
    print(f"  Node types: {stats['node_types']}")
    print(f"  Jurisdictions: {stats['jurisdictions']}")
    print(f"  Critical findings (anti-supplanting): {stats['total_critical']}")
    print(f"  High findings (jag-funded-surveillance): {stats['total_high']}")

    json_path = args.out_dir / "jag_anti_supplanting.json"
    export_graph_json(subgraph, json_path)
    print(f"JSON exported: {json_path}")

    if not args.json_only:
        html_path = args.out_dir / "jag_anti_supplanting.html"
        export_graph_html(subgraph, html_path)
        print(f"HTML exported: {html_path}")

    print()
    print("Watch 2 check (pyvis render quality gate): node count under 500")
    watch2_pass = stats["nodes"] < 500
    print(
        f"  Nodes: {stats['nodes']} -- {'PASS' if watch2_pass else 'FAIL (exceeds 500)'}"
    )

    print()
    print(
        "Watch 1 check: JAG anti-supplanting chain coverage (all jurisdictions present)"
    )
    jurisdiction_nodes = [
        n
        for n, d in subgraph.G.nodes(data=True)
        if d.get("node_type") == "jurisdiction"
    ]
    print(f"  Jurisdiction nodes: {len(jurisdiction_nodes)}")
    for jn in sorted(jurisdiction_nodes):
        juris = jn.replace("JURIS:", "")
        # check it has at least one outgoing finding edge
        out_edges = list(subgraph.G.successors(jn))
        print(f"    {juris}: {len(out_edges)} finding links")


if __name__ == "__main__":
    main()
