#!/usr/bin/env python3
"""Extended Ingestion Script for HIST-8123 and 2021-2025 Legislative Corpus.

This script provides enhanced ingestion capabilities with year-aware logic
for the 2021-2025 legislative corpus extension. It builds upon the Phase-20
full ingestion pipeline to support:

1. Year-aware corpus filtering (e.g., --years 2021-2025)
2. HIST-8123 specific ingestion
3. Extended metadata generation for modern corpus entries
4. Validation of 11-year corpus architecture (2014-2025)

Author: GitHub Copilot Agent
Date: 2025-12-05
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import (  # noqa: E402
    HIST_FILES,
    REQUIRED_SUBDIRS,
    calculate_file_hash,
    calculate_text_hash,
    verify_hash_consistency,
)

# Constant for recovered corpus identification
RECOVERED_CORPUS_ID = "HIST-11740"

# Extended source URLs for 2021-2025 corpus entries
EXTENDED_SOURCE_URLS = {
    # 2021
    "#21-0443": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6556979&GUID=6AE534FE-5694-422F-A408-61E09B851862&Options=ID|Text|Attachments|Other|&Search=JAG",
    "#21-0588": "https://visalia.legistar.com/LegislationDetail.aspx?ID=5201038&GUID=51FAF735-8FCD-4575-8CA7-E87D1383E7C0&Options=ID|Text|Attachments|Other|&Search=JAG",
    # 2022
    "#22-0012": "https://visalia.legistar.com/LegislationDetail.aspx?ID=5531572&GUID=A26C1179-4598-4549-A8AC-2797DE108B5B&Options=ID|Text|Attachments|Other|&Search=JAG",
    "#22-0080": "https://visalia.legistar.com/LegislationDetail.aspx?ID=5531573&GUID=E103EC4F-119B-4BA4-85B2-585EF464655D&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#22-0463": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6050807&GUID=B65F1FB3-884A-4BE9-AA89-B9CD6D2499F0&Options=ID|Text|Attachments|Other|&Search=Axon",
    # 2023
    "#23-0148": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6190815&GUID=93BF5B7F-BBD6-4BBB-AC96-B13F602B4566&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#23-0214": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6248369&GUID=2A5BD974-C5B3-4F27-AB66-8768C3FC38A9&Options=ID|Text|Attachments|Other|&Search=Axon",
    # 2024
    "#24-0034": "https://visalia.legistar.com/LegislationDetail.aspx?ID=7050372&GUID=71183219-C42E-4239-99B9-FC61CA61417B&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#24-0039": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6518797&GUID=7D5AC41F-FEF3-46DB-A24A-412A8C81C221&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#24-0163": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6712070&GUID=8BE005EA-41B1-4AC2-B703-49B6497153A5&Options=ID|Text|Attachments|Other|&Search=Flock",
    "#24-0403": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6885625&GUID=69890EF5-FD15-4359-ADD6-7ADCDB955FED&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#24-0410": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6885627&GUID=C6692DE6-646A-475D-A48C-B94559F57DDD&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#24-0415": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6900047&GUID=BC55EDAF-4F50-456C-8857-C76DBF7166DE&Options=ID|Text|Attachments|Other|&Search=JAG",
    "#24-0477": "https://visalia.legistar.com/LegislationDetail.aspx?ID=7059588&GUID=A80529F7-D8A3-4BBD-84C4-F47ABE973194&Options=ID|Text|Attachments|Other|&Search=Flock",
    "#24-0559": "https://visalia.legistar.com/LegislationDetail.aspx?ID=7099371&GUID=54AD98CC-F05C-452A-8181-7528325A95B5&Options=ID|Text|Attachments|Other|&Search=Flock",
    # 2025
    "#25-0171": "https://visalia.legistar.com/LegislationDetail.aspx?ID=7404093&GUID=89BB9034-E2BC-44EB-848A-50E07F79A614&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#25-0202": "https://visalia.legistar.com/LegislationDetail.aspx?ID=7421753&GUID=798D5F44-03EA-4956-9320-4C88833D5075&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#25-0203": "https://visalia.legistar.com/LegislationDetail.aspx?ID=7438906&GUID=4B5439EA-2363-4568-A6D0-7ABE615D043E&Options=ID|Text|Attachments|Other|&Search=Axon",
    "#25-0333": "https://visalia.legistar.com/LegislationDetail.aspx?ID=7502920&GUID=86D6E330-007C-437B-98B1-E1CD9225ECA8&Options=ID|Text|Attachments|Other|&Search=Flock",
    # Historic HIST entries (2014-2020)
    "HIST-6225": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6060759&GUID=19497FE7-65B7-4923-914E-3AE5362C6C26&Options=ID|Text|Attachments|Other|&Search=JAG",
    "HIST-7722": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6061005&GUID=B87CF8C9-74AF-4834-9768-4BDEB278DD45&Options=ID|Text|Attachments|Other|&Search=Axon",
    "HIST-8213": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6061085&GUID=158C3226-B821-4E97-B696-15E2FC032EDB&Options=ID|Text|Attachments|Other|&Search=JAG",
    "HIST-9493": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6061591&GUID=946D4078-5373-4608-B695-EDFD9812BC48&Options=ID|Text|Attachments|Other|&Search=JAG",
    "HIST-11153": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6060276&GUID=B56BBF59-3DAC-4775-ADA8-5AE06780D430&Options=ID|Text|Attachments|Other|&Search=JAG",
    "HIST-11740": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062163&GUID=C70178B5-6CAA-48A5-9D94-E667BCE842CA&Options=ID|Text|Attachments|Other|&Search=BWC",
    "HIST-11877": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062297&GUID=BAB7266D-C49B-4C2F-AA8E-3A5F97ED8676&Options=ID|Text|Attachments|Other|&Search=BWC",
    "HIST-11887": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062274&GUID=D894FC62-6957-4150-ACE4-D78B56A532F8&Options=ID|Text|Attachments|Other|&Search=BWC",
    "HIST-12077": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062193&GUID=1EB2DD29-67C1-4024-9E12-BEBA6D650F4C&Options=ID|Text|Attachments|Other|&Search=JAG",
    "HIST-12223": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062196&GUID=C12645A3-09AE-457B-8E45-E1368AF68E32&Options=ID|Text|Attachments|Other|&Search=Axon",
    "HIST-13175": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6061882&GUID=BBAF7C12-0AE2-4797-9694-998C15B25D2D&Options=ID|Text|Attachments|Other|&Search=JAG",
    "HIST-13397": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062023&GUID=D9E6A359-5020-4360-99AD-C37ACC62CC2F&Options=ID|Text|Attachments|Other|&Search=BWC",
    "HIST-13594": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062515&GUID=71061927-31E1-4EA1-B94F-1A2651084FD7&Options=ID|Text|Attachments|Other|&Search=BWC",
    "HIST-13848": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062843&GUID=1FACE38B-86E2-44F8-9455-FA50D7B3E302&Options=ID|Text|Attachments|Other|&Search=JAG",
    "HIST-14845": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062772&GUID=E0CFB31F-7ED6-41C1-8813-2307D473CC97&Options=ID|Text|Attachments|Other|&Search=Axon",
    "HIST-14973": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6062827&GUID=FE902739-26DA-4E2E-ADE1-0E8ED86913B4&Options=ID|Text|Attachments|Other|&Search=Axon",
    "HIST-15517": "https://visalia.legistar.com/LegislationDetail.aspx?ID=6063025&GUID=76A8B953-E388-4EC4-944F-7346A5E6CE05&Options=ID|Text|Attachments|Other|&Search=JAG",
}


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_year_range(year_range: str) -> tuple[int, int]:
    """Parse a year range string (e.g., '2021-2025') into start and end years."""
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


def validate_year_filtered_structure(
    corpus_root: Path, corpora: dict[str, str]
) -> dict[str, Any]:
    """Validate directory structure for filtered corpora."""
    print(f"\n[1/5] Validating Directory Structure ({len(corpora)} corpora)...")

    results = {
        "passed": True,
        "corpus_count": 0,
        "structure_issues": [],
        "pdfs_found": 0,
        "empty_categories": [],
    }

    for hist_id in sorted(corpora.keys(), key=lambda x: corpora[x]):
        corpus_path = corpus_root / hist_id
        results["corpus_count"] += 1

        if not corpus_path.exists():
            results["structure_issues"].append(
                {"hist_id": hist_id, "issue": "Directory does not exist"}
            )
            results["passed"] = False
            continue

        # Check for required subdirectories
        for subdir in REQUIRED_SUBDIRS:
            subdir_path = corpus_path / subdir
            if not subdir_path.exists():
                results["structure_issues"].append(
                    {"hist_id": hist_id, "issue": f"Missing subdirectory: {subdir}"}
                )
                results["passed"] = False

        # Count PDFs
        for subdir in ["agendas", "minutes", "staff_reports", "attachments"]:
            subdir_path = corpus_path / subdir
            if subdir_path.exists():
                pdf_count = len(list(subdir_path.glob("*.pdf"))) + len(
                    list(subdir_path.glob("*.PDF"))
                )
                results["pdfs_found"] += pdf_count

                if pdf_count == 0:
                    results["empty_categories"].append(
                        {"hist_id": hist_id, "category": subdir}
                    )

    print(f"  Corpora validated: {results['corpus_count']}")
    print(f"  PDFs found: {results['pdfs_found']}")
    print(f"  Structure issues: {len(results['structure_issues'])}")

    return results


def generate_extended_metadata(
    corpus_root: Path, corpora: dict[str, str]
) -> dict[str, Any]:
    """Generate metadata for filtered corpora with extended fields."""
    print(f"\n[2/5] Generating Extended Metadata ({len(corpora)} corpora)...")

    results = {
        "corpora_processed": 0,
        "metadata_files_created": 0,
        "pdfs_processed": 0,
        "warnings": [],
    }

    for hist_id in sorted(corpora.keys(), key=lambda x: corpora[x]):
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        results["corpora_processed"] += 1
        meeting_date = corpora[hist_id]
        source_url = EXTENDED_SOURCE_URLS.get(hist_id, "NEEDS_USER_INPUT")

        # Create corpus-level metadata
        corpus_metadata = {
            "corpus_id": hist_id,
            "file_id": hist_id,
            "meeting_date": meeting_date,
            "meeting_type": "City Council Regular Meeting",
            "jurisdiction": "City of Visalia",
            "source_url": source_url,
            "document_titles": [],
            "document_urls": {},
            "ingest_version": "2.1",  # Extended version for 2021-2025 support
            "ingestion_timestamp": get_utc_timestamp(),
            "provenance_flags": {
                "manual_date_entry": True,
                "manual_source_entry": source_url != "NEEDS_USER_INPUT",
                "extended_ingest": True,  # Flag for extended ingestion
                "recovered_corpus": hist_id == RECOVERED_CORPUS_ID,
            },
            "category_flags": {
                "has_agendas": False,
                "has_minutes": False,
                "has_staff_reports": False,
                "has_attachments": False,
                "has_packets": False,
                "has_transmittals": False,
            },
            "files": [],
        }

        # Check which categories have content
        for category in ["agendas", "minutes", "staff_reports", "attachments"]:
            category_path = corpus_path / category
            if category_path.exists():
                pdf_files = list(category_path.glob("*.pdf")) + list(
                    category_path.glob("*.PDF")
                )
                if pdf_files:
                    corpus_metadata["category_flags"][f"has_{category}"] = True

                for pdf_file in pdf_files:
                    results["pdfs_processed"] += 1
                    file_hash = calculate_file_hash(pdf_file)
                    text_file = corpus_path / "extracted" / (pdf_file.stem + ".txt")
                    text_hash = calculate_text_hash(text_file)

                    file_type_map = {
                        "agendas": "agenda",
                        "minutes": "minutes",
                        "staff_reports": "staff_report",
                        "attachments": "attachment",
                    }

                    file_metadata = {
                        "file_name": pdf_file.name,
                        "file_type": file_type_map.get(category, "unknown"),
                        "file_hash": file_hash,
                        "text_hash": text_hash,
                        "extraction_complete": text_hash != "",
                    }
                    corpus_metadata["files"].append(file_metadata)

                    # Write individual file metadata
                    metadata_dir = corpus_path / "metadata"
                    metadata_dir.mkdir(exist_ok=True)
                    metadata_file = metadata_dir / (pdf_file.stem + ".json")

                    individual_metadata = {
                        "file_name": pdf_file.name,
                        "file_type": file_type_map.get(category, "unknown"),
                        "meeting_date": meeting_date,
                        "meeting_type": "City Council Regular Meeting",
                        "jurisdiction": "City of Visalia",
                        "source_url": source_url,
                        "file_hash": file_hash,
                        "text_hash": text_hash,
                        "document_titles": [],
                        "document_urls": {},
                        "ingest_version": "2.1",
                        "provenance_flags": {
                            "manual_date_entry": True,
                            "manual_source_entry": source_url != "NEEDS_USER_INPUT",
                            "extended_ingest": True,
                            "recovered_corpus": hist_id == RECOVERED_CORPUS_ID,
                        },
                    }

                    with open(metadata_file, "w") as f:
                        json.dump(individual_metadata, f, indent=2)
                        f.write("\n")
                    results["metadata_files_created"] += 1

        # Write corpus index.json
        index_file = corpus_path / "index.json"
        corpus_metadata["generated_at"] = get_utc_timestamp()
        corpus_metadata["statistics"] = {
            "total_files": len(corpus_metadata["files"]),
            "by_type": {},
        }
        for file_info in corpus_metadata["files"]:
            ft = file_info["file_type"]
            corpus_metadata["statistics"]["by_type"][ft] = (
                corpus_metadata["statistics"]["by_type"].get(ft, 0) + 1
            )

        with open(index_file, "w") as f:
            json.dump(corpus_metadata, f, indent=2)
            f.write("\n")

    print(f"  Corpora processed: {results['corpora_processed']}")
    print(f"  PDFs processed: {results['pdfs_processed']}")
    print(f"  Metadata files created: {results['metadata_files_created']}")

    return results


def scaffold_missing_directories(
    corpus_root: Path, corpora: dict[str, str]
) -> dict[str, Any]:
    """Create scaffolding for missing corpus directories."""
    print(f"\n[3/5] Scaffolding Missing Directories ({len(corpora)} corpora)...")

    results = {
        "directories_created": 0,
        "subdirs_created": 0,
        "already_exists": 0,
    }

    for hist_id in sorted(corpora.keys(), key=lambda x: corpora[x]):
        corpus_path = corpus_root / hist_id

        if corpus_path.exists():
            results["already_exists"] += 1
        else:
            corpus_path.mkdir(parents=True, exist_ok=True)
            results["directories_created"] += 1

        # Ensure all required subdirectories exist
        for subdir in REQUIRED_SUBDIRS:
            subdir_path = corpus_path / subdir
            if not subdir_path.exists():
                subdir_path.mkdir(exist_ok=True)
                results["subdirs_created"] += 1

            # Create .gitkeep for empty directories
            gitkeep = subdir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

    print(f"  Directories created: {results['directories_created']}")
    print(f"  Subdirectories created: {results['subdirs_created']}")
    print(f"  Already existed: {results['already_exists']}")

    return results


def run_integrity_verification(
    corpus_root: Path, corpora: dict[str, str]
) -> dict[str, Any]:
    """Run integrity verification for filtered corpora."""
    print(f"\n[4/5] Running Integrity Verification ({len(corpora)} corpora)...")

    results = verify_hash_consistency(corpus_root)
    results["corpora_verified"] = len(corpora)

    print(f"  Hash verifications: {results['verified']}")
    print(f"  Hash mismatches: {len(results['mismatches'])}")
    print(f"  Missing files: {len(results['missing_files'])}")

    return results


def generate_ingestion_report_extended(
    corpus_root: Path,
    corpora: dict[str, str],
    structure_results: dict,
    metadata_results: dict,
    scaffold_results: dict,
    integrity_results: dict,
    year_range: str,
) -> dict[str, Any]:
    """Generate extended ingestion report for year-filtered corpora."""
    print("\n[5/5] Generating Extended Ingestion Report...")

    report = {
        "report_id": hashlib.sha256(get_utc_timestamp().encode()).hexdigest()[:16],
        "generated_at": get_utc_timestamp(),
        "schema_version": "2.1",
        "year_range": year_range,
        "description": (
            f"Extended Ingestion Report for City of Visalia "
            f"Legislative Corpus ({year_range})"
        ),
        "summary": {
            "total_corpora": structure_results["corpus_count"],
            "total_files_processed": metadata_results["pdfs_processed"],
            "directories_scaffolded": scaffold_results["directories_created"],
            "subdirs_scaffolded": scaffold_results["subdirs_created"],
            "hash_verifications": integrity_results["verified"],
            "structure_validation_passed": structure_results["passed"],
            "empty_categories_count": len(structure_results["empty_categories"]),
        },
        "corpora_by_year": {},
        "missing_data_summary": {
            "missing_agendas": [],
            "missing_minutes": [],
            "missing_staff_reports": [],
            "missing_attachments": [],
        },
        "warnings": [],
        "flagged_irregularities": [],
    }

    # Organize corpora by year
    for hist_id, meeting_date in corpora.items():
        year = meeting_date[:4]
        if year not in report["corpora_by_year"]:
            report["corpora_by_year"][year] = []
        report["corpora_by_year"][year].append(
            {"corpus_id": hist_id, "meeting_date": meeting_date}
        )

    # Categorize missing data
    for item in structure_results["empty_categories"]:
        category = item["category"]
        key = f"missing_{category}"
        if key in report["missing_data_summary"]:
            report["missing_data_summary"][key].append(item["hist_id"])

    # Add warnings
    if structure_results["pdfs_found"] == 0:
        report["warnings"].append(
            "No PDF files found in filtered corpora - awaiting document upload"
        )

    if integrity_results.get("mismatches"):
        report["warnings"].append(
            f"{len(integrity_results['mismatches'])} hash mismatch(es) detected"
        )

    # Add flagged irregularities
    for item in structure_results["structure_issues"]:
        report["flagged_irregularities"].append({"type": "structure", "details": item})

    # Write report to file
    report_file = corpus_root / "audit_extension_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
        f.write("\n")

    print(f"  Report ID: {report['report_id']}")
    print(f"  Year range: {year_range}")
    print(f"  Total corpora: {report['summary']['total_corpora']}")
    print(f"  Report saved to: {report_file}")

    return report


def print_extended_summary(report: dict) -> None:
    """Print a human-readable summary of the extended ingestion."""
    print("\n" + "=" * 80)
    print(f"EXTENDED INGESTION SUMMARY ({report['year_range']})")
    print("=" * 80)

    summary = report["summary"]
    print(f"\nCorpora Processed: {summary['total_corpora']}")
    print(f"Total Files Processed: {summary['total_files_processed']}")
    print(f"Directories Scaffolded: {summary['directories_scaffolded']}")
    print(f"Subdirectories Scaffolded: {summary['subdirs_scaffolded']}")
    print(f"Hash Verifications: {summary['hash_verifications']}")
    passed = summary["structure_validation_passed"]
    status = "✓ Passed" if passed else "✗ Failed"
    print(f"Structure Validation: {status}")

    if report["corpora_by_year"]:
        print("\nCorpora by Year:")
        for year in sorted(report["corpora_by_year"].keys()):
            count = len(report["corpora_by_year"][year])
            print(f"  {year}: {count} corpora")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  ⚠ {warning}")

    print("\n" + "=" * 80)
    print("EXTENDED INGESTION COMPLETE")
    print("=" * 80)


def main():
    """Run the extended ingestion pipeline."""
    parser = argparse.ArgumentParser(
        description="Extended ingestion for HIST-8123 and 2021-2025 corpus"
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
        default="2021-2025",
        help="Year range to process (e.g., 2021-2025 or single year like 2024)",
    )
    parser.add_argument(
        "--all-years",
        action="store_true",
        help="Process all years (2014-2025)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, do not modify files",
    )
    parser.add_argument(
        "--scaffold-only",
        action="store_true",
        help="Only create directory scaffolding",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()

    # Determine year range
    if args.all_years:
        start_year, end_year = 2014, 2025
        year_range = "2014-2025"
    else:
        start_year, end_year = parse_year_range(args.years)
        year_range = args.years

    # Filter corpora by years
    corpora = filter_corpora_by_years(start_year, end_year)

    print("=" * 80)
    print(f"EXTENDED INGESTION PIPELINE ({year_range})")
    print(f"Corpus Root: {corpus_root}")
    print(f"Corpora to process: {len(corpora)}")
    print(f"Timestamp: {get_utc_timestamp()}")
    if args.dry_run:
        print("Mode: DRY RUN (validation only)")
    print("=" * 80)

    if not corpus_root.exists():
        print(f"Error: Corpus root not found: {corpus_root}")
        return 1

    if len(corpora) == 0:
        print(f"Warning: No corpora found for year range {year_range}")
        return 0

    # Step 1: Scaffold missing directories
    if not args.dry_run:
        scaffold_results = scaffold_missing_directories(corpus_root, corpora)
    else:
        scaffold_results = {
            "directories_created": 0,
            "subdirs_created": 0,
            "already_exists": len(corpora),
        }
        print("\n[3/5] Scaffolding (skipped in dry-run mode)")

    if args.scaffold_only:
        print("\n" + "=" * 80)
        print("SCAFFOLDING COMPLETE")
        print("=" * 80)
        return 0

    # Step 2: Validate structure
    structure_results = validate_year_filtered_structure(corpus_root, corpora)

    # Step 3: Generate metadata (skip in dry-run)
    if not args.dry_run:
        metadata_results = generate_extended_metadata(corpus_root, corpora)
    else:
        metadata_results = {
            "corpora_processed": len(corpora),
            "metadata_files_created": 0,
            "pdfs_processed": 0,
            "warnings": [],
        }
        print("\n[2/5] Metadata generation (skipped in dry-run mode)")

    # Step 4: Integrity verification
    integrity_results = run_integrity_verification(corpus_root, corpora)

    # Step 5: Generate report
    report = generate_ingestion_report_extended(
        corpus_root,
        corpora,
        structure_results,
        metadata_results,
        scaffold_results,
        integrity_results,
        year_range,
    )

    # Print summary
    print_extended_summary(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
