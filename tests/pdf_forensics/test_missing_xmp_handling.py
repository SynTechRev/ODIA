#!/usr/bin/env python3
"""Tests for missing XMP handling functionality.

This module tests graceful handling of missing XMP metadata.
Total: 5 tests
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import (
    detect_xmp_anomalies,
    extract_pdf_metadata,
    parse_xmp_metadata,
    score_forensic_integrity,
)


class TestMissingXmpHandling:
    """Tests for missing XMP handling."""

    def test_parse_none_xmp(self):
        """Test parsing None XMP data."""
        result = parse_xmp_metadata(None)
        assert result["present"] is False
        assert result.get("raw") is None
        assert result["parsed"] == {}

    def test_parse_empty_string_xmp(self):
        """Test parsing empty string XMP data."""
        result = parse_xmp_metadata("")
        assert result["present"] is False

    def test_detect_missing_xmp_anomaly(self):
        """Test that missing XMP is flagged as anomaly."""
        metadata = {"xmp": {"present": False}}
        result = detect_xmp_anomalies(metadata)
        assert len(result) > 0
        assert result[0]["subtype"] == "missing_xmp"
        assert result[0]["severity"] == "low"

    def test_score_with_missing_xmp(self):
        """Test scoring when XMP is missing."""
        metadata = {"xmp": {"present": False}}
        result = score_forensic_integrity(
            metadata,
            temporal_anomalies=[],
            producer_anomalies=[],
            xmp_anomalies=[],
            retroactive_indicators=[],
            ace_anomaly_count=0,
        )
        # XMP integrity component should be reduced but not zero
        assert result["components"]["xmp_integrity"] == 0.5

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader")
    def test_extract_pdf_without_xmp(self, mock_reader, tmp_path):
        """Test extraction of PDF without XMP metadata."""
        mock_instance = MagicMock()
        mock_instance.metadata = MagicMock()
        mock_instance.metadata.producer = "Producer"
        mock_instance.metadata.creator = None
        mock_instance.metadata.author = None
        mock_instance.metadata.title = None
        mock_instance.metadata.subject = None
        mock_instance.metadata.creation_date = None
        mock_instance.metadata.modification_date = None
        mock_instance.pages = []
        mock_instance.is_encrypted = False
        mock_instance.xmp_metadata = None  # No XMP
        mock_reader.return_value = mock_instance

        test_file = tmp_path / "no_xmp.pdf"
        test_file.write_bytes(b"%PDF-1.4 content")

        result = extract_pdf_metadata(test_file)
        assert result["extraction_success"] is True
        assert result["xmp"]["present"] is False


class TestXmpFieldGracefulDegradation:
    """Tests for graceful degradation when XMP fields are missing."""

    def test_xmp_with_missing_fields(self):
        """Test XMP parsing with missing common fields."""
        xmp_str = '<?xpacket begin="..."?><?xpacket end="w"?>'
        result = parse_xmp_metadata(xmp_str)
        assert result["present"] is True
        # Should have empty parsed dict
        assert isinstance(result["parsed"], dict)

    def test_xmp_with_partial_fields(self):
        """Test XMP parsing with some fields present."""
        xmp_str = "<xmp:CreateDate>2014-12-08</xmp:CreateDate>"
        result = parse_xmp_metadata(xmp_str)
        assert result["present"] is True
        assert "CreateDate" in result["parsed"]
        # ModifyDate should not be present
        assert "ModifyDate" not in result["parsed"]

    def test_xmp_anomaly_detection_empty_parsed(self):
        """Test anomaly detection when parsed XMP is empty."""
        metadata = {
            "xmp": {
                "present": True,
                "malformed": False,
                "truncated": False,
                "packet_count": 1,
                "parsed": {},  # Empty
            }
        }
        result = detect_xmp_anomalies(metadata)
        # Should not crash and should not flag OCR regeneration
        ocr = [a for a in result if a["subtype"] == "ocr_regenerated"]
        assert len(ocr) == 0

    def test_xmp_anomaly_detection_none_values(self):
        """Test anomaly detection when XMP fields are None."""
        metadata = {
            "xmp": {
                "present": True,
                "parsed": {
                    "CreateDate": None,
                    "ModifyDate": None,
                    "Producer": None,
                },
            }
        }
        result = detect_xmp_anomalies(metadata)
        # Should not crash on None values
        assert isinstance(result, list)
