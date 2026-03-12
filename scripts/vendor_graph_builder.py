#!/usr/bin/env python3
"""Vendor Influence Graph Builder v1.0.

This module implements the vendor influence graph engine that:
- Builds a graph model of vendor relationships
- Creates Vendor → Contract → Year edges
- Calculates influence scores
- Outputs vendor_graph.json, vendor_scores.json, vendor_influence_network.csv

Author: GitHub Copilot Agent
Date: 2025-12-06
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import HIST_FILES  # noqa: E402

# Constants
VICFM_VERSION = "1.0"

# Influence score weights
WEIGHT_FREQUENCY = 0.25
WEIGHT_VALUE = 0.25
WEIGHT_ANOMALY = 0.20
WEIGHT_CENTRALITY = 0.15
WEIGHT_CONTINUITY = 0.15


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_year_range(year_range: str) -> tuple[int, int]:
    """Parse a year range string (e.g., '2014-2025') into start and end years."""
    if "-" in year_range:
        parts = year_range.split("-")
        return int(parts[0]), int(parts[1])
    else:
        year = int(year_range)
        return year, year


def filter_corpora_by_years(start_year: int, end_year: int) -> dict[str, str]:
    """Filter HIST_FILES to only include entries within the year range."""
    filtered = {}
    for hist_id, meeting_date in HIST_FILES.items():
        year = int(meeting_date[:4])
        if start_year <= year <= end_year:
            filtered[hist_id] = meeting_date
    return filtered


class VendorGraph:
    """Lightweight graph model for vendor relationships."""

    def __init__(self):
        """Initialize empty graph."""
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self.adjacency: dict[str, list[str]] = defaultdict(list)

    def add_node(
        self, node_id: str, node_type: str, **attributes: Any
    ) -> dict[str, Any]:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node
            node_type: Type of node (vendor, contract, year, corpus)
            **attributes: Additional node attributes

        Returns:
            The created node
        """
        node = {
            "id": node_id,
            "type": node_type,
            **attributes,
        }
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        **attributes: Any,
    ) -> dict[str, Any]:
        """Add an edge to the graph.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Type of relationship
            **attributes: Additional edge attributes

        Returns:
            The created edge
        """
        edge = {
            "source": source,
            "target": target,
            "type": edge_type,
            **attributes,
        }
        self.edges.append(edge)
        self.adjacency[source].append(target)
        self.adjacency[target].append(source)
        return edge

    def get_neighbors(self, node_id: str) -> list[str]:
        """Get neighbors of a node.

        Returns:
            List of neighbor node IDs
        """
        return self.adjacency.get(node_id, [])

    def get_degree(self, node_id: str) -> int:
        """Get degree of a node.

        Returns:
            Number of edges connected to node
        """
        return len(self.adjacency.get(node_id, []))

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary for JSON serialization.

        Returns:
            Dictionary representation of graph
        """
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": self._count_node_types(),
                "edge_types": self._count_edge_types(),
            },
        }

    def _count_node_types(self) -> dict[str, int]:
        """Count nodes by type."""
        counts: dict[str, int] = defaultdict(int)
        for node in self.nodes.values():
            counts[node.get("type", "unknown")] += 1
        return dict(counts)

    def _count_edge_types(self) -> dict[str, int]:
        """Count edges by type."""
        counts: dict[str, int] = defaultdict(int)
        for edge in self.edges:
            counts[edge.get("type", "unknown")] += 1
        return dict(counts)


def build_vendor_graph(
    vendor_index: dict[str, Any],
    relationships: list[dict[str, Any]],
    corpora: dict[str, str],
    tech_programs: dict[str, Any] | None = None,
) -> VendorGraph:
    """Build a vendor influence graph from extraction data.

    Creates nodes for:
    - Vendors
    - Contracts (corpus items)
    - Years

    Creates edges for:
    - Vendor → Contract (mentions)
    - Contract → Year (temporal)
    - Vendor → Year (activity)

    Returns:
        VendorGraph instance
    """
    graph = VendorGraph()

    # Create year nodes
    years = set()
    for meeting_date in corpora.values():
        year = meeting_date[:4]
        years.add(year)

    for year in sorted(years):
        graph.add_node(f"year:{year}", "year", year=year)

    # Create corpus nodes
    for hist_id, meeting_date in corpora.items():
        year = meeting_date[:4]
        graph.add_node(
            f"corpus:{hist_id}",
            "corpus",
            hist_id=hist_id,
            year=year,
            meeting_date=meeting_date,
        )
        # Link corpus to year
        graph.add_edge(f"corpus:{hist_id}", f"year:{year}", "occurred_in")

    # Create vendor nodes
    for vendor_name, vendor_data in vendor_index.items():
        graph.add_node(
            f"vendor:{vendor_name}",
            "vendor",
            name=vendor_name,
            appearance_count=vendor_data.get("appearance_count", 0),
            year_span=vendor_data.get("year_span", 0),
            years=vendor_data.get("years", []),
        )

        # Link vendor to corpora where they appear
        for hist_id in vendor_data.get("hist_ids", []):
            if hist_id in corpora:
                graph.add_edge(
                    f"vendor:{vendor_name}",
                    f"corpus:{hist_id}",
                    "mentioned_in",
                )

        # Link vendor to years
        for year in vendor_data.get("years", []):
            graph.add_edge(
                f"vendor:{vendor_name}",
                f"year:{year}",
                "active_in",
            )

    # Add relationship edges with amounts
    for rel in relationships:
        vendor = rel.get("vendor")
        hist_id = rel.get("hist_id")
        amount = rel.get("total_amount", 0)

        if vendor and hist_id and hist_id in corpora:
            # Add contract edge with amount
            graph.add_edge(
                f"vendor:{vendor}",
                f"corpus:{hist_id}",
                "contract_with",
                amount=amount,
            )

    # Add technology program nodes and edges
    if tech_programs:
        for prog_name, prog_data in tech_programs.items():
            if prog_data.get("mention_count", 0) > 0:
                graph.add_node(
                    f"program:{prog_name}",
                    "program",
                    name=prog_name,
                    mention_count=prog_data.get("mention_count", 0),
                    years=prog_data.get("years", []),
                )

                # Link vendors to programs
                for vendor in prog_data.get("vendors", []):
                    if f"vendor:{vendor}" in graph.nodes:
                        graph.add_edge(
                            f"vendor:{vendor}",
                            f"program:{prog_name}",
                            "associated_with",
                        )

    return graph


def calculate_influence_scores(
    graph: VendorGraph,
    vendor_index: dict[str, Any],
    relationships: list[dict[str, Any]],
    ace_anomalies: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Calculate influence scores for each vendor.

    Influence score is calculated based on:
    - Contract frequency (25%)
    - Contract value (25%)
    - Anomaly intersections with ACE (20%)
    - Technology centrality (15%)
    - Cross-year continuity (15%)

    Returns:
        Dictionary of vendor scores
    """
    scores: dict[str, dict[str, Any]] = {}

    # Calculate max values for normalization
    max_frequency = max(
        (v.get("appearance_count", 0) for v in vendor_index.values()), default=1
    )
    max_value = max((r.get("total_amount", 0) or 0 for r in relationships), default=1)
    max_years = max((v.get("year_span", 0) for v in vendor_index.values()), default=1)
    max_centrality = max(
        (graph.get_degree(f"vendor:{v}") for v in vendor_index), default=1
    )

    # Build anomaly map by hist_id
    anomaly_counts: dict[str, int] = defaultdict(int)
    if ace_anomalies:
        for anomaly in ace_anomalies:
            hist_id = anomaly.get("hist_id")
            if hist_id:
                anomaly_counts[hist_id] += 1

    for vendor_name, vendor_data in vendor_index.items():
        # Frequency score (normalized)
        frequency = vendor_data.get("appearance_count", 0)
        freq_score = frequency / max_frequency if max_frequency > 0 else 0

        # Value score (normalized)
        vendor_amounts = [
            r.get("total_amount", 0) or 0
            for r in relationships
            if r.get("vendor") == vendor_name
        ]
        total_value = sum(vendor_amounts)
        value_score = total_value / max_value if max_value > 0 else 0

        # Anomaly intersection score
        vendor_hist_ids = vendor_data.get("hist_ids", [])
        anomaly_intersections = sum(anomaly_counts.get(h, 0) for h in vendor_hist_ids)
        anomaly_score = min(anomaly_intersections / 10, 1.0)  # Cap at 1.0

        # Centrality score (normalized degree)
        degree = graph.get_degree(f"vendor:{vendor_name}")
        centrality_score = degree / max_centrality if max_centrality > 0 else 0

        # Continuity score (year span normalized)
        year_span = vendor_data.get("year_span", 0)
        continuity_score = year_span / max_years if max_years > 0 else 0

        # Calculate weighted influence score
        influence_score = (
            (freq_score * WEIGHT_FREQUENCY)
            + (value_score * WEIGHT_VALUE)
            + (anomaly_score * WEIGHT_ANOMALY)
            + (centrality_score * WEIGHT_CENTRALITY)
            + (continuity_score * WEIGHT_CONTINUITY)
        )

        scores[vendor_name] = {
            "vendor": vendor_name,
            "influence_score": round(influence_score, 4),
            "components": {
                "frequency": round(freq_score, 4),
                "value": round(value_score, 4),
                "anomaly_intersection": round(anomaly_score, 4),
                "centrality": round(centrality_score, 4),
                "continuity": round(continuity_score, 4),
            },
            "raw_metrics": {
                "appearance_count": frequency,
                "total_contract_value": total_value,
                "anomaly_intersections": anomaly_intersections,
                "graph_degree": degree,
                "year_span": year_span,
            },
            "years": vendor_data.get("years", []),
        }

    return scores


def determine_dependency_tier(score: float) -> str:
    """Determine dependency tier based on influence score.

    Tiers:
    - Critical: >= 0.8
    - High: >= 0.6
    - Moderate: >= 0.4
    - Low: < 0.4

    Returns:
        Tier string
    """
    if score >= 0.8:
        return "Critical"
    elif score >= 0.6:
        return "High"
    elif score >= 0.4:
        return "Moderate"
    else:
        return "Low"


def generate_vendor_scores_report(scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Generate the vendor_scores.json report.

    Returns:
        Dictionary suitable for JSON output
    """
    timestamp = get_utc_timestamp()

    # Sort vendors by influence score
    sorted_vendors = sorted(
        scores.values(), key=lambda x: x.get("influence_score", 0), reverse=True
    )

    # Add tier and rank
    for rank, vendor_score in enumerate(sorted_vendors, 1):
        vendor_score["rank"] = rank
        vendor_score["tier"] = determine_dependency_tier(
            vendor_score.get("influence_score", 0)
        )

    # Count by tier
    tier_counts: dict[str, int] = defaultdict(int)
    for vs in sorted_vendors:
        tier_counts[vs.get("tier", "Unknown")] += 1

    return {
        "version": VICFM_VERSION,
        "generated_at": timestamp,
        "summary": {
            "total_vendors": len(sorted_vendors),
            "tier_distribution": dict(tier_counts),
            "top_5_vendors": [
                {"vendor": v["vendor"], "score": v["influence_score"]}
                for v in sorted_vendors[:5]
            ],
        },
        "scoring_weights": {
            "frequency": WEIGHT_FREQUENCY,
            "value": WEIGHT_VALUE,
            "anomaly_intersection": WEIGHT_ANOMALY,
            "centrality": WEIGHT_CENTRALITY,
            "continuity": WEIGHT_CONTINUITY,
        },
        "vendors": sorted_vendors,
    }


def generate_influence_network_csv(
    graph: VendorGraph, scores: dict[str, dict[str, Any]]
) -> list[list[str]]:
    """Generate vendor_influence_network.csv data.

    Returns:
        List of CSV rows
    """
    headers = [
        "source",
        "target",
        "edge_type",
        "source_type",
        "target_type",
        "source_score",
        "amount",
    ]

    rows = [headers]

    for edge in graph.edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        edge_type = edge.get("type", "")
        amount = edge.get("amount", "")

        # Get node types
        source_node = graph.nodes.get(source, {})
        target_node = graph.nodes.get(target, {})
        source_type = source_node.get("type", "")
        target_type = target_node.get("type", "")

        # Get source score if it's a vendor
        source_score = ""
        if source.startswith("vendor:"):
            vendor_name = source.replace("vendor:", "")
            if vendor_name in scores:
                source_score = str(scores[vendor_name].get("influence_score", ""))

        rows.append(
            [
                source,
                target,
                edge_type,
                source_type,
                target_type,
                source_score,
                str(amount) if amount else "",
            ]
        )

    return rows


def load_ace_report(ace_report_path: Path | None = None) -> list[dict[str, Any]]:
    """Load ACE anomalies from ACE_REPORT.json.

    Returns:
        List of anomalies or empty list if not found
    """
    if ace_report_path is None:
        ace_report_path = Path("ACE_REPORT.json")

    if ace_report_path.exists():
        try:
            with open(ace_report_path, encoding="utf-8") as f:
                ace_report = json.load(f)
                return ace_report.get("all_anomalies", [])
        except (json.JSONDecodeError, OSError):
            pass

    return []


def load_vendor_extraction(extraction_path: Path) -> dict[str, Any]:
    """Load vendor extraction results.

    Returns:
        Extraction data dictionary
    """
    if extraction_path.exists():
        try:
            with open(extraction_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    return {}


def generate_vendor_anomaly_links(
    vendor_index: dict[str, Any],
    ace_anomalies: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate VENDOR_ANOMALY_LINKS.json content.

    Maps vendors to their associated ACE anomalies.

    Returns:
        Dictionary of vendor-anomaly links
    """
    timestamp = get_utc_timestamp()

    # Build anomaly map by hist_id
    anomalies_by_hist: dict[str, list[dict]] = defaultdict(list)
    for anomaly in ace_anomalies:
        hist_id = anomaly.get("hist_id")
        if hist_id:
            anomalies_by_hist[hist_id].append(anomaly)

    # Link vendors to anomalies
    vendor_links: dict[str, dict] = {}
    for vendor_name, vendor_data in vendor_index.items():
        hist_ids = vendor_data.get("hist_ids", [])
        linked_anomalies = []

        for hist_id in hist_ids:
            if hist_id in anomalies_by_hist:
                for anomaly in anomalies_by_hist[hist_id]:
                    linked_anomalies.append(
                        {
                            "hist_id": hist_id,
                            "anomaly_type": anomaly.get("type"),
                            "subtype": anomaly.get("subtype"),
                            "ace_score": anomaly.get("ace_score"),
                            "severity": anomaly.get("severity"),
                        }
                    )

        if linked_anomalies:
            vendor_links[vendor_name] = {
                "vendor": vendor_name,
                "anomaly_count": len(linked_anomalies),
                "max_ace_score": max(
                    (a.get("ace_score", 0) for a in linked_anomalies), default=0
                ),
                "anomalies": linked_anomalies,
            }

    return {
        "version": VICFM_VERSION,
        "generated_at": timestamp,
        "total_vendors_with_anomalies": len(vendor_links),
        "vendor_links": vendor_links,
    }


def generate_tech_dependencies(
    tech_programs: dict[str, Any],
    ace_anomalies: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate VENDOR_TECH_DEPENDENCIES.json content.

    Maps technology programs to vendors and anomaly flags.

    Returns:
        Dictionary of tech dependencies
    """
    timestamp = get_utc_timestamp()

    # Build anomaly map by hist_id
    anomalies_by_hist: dict[str, list[dict]] = defaultdict(list)
    for anomaly in ace_anomalies:
        hist_id = anomaly.get("hist_id")
        if hist_id:
            anomalies_by_hist[hist_id].append(anomaly)

    dependencies: dict[str, dict] = {}
    for prog_name, prog_data in tech_programs.items():
        hist_ids = prog_data.get("hist_ids", [])
        vendors = prog_data.get("vendors", [])

        # Check for anomalies in program-related corpora
        program_anomalies = []
        for hist_id in hist_ids:
            if hist_id in anomalies_by_hist:
                program_anomalies.extend(anomalies_by_hist[hist_id])

        dependencies[prog_name] = {
            "program": prog_name,
            "vendors": vendors,
            "vendor_count": len(vendors),
            "years_active": prog_data.get("years", []),
            "year_count": len(prog_data.get("years", [])),
            "anomaly_count": len(program_anomalies),
            "has_anomaly_flag": len(program_anomalies) > 0,
        }

    return {
        "version": VICFM_VERSION,
        "generated_at": timestamp,
        "total_programs": len(dependencies),
        "programs_with_anomalies": sum(
            1 for d in dependencies.values() if d["has_anomaly_flag"]
        ),
        "dependencies": dependencies,
    }


def generate_vendor_influence_report_md(
    scores: dict[str, dict[str, Any]],
    vendor_index: dict[str, Any],
    irregularities: list[dict[str, Any]],
) -> str:
    """Generate VENDOR_INFLUENCE_REPORT.md content.

    Returns:
        Markdown string
    """
    lines = [
        "# Vendor Influence Report (2014–2025)",
        "",
        f"**Generated:** {get_utc_timestamp()}",
        f"**Version:** {VICFM_VERSION}",
        "",
        "## Executive Summary",
        "",
    ]

    # Sort vendors by score
    sorted_vendors = sorted(
        scores.values(), key=lambda x: x.get("influence_score", 0), reverse=True
    )

    # Count by tier
    tier_counts: dict[str, int] = defaultdict(int)
    for vs in sorted_vendors:
        tier = determine_dependency_tier(vs.get("influence_score", 0))
        tier_counts[tier] += 1

    lines.extend(
        [
            f"- **Total Vendors Analyzed:** {len(sorted_vendors)}",
            f"- **Critical Tier:** {tier_counts.get('Critical', 0)}",
            f"- **High Tier:** {tier_counts.get('High', 0)}",
            f"- **Moderate Tier:** {tier_counts.get('Moderate', 0)}",
            f"- **Low Tier:** {tier_counts.get('Low', 0)}",
            "",
            "---",
            "",
            "## Top 25 Vendors by Influence Score",
            "",
            "| Rank | Vendor | Score | Tier | Years | Appearances |",
            "|------|--------|-------|------|-------|-------------|",
        ]
    )

    for i, vs in enumerate(sorted_vendors[:25], 1):
        vendor_name = vs.get("vendor", "Unknown")
        score = vs.get("influence_score", 0)
        tier = determine_dependency_tier(score)
        years = len(vs.get("years", []))
        raw = vs.get("raw_metrics", {})
        appearances = raw.get("appearance_count", 0)
        lines.append(
            f"| {i} | {vendor_name} | {score:.4f} | {tier} | {years} | {appearances} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Influence Score Components",
            "",
            "| Vendor | Frequency | Value | Anomaly | Centrality | Continuity |",
            "|--------|-----------|-------|---------|------------|------------|",
        ]
    )

    for vs in sorted_vendors[:15]:
        vendor_name = vs.get("vendor", "Unknown")
        comp = vs.get("components", {})
        lines.append(
            f"| {vendor_name} | "
            f"{comp.get('frequency', 0):.2f} | "
            f"{comp.get('value', 0):.2f} | "
            f"{comp.get('anomaly_intersection', 0):.2f} | "
            f"{comp.get('centrality', 0):.2f} | "
            f"{comp.get('continuity', 0):.2f} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## Dependency Tiers",
            "",
            "### Critical Tier (Score ≥ 0.80)",
            "",
        ]
    )

    critical = [
        v
        for v in sorted_vendors
        if determine_dependency_tier(v.get("influence_score", 0)) == "Critical"
    ]
    if critical:
        for vs in critical:
            years_str = ", ".join(vs.get("years", [])[:5])
            if len(vs.get("years", [])) > 5:
                years_str += "..."
            lines.append(
                f"- **{vs['vendor']}** - Score: {vs['influence_score']:.4f}, Years: {years_str}"
            )
    else:
        lines.append("*No vendors in Critical tier*")

    lines.extend(
        [
            "",
            "### High Tier (Score 0.60–0.79)",
            "",
        ]
    )

    high = [
        v
        for v in sorted_vendors
        if determine_dependency_tier(v.get("influence_score", 0)) == "High"
    ]
    if high:
        for vs in high[:10]:
            lines.append(f"- **{vs['vendor']}** - Score: {vs['influence_score']:.4f}")
        if len(high) > 10:
            lines.append(f"- *...and {len(high) - 10} more*")
    else:
        lines.append("*No vendors in High tier*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Contract Continuity Paths",
            "",
        ]
    )

    # Show vendors with longest continuity
    continuous = sorted(
        [v for v in sorted_vendors if len(v.get("years", [])) >= 3],
        key=lambda x: len(x.get("years", [])),
        reverse=True,
    )

    for vs in continuous[:10]:
        years = vs.get("years", [])
        lines.append(f"- **{vs['vendor']}**: {' → '.join(years)}")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Notable Escalation Patterns",
            "",
        ]
    )

    escalations = [i for i in irregularities if i.get("type") == "cost_escalation"]
    if escalations:
        for esc in escalations[:10]:
            lines.append(f"- {esc.get('details', 'N/A')}")
    else:
        lines.append("*No significant cost escalations detected*")

    lines.extend(
        [
            "",
            "---",
            "",
            "*Generated by Vendor Influence & Contract Flow Map v1.0*",
        ]
    )

    return "\n".join(lines)


def generate_procurement_flags(
    irregularities: list[dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    """Generate PROCUREMENT_FLAGS.json and PROCUREMENT_FLAGS.md content.

    Returns:
        Tuple of (JSON dict, Markdown string)
    """
    timestamp = get_utc_timestamp()

    # Group by type
    by_type: dict[str, list[dict]] = defaultdict(list)
    for irr in irregularities:
        irr_type = irr.get("type", "unknown")
        by_type[irr_type].append(irr)

    # Count by severity
    by_severity: dict[str, int] = defaultdict(int)
    for irr in irregularities:
        severity = irr.get("severity", "unknown")
        by_severity[severity] += 1

    json_output = {
        "version": VICFM_VERSION,
        "generated_at": timestamp,
        "summary": {
            "total_flags": len(irregularities),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_severity": dict(by_severity),
        },
        "flags": irregularities,
    }

    # Generate markdown
    md_lines = [
        "# Procurement Irregularity Flags",
        "",
        f"**Generated:** {timestamp}",
        "",
        "## Summary",
        "",
        f"- **Total Flags:** {len(irregularities)}",
        "",
        "### By Type",
        "",
    ]

    for irr_type, items in sorted(by_type.items()):
        md_lines.append(f"- **{irr_type}:** {len(items)}")

    md_lines.extend(
        [
            "",
            "### By Severity",
            "",
        ]
    )

    for severity, count in sorted(by_severity.items()):
        md_lines.append(f"- **{severity}:** {count}")

    md_lines.extend(
        [
            "",
            "---",
            "",
            "## Flag Details",
            "",
        ]
    )

    for irr_type, items in sorted(by_type.items()):
        md_lines.append(f"### {irr_type.replace('_', ' ').title()}")
        md_lines.append("")
        for item in items[:10]:
            details = item.get("details", "No details")
            severity = item.get("severity", "unknown")
            md_lines.append(f"- [{severity.upper()}] {details}")
        if len(items) > 10:
            md_lines.append(f"- *...and {len(items) - 10} more*")
        md_lines.append("")

    md_lines.extend(
        [
            "---",
            "",
            "*Generated by Vendor Influence & Contract Flow Map v1.0*",
        ]
    )

    return json_output, "\n".join(md_lines)


def run_vendor_graph_builder(
    vendor_data: dict[str, Any],
    year_range: str,
    output_dir: Path | None = None,
    ace_report_path: Path | None = None,
) -> dict[str, Any]:
    """Run the vendor graph builder pipeline.

    Returns:
        Dictionary with graph and scores
    """
    print(f"Vendor Graph Builder v{VICFM_VERSION}")
    print("=" * 60)

    start_year, end_year = parse_year_range(year_range)
    corpora = filter_corpora_by_years(start_year, end_year)

    vendor_index = vendor_data.get("vendor_index", {})
    relationships = vendor_data.get("relationships", [])
    tech_programs = vendor_data.get("tech_programs", {})
    irregularities = vendor_data.get("irregularities", [])

    print(f"Year Range: {year_range}")
    print(f"Corpora: {len(corpora)}")
    print(f"Vendors: {len(vendor_index)}")
    print(f"Relationships: {len(relationships)}")
    print("=" * 60)

    # Step 1: Build graph
    print("\n[1/4] Building vendor influence graph...")
    graph = build_vendor_graph(vendor_index, relationships, corpora, tech_programs)
    print(f"  - Nodes: {len(graph.nodes)}")
    print(f"  - Edges: {len(graph.edges)}")

    # Step 2: Load ACE anomalies and calculate scores
    print("\n[2/4] Calculating influence scores...")
    ace_anomalies = load_ace_report(ace_report_path)
    print(f"  - ACE anomalies loaded: {len(ace_anomalies)}")
    scores = calculate_influence_scores(
        graph, vendor_index, relationships, ace_anomalies
    )
    print(f"  - Scores calculated for {len(scores)} vendors")

    # Step 3: Generate additional outputs
    print("\n[3/4] Generating ACE integration outputs...")
    vendor_anomaly_links = generate_vendor_anomaly_links(vendor_index, ace_anomalies)
    tech_dependencies = generate_tech_dependencies(tech_programs, ace_anomalies)
    influence_report_md = generate_vendor_influence_report_md(
        scores, vendor_index, irregularities
    )
    procurement_flags_json, procurement_flags_md = generate_procurement_flags(
        irregularities
    )

    # Step 4: Generate primary outputs
    print("\n[4/4] Generating output files...")
    timestamp = get_utc_timestamp()

    graph_output = {
        "version": VICFM_VERSION,
        "generated_at": timestamp,
        "year_range": year_range,
        **graph.to_dict(),
    }

    scores_output = generate_vendor_scores_report(scores)
    csv_rows = generate_influence_network_csv(graph, scores)

    # Write files
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # vendor_graph.json
        graph_path = output_dir / "vendor_graph.json"
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(graph_output, f, indent=2, default=str)
        print(f"  - Wrote {graph_path}")

        # vendor_scores.json
        scores_path = output_dir / "vendor_scores.json"
        with open(scores_path, "w", encoding="utf-8") as f:
            json.dump(scores_output, f, indent=2, default=str)
        print(f"  - Wrote {scores_path}")

        # vendor_influence_network.csv
        csv_path = output_dir / "vendor_influence_network.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
        print(f"  - Wrote {csv_path}")

        # VENDOR_ANOMALY_LINKS.json
        anomaly_links_path = output_dir / "VENDOR_ANOMALY_LINKS.json"
        with open(anomaly_links_path, "w", encoding="utf-8") as f:
            json.dump(vendor_anomaly_links, f, indent=2, default=str)
        print(f"  - Wrote {anomaly_links_path}")

        # VENDOR_TECH_DEPENDENCIES.json
        tech_deps_path = output_dir / "VENDOR_TECH_DEPENDENCIES.json"
        with open(tech_deps_path, "w", encoding="utf-8") as f:
            json.dump(tech_dependencies, f, indent=2, default=str)
        print(f"  - Wrote {tech_deps_path}")

        # VENDOR_INFLUENCE_REPORT.md
        influence_report_path = output_dir / "VENDOR_INFLUENCE_REPORT.md"
        with open(influence_report_path, "w", encoding="utf-8") as f:
            f.write(influence_report_md)
        print(f"  - Wrote {influence_report_path}")

        # PROCUREMENT_FLAGS.json
        procurement_json_path = output_dir / "PROCUREMENT_FLAGS.json"
        with open(procurement_json_path, "w", encoding="utf-8") as f:
            json.dump(procurement_flags_json, f, indent=2, default=str)
        print(f"  - Wrote {procurement_json_path}")

        # PROCUREMENT_FLAGS.md
        procurement_md_path = output_dir / "PROCUREMENT_FLAGS.md"
        with open(procurement_md_path, "w", encoding="utf-8") as f:
            f.write(procurement_flags_md)
        print(f"  - Wrote {procurement_md_path}")

    print("\n" + "=" * 60)
    print("VENDOR GRAPH BUILDING COMPLETE")
    print("=" * 60)

    # Print top vendors
    sorted_scores = sorted(
        scores.values(), key=lambda x: x.get("influence_score", 0), reverse=True
    )
    print("\nTop 5 Vendors by Influence Score:")
    for i, vs in enumerate(sorted_scores[:5], 1):
        print(
            f"  {i}. {vs['vendor']}: {vs['influence_score']:.4f} ({vs.get('tier', 'Unknown')} tier)"
        )

    return {
        "graph": graph_output,
        "scores": scores_output,
        "csv_rows": csv_rows,
        "vendor_anomaly_links": vendor_anomaly_links,
        "tech_dependencies": tech_dependencies,
        "procurement_flags": procurement_flags_json,
    }


def main():
    """Run the vendor graph builder from command line."""
    parser = argparse.ArgumentParser(description="Vendor Influence Graph Builder v1.0")
    parser.add_argument(
        "--vendor-data",
        type=str,
        required=True,
        help="Path to vendor extraction JSON file",
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2014-2025",
        help="Year range to analyze",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Output directory for graph files",
    )
    parser.add_argument(
        "--ace-report",
        type=str,
        default=None,
        help="Path to ACE_REPORT.json for anomaly integration",
    )

    args = parser.parse_args()

    vendor_data_path = Path(args.vendor_data)
    if not vendor_data_path.exists():
        print(f"Error: Vendor data file not found: {vendor_data_path}")
        sys.exit(1)

    vendor_data = load_vendor_extraction(vendor_data_path)
    if not vendor_data:
        print("Error: Failed to load vendor extraction data")
        sys.exit(1)

    ace_report_path = Path(args.ace_report) if args.ace_report else None

    run_vendor_graph_builder(
        vendor_data,
        args.years,
        Path(args.output),
        ace_report_path,
    )


if __name__ == "__main__":
    main()
