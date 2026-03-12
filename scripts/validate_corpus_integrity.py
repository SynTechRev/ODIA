#!/usr/bin/env python3
"""Validate corpus integrity and structure compliance.

This script validates that corpus directories meet Phase 20 ingestion
schema requirements.

Usage:
    python scripts/validate_corpus_integrity.py [--corpus-root CORPUS_ROOT]

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
    HIST_FILES,
    MAX_DISPLAYED_ERRORS,
    MEETING_DATE_PATTERN,
    REQUIRED_SUBDIRS,
    validate_corpus_structure,
    verify_hash_consistency,
)


def validate_metadata_schema(corpus_root: Path) -> dict:
    """Validate that metadata files conform to Phase 20 schema.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with validation results
    """
    required_fields = [
        "file_name",
        "file_type",
        "meeting_date",
        "source_url",
        "file_hash",
        "text_hash",
        "ingest_version",
        "provenance_flags",
    ]

    valid_file_types = ["agenda", "minutes", "attachment", "staff_report"]

    results = {
        "valid": 0,
        "invalid": 0,
        "errors": [],
    }

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        metadata_path = corpus_path / "metadata"

        if not metadata_path.exists():
            continue

        for meta_file in metadata_path.glob("*.json"):
            if meta_file.name == "index.json":
                continue

            try:
                with open(meta_file) as f:
                    metadata = json.load(f)
            except json.JSONDecodeError as e:
                results["invalid"] += 1
                results["errors"].append(
                    {
                        "file": str(meta_file),
                        "error": f"Invalid JSON: {e}",
                    }
                )
                continue

            # Check required fields
            missing_fields = []
            for field in required_fields:
                if field not in metadata:
                    missing_fields.append(field)

            if missing_fields:
                results["invalid"] += 1
                results["errors"].append(
                    {
                        "file": str(meta_file),
                        "error": f"Missing required fields: {missing_fields}",
                    }
                )
                continue

            # Validate file_type
            if metadata.get("file_type") not in valid_file_types:
                results["invalid"] += 1
                results["errors"].append(
                    {
                        "file": str(meta_file),
                        "error": f"Invalid file_type: {metadata.get('file_type')}",
                    }
                )
                continue

            # Validate meeting_date format (YYYY-MM-DD) using regex
            meeting_date = metadata.get("meeting_date", "")
            if not MEETING_DATE_PATTERN.match(meeting_date):
                results["invalid"] += 1
                results["errors"].append(
                    {
                        "file": str(meta_file),
                        "error": f"Invalid meeting_date format: {meeting_date}",
                    }
                )
                continue

            # Validate provenance_flags
            prov_flags = metadata.get("provenance_flags", {})
            if not isinstance(prov_flags, dict):
                results["invalid"] += 1
                results["errors"].append(
                    {
                        "file": str(meta_file),
                        "error": "provenance_flags must be an object",
                    }
                )
                continue

            results["valid"] += 1

    return results


def main():
    """Validate corpus integrity."""
    parser = argparse.ArgumentParser(
        description="Validate corpus integrity and Phase 20 schema compliance"
    )
    parser.add_argument(
        "--corpus-root",
        type=str,
        default="oraculus/corpus",
        help="Root directory for corpus files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed validation errors",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any validation error",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()

    print("=" * 70)
    print("CORPUS INTEGRITY VALIDATION")
    print("=" * 70)

    if not corpus_root.exists():
        print(f"\n[FAIL] Corpus root not found: {corpus_root}")
        return 1

    exit_code = 0

    # Step 1: Validate directory structure
    print("\n[1/3] Validating directory structure...")
    structure_results = validate_corpus_structure(corpus_root)

    structure_pass = 0
    structure_fail = 0
    for hist_id, status in structure_results.items():
        if status["exists"] and not status["missing_subdirs"]:
            structure_pass += 1
            print(f"  [OK] {hist_id}: All {len(REQUIRED_SUBDIRS)} subdirectories present")
        elif status["exists"]:
            structure_fail += 1
            print(f"  ⚠ {hist_id}: Missing subdirectories: {status['missing_subdirs']}")
        else:
            structure_fail += 1
            print(f"  [FAIL] {hist_id}: Directory not found")

    print(f"\n  Summary: {structure_pass} passed, {structure_fail} failed")

    if structure_fail > 0 and args.strict:
        exit_code = 1

    # Step 2: Validate metadata schema
    print("\n[2/3] Validating metadata schema compliance...")
    schema_results = validate_metadata_schema(corpus_root)

    print(f"  Valid metadata files: {schema_results['valid']}")
    print(f"  Invalid metadata files: {schema_results['invalid']}")

    if args.verbose and schema_results["errors"]:
        print("\n  Errors:")
        for error in schema_results["errors"][:MAX_DISPLAYED_ERRORS]:
            print(f"    - {error['file']}: {error['error']}")
        if len(schema_results["errors"]) > MAX_DISPLAYED_ERRORS:
            remaining = len(schema_results["errors"]) - MAX_DISPLAYED_ERRORS
            print(f"    ... and {remaining} more")

    if schema_results["invalid"] > 0 and args.strict:
        exit_code = 1

    # Step 3: Verify hash consistency
    print("\n[3/3] Verifying hash consistency...")
    hash_results = verify_hash_consistency(corpus_root)

    print(f"  Files verified: {hash_results['verified']}")
    print(f"  Hash mismatches: {len(hash_results['mismatches'])}")
    print(f"  Missing files: {len(hash_results['missing_files'])}")
    print(f"  PDFs without metadata: {len(hash_results['pdfs_without_metadata'])}")

    if args.verbose:
        if hash_results["mismatches"]:
            print("\n  Hash mismatches:")
            for mismatch in hash_results["mismatches"][:5]:
                print(f"    - {mismatch['hist_id']}/{mismatch['file_name']}")
            if len(hash_results["mismatches"]) > 5:
                print(f"    ... and {len(hash_results['mismatches']) - 5} more")

        if hash_results["pdfs_without_metadata"]:
            print("\n  PDFs without metadata:")
            for orphan in hash_results["pdfs_without_metadata"][:5]:
                print(f"    - {orphan['hist_id']}/{orphan['file_name']}")
            if len(hash_results["pdfs_without_metadata"]) > 5:
                remaining = len(hash_results["pdfs_without_metadata"]) - 5
                print(f"    ... and {remaining} more")

    if hash_results["mismatches"] and args.strict:
        exit_code = 1

    # Final summary
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("[OK] VALIDATION PASSED")
    else:
        print("[FAIL] VALIDATION FAILED")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
