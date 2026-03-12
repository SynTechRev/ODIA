#!/usr/bin/env python3
"""Tests for ACE metadata outlier detection.

This module tests the scan_metadata_for_outliers function which detects:
- Missing required fields
- Malformed field values
- Inconsistent field patterns
- Schema deviations
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.ace_analyzer import scan_metadata_for_outliers


class TestScanMetadataForOutliers:
    """Tests for scan_metadata_for_outliers function."""

    def test_empty_metadata_returns_no_anomalies(self):
        """Test that empty metadata dict returns no anomalies."""
        reports = {"metadata_files": {}}
        anomalies = scan_metadata_for_outliers(reports)
        assert anomalies == []

    def test_valid_metadata_returns_no_anomalies(self):
        """Test that valid metadata returns no anomalies."""
        reports = {
            "metadata_files": {
                "HIST-6225/corpus.json": {
                    "meeting_date": "2014-06-02",
                    "source_url": "https://example.legistar.com/LegislationDetail.aspx?ID=12345",
                    "file_hash": "abc123" * 10,
                    "corpus_id": "HIST-6225",
                }
            }
        }
        anomalies = scan_metadata_for_outliers(reports)
        assert anomalies == []

    def test_detects_missing_required_fields(self):
        """Test detection of missing required fields."""
        reports = {
            "metadata_files": {
                "HIST-6225/corpus.json": {
                    "meeting_date": "2014-06-02",
                    # missing source_url, file_hash, corpus_id
                }
            }
        }
        anomalies = scan_metadata_for_outliers(reports)
        assert len(anomalies) == 1
        assert anomalies[0]["type"] == "schema_irregularity"
        assert anomalies[0]["subtype"] == "missing_required_fields"
        assert "source_url" in anomalies[0]["missing_fields"]
        assert "file_hash" in anomalies[0]["missing_fields"]
        assert "corpus_id" in anomalies[0]["missing_fields"]

    def test_detects_malformed_date(self):
        """Test detection of malformed meeting_date."""
        reports = {
            "metadata_files": {
                "HIST-6225/corpus.json": {
                    "meeting_date": "06-02-2014",  # Wrong format
                    "source_url": "https://example.com",
                    "file_hash": "abc123" * 10,
                    "corpus_id": "HIST-6225",
                }
            }
        }
        anomalies = scan_metadata_for_outliers(reports)
        assert len(anomalies) == 1
        assert anomalies[0]["type"] == "schema_irregularity"
        assert anomalies[0]["subtype"] == "malformed_date"

    def test_detects_placeholder_source_url(self):
        """Test detection of placeholder source URLs."""
        reports = {
            "metadata_files": {
                "HIST-6225/corpus.json": {
                    "meeting_date": "2014-06-02",
                    "source_url": "NEEDS_USER_INPUT",
                    "file_hash": "abc123" * 10,
                    "corpus_id": "HIST-6225",
                }
            }
        }
        anomalies = scan_metadata_for_outliers(reports)
        assert len(anomalies) == 1
        assert anomalies[0]["type"] == "schema_irregularity"
        assert anomalies[0]["subtype"] == "placeholder_source_url"

    def test_detects_empty_source_url(self):
        """Test detection of empty source URLs."""
        reports = {
            "metadata_files": {
                "HIST-6225/corpus.json": {
                    "meeting_date": "2014-06-02",
                    "source_url": "",
                    "file_hash": "abc123" * 10,
                    "corpus_id": "HIST-6225",
                }
            }
        }
        anomalies = scan_metadata_for_outliers(reports)
        # Should detect both missing source_url and placeholder
        assert len(anomalies) >= 1

    def test_detects_invalid_metadata_format(self):
        """Test detection of non-dict metadata."""
        reports = {"metadata_files": {"HIST-6225/corpus.json": "not a dict"}}
        anomalies = scan_metadata_for_outliers(reports)
        assert len(anomalies) == 1
        assert anomalies[0]["type"] == "schema_irregularity"
        assert anomalies[0]["subtype"] == "invalid_metadata_format"

    def test_extracts_hist_id_from_path(self):
        """Test that hist_id is correctly extracted from file path."""
        reports = {
            "metadata_files": {
                "HIST-6225/test.json": {
                    "meeting_date": "bad-date",
                    "source_url": "https://example.com",
                    "file_hash": "abc123" * 10,
                    "corpus_id": "HIST-6225",
                }
            }
        }
        anomalies = scan_metadata_for_outliers(reports)
        assert anomalies[0]["hist_id"] == "HIST-6225"

    def test_multiple_anomalies_same_file(self):
        """Test detection of multiple anomalies in same file."""
        reports = {
            "metadata_files": {
                "HIST-6225/corpus.json": {
                    "meeting_date": "bad-date",
                    "source_url": "NEEDS_USER_INPUT",
                    # missing file_hash and corpus_id
                }
            }
        }
        anomalies = scan_metadata_for_outliers(reports)
        # Should have: missing_required_fields, malformed_date, placeholder_source_url
        assert len(anomalies) >= 2
        types = [a["subtype"] for a in anomalies]
        assert "malformed_date" in types

    def test_handles_missing_metadata_files_key(self):
        """Test handling of reports without metadata_files key."""
        reports = {}
        anomalies = scan_metadata_for_outliers(reports)
        assert anomalies == []
