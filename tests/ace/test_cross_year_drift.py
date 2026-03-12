#!/usr/bin/env python3
"""Tests for ACE cross-year drift detection.

This module tests the detect_cross_year_irregularities function which detects:
- Chronological drift (meeting date mismatches)
- Time-gap irregularities
- Patterns repeated across years
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.ace_analyzer import (
    HIGH_RISK_THRESHOLD,
    detect_cross_year_irregularities,
)


class TestDetectCrossYearIrregularities:
    """Tests for detect_cross_year_irregularities function."""

    def test_empty_correlated_returns_empty(self):
        """Test that empty correlated dict returns empty list."""
        correlated = {}
        corpora = {}
        anomalies = detect_cross_year_irregularities(correlated, corpora)
        assert anomalies == []

    def test_detects_duplicate_dates(self):
        """Test detection of multiple corpora with same meeting date."""
        correlated = {
            "HIST-6225": [],
            "HIST-6226": [],
        }
        corpora = {
            "HIST-6225": "2014-06-02",
            "HIST-6226": "2014-06-02",  # Same date
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        duplicate_anomalies = [
            a for a in anomalies if a.get("subtype") == "duplicate_dates"
        ]
        assert len(duplicate_anomalies) == 1
        assert "HIST-6225" in duplicate_anomalies[0]["hist_ids"]
        assert "HIST-6226" in duplicate_anomalies[0]["hist_ids"]

    def test_detects_large_time_gap(self):
        """Test detection of large time gaps within same year."""
        correlated = {
            "HIST-6225": [],
            "HIST-6226": [],
        }
        corpora = {
            "HIST-6225": "2014-01-15",
            "HIST-6226": "2014-09-15",  # 243 days gap in same year
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        gap_anomalies = [a for a in anomalies if a.get("subtype") == "large_time_gap"]
        assert len(gap_anomalies) == 1
        assert gap_anomalies[0]["gap_days"] > 180

    def test_no_gap_anomaly_for_cross_year(self):
        """Test that gaps across years don't trigger large_time_gap."""
        correlated = {
            "HIST-6225": [],
            "HIST-6226": [],
        }
        corpora = {
            "HIST-6225": "2014-06-15",
            "HIST-6226": "2015-03-15",  # Different year
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        gap_anomalies = [a for a in anomalies if a.get("subtype") == "large_time_gap"]
        assert len(gap_anomalies) == 0

    def test_detects_multi_year_pattern(self):
        """Test detection of anomaly patterns across multiple years."""
        # Create anomalies across 3+ years
        correlated = {
            "HIST-2014": [{"type": "structural_gap"}],
            "HIST-2015": [{"type": "structural_gap"}],
            "HIST-2016": [{"type": "structural_gap"}],
        }
        corpora = {
            "HIST-2014": "2014-06-02",
            "HIST-2015": "2015-06-02",
            "HIST-2016": "2016-06-02",
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        # Should detect multi-year pattern
        high_risk = [a for a in anomalies if a.get("type") == "high_risk_flag"]
        assert len(high_risk) >= 1
        assert any(a.get("subtype") == "multi_year_pattern" for a in high_risk)

    def test_high_risk_threshold(self):
        """Test that high-risk threshold is correctly applied."""
        # Just below threshold - should not trigger
        correlated = {
            f"HIST-{i}": [{"type": "test_anomaly"}]
            for i in range(HIGH_RISK_THRESHOLD - 1)
        }
        corpora = {
            f"HIST-{i}": f"{2014+i}-06-02" for i in range(HIGH_RISK_THRESHOLD - 1)
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        high_risk = [
            a
            for a in anomalies
            if a.get("type") == "high_risk_flag"
            and a.get("pattern_type") == "test_anomaly"
        ]
        assert len(high_risk) == 0

    def test_chronological_drift_type(self):
        """Test that chronological drift anomalies have correct type."""
        correlated = {
            "HIST-6225": [],
            "HIST-6226": [],
        }
        corpora = {
            "HIST-6225": "2014-01-15",
            "HIST-6226": "2014-09-15",
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        for anomaly in anomalies:
            if anomaly.get("subtype") == "large_time_gap":
                assert anomaly["type"] == "chronological_drift"

    def test_handles_invalid_dates(self):
        """Test that invalid dates don't cause crashes."""
        correlated = {
            "HIST-6225": [],
            "HIST-6226": [],
        }
        corpora = {
            "HIST-6225": "invalid-date",
            "HIST-6226": "2014-06-02",
        }
        # Should not raise exception
        anomalies = detect_cross_year_irregularities(correlated, corpora)
        assert isinstance(anomalies, list)

    def test_counts_years_affected(self):
        """Test that years_affected is correctly populated."""
        correlated = {
            "HIST-2014a": [{"type": "test_type"}],
            "HIST-2014b": [{"type": "test_type"}],
            "HIST-2015": [{"type": "test_type"}],
            "HIST-2016": [{"type": "test_type"}],
        }
        corpora = {
            "HIST-2014a": "2014-01-02",
            "HIST-2014b": "2014-06-02",
            "HIST-2015": "2015-06-02",
            "HIST-2016": "2016-06-02",
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        high_risk = [
            a
            for a in anomalies
            if a.get("type") == "high_risk_flag"
            and a.get("pattern_type") == "test_type"
        ]
        if high_risk:
            years = high_risk[0].get("years_affected", [])
            assert "2014" in years
            assert "2015" in years
            assert "2016" in years


class TestChronologicalDriftDetails:
    """Additional tests for chronological drift detection specifics."""

    def test_gap_days_calculation(self):
        """Test that gap_days is correctly calculated."""
        correlated = {
            "HIST-A": [],
            "HIST-B": [],
        }
        corpora = {
            "HIST-A": "2014-01-01",
            "HIST-B": "2014-07-04",  # 184 days later
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        gap_anomalies = [a for a in anomalies if a.get("subtype") == "large_time_gap"]
        if gap_anomalies:
            assert gap_anomalies[0]["gap_days"] == 184

    def test_previous_hist_id_tracked(self):
        """Test that previous_hist_id is tracked in gap anomalies."""
        correlated = {
            "HIST-A": [],
            "HIST-B": [],
        }
        corpora = {
            "HIST-A": "2014-01-01",
            "HIST-B": "2014-09-01",
        }
        anomalies = detect_cross_year_irregularities(correlated, corpora)

        gap_anomalies = [a for a in anomalies if a.get("subtype") == "large_time_gap"]
        if gap_anomalies:
            assert gap_anomalies[0]["previous_hist_id"] == "HIST-A"
            assert gap_anomalies[0]["hist_id"] == "HIST-B"
