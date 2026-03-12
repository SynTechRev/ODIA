#!/usr/bin/env python3
"""Tests for vendor extraction functionality.

This module tests the vendor_map_extractor.py functions.
Total: 20 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.vendor_map_extractor import (
    _detect_vendor_in_text,
    _extract_context,
    _parse_amount,
    build_vendor_index,
    detect_vendor_aliases,
    extract_contract_amounts,
    extract_vendors_from_filenames,
    extract_vendors_from_metadata,
)


class TestDetectVendorInText:
    """Tests for _detect_vendor_in_text function."""

    def test_detect_axon(self):
        """Test detection of Axon vendor."""
        text = "This contract is with Axon for body cameras."
        result = _detect_vendor_in_text(text)
        assert "Axon" in result

    def test_detect_flock(self):
        """Test detection of Flock Safety vendor."""
        text = "Flock Safety provides ALPR systems."
        result = _detect_vendor_in_text(text)
        assert "Flock Safety" in result

    def test_detect_tmobile(self):
        """Test detection of T-Mobile vendor."""
        text = "T-Mobile cellular infrastructure contract."
        result = _detect_vendor_in_text(text)
        assert "T-Mobile" in result

    def test_detect_multiple_vendors(self):
        """Test detection of multiple vendors in same text."""
        text = "Working with Axon and T-Mobile for public safety."
        result = _detect_vendor_in_text(text)
        assert "Axon" in result
        assert "T-Mobile" in result

    def test_case_insensitive(self):
        """Test case-insensitive detection."""
        text = "AXON body cameras and FLOCK systems"
        result = _detect_vendor_in_text(text)
        assert "Axon" in result
        assert "Flock Safety" in result

    def test_no_vendor_found(self):
        """Test no vendor found in text."""
        text = "General meeting minutes about budget."
        result = _detect_vendor_in_text(text)
        assert len(result) == 0


class TestExtractContext:
    """Tests for _extract_context function."""

    def test_extract_context_found(self):
        """Test context extraction when vendor found."""
        text = "The city approved a contract with Axon for $500,000."
        context = _extract_context(text, "Axon")
        assert "Axon" in context
        assert "$500,000" in context

    def test_extract_context_not_found(self):
        """Test context extraction when vendor not in text."""
        text = "General meeting about infrastructure."
        context = _extract_context(text, "UnknownVendor")
        assert context == ""

    def test_context_truncation(self):
        """Test context is truncated appropriately."""
        text = "A" * 100 + " Axon contract " + "B" * 200
        context = _extract_context(text, "Axon")
        assert len(context) <= 250


class TestParseAmount:
    """Tests for _parse_amount function."""

    def test_parse_simple_amount(self):
        """Test parsing simple dollar amount."""
        result = _parse_amount("50000")
        assert result == 50000.0

    def test_parse_with_commas(self):
        """Test parsing amount with commas."""
        result = _parse_amount("1,234,567")
        assert result == 1234567.0

    def test_parse_with_decimals(self):
        """Test parsing amount with decimals."""
        result = _parse_amount("1234.56")
        assert result == 1234.56

    def test_parse_with_dollar_sign(self):
        """Test parsing amount with dollar sign."""
        result = _parse_amount("$50,000")
        assert result == 50000.0

    def test_parse_million(self):
        """Test parsing million suffix."""
        result = _parse_amount("1.5 million")
        assert result == 1500000.0

    def test_parse_invalid(self):
        """Test parsing invalid amount."""
        result = _parse_amount("not a number")
        assert result is None

    def test_parse_empty(self):
        """Test parsing empty string."""
        result = _parse_amount("")
        assert result is None


class TestExtractVendorsFromMetadata:
    """Tests for extract_vendors_from_metadata function."""

    def test_empty_data(self):
        """Test with empty data."""
        data = {"metadata_files": {}}
        result = extract_vendors_from_metadata(data)
        assert result == []

    def test_vendor_field(self):
        """Test extraction from vendor field."""
        data = {
            "metadata_files": {
                "HIST-1234/file.json": {
                    "vendor": "Axon",
                }
            }
        }
        result = extract_vendors_from_metadata(data)
        assert len(result) == 1
        assert result[0]["value"] == "Axon"


class TestExtractVendorsFromFilenames:
    """Tests for extract_vendors_from_filenames function."""

    def test_detect_vendor_in_filename(self):
        """Test vendor detection in filename."""
        data = {
            "attachment_files": [{"hist_id": "HIST-1234", "filename": "Axon Quote.pdf"}]
        }
        result = extract_vendors_from_filenames(data)
        assert len(result) == 1
        assert result[0]["vendor_name"] == "Axon"

    def test_no_vendor_in_filename(self):
        """Test no vendor found in filename."""
        data = {
            "attachment_files": [
                {"hist_id": "HIST-1234", "filename": "Budget Report.pdf"}
            ]
        }
        result = extract_vendors_from_filenames(data)
        assert len(result) == 0


class TestBuildVendorIndex:
    """Tests for build_vendor_index function."""

    def test_build_index_basic(self):
        """Test basic index building."""
        vendors = [
            {"vendor_name": "Axon", "hist_id": "HIST-1234", "source": "filename"},
            {"vendor_name": "Axon", "hist_id": "HIST-5678", "source": "text"},
        ]
        corpora = {"HIST-1234": "2020-01-15", "HIST-5678": "2021-03-20"}
        result = build_vendor_index(vendors, corpora)

        assert "Axon" in result
        assert result["Axon"]["appearance_count"] == 2
        assert "2020" in result["Axon"]["years"]
        assert "2021" in result["Axon"]["years"]

    def test_build_index_empty(self):
        """Test building empty index."""
        result = build_vendor_index([], {})
        assert result == {}


class TestDetectVendorAliases:
    """Tests for detect_vendor_aliases function."""

    def test_detect_known_aliases(self):
        """Test detection of known vendor aliases."""
        vendors = [
            {"vendor_name": "Axon", "hist_id": "HIST-1234"},
        ]
        result = detect_vendor_aliases(vendors)
        assert "Axon" in result
        assert "axon" in result["Axon"]
        assert "taser" in result["Axon"]


class TestExtractContractAmounts:
    """Tests for extract_contract_amounts function."""

    def test_extract_from_metadata_field(self):
        """Test extraction from metadata amount field."""
        data = {
            "metadata_files": {
                "HIST-1234/file.json": {
                    "contract_amount": "50000",
                }
            },
            "extracted_text_cache": {},
        }
        result = extract_contract_amounts(data)
        assert len(result) >= 1
        assert any(r.get("parsed_amount") == 50000.0 for r in result)
