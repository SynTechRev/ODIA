"""
Tests for the triage.py script.
Verifies basic manifest creation and update functionality.
"""

import json
import subprocess
import sys

import pytest


def test_manifest_creation_basic(tmp_path):
    """Test basic manifest creation with minimal arguments."""

    doc_id = "TEST001"
    author = "Test User"

    # Create a temporary test file
    test_file = tmp_path / "test_document.pdf"
    test_file.write_text("Test content")

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    # Run triage script
    result = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            doc_id,
            "--path",
            str(test_file),
            "--author",
            author,
            "--manifests-dir",
            str(manifests_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify manifest was created
    manifest_file = manifests_dir / f"{doc_id}.json"
    assert manifest_file.exists(), "Manifest file was not created"

    # Load and verify manifest content
    with open(manifest_file) as f:
        manifest = json.load(f)

    assert manifest["document_id"] == doc_id
    assert manifest["original_path"] == str(test_file)
    assert manifest["uploader"] == "system"
    assert len(manifest["checksum_sha256"]) == 64  # SHA-256 is 64 hex chars
    assert "chain_of_custody" in manifest
    assert len(manifest["chain_of_custody"]) > 0


def test_manifest_add_flag(tmp_path):
    """Test adding a flag to a manifest."""

    doc_id = "TEST002"
    author = "Test User"
    flag_message = "Test flag message"
    severity = "high"

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    # Run triage script with flag
    result = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            doc_id,
            "--author",
            author,
            "--flag",
            flag_message,
            "--severity",
            severity,
            "--category",
            "irb_consent",
            "--manifests-dir",
            str(manifests_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Load and verify manifest
    manifest_file = manifests_dir / f"{doc_id}.json"
    with open(manifest_file) as f:
        manifest = json.load(f)

    assert "flags" in manifest
    assert len(manifest["flags"]) == 1
    assert manifest["flags"][0]["message"] == flag_message
    assert manifest["flags"][0]["severity"] == severity
    assert manifest["flags"][0]["category"] == "irb_consent"
    assert manifest["flags"][0]["author"] == author


def test_manifest_add_note(tmp_path):
    """Test adding a note to a manifest."""

    doc_id = "TEST003"
    author = "Test User"
    note_text = "This is a test note"

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    # Run triage script with note
    result = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            doc_id,
            "--author",
            author,
            "--note",
            note_text,
            "--manifests-dir",
            str(manifests_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Load and verify manifest
    manifest_file = manifests_dir / f"{doc_id}.json"
    with open(manifest_file) as f:
        manifest = json.load(f)

    assert "notes" in manifest
    assert len(manifest["notes"]) == 1
    assert manifest["notes"][0]["note"] == note_text
    assert manifest["notes"][0]["author"] == author


def test_manifest_update_existing(tmp_path):
    """Test updating an existing manifest."""

    doc_id = "TEST004"
    author1 = "User One"
    author2 = "User Two"

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    # Create initial manifest
    result1 = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            doc_id,
            "--author",
            author1,
            "--note",
            "First note",
            "--manifests-dir",
            str(manifests_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result1.returncode == 0

    # Update with second note
    result2 = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            doc_id,
            "--author",
            author2,
            "--note",
            "Second note",
            "--manifests-dir",
            str(manifests_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0

    # Load and verify manifest
    manifest_file = manifests_dir / f"{doc_id}.json"
    with open(manifest_file) as f:
        manifest = json.load(f)

    # Should have two notes now
    assert len(manifest["notes"]) == 2
    assert manifest["notes"][0]["author"] == author1
    assert manifest["notes"][1]["author"] == author2

    # Should have multiple custody entries
    assert len(manifest["chain_of_custody"]) >= 2


def test_checksum_calculation(tmp_path):
    """Test that checksums are calculated correctly."""
    import hashlib

    doc_id = "TEST005"
    author = "Test User"

    # Create test file with known content
    test_file = tmp_path / "test_document.pdf"
    test_content = b"Known test content for checksum"
    test_file.write_bytes(test_content)

    # Calculate expected checksum
    expected_checksum = hashlib.sha256(test_content).hexdigest()

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    # Run triage script
    result = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            doc_id,
            "--path",
            str(test_file),
            "--author",
            author,
            "--manifests-dir",
            str(manifests_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    # Load and verify checksum
    manifest_file = manifests_dir / f"{doc_id}.json"
    with open(manifest_file) as f:
        manifest = json.load(f)

    assert manifest["checksum_sha256"] == expected_checksum


def test_severity_validation():
    """Test that invalid severity levels are rejected."""

    # Try to create manifest with invalid severity
    result = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            "TEST006",
            "--author",
            "Test User",
            "--flag",
            "Test flag",
            "--severity",
            "invalid_severity",
        ],
        capture_output=True,
        text=True,
    )

    # Should fail with non-zero exit code
    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower()


def test_flag_without_severity_fails():
    """Test that adding a flag without severity fails."""

    result = subprocess.run(
        [
            sys.executable,
            "scripts/triage.py",
            "--doc-id",
            "TEST007",
            "--author",
            "Test User",
            "--flag",
            "Test flag",
            # No --severity provided
        ],
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode != 0
    assert "severity" in result.stderr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
