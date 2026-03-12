"""Tests for corpus manifest generation."""

import json
import sys
from pathlib import Path

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

_SKIP_REASON = "requires generated transparency_release artifacts (run pipeline first)"


@pytest.mark.skip(reason=_SKIP_REASON)
def test_manifest_exists():
    """Test that corpus manifest file exists."""
    repo_root = Path(__file__).parent.parent
    manifest_path = repo_root / "transparency_release" / "corpus_manifest.json"

    assert manifest_path.exists(), f"Corpus manifest should exist at {manifest_path}"
    print(f"✓ Corpus manifest exists at {manifest_path}")


def test_manifest_structure():
    """Test corpus manifest structure."""
    repo_root = Path(__file__).parent.parent
    manifest_path = repo_root / "transparency_release" / "corpus_manifest.json"

    if not manifest_path.exists():
        print("Manifest not found, skipping test")
        return

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # Check required fields
    required_fields = [
        "manifest_version",
        "generated_at",
        "description",
        "corpus_range",
        "total_corpora",
        "corpora",
        "total_files",
        "years_covered",
    ]

    for field in required_fields:
        assert field in manifest, f"Manifest should have '{field}' field"

    print("✓ Manifest has all required fields")


def test_manifest_corpora():
    """Test corpus entries in manifest."""
    repo_root = Path(__file__).parent.parent
    manifest_path = repo_root / "transparency_release" / "corpus_manifest.json"

    if not manifest_path.exists():
        print("Manifest not found, skipping test")
        return

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # Check corpora structure
    assert isinstance(manifest["corpora"], list), "Corpora should be a list"
    assert len(manifest["corpora"]) > 0, "Should have at least one corpus"

    # Check corpus entry structure
    for corpus in manifest["corpora"]:
        assert "corpus_id" in corpus, "Corpus should have corpus_id"
        assert "meeting_date" in corpus, "Corpus should have meeting_date"
        assert "year" in corpus, "Corpus should have year"
        assert "files" in corpus, "Corpus should have files array"
        assert "file_count" in corpus, "Corpus should have file_count"
        assert isinstance(corpus["files"], list), "Files should be a list"

    print(f"✓ Manifest has {len(manifest['corpora'])} corpus entries")


def test_manifest_files():
    """Test file entries in manifest."""
    repo_root = Path(__file__).parent.parent
    manifest_path = repo_root / "transparency_release" / "corpus_manifest.json"

    if not manifest_path.exists():
        print("Manifest not found, skipping test")
        return

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # Count files across all corpora
    total_from_corpora = sum(c["file_count"] for c in manifest["corpora"])

    # Should match total_files
    assert manifest["total_files"] == total_from_corpora, (
        f"total_files ({manifest['total_files']}) should match "
        f"sum of file_count ({total_from_corpora})"
    )

    # Check if top-level files array exists
    if "files" in manifest:
        assert (
            len(manifest["files"]) == manifest["total_files"]
        ), "Files array length should match total_files"

    print(f"✓ Manifest has {manifest['total_files']} total files")


def test_manifest_no_empty_required_arrays():
    """Test that the old schema bug is fixed.

    Files arrays should exist even if empty.
    """
    repo_root = Path(__file__).parent.parent
    manifest_path = repo_root / "transparency_release" / "corpus_manifest.json"

    if not manifest_path.exists():
        print("Manifest not found, skipping test")
        return

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # All corpora should have a files array (even if empty)
    for corpus in manifest["corpora"]:
        assert (
            "files" in corpus
        ), f"Corpus {corpus['corpus_id']} should have files array"
        assert isinstance(
            corpus["files"], list
        ), f"Corpus {corpus['corpus_id']} files should be a list"

    print("✓ All corpora have files arrays (schema fix verified)")


if __name__ == "__main__":
    print("Running corpus manifest tests...")
    print()

    test_manifest_exists()
    test_manifest_structure()
    test_manifest_corpora()
    test_manifest_files()
    test_manifest_no_empty_required_arrays()

    print()
    print("All tests passed!")
