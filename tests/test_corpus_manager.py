#!/usr/bin/env python3
"""Tests for corpus_manager.py module.

This module provides comprehensive test coverage for the corpus management
utilities used in Phase 20 ingestion schema compliance.
"""

import json

# Add scripts directory to path for imports
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scripts.corpus_manager import (
    FILE_TYPE_TO_SUBDIR,
    HIST_FILES,
    MEETING_DATE_PATTERN,
    REQUIRED_SUBDIRS,
    build_corpus_index,
    create_corpus_directory_structure,
    create_metadata_json,
    get_utc_timestamp,
    validate_corpus_structure,
    verify_hash_consistency,
)


class TestCreateMetadataJson:
    """Tests for create_metadata_json function."""

    def test_creates_valid_metadata(self):
        """Test that create_metadata_json creates valid metadata structure."""
        metadata = create_metadata_json(
            file_name="test.pdf",
            file_type="agenda",
            meeting_date="2024-01-15",
            file_hash="a" * 64,
            text_hash="b" * 64,
        )

        assert metadata["file_name"] == "test.pdf"
        assert metadata["file_type"] == "agenda"
        assert metadata["meeting_date"] == "2024-01-15"
        assert metadata["file_hash"] == "a" * 64
        assert metadata["text_hash"] == "b" * 64
        assert metadata["ingest_version"] == "1.0"
        assert "provenance_flags" in metadata

    def test_sets_recovered_corpus_flag(self):
        """Test that recovered_corpus flag is set correctly."""
        metadata = create_metadata_json(
            file_name="test.pdf",
            file_type="agenda",
            meeting_date="2024-01-15",
            file_hash="a" * 64,
            text_hash="",
            recovered_corpus=True,
        )

        assert metadata["provenance_flags"]["recovered_corpus"] is True

    def test_handles_empty_text_hash(self):
        """Test that empty text_hash is handled correctly."""
        metadata = create_metadata_json(
            file_name="test.pdf",
            file_type="minutes",
            meeting_date="2024-01-15",
            file_hash="a" * 64,
            text_hash="",
        )

        assert metadata["text_hash"] == ""

    def test_sets_manual_entry_flags(self):
        """Test that manual entry flags are set correctly."""
        metadata = create_metadata_json(
            file_name="test.pdf",
            file_type="attachment",
            meeting_date="2024-01-15",
            file_hash="a" * 64,
            text_hash="",
        )

        assert metadata["provenance_flags"]["manual_date_entry"] is True
        assert metadata["provenance_flags"]["manual_source_entry"] is True


class TestValidateCorpusStructure:
    """Tests for validate_corpus_structure function."""

    def test_validates_empty_directory(self):
        """Test validation of a directory with no corpus."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_root = Path(tmp_dir)
            results = validate_corpus_structure(corpus_root)

            # All HIST files should be missing
            for hist_id in HIST_FILES:
                assert results[hist_id]["exists"] is False

    def test_validates_complete_structure(self):
        """Test validation of a complete corpus structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_root = Path(tmp_dir)

            # Create one HIST directory with all subdirs
            hist_path = corpus_root / "HIST-6225"
            hist_path.mkdir()
            for subdir in REQUIRED_SUBDIRS:
                (hist_path / subdir).mkdir()

            results = validate_corpus_structure(corpus_root)

            assert results["HIST-6225"]["exists"] is True
            assert len(results["HIST-6225"]["missing_subdirs"]) == 0

    def test_detects_missing_subdirectories(self):
        """Test detection of missing subdirectories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_root = Path(tmp_dir)

            # Create HIST directory with only some subdirs
            hist_path = corpus_root / "HIST-7722"
            hist_path.mkdir()
            (hist_path / "agendas").mkdir()
            (hist_path / "minutes").mkdir()
            # Missing: staff_reports, attachments, extracted, metadata

            results = validate_corpus_structure(corpus_root)

            assert results["HIST-7722"]["exists"] is True
            missing = results["HIST-7722"]["missing_subdirs"]
            assert "staff_reports" in missing
            assert "attachments" in missing
            assert "extracted" in missing
            assert "metadata" in missing


class TestBuildCorpusIndex:
    """Tests for build_corpus_index function."""

    def test_builds_empty_index(self):
        """Test building index for corpus with no files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_path = Path(tmp_dir)
            (corpus_path / "metadata").mkdir()

            index = build_corpus_index(corpus_path)

            assert index["corpus_id"] == corpus_path.name
            assert "generated_at" in index
            assert index["files"] == []
            assert index["statistics"]["total_files"] == 0

    def test_builds_index_with_metadata_files(self):
        """Test building index with metadata files present."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_path = Path(tmp_dir)
            metadata_path = corpus_path / "metadata"
            metadata_path.mkdir()

            # Create a metadata file
            metadata = {
                "file_name": "test.pdf",
                "file_type": "agenda",
                "meeting_date": "2024-01-15",
                "file_hash": "a" * 64,
                "text_hash": "",
                "ingest_version": "1.0",
                "source_url": "NEEDS_USER_INPUT",
                "provenance_flags": {
                    "manual_date_entry": True,
                    "manual_source_entry": True,
                },
            }
            with open(metadata_path / "test.json", "w") as f:
                json.dump(metadata, f)

            index = build_corpus_index(corpus_path)

            assert index["statistics"]["total_files"] == 1
            assert len(index["files"]) == 1
            assert index["files"][0]["file_name"] == "test.pdf"

    def test_ignores_index_json(self):
        """Test that index.json is ignored when building index."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_path = Path(tmp_dir)
            metadata_path = corpus_path / "metadata"
            metadata_path.mkdir()

            # Create an index.json file that should be ignored
            with open(metadata_path / "index.json", "w") as f:
                json.dump({"old": "index"}, f)

            index = build_corpus_index(corpus_path)

            assert index["statistics"]["total_files"] == 0
            assert len(index["files"]) == 0


class TestVerifyHashConsistency:
    """Tests for verify_hash_consistency function."""

    def test_handles_empty_corpus(self):
        """Test hash verification with empty corpus."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_root = Path(tmp_dir)
            results = verify_hash_consistency(corpus_root)

            assert results["verified"] == 0
            assert len(results["mismatches"]) == 0
            assert len(results["missing_files"]) == 0
            assert len(results["pdfs_without_metadata"]) == 0

    def test_detects_missing_files(self):
        """Test detection of files referenced in metadata but missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_root = Path(tmp_dir)

            # Create HIST directory structure
            hist_path = corpus_root / "HIST-6225"
            hist_path.mkdir()
            for subdir in REQUIRED_SUBDIRS:
                (hist_path / subdir).mkdir()

            # Create metadata referencing a non-existent file
            metadata = {
                "file_name": "missing.pdf",
                "file_type": "agenda",
                "meeting_date": "2024-01-15",
                "file_hash": "a" * 64,
                "text_hash": "",
                "ingest_version": "1.0",
                "source_url": "NEEDS_USER_INPUT",
                "provenance_flags": {
                    "manual_date_entry": True,
                    "manual_source_entry": True,
                },
            }
            metadata_path = hist_path / "metadata"
            with open(metadata_path / "missing.json", "w") as f:
                json.dump(metadata, f)

            results = verify_hash_consistency(corpus_root)

            assert len(results["missing_files"]) == 1
            assert results["missing_files"][0]["file_name"] == "missing.pdf"


class TestCreateCorpusDirectoryStructure:
    """Tests for create_corpus_directory_structure function."""

    def test_creates_all_directories(self):
        """Test that all HIST directories and subdirs are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_root = Path(tmp_dir)
            results = create_corpus_directory_structure(corpus_root)

            # Check all HIST directories were created
            for hist_id in HIST_FILES:
                assert hist_id in results
                hist_path = corpus_root / hist_id
                assert hist_path.exists()

                # Check all subdirs exist
                for subdir in REQUIRED_SUBDIRS:
                    assert (hist_path / subdir).exists()

    def test_reports_correct_subdirs_created(self):
        """Test that results correctly report subdirs created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            corpus_root = Path(tmp_dir)
            results = create_corpus_directory_structure(corpus_root)

            for hist_id in HIST_FILES:
                assert len(results[hist_id]["subdirs_created"]) == len(REQUIRED_SUBDIRS)
                assert results[hist_id]["meeting_date"] == HIST_FILES[hist_id]


class TestMeetingDatePattern:
    """Tests for MEETING_DATE_PATTERN regex."""

    def test_valid_date_formats(self):
        """Test that valid date formats match."""
        valid_dates = [
            "2024-01-15",
            "2014-06-02",
            "2017-11-06",
            "2000-12-31",
        ]
        for date in valid_dates:
            assert MEETING_DATE_PATTERN.match(date) is not None

    def test_invalid_date_formats(self):
        """Test that invalid date formats do not match."""
        invalid_dates = [
            "2024/01/15",
            "01-15-2024",
            "2024-1-15",
            "2024-01-5",
            "24-01-15",
            "2024-01-15T00:00:00",
            "",
        ]
        for date in invalid_dates:
            assert MEETING_DATE_PATTERN.match(date) is None


class TestGetUtcTimestamp:
    """Tests for get_utc_timestamp function."""

    def test_returns_valid_iso_format(self):
        """Test that timestamp is in valid ISO format."""
        timestamp = get_utc_timestamp()

        # Should end with Z
        assert timestamp.endswith("Z")

        # Should be parseable as ISO format
        from datetime import datetime

        # Remove Z and parse
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None


class TestFileTypeMapping:
    """Tests for FILE_TYPE_TO_SUBDIR mapping."""

    def test_all_file_types_have_subdirs(self):
        """Test that all file types map to valid subdirs."""
        for _file_type, subdir in FILE_TYPE_TO_SUBDIR.items():
            assert subdir in REQUIRED_SUBDIRS or subdir == "extracted"

    def test_mapping_is_consistent(self):
        """Test that mapping is consistent with expected types."""
        assert FILE_TYPE_TO_SUBDIR["agenda"] == "agendas"
        assert FILE_TYPE_TO_SUBDIR["minutes"] == "minutes"
        assert FILE_TYPE_TO_SUBDIR["staff_report"] == "staff_reports"
        assert FILE_TYPE_TO_SUBDIR["attachment"] == "attachments"
