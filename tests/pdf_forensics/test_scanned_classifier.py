#!/usr/bin/env python3
"""Tests for scanned-vs-digital classification functionality.

This module tests the detect_scanned_vs_digital and related functions.
Total: 10 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import (
    classify_origin_type,
    detect_ocr_presence,
    detect_scanned_vs_digital,
)


class TestDetectScannedVsDigital:
    """Tests for detect_scanned_vs_digital function."""

    def test_detect_scanned_scanner_producer(self):
        """Test detection of scanned PDF from scanner producer."""
        metadata = {
            "info_dict": {
                "producer": "Xerox WorkCentre",
                "creator": "Scan Application",
            }
        }
        result = detect_scanned_vs_digital(metadata)
        assert result["classification"] == "scanned"
        assert result["confidence"] > 0

    def test_detect_scanned_ocr_producer(self):
        """Test detection of scanned PDF from OCR producer."""
        metadata = {
            "info_dict": {
                "producer": "ABBYY FineReader 14",
                "creator": "",
            }
        }
        result = detect_scanned_vs_digital(metadata)
        assert result["classification"] == "scanned"
        assert "ocr_pattern" in str(result["indicators"])

    def test_detect_digital_word(self):
        """Test detection of digital PDF from Word."""
        metadata = {
            "info_dict": {
                "producer": "Microsoft Word 2016",
                "creator": "Microsoft Word",
            }
        }
        result = detect_scanned_vs_digital(metadata)
        assert result["classification"] == "digital"

    def test_detect_digital_acrobat(self):
        """Test detection of digital PDF from Acrobat."""
        metadata = {
            "info_dict": {
                "producer": "Adobe Acrobat Pro DC",
                "creator": "",
            }
        }
        result = detect_scanned_vs_digital(metadata)
        assert result["classification"] == "digital"

    def test_detect_unknown_empty(self):
        """Test unknown classification for empty metadata."""
        metadata = {"info_dict": {"producer": "", "creator": ""}}
        result = detect_scanned_vs_digital(metadata)
        assert result["classification"] == "unknown"
        assert result["confidence"] == 0.0

    def test_detect_mixed_indicators(self):
        """Test classification with mixed indicators."""
        metadata = {
            "info_dict": {
                "producer": "Adobe Acrobat Scan",
                "creator": "",
            }
        }
        result = detect_scanned_vs_digital(metadata)
        # Should have indicators from both sides
        assert len(result["indicators"]) > 0


class TestDetectOcrPresence:
    """Tests for detect_ocr_presence function."""

    def test_detect_ocr_in_producer(self):
        """Test OCR detection in producer field."""
        metadata = {
            "info_dict": {
                "producer": "ABBYY FineReader OCR",
                "creator": "",
            },
            "xmp": {"present": False},
        }
        result = detect_ocr_presence(metadata)
        assert result["ocr_detected"] is True
        assert result["confidence"] > 0

    def test_detect_ocr_tesseract(self):
        """Test OCR detection for Tesseract."""
        metadata = {
            "info_dict": {
                "producer": "Tesseract OCR Engine",
                "creator": "",
            },
            "xmp": {"present": False},
        }
        result = detect_ocr_presence(metadata)
        assert result["ocr_detected"] is True

    def test_no_ocr_digital(self):
        """Test no OCR for digital PDF."""
        metadata = {
            "info_dict": {
                "producer": "Microsoft Word",
                "creator": "",
            },
            "xmp": {"present": False},
        }
        result = detect_ocr_presence(metadata)
        assert result["ocr_detected"] is False

    def test_detect_ocr_in_xmp(self):
        """Test OCR detection in XMP metadata."""
        metadata = {
            "info_dict": {
                "producer": "",
                "creator": "",
            },
            "xmp": {
                "present": True,
                "parsed": {
                    "CreatorTool": "OmniPage OCR",
                },
            },
        }
        result = detect_ocr_presence(metadata)
        assert result["ocr_detected"] is True


class TestClassifyOriginType:
    """Tests for classify_origin_type function."""

    def test_classify_xerox_scanner(self):
        """Test classification of Xerox scanner origin."""
        metadata = {
            "info_dict": {
                "producer": "Xerox WorkCentre 7845",
                "creator": "",
            }
        }
        result = classify_origin_type(metadata)
        assert result["origin_type"] == "scanned"
        assert result["scanner_signature"] == "Xerox"

    def test_classify_canon_scanner(self):
        """Test classification of Canon scanner origin."""
        metadata = {
            "info_dict": {
                "producer": "Canon imageCLASS",
                "creator": "",
            }
        }
        result = classify_origin_type(metadata)
        assert result["origin_type"] == "scanned"
        assert result["scanner_signature"] == "Canon"

    def test_classify_microsoft_digital(self):
        """Test classification of Microsoft digital origin."""
        metadata = {
            "info_dict": {
                "producer": "Microsoft Word 2016",
                "creator": "Microsoft Word",
            }
        }
        result = classify_origin_type(metadata)
        assert result["origin_type"] == "digital"
        assert result["vendor"] == "Microsoft"

    def test_classify_unknown_origin(self):
        """Test classification of unknown origin."""
        metadata = {"info_dict": {"producer": "", "creator": ""}}
        result = classify_origin_type(metadata)
        assert result["origin_type"] == "unknown"
        assert result["confidence"] == 0.0
