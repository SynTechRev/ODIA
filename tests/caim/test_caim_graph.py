#!/usr/bin/env python3
"""Tests for CAIM graph building functionality.

This module tests the cross_agency_influence.py functions.
Total: 31 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.cross_agency_influence import (
    WEIGHT_ACE_ANOMALY_LINKAGE,
    WEIGHT_CONTRACT_FLOW_SYNC,
    WEIGHT_PROGRAMMATIC_CONTINUITY,
    WEIGHT_TECH_STACK,
    WEIGHT_VENDOR_OVERLAP,
    AgencyGraph,
    build_agency_graph,
    calculate_ace_anomaly_linkage,
    calculate_contract_flow_sync,
    calculate_influence_score,
    calculate_programmatic_continuity,
    calculate_tech_stack_similarity,
    calculate_vendor_overlap,
    generate_cross_agency_edges_csv,
)


class TestAgencyGraph:
    """Tests for AgencyGraph class."""

    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = AgencyGraph()
        node = graph.add_node("agency:City Council", "agency", name="City Council")

        assert "agency:City Council" in graph.nodes
        assert node["type"] == "agency"
        assert node["name"] == "City Council"

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = AgencyGraph()
        graph.add_node("agency:A", "agency")
        graph.add_node("agency:B", "agency")
        edge = graph.add_edge("agency:A", "agency:B", "interacts_with", weight=0.5)

        assert len(graph.edges) == 1
        assert edge["source"] == "agency:A"
        assert edge["target"] == "agency:B"
        assert edge["weight"] == 0.5

    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        graph = AgencyGraph()
        graph.add_node("agency:A", "agency")
        graph.add_node("agency:B", "agency")
        graph.add_node("agency:C", "agency")
        graph.add_edge("agency:A", "agency:B", "interacts_with")
        graph.add_edge("agency:A", "agency:C", "interacts_with")

        neighbors = graph.get_neighbors("agency:A")
        assert "agency:B" in neighbors
        assert "agency:C" in neighbors
        assert len(neighbors) == 2

    def test_get_degree(self):
        """Test getting degree of a node."""
        graph = AgencyGraph()
        graph.add_node("agency:A", "agency")
        graph.add_node("agency:B", "agency")
        graph.add_node("agency:C", "agency")
        graph.add_edge("agency:A", "agency:B", "interacts_with")
        graph.add_edge("agency:A", "agency:C", "interacts_with")

        assert graph.get_degree("agency:A") == 2
        assert graph.get_degree("agency:B") == 1

    def test_get_edge_weight_sum(self):
        """Test sum of edge weights for a node."""
        graph = AgencyGraph()
        graph.add_node("agency:A", "agency")
        graph.add_node("agency:B", "agency")
        graph.add_node("agency:C", "agency")
        graph.add_edge("agency:A", "agency:B", "interacts_with", weight=0.5)
        graph.add_edge("agency:A", "agency:C", "interacts_with", weight=0.3)

        weight_sum = graph.get_edge_weight_sum("agency:A")
        assert weight_sum == 0.8

    def test_to_dict(self):
        """Test graph serialization to dictionary."""
        graph = AgencyGraph()
        graph.add_node("agency:A", "agency")
        graph.add_node("agency:B", "agency")
        graph.add_edge("agency:A", "agency:B", "interacts_with")

        result = graph.to_dict()
        assert "nodes" in result
        assert "edges" in result
        assert "statistics" in result
        assert result["statistics"]["total_nodes"] == 2
        assert result["statistics"]["total_edges"] == 1


class TestBuildAgencyGraph:
    """Tests for build_agency_graph function."""

    def test_build_empty_graph(self):
        """Test building graph with empty inputs."""
        graph = build_agency_graph({}, [], {})
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_build_with_agencies(self):
        """Test building graph with agencies."""
        agency_index = {
            "City Council": {
                "name": "City Council",
                "type": "municipal",
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
                "appearance_count": 1,
                "year_span": 1,
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        graph = build_agency_graph(agency_index, [], corpora)

        assert "agency:City Council" in graph.nodes
        assert graph.nodes["agency:City Council"]["type"] == "agency"

    def test_build_with_relationships(self):
        """Test building graph with agency relationships."""
        agency_index = {
            "City Council": {
                "name": "City Council",
                "type": "municipal",
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
                "appearance_count": 1,
                "year_span": 1,
            },
            "Police Department": {
                "name": "Police Department",
                "type": "municipal",
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
                "appearance_count": 1,
                "year_span": 1,
            },
        }
        relationships = [
            {
                "agency_a": "City Council",
                "agency_b": "Police Department",
                "co_occurrence_count": 1,
            }
        ]
        corpora = {"HIST-1234": "2020-01-15"}

        graph = build_agency_graph(agency_index, relationships, corpora)

        # Should have agency-agency edge
        interacts_edges = [e for e in graph.edges if e["type"] == "interacts_with"]
        assert len(interacts_edges) == 1


class TestCalculateVendorOverlap:
    """Tests for calculate_vendor_overlap function."""

    def test_full_overlap(self):
        """Test full vendor overlap."""
        vendor_map = {
            "Agency A": {"Vendor1", "Vendor2"},
            "Agency B": {"Vendor1", "Vendor2"},
        }
        result = calculate_vendor_overlap("Agency A", "Agency B", vendor_map)
        assert result == 1.0

    def test_no_overlap(self):
        """Test no vendor overlap."""
        vendor_map = {
            "Agency A": {"Vendor1"},
            "Agency B": {"Vendor2"},
        }
        result = calculate_vendor_overlap("Agency A", "Agency B", vendor_map)
        assert result == 0.0

    def test_partial_overlap(self):
        """Test partial vendor overlap."""
        vendor_map = {
            "Agency A": {"Vendor1", "Vendor2"},
            "Agency B": {"Vendor2", "Vendor3"},
        }
        # Jaccard: 1 / 3 = 0.333...
        result = calculate_vendor_overlap("Agency A", "Agency B", vendor_map)
        assert 0.3 <= result <= 0.4

    def test_empty_vendors(self):
        """Test empty vendor sets."""
        vendor_map = {
            "Agency A": set(),
            "Agency B": {"Vendor1"},
        }
        result = calculate_vendor_overlap("Agency A", "Agency B", vendor_map)
        assert result == 0.0


class TestCalculateTechStackSimilarity:
    """Tests for calculate_tech_stack_similarity function."""

    def test_full_similarity(self):
        """Test full tech stack similarity."""
        tech_map = {
            "Agency A": {"ALPR", "BWC"},
            "Agency B": {"ALPR", "BWC"},
        }
        result = calculate_tech_stack_similarity("Agency A", "Agency B", tech_map)
        assert result == 1.0

    def test_no_similarity(self):
        """Test no tech stack similarity."""
        tech_map = {
            "Agency A": {"ALPR"},
            "Agency B": {"BWC"},
        }
        result = calculate_tech_stack_similarity("Agency A", "Agency B", tech_map)
        assert result == 0.0


class TestCalculateContractFlowSync:
    """Tests for calculate_contract_flow_sync function."""

    def test_full_sync(self):
        """Test full year synchronization."""
        years_map = {
            "Agency A": {"2020", "2021"},
            "Agency B": {"2020", "2021"},
        }
        result = calculate_contract_flow_sync("Agency A", "Agency B", years_map)
        assert result == 1.0

    def test_no_sync(self):
        """Test no year synchronization."""
        years_map = {
            "Agency A": {"2020"},
            "Agency B": {"2021"},
        }
        result = calculate_contract_flow_sync("Agency A", "Agency B", years_map)
        assert result == 0.0


class TestCalculateAceAnomalyLinkage:
    """Tests for calculate_ace_anomaly_linkage function."""

    def test_shared_anomalies(self):
        """Test shared anomaly patterns."""
        anomaly_map = {
            "Agency A": {"HIST-1234:structural_gap"},
            "Agency B": {"HIST-1234:structural_gap"},
        }
        result = calculate_ace_anomaly_linkage("Agency A", "Agency B", anomaly_map)
        assert result == 1.0

    def test_no_shared_anomalies(self):
        """Test no shared anomaly patterns."""
        anomaly_map = {
            "Agency A": {"HIST-1234:structural_gap"},
            "Agency B": {"HIST-5678:extraction_issue"},
        }
        result = calculate_ace_anomaly_linkage("Agency A", "Agency B", anomaly_map)
        assert result == 0.0


class TestCalculateProgrammaticContinuity:
    """Tests for calculate_programmatic_continuity function."""

    def test_full_continuity(self):
        """Test full corpus co-occurrence."""
        hist_map = {
            "Agency A": {"HIST-1234", "HIST-5678"},
            "Agency B": {"HIST-1234", "HIST-5678"},
        }
        result = calculate_programmatic_continuity("Agency A", "Agency B", hist_map)
        assert result == 1.0


class TestCalculateInfluenceScore:
    """Tests for calculate_influence_score function."""

    def test_all_zeros(self):
        """Test influence score with all zero components."""
        result = calculate_influence_score(0.0, 0.0, 0.0, 0.0, 0.0)
        assert result == 0.0

    def test_all_ones(self):
        """Test influence score with all one components."""
        result = calculate_influence_score(1.0, 1.0, 1.0, 1.0, 1.0)
        assert result == 1.0

    def test_weighted_calculation(self):
        """Test weighted influence calculation."""
        # Only vendor overlap = 1.0, rest = 0.0
        result = calculate_influence_score(1.0, 0.0, 0.0, 0.0, 0.0)
        assert result == WEIGHT_VENDOR_OVERLAP


class TestInfluenceWeights:
    """Tests for influence weight constants."""

    def test_weights_sum_to_one(self):
        """Test that all weights sum to 1.0."""
        total = (
            WEIGHT_VENDOR_OVERLAP
            + WEIGHT_TECH_STACK
            + WEIGHT_CONTRACT_FLOW_SYNC
            + WEIGHT_ACE_ANOMALY_LINKAGE
            + WEIGHT_PROGRAMMATIC_CONTINUITY
        )
        assert total == 1.0

    def test_vendor_overlap_weight(self):
        """Test vendor overlap weight value."""
        assert WEIGHT_VENDOR_OVERLAP == 0.25

    def test_tech_stack_weight(self):
        """Test tech stack weight value."""
        assert WEIGHT_TECH_STACK == 0.20

    def test_contract_flow_weight(self):
        """Test contract flow sync weight value."""
        assert WEIGHT_CONTRACT_FLOW_SYNC == 0.20

    def test_ace_anomaly_weight(self):
        """Test ACE anomaly linkage weight value."""
        assert WEIGHT_ACE_ANOMALY_LINKAGE == 0.20

    def test_programmatic_continuity_weight(self):
        """Test programmatic continuity weight value."""
        assert WEIGHT_PROGRAMMATIC_CONTINUITY == 0.15


class TestGenerateCrossAgencyEdgesCsv:
    """Tests for generate_cross_agency_edges_csv function."""

    def test_csv_has_headers(self):
        """Test CSV output includes headers."""
        graph = AgencyGraph()
        rows = generate_cross_agency_edges_csv(graph)
        assert len(rows) >= 1
        assert rows[0][0] == "source"

    def test_csv_includes_interacts_edges(self):
        """Test CSV includes interacts_with edges."""
        graph = AgencyGraph()
        graph.add_node("agency:A", "agency")
        graph.add_node("agency:B", "agency")
        graph.add_edge(
            "agency:A",
            "agency:B",
            "interacts_with",
            weight=0.5,
            vendor_overlap=0.2,
            tech_stack=0.1,
            contract_flow_sync=0.1,
            ace_anomaly_linkage=0.05,
            programmatic_continuity=0.05,
            co_occurrence_count=3,
        )

        rows = generate_cross_agency_edges_csv(graph)
        assert len(rows) == 2  # Header + 1 edge
        assert rows[1][0] == "agency:A"
        assert rows[1][1] == "agency:B"
