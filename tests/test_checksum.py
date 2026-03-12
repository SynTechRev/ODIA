"""Tests for checksum and provenance tracking module.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import json

import pytest

from oraculus_di_auditor.ingestion.checksum import (
    file_checksum,
    record_provenance,
    verify_integrity,
)


def test_file_checksum_simple(tmp_path):
    """Test calculating checksum for simple file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    checksum = file_checksum(test_file)

    # Expected SHA-256 for "Hello, World!"
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 produces 64 hex characters
    assert (
        checksum == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    )


def test_file_checksum_binary(tmp_path):
    """Test checksum for binary file."""
    test_file = tmp_path / "binary.dat"
    test_file.write_bytes(bytes([0, 1, 2, 3, 4, 5]))

    checksum = file_checksum(test_file)

    assert isinstance(checksum, str)
    assert len(checksum) == 64


def test_file_checksum_large_file(tmp_path):
    """Test checksum for large file (chunked reading)."""
    test_file = tmp_path / "large.txt"

    # Create a file larger than the chunk size (8192 bytes)
    content = "A" * 10000
    test_file.write_text(content)

    checksum = file_checksum(test_file)

    assert isinstance(checksum, str)
    assert len(checksum) == 64


def test_file_checksum_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        file_checksum("/nonexistent/file.txt")


def test_file_checksum_deterministic(tmp_path):
    """Test that checksums are deterministic."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Same content")

    checksum1 = file_checksum(test_file)
    checksum2 = file_checksum(test_file)

    assert checksum1 == checksum2


def test_file_checksum_different_content(tmp_path):
    """Test that different content produces different checksums."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Content A")
    file2.write_text("Content B")

    checksum1 = file_checksum(file1)
    checksum2 = file_checksum(file2)

    assert checksum1 != checksum2


def test_record_provenance_basic(tmp_path):
    """Test basic provenance recording."""
    test_file = tmp_path / "test.xml"
    test_file.write_text("<doc>Test</doc>")

    provenance_log = tmp_path / "provenance.jsonl"

    record = record_provenance(
        path=test_file,
        source_url="http://example.com/test.xml",
        output=provenance_log,
        jurisdiction="federal",
    )

    # Check returned record
    assert record["file"] == str(test_file.absolute())
    assert "sha256" in record
    assert record["source"] == "http://example.com/test.xml"
    assert record["jurisdiction"] == "federal"
    assert record["size"] == len("<doc>Test</doc>")

    # Check file was created
    assert provenance_log.exists()

    # Check file content
    with open(provenance_log) as f:
        logged_record = json.loads(f.read())
        assert logged_record == record


def test_record_provenance_with_metadata(tmp_path):
    """Test provenance recording with custom metadata."""
    test_file = tmp_path / "statute.xml"
    test_file.write_text("<statute>Content</statute>")

    provenance_log = tmp_path / "provenance.jsonl"

    record = record_provenance(
        path=test_file,
        source_url="http://example.com/statute.xml",
        output=provenance_log,
        jurisdiction="california",
        metadata={"title": "42", "section": "1983"},
    )

    assert record["metadata"]["title"] == "42"
    assert record["metadata"]["section"] == "1983"


def test_record_provenance_append(tmp_path):
    """Test that multiple records are appended."""
    file1 = tmp_path / "file1.xml"
    file2 = tmp_path / "file2.xml"

    file1.write_text("Content 1")
    file2.write_text("Content 2")

    provenance_log = tmp_path / "provenance.jsonl"

    record_provenance(file1, "source1", provenance_log, "federal")
    record_provenance(file2, "source2", provenance_log, "federal")

    # Check both records are in the file
    with open(provenance_log) as f:
        lines = f.readlines()
        assert len(lines) == 2

        record1 = json.loads(lines[0])
        record2 = json.loads(lines[1])

        assert "file1.xml" in record1["file"]
        assert "file2.xml" in record2["file"]


def test_record_provenance_file_not_found(tmp_path):
    """Test error handling for missing file."""
    provenance_log = tmp_path / "provenance.jsonl"

    with pytest.raises(FileNotFoundError):
        record_provenance(
            path="/nonexistent/file.xml",
            source_url="http://example.com",
            output=provenance_log,
            jurisdiction="federal",
        )


def test_verify_integrity_all_verified(tmp_path):
    """Test verification when all files are verified."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Content 1")
    file2.write_text("Content 2")

    provenance_log = tmp_path / "provenance.jsonl"

    record_provenance(file1, "source1", provenance_log, "federal")
    record_provenance(file2, "source2", provenance_log, "federal")

    results = verify_integrity(provenance_log)

    assert results["total"] == 2
    assert results["verified"] == 2
    assert results["failed"] == 0
    assert results["missing"] == 0
    assert len(results["details"]) == 2


def test_verify_integrity_modified_file(tmp_path):
    """Test verification when file is modified."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Original content")

    provenance_log = tmp_path / "provenance.jsonl"
    record_provenance(test_file, "source", provenance_log, "federal")

    # Modify the file
    test_file.write_text("Modified content")

    results = verify_integrity(provenance_log)

    assert results["total"] == 1
    assert results["verified"] == 0
    assert results["failed"] == 1
    assert results["missing"] == 0

    detail = results["details"][0]
    assert detail["status"] == "failed"
    assert detail["expected_hash"] != detail["actual_hash"]


def test_verify_integrity_missing_file(tmp_path):
    """Test verification when file is missing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Content")

    provenance_log = tmp_path / "provenance.jsonl"
    record_provenance(test_file, "source", provenance_log, "federal")

    # Delete the file
    test_file.unlink()

    results = verify_integrity(provenance_log)

    assert results["total"] == 1
    assert results["verified"] == 0
    assert results["failed"] == 0
    assert results["missing"] == 1

    detail = results["details"][0]
    assert detail["status"] == "missing"
    assert "actual_hash" not in detail


def test_verify_integrity_mixed_results(tmp_path):
    """Test verification with mixed results."""
    file1 = tmp_path / "verified.txt"
    file2 = tmp_path / "modified.txt"
    file3 = tmp_path / "missing.txt"

    file1.write_text("Verified")
    file2.write_text("Original")
    file3.write_text("Will be deleted")

    provenance_log = tmp_path / "provenance.jsonl"

    record_provenance(file1, "source1", provenance_log, "federal")
    record_provenance(file2, "source2", provenance_log, "federal")
    record_provenance(file3, "source3", provenance_log, "federal")

    # Modify file2 and delete file3
    file2.write_text("Modified")
    file3.unlink()

    results = verify_integrity(provenance_log)

    assert results["total"] == 3
    assert results["verified"] == 1
    assert results["failed"] == 1
    assert results["missing"] == 1


def test_verify_integrity_empty_log(tmp_path):
    """Test verification with empty provenance log."""
    provenance_log = tmp_path / "empty.jsonl"
    provenance_log.touch()

    results = verify_integrity(provenance_log)

    assert results["total"] == 0
    assert results["verified"] == 0
    assert results["failed"] == 0
    assert results["missing"] == 0


def test_verify_integrity_log_not_found(tmp_path):
    """Test error handling for missing provenance log."""
    with pytest.raises(FileNotFoundError):
        verify_integrity(tmp_path / "nonexistent.jsonl")
