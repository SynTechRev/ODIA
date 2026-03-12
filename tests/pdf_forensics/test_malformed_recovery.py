#!/usr/bin/env python3
"""Tests for malformed PDF recovery functionality.

This module tests error handling for malformed PDFs.
Total: 5 tests
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import (
    extract_pdf_metadata,
    parse_xmp_metadata,
)


class TestMalformedPdfRecovery:
    """Tests for malformed PDF error recovery."""

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader")
    def test_recover_from_pdf_read_error(self, mock_reader, tmp_path):
        """Test recovery from PDF read error."""
        from scripts.pdf_forensics.pdf_metadata_miner import PdfReadError

        mock_reader.side_effect = PdfReadError("Corrupted PDF")

        test_file = tmp_path / "corrupted.pdf"
        test_file.write_bytes(b"%PDF-1.4 corrupted content")

        result = extract_pdf_metadata(test_file)
        assert result["extraction_success"] is False
        assert "PDF read error" in result["extraction_error"]

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader")
    def test_recover_from_unexpected_exception(self, mock_reader, tmp_path):
        """Test recovery from unexpected exception."""
        mock_reader.side_effect = ValueError("Unexpected error")

        test_file = tmp_path / "broken.pdf"
        test_file.write_bytes(b"%PDF-1.4 broken content")

        result = extract_pdf_metadata(test_file)
        assert result["extraction_success"] is False
        assert "Unexpected error" in result["extraction_error"]

    def test_recover_from_empty_file(self, tmp_path):
        """Test recovery from empty file."""
        test_file = tmp_path / "empty.pdf"
        test_file.write_bytes(b"")

        with patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader") as mock_reader:
            mock_reader.side_effect = Exception("Empty file")

            result = extract_pdf_metadata(test_file)
            assert result["extraction_success"] is False

    def test_recover_from_non_pdf(self, tmp_path):
        """Test recovery from non-PDF file."""
        test_file = tmp_path / "not_a_pdf.pdf"
        test_file.write_text("This is just text, not a PDF")

        with patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader") as mock_reader:
            mock_reader.side_effect = Exception("Not a valid PDF")

            result = extract_pdf_metadata(test_file)
            assert result["extraction_success"] is False

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader")
    def test_partial_metadata_extraction(self, mock_reader, tmp_path):
        """Test partial metadata extraction when some fields fail."""
        mock_instance = MagicMock()
        mock_instance.metadata = MagicMock()
        mock_instance.metadata.producer = "Valid Producer"
        mock_instance.metadata.creator = None  # Missing
        mock_instance.metadata.author = None  # Missing
        mock_instance.metadata.title = None
        mock_instance.metadata.subject = None
        mock_instance.metadata.creation_date = None
        mock_instance.metadata.modification_date = None
        mock_instance.pages = []
        mock_instance.is_encrypted = False
        mock_instance.xmp_metadata = None
        mock_reader.return_value = mock_instance

        test_file = tmp_path / "partial.pdf"
        test_file.write_bytes(b"%PDF-1.4 partial content")

        result = extract_pdf_metadata(test_file)
        assert result["extraction_success"] is True
        assert result["info_dict"]["producer"] == "Valid Producer"
        assert result["info_dict"]["creator"] is None


class TestMalformedXmpRecovery:
    """Tests for malformed XMP error recovery."""

    def test_recover_from_invalid_utf8(self):
        """Test recovery from invalid UTF-8 in XMP."""
        # Invalid UTF-8 bytes
        xmp_bytes = b"<?xpacket begin='\xff\xfe'?></xpacket>"
        result = parse_xmp_metadata(xmp_bytes)
        # Should not crash, should return some result
        assert isinstance(result, dict)

    def test_recover_from_truncated_xml(self):
        """Test recovery from truncated XML in XMP."""
        xmp_str = '<?xpacket begin="..."?><x:xmpmeta><incomplete'
        result = parse_xmp_metadata(xmp_str)
        assert result["present"] is True
        assert result["truncated"] is True

    def test_recover_from_empty_xmp_bytes(self):
        """Test recovery from empty XMP bytes."""
        result = parse_xmp_metadata(b"")
        assert result["present"] is False

    def test_recover_from_non_xml_content(self):
        """Test recovery from non-XML content in XMP field."""
        xmp_str = "This is not XML at all, just random text"
        result = parse_xmp_metadata(xmp_str)
        assert result["present"] is True
        assert result["packet_count"] == 0
