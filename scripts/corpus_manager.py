#!/usr/bin/env python3
"""Corpus management utilities for Phase 20 ingestion schema compliance.

This module provides utilities for:
- Creating and validating corpus directory structures
- Managing metadata JSON files
- Rebuilding indexes
- Cross-platform normalization
- Hash reconciliation

Author: GitHub Copilot Agent
Date: 2025-11-25
"""

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Corpus file definitions with canonical dates.
# Load from a corpus_manifest.json config file, or provide as empty default.
# To configure for your jurisdiction, create a JSON file with
# {"ITEM-ID": "YYYY-MM-DD", ...} mapping corpus IDs to meeting dates.
HIST_FILES: dict[str, str] = {}


def load_corpus_manifest(manifest_path: Path | str | None = None) -> dict[str, str]:
    """Load corpus manifest from a JSON config file.

    Args:
        manifest_path: Path to JSON file mapping corpus IDs to meeting dates.
                       If None, looks for 'corpus_manifest.json' in the config/ directory.

    Returns:
        Dictionary mapping corpus IDs to date strings (YYYY-MM-DD).
    """
    global HIST_FILES
    if manifest_path is None:
        default_path = Path(__file__).parent.parent / "config" / "corpus_manifest.json"
        if default_path.exists():
            manifest_path = default_path
        else:
            return HIST_FILES
    manifest_path = Path(manifest_path)
    if manifest_path.exists():
        with open(manifest_path) as f:
            HIST_FILES = json.load(f)
    return HIST_FILES


# Required subdirectories for each corpus
REQUIRED_SUBDIRS = [
    "agendas",
    "minutes",
    "staff_reports",
    "attachments",
    "extracted",
    "metadata",
]

# Mapping from file types to subdirectory names
FILE_TYPE_TO_SUBDIR = {
    "agenda": "agendas",
    "minutes": "minutes",
    "staff_report": "staff_reports",
    "attachment": "attachments",
}

# Pattern for validating meeting date format (YYYY-MM-DD)
MEETING_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Maximum number of errors to display in verbose output
MAX_DISPLAYED_ERRORS = 10


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix.

    Returns:
        ISO 8601 formatted timestamp string
    """
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal SHA-256 hash string
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def calculate_text_hash(text_path: Path) -> str:
    """Calculate SHA-256 hash of extracted text file.

    Args:
        text_path: Path to the text file

    Returns:
        Hexadecimal SHA-256 hash string, or empty string if file not found
    """
    if not text_path.exists():
        return ""
    return calculate_file_hash(text_path)


def create_corpus_directory_structure(corpus_root: Path) -> dict[str, Any]:
    """Create directory structure for all HIST corpora.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with creation status for each HIST directory
    """
    results = {}
    for hist_id in HIST_FILES:
        hist_path = corpus_root / hist_id
        hist_path.mkdir(parents=True, exist_ok=True)

        subdirs_created = []
        for subdir in REQUIRED_SUBDIRS:
            subdir_path = hist_path / subdir
            subdir_path.mkdir(exist_ok=True)
            # Create .gitkeep to preserve empty directories
            gitkeep = subdir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
            subdirs_created.append(subdir)

        results[hist_id] = {
            "path": str(hist_path),
            "subdirs_created": subdirs_created,
            "meeting_date": HIST_FILES[hist_id],
        }

    return results


def validate_corpus_structure(corpus_root: Path) -> dict[str, Any]:
    """Validate that all required directories exist.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with validation results for each HIST directory
    """
    results = {}
    for hist_id in HIST_FILES:
        hist_path = corpus_root / hist_id
        validation = {
            "exists": hist_path.exists(),
            "missing_subdirs": [],
            "pdf_count": 0,
            "metadata_count": 0,
            "extracted_count": 0,
        }

        if hist_path.exists():
            for subdir in REQUIRED_SUBDIRS:
                subdir_path = hist_path / subdir
                if not subdir_path.exists():
                    validation["missing_subdirs"].append(subdir)

            # Count files
            for ext in ["*.pdf", "*.PDF"]:
                for subdir in ["agendas", "minutes", "staff_reports", "attachments"]:
                    subdir_path = hist_path / subdir
                    if subdir_path.exists():
                        validation["pdf_count"] += len(list(subdir_path.glob(ext)))

            metadata_path = hist_path / "metadata"
            if metadata_path.exists():
                validation["metadata_count"] = len(list(metadata_path.glob("*.json")))

            extracted_path = hist_path / "extracted"
            if extracted_path.exists():
                validation["extracted_count"] = len(list(extracted_path.glob("*.txt")))

        results[hist_id] = validation

    return results


def create_metadata_json(
    file_name: str,
    file_type: str,
    meeting_date: str,
    source_url: str = "NEEDS_USER_INPUT",
    file_hash: str = "",
    text_hash: str = "",
    recovered_corpus: bool = False,
    file_id: str = "",
    meeting_type: str = "City Council Regular Meeting",
    jurisdiction: str = "",
) -> dict[str, Any]:
    """Create Phase 20 compliant metadata JSON.

    Args:
        file_name: Name of the file
        file_type: Type of file (agenda, minutes, attachment, staff_report)
        meeting_date: Meeting date in YYYY-MM-DD format
        source_url: Source URL (placeholder until user provides)
        file_hash: SHA-256 hash of the file
        text_hash: SHA-256 hash of extracted text
        recovered_corpus: Whether this is a recovered corpus
        file_id: Unique identifier for the file
        meeting_type: Type of meeting
        jurisdiction: Jurisdiction of the meeting

    Returns:
        Metadata dictionary
    """
    metadata = {
        "file_name": file_name,
        "file_type": file_type,
        "meeting_date": meeting_date,
        "meeting_type": meeting_type,
        "jurisdiction": jurisdiction,
        "source_url": source_url,
        "file_hash": file_hash,
        "text_hash": text_hash,
        "document_titles": [],
        "document_urls": {},
        "ingest_version": "1.0",
        "provenance_flags": {
            "manual_date_entry": True,
            "manual_source_entry": True,
        },
    }

    if file_id:
        metadata["file_id"] = file_id

    if recovered_corpus:
        metadata["provenance_flags"]["recovered_corpus"] = True

    return metadata


def scan_and_generate_metadata(corpus_root: Path) -> dict[str, Any]:
    """Scan corpus directories and generate metadata for PDFs.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with metadata generation results
    """
    results = {}

    for hist_id, meeting_date in HIST_FILES.items():
        hist_path = corpus_root / hist_id
        metadata_path = hist_path / "metadata"
        extracted_path = hist_path / "extracted"

        hist_results = {
            "meeting_date": meeting_date,
            "files_processed": 0,
            "metadata_created": 0,
            "is_recovered": hist_id == "HIST-11740",
        }

        if not hist_path.exists():
            results[hist_id] = hist_results
            continue

        # Iterate through subdirectories and map to file types
        subdir_to_type = {v: k for k, v in FILE_TYPE_TO_SUBDIR.items()}

        for subdir, file_type in subdir_to_type.items():
            subdir_path = hist_path / subdir
            if not subdir_path.exists():
                continue

            for pdf_file in list(subdir_path.glob("*.pdf")) + list(
                subdir_path.glob("*.PDF")
            ):
                hist_results["files_processed"] += 1

                # Check if metadata already exists
                metadata_file = metadata_path / (pdf_file.stem + ".json")
                existing_metadata = None
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            existing_metadata = json.load(f)
                    except (json.JSONDecodeError, OSError):
                        existing_metadata = None

                # Calculate current hashes
                current_file_hash = calculate_file_hash(pdf_file)
                text_file = extracted_path / (pdf_file.stem + ".txt")
                current_text_hash = calculate_text_hash(text_file)

                # Preserve existing hash values if they match the current file
                if existing_metadata:
                    # Use existing file_hash if it matches current file
                    existing_file_hash = existing_metadata.get("file_hash", "")
                    if existing_file_hash == current_file_hash:
                        file_hash = existing_file_hash
                    else:
                        file_hash = current_file_hash

                    # Use existing text_hash if it matches current text
                    existing_text_hash = existing_metadata.get("text_hash", "")
                    if existing_text_hash == current_text_hash:
                        text_hash = existing_text_hash
                    else:
                        text_hash = current_text_hash
                else:
                    file_hash = current_file_hash
                    text_hash = current_text_hash

                # Generate metadata
                metadata = create_metadata_json(
                    file_name=pdf_file.name,
                    file_type=file_type,
                    meeting_date=meeting_date,
                    file_hash=file_hash,
                    text_hash=text_hash,
                    recovered_corpus=(hist_id == "HIST-11740"),
                )

                # Write metadata file
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)
                    f.write("\n")  # Add trailing newline for POSIX compliance
                hist_results["metadata_created"] += 1

        results[hist_id] = hist_results

    return results


def build_corpus_index(corpus_path: Path) -> dict[str, Any]:
    """Build index.json for a single corpus.

    Args:
        corpus_path: Path to the corpus directory

    Returns:
        Index dictionary
    """
    index = {
        "corpus_id": corpus_path.name,
        "generated_at": get_utc_timestamp(),
        "files": [],
        "statistics": {
            "total_files": 0,
            "by_type": {},
        },
    }

    metadata_path = corpus_path / "metadata"
    if not metadata_path.exists():
        return index

    for meta_file in metadata_path.glob("*.json"):
        if meta_file.name == "index.json":
            continue
        try:
            with open(meta_file) as f:
                metadata = json.load(f)
            index["files"].append(metadata)
            index["statistics"]["total_files"] += 1

            file_type = metadata.get("file_type", "unknown")
            index["statistics"]["by_type"][file_type] = (
                index["statistics"]["by_type"].get(file_type, 0) + 1
            )
        except (json.JSONDecodeError, KeyError):
            continue

    return index


def rebuild_all_indexes(corpus_root: Path) -> dict[str, Any]:
    """Rebuild indexes for all corpora and global index.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with rebuild results
    """
    results = {
        "corpus_indexes": {},
        "global_index": None,
    }

    global_index = {
        "generated_at": get_utc_timestamp(),
        "corpora": [],
        "total_files": 0,
    }

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        # Build corpus index
        corpus_index = build_corpus_index(corpus_path)

        # Write corpus index
        index_file = corpus_path / "index.json"
        with open(index_file, "w") as f:
            json.dump(corpus_index, f, indent=2)
            f.write("\n")  # Add trailing newline for POSIX compliance

        results["corpus_indexes"][hist_id] = {
            "total_files": corpus_index["statistics"]["total_files"],
            "by_type": corpus_index["statistics"]["by_type"],
        }

        # Add to global index
        global_index["corpora"].append(
            {
                "corpus_id": hist_id,
                "meeting_date": HIST_FILES[hist_id],
                "total_files": corpus_index["statistics"]["total_files"],
            }
        )
        global_index["total_files"] += corpus_index["statistics"]["total_files"]

    # Write global index
    global_index_file = corpus_root / "index.json"
    with open(global_index_file, "w") as f:
        json.dump(global_index, f, indent=2)
        f.write("\n")  # Add trailing newline for POSIX compliance

    results["global_index"] = {
        "total_corpora": len(global_index["corpora"]),
        "total_files": global_index["total_files"],
    }

    return results


def check_cross_platform_compatibility(corpus_root: Path) -> dict[str, Any]:
    """Check for cross-platform compatibility issues.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with compatibility check results
    """
    results = {
        "line_ending_issues": [],
        "permission_issues": [],
        "path_case_issues": [],
    }

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        # Check file permissions
        for subdir in REQUIRED_SUBDIRS:
            subdir_path = corpus_path / subdir
            if subdir_path.exists():
                if not os.access(subdir_path, os.R_OK | os.W_OK):
                    results["permission_issues"].append(
                        {
                            "path": str(subdir_path),
                            "hist_id": hist_id,
                            "issue": "read/write permission denied",
                        }
                    )

        # Check metadata files for line endings
        metadata_path = corpus_path / "metadata"
        if metadata_path.exists():
            for json_file in metadata_path.glob("*.json"):
                try:
                    with open(json_file, "rb") as f:
                        content = f.read()
                    if b"\r\n" in content:
                        results["line_ending_issues"].append(
                            {
                                "path": str(json_file),
                                "issue": "Windows line endings (CRLF) detected",
                            }
                        )
                except OSError:
                    # Skip files that cannot be read (permissions, etc.)
                    pass

    return results


def normalize_line_endings(corpus_root: Path) -> dict[str, int]:
    """Normalize line endings to Unix-style (LF) in all text files.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with normalization statistics
    """
    stats = {"files_checked": 0, "files_normalized": 0}

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        # Normalize JSON files
        metadata_path = corpus_path / "metadata"
        if metadata_path.exists():
            for json_file in metadata_path.glob("*.json"):
                stats["files_checked"] += 1
                try:
                    with open(json_file, "rb") as f:
                        content = f.read()
                    if b"\r\n" in content:
                        normalized = content.replace(b"\r\n", b"\n")
                        with open(json_file, "wb") as f:
                            f.write(normalized)
                        stats["files_normalized"] += 1
                except OSError:
                    # Skip files that cannot be read/written (permissions, etc.)
                    pass

        # Normalize extracted text files
        extracted_path = corpus_path / "extracted"
        if extracted_path.exists():
            for txt_file in extracted_path.glob("*.txt"):
                stats["files_checked"] += 1
                try:
                    with open(txt_file, "rb") as f:
                        content = f.read()
                    if b"\r\n" in content:
                        normalized = content.replace(b"\r\n", b"\n")
                        with open(txt_file, "wb") as f:
                            f.write(normalized)
                        stats["files_normalized"] += 1
                except OSError:
                    # Skip files that cannot be read/written (permissions, etc.)
                    pass

    return stats


def verify_hash_consistency(corpus_root: Path) -> dict[str, Any]:
    """Verify hash consistency between files and metadata.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with verification results
    """
    results = {
        "verified": 0,
        "mismatches": [],
        "missing_files": [],
        "pdfs_without_metadata": [],
    }

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        metadata_path = corpus_path / "metadata"
        if not metadata_path.exists():
            continue

        # Track files we've seen metadata for
        metadata_files = set()

        for meta_file in metadata_path.glob("*.json"):
            if meta_file.name == "index.json":
                continue

            try:
                with open(meta_file) as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            file_name = metadata.get("file_name", "")
            file_type = metadata.get("file_type", "")
            expected_hash = metadata.get("file_hash", "")

            # Map file type to subdirectory
            subdir = FILE_TYPE_TO_SUBDIR.get(file_type, "")
            if not subdir:
                continue

            file_path = corpus_path / subdir / file_name
            metadata_files.add(file_name)

            if not file_path.exists():
                if expected_hash:  # Only flag if we expected a file
                    results["missing_files"].append(
                        {
                            "hist_id": hist_id,
                            "file_name": file_name,
                            "expected_at": str(file_path),
                        }
                    )
                continue

            actual_hash = calculate_file_hash(file_path)
            if expected_hash and actual_hash != expected_hash:
                results["mismatches"].append(
                    {
                        "hist_id": hist_id,
                        "file_name": file_name,
                        "expected_hash": expected_hash,
                        "actual_hash": actual_hash,
                    }
                )
            elif expected_hash:  # Only count as verified if hash exists and matches
                results["verified"] += 1

        # Check for orphan PDFs (PDFs without metadata)
        for subdir in FILE_TYPE_TO_SUBDIR.values():
            subdir_path = corpus_path / subdir
            if subdir_path.exists():
                for pdf_file in list(subdir_path.glob("*.pdf")) + list(
                    subdir_path.glob("*.PDF")
                ):
                    if pdf_file.name not in metadata_files:
                        results["pdfs_without_metadata"].append(
                            {
                                "hist_id": hist_id,
                                "file_name": pdf_file.name,
                                "path": str(pdf_file),
                            }
                        )

    return results


def generate_summary_report(corpus_root: Path) -> str:
    """Generate a summary report for all corpus operations.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Formatted summary report string
    """
    report_lines = [
        "=" * 80,
        "CORPUS INTEGRATION SUMMARY REPORT",
        f"Generated: {get_utc_timestamp()}",
        "=" * 80,
        "",
    ]

    # Validate structure
    validation = validate_corpus_structure(corpus_root)
    total_pdfs = 0
    total_metadata = 0

    report_lines.append("CORPUS STATUS:")
    report_lines.append("-" * 40)

    for hist_id, status in validation.items():
        if status["exists"]:
            status_str = "PASS" if not status["missing_subdirs"] else "PARTIAL"
            total_pdfs += status["pdf_count"]
            total_metadata += status["metadata_count"]
        else:
            status_str = "MISSING"

        report_lines.append(
            f"  {hist_id} ({HIST_FILES[hist_id]}): {status_str}"
            f" - PDFs: {status['pdf_count']}, Metadata: {status['metadata_count']}"
        )

    report_lines.append("")
    report_lines.append("TOTALS:")
    report_lines.append("-" * 40)
    report_lines.append(f"  Total PDFs indexed: {total_pdfs}")
    report_lines.append(f"  Total metadata files: {total_metadata}")
    report_lines.append("")

    # Check for missing URLs
    report_lines.append("MISSING SOURCE URLs (require user input):")
    report_lines.append("-" * 40)
    missing_urls = []
    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        metadata_path = corpus_path / "metadata"
        if metadata_path.exists():
            for meta_file in metadata_path.glob("*.json"):
                if meta_file.name == "index.json":
                    continue
                try:
                    with open(meta_file) as f:
                        metadata = json.load(f)
                    if metadata.get("source_url") == "NEEDS_USER_INPUT":
                        missing_urls.append(f"  {hist_id}/{meta_file.name}")
                except (json.JSONDecodeError, OSError):
                    # Skip malformed or unreadable metadata files
                    pass

    if missing_urls:
        report_lines.extend(missing_urls[:20])  # Limit to 20 entries
        if len(missing_urls) > 20:
            report_lines.append(f"  ... and {len(missing_urls) - 20} more")
    else:
        report_lines.append("  None")

    report_lines.append("")

    # Cross-platform check
    compat = check_cross_platform_compatibility(corpus_root)
    report_lines.append("CROSS-PLATFORM COMPATIBILITY:")
    report_lines.append("-" * 40)
    if compat["permission_issues"]:
        report_lines.append(f"  Permission issues: {len(compat['permission_issues'])}")
        for issue in compat["permission_issues"]:
            report_lines.append(
                f"    - {issue['hist_id']}: {issue['path']} ({issue['issue']})"
            )
    else:
        report_lines.append("  No permission issues detected")

    if compat["line_ending_issues"]:
        report_lines.append(
            f"  Line ending issues: {len(compat['line_ending_issues'])}"
        )
    else:
        report_lines.append("  No line ending issues detected")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)


def main():
    """Main entry point for corpus management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Corpus management for Phase 20 ingestion schema compliance"
    )
    parser.add_argument(
        "--corpus-root",
        type=str,
        default="oraculus/corpus",
        help="Root directory for corpus files",
    )
    parser.add_argument(
        "--action",
        choices=[
            "create",
            "validate",
            "generate-metadata",
            "rebuild-index",
            "check-compat",
            "normalize",
            "verify-hash",
            "report",
            "full",
        ],
        default="full",
        help="Action to perform",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()

    if args.action == "create" or args.action == "full":
        print("Creating corpus directory structure...")
        results = create_corpus_directory_structure(corpus_root)
        for hist_id, info in results.items():
            print(f"  {hist_id}: {len(info['subdirs_created'])} subdirs created")

    if args.action == "validate" or args.action == "full":
        print("\nValidating corpus structure...")
        results = validate_corpus_structure(corpus_root)
        for hist_id, status in results.items():
            is_ok = status["exists"] and not status["missing_subdirs"]
            status_str = "OK" if is_ok else "ISSUES"
            print(f"  {hist_id}: {status_str}")

    if args.action == "generate-metadata" or args.action == "full":
        print("\nGenerating metadata for PDFs...")
        results = scan_and_generate_metadata(corpus_root)
        for hist_id, info in results.items():
            print(
                f"  {hist_id}: {info['files_processed']} PDFs, "
                f"{info['metadata_created']} metadata files"
            )

    if args.action == "rebuild-index" or args.action == "full":
        print("\nRebuilding indexes...")
        results = rebuild_all_indexes(corpus_root)
        for hist_id, info in results["corpus_indexes"].items():
            print(f"  {hist_id}: {info['total_files']} files indexed")
        if results["global_index"]:
            print(
                f"  Global index: {results['global_index']['total_corpora']} corpora, "
                f"{results['global_index']['total_files']} total files"
            )

    if args.action == "check-compat" or args.action == "full":
        print("\nChecking cross-platform compatibility...")
        results = check_cross_platform_compatibility(corpus_root)
        print(f"  Permission issues: {len(results['permission_issues'])}")
        print(f"  Line ending issues: {len(results['line_ending_issues'])}")

    if args.action == "normalize" or args.action == "full":
        print("\nNormalizing line endings...")
        stats = normalize_line_endings(corpus_root)
        print(
            f"  Files checked: {stats['files_checked']}, "
            f"normalized: {stats['files_normalized']}"
        )

    if args.action == "verify-hash" or args.action == "full":
        print("\nVerifying hash consistency...")
        results = verify_hash_consistency(corpus_root)
        print(f"  Verified: {results['verified']}")
        print(f"  Mismatches: {len(results['mismatches'])}")
        print(f"  Missing files: {len(results['missing_files'])}")
        print(f"  PDFs without metadata: {len(results['pdfs_without_metadata'])}")

    if args.action == "report" or args.action == "full":
        print("\n" + generate_summary_report(corpus_root))


if __name__ == "__main__":
    main()
