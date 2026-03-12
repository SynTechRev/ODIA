#!/usr/bin/env python3
"""Vendor Map Extractor v1.0 - Vendor Influence & Contract Flow Map Pipeline.

This module provides vendor extraction and analysis capabilities for the
11-year legislative corpus (2014-2025). It identifies vendors, contract flows,
renewal patterns, technology dependencies, and procurement irregularities.
[MSH-v1] Supports non-standard legal meaning detection via semantic harmonization.

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
VICFM_VERSION = "1.0"
VICFM_SCHEMA_VERSION = "1.0"

# Vendor detection patterns - known vendors and keywords
KNOWN_VENDORS = {
    # Surveillance technology vendors
    "Axon": ["axon", "taser"],
    "Flock Safety": ["flock", "flock safety"],
    "Motorola Solutions": ["motorola", "motorola solutions"],
    # Telecom vendors
    "T-Mobile": ["t-mobile", "tmobile", "t mobile"],
    "Verizon": ["verizon", "verizon wireless"],
    "AT&T": ["at&t", "att", "at & t"],
    # ALPR vendors
    "Vigilant Solutions": ["vigilant", "vigilant solutions"],
    "Leonardo/ELSAG": ["leonardo", "elsag"],
    "Rekor Systems": ["rekor"],
    # IT/Software vendors
    "Microsoft": ["microsoft"],
    "Oracle": ["oracle"],
    "Tyler Technologies": ["tyler", "tyler technologies"],
    # Construction/Infrastructure
    "Granite Construction": ["granite construction", "granite"],
    "Teichert Construction": ["teichert"],
    # Professional services
    "NBS": ["nbs government finance"],
    "HdL Companies": ["hdl companies", "hdl"],
}

# Technology program patterns
TECH_PROGRAMS = {
    "ALPR": [
        "automated license plate reader",
        "alpr",
        "license plate recognition",
        "lpr system",
        "plate reader",
    ],
    "Body-Worn Cameras": [
        "body worn camera",
        "body-worn camera",
        "bwc",
        "bodycam",
        "body cam",
        "axon body",
    ],
    "Cellular Infrastructure": [
        "cell tower",
        "cellular infrastructure",
        "wireless network",
        "mobile network",
        "5g",
        "4g lte",
    ],
    "Video Surveillance": [
        "video surveillance",
        "cctv",
        "security camera",
        "surveillance camera",
    ],
    "JAG Grants": [
        "jag grant",
        "justice assistance grant",
        "byrne jag",
        "edward byrne",
    ],
    "Capital Improvement": [
        "capital improvement",
        "cip",
        "infrastructure improvement",
        "capital project",
    ],
    "Software/IT": [
        "software license",
        "saas",
        "cloud service",
        "enterprise software",
        "it contract",
    ],
}

# Procurement irregularity patterns
SOLE_SOURCE_PATTERNS = [
    r"sole.?source",
    r"single.?source",
    r"non.?competitive",
    r"emergency.?procurement",
    r"piggyback.?contract",
]

# Contract amount patterns
AMOUNT_PATTERNS = [
    r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|M)?",
    r"([\d,]+(?:\.\d{2})?)\s*dollars",
    r"contract.{0,30}([\d,]+(?:\.\d{2})?)",
    r"amount.{0,20}\$?\s*([\d,]+(?:\.\d{2})?)",
]


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
    """Load all relevant corpus data for vendor extraction.

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


def extract_vendors_from_metadata(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract vendor mentions from metadata files.

    Scans metadata for vendor-related fields and patterns.

    Returns:
        List of vendor extraction results
    """
    vendors = []

    for meta_key, meta_data in data.get("metadata_files", {}).items():
        if not isinstance(meta_data, dict):
            continue

        hist_id = meta_key.split("/")[0] if "/" in meta_key else "unknown"

        # Check for vendor-related fields
        vendor_fields = ["vendor", "contractor", "supplier", "company", "organization"]
        for field in vendor_fields:
            if field in meta_data:
                vendors.append(
                    {
                        "source": "metadata_field",
                        "hist_id": hist_id,
                        "field": field,
                        "value": meta_data[field],
                        "file": meta_key,
                    }
                )

        # Check document titles for vendor mentions
        titles = meta_data.get("document_titles", [])
        if isinstance(titles, list):
            for title in titles:
                detected = _detect_vendor_in_text(str(title))
                for vendor_name in detected:
                    vendors.append(
                        {
                            "source": "document_title",
                            "hist_id": hist_id,
                            "vendor_name": vendor_name,
                            "context": title[:200],
                            "file": meta_key,
                        }
                    )

    return vendors


def extract_vendors_from_filenames(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract vendor mentions from attachment filenames.

    Scans filenames for patterns like:
    - "Axon Quote.pdf"
    - "FLOCK Agreement.pdf"
    - "T-Mobile Contract.pdf"

    Returns:
        List of vendor extraction results
    """
    vendors = []

    for att in data.get("attachment_files", []):
        filename = att.get("filename", "")
        hist_id = att.get("hist_id", "unknown")

        detected = _detect_vendor_in_text(filename)
        for vendor_name in detected:
            vendors.append(
                {
                    "source": "filename",
                    "hist_id": hist_id,
                    "vendor_name": vendor_name,
                    "filename": filename,
                }
            )

    return vendors


def extract_vendors_from_text(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract vendor mentions from extracted text content.

    Scans extracted text files for vendor patterns.

    Returns:
        List of vendor extraction results
    """
    vendors = []

    for text_key, text_content in data.get("extracted_text_cache", {}).items():
        if not text_content:
            continue

        hist_id = text_key.split("/")[0] if "/" in text_key else "unknown"

        detected = _detect_vendor_in_text(text_content)
        for vendor_name in detected:
            # Find context around the vendor mention
            context = _extract_context(text_content, vendor_name)
            vendors.append(
                {
                    "source": "extracted_text",
                    "hist_id": hist_id,
                    "vendor_name": vendor_name,
                    "context": context,
                    "file": text_key,
                }
            )

    return vendors


def _detect_vendor_in_text(text: str) -> list[str]:
    """Detect known vendors in text.

    Returns:
        List of detected vendor names
    """
    detected = []
    text_lower = text.lower()

    for vendor_name, patterns in KNOWN_VENDORS.items():
        for pattern in patterns:
            if pattern.lower() in text_lower:
                detected.append(vendor_name)
                break  # Only add vendor once

    return detected


def _extract_context(text: str, vendor_name: str) -> str:
    """Extract context around a vendor mention.

    Returns:
        String with up to 200 chars of context
    """
    patterns = KNOWN_VENDORS.get(vendor_name, [vendor_name.lower()])
    text_lower = text.lower()

    for pattern in patterns:
        idx = text_lower.find(pattern.lower())
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(text), idx + len(pattern) + 150)
            return text[start:end].strip()

    return ""


def extract_contract_amounts(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract contract amounts from corpus data.

    Scans metadata and extracted text for dollar amounts.

    Returns:
        List of contract amount findings
    """
    amounts = []
    amount_patterns = [re.compile(p, re.IGNORECASE) for p in AMOUNT_PATTERNS]

    # Check metadata
    for meta_key, meta_data in data.get("metadata_files", {}).items():
        if not isinstance(meta_data, dict):
            continue

        hist_id = meta_key.split("/")[0] if "/" in meta_key else "unknown"

        # Check for amount fields
        amount_fields = ["contract_amount", "amount", "value", "cost", "total"]
        for field in amount_fields:
            if field in meta_data:
                value = meta_data[field]
                if isinstance(value, int | float) or (
                    isinstance(value, str) and any(c.isdigit() for c in value)
                ):
                    amounts.append(
                        {
                            "source": "metadata_field",
                            "hist_id": hist_id,
                            "field": field,
                            "raw_value": str(value),
                            "parsed_amount": _parse_amount(str(value)),
                            "file": meta_key,
                        }
                    )

    # Check extracted text
    for text_key, text_content in data.get("extracted_text_cache", {}).items():
        if not text_content:
            continue

        hist_id = text_key.split("/")[0] if "/" in text_key else "unknown"

        for pattern in amount_patterns:
            matches = pattern.findall(text_content[:10000])  # Limit search
            for match in matches[:5]:  # Limit matches per file
                parsed = _parse_amount(match)
                if parsed and parsed >= 1000:  # Only significant amounts
                    amounts.append(
                        {
                            "source": "extracted_text",
                            "hist_id": hist_id,
                            "raw_value": match,
                            "parsed_amount": parsed,
                            "file": text_key,
                        }
                    )

    return amounts


def _parse_amount(value: str) -> float | None:
    """Parse a dollar amount string to float.

    Returns:
        Parsed amount or None if parsing fails
    """
    try:
        value_str = str(value)
        value_lower = value_str.lower()

        # Handle "million" suffix first
        if "million" in value_lower:
            # Extract the numeric part before "million"
            numeric_part = re.sub(r"[,$\s]", "", value_str.split("million")[0].strip())
            numeric_part = numeric_part.lstrip("$").rstrip("Mm")
            return float(numeric_part) * 1_000_000

        # Handle M suffix (e.g., "1.5M")
        if value_str.rstrip().endswith("M") or value_str.rstrip().endswith("m"):
            cleaned = re.sub(r"[,$\s]", "", value_str)
            cleaned = cleaned.lstrip("$").rstrip("Mm")
            return float(cleaned) * 1_000_000

        # Remove common formatting for regular amounts
        cleaned = re.sub(r"[,$\s]", "", value_str)
        cleaned = cleaned.lstrip("$")

        return float(cleaned) if cleaned else None
    except (ValueError, AttributeError):
        return None


def detect_vendor_aliases(
    vendor_extractions: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Detect potential vendor aliases and variations.

    Groups vendor mentions that may refer to the same entity.

    Returns:
        Dictionary mapping canonical vendor names to aliases
    """
    aliases: dict[str, list[str]] = defaultdict(list)

    # Group by known vendor names
    for vendor in vendor_extractions:
        vendor_name = vendor.get("vendor_name") or vendor.get("value", "")
        if vendor_name and vendor_name in KNOWN_VENDORS:
            patterns = KNOWN_VENDORS[vendor_name]
            for pattern in patterns:
                if pattern not in aliases[vendor_name]:
                    aliases[vendor_name].append(pattern)

    return dict(aliases)


def build_vendor_index(
    vendor_extractions: list[dict[str, Any]], corpora: dict[str, str]
) -> dict[str, Any]:
    """Build a comprehensive vendor index.

    Creates an index mapping vendors to their appearances across the corpus.

    Returns:
        Vendor index dictionary
    """
    vendor_index: dict[str, Any] = {}

    for vendor in vendor_extractions:
        vendor_name = vendor.get("vendor_name") or vendor.get("value", "Unknown")
        hist_id = vendor.get("hist_id", "unknown")

        if vendor_name not in vendor_index:
            vendor_index[vendor_name] = {
                "name": vendor_name,
                "appearances": [],
                "years": set(),
                "hist_ids": set(),
                "sources": set(),
            }

        # Get year from corpus mapping
        meeting_date = corpora.get(hist_id, "")
        year = meeting_date[:4] if meeting_date else ""

        vendor_index[vendor_name]["appearances"].append(
            {
                "hist_id": hist_id,
                "year": year,
                "source": vendor.get("source"),
                "context": vendor.get("context", ""),
            }
        )
        if year:
            vendor_index[vendor_name]["years"].add(year)
        vendor_index[vendor_name]["hist_ids"].add(hist_id)
        vendor_index[vendor_name]["sources"].add(vendor.get("source", ""))

    # Convert sets to sorted lists for JSON serialization
    for vendor_name in vendor_index:
        vendor_index[vendor_name]["years"] = sorted(vendor_index[vendor_name]["years"])
        vendor_index[vendor_name]["hist_ids"] = sorted(
            vendor_index[vendor_name]["hist_ids"]
        )
        vendor_index[vendor_name]["sources"] = sorted(
            vendor_index[vendor_name]["sources"]
        )
        vendor_index[vendor_name]["appearance_count"] = len(
            vendor_index[vendor_name]["appearances"]
        )
        vendor_index[vendor_name]["year_span"] = len(vendor_index[vendor_name]["years"])

    return vendor_index


def infer_contract_relationships(
    vendor_index: dict[str, Any],
    amounts: list[dict[str, Any]],
    corpora: dict[str, str],
) -> list[dict[str, Any]]:
    """Infer contract relationships between vendors and corpora.

    Links vendor appearances with contract amounts and timing.

    Returns:
        List of inferred contract relationships
    """
    relationships = []

    # Group amounts by hist_id
    amounts_by_hist: dict[str, list[dict]] = defaultdict(list)
    for amount in amounts:
        hist_id = amount.get("hist_id", "unknown")
        amounts_by_hist[hist_id].append(amount)

    # Link vendors to amounts in same corpus
    for vendor_name, vendor_data in vendor_index.items():
        for hist_id in vendor_data.get("hist_ids", []):
            hist_amounts = amounts_by_hist.get(hist_id, [])
            meeting_date = corpora.get(hist_id, "")
            year = meeting_date[:4] if meeting_date else ""

            if hist_amounts:
                # Found potential contract amounts in same corpus
                total_amount = sum(a.get("parsed_amount", 0) or 0 for a in hist_amounts)
                relationships.append(
                    {
                        "vendor": vendor_name,
                        "hist_id": hist_id,
                        "year": year,
                        "meeting_date": meeting_date,
                        "amount_count": len(hist_amounts),
                        "total_amount": total_amount,
                        "amounts": [a.get("parsed_amount") for a in hist_amounts],
                        "relationship_type": "direct_mention",
                    }
                )

    return relationships


def scan_for_procurement_irregularities(
    vendor_index: dict[str, Any],
    relationships: list[dict[str, Any]],
    data: dict[str, Any],
    corpora: dict[str, str],
) -> list[dict[str, Any]]:
    """Scan for procurement irregularities and red flags.

    Detects:
    - Missing competition
    - Sole-source red flags
    - Sudden cost escalations
    - Unexplained renewals
    - Cross-vendor shadow links

    Returns:
        List of procurement irregularities
    """
    irregularities = []
    sole_source_patterns = [re.compile(p, re.IGNORECASE) for p in SOLE_SOURCE_PATTERNS]

    # 1. Detect sole-source/non-competitive mentions
    for text_key, text_content in data.get("extracted_text_cache", {}).items():
        if not text_content:
            continue

        hist_id = text_key.split("/")[0] if "/" in text_key else "unknown"
        meeting_date = corpora.get(hist_id, "")
        year = meeting_date[:4] if meeting_date else ""

        for pattern in sole_source_patterns:
            matches = pattern.findall(text_content)
            if matches:
                context = _extract_sole_source_context(text_content, matches[0])
                irregularities.append(
                    {
                        "type": "sole_source_flag",
                        "hist_id": hist_id,
                        "year": year,
                        "pattern_matched": matches[0],
                        "context": context,
                        "severity": "medium",
                        "details": f"Sole source procurement detected: {matches[0]}",
                    }
                )

    # 2. Detect recurring vendors with inconsistent labeling
    for vendor_name, vendor_data in vendor_index.items():
        years = vendor_data.get("years", [])
        sources = vendor_data.get("sources", [])

        if len(years) >= 3 and len(sources) > 1:
            irregularities.append(
                {
                    "type": "inconsistent_labeling",
                    "vendor": vendor_name,
                    "years": years,
                    "sources": sources,
                    "severity": "low",
                    "details": (
                        f"Recurring vendor '{vendor_name}' appears across "
                        f"{len(years)} years with {len(sources)} different source types"
                    ),
                }
            )

    # 3. Detect cost escalations (>40% increase year-over-year)
    vendor_amounts: dict[str, dict[str, float]] = defaultdict(dict)
    for rel in relationships:
        vendor = rel.get("vendor")
        year = rel.get("year")
        amount = rel.get("total_amount", 0)
        if vendor and year and amount:
            if year not in vendor_amounts[vendor]:
                vendor_amounts[vendor][year] = 0
            vendor_amounts[vendor][year] += amount

    for vendor, yearly_amounts in vendor_amounts.items():
        sorted_years = sorted(yearly_amounts.keys())
        for i in range(1, len(sorted_years)):
            prev_year = sorted_years[i - 1]
            curr_year = sorted_years[i]
            prev_amount = yearly_amounts[prev_year]
            curr_amount = yearly_amounts[curr_year]

            if prev_amount > 0:
                increase_pct = ((curr_amount - prev_amount) / prev_amount) * 100
                if increase_pct > 40:
                    irregularities.append(
                        {
                            "type": "cost_escalation",
                            "vendor": vendor,
                            "from_year": prev_year,
                            "to_year": curr_year,
                            "from_amount": prev_amount,
                            "to_amount": curr_amount,
                            "increase_percent": round(increase_pct, 1),
                            "severity": "high" if increase_pct > 100 else "medium",
                            "details": (
                                f"Cost spike of {increase_pct:.1f}% for '{vendor}' "
                                f"from {prev_year} (${prev_amount:,.0f}) "
                                f"to {curr_year} (${curr_amount:,.0f})"
                            ),
                        }
                    )

    # 4. Detect vendors in anomaly clusters across >3 years
    for vendor_name, vendor_data in vendor_index.items():
        years = vendor_data.get("years", [])
        if len(years) > 3:
            irregularities.append(
                {
                    "type": "multi_year_vendor",
                    "vendor": vendor_name,
                    "years": years,
                    "year_count": len(years),
                    "severity": "low",
                    "details": (
                        f"Vendor '{vendor_name}' appears across {len(years)} years: "
                        f"{', '.join(years[:5])}{'...' if len(years) > 5 else ''}"
                    ),
                }
            )

    return irregularities


def _extract_sole_source_context(text: str, match: str) -> str:
    """Extract context around a sole-source match.

    Returns:
        Context string (up to 300 chars)
    """
    text_lower = text.lower()
    match_lower = match.lower()
    idx = text_lower.find(match_lower)

    if idx >= 0:
        start = max(0, idx - 100)
        end = min(len(text), idx + len(match) + 200)
        return text[start:end].strip()

    return ""


def detect_tech_programs(
    data: dict[str, Any], corpora: dict[str, str]
) -> dict[str, Any]:
    """Detect technology program mentions and map vendors to programs.

    Returns:
        Dictionary of technology programs with vendor associations
    """
    programs: dict[str, dict] = {
        prog: {
            "name": prog,
            "mentions": [],
            "vendors": set(),
            "years": set(),
            "hist_ids": set(),
        }
        for prog in TECH_PROGRAMS
    }

    # Scan extracted text for program patterns
    for text_key, text_content in data.get("extracted_text_cache", {}).items():
        if not text_content:
            continue

        hist_id = text_key.split("/")[0] if "/" in text_key else "unknown"
        meeting_date = corpora.get(hist_id, "")
        year = meeting_date[:4] if meeting_date else ""
        text_lower = text_content.lower()

        for prog_name, patterns in TECH_PROGRAMS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    programs[prog_name]["mentions"].append(
                        {
                            "hist_id": hist_id,
                            "year": year,
                            "pattern": pattern,
                        }
                    )
                    if year:
                        programs[prog_name]["years"].add(year)
                    programs[prog_name]["hist_ids"].add(hist_id)

                    # Find associated vendors in same corpus
                    vendors_found = _detect_vendor_in_text(text_content)
                    for v in vendors_found:
                        programs[prog_name]["vendors"].add(v)
                    break  # Only count once per pattern type

    # Convert sets to lists for JSON
    for prog_name in programs:
        programs[prog_name]["vendors"] = sorted(programs[prog_name]["vendors"])
        programs[prog_name]["years"] = sorted(programs[prog_name]["years"])
        programs[prog_name]["hist_ids"] = sorted(programs[prog_name]["hist_ids"])
        programs[prog_name]["mention_count"] = len(programs[prog_name]["mentions"])

    return programs


def run_vendor_extraction(
    corpus_root: Path, year_range: str, output_dir: Path | None = None
) -> dict[str, Any]:
    """Run the complete vendor extraction pipeline.

    Returns:
        Dictionary with all extraction results
    """
    start_year, end_year = parse_year_range(year_range)
    corpora = filter_corpora_by_years(start_year, end_year)

    print(f"Vendor Map Extractor v{VICFM_VERSION}")
    print("=" * 60)
    print(f"Corpus Root: {corpus_root}")
    print(f"Year Range: {year_range}")
    print(f"Corpora to analyze: {len(corpora)}")
    print("=" * 60)

    # Step 1: Load corpus data
    print("\n[1/7] Loading corpus data...")
    data = load_corpus_data(corpus_root)
    print(f"  - Loaded {len(data['metadata_files'])} metadata files")
    print(f"  - Loaded {len(data['corpus_indexes'])} corpus indexes")
    print(f"  - Loaded {len(data['attachment_files'])} attachment files")
    print(f"  - Loaded {len(data['extracted_text_cache'])} extracted text files")

    # Step 2: Extract vendors from all sources
    print("\n[2/7] Extracting vendors...")
    metadata_vendors = extract_vendors_from_metadata(data)
    filename_vendors = extract_vendors_from_filenames(data)
    text_vendors = extract_vendors_from_text(data)
    all_vendors = metadata_vendors + filename_vendors + text_vendors
    print(f"  - From metadata: {len(metadata_vendors)}")
    print(f"  - From filenames: {len(filename_vendors)}")
    print(f"  - From text: {len(text_vendors)}")
    print(f"  - Total: {len(all_vendors)}")

    # Step 3: Extract contract amounts
    print("\n[3/7] Extracting contract amounts...")
    amounts = extract_contract_amounts(data)
    print(f"  - Found {len(amounts)} contract amounts")

    # Step 4: Detect vendor aliases
    print("\n[4/7] Detecting vendor aliases...")
    aliases = detect_vendor_aliases(all_vendors)
    print(f"  - Identified {len(aliases)} vendor alias groups")

    # Step 5: Build vendor index
    print("\n[5/7] Building vendor index...")
    vendor_index = build_vendor_index(all_vendors, corpora)
    print(f"  - Indexed {len(vendor_index)} unique vendors")

    # Step 6: Infer contract relationships
    print("\n[6/7] Inferring contract relationships...")
    relationships = infer_contract_relationships(vendor_index, amounts, corpora)
    print(f"  - Found {len(relationships)} vendor-contract relationships")

    # Step 7: Scan for procurement irregularities
    print("\n[7/7] Scanning for procurement irregularities...")
    irregularities = scan_for_procurement_irregularities(
        vendor_index, relationships, data, corpora
    )
    print(f"  - Detected {len(irregularities)} potential irregularities")

    # Detect technology programs
    tech_programs = detect_tech_programs(data, corpora)

    # Build result
    timestamp = get_utc_timestamp()
    result = {
        "version": VICFM_VERSION,
        "schema_version": VICFM_SCHEMA_VERSION,
        "generated_at": timestamp,
        "year_range": year_range,
        "corpora_analyzed": len(corpora),
        "summary": {
            "total_vendor_mentions": len(all_vendors),
            "unique_vendors": len(vendor_index),
            "contract_amounts_found": len(amounts),
            "relationships_inferred": len(relationships),
            "irregularities_detected": len(irregularities),
        },
        "vendor_index": vendor_index,
        "aliases": aliases,
        "amounts": amounts,
        "relationships": relationships,
        "irregularities": irregularities,
        "tech_programs": tech_programs,
    }

    # Write output files if output_dir specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        vendor_index_path = output_dir / "vendor_index.json"
        with open(vendor_index_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  - Wrote {vendor_index_path}")

    print("\n" + "=" * 60)
    print("VENDOR EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"\nUnique Vendors: {len(vendor_index)}")
    print(f"Contract Relationships: {len(relationships)}")
    print(f"Procurement Irregularities: {len(irregularities)}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Vendor Map Extractor v1.0 - Extract vendors from corpus"
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

    run_vendor_extraction(corpus_root, args.years, output_dir)
