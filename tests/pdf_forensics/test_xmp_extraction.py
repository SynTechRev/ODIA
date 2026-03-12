#!/usr/bin/env python3
"""Tests for XMP metadata extraction functionality.

This module tests the detect_xmp_anomalies and related functions.
Total: 10 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import (
    detect_xmp_anomalies,
    parse_xmp_metadata,
)


class TestDetectXmpAnomalies:
    """Tests for detect_xmp_anomalies function."""

    def test_detect_missing_xmp(self):
        """Test detection of missing XMP."""
        metadata = {"xmp": {"present": False}}
        result = detect_xmp_anomalies(metadata)
        assert len(result) > 0
        assert result[0]["subtype"] == "missing_xmp"
        assert result[0]["severity"] == "low"

    def test_detect_malformed_xmp(self):
        """Test detection of malformed XMP."""
        metadata = {
            "xmp": {
                "present": True,
                "malformed": True,
            }
        }
        result = detect_xmp_anomalies(metadata)
        malformed = [a for a in result if a["subtype"] == "malformed_xmp"]
        assert len(malformed) > 0

    def test_detect_truncated_xmp(self):
        """Test detection of truncated XMP."""
        metadata = {
            "xmp": {
                "present": True,
                "truncated": True,
            }
        }
        result = detect_xmp_anomalies(metadata)
        truncated = [a for a in result if a["subtype"] == "truncated_xmp"]
        assert len(truncated) > 0

    def test_detect_multiple_packets(self):
        """Test detection of multiple XMP packets."""
        metadata = {
            "xmp": {
                "present": True,
                "packet_count": 3,
            }
        }
        result = detect_xmp_anomalies(metadata)
        multiple = [a for a in result if a["subtype"] == "multiple_xmp_packets"]
        assert len(multiple) > 0
        assert multiple[0]["packet_count"] == 3

    def test_detect_ocr_regenerated(self):
        """Test detection of OCR regeneration in XMP."""
        metadata = {
            "xmp": {
                "present": True,
                "parsed": {
                    "CreatorTool": "ABBYY FineReader OCR",
                },
            }
        }
        result = detect_xmp_anomalies(metadata)
        ocr = [a for a in result if a["subtype"] == "ocr_regenerated"]
        assert len(ocr) > 0

    def test_no_anomalies_valid_xmp(self):
        """Test no anomalies for valid XMP."""
        metadata = {
            "xmp": {
                "present": True,
                "malformed": False,
                "truncated": False,
                "packet_count": 1,
                "parsed": {"CreateDate": "2014-12-08"},
            }
        }
        result = detect_xmp_anomalies(metadata)
        assert len(result) == 0

    def test_detect_single_packet_no_anomaly(self):
        """Test that single packet doesn't flag anomaly."""
        metadata = {
            "xmp": {
                "present": True,
                "packet_count": 1,
            }
        }
        result = detect_xmp_anomalies(metadata)
        multiple = [a for a in result if a["subtype"] == "multiple_xmp_packets"]
        assert len(multiple) == 0

    def test_xmp_empty_parsed_no_ocr(self):
        """Test empty parsed XMP doesn't flag OCR."""
        metadata = {
            "xmp": {
                "present": True,
                "parsed": {},
            }
        }
        result = detect_xmp_anomalies(metadata)
        ocr = [a for a in result if a["subtype"] == "ocr_regenerated"]
        assert len(ocr) == 0

    def test_xmp_none_value_handling(self):
        """Test handling of None values in XMP parsed fields."""
        metadata = {
            "xmp": {
                "present": True,
                "parsed": {
                    "CreateDate": None,
                    "Producer": None,
                },
            }
        }
        result = detect_xmp_anomalies(metadata)
        # Should not crash on None values
        assert isinstance(result, list)


class TestXmpNamespaces:
    """Tests for XMP namespace detection."""

    def test_detect_dc_namespace(self):
        """Test detection of Dublin Core namespace."""
        xmp_str = 'xmlns:dc="http://purl.org/dc/elements/1.1/"'
        result = parse_xmp_metadata(xmp_str)
        assert "dc" in result["namespaces_found"]

    def test_detect_xmp_namespace(self):
        """Test detection of XMP namespace."""
        xmp_str = 'xmlns:xmp="http://ns.adobe.com/xap/1.0/"'
        result = parse_xmp_metadata(xmp_str)
        assert "xmp" in result["namespaces_found"]

    def test_detect_pdf_namespace(self):
        """Test detection of PDF namespace."""
        xmp_str = 'xmlns:pdf="http://ns.adobe.com/pdf/1.3/"'
        result = parse_xmp_metadata(xmp_str)
        assert "pdf" in result["namespaces_found"]

    def test_detect_multiple_namespaces(self):
        """Test detection of multiple namespaces."""
        xmp_str = (
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:xmp="http://ns.adobe.com/xap/1.0/"'
        )
        result = parse_xmp_metadata(xmp_str)
        assert "dc" in result["namespaces_found"]
        assert "xmp" in result["namespaces_found"]
