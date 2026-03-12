#!/usr/bin/env python3
"""Tests for ACE anomaly scoring.

This module tests the score_anomaly function which implements the 1-5 scoring model:
1. Mild irregularity
2. Repeated pattern
3. Multi-year repeated pattern
4. Structural or chronological anomaly
5. High-risk (cross-category correlation)
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.ace_analyzer import (
    SCORE_HIGH_RISK,
    SCORE_MILD,
    SCORE_MULTI_YEAR,
    SCORE_REPEATED,
    SCORE_STRUCTURAL,
    score_anomaly,
)


class TestScoreAnomaly:
    """Tests for score_anomaly function."""

    def test_mild_irregularity_default(self):
        """Test that default/unknown anomalies score as mild."""
        anomaly = {
            "type": "unknown_type",
            "severity": "low",
        }
        score = score_anomaly(anomaly)
        assert score == SCORE_MILD

    def test_high_risk_flag_scores_5(self):
        """Test that high_risk_flag type always scores 5."""
        anomaly = {
            "type": "high_risk_flag",
            "subtype": "multi_year_pattern",
            "severity": "critical",
        }
        score = score_anomaly(anomaly)
        assert score == SCORE_HIGH_RISK

    def test_multi_year_pattern_scores_at_least_3(self):
        """Test that multi-year patterns score at least 3."""
        anomaly = {
            "type": "structural_gap",
            "subtype": "multi_year_pattern",
            "years_affected": ["2014", "2015", "2016"],
            "severity": "low",
        }
        score = score_anomaly(anomaly)
        assert score >= SCORE_MULTI_YEAR

    def test_repeated_pattern_scores_at_least_2(self):
        """Test that repeated patterns score at least 2."""
        anomaly = {
            "type": "schema_irregularity",
            "occurrences": 5,
            "severity": "low",
        }
        score = score_anomaly(anomaly)
        assert score >= SCORE_REPEATED

    def test_structural_anomaly_scores_4(self):
        """Test that structural anomalies score 4."""
        anomaly = {
            "type": "chronological_drift",
            "subtype": "large_time_gap",
            "severity": "medium",
        }
        score = score_anomaly(anomaly)
        assert score >= SCORE_STRUCTURAL

    def test_critical_severity_scores_high(self):
        """Test that critical severity scores high."""
        anomaly = {
            "type": "test_type",
            "severity": "critical",
        }
        score = score_anomaly(anomaly)
        assert score == SCORE_HIGH_RISK

    def test_high_severity_scores_4(self):
        """Test that high severity scores 4."""
        anomaly = {
            "type": "test_type",
            "severity": "high",
        }
        score = score_anomaly(anomaly)
        assert score == SCORE_STRUCTURAL

    def test_medium_severity_scores_2(self):
        """Test that medium severity scores 2."""
        anomaly = {
            "type": "test_type",
            "severity": "medium",
        }
        score = score_anomaly(anomaly)
        assert score == SCORE_REPEATED

    def test_low_severity_scores_1(self):
        """Test that low severity scores 1."""
        anomaly = {
            "type": "test_type",
            "severity": "low",
        }
        score = score_anomaly(anomaly)
        assert score == SCORE_MILD

    def test_years_affected_threshold(self):
        """Test that 3+ years_affected triggers multi-year score."""
        anomaly = {
            "type": "test_type",
            "years_affected": ["2014", "2015", "2016"],
            "severity": "low",
        }
        score = score_anomaly(anomaly)
        assert score >= SCORE_MULTI_YEAR

    def test_below_years_threshold(self):
        """Test that fewer than 3 years_affected doesn't trigger multi-year."""
        anomaly = {
            "type": "test_type",
            "years_affected": ["2014", "2015"],
            "severity": "low",
        }
        score = score_anomaly(anomaly)
        assert score < SCORE_MULTI_YEAR

    def test_total_occurrences_threshold(self):
        """Test that 3+ total_occurrences triggers repeated score."""
        anomaly = {
            "type": "test_type",
            "total_occurrences": 5,
            "severity": "low",
        }
        score = score_anomaly(anomaly)
        assert score >= SCORE_REPEATED

    def test_empty_anomaly_defaults_to_mild(self):
        """Test that empty anomaly defaults to mild score."""
        anomaly = {}
        score = score_anomaly(anomaly)
        assert score == SCORE_MILD

    def test_score_range(self):
        """Test that all scores are in valid range 1-5."""
        test_cases = [
            {"type": "unknown"},
            {"type": "high_risk_flag"},
            {"type": "chronological_drift", "subtype": "large_time_gap"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
            {"years_affected": ["2014", "2015", "2016", "2017"]},
            {"occurrences": 10},
        ]

        for anomaly in test_cases:
            score = score_anomaly(anomaly)
            assert 1 <= score <= 5, f"Score {score} out of range for {anomaly}"


class TestScoringModelConsistency:
    """Tests to ensure scoring model is consistent with documentation."""

    def test_score_1_is_mild(self):
        """Test Score 1 = Mild irregularity."""
        assert SCORE_MILD == 1

    def test_score_2_is_repeated(self):
        """Test Score 2 = Repeated pattern."""
        assert SCORE_REPEATED == 2

    def test_score_3_is_multi_year(self):
        """Test Score 3 = Multi-year repeated pattern."""
        assert SCORE_MULTI_YEAR == 3

    def test_score_4_is_structural(self):
        """Test Score 4 = Structural or chronological anomaly."""
        assert SCORE_STRUCTURAL == 4

    def test_score_5_is_high_risk(self):
        """Test Score 5 = High-risk (cross-category correlation)."""
        assert SCORE_HIGH_RISK == 5


class TestScoreHierarchy:
    """Tests to ensure score hierarchy is respected."""

    def test_high_risk_overrides_everything(self):
        """Test that high_risk_flag always scores 5 regardless of other fields."""
        anomaly = {
            "type": "high_risk_flag",
            "severity": "low",  # Low severity should be overridden
            "years_affected": [],  # No years
        }
        score = score_anomaly(anomaly)
        assert score == SCORE_HIGH_RISK

    def test_severity_can_elevate_score(self):
        """Test that severity can elevate base score."""
        low_severity = {
            "type": "test",
            "severity": "low",
        }
        high_severity = {
            "type": "test",
            "severity": "high",
        }
        assert score_anomaly(high_severity) > score_anomaly(low_severity)

    def test_multiple_factors_use_highest(self):
        """Test that multiple scoring factors use the highest score."""
        anomaly = {
            "type": "test",
            "severity": "medium",  # Score 2
            "years_affected": ["2014", "2015", "2016"],  # Score 3
        }
        score = score_anomaly(anomaly)
        assert score >= SCORE_MULTI_YEAR  # Should use higher score
