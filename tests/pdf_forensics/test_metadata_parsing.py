#!/usr/bin/env python3
"""Tests for PDF metadata parsing functionality.

This module tests the extract_pdf_metadata and related functions.
Total: 20 tests
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.pdf_forensics.pdf_metadata_miner import (
    compute_file_hashes,
    extract_pdf_metadata,
    parse_xmp_metadata,
)


class TestComputeFileHashes:
    """Tests for compute_file_hashes function."""

    def test_compute_hashes_valid_file(self, tmp_path):
        """Test hash computation on valid file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        result = compute_file_hashes(test_file)
        assert "md5" in result
        assert "sha256" in result
        assert len(result["md5"]) == 32
        assert len(result["sha256"]) == 64

    def test_compute_hashes_empty_file(self, tmp_path):
        """Test hash computation on empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        result = compute_file_hashes(test_file)
        assert result["md5"] != ""
        assert result["sha256"] != ""

    def test_compute_hashes_nonexistent_file(self, tmp_path):
        """Test hash computation on nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"
        result = compute_file_hashes(test_file)
        assert result["md5"] == ""
        assert result["sha256"] == ""

    def test_compute_hashes_consistent(self, tmp_path):
        """Test that same content produces same hashes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Consistent content")
        result1 = compute_file_hashes(test_file)
        result2 = compute_file_hashes(test_file)
        assert result1["md5"] == result2["md5"]
        assert result1["sha256"] == result2["sha256"]

    def test_compute_hashes_different_content(self, tmp_path):
        """Test that different content produces different hashes."""
        test_file1 = tmp_path / "test1.txt"
        test_file2 = tmp_path / "test2.txt"
        test_file1.write_text("Content A")
        test_file2.write_text("Content B")
        result1 = compute_file_hashes(test_file1)
        result2 = compute_file_hashes(test_file2)
        assert result1["md5"] != result2["md5"]
        assert result1["sha256"] != result2["sha256"]


class TestParseXmpMetadata:
    """Tests for parse_xmp_metadata function."""

    def test_parse_empty_xmp(self):
        """Test parsing empty XMP data."""
        result = parse_xmp_metadata(None)
        assert result["present"] is False

    def test_parse_xmp_bytes(self):
        """Test parsing XMP from bytes."""
        xmp_bytes = b'<?xpacket begin="..."?><x:xmpmeta></x:xmpmeta><?xpacket end="w"?>'
        result = parse_xmp_metadata(xmp_bytes)
        assert result["present"] is True
        assert result["packet_count"] == 1

    def test_parse_xmp_string(self):
        """Test parsing XMP from string."""
        xmp_str = '<?xpacket begin="..."?><x:xmpmeta></x:xmpmeta><?xpacket end="w"?>'
        result = parse_xmp_metadata(xmp_str)
        assert result["present"] is True

    def test_detect_truncated_xmp(self):
        """Test detection of truncated XMP."""
        xmp_str = '<?xpacket begin="..."?><x:xmpmeta></x:xmpmeta>'
        result = parse_xmp_metadata(xmp_str)
        assert result["truncated"] is True
        assert result["malformed"] is True

    def test_detect_multiple_packets(self):
        """Test detection of multiple XMP packets."""
        xmp_str = (
            '<?xpacket begin="..."?><?xpacket end="w"?>'
            '<?xpacket begin="..."?><?xpacket end="w"?>'
        )
        result = parse_xmp_metadata(xmp_str)
        assert result["packet_count"] == 2

    def test_extract_create_date(self):
        """Test extraction of CreateDate field."""
        xmp_str = "<xmp:CreateDate>2014-12-08T15:30:00</xmp:CreateDate>"
        result = parse_xmp_metadata(xmp_str)
        assert result["parsed"].get("CreateDate") == "2014-12-08T15:30:00"

    def test_extract_modify_date(self):
        """Test extraction of ModifyDate field."""
        xmp_str = "<xmp:ModifyDate>2015-01-15T10:00:00</xmp:ModifyDate>"
        result = parse_xmp_metadata(xmp_str)
        assert result["parsed"].get("ModifyDate") == "2015-01-15T10:00:00"

    def test_extract_producer(self):
        """Test extraction of Producer field."""
        xmp_str = "<pdf:Producer>Adobe Acrobat Pro DC</pdf:Producer>"
        result = parse_xmp_metadata(xmp_str)
        assert "Adobe Acrobat Pro DC" in result["parsed"].get("Producer", "")

    def test_detect_pdfa_namespace(self):
        """Test detection of PDF/A namespace."""
        xmp_str = 'xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"'
        result = parse_xmp_metadata(xmp_str)
        assert "pdfaid" in result["namespaces_found"]

    def test_extract_pdfa_conformance(self):
        """Test extraction of PDF/A conformance."""
        xmp_str = (
            'xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"'
            "<pdfaid:part>1</pdfaid:part>"
            "<pdfaid:conformance>A</pdfaid:conformance>"
        )
        result = parse_xmp_metadata(xmp_str)
        assert result.get("pdfa_conformance") == "pdf/a-1a"


class TestExtractPdfMetadata:
    """Tests for extract_pdf_metadata function."""

    def test_extract_nonexistent_file(self):
        """Test extraction from nonexistent file."""
        result = extract_pdf_metadata(Path("/nonexistent/file.pdf"))
        assert result["extraction_success"] is False
        assert result["extraction_error"] is not None

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader")
    def test_extract_valid_pdf(self, mock_reader):
        """Test extraction from valid PDF with mocked reader."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.metadata = MagicMock()
        mock_instance.metadata.producer = "Adobe Acrobat"
        mock_instance.metadata.creator = "Word"
        mock_instance.metadata.author = "Test Author"
        mock_instance.metadata.title = "Test Title"
        mock_instance.metadata.subject = "Test Subject"
        mock_instance.metadata.creation_date = "2014-12-08"
        mock_instance.metadata.modification_date = "2015-01-15"
        mock_instance.pages = [MagicMock()]
        mock_instance.is_encrypted = False
        mock_instance.xmp_metadata = None
        mock_reader.return_value = mock_instance

        # Create a dummy file
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 dummy content")
            temp_path = Path(f.name)

        try:
            result = extract_pdf_metadata(temp_path)
            assert result["extraction_success"] is True
            assert result["info_dict"]["producer"] == "Adobe Acrobat"
        finally:
            temp_path.unlink()

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader")
    def test_extract_encrypted_pdf(self, mock_reader):
        """Test extraction from encrypted PDF."""
        mock_instance = MagicMock()
        mock_instance.metadata = None
        mock_instance.pages = []
        mock_instance.is_encrypted = True
        mock_instance.xmp_metadata = None
        mock_reader.return_value = mock_instance

        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 encrypted dummy")
            temp_path = Path(f.name)

        try:
            result = extract_pdf_metadata(temp_path)
            assert result["structure"]["is_encrypted"] is True
        finally:
            temp_path.unlink()

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader")
    def test_extract_page_count(self, mock_reader):
        """Test extraction of page count."""
        mock_instance = MagicMock()
        mock_instance.metadata = None
        mock_instance.pages = [MagicMock() for _ in range(5)]
        mock_instance.is_encrypted = False
        mock_instance.xmp_metadata = None
        mock_reader.return_value = mock_instance

        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 dummy")
            temp_path = Path(f.name)

        try:
            result = extract_pdf_metadata(temp_path)
            assert result["structure"]["page_count"] == 5
        finally:
            temp_path.unlink()

    def test_extract_file_hashes(self, tmp_path):
        """Test that file hashes are computed."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        with patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader") as mock_reader:
            mock_instance = MagicMock()
            mock_instance.metadata = None
            mock_instance.pages = []
            mock_instance.is_encrypted = False
            mock_instance.xmp_metadata = None
            mock_reader.return_value = mock_instance

            result = extract_pdf_metadata(test_file)
            assert result["hashes"]["md5"] != ""
            assert result["hashes"]["sha256"] != ""

    def test_extract_file_size(self, tmp_path):
        """Test that file size is computed."""
        test_file = tmp_path / "test.pdf"
        content = b"%PDF-1.4 test content" * 100
        test_file.write_bytes(content)

        with patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader") as mock_reader:
            mock_instance = MagicMock()
            mock_instance.metadata = None
            mock_instance.pages = []
            mock_instance.is_encrypted = False
            mock_instance.xmp_metadata = None
            mock_reader.return_value = mock_instance

            result = extract_pdf_metadata(test_file)
            assert result["file_size"] == len(content)

    def test_extract_file_name(self, tmp_path):
        """Test that file name is captured."""
        test_file = tmp_path / "my_document.pdf"
        test_file.write_bytes(b"%PDF-1.4 test")

        with patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader") as mock_reader:
            mock_instance = MagicMock()
            mock_instance.metadata = None
            mock_instance.pages = []
            mock_instance.is_encrypted = False
            mock_instance.xmp_metadata = None
            mock_reader.return_value = mock_instance

            result = extract_pdf_metadata(test_file)
            assert result["file_name"] == "my_document.pdf"

    @patch("scripts.pdf_forensics.pdf_metadata_miner.PdfReader", None)
    def test_extract_without_pypdf(self, tmp_path):
        """Test extraction when pypdf is not available."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test")
        result = extract_pdf_metadata(test_file)
        assert result["extraction_success"] is False
        assert "not available" in result.get("extraction_error", "")
