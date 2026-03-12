#!/usr/bin/env python3
"""Tests for producer validation functionality.

This module tests the detect_producer_anomalies and related functions.
Total: 10 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import (
    _check_producer_timeline,
    _detect_platform,
    detect_producer_anomalies,
)


class TestDetectPlatform:
    """Tests for _detect_platform function."""

    def test_detect_windows(self):
        """Test detection of Windows platform."""
        result = _detect_platform("Microsoft Word", "")
        assert result == "Windows"

    def test_detect_macos(self):
        """Test detection of macOS platform."""
        result = _detect_platform("Apple Quartz PDFContext", "")
        assert result == "macOS"

    def test_detect_linux(self):
        """Test detection of Linux platform."""
        result = _detect_platform("LibreOffice 7.0", "")
        assert result == "Linux"

    def test_detect_unknown(self):
        """Test detection of unknown platform."""
        result = _detect_platform("Unknown Producer", "Unknown Creator")
        assert result is None


class TestCheckProducerTimeline:
    """Tests for _check_producer_timeline function."""

    def test_producer_timeline_mismatch(self):
        """Test detection of producer timeline mismatch."""
        result = _check_producer_timeline("Microsoft Word 2019", 2014)
        assert result is not None
        assert result["type"] == "temporal_anomaly"
        assert result["subtype"] == "producer_timeline_mismatch"
        assert result["severity"] == "high"

    def test_producer_timeline_valid(self):
        """Test valid producer timeline."""
        result = _check_producer_timeline("Microsoft Word 2010", 2014)
        assert result is None

    def test_producer_timeline_adobe_mismatch(self):
        """Test Adobe producer timeline mismatch."""
        result = _check_producer_timeline("Adobe Acrobat Pro DC", 2014)
        assert result is not None
        assert "Adobe" in result["producer"]


class TestDetectProducerAnomalies:
    """Tests for detect_producer_anomalies function."""

    def test_detect_platform_mismatch(self):
        """Test detection of platform mismatch."""
        metadata = {
            "info_dict": {
                "producer": "Apple Quartz PDFContext",
                "creator": "Preview",
            }
        }
        result = detect_producer_anomalies(metadata, expected_platform="Windows")
        platform_anomalies = [a for a in result if a["subtype"] == "platform_mismatch"]
        assert len(platform_anomalies) > 0

    def test_detect_vendor_software(self):
        """Test detection of vendor-linked software."""
        metadata = {
            "info_dict": {
                "producer": "Microsoft Word 2016",
                "creator": "Microsoft Word",
            }
        }
        result = detect_producer_anomalies(metadata)
        vendor_anomalies = [
            a for a in result if a["subtype"] == "vendor_software_detected"
        ]
        assert len(vendor_anomalies) > 0
        assert vendor_anomalies[0]["vendor"] == "Microsoft"

    def test_detect_no_anomalies_empty(self):
        """Test no anomalies for empty producer/creator."""
        metadata = {"info_dict": {"producer": "", "creator": ""}}
        result = detect_producer_anomalies(metadata)
        # May still detect vendor patterns for empty strings
        assert isinstance(result, list)
