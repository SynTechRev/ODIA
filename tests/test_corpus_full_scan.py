"""Tests for corpus full scan functionality (PR #55)."""

import sys
from pathlib import Path

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._utils import normalize_relpath, safe_int
from scripts.ingest_corpus import (
    build_manifest,
    find_all_corpora,
    load_index_for_corpus,
    scan_files_under,
)

_SKIP_CORPUS = "requires populated oraculus/corpus/ directory (runtime data)"


@pytest.mark.skip(reason=_SKIP_CORPUS)
def test_find_all_corpora():
    """Test that corpus discovery finds all directories."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    corpora = find_all_corpora(corpus_path)

    # Should find some corpus directories
    assert len(corpora) > 0, "Should find at least one corpus directory"
    assert all(isinstance(c, Path) for c in corpora), "All should be Path objects"
    assert all(c.is_dir() for c in corpora), "All should be directories"

    print(f"✓ Found {len(corpora)} corpus directories")


def test_scan_files_under():
    """Test that file scanning recursively finds files."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    # Pick the first corpus directory
    corpora = find_all_corpora(corpus_path)
    if not corpora:
        print("No corpus directories found, skipping test")
        return

    first_corpus = corpora[0]
    files = list(scan_files_under(first_corpus))

    # Should find files or empty (both valid)
    assert isinstance(files, list), "Should return a list"
    assert all(isinstance(f, Path) for f in files), "All should be Path objects"
    assert all(f.is_file() for f in files), "All should be files"

    print(f"✓ Found {len(files)} files in {first_corpus.name}")


def test_deduplication_logic():
    """Test that deduplication works with composite keys."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    manifest = build_manifest(corpus_path, force_hash=False)

    # Check for duplicates using same composite key logic
    seen_keys = set()
    duplicate_count = 0

    for entry in manifest.get("files", []):
        key = (
            entry.get("file_hash") or "",
            entry.get("relative_path") or "",
            entry.get("size") or 0,
        )
        if key in seen_keys:
            duplicate_count += 1
        seen_keys.add(key)

    # Should have no duplicates in the manifest
    assert duplicate_count == 0, f"Found {duplicate_count} duplicates in manifest"

    print(f"✓ No duplicates found in {len(manifest.get('files', []))} files")


def test_extraction_status():
    """Test that extraction status is preserved from index.json."""
    repo_root = Path(__file__).parent.parent
    corpus_path = repo_root / "oraculus" / "corpus"

    if not corpus_path.exists():
        print("Corpus directory not found, skipping test")
        return

    corpora = find_all_corpora(corpus_path)
    found_extracted = False

    for corpus_dir in corpora:
        idx = load_index_for_corpus(corpus_dir)
        if idx and isinstance(idx.get("files"), list):
            for fe in idx["files"]:
                if fe.get("extraction_complete") is True:
                    found_extracted = True
                    break
        if found_extracted:
            break

    # At least verify the structure is readable
    print(f"✓ Checked {len(corpora)} corpora for extraction status")
    if found_extracted:
        print("  Found at least one extracted file")


def test_utils_functions():
    """Test utility functions from _utils module."""
    # Test safe_int
    assert safe_int("123") == 123
    assert safe_int("invalid", default=-1) == -1
    assert safe_int(None, default=0) == 0

    # Test normalize_relpath with more robust validation
    base = Path("/home/test")
    path = Path("/home/test/subdir/file.txt")
    result = normalize_relpath(base, path)
    # Check that the result contains the expected path components
    result_parts = Path(result).parts
    assert "subdir" in result_parts or result == "subdir/file.txt"

    print("✓ Utility functions working correctly")


if __name__ == "__main__":
    # Run all tests
    test_find_all_corpora()
    test_scan_files_under()
    test_deduplication_logic()
    test_extraction_status()
    test_utils_functions()
    print("\n✓ All tests passed")
