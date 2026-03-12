#!/usr/bin/env python3
"""Tests for anomaly scoring functionality.

This module tests the score_forensic_integrity and detect_temporal_anomalies functions.
Total: 10 tests
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import (
    detect_retroactive_edit_indicators,
    detect_temporal_anomalies,
    score_forensic_integrity,
)


class TestScoreForensicIntegrity:
    """Tests for score_forensic_integrity function."""

    def test_perfect_score(self):
        """Test perfect score with no anomalies."""
        metadata = {"xmp": {"present": True}}
        result = score_forensic_integrity(
            metadata,
            temporal_anomalies=[],
            producer_anomalies=[],
            xmp_anomalies=[],
            retroactive_indicators=[],
            ace_anomaly_count=0,
        )
        assert result["forensic_score"] == 100.0

    def test_score_with_temporal_anomalies(self):
        """Test score reduction from temporal anomalies."""
        metadata = {"xmp": {"present": True}}
        temporal = [{"severity": "high"}, {"severity": "medium"}]
        result = score_forensic_integrity(
            metadata,
            temporal_anomalies=temporal,
            producer_anomalies=[],
            xmp_anomalies=[],
            retroactive_indicators=[],
            ace_anomaly_count=0,
        )
        assert result["forensic_score"] < 100.0
        assert result["components"]["timestamp_integrity"] < 1.0

    def test_score_with_missing_xmp(self):
        """Test score reduction from missing XMP."""
        metadata = {"xmp": {"present": False}}
        result = score_forensic_integrity(
            metadata,
            temporal_anomalies=[],
            producer_anomalies=[],
            xmp_anomalies=[],
            retroactive_indicators=[],
            ace_anomaly_count=0,
        )
        # XMP integrity should be 0.5 (not 1.0) when missing
        assert result["components"]["xmp_integrity"] == 0.5

    def test_score_with_ace_anomalies(self):
        """Test score reduction from ACE anomalies."""
        metadata = {"xmp": {"present": True}}
        result = score_forensic_integrity(
            metadata,
            temporal_anomalies=[],
            producer_anomalies=[],
            xmp_anomalies=[],
            retroactive_indicators=[],
            ace_anomaly_count=5,
        )
        assert result["components"]["ace_linkage"] < 1.0

    def test_score_contains_weights(self):
        """Test that score contains weight information."""
        metadata = {"xmp": {"present": True}}
        result = score_forensic_integrity(metadata, [], [], [], [], 0)
        assert "weights" in result
        assert result["weights"]["timestamp_integrity"] == 0.25
        assert result["weights"]["producer_consistency"] == 0.20
        assert result["weights"]["xmp_integrity"] == 0.20
        assert result["weights"]["origin_signature_stability"] == 0.20
        assert result["weights"]["ace_linkage"] == 0.15

    def test_score_contains_anomaly_counts(self):
        """Test that score contains anomaly counts."""
        metadata = {"xmp": {"present": True}}
        temporal = [{"severity": "low"}]
        producer = [{"severity": "medium"}, {"severity": "low"}]
        result = score_forensic_integrity(
            metadata,
            temporal_anomalies=temporal,
            producer_anomalies=producer,
            xmp_anomalies=[],
            retroactive_indicators=[],
            ace_anomaly_count=3,
        )
        assert result["anomaly_counts"]["temporal"] == 1
        assert result["anomaly_counts"]["producer"] == 2
        assert result["anomaly_counts"]["ace_linked"] == 3


class TestDetectTemporalAnomalies:
    """Tests for detect_temporal_anomalies function."""

    def test_detect_creation_after_modification(self):
        """Test detection of creation date after modification date."""
        now = datetime.now(UTC)
        creation = (now - timedelta(days=30)).isoformat()
        modification = (now - timedelta(days=60)).isoformat()

        metadata = {
            "normalized": {
                "creation_date": creation,
                "modification_date": modification,
            },
            "info_dict": {},
        }
        result = detect_temporal_anomalies(metadata)
        creation_after = [
            a for a in result if a["subtype"] == "creation_after_modification"
        ]
        assert len(creation_after) > 0

    def test_detect_future_dated(self):
        """Test detection of future-dated document."""
        future = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        metadata = {
            "normalized": {
                "creation_date": future,
                "modification_date": None,
            },
            "info_dict": {},
        }
        result = detect_temporal_anomalies(metadata)
        future_dated = [a for a in result if a["subtype"] == "future_dated"]
        assert len(future_dated) > 0

    def test_detect_producer_timeline_mismatch(self):
        """Test detection of producer timeline mismatch."""
        metadata = {
            "normalized": {
                "creation_date": "2014-01-15T00:00:00+00:00",
                "modification_date": None,
                "creation_year": 2014,
            },
            "info_dict": {
                "producer": "Microsoft Word 2019",
            },
        }
        result = detect_temporal_anomalies(metadata)
        timeline = [a for a in result if a["subtype"] == "producer_timeline_mismatch"]
        assert len(timeline) > 0

    def test_no_anomalies_valid_dates(self):
        """Test no anomalies for valid dates."""
        now = datetime.now(UTC)
        creation = (now - timedelta(days=60)).isoformat()
        modification = (now - timedelta(days=30)).isoformat()

        metadata = {
            "normalized": {
                "creation_date": creation,
                "modification_date": modification,
            },
            "info_dict": {},
        }
        result = detect_temporal_anomalies(metadata)
        # Should have no creation_after_modification or future_dated
        bad_anomalies = [
            a
            for a in result
            if a["subtype"] in ["creation_after_modification", "future_dated"]
        ]
        assert len(bad_anomalies) == 0


class TestDetectRetroactiveEditIndicators:
    """Tests for detect_retroactive_edit_indicators function."""

    def test_detect_significant_year_gap(self):
        """Test detection of significant year gap."""
        metadata = {
            "normalized": {
                "creation_year": 2014,
                "modification_year": 2020,
            },
            "info_dict": {
                "producer": "",
                "creator": "",
            },
            "xmp": {"present": False, "parsed": {}},
        }
        result = detect_retroactive_edit_indicators(metadata)
        year_gap = [a for a in result if a["subtype"] == "significant_year_gap"]
        assert len(year_gap) > 0
        assert year_gap[0]["year_gap"] == 6

    def test_no_retroactive_for_small_gap(self):
        """Test no retroactive indicator for small year gap."""
        metadata = {
            "normalized": {
                "creation_year": 2014,
                "modification_year": 2015,
            },
            "info_dict": {
                "producer": "",
                "creator": "",
            },
            "xmp": {"present": False, "parsed": {}},
        }
        result = detect_retroactive_edit_indicators(metadata)
        year_gap = [a for a in result if a["subtype"] == "significant_year_gap"]
        assert len(year_gap) == 0
