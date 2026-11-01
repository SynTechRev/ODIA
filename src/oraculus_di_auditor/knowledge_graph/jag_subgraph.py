"""Day 8: Knowledge Graph -- JAG Anti-Supplanting Subgraph.

Builds a directed knowledge graph of the JAG anti-supplanting evidence chain
across all ODIA-indexed jurisdictions. Nodes represent federal statutes,
jurisdictions, finding clusters, surveillance vendors, and the pattern-and-practice
anchor. Edges represent the compliance violation chain from federal requirement
to corpus finding to Section 1983 predicate.

Graph topology (54 nodes, ~120 edges):
  Federal statute nodes (3) -> Jurisdiction nodes (14) -> Finding clusters (28)
  Finding clusters -> Vendor nodes (8) [jag-funded-surveillance only]
  Critical finding clusters -> Pattern-and-practice anchor (1)

Watch 2 compliance: node count held under 500 (target 100-300) for pyvis render quality.

Output:
  data/graphs/jag_anti_supplanting.json  -- node-link JSON for Day 9 memory integration
  data/graphs/jag_anti_supplanting.html  -- pyvis interactive visualization
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Node type constants
# ---------------------------------------------------------------------------

NT_STATUTE = "federal_statute"
NT_REQUIREMENT = "federal_requirement"
NT_JURISDICTION = "jurisdiction"
NT_FINDING_CRITICAL = "finding_cluster_critical"
NT_FINDING_HIGH = "finding_cluster_high"
NT_VENDOR = "vendor"
NT_ANCHOR = "pattern_and_practice_anchor"

# Edge type constants
ET_GRANT_RECEIVED = "JAG_GRANT_RECEIVED"
ET_VIOLATED = "ANTI_SUPPLANTING_VIOLATED"
ET_NOT_REPORTED = "BJA_REPORTING_NOT_MET"
ET_HAS_FINDING = "HAS_CRITICAL_FINDING"
ET_HAS_HIGH = "HAS_HIGH_FINDING"
ET_NAMES_VENDOR = "NAMES_VENDOR"
ET_SUPPORTS = "SUPPORTS_PATTERN_AND_PRACTICE"
ET_REQUIRES = "REQUIRES"

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class JurisdictionFindings:
    jurisdiction: str
    anti_supplanting_count: int = 0
    jag_surveillance_count: int = 0
    vendors: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# DB query
# ---------------------------------------------------------------------------


def _query_jag_findings(db_path: Path) -> dict[str, JurisdictionFindings]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    findings: dict[str, JurisdictionFindings] = {}

    # Anti-supplanting (critical)
    rows = conn.execute("""
        SELECT d.jurisdiction, COUNT(*) as cnt
        FROM anomalies a
        JOIN analyses an ON a.analysis_id = an.id
        JOIN documents d ON an.document_id = d.document_id
        WHERE a.anomaly_id = 'grant:jag-without-anti-supplanting'
        GROUP BY d.jurisdiction
    """).fetchall()
    for r in rows:
        juris = r["jurisdiction"]
        if juris not in findings:
            findings[juris] = JurisdictionFindings(jurisdiction=juris)
        findings[juris].anti_supplanting_count = r["cnt"]

    # JAG-funded surveillance (high) with vendor names
    rows2 = conn.execute("""
        SELECT d.jurisdiction, a.details_json
        FROM anomalies a
        JOIN analyses an ON a.analysis_id = an.id
        JOIN documents d ON an.document_id = d.document_id
        WHERE a.anomaly_id = 'grant:jag-funded-surveillance'
    """).fetchall()
    for r in rows2:
        juris = r["jurisdiction"]
        if juris not in findings:
            findings[juris] = JurisdictionFindings(jurisdiction=juris)
        findings[juris].jag_surveillance_count += 1
        if r["details_json"]:
            try:
                details = json.loads(r["details_json"])
                for v in details.get("vendors", []):
                    if v:
                        findings[juris].vendors.add(v)
            except (json.JSONDecodeError, TypeError):
                pass

    conn.close()
    return findings


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


class JAGSubgraph:
    """JAG anti-supplanting evidence chain as a networkx DiGraph."""

    def __init__(self) -> None:
        self.G: nx.DiGraph = nx.DiGraph()
        self._jurisdiction_findings: dict[str, JurisdictionFindings] = {}

    def build(self, jurisdiction_findings: dict[str, JurisdictionFindings]) -> None:
        self._jurisdiction_findings = jurisdiction_findings
        self.G = nx.DiGraph()

        self._add_federal_layer()
        self._add_jurisdiction_layer(jurisdiction_findings)
        self._add_finding_clusters(jurisdiction_findings)
        self._add_vendor_layer(jurisdiction_findings)
        self._add_anchor_layer(jurisdiction_findings)

    def _add_federal_layer(self) -> None:
        self.G.add_node(
            "34_USC_10152",
            label="34 USC 10152\nJAG Statute",
            node_type=NT_STATUTE,
            title="Edward Byrne Memorial Justice Assistance Grant Program\n34 USC 10152",
            color="#1a4480",
            size=40,
            shape="diamond",
        )
        self.G.add_node(
            "34_USC_10153_a_2",
            label="34 USC 10153(a)(2)\nAnti-Supplanting",
            node_type=NT_REQUIREMENT,
            title=(
                "Anti-supplanting requirement: JAG funds may not be used to supplant "
                "State or local funds that would otherwise be available for law "
                "enforcement activities. 34 USC 10153(a)(2)."
            ),
            color="#c41230",
            size=40,
            shape="diamond",
        )
        self.G.add_node(
            "BJA_REPORTING",
            label="BJA Reporting\nRequirement",
            node_type=NT_REQUIREMENT,
            title=(
                "Bureau of Justice Assistance reporting requirement: JAG-funded "
                "technology purchases must be itemised and reported to BJA. "
                "2 CFR Part 200 / JAG Program conditions."
            ),
            color="#8b0000",
            size=30,
            shape="diamond",
        )
        # Federal statutes link: JAG grants must satisfy anti-supplanting
        self.G.add_edge(
            "34_USC_10152",
            "34_USC_10153_a_2",
            edge_type=ET_REQUIRES,
            label="requires",
            color="#555555",
        )
        self.G.add_edge(
            "34_USC_10152",
            "BJA_REPORTING",
            edge_type=ET_REQUIRES,
            label="requires",
            color="#555555",
        )

    def _add_jurisdiction_layer(
        self, jurisdiction_findings: dict[str, JurisdictionFindings]
    ) -> None:
        for juris, jf in sorted(jurisdiction_findings.items()):
            total = jf.anti_supplanting_count + jf.jag_surveillance_count
            self.G.add_node(
                f"JURIS:{juris}",
                label=juris,
                node_type=NT_JURISDICTION,
                title=(
                    f"Jurisdiction: {juris}\n"
                    f"Anti-supplanting (critical): {jf.anti_supplanting_count}\n"
                    f"JAG-funded surveillance (high): {jf.jag_surveillance_count}\n"
                    f"Total JAG findings: {total}"
                ),
                color="#2e6da4",
                size=max(20, min(45, 20 + total // 10)),
                shape="ellipse",
                jurisdiction=juris,
            )
            # Federal statute -> jurisdiction (grant received)
            self.G.add_edge(
                "34_USC_10152",
                f"JURIS:{juris}",
                edge_type=ET_GRANT_RECEIVED,
                label="grant received",
                color="#2e6da4",
            )

    def _add_finding_clusters(
        self, jurisdiction_findings: dict[str, JurisdictionFindings]
    ) -> None:
        for juris, jf in sorted(jurisdiction_findings.items()):
            # Anti-supplanting critical cluster
            if jf.anti_supplanting_count > 0:
                node_id = f"ANTI_SUPPLANTING:{juris}"
                self.G.add_node(
                    node_id,
                    label=f"Anti-Supplanting\n{juris}\n({jf.anti_supplanting_count} critical)",
                    node_type=NT_FINDING_CRITICAL,
                    title=(
                        f"jag-without-anti-supplanting\n"
                        f"Jurisdiction: {juris}\n"
                        f"Severity: CRITICAL\n"
                        f"Count: {jf.anti_supplanting_count}\n"
                        f"Issue: JAG-funded expenditures lack anti-supplanting certification"
                    ),
                    color="#c41230",
                    size=max(15, min(35, 15 + jf.anti_supplanting_count // 10)),
                    shape="box",
                    finding_type="jag-without-anti-supplanting",
                    severity="critical",
                    count=jf.anti_supplanting_count,
                    jurisdiction=juris,
                )
                self.G.add_edge(
                    f"JURIS:{juris}",
                    node_id,
                    edge_type=ET_HAS_FINDING,
                    label=f"{jf.anti_supplanting_count} critical",
                    color="#c41230",
                    weight=jf.anti_supplanting_count,
                )
                self.G.add_edge(
                    "34_USC_10153_a_2",
                    node_id,
                    edge_type=ET_VIOLATED,
                    label="violated",
                    color="#c41230",
                )

            # JAG-funded surveillance high cluster
            if jf.jag_surveillance_count > 0:
                node_id = f"JAG_SURVEILLANCE:{juris}"
                self.G.add_node(
                    node_id,
                    label=f"JAG Surveillance\n{juris}\n({jf.jag_surveillance_count} high)",
                    node_type=NT_FINDING_HIGH,
                    title=(
                        f"jag-funded-surveillance\n"
                        f"Jurisdiction: {juris}\n"
                        f"Severity: HIGH\n"
                        f"Count: {jf.jag_surveillance_count}\n"
                        f"Vendors: {', '.join(sorted(jf.vendors))}\n"
                        f"Issue: JAG grant referenced alongside surveillance vendor without "
                        f"BJA itemisation"
                    ),
                    color="#d47500",
                    size=max(15, min(30, 15 + jf.jag_surveillance_count // 5)),
                    shape="box",
                    finding_type="jag-funded-surveillance",
                    severity="high",
                    count=jf.jag_surveillance_count,
                    jurisdiction=juris,
                    vendors=list(sorted(jf.vendors)),
                )
                self.G.add_edge(
                    f"JURIS:{juris}",
                    node_id,
                    edge_type=ET_HAS_HIGH,
                    label=f"{jf.jag_surveillance_count} high",
                    color="#d47500",
                    weight=jf.jag_surveillance_count,
                )
                self.G.add_edge(
                    "BJA_REPORTING",
                    node_id,
                    edge_type=ET_NOT_REPORTED,
                    label="not reported",
                    color="#d47500",
                )

    def _add_vendor_layer(
        self, jurisdiction_findings: dict[str, JurisdictionFindings]
    ) -> None:
        all_vendors: dict[str, list[str]] = defaultdict(list)
        for juris, jf in jurisdiction_findings.items():
            for vendor in jf.vendors:
                all_vendors[vendor].append(juris)

        vendor_colors = {
            "Axon Enterprise": "#4a1942",
            "Flock Safety": "#1b4332",
            "BCS Consulting": "#003087",
            "Lexipol": "#2c3e50",
            "T-Mobile": "#e20074",
            "Motorola Solutions": "#005eb8",
            "Nexanet": "#4a4a4a",
            "Security Lines US": "#6b3a2a",
        }

        for vendor, jurisdictions in sorted(all_vendors.items()):
            color = vendor_colors.get(vendor, "#555555")
            self.G.add_node(
                f"VENDOR:{vendor}",
                label=vendor,
                node_type=NT_VENDOR,
                title=(
                    f"Vendor: {vendor}\n"
                    f"Jurisdictions with JAG-funded purchases: {len(jurisdictions)}\n"
                    f"({', '.join(sorted(jurisdictions))})"
                ),
                color=color,
                size=max(20, min(35, 15 + len(jurisdictions) * 3)),
                shape="triangle",
                vendor_name=vendor,
                jurisdiction_count=len(jurisdictions),
            )
            # Each jurisdiction's surveillance cluster -> vendor
            for juris in sorted(set(jurisdictions)):
                surv_node = f"JAG_SURVEILLANCE:{juris}"
                if self.G.has_node(surv_node):
                    self.G.add_edge(
                        surv_node,
                        f"VENDOR:{vendor}",
                        edge_type=ET_NAMES_VENDOR,
                        label="names vendor",
                        color=color,
                    )

    def _add_anchor_layer(
        self, jurisdiction_findings: dict[str, JurisdictionFindings]
    ) -> None:
        total_critical = sum(
            jf.anti_supplanting_count for jf in jurisdiction_findings.values()
        )
        total_high = sum(
            jf.jag_surveillance_count for jf in jurisdiction_findings.values()
        )
        self.G.add_node(
            "SECTION_1983_PATTERN",
            label=(
                "Section 1983\nPattern and Practice\n"
                f"({total_critical} critical / {total_high} high)"
            ),
            node_type=NT_ANCHOR,
            title=(
                "42 USC 1983 Pattern and Practice Anchor\n"
                f"Total anti-supplanting violations: {total_critical}\n"
                f"Total BJA reporting failures: {total_high}\n"
                "Cross-jurisdictional scope: 14 agencies\n"
                "Predicate: systematic failure to certify anti-supplanting compliance "
                "across all JAG-funded expenditures in the Fresno / Tulare county region"
            ),
            color="#000000",
            size=55,
            shape="star",
            total_critical=total_critical,
            total_high=total_high,
        )
        # Critical finding clusters -> anchor
        for juris, jf in jurisdiction_findings.items():
            if jf.anti_supplanting_count > 0:
                self.G.add_edge(
                    f"ANTI_SUPPLANTING:{juris}",
                    "SECTION_1983_PATTERN",
                    edge_type=ET_SUPPORTS,
                    label="supports",
                    color="#c41230",
                    weight=jf.anti_supplanting_count,
                )

    def stats(self) -> dict[str, Any]:
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "node_types": dict(
                Counter(
                    self.G.nodes[n].get("node_type", "unknown") for n in self.G.nodes
                )
            ),
            "jurisdictions": len(self._jurisdiction_findings),
            "total_critical": sum(
                jf.anti_supplanting_count for jf in self._jurisdiction_findings.values()
            ),
            "total_high": sum(
                jf.jag_surveillance_count for jf in self._jurisdiction_findings.values()
            ),
        }


# ---------------------------------------------------------------------------
# Public build function
# ---------------------------------------------------------------------------


def build_jag_subgraph(db_path: Path | str) -> JAGSubgraph:
    """Query oraculus_audit.db and build the JAG anti-supplanting knowledge graph."""
    db_path = Path(db_path)
    jurisdiction_findings = _query_jag_findings(db_path)
    subgraph = JAGSubgraph()
    subgraph.build(jurisdiction_findings)
    return subgraph


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------


def export_graph_json(subgraph: JAGSubgraph, output_path: Path | str) -> dict:
    """Export subgraph as node-link JSON for Day 9 memory integration."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = nx.node_link_data(subgraph.G)
    stats = subgraph.stats()
    export = {"stats": stats, "graph": data}

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(export, fh, indent=2, default=str)

    logger.info(
        "Graph JSON exported to %s (%d nodes, %d edges)",
        output_path,
        stats["nodes"],
        stats["edges"],
    )
    return export


def export_graph_html(
    subgraph: JAGSubgraph,
    output_path: Path | str,
    notebook: bool = False,
) -> None:
    """Render subgraph as interactive pyvis HTML visualization."""
    try:
        from pyvis.network import Network
    except ImportError:
        logger.warning("pyvis not available -- skipping HTML export")
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    net = Network(
        height="900px",
        width="100%",
        directed=True,
        notebook=notebook,
        bgcolor="#1a1a2e",
        font_color="white",
    )

    # Add nodes
    for node_id, attrs in subgraph.G.nodes(data=True):
        net.add_node(
            str(node_id),
            label=attrs.get("label", str(node_id)),
            title=attrs.get("title", ""),
            color=attrs.get("color", "#888888"),
            size=attrs.get("size", 20),
            shape=attrs.get("shape", "ellipse"),
        )

    # Add edges
    for src, dst, attrs in subgraph.G.edges(data=True):
        net.add_edge(
            str(src),
            str(dst),
            title=attrs.get("label", ""),
            color=attrs.get("color", "#888888"),
            arrows="to",
        )

    # Physics layout for DAG readability
    net.set_options("""
{
  "physics": {
    "hierarchicalRepulsion": {
      "centralGravity": 0.1,
      "springLength": 200,
      "springConstant": 0.02,
      "nodeDistance": 180,
      "damping": 0.09
    },
    "solver": "hierarchicalRepulsion",
    "stabilization": {"iterations": 200}
  },
  "layout": {
    "hierarchical": {
      "enabled": true,
      "levelSeparation": 180,
      "nodeSpacing": 160,
      "treeSpacing": 200,
      "direction": "UD",
      "sortMethod": "directed"
    }
  },
  "edges": {
    "smooth": {"type": "cubicBezier", "forceDirection": "vertical"},
    "arrows": {"to": {"enabled": true, "scaleFactor": 0.8}}
  },
  "nodes": {
    "font": {"size": 11, "color": "white"}
  },
  "interaction": {
    "hover": true,
    "navigationButtons": true,
    "keyboard": true
  }
}
""")

    net.save_graph(str(output_path))
    logger.info("Graph HTML exported to %s", output_path)
