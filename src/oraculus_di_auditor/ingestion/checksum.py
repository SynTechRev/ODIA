"""Checksum calculation and provenance tracking for file integrity.

Provides SHA-256 hashing and provenance record management for
cryptographically verifiable data integrity.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import hashlib
import json
from pathlib import Path
from typing import Any, TypedDict


def file_checksum(path: str | Path) -> str:
    """Calculate SHA-256 checksum for a file.

    Args:
        path: Path to the file

    Returns:
        Hexadecimal SHA-256 hash string

    Raises:
        FileNotFoundError: If the file does not exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def record_provenance(
    path: str | Path,
    source_url: str,
    output: str | Path,
    jurisdiction: str = "unknown",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record provenance information for a file.

    Args:
        path: Path to the file
        source_url: URL or description of the source
        output: Path to the provenance log file (JSONL format)
        jurisdiction: Legal jurisdiction (e.g., 'federal', 'california')
        metadata: Additional metadata to include

    Returns:
        Provenance record dictionary

    Raises:
        FileNotFoundError: If the input file does not exist
    """
    path = Path(path)
    output = Path(output)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Calculate checksum
    checksum = file_checksum(path)

    # Build provenance record
    record = {
        "file": str(path.absolute()),
        "sha256": checksum,
        "source": source_url,
        "jurisdiction": jurisdiction,
        "size": path.stat().st_size,
    }

    # Add optional metadata
    if metadata:
        record["metadata"] = metadata

    # Append to provenance log
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record


class VerifyResults(TypedDict):
    total: int
    verified: int
    failed: int
    missing: int
    details: list[dict[str, Any]]


def verify_integrity(provenance_file: str | Path) -> VerifyResults:
    """Verify file integrity against recorded checksums.

    Args:
        provenance_file: Path to the provenance log file (JSONL format)

    Returns:
        Dictionary with verification results:
        - total: Total number of records
        - verified: Number of verified files
        - failed: Number of failed verifications
        - missing: Number of missing files
        - details: List of verification details
    """
    provenance_file = Path(provenance_file)

    if not provenance_file.exists():
        raise FileNotFoundError(f"Provenance file not found: {provenance_file}")

    results: VerifyResults = {
        "total": 0,
        "verified": 0,
        "failed": 0,
        "missing": 0,
        "details": [],
    }

    with open(provenance_file) as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            results["total"] += 1

            file_path = Path(record["file"])
            expected_hash = record["sha256"]

            detail = {
                "file": str(file_path),
                "expected_hash": expected_hash,
                "status": None,
            }

            if not file_path.exists():
                results["missing"] += 1
                detail["status"] = "missing"
            else:
                actual_hash = file_checksum(file_path)
                detail["actual_hash"] = actual_hash

                if actual_hash == expected_hash:
                    results["verified"] += 1
                    detail["status"] = "verified"
                else:
                    results["failed"] += 1
                    detail["status"] = "failed"

            results["details"].append(detail)

    return results
