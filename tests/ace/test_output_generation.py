#!/usr/bin/env python3
"""Tests for ACE output generation.

This module tests the output generation functions:
- generate_ace_report()
- generate_ace_summary_md()
- generate_anomaly_map_csv()
- generate_network_graph()
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.ace_analyzer import (
    ACE_SCHEMA_VERSION,
    ACE_VERSION,
    generate_ace_report,
    generate_ace_summary_md,
    generate_anomaly_map_csv,
    generate_network_graph,
)


class TestGenerateAceReport:
    """Tests for generate_ace_report function."""

    def test_report_has_required_fields(self):
        """Test that report contains all required fields."""
        reports = {}
        anomalies = []
        correlated = {}
        year_range = "2014-2025"

        report = generate_ace_report(reports, anomalies, correlated, year_range)

        assert "report_id" in report
        assert "generated_at" in report
        assert "ace_version" in report
        assert "schema_version" in report
        assert "year_range" in report
        assert "summary" in report
        assert "all_anomalies" in report

    def test_report_version_matches(self):
        """Test that report versions match constants."""
        reports = {}
        anomalies = []
        correlated = {}

        report = generate_ace_report(reports, anomalies, correlated, "2014-2025")

        assert report["ace_version"] == ACE_VERSION
        assert report["schema_version"] == ACE_SCHEMA_VERSION

    def test_report_summary_structure(self):
        """Test that summary has correct structure."""
        reports = {}
        anomalies = [
            {"type": "test", "severity": "low"},
            {"type": "test", "severity": "medium"},
        ]
        correlated = {"HIST-1": anomalies}

        report = generate_ace_report(reports, anomalies, correlated, "2014-2025")

        summary = report["summary"]
        assert "total_anomalies" in summary
        assert "unique_corpora_affected" in summary
        assert "average_score" in summary
        assert "high_risk_count" in summary
        assert "score_distribution" in summary

    def test_anomalies_are_scored(self):
        """Test that all anomalies receive ace_score."""
        reports = {}
        anomalies = [
            {"type": "test1", "severity": "low"},
            {"type": "test2", "severity": "high"},
        ]
        correlated = {}

        report = generate_ace_report(reports, anomalies, correlated, "2014-2025")

        for anomaly in report["all_anomalies"]:
            assert "ace_score" in anomaly
            assert 1 <= anomaly["ace_score"] <= 5

    def test_high_risk_alerts_populated(self):
        """Test that high_risk_alerts contains score 5 anomalies."""
        reports = {}
        anomalies = [
            {"type": "high_risk_flag", "severity": "critical"},
            {"type": "test", "severity": "low"},
        ]
        correlated = {}

        report = generate_ace_report(reports, anomalies, correlated, "2014-2025")

        assert len(report["high_risk_alerts"]) == 1
        assert report["high_risk_alerts"][0]["ace_score"] == 5

    def test_by_category_grouping(self):
        """Test that anomalies are grouped by category."""
        reports = {}
        anomalies = [
            {"type": "type_a", "severity": "low"},
            {"type": "type_a", "severity": "medium"},
            {"type": "type_b", "severity": "low"},
        ]
        correlated = {}

        report = generate_ace_report(reports, anomalies, correlated, "2014-2025")

        assert "type_a" in report["by_category"]
        assert "type_b" in report["by_category"]
        assert len(report["by_category"]["type_a"]) == 2
        assert len(report["by_category"]["type_b"]) == 1

    def test_by_hist_id_grouping(self):
        """Test that anomalies are grouped by hist_id."""
        reports = {}
        anomalies = []
        correlated = {
            "HIST-1": [{"type": "test", "severity": "low"}],
            "HIST-2": [
                {"type": "test", "severity": "low"},
                {"type": "test", "severity": "medium"},
            ],
        }

        report = generate_ace_report(reports, anomalies, correlated, "2014-2025")

        assert "HIST-1" in report["by_hist_id"]
        assert "HIST-2" in report["by_hist_id"]
        assert len(report["by_hist_id"]["HIST-1"]) == 1
        assert len(report["by_hist_id"]["HIST-2"]) == 2

    def test_scoring_model_included(self):
        """Test that scoring model definitions are included."""
        reports = {}
        report = generate_ace_report(reports, [], {}, "2014-2025")

        assert "scoring_model" in report
        assert "1" in report["scoring_model"]
        assert "5" in report["scoring_model"]

    def test_report_id_is_hex(self):
        """Test that report_id is valid hex string."""
        reports = {}
        report = generate_ace_report(reports, [], {}, "2014-2025")

        report_id = report["report_id"]
        assert len(report_id) == 16
        assert all(c in "0123456789abcdef" for c in report_id)


class TestGenerateAceSummaryMd:
    """Tests for generate_ace_summary_md function."""

    def test_summary_is_string(self):
        """Test that summary is a string."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "report_id": "abc123",
            "year_range": "2014-2025",
            "summary": {
                "total_anomalies": 10,
                "unique_corpora_affected": 5,
                "average_score": 2.5,
                "high_risk_count": 1,
                "score_distribution": {1: 5, 2: 3, 3: 1, 5: 1},
            },
            "scoring_model": {
                "1": "Mild",
                "2": "Repeated",
                "3": "Multi-year",
                "4": "Structural",
                "5": "High-risk",
            },
            "by_category": {},
            "high_risk_alerts": [],
        }

        md = generate_ace_summary_md(report)
        assert isinstance(md, str)

    def test_summary_has_header(self):
        """Test that summary has ACE header."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "report_id": "abc123",
            "year_range": "2014-2025",
            "summary": {
                "total_anomalies": 0,
                "unique_corpora_affected": 0,
                "average_score": 0,
                "high_risk_count": 0,
                "score_distribution": {},
            },
            "scoring_model": {},
            "by_category": {},
            "high_risk_alerts": [],
        }

        md = generate_ace_summary_md(report)
        assert "ACE v1.0" in md
        assert "Anomaly Correlation Engine" in md

    def test_summary_includes_statistics(self):
        """Test that summary includes key statistics."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "report_id": "abc123",
            "year_range": "2014-2025",
            "summary": {
                "total_anomalies": 42,
                "unique_corpora_affected": 15,
                "average_score": 2.7,
                "high_risk_count": 3,
                "score_distribution": {1: 10, 2: 20, 5: 3},
            },
            "scoring_model": {"1": "Mild", "5": "High-risk"},
            "by_category": {},
            "high_risk_alerts": [],
        }

        md = generate_ace_summary_md(report)
        assert "42" in md  # Total anomalies
        assert "15" in md  # Corpora affected
        assert "3" in md  # High-risk count

    def test_summary_includes_table(self):
        """Test that summary includes score distribution table."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "report_id": "abc123",
            "year_range": "2014-2025",
            "summary": {
                "total_anomalies": 0,
                "unique_corpora_affected": 0,
                "average_score": 0,
                "high_risk_count": 0,
                "score_distribution": {},
            },
            "scoring_model": {"1": "Mild", "2": "Repeated"},
            "by_category": {},
            "high_risk_alerts": [],
        }

        md = generate_ace_summary_md(report)
        assert "| Score |" in md
        assert "| Count |" in md


class TestGenerateAnomalyMapCsv:
    """Tests for generate_anomaly_map_csv function."""

    def test_csv_has_headers(self):
        """Test that CSV has correct headers."""
        report = {"all_anomalies": []}

        rows = generate_anomaly_map_csv(report)

        assert len(rows) >= 1
        headers = rows[0]
        assert "hist_id" in headers
        assert "type" in headers
        assert "subtype" in headers
        assert "ace_score" in headers
        assert "severity" in headers

    def test_csv_rows_match_anomalies(self):
        """Test that CSV has correct number of rows."""
        report = {
            "all_anomalies": [
                {
                    "hist_id": "H1",
                    "type": "t1",
                    "subtype": "s1",
                    "ace_score": 1,
                    "severity": "low",
                    "details": "d1",
                },
                {
                    "hist_id": "H2",
                    "type": "t2",
                    "subtype": "s2",
                    "ace_score": 2,
                    "severity": "medium",
                    "details": "d2",
                },
            ]
        }

        rows = generate_anomaly_map_csv(report)

        assert len(rows) == 3  # Header + 2 data rows

    def test_csv_data_correct(self):
        """Test that CSV data is correctly populated."""
        report = {
            "all_anomalies": [
                {
                    "hist_id": "HIST-123",
                    "type": "test_type",
                    "subtype": "test_sub",
                    "ace_score": 3,
                    "severity": "high",
                    "details": "Test details",
                },
            ]
        }

        rows = generate_anomaly_map_csv(report)
        data_row = rows[1]

        assert "HIST-123" in data_row
        assert "test_type" in data_row
        assert "test_sub" in data_row
        assert "3" in data_row

    def test_csv_handles_missing_fields(self):
        """Test that CSV handles missing fields gracefully."""
        report = {
            "all_anomalies": [
                {"type": "test"},  # Missing most fields
            ]
        }

        rows = generate_anomaly_map_csv(report)
        assert len(rows) == 2  # Header + 1 row

    def test_csv_truncates_long_details(self):
        """Test that long details are truncated."""
        long_details = "x" * 500
        report = {
            "all_anomalies": [
                {"hist_id": "H1", "type": "t", "details": long_details},
            ]
        }

        rows = generate_anomaly_map_csv(report)
        headers = rows[0]
        assert "details" in headers, "details column should exist"
        details_idx = headers.index("details")
        assert len(rows[1][details_idx]) <= 200


class TestGenerateNetworkGraph:
    """Tests for generate_network_graph function."""

    def test_graph_has_required_fields(self):
        """Test that graph has required structure."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "by_hist_id": {},
            "by_category": {},
        }

        graph = generate_network_graph(report)

        assert "nodes" in graph
        assert "edges" in graph
        assert "statistics" in graph

    def test_graph_creates_corpus_nodes(self):
        """Test that graph creates nodes for corpora."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "by_hist_id": {
                "HIST-1": [{"ace_score": 2}],
                "HIST-2": [{"ace_score": 3}],
            },
            "by_category": {},
        }

        graph = generate_network_graph(report)

        corpus_nodes = [n for n in graph["nodes"] if n.get("type") == "corpus"]
        assert len(corpus_nodes) == 2

    def test_graph_creates_type_nodes(self):
        """Test that graph creates nodes for anomaly types."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "by_hist_id": {"HIST-1": [{"ace_score": 2}]},
            "by_category": {
                "type_a": [{"hist_id": "HIST-1"}],
            },
        }

        graph = generate_network_graph(report)

        type_nodes = [n for n in graph["nodes"] if n.get("type") == "anomaly_type"]
        assert len(type_nodes) == 1
        assert type_nodes[0]["id"] == "type_a"

    def test_graph_creates_edges(self):
        """Test that graph creates edges between nodes."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "by_hist_id": {
                "HIST-1": [{"ace_score": 2}],
            },
            "by_category": {
                "type_a": [{"hist_id": "HIST-1"}],
            },
        }

        graph = generate_network_graph(report)

        has_anomaly_edges = [
            e for e in graph["edges"] if e.get("type") == "has_anomaly"
        ]
        assert len(has_anomaly_edges) >= 1

    def test_graph_statistics(self):
        """Test that graph statistics are correct."""
        report = {
            "generated_at": "2025-01-01T00:00:00Z",
            "by_hist_id": {
                "HIST-1": [{"ace_score": 2}],
                "HIST-2": [{"ace_score": 3}],
            },
            "by_category": {
                "type_a": [],
            },
        }

        graph = generate_network_graph(report)

        stats = graph["statistics"]
        assert stats["total_nodes"] == len(graph["nodes"])
        assert stats["total_edges"] == len(graph["edges"])
        assert stats["corpus_nodes"] == 2
        assert stats["anomaly_type_nodes"] == 1
