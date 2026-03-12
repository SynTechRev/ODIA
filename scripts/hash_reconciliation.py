#!/usr/bin/env python3
"""Hash reconciliation for corpus files.

This script verifies that file hashes in metadata match the actual
file contents, and can repair inconsistencies.

Usage:
    python scripts/hash_reconciliation.py [--corpus-root CORPUS_ROOT] [--repair]

Author: GitHub Copilot Agent
Date: 2025-11-25
"""

import argparse
import json
import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import (
    FILE_TYPE_TO_SUBDIR,
    HIST_FILES,
    calculate_file_hash,
    calculate_text_hash,
    verify_hash_consistency,
)


def reconcile_hashes(corpus_root: Path, repair: bool = False) -> dict:
    """Reconcile file hashes with metadata.

    Args:
        corpus_root: Root path for corpus directories
        repair: If True, update metadata with correct hashes

    Returns:
        Dictionary with reconciliation results
    """
    results = {
        "verified": 0,
        "repaired": 0,
        "mismatches": [],
        "errors": [],
    }

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        metadata_path = corpus_path / "metadata"
        extracted_path = corpus_path / "extracted"

        if not metadata_path.exists():
            continue

        for meta_file in metadata_path.glob("*.json"):
            if meta_file.name == "index.json":
                continue

            try:
                with open(meta_file) as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                results["errors"].append(
                    {
                        "file": str(meta_file),
                        "error": str(e),
                    }
                )
                continue

            file_name = metadata.get("file_name", "")
            file_type = metadata.get("file_type", "")
            stored_file_hash = metadata.get("file_hash", "")
            stored_text_hash = metadata.get("text_hash", "")

            subdir = FILE_TYPE_TO_SUBDIR.get(file_type, "")
            if not subdir or not file_name:
                continue

            file_path = corpus_path / subdir / file_name
            text_path = extracted_path / (Path(file_name).stem + ".txt")

            needs_repair = False

            # Check file hash
            if file_path.exists():
                actual_file_hash = calculate_file_hash(file_path)
                if stored_file_hash and actual_file_hash != stored_file_hash:
                    results["mismatches"].append(
                        {
                            "hist_id": hist_id,
                            "file": file_name,
                            "field": "file_hash",
                            "stored": stored_file_hash,
                            "actual": actual_file_hash,
                        }
                    )
                    if repair:
                        metadata["file_hash"] = actual_file_hash
                        needs_repair = True
                elif not stored_file_hash:
                    # Missing hash, add it
                    if repair:
                        metadata["file_hash"] = actual_file_hash
                        needs_repair = True
                else:
                    results["verified"] += 1

            # Check text hash
            if text_path.exists():
                actual_text_hash = calculate_text_hash(text_path)
                if stored_text_hash and actual_text_hash != stored_text_hash:
                    results["mismatches"].append(
                        {
                            "hist_id": hist_id,
                            "file": file_name,
                            "field": "text_hash",
                            "stored": stored_text_hash,
                            "actual": actual_text_hash,
                        }
                    )
                    if repair:
                        metadata["text_hash"] = actual_text_hash
                        needs_repair = True
                elif not stored_text_hash:
                    # Missing hash, add it
                    if repair:
                        metadata["text_hash"] = actual_text_hash
                        needs_repair = True
                else:
                    results["verified"] += 1

            if needs_repair:
                with open(meta_file, "w") as f:
                    json.dump(metadata, f, indent=2)
                    f.write("\n")  # Add trailing newline for POSIX compliance
                results["repaired"] += 1

    return results


def main():
    """Run hash reconciliation."""
    parser = argparse.ArgumentParser(
        description="Reconcile file hashes with metadata records"
    )
    parser.add_argument(
        "--corpus-root",
        type=str,
        default="oraculus/corpus",
        help="Root directory for corpus files",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Repair mismatched hashes by updating metadata",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed mismatch information",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()

    print("=" * 70)
    print("HASH RECONCILIATION")
    print("=" * 70)

    if not corpus_root.exists():
        print(f"\n[FAIL] Corpus root not found: {corpus_root}")
        return 1

    # First, check current state
    print("\nChecking hash consistency...")
    initial = verify_hash_consistency(corpus_root)
    print(f"  Files with valid hashes: {initial['verified']}")
    print(f"  Hash mismatches: {len(initial['mismatches'])}")

    if args.repair:
        print("\nRepairing hashes...")
        results = reconcile_hashes(corpus_root, repair=True)
        print(f"  Files repaired: {results['repaired']}")

        if results["errors"]:
            print(f"  Errors encountered: {len(results['errors'])}")
            if args.verbose:
                for error in results["errors"]:
                    print(f"    - {error['file']}: {error['error']}")
    else:
        print("\n(Use --repair to fix mismatches)")

    if args.verbose and initial["mismatches"]:
        print("\nHash mismatches detected:")
        for mismatch in initial["mismatches"]:
            print(f"  - {mismatch['hist_id']}/{mismatch['file_name']}")
            print(f"    Expected: {mismatch['expected_hash'][:16]}...")
            print(f"    Actual:   {mismatch['actual_hash'][:16]}...")

    print("\n" + "=" * 70)
    print("RECONCILIATION COMPLETE")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
