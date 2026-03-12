#!/usr/bin/env python3
"""Tests for PDF date normalization functionality.

This module tests the normalize_pdf_date function.
Total: 15 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import normalize_pdf_date


class TestNormalizePdfDate:
    """Tests for normalize_pdf_date function."""

    def test_normalize_none(self):
        """Test normalizing None returns None."""
        result = normalize_pdf_date(None)
        assert result is None

    def test_normalize_empty_string(self):
        """Test normalizing empty string returns None."""
        result = normalize_pdf_date("")
        assert result is None

    def test_normalize_standard_pdf_date(self):
        """Test normalizing standard PDF date format."""
        result = normalize_pdf_date("D:20141208153000")
        assert result is not None
        assert result.year == 2014
        assert result.month == 12
        assert result.day == 8
        assert result.hour == 15
        assert result.minute == 30
        assert result.second == 0

    def test_normalize_pdf_date_with_z_suffix(self):
        """Test normalizing PDF date with Z suffix."""
        result = normalize_pdf_date("D:20141208153000Z")
        assert result is not None
        assert result.year == 2014
        assert result.tzinfo is not None

    def test_normalize_pdf_date_with_positive_offset(self):
        """Test normalizing PDF date with positive timezone offset."""
        result = normalize_pdf_date("D:20141208153000+08'00'")
        assert result is not None
        assert result.year == 2014

    def test_normalize_pdf_date_with_negative_offset(self):
        """Test normalizing PDF date with negative timezone offset."""
        result = normalize_pdf_date("D:20141208153000-08'00'")
        assert result is not None
        assert result.year == 2014

    def test_normalize_short_pdf_date(self):
        """Test normalizing short PDF date (no time component)."""
        result = normalize_pdf_date("D:20140812")
        assert result is not None
        assert result.year == 2014
        assert result.month == 8
        assert result.day == 12

    def test_normalize_iso_date(self):
        """Test normalizing ISO format date."""
        result = normalize_pdf_date("2014-12-08")
        assert result is not None
        assert result.year == 2014
        assert result.month == 12
        assert result.day == 8

    def test_normalize_iso_datetime(self):
        """Test normalizing ISO format datetime."""
        result = normalize_pdf_date("2014-12-08T15:30:00Z")
        assert result is not None
        assert result.year == 2014
        assert result.hour == 15

    def test_normalize_slash_date(self):
        """Test normalizing date with slashes."""
        result = normalize_pdf_date("2014/12/08")
        assert result is not None
        assert result.year == 2014
        assert result.month == 12
        assert result.day == 8

    def test_normalize_invalid_date(self):
        """Test normalizing invalid date returns None."""
        result = normalize_pdf_date("not a date")
        assert result is None

    def test_normalize_invalid_pdf_format(self):
        """Test normalizing malformed PDF date returns None."""
        result = normalize_pdf_date("D:invalid")
        assert result is None

    def test_normalize_partial_time(self):
        """Test normalizing PDF date with partial time."""
        result = normalize_pdf_date("D:2014120815")
        assert result is not None
        assert result.year == 2014
        assert result.hour == 15

    def test_normalize_preserves_utc(self):
        """Test that normalized dates have UTC timezone."""
        result = normalize_pdf_date("D:20141208153000Z")
        assert result is not None
        assert result.tzinfo is not None

    def test_normalize_impossible_date(self):
        """Test normalizing impossible date (Feb 30) returns None."""
        result = normalize_pdf_date("D:20140230")
        assert result is None
