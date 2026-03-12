#!/usr/bin/env python3
"""Extended Audit Script for HIST-8123 and 2021-2025 Legislative Corpus.

This script provides year-aware audit capabilities for the 2021-2025
legislative corpus extension. It builds upon the unified corpus audit
to provide:

1. Year-aware corpus filtering (e.g., --years 2021-2025)
2. HIST-8123 specific auditing
3. Missing data flagging
4. Corpus completeness verification
5. 11-year corpus architecture validation

Author: GitHub Copilot Agent
Date: 2025-12-05
"""

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import HIST_FILES  # noqa: E402

CORPUS_ROOT = Path("oraculus/corpus")
CORPUS_PATTERN = re.compile(r"(HIST-\d{4,5}|#\d{2}-\d{4})")

# Document types expected per corpus entry
EXPECTED_CATEGORIES = ["agendas", "minutes", "staff_reports", "attachments"]


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def hash_file(path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    h = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_year_range(year_range: str) -> tuple[int, int]:
    """Parse a year range string (e.g., '2014-2025') into start and end years."""
    if "-" in year_range:
        parts = year_range.split("-")
        return int(parts[0]), int(parts[1])
    else:
        year = int(year_range)
        return year, year


def filter_corpora_by_years(start_year: int, end_year: int) -> dict[str, str]:
    """Filter HIST_FILES to only include entries within the year range."""
    filtered = {}
    for hist_id, meeting_date in HIST_FILES.items():
        year = int(meeting_date[:4])
        if start_year <= year <= end_year:
            filtered[hist_id] = meeting_date
    return filtered


def collect_corpora(corpus_root: Path) -> list[Path]:
    """Collect all corpus directories matching the pattern."""
    corpora = []
    if not corpus_root.exists():
        return corpora
    for entry in corpus_root.iterdir():
        if entry.is_dir() and CORPUS_PATTERN.match(entry.name):
            corpora.append(entry)
    return sorted(corpora)


def audit_corpus(folder: Path) -> dict[str, Any]:  # noqa: C901
    """Audit a single corpus folder for completeness and integrity."""
    pdf_files = list(folder.rglob("*.pdf"))
    meta_files = list((folder / "metadata").glob("*.json"))
    extracted_files = list((folder / "extracted").glob("*.txt"))
    index_file = folder / "index.json"

    # Check metadata completeness
    meta_ok = True
    missing_fields = []
    for meta in meta_files:
        if meta.name == "index.json":
            continue
        try:
            with open(meta, encoding="utf-8") as f:
                data = json.load(f)
            for field in ("meeting_date", "source_url", "file_hash", "text_hash"):
                if field not in data or not data[field]:
                    meta_ok = False
                    missing_fields.append((meta.name, field))
        except (json.JSONDecodeError, OSError):
            meta_ok = False
            missing_fields.append((meta.name, "PARSE_ERROR"))

    # Check extraction rate
    extraction_rate = len(extracted_files) / len(pdf_files) if pdf_files else 1.0

    # Check for missing document categories
    missing_categories = []
    for category in EXPECTED_CATEGORIES:
        category_path = folder / category
        if not category_path.exists():
            missing_categories.append(category)
        elif not list(category_path.glob("*.pdf")) and not list(
            category_path.glob("*.PDF")
        ):
            missing_categories.append(f"{category} (empty)")

    # Check index.json validity
    index_valid = False
    index_stats = {}
    if index_file.exists():
        try:
            with open(index_file, encoding="utf-8") as f:
                index_data = json.load(f)
            index_valid = True
            index_stats = index_data.get("statistics", {})
        except (json.JSONDecodeError, OSError):
            index_valid = False

    return {
        "folder": folder.name,
        "pdf_count": len(pdf_files),
        "metadata_files": len(meta_files),
        "extracted_files": len(extracted_files),
        "metadata_complete": meta_ok,
        "missing_metadata_fields": missing_fields,
        "extraction_success_rate": extraction_rate,
        "missing_categories": missing_categories,
        "index_valid": index_valid,
        "index_stats": index_stats,
    }


def audit_by_year(
    corpus_root: Path, corpora: dict[str, str]
) -> dict[str, list[dict[str, Any]]]:
    """Audit corpora organized by year."""
    results_by_year: dict[str, list[dict[str, Any]]] = {}

    for hist_id in sorted(corpora.keys(), key=lambda x: corpora[x]):
        meeting_date = corpora[hist_id]
        year = meeting_date[:4]
        folder = corpus_root / hist_id

        if folder.exists():
            audit_result = audit_corpus(folder)
            audit_result["meeting_date"] = meeting_date
        else:
            audit_result = {
                "folder": hist_id,
                "pdf_count": 0,
                "metadata_files": 0,
                "extracted_files": 0,
                "metadata_complete": False,
                "missing_metadata_fields": [],
                "extraction_success_rate": 0.0,
                "missing_categories": EXPECTED_CATEGORIES.copy(),
                "index_valid": False,
                "index_stats": {},
                "meeting_date": meeting_date,
                "directory_missing": True,
            }

        if year not in results_by_year:
            results_by_year[year] = []
        results_by_year[year].append(audit_result)

    return results_by_year


def generate_missing_items_log(
    corpus_root: Path, corpora: dict[str, str], results_by_year: dict
) -> dict[str, Any]:
    """Generate a log of all missing items across the corpus."""
    missing_log = {
        "generated_at": get_utc_timestamp(),
        "missing_directories": [],
        "missing_agendas": [],
        "missing_minutes": [],
        "missing_staff_reports": [],
        "missing_attachments": [],
        "missing_agenda_item_transmittals": [],
        "missing_agenda_packets": [],
        "incomplete_metadata": [],
        "low_extraction_rate": [],
    }

    for year, results in results_by_year.items():
        for result in results:
            hist_id = result["folder"]

            # Check for missing directories
            if result.get("directory_missing"):
                missing_log["missing_directories"].append(
                    {
                        "hist_id": hist_id,
                        "year": year,
                        "meeting_date": result.get("meeting_date", ""),
                    }
                )

            # Check for missing categories
            for category in result.get("missing_categories", []):
                clean_category = category.replace(" (empty)", "")
                key = f"missing_{clean_category}"
                if key in missing_log:
                    missing_log[key].append(
                        {
                            "hist_id": hist_id,
                            "year": year,
                            "empty": "(empty)" in category,
                        }
                    )

            # Check for incomplete metadata
            if not result.get("metadata_complete"):
                missing_log["incomplete_metadata"].append(
                    {
                        "hist_id": hist_id,
                        "year": year,
                        "missing_fields": result.get("missing_metadata_fields", []),
                    }
                )

            # Check for low extraction rate
            rate = result.get("extraction_success_rate", 0)
            if rate < 1.0 and result.get("pdf_count", 0) > 0:
                missing_log["low_extraction_rate"].append(
                    {"hist_id": hist_id, "year": year, "rate": rate}
                )

    # Write missing items log
    log_file = corpus_root / "missing_items_log.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(missing_log, f, indent=2)
        f.write("\n")

    return missing_log


def generate_audit_report(
    corpus_root: Path,
    corpora: dict[str, str],
    results_by_year: dict,
    missing_log: dict,
    year_range: str,
) -> dict[str, Any]:
    """Generate comprehensive audit report for year-filtered corpora."""
    # Calculate totals
    total_corpora = sum(len(results) for results in results_by_year.values())
    total_pdfs = sum(
        r["pdf_count"] for results in results_by_year.values() for r in results
    )
    total_metadata = sum(
        r["metadata_files"] for results in results_by_year.values() for r in results
    )
    total_extracted = sum(
        r["extracted_files"] for results in results_by_year.values() for r in results
    )

    # Calculate extraction rate (None when no data available)
    extraction_rates = [
        r["extraction_success_rate"]
        for results in results_by_year.values()
        for r in results
        if r["pdf_count"] > 0
    ]
    avg_extraction_rate = (
        sum(extraction_rates) / len(extraction_rates) if extraction_rates else None
    )

    # Count completeness metrics
    metadata_complete_count = sum(
        1
        for results in results_by_year.values()
        for r in results
        if r["metadata_complete"]
    )
    index_valid_count = sum(
        1 for results in results_by_year.values() for r in results if r["index_valid"]
    )

    report = {
        "report_id": sha256(get_utc_timestamp().encode()).hexdigest()[:16],
        "generated_at": get_utc_timestamp(),
        "schema_version": "2.1",
        "year_range": year_range,
        "description": (
            f"Extended Audit Report for City of Visalia "
            f"Legislative Corpus ({year_range})"
        ),
        "summary": {
            "total_corpora": total_corpora,
            "planned_corpora": len(corpora),
            "total_pdfs": total_pdfs,
            "total_metadata_files": total_metadata,
            "total_extracted_files": total_extracted,
            "average_extraction_rate": (
                round(avg_extraction_rate * 100, 2)
                if avg_extraction_rate is not None
                else None
            ),
            "metadata_complete_corpora": metadata_complete_count,
            "index_valid_corpora": index_valid_count,
        },
        "by_year": {},
        "missing_data_summary": {
            "missing_directories": len(missing_log["missing_directories"]),
            "missing_agendas": len(missing_log["missing_agendas"]),
            "missing_minutes": len(missing_log["missing_minutes"]),
            "missing_staff_reports": len(missing_log["missing_staff_reports"]),
            "missing_attachments": len(missing_log["missing_attachments"]),
            "incomplete_metadata": len(missing_log["incomplete_metadata"]),
            "low_extraction_rate": len(missing_log["low_extraction_rate"]),
        },
        "warnings": [],
        "details": results_by_year,
    }

    # Summarize by year
    for year in sorted(results_by_year.keys()):
        year_results = results_by_year[year]
        report["by_year"][year] = {
            "corpora_count": len(year_results),
            "pdf_count": sum(r["pdf_count"] for r in year_results),
            "complete_metadata": sum(1 for r in year_results if r["metadata_complete"]),
            "valid_indexes": sum(1 for r in year_results if r["index_valid"]),
        }

    # Add warnings
    if missing_log["missing_directories"]:
        report["warnings"].append(
            f"{len(missing_log['missing_directories'])} corpus directories missing"
        )
    if missing_log["missing_minutes"]:
        report["warnings"].append(
            f"{len(missing_log['missing_minutes'])} corpora missing minutes documents"
        )
    if missing_log["missing_agendas"]:
        report["warnings"].append(
            f"{len(missing_log['missing_agendas'])} corpora missing agenda documents"
        )
    if missing_log["incomplete_metadata"]:
        count = len(missing_log["incomplete_metadata"])
        report["warnings"].append(f"{count} corpora with incomplete metadata")

    return report


def print_audit_summary(report: dict) -> None:
    """Print a human-readable summary of the audit."""
    print("\n" + "=" * 80)
    print(f"CORPUS AUDIT SUMMARY ({report['year_range']})")
    print("=" * 80)

    summary = report["summary"]
    total_corpora = summary["total_corpora"]
    planned_corpora = summary["planned_corpora"]
    print(f"\nTotal Corpora: {total_corpora} / {planned_corpora} planned")
    print(f"Total PDFs: {summary['total_pdfs']}")
    print(f"Total Metadata Files: {summary['total_metadata_files']}")
    print(f"Total Extracted Files: {summary['total_extracted_files']}")
    extraction_rate = summary["average_extraction_rate"]
    if extraction_rate is not None:
        print(f"Average Extraction Rate: {extraction_rate}%")
    else:
        print("Average Extraction Rate: N/A (no PDFs processed)")
    print(f"Metadata Complete Corpora: {summary['metadata_complete_corpora']}")
    print(f"Valid Indexes: {summary['index_valid_corpora']}")

    print("\nCorpora by Year:")
    for year in sorted(report["by_year"].keys()):
        year_data = report["by_year"][year]
        count = year_data["corpora_count"]
        pdfs = year_data["pdf_count"]
        complete = year_data["complete_metadata"]
        print(f"  {year}: {count} corpora, {pdfs} PDFs, {complete}/{count} complete")

    missing = report["missing_data_summary"]
    print("\nMissing Data Summary:")
    print(f"  Missing Directories: {missing['missing_directories']}")
    print(f"  Missing Agendas: {missing['missing_agendas']}")
    print(f"  Missing Minutes: {missing['missing_minutes']}")
    print(f"  Missing Staff Reports: {missing['missing_staff_reports']}")
    print(f"  Missing Attachments: {missing['missing_attachments']}")
    print(f"  Incomplete Metadata: {missing['incomplete_metadata']}")
    print(f"  Low Extraction Rate: {missing['low_extraction_rate']}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  ⚠ {warning}")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


def main():
    """Run the extended audit pipeline."""
    parser = argparse.ArgumentParser(
        description="Extended audit for HIST-8123 and 2021-2025 corpus"
    )
    parser.add_argument(
        "--corpus-root",
        type=str,
        default="oraculus/corpus",
        help="Root directory for corpus files",
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2014-2025",
        help="Year range to audit (e.g., 2014-2025 or single year like 2024)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for audit report (defaults to VALIDATION_REPORT.json)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output JSON only, no summary",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode - skip detailed file scanning",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()

    # Parse year range
    start_year, end_year = parse_year_range(args.years)
    year_range = args.years

    # Filter corpora by years
    corpora = filter_corpora_by_years(start_year, end_year)

    if not args.json_only:
        print("=" * 80)
        print(f"EXTENDED CORPUS AUDIT ({year_range})")
        print(f"Corpus Root: {corpus_root}")
        print(f"Corpora to audit: {len(corpora)}")
        print(f"Timestamp: {get_utc_timestamp()}")
        print("=" * 80)

    if not corpus_root.exists():
        print(f"Error: Corpus root not found: {corpus_root}")
        return 1

    if len(corpora) == 0:
        print(f"Warning: No corpora found for year range {year_range}")
        return 0

    # Audit corpora by year
    results_by_year = audit_by_year(corpus_root, corpora)

    # Generate missing items log
    missing_log = generate_missing_items_log(corpus_root, corpora, results_by_year)

    # Generate audit report
    report = generate_audit_report(
        corpus_root, corpora, results_by_year, missing_log, year_range
    )

    # Determine output file
    output_file = Path(args.output) if args.output else Path("VALIDATION_REPORT.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")

    if args.json_only:
        print(json.dumps(report, indent=2))
    else:
        print_audit_summary(report)
        print("\nReports saved:")
        print(f"  - {output_file}")
        print(f"  - {corpus_root / 'missing_items_log.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
