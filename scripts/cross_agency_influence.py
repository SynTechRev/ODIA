#!/usr/bin/env python3
"""Cross-Agency Influence v1.0 - CAIM Graph Builder.

This module implements the Cross-Agency Influence Map (CAIM) graph engine that:
- Builds a graph model of agency relationships
- Creates Agency → Contract → Year edges
- Calculates influence weights based on multiple factors
- Integrates with ACE anomalies and VICFM vendor data
- [MSH-v1] Supports meaning-coherence scoring via semantic harmonization

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
CAIM_VERSION = "1.0"

# Influence edge weights for CAIM
WEIGHT_VENDOR_OVERLAP = 0.25
WEIGHT_TECH_STACK = 0.20
WEIGHT_CONTRACT_FLOW_SYNC = 0.20
WEIGHT_ACE_ANOMALY_LINKAGE = 0.20
WEIGHT_PROGRAMMATIC_CONTINUITY = 0.15


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


class AgencyGraph:
    """Graph model for cross-agency relationships."""

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
            node_type: Type of node (agency, vendor, year, corpus, program)
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
        weight: float = 1.0,
        **attributes: Any,
    ) -> dict[str, Any]:
        """Add an edge to the graph.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Type of relationship
            weight: Edge weight (default 1.0)
            **attributes: Additional edge attributes

        Returns:
            The created edge
        """
        edge = {
            "source": source,
            "target": target,
            "type": edge_type,
            "weight": weight,
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

    def get_edge_weight_sum(self, node_id: str) -> float:
        """Get sum of edge weights for a node.

        Returns:
            Sum of edge weights
        """
        total = 0.0
        for edge in self.edges:
            if edge["source"] == node_id or edge["target"] == node_id:
                total += edge.get("weight", 1.0)
        return total

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


def calculate_vendor_overlap(
    agency_a: str,
    agency_b: str,
    agency_vendor_map: dict[str, set[str]],
) -> float:
    """Calculate vendor overlap between two agencies.

    Returns:
        Jaccard similarity of shared vendors (0-1)
    """
    vendors_a = agency_vendor_map.get(agency_a, set())
    vendors_b = agency_vendor_map.get(agency_b, set())

    if not vendors_a or not vendors_b:
        return 0.0

    intersection = len(vendors_a & vendors_b)
    union = len(vendors_a | vendors_b)

    return intersection / union if union > 0 else 0.0


def calculate_tech_stack_similarity(
    agency_a: str,
    agency_b: str,
    agency_tech_map: dict[str, set[str]],
) -> float:
    """Calculate technology stack similarity between two agencies.

    Returns:
        Jaccard similarity of shared tech programs (0-1)
    """
    tech_a = agency_tech_map.get(agency_a, set())
    tech_b = agency_tech_map.get(agency_b, set())

    if not tech_a or not tech_b:
        return 0.0

    intersection = len(tech_a & tech_b)
    union = len(tech_a | tech_b)

    return intersection / union if union > 0 else 0.0


def calculate_contract_flow_sync(
    agency_a: str,
    agency_b: str,
    agency_years_map: dict[str, set[str]],
) -> float:
    """Calculate contract flow synchronization between agencies.

    Measures how often agencies appear in the same years.

    Returns:
        Year overlap ratio (0-1)
    """
    years_a = agency_years_map.get(agency_a, set())
    years_b = agency_years_map.get(agency_b, set())

    if not years_a or not years_b:
        return 0.0

    intersection = len(years_a & years_b)
    union = len(years_a | years_b)

    return intersection / union if union > 0 else 0.0


def calculate_ace_anomaly_linkage(
    agency_a: str,
    agency_b: str,
    agency_anomaly_map: dict[str, set[str]],
) -> float:
    """Calculate ACE anomaly linkage between agencies.

    Measures shared anomaly patterns.

    Returns:
        Anomaly overlap ratio (0-1)
    """
    anomalies_a = agency_anomaly_map.get(agency_a, set())
    anomalies_b = agency_anomaly_map.get(agency_b, set())

    if not anomalies_a or not anomalies_b:
        return 0.0

    intersection = len(anomalies_a & anomalies_b)
    union = len(anomalies_a | anomalies_b)

    return intersection / union if union > 0 else 0.0


def calculate_programmatic_continuity(
    agency_a: str,
    agency_b: str,
    agency_hist_map: dict[str, set[str]],
) -> float:
    """Calculate programmatic continuity between agencies.

    Measures shared corpus appearances.

    Returns:
        Corpus overlap ratio (0-1)
    """
    hist_a = agency_hist_map.get(agency_a, set())
    hist_b = agency_hist_map.get(agency_b, set())

    if not hist_a or not hist_b:
        return 0.0

    intersection = len(hist_a & hist_b)
    union = len(hist_a | hist_b)

    return intersection / union if union > 0 else 0.0


def calculate_influence_score(
    vendor_overlap: float,
    tech_stack: float,
    contract_flow_sync: float,
    ace_anomaly_linkage: float,
    programmatic_continuity: float,
) -> float:
    """Calculate weighted influence score between agencies.

    Score = (VendorOverlap * 0.25)
          + (TechStack * 0.20)
          + (ContractFlowSync * 0.20)
          + (ACE_Anomaly_Linkage * 0.20)
          + (ProgrammaticContinuity * 0.15)

    Returns:
        Influence score (0-1)
    """
    return (
        (vendor_overlap * WEIGHT_VENDOR_OVERLAP)
        + (tech_stack * WEIGHT_TECH_STACK)
        + (contract_flow_sync * WEIGHT_CONTRACT_FLOW_SYNC)
        + (ace_anomaly_linkage * WEIGHT_ACE_ANOMALY_LINKAGE)
        + (programmatic_continuity * WEIGHT_PROGRAMMATIC_CONTINUITY)
    )


def build_agency_graph(
    agency_index: dict[str, Any],
    relationships: list[dict[str, Any]],
    corpora: dict[str, str],
    vendor_data: dict[str, Any] | None = None,
    ace_report: dict[str, Any] | None = None,
) -> AgencyGraph:
    """Build a cross-agency influence graph.

    Creates nodes for:
    - Agencies
    - Vendors (if vendor_data provided)
    - Years
    - Corpus items

    Creates edges for:
    - Agency → Agency (co-occurrence)
    - Agency → Vendor (shared vendors)
    - Agency → Corpus (appearances)
    - Agency → Year (activity)

    Returns:
        AgencyGraph instance
    """
    graph = AgencyGraph()

    # Build agency-vendor map from vendor data
    agency_vendor_map: dict[str, set[str]] = defaultdict(set)
    agency_tech_map: dict[str, set[str]] = defaultdict(set)
    agency_hist_map: dict[str, set[str]] = defaultdict(set)
    agency_years_map: dict[str, set[str]] = defaultdict(set)
    agency_anomaly_map: dict[str, set[str]] = defaultdict(set)

    # Process vendor data if available
    if vendor_data:
        vendor_index = vendor_data.get("vendor_index", {})
        for vendor_name, vendor_info in vendor_index.items():
            hist_ids = vendor_info.get("hist_ids", [])
            for hist_id in hist_ids:
                # Find agencies that appear in same corpus as vendor
                for agency_name, agency_info in agency_index.items():
                    if hist_id in agency_info.get("hist_ids", []):
                        agency_vendor_map[agency_name].add(vendor_name)

        # Process tech programs
        tech_programs = vendor_data.get("tech_programs", {})
        for prog_name, prog_info in tech_programs.items():
            hist_ids = prog_info.get("hist_ids", [])
            for hist_id in hist_ids:
                for agency_name, agency_info in agency_index.items():
                    if hist_id in agency_info.get("hist_ids", []):
                        agency_tech_map[agency_name].add(prog_name)

    # Build agency maps from agency_index
    for agency_name, agency_info in agency_index.items():
        hist_ids = set(agency_info.get("hist_ids", []))
        years = set(agency_info.get("years", []))
        agency_hist_map[agency_name] = hist_ids
        agency_years_map[agency_name] = years

    # Process ACE anomalies if available
    if ace_report:
        by_hist_id = ace_report.get("by_hist_id", {})
        for hist_id, anomalies in by_hist_id.items():
            for anomaly in anomalies:
                anomaly_type = anomaly.get("type", "unknown")
                for agency_name, agency_info in agency_index.items():
                    if hist_id in agency_info.get("hist_ids", []):
                        agency_anomaly_map[agency_name].add(f"{hist_id}:{anomaly_type}")

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

    # Create agency nodes
    for agency_name, agency_info in agency_index.items():
        agency_type = agency_info.get("type", "unknown")
        graph.add_node(
            f"agency:{agency_name}",
            "agency",
            name=agency_name,
            agency_type=agency_type,
            appearance_count=agency_info.get("appearance_count", 0),
            year_span=agency_info.get("year_span", 0),
            years=agency_info.get("years", []),
        )

        # Link agency to corpora where they appear
        for hist_id in agency_info.get("hist_ids", []):
            if hist_id in corpora:
                graph.add_edge(
                    f"agency:{agency_name}",
                    f"corpus:{hist_id}",
                    "mentioned_in",
                )

        # Link agency to years
        for year in agency_info.get("years", []):
            graph.add_edge(
                f"agency:{agency_name}",
                f"year:{year}",
                "active_in",
            )

    # Create vendor nodes and agency-vendor edges if vendor data available
    if vendor_data:
        vendor_index = vendor_data.get("vendor_index", {})
        for vendor_name, vendor_info in vendor_index.items():
            graph.add_node(
                f"vendor:{vendor_name}",
                "vendor",
                name=vendor_name,
                appearance_count=vendor_info.get("appearance_count", 0),
            )

        # Add agency-vendor edges
        for agency_name, vendors in agency_vendor_map.items():
            for vendor_name in vendors:
                graph.add_edge(
                    f"agency:{agency_name}",
                    f"vendor:{vendor_name}",
                    "shares_vendor",
                )

    # Create agency-agency edges based on relationships
    for rel in relationships:
        agency_a = rel.get("agency_a")
        agency_b = rel.get("agency_b")

        if agency_a and agency_b:
            # Calculate weighted influence score
            vendor_overlap = calculate_vendor_overlap(
                agency_a, agency_b, agency_vendor_map
            )
            tech_stack = calculate_tech_stack_similarity(
                agency_a, agency_b, agency_tech_map
            )
            contract_flow = calculate_contract_flow_sync(
                agency_a, agency_b, agency_years_map
            )
            anomaly_link = calculate_ace_anomaly_linkage(
                agency_a, agency_b, agency_anomaly_map
            )
            prog_continuity = calculate_programmatic_continuity(
                agency_a, agency_b, agency_hist_map
            )

            influence_score = calculate_influence_score(
                vendor_overlap, tech_stack, contract_flow, anomaly_link, prog_continuity
            )

            graph.add_edge(
                f"agency:{agency_a}",
                f"agency:{agency_b}",
                "interacts_with",
                weight=influence_score,
                vendor_overlap=vendor_overlap,
                tech_stack=tech_stack,
                contract_flow_sync=contract_flow,
                ace_anomaly_linkage=anomaly_link,
                programmatic_continuity=prog_continuity,
                co_occurrence_count=rel.get("co_occurrence_count", 0),
            )

    return graph


def generate_cross_agency_edges_csv(graph: AgencyGraph) -> list[list[str]]:
    """Generate cross_agency_edges.csv data.

    Returns:
        List of CSV rows
    """
    headers = [
        "source",
        "target",
        "edge_type",
        "weight",
        "vendor_overlap",
        "tech_stack",
        "contract_flow_sync",
        "ace_anomaly_linkage",
        "programmatic_continuity",
        "co_occurrence_count",
    ]

    rows = [headers]

    for edge in graph.edges:
        if edge.get("type") == "interacts_with":
            rows.append(
                [
                    str(edge.get("source", "")),
                    str(edge.get("target", "")),
                    str(edge.get("type", "")),
                    str(round(edge.get("weight", 0), 4)),
                    str(round(edge.get("vendor_overlap", 0), 4)),
                    str(round(edge.get("tech_stack", 0), 4)),
                    str(round(edge.get("contract_flow_sync", 0), 4)),
                    str(round(edge.get("ace_anomaly_linkage", 0), 4)),
                    str(round(edge.get("programmatic_continuity", 0), 4)),
                    str(edge.get("co_occurrence_count", 0)),
                ]
            )

    return rows


def load_agency_extraction(extraction_path: Path) -> dict[str, Any]:
    """Load agency extraction results.

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


def load_vendor_data(vendor_path: Path | None) -> dict[str, Any]:
    """Load vendor extraction data.

    Returns:
        Vendor data dictionary
    """
    if vendor_path and vendor_path.exists():
        try:
            with open(vendor_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_ace_report(ace_path: Path | None) -> dict[str, Any]:
    """Load ACE report.

    Returns:
        ACE report dictionary
    """
    if ace_path is None:
        ace_path = Path("ACE_REPORT.json")

    if ace_path.exists():
        try:
            with open(ace_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def run_cross_agency_influence(
    agency_data: dict[str, Any],
    year_range: str,
    output_dir: Path | None = None,
    vendor_data: dict[str, Any] | None = None,
    ace_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the cross-agency influence pipeline.

    Returns:
        Dictionary with graph and analysis results
    """
    print(f"Cross-Agency Influence v{CAIM_VERSION}")
    print("=" * 60)

    start_year, end_year = parse_year_range(year_range)
    corpora = filter_corpora_by_years(start_year, end_year)

    agency_index = agency_data.get("agency_index", {})
    relationships = agency_data.get("relationships", [])

    print(f"Year Range: {year_range}")
    print(f"Corpora: {len(corpora)}")
    print(f"Agencies: {len(agency_index)}")
    print(f"Relationships: {len(relationships)}")
    print("=" * 60)

    # Build graph
    print("\n[1/2] Building cross-agency influence graph...")
    graph = build_agency_graph(
        agency_index, relationships, corpora, vendor_data, ace_report
    )
    print(f"  - Nodes: {len(graph.nodes)}")
    print(f"  - Edges: {len(graph.edges)}")

    # Generate outputs
    print("\n[2/2] Generating output files...")
    timestamp = get_utc_timestamp()

    graph_output = {
        "version": CAIM_VERSION,
        "generated_at": timestamp,
        "year_range": year_range,
        **graph.to_dict(),
    }

    csv_rows = generate_cross_agency_edges_csv(graph)

    # Write files
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # agency_graph.json
        graph_path = output_dir / "agency_graph.json"
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(graph_output, f, indent=2, default=str)
        print(f"  - Wrote {graph_path}")

        # cross_agency_edges.csv
        csv_path = output_dir / "cross_agency_edges.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
        print(f"  - Wrote {csv_path}")

    print("\n" + "=" * 60)
    print("CROSS-AGENCY INFLUENCE COMPLETE")
    print("=" * 60)

    # Print top agency pairs by influence
    agency_edges = [e for e in graph.edges if e.get("type") == "interacts_with"]
    sorted_edges = sorted(agency_edges, key=lambda x: x.get("weight", 0), reverse=True)

    print("\nTop 5 Agency Pairs by Influence Score:")
    for i, edge in enumerate(sorted_edges[:5], 1):
        source = edge.get("source", "").replace("agency:", "")
        target = edge.get("target", "").replace("agency:", "")
        weight = edge.get("weight", 0)
        print(f"  {i}. {source} ↔ {target}: {weight:.4f}")

    return {
        "graph": graph_output,
        "csv_rows": csv_rows,
    }


def main():
    """Run cross-agency influence from command line."""
    parser = argparse.ArgumentParser(
        description="Cross-Agency Influence v1.0 - Build CAIM Graph"
    )
    parser.add_argument(
        "--agency-data",
        type=str,
        required=True,
        help="Path to agency extraction JSON file",
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
        "--vendor-data",
        type=str,
        default=None,
        help="Path to vendor extraction JSON file",
    )
    parser.add_argument(
        "--ace-report",
        type=str,
        default=None,
        help="Path to ACE_REPORT.json",
    )

    args = parser.parse_args()

    agency_data_path = Path(args.agency_data)
    if not agency_data_path.exists():
        print(f"Error: Agency data file not found: {agency_data_path}")
        sys.exit(1)

    agency_data = load_agency_extraction(agency_data_path)
    if not agency_data:
        print("Error: Failed to load agency extraction data")
        sys.exit(1)

    vendor_data = None
    if args.vendor_data:
        vendor_data = load_vendor_data(Path(args.vendor_data))

    ace_report = None
    if args.ace_report:
        ace_report = load_ace_report(Path(args.ace_report))

    run_cross_agency_influence(
        agency_data,
        args.years,
        Path(args.output),
        vendor_data,
        ace_report,
    )


if __name__ == "__main__":
    main()
