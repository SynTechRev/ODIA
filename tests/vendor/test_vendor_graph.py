#!/usr/bin/env python3
"""Tests for vendor graph building functionality.

This module tests the vendor_graph_builder.py functions.
Total: 20 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.vendor_graph_builder import (
    WEIGHT_ANOMALY,
    WEIGHT_CENTRALITY,
    WEIGHT_CONTINUITY,
    WEIGHT_FREQUENCY,
    WEIGHT_VALUE,
    VendorGraph,
    build_vendor_graph,
    calculate_influence_scores,
    determine_dependency_tier,
    generate_influence_network_csv,
    generate_vendor_scores_report,
)


class TestVendorGraph:
    """Tests for VendorGraph class."""

    def test_add_node(self):
        """Test adding a node to graph."""
        graph = VendorGraph()
        node = graph.add_node("test_node", "vendor", name="Test")
        assert node["id"] == "test_node"
        assert node["type"] == "vendor"
        assert "test_node" in graph.nodes

    def test_add_edge(self):
        """Test adding an edge to graph."""
        graph = VendorGraph()
        graph.add_node("node1", "vendor")
        graph.add_node("node2", "corpus")
        edge = graph.add_edge("node1", "node2", "mentioned_in")
        assert edge["source"] == "node1"
        assert edge["target"] == "node2"
        assert edge["type"] == "mentioned_in"

    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        graph = VendorGraph()
        graph.add_node("node1", "vendor")
        graph.add_node("node2", "corpus")
        graph.add_node("node3", "corpus")
        graph.add_edge("node1", "node2", "test")
        graph.add_edge("node1", "node3", "test")

        neighbors = graph.get_neighbors("node1")
        assert "node2" in neighbors
        assert "node3" in neighbors
        assert len(neighbors) == 2

    def test_get_degree(self):
        """Test getting degree of a node."""
        graph = VendorGraph()
        graph.add_node("node1", "vendor")
        graph.add_node("node2", "corpus")
        graph.add_node("node3", "corpus")
        graph.add_edge("node1", "node2", "test")
        graph.add_edge("node1", "node3", "test")

        assert graph.get_degree("node1") == 2
        assert graph.get_degree("node2") == 1

    def test_to_dict(self):
        """Test converting graph to dictionary."""
        graph = VendorGraph()
        graph.add_node("node1", "vendor")
        graph.add_node("node2", "corpus")
        graph.add_edge("node1", "node2", "test")

        result = graph.to_dict()
        assert "nodes" in result
        assert "edges" in result
        assert "statistics" in result
        assert result["statistics"]["total_nodes"] == 2
        assert result["statistics"]["total_edges"] == 1


class TestBuildVendorGraph:
    """Tests for build_vendor_graph function."""

    def test_build_empty_graph(self):
        """Test building graph with empty data."""
        graph = build_vendor_graph({}, [], {})
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_build_with_vendors(self):
        """Test building graph with vendor data."""
        vendor_index = {
            "Axon": {
                "name": "Axon",
                "appearance_count": 3,
                "year_span": 2,
                "years": ["2020", "2021"],
                "hist_ids": ["HIST-1234"],
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        graph = build_vendor_graph(vendor_index, [], corpora)

        assert "vendor:Axon" in graph.nodes
        assert "corpus:HIST-1234" in graph.nodes
        assert "year:2020" in graph.nodes

    def test_build_with_relationships(self):
        """Test building graph with relationship data."""
        vendor_index = {
            "Axon": {
                "name": "Axon",
                "appearance_count": 1,
                "year_span": 1,
                "years": ["2020"],
                "hist_ids": ["HIST-1234"],
            }
        }
        relationships = [
            {"vendor": "Axon", "hist_id": "HIST-1234", "total_amount": 50000}
        ]
        corpora = {"HIST-1234": "2020-01-15"}

        graph = build_vendor_graph(vendor_index, relationships, corpora)

        # Check for contract_with edge
        contract_edges = [e for e in graph.edges if e.get("type") == "contract_with"]
        assert len(contract_edges) >= 1


class TestCalculateInfluenceScores:
    """Tests for calculate_influence_scores function."""

    def test_scores_for_single_vendor(self):
        """Test score calculation for single vendor."""
        graph = VendorGraph()
        graph.add_node("vendor:Axon", "vendor")

        vendor_index = {
            "Axon": {
                "appearance_count": 5,
                "year_span": 3,
                "years": ["2020", "2021", "2022"],
                "hist_ids": ["HIST-1234"],
            }
        }

        relationships = [{"vendor": "Axon", "total_amount": 100000}]

        scores = calculate_influence_scores(graph, vendor_index, relationships)

        assert "Axon" in scores
        assert "influence_score" in scores["Axon"]
        assert 0 <= scores["Axon"]["influence_score"] <= 1

    def test_scores_include_components(self):
        """Test that scores include component breakdown."""
        graph = VendorGraph()
        graph.add_node("vendor:Axon", "vendor")

        vendor_index = {
            "Axon": {
                "appearance_count": 1,
                "year_span": 1,
                "years": ["2020"],
                "hist_ids": [],
            }
        }

        scores = calculate_influence_scores(graph, vendor_index, [])

        components = scores["Axon"]["components"]
        assert "frequency" in components
        assert "value" in components
        assert "anomaly_intersection" in components
        assert "centrality" in components
        assert "continuity" in components

    def test_scores_with_ace_anomalies(self):
        """Test score calculation with ACE anomalies."""
        graph = VendorGraph()
        graph.add_node("vendor:Axon", "vendor")

        vendor_index = {
            "Axon": {
                "appearance_count": 1,
                "year_span": 1,
                "years": ["2020"],
                "hist_ids": ["HIST-1234"],
            }
        }

        ace_anomalies = [
            {"hist_id": "HIST-1234", "type": "structural_gap"},
            {"hist_id": "HIST-1234", "type": "schema_irregularity"},
        ]

        scores = calculate_influence_scores(graph, vendor_index, [], ace_anomalies)

        # Anomaly intersection should be > 0
        assert scores["Axon"]["components"]["anomaly_intersection"] > 0


class TestDetermineDependencyTier:
    """Tests for determine_dependency_tier function."""

    def test_critical_tier(self):
        """Test critical tier determination."""
        assert determine_dependency_tier(0.9) == "Critical"
        assert determine_dependency_tier(0.8) == "Critical"

    def test_high_tier(self):
        """Test high tier determination."""
        assert determine_dependency_tier(0.7) == "High"
        assert determine_dependency_tier(0.6) == "High"

    def test_moderate_tier(self):
        """Test moderate tier determination."""
        assert determine_dependency_tier(0.5) == "Moderate"
        assert determine_dependency_tier(0.4) == "Moderate"

    def test_low_tier(self):
        """Test low tier determination."""
        assert determine_dependency_tier(0.3) == "Low"
        assert determine_dependency_tier(0.1) == "Low"
        assert determine_dependency_tier(0.0) == "Low"


class TestGenerateVendorScoresReport:
    """Tests for generate_vendor_scores_report function."""

    def test_report_structure(self):
        """Test report has required structure."""
        scores = {
            "Axon": {"vendor": "Axon", "influence_score": 0.75},
            "Flock": {"vendor": "Flock", "influence_score": 0.5},
        }

        report = generate_vendor_scores_report(scores)

        assert "version" in report
        assert "generated_at" in report
        assert "summary" in report
        assert "vendors" in report
        assert "scoring_weights" in report

    def test_vendors_are_ranked(self):
        """Test vendors are ranked by score."""
        scores = {
            "Axon": {"vendor": "Axon", "influence_score": 0.75},
            "Flock": {"vendor": "Flock", "influence_score": 0.5},
        }

        report = generate_vendor_scores_report(scores)

        # First vendor should have higher score
        assert (
            report["vendors"][0]["influence_score"]
            >= report["vendors"][1]["influence_score"]
        )

    def test_tiers_are_assigned(self):
        """Test dependency tiers are assigned."""
        scores = {
            "Axon": {"vendor": "Axon", "influence_score": 0.85},
        }

        report = generate_vendor_scores_report(scores)

        assert report["vendors"][0]["tier"] == "Critical"


class TestGenerateInfluenceNetworkCsv:
    """Tests for generate_influence_network_csv function."""

    def test_csv_has_headers(self):
        """Test CSV output has headers."""
        graph = VendorGraph()
        graph.add_node("vendor:Axon", "vendor")
        graph.add_node("corpus:HIST-1234", "corpus")
        graph.add_edge("vendor:Axon", "corpus:HIST-1234", "mentioned_in")

        rows = generate_influence_network_csv(graph, {})

        assert len(rows) >= 1
        headers = rows[0]
        assert "source" in headers
        assert "target" in headers
        assert "edge_type" in headers

    def test_csv_includes_edges(self):
        """Test CSV includes all edges."""
        graph = VendorGraph()
        graph.add_node("vendor:Axon", "vendor")
        graph.add_node("corpus:HIST-1234", "corpus")
        graph.add_edge("vendor:Axon", "corpus:HIST-1234", "mentioned_in")

        rows = generate_influence_network_csv(graph, {})

        # Should have header + 1 edge
        assert len(rows) == 2


class TestInfluenceWeights:
    """Tests for influence score weights."""

    def test_weights_sum_to_one(self):
        """Test that scoring weights sum to 1.0."""
        total = (
            WEIGHT_FREQUENCY
            + WEIGHT_VALUE
            + WEIGHT_ANOMALY
            + WEIGHT_CENTRALITY
            + WEIGHT_CONTINUITY
        )
        assert abs(total - 1.0) < 0.001

    def test_frequency_weight(self):
        """Test frequency weight value."""
        assert WEIGHT_FREQUENCY == 0.25

    def test_value_weight(self):
        """Test value weight."""
        assert WEIGHT_VALUE == 0.25

    def test_anomaly_weight(self):
        """Test anomaly weight."""
        assert WEIGHT_ANOMALY == 0.20
