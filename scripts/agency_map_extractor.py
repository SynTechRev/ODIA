#!/usr/bin/env python3
"""Agency Map Extractor v1.0 - Cross-Agency Influence Map Pipeline.

This module provides agency extraction and analysis capabilities for the
11-year legislative corpus (2014-2025). It identifies agencies, departments,
divisions, programs, and legislative hubs from metadata, filenames, staff
reports, grant documents, and contract packets.

Author: GitHub Copilot Agent
Date: 2025-12-06
"""

import json
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import HIST_FILES  # noqa: E402

# Constants
CORPUS_ROOT = Path("oraculus/corpus")
CAIM_VERSION = "1.0"
CAIM_SCHEMA_VERSION = "1.0"

def load_known_agencies() -> dict:
    """Load agency aliases from config/agencies.json (falls back to example)."""
    config_dir = _script_dir.parent / "config"
    for filename in ("agencies.json", "agencies.example.json"):
        config_file = config_dir / filename
        if config_file.exists():
            import json as _json
            with open(config_file) as _f:
                data = _json.load(_f)
            return {k: v for k, v in data.items() if not k.startswith("_")}
    return {}


# Load agency aliases from config
KNOWN_AGENCIES: dict[str, list[str]] = load_known_agencies()

# Agency type classifications
AGENCY_TYPES = {
    "municipal": [
        "City Government",
        "City Council",
        "City Manager",
        "Finance Department",
        "Police Department",
        "Fire Department",
        "Public Works",
        "Parks & Recreation",
        "Community Development",
        "Human Resources",
        "Information Technology",
        "Legal/City Attorney",
        "Utilities",
    ],
    "county": ["Tulare County", "Tulare County Sheriff"],
    "state": ["State of California", "CalTrans", "DMV", "CalOES", "State Legislature"],
    "federal": [
        "Federal Government",
        "Department of Justice",
        "DOT",
        "HUD",
        "FEMA",
        "EPA",
        "Congress",
    ],
    "program": ["JAG Program", "COPS Program", "CDBG Program"],
}


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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


def load_corpus_data(corpus_root: Path) -> dict[str, Any]:
    """Load all relevant corpus data for agency extraction.

    Loads:
    - All metadata.json files
    - All index.json files
    - Filename patterns from attachments

    Returns:
        Dictionary containing all loaded corpus data
    """
    data: dict[str, Any] = {
        "metadata_files": {},
        "corpus_indexes": {},
        "attachment_files": [],
        "extracted_text_cache": {},
    }

    # Iterate through corpus directories
    corpus_pattern = re.compile(r"(HIST-\d{4,5}|#\d{2}-\d{4})")

    for entry in corpus_root.iterdir():
        if entry.is_dir() and corpus_pattern.match(entry.name):
            hist_id = entry.name

            # Load metadata files
            metadata_dir = entry / "metadata"
            if metadata_dir.exists():
                for meta_file in metadata_dir.glob("*.json"):
                    if meta_file.name not in ("index.json",):
                        try:
                            with open(meta_file, encoding="utf-8") as f:
                                key = f"{hist_id}/{meta_file.name}"
                                data["metadata_files"][key] = json.load(f)
                        except (json.JSONDecodeError, OSError):
                            pass

            # Load corpus index
            index_path = entry / "index.json"
            if index_path.exists():
                try:
                    with open(index_path, encoding="utf-8") as f:
                        data["corpus_indexes"][hist_id] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass

            # Collect attachment filenames
            attachments_dir = entry / "attachments"
            if attachments_dir.exists():
                for att_file in attachments_dir.glob("*.pdf"):
                    data["attachment_files"].append(
                        {
                            "hist_id": hist_id,
                            "filename": att_file.name,
                            "path": str(att_file),
                        }
                    )

            # Load extracted text for text analysis
            extracted_dir = entry / "extracted"
            if extracted_dir.exists():
                for txt_file in extracted_dir.glob("*.txt"):
                    try:
                        with open(txt_file, encoding="utf-8", errors="ignore") as f:
                            key = f"{hist_id}/{txt_file.name}"
                            data["extracted_text_cache"][key] = f.read()
                    except OSError:
                        pass

    return data


def detect_agency_in_text(text: str) -> list[str]:
    """Detect known agencies in text.

    Returns:
        List of detected agency names
    """
    detected = []
    text_lower = text.lower()

    for agency_name, patterns in KNOWN_AGENCIES.items():
        for pattern in patterns:
            if pattern.lower() in text_lower:
                if agency_name not in detected:
                    detected.append(agency_name)
                break  # Only add agency once

    return detected


def get_agency_type(agency_name: str) -> str:
    """Get the type classification for an agency.

    Returns:
        Agency type string (municipal, county, state, federal, program)
    """
    for agency_type, agencies in AGENCY_TYPES.items():
        if agency_name in agencies:
            return agency_type
    return "unknown"


def extract_agencies_from_metadata(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract agency mentions from metadata files.

    Scans metadata for agency-related fields and patterns.

    Returns:
        List of agency extraction results
    """
    agencies = []

    for meta_key, meta_data in data.get("metadata_files", {}).items():
        if not isinstance(meta_data, dict):
            continue

        hist_id = meta_key.split("/")[0] if "/" in meta_key else "unknown"

        # Check for agency-related fields
        agency_fields = ["department", "agency", "jurisdiction", "organization"]
        for field in agency_fields:
            if field in meta_data:
                value = str(meta_data[field])
                detected = detect_agency_in_text(value)
                for agency_name in detected:
                    agencies.append(
                        {
                            "source": "metadata_field",
                            "hist_id": hist_id,
                            "field": field,
                            "agency_name": agency_name,
                            "agency_type": get_agency_type(agency_name),
                            "context": value[:200],
                            "file": meta_key,
                        }
                    )

        # Check document titles for agency mentions
        titles = meta_data.get("document_titles", [])
        if isinstance(titles, list):
            for title in titles:
                detected = detect_agency_in_text(str(title))
                for agency_name in detected:
                    agencies.append(
                        {
                            "source": "document_title",
                            "hist_id": hist_id,
                            "agency_name": agency_name,
                            "agency_type": get_agency_type(agency_name),
                            "context": title[:200],
                            "file": meta_key,
                        }
                    )

    return agencies


def extract_agencies_from_filenames(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract agency mentions from attachment filenames.

    Scans filenames for agency patterns.

    Returns:
        List of agency extraction results
    """
    agencies = []

    for att in data.get("attachment_files", []):
        filename = att.get("filename", "")
        hist_id = att.get("hist_id", "unknown")

        detected = detect_agency_in_text(filename)
        for agency_name in detected:
            agencies.append(
                {
                    "source": "filename",
                    "hist_id": hist_id,
                    "agency_name": agency_name,
                    "agency_type": get_agency_type(agency_name),
                    "filename": filename,
                }
            )

    return agencies


def extract_agencies_from_text(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract agency mentions from extracted text content.

    Scans extracted text files for agency patterns.

    Returns:
        List of agency extraction results
    """
    agencies = []

    for text_key, text_content in data.get("extracted_text_cache", {}).items():
        if not text_content:
            continue

        hist_id = text_key.split("/")[0] if "/" in text_key else "unknown"

        detected = detect_agency_in_text(text_content)
        for agency_name in detected:
            # Find context around the agency mention
            context = _extract_agency_context(text_content, agency_name)
            agencies.append(
                {
                    "source": "extracted_text",
                    "hist_id": hist_id,
                    "agency_name": agency_name,
                    "agency_type": get_agency_type(agency_name),
                    "context": context,
                    "file": text_key,
                }
            )

    return agencies


def _extract_agency_context(text: str, agency_name: str) -> str:
    """Extract context around an agency mention.

    Returns:
        String with up to 200 chars of context
    """
    patterns = KNOWN_AGENCIES.get(agency_name, [agency_name.lower()])
    text_lower = text.lower()

    for pattern in patterns:
        idx = text_lower.find(pattern.lower())
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(text), idx + len(pattern) + 150)
            return text[start:end].strip()

    return ""


def detect_agency_aliases(
    agency_extractions: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Detect potential agency aliases and variations.

    Groups agency mentions that may refer to the same entity.

    Returns:
        Dictionary mapping canonical agency names to aliases
    """
    aliases: dict[str, list[str]] = defaultdict(list)

    # Group by known agency names
    for agency in agency_extractions:
        agency_name = agency.get("agency_name", "")
        if agency_name and agency_name in KNOWN_AGENCIES:
            patterns = KNOWN_AGENCIES[agency_name]
            for pattern in patterns:
                if pattern not in aliases[agency_name]:
                    aliases[agency_name].append(pattern)

    return dict(aliases)


def normalize_agency_identifier(agency_name: str) -> str:
    """Normalize an agency name to a standard identifier.

    Returns:
        Normalized agency identifier
    """
    # Remove special characters and normalize whitespace
    normalized = re.sub(r"[^\w\s]", "", agency_name.lower())
    normalized = re.sub(r"\s+", "_", normalized.strip())
    return normalized


def build_agency_index(
    agency_extractions: list[dict[str, Any]], corpora: dict[str, str]
) -> dict[str, Any]:
    """Build a comprehensive agency index.

    Creates an index mapping agencies to their appearances across the corpus.

    Returns:
        Agency index dictionary
    """
    agency_index: dict[str, Any] = {}

    for agency in agency_extractions:
        agency_name = agency.get("agency_name", "Unknown")
        hist_id = agency.get("hist_id", "unknown")
        agency_type = agency.get("agency_type", "unknown")

        if agency_name not in agency_index:
            agency_index[agency_name] = {
                "name": agency_name,
                "normalized_id": normalize_agency_identifier(agency_name),
                "type": agency_type,
                "appearances": [],
                "years": set(),
                "hist_ids": set(),
                "sources": set(),
            }

        # Get year from corpus mapping
        meeting_date = corpora.get(hist_id, "")
        year = meeting_date[:4] if meeting_date else ""

        agency_index[agency_name]["appearances"].append(
            {
                "hist_id": hist_id,
                "year": year,
                "source": agency.get("source"),
                "context": agency.get("context", ""),
            }
        )
        if year:
            agency_index[agency_name]["years"].add(year)
        agency_index[agency_name]["hist_ids"].add(hist_id)
        agency_index[agency_name]["sources"].add(agency.get("source", ""))

    # Convert sets to sorted lists for JSON serialization
    for agency_name in agency_index:
        agency_index[agency_name]["years"] = sorted(agency_index[agency_name]["years"])
        agency_index[agency_name]["hist_ids"] = sorted(
            agency_index[agency_name]["hist_ids"]
        )
        agency_index[agency_name]["sources"] = sorted(
            agency_index[agency_name]["sources"]
        )
        agency_index[agency_name]["appearance_count"] = len(
            agency_index[agency_name]["appearances"]
        )
        agency_index[agency_name]["year_span"] = len(agency_index[agency_name]["years"])

    return agency_index


def extract_agency_relationships(
    agency_index: dict[str, Any], corpora: dict[str, str]
) -> list[dict[str, Any]]:
    """Extract relationships between agencies based on co-occurrence.

    Two agencies are related if they appear in the same corpus item.

    Returns:
        List of agency relationship dicts
    """
    relationships = []

    # Build inverse index: hist_id -> set of agencies
    hist_to_agencies: dict[str, set[str]] = defaultdict(set)
    for agency_name, agency_data in agency_index.items():
        for hist_id in agency_data.get("hist_ids", []):
            hist_to_agencies[hist_id].add(agency_name)

    # Find co-occurrences
    co_occurrences: dict[tuple[str, str], list[str]] = defaultdict(list)
    for hist_id, agencies in hist_to_agencies.items():
        agencies_list = sorted(agencies)
        for i in range(len(agencies_list)):
            for j in range(i + 1, len(agencies_list)):
                pair = (agencies_list[i], agencies_list[j])
                co_occurrences[pair].append(hist_id)

    # Convert to relationships
    for (agency_a, agency_b), hist_ids in co_occurrences.items():
        meeting_date = corpora.get(hist_ids[0], "")
        year = meeting_date[:4] if meeting_date else ""

        relationships.append(
            {
                "agency_a": agency_a,
                "agency_b": agency_b,
                "co_occurrence_count": len(hist_ids),
                "shared_hist_ids": hist_ids,
                "relationship_type": "co_occurrence",
                "first_year": year,
            }
        )

    return relationships


def run_agency_extraction(
    corpus_root: Path, year_range: str, output_dir: Path | None = None
) -> dict[str, Any]:
    """Run the complete agency extraction pipeline.

    Returns:
        Dictionary with all extraction results
    """
    start_year, end_year = parse_year_range(year_range)
    corpora = filter_corpora_by_years(start_year, end_year)

    print(f"Agency Map Extractor v{CAIM_VERSION}")
    print("=" * 60)
    print(f"Corpus Root: {corpus_root}")
    print(f"Year Range: {year_range}")
    print(f"Corpora to analyze: {len(corpora)}")
    print("=" * 60)

    # Step 1: Load corpus data
    print("\n[1/5] Loading corpus data...")
    data = load_corpus_data(corpus_root)
    print(f"  - Loaded {len(data['metadata_files'])} metadata files")
    print(f"  - Loaded {len(data['corpus_indexes'])} corpus indexes")
    print(f"  - Loaded {len(data['attachment_files'])} attachment files")
    print(f"  - Loaded {len(data['extracted_text_cache'])} extracted text files")

    # Step 2: Extract agencies from all sources
    print("\n[2/5] Extracting agencies...")
    metadata_agencies = extract_agencies_from_metadata(data)
    filename_agencies = extract_agencies_from_filenames(data)
    text_agencies = extract_agencies_from_text(data)
    all_agencies = metadata_agencies + filename_agencies + text_agencies
    print(f"  - From metadata: {len(metadata_agencies)}")
    print(f"  - From filenames: {len(filename_agencies)}")
    print(f"  - From text: {len(text_agencies)}")
    print(f"  - Total: {len(all_agencies)}")

    # Step 3: Detect agency aliases
    print("\n[3/5] Detecting agency aliases...")
    aliases = detect_agency_aliases(all_agencies)
    print(f"  - Identified {len(aliases)} agency alias groups")

    # Step 4: Build agency index
    print("\n[4/5] Building agency index...")
    agency_index = build_agency_index(all_agencies, corpora)
    print(f"  - Indexed {len(agency_index)} unique agencies")

    # Step 5: Extract relationships
    print("\n[5/5] Extracting agency relationships...")
    relationships = extract_agency_relationships(agency_index, corpora)
    print(f"  - Found {len(relationships)} agency relationships")

    # Build result
    timestamp = get_utc_timestamp()
    result = {
        "version": CAIM_VERSION,
        "schema_version": CAIM_SCHEMA_VERSION,
        "generated_at": timestamp,
        "year_range": year_range,
        "corpora_analyzed": len(corpora),
        "summary": {
            "total_agency_mentions": len(all_agencies),
            "unique_agencies": len(agency_index),
            "relationships_found": len(relationships),
        },
        "agency_index": agency_index,
        "aliases": aliases,
        "relationships": relationships,
    }

    # Write output files if output_dir specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        agency_index_path = output_dir / "agency_index.json"
        with open(agency_index_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  - Wrote {agency_index_path}")

    print("\n" + "=" * 60)
    print("AGENCY EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"\nUnique Agencies: {len(agency_index)}")
    print(f"Agency Relationships: {len(relationships)}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Agency Map Extractor v1.0 - Extract agencies from corpus"
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
        help="Year range to analyze (e.g., 2014-2025)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for extraction results",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()
    output_dir = Path(args.output).resolve() if args.output else None

    if not corpus_root.exists():
        print(f"Error: Corpus root not found: {corpus_root}")
        sys.exit(1)

    run_agency_extraction(corpus_root, args.years, output_dir)
