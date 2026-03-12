"""Tests for corpus ingestion scanner."""

import sys
from pathlib import Path

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest_corpus import generate_manifest, scan_corpus

_SKIP_CORPUS = "requires populated oraculus/corpus/ directory (runtime data)"


@pytest.mark.skip(reason=_SKIP_CORPUS)
def test_scan_corpus():
    """Test that corpus scanning finds entries."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    entries = scan_corpus(corpus_path)

    # Should find 36 corpus entries
    assert len(entries) > 0, "Should find corpus entries"
    assert all(isinstance(e, dict) for e in entries), "All entries should be dicts"
    assert all("corpus_id" in e for e in entries), "All entries should have corpus_id"
    assert all("files" in e for e in entries), "All entries should have files array"

    print(f"✓ Found {len(entries)} corpus entries")


def test_generate_manifest():
    """Test manifest generation."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    entries = scan_corpus(corpus_path)
    manifest = generate_manifest(entries)

    # Verify manifest structure
    assert "manifest_version" in manifest
    assert "generated_at" in manifest
    assert "total_corpora" in manifest
    assert "corpora" in manifest
    assert "total_files" in manifest

    assert manifest["total_corpora"] == len(entries)
    assert isinstance(manifest["corpora"], list)

    total_files = manifest["total_files"]
    total_corpora = manifest["total_corpora"]
    print(f"✓ Manifest has {total_files} files across {total_corpora} corpora")


@pytest.mark.skip(reason=_SKIP_CORPUS)
def test_corpus_file_counts():
    """Test that some corpora have files."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    entries = scan_corpus(corpus_path)
    manifest = generate_manifest(entries)

    # At least some corpora should have files
    corpora_with_files = [c for c in manifest["corpora"] if c["file_count"] > 0]
    assert len(corpora_with_files) > 0, "At least some corpora should have files"

    print(f"✓ {len(corpora_with_files)} corpora have files")


def test_manifest_files_array():
    """Test that manifest has top-level files array."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    entries = scan_corpus(corpus_path)
    manifest = generate_manifest(entries)

    assert "files" in manifest, "Manifest should have files array"
    assert isinstance(manifest["files"], list), "Files should be a list"

    # Should match total_files count
    assert len(manifest["files"]) == manifest["total_files"], (
        f"Files array length ({len(manifest['files'])}) should match "
        f"total_files ({manifest['total_files']})"
    )

    print(f"✓ Manifest files array has {len(manifest['files'])} entries")


if __name__ == "__main__":
    print("Running corpus ingestion tests...")
    print()

    test_scan_corpus()
    test_generate_manifest()
    test_corpus_file_counts()
    test_manifest_files_array()

    print()
    print("All tests passed!")
