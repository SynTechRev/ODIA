#!/usr/bin/env python3
"""Tests for CAIM-ACE integration functionality.

This module tests integration between CAIM and ACE.
Total: 11 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.cross_agency_influence import (
    build_agency_graph,
    calculate_ace_anomaly_linkage,
)
from scripts.interdepartmental_matrix import (
    build_agency_maps,
    calculate_icm_score,
)


class TestAceIntegrationMaps:
    """Tests for ACE anomaly integration in agency maps."""

    def test_anomaly_map_from_ace_report(self):
        """Test building anomaly map from ACE report."""
        agency_index = {
            "City Council": {
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
            }
        }
        ace_report = {
            "by_hist_id": {
                "HIST-1234": [
                    {"type": "structural_gap", "subtype": "missing_minutes"},
                    {"type": "schema_irregularity", "subtype": "missing_field"},
                ]
            }
        }

        _, _, _, _, anomaly_map = build_agency_maps(agency_index, None, ace_report)

        assert "City Council" in anomaly_map
        assert len(anomaly_map["City Council"]) == 2

    def test_empty_ace_report(self):
        """Test with empty ACE report."""
        agency_index = {
            "City Council": {
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
            }
        }

        _, _, _, _, anomaly_map = build_agency_maps(agency_index, None, {})

        assert len(anomaly_map["City Council"]) == 0

    def test_no_matching_hist_id(self):
        """Test when ACE anomalies don't match agency hist_ids."""
        agency_index = {
            "City Council": {
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
            }
        }
        ace_report = {"by_hist_id": {"HIST-9999": [{"type": "structural_gap"}]}}

        _, _, _, _, anomaly_map = build_agency_maps(agency_index, None, ace_report)

        assert len(anomaly_map["City Council"]) == 0


class TestAnomalyLinkageCalculation:
    """Tests for ACE anomaly linkage calculation."""

    def test_shared_anomaly_pattern(self):
        """Test agencies sharing same anomaly pattern."""
        anomaly_map = {
            "Agency A": {"HIST-1234:structural_gap", "HIST-1234:schema_issue"},
            "Agency B": {"HIST-1234:structural_gap", "HIST-5678:other_issue"},
        }

        result = calculate_ace_anomaly_linkage("Agency A", "Agency B", anomaly_map)

        # Intersection: 1 (HIST-1234:structural_gap)
        # Union: 3
        # Jaccard: 1/3 ≈ 0.333
        assert 0.3 <= result <= 0.4

    def test_no_shared_anomalies(self):
        """Test agencies with no shared anomalies."""
        anomaly_map = {
            "Agency A": {"HIST-1234:structural_gap"},
            "Agency B": {"HIST-5678:schema_issue"},
        }

        result = calculate_ace_anomaly_linkage("Agency A", "Agency B", anomaly_map)

        assert result == 0.0

    def test_identical_anomalies(self):
        """Test agencies with identical anomaly patterns."""
        anomaly_map = {
            "Agency A": {"HIST-1234:structural_gap"},
            "Agency B": {"HIST-1234:structural_gap"},
        }

        result = calculate_ace_anomaly_linkage("Agency A", "Agency B", anomaly_map)

        assert result == 1.0

    def test_empty_anomaly_sets(self):
        """Test with empty anomaly sets."""
        anomaly_map = {
            "Agency A": set(),
            "Agency B": set(),
        }

        result = calculate_ace_anomaly_linkage("Agency A", "Agency B", anomaly_map)

        assert result == 0.0


class TestAceIntegrationInIcmScore:
    """Tests for ACE integration in ICM score calculation."""

    def test_ace_component_in_score(self):
        """Test that ACE anomaly linkage affects total score."""
        vendor_map = {"A": set(), "B": set()}
        tech_map = {"A": set(), "B": set()}
        years_map = {"A": set(), "B": set()}
        hist_map = {"A": set(), "B": set()}
        anomaly_map = {
            "A": {"HIST-1234:anomaly"},
            "B": {"HIST-1234:anomaly"},
        }

        result = calculate_icm_score(
            "A", "B", vendor_map, tech_map, years_map, hist_map, anomaly_map
        )

        # ACE anomaly linkage should be 1.0 (identical sets)
        assert result["ace_anomaly_linkage"] == 1.0
        # Total score should include ACE component (0.20 weight)
        assert result["total_score"] == 0.20

    def test_no_ace_impact_when_no_anomalies(self):
        """Test no ACE impact when no anomalies present."""
        vendor_map = {"A": set(), "B": set()}
        tech_map = {"A": set(), "B": set()}
        years_map = {"A": set(), "B": set()}
        hist_map = {"A": set(), "B": set()}
        anomaly_map = {"A": set(), "B": set()}

        result = calculate_icm_score(
            "A", "B", vendor_map, tech_map, years_map, hist_map, anomaly_map
        )

        assert result["ace_anomaly_linkage"] == 0.0


class TestAceIntegrationInGraph:
    """Tests for ACE integration in agency graph building."""

    def test_graph_with_ace_report(self):
        """Test building graph with ACE report data."""
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
        ace_report = {"by_hist_id": {"HIST-1234": [{"type": "structural_gap"}]}}

        graph = build_agency_graph(
            agency_index, relationships, corpora, None, ace_report
        )

        # Should have interacts_with edge with ace_anomaly_linkage attribute
        interacts_edges = [e for e in graph.edges if e["type"] == "interacts_with"]
        assert len(interacts_edges) == 1
        assert "ace_anomaly_linkage" in interacts_edges[0]

    def test_graph_without_ace_report(self):
        """Test building graph without ACE report."""
        agency_index = {
            "City Council": {
                "name": "City Council",
                "type": "municipal",
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
                "appearance_count": 1,
                "year_span": 1,
            },
        }
        corpora = {"HIST-1234": "2020-01-15"}

        graph = build_agency_graph(agency_index, [], corpora, None, None)

        # Should still create agency node
        assert "agency:City Council" in graph.nodes
