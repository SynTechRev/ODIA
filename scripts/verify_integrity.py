#!/usr/bin/env python3
"""Verify file integrity using provenance checksums.

This script reads a provenance log file and verifies that all recorded
files still match their SHA-256 checksums.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.ingestion.checksum import verify_integrity


def main():
    """Verify file integrity from provenance log."""
    parser = argparse.ArgumentParser(
        description="Verify file integrity using provenance checksums"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/provenance.jsonl",
        help="Path to provenance log file (JSONL format)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed verification results",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("File Integrity Verification")
    print("=" * 70)

    provenance_file = Path(args.input)
    if not provenance_file.exists():
        print(f"\n✗ Provenance file not found: {provenance_file}")
        print("  Run ingestion with --format xml to generate provenance records")
        return 1

    print(f"\nVerifying files from: {provenance_file}")

    try:
        results = verify_integrity(provenance_file)
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        return 1

    # Print summary
    print("\n" + "=" * 70)
    print("Verification Results")
    print("=" * 70)
    print(f"Total records:   {results['total']}")
    print(f"✓ Verified:      {results['verified']}")
    print(f"✗ Failed:        {results['failed']}")
    print(f"⚠ Missing:       {results['missing']}")

    # Calculate success rate
    if results["total"] > 0:
        success_rate = (results["verified"] / results["total"]) * 100
        print(f"\nSuccess rate:    {success_rate:.1f}%")

    # Show detailed results if requested
    if args.verbose:
        print("\n" + "=" * 70)
        print("Detailed Results")
        print("=" * 70)

        for detail in results["details"]:
            status_symbol = {
                "verified": "✓",
                "failed": "✗",
                "missing": "⚠",
            }
            symbol = status_symbol.get(detail["status"], "?")
            print(f"\n{symbol} {detail['file']}")
            print(f"  Status: {detail['status']}")
            print(f"  Expected: {detail['expected_hash']}")
            if "actual_hash" in detail:
                print(f"  Actual:   {detail['actual_hash']}")

    # Exit with error if any files failed verification
    if results["failed"] > 0 or results["missing"] > 0:
        print("\n⚠ Some files failed verification or are missing")
        return 1

    print("\n✓ All files verified successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
