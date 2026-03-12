#!/usr/bin/env python3
"""Tests for ACE/VICFM crosslink functionality.

This module tests the forensic integration functions.
Total: 5 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.forensic_integration import (
    generate_forensic_agency_patterns,
    generate_forensic_anomaly_links,
    generate_forensic_vendor_overlaps,
)


class TestGenerateForensicAnomalyLinks:
    """Tests for generate_forensic_anomaly_links function."""

    def test_generate_links_empty(self):
        """Test link generation with empty reports."""
        forensic_report = {"anomalies": []}
        ace_report = {"by_hist_id": {}}
        result = generate_forensic_anomaly_links(forensic_report, ace_report)
        assert result["summary"]["total_links"] == 0

    def test_generate_links_no_ace(self):
        """Test link generation without ACE report."""
        forensic_report = {
            "anomalies": [{"hist_id": "HIST-1234", "type": "temporal_anomaly"}]
        }
        result = generate_forensic_anomaly_links(forensic_report, None)
        assert result["summary"]["total_links"] == 0

    def test_generate_links_with_overlap(self):
        """Test link generation with overlapping hist_ids."""
        forensic_report = {
            "anomalies": [
                {
                    "hist_id": "HIST-1234",
                    "type": "temporal_anomaly",
                    "subtype": "creation_after_modification",
                    "severity": "medium",
                    "details": "Creation date after modification",
                }
            ]
        }
        ace_report = {
            "by_hist_id": {
                "HIST-1234": [
                    {
                        "type": "chronological_drift",
                        "subtype": "large_time_gap",
                        "ace_score": 3,
                        "details": "Large gap detected",
                    }
                ]
            }
        }
        result = generate_forensic_anomaly_links(forensic_report, ace_report)
        assert result["summary"]["total_links"] > 0
        assert "HIST-1234" in result["summary"]["overlap_by_hist_id"]


class TestGenerateForensicVendorOverlaps:
    """Tests for generate_forensic_vendor_overlaps function."""

    def test_generate_overlaps_empty(self):
        """Test overlap generation with empty report."""
        forensic_report = {"anomalies": []}
        result = generate_forensic_vendor_overlaps(forensic_report)
        assert result["summary"]["total_overlaps"] == 0

    def test_generate_overlaps_with_vendor_anomalies(self):
        """Test overlap generation with vendor anomalies."""
        forensic_report = {
            "anomalies": [
                {
                    "type": "producer_anomaly",
                    "subtype": "vendor_software_detected",
                    "vendor": "Microsoft",
                    "producer": "Microsoft Word 2016",
                    "creator": "",
                    "pattern_matched": "microsoft",
                    "hist_id": "HIST-1234",
                    "file_path": "/path/to/doc.pdf",
                }
            ]
        }
        result = generate_forensic_vendor_overlaps(forensic_report)
        assert result["summary"]["total_overlaps"] > 0
        assert "Microsoft" in result["summary"]["vendors_with_forensic_flags"]


class TestGenerateForensicAgencyPatterns:
    """Tests for generate_forensic_agency_patterns function."""

    def test_generate_patterns_empty(self):
        """Test pattern generation with empty report."""
        forensic_report = {
            "anomalies": [],
            "clusters": {"clusters": {}},
        }
        result = generate_forensic_agency_patterns(forensic_report)
        assert result["summary"]["total_patterns"] == 0

    def test_generate_patterns_with_multi_year(self):
        """Test pattern generation with multi-year anomalies."""
        forensic_report = {
            "anomalies": [
                {
                    "type": "temporal_anomaly",
                    "meeting_date": "2014-01-15",
                },
                {
                    "type": "temporal_anomaly",
                    "meeting_date": "2015-03-20",
                },
                {
                    "type": "temporal_anomaly",
                    "meeting_date": "2016-06-10",
                },
            ],
            "clusters": {"clusters": {}},
        }
        result = generate_forensic_agency_patterns(forensic_report)
        # Should detect multi-year pattern
        assert result["summary"]["total_patterns"] > 0
        pattern = result["patterns"][0]
        assert pattern["type"] == "multi_year_pattern"
        assert len(pattern["years_affected"]) >= 2
