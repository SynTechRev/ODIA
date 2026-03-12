#!/usr/bin/env python3
"""Interdepartmental Correlation Matrix v1.0 - ICM Generator.

This module implements the Interdepartmental Correlation Matrix (ICM) that:
- Creates a weighted correlation matrix between agencies
- Scores influence direction and magnitude
- Integrates with ACE anomalies and VICFM vendor data
- Outputs CSV and NumPy-compatible formats

Scoring Formula:
    Score = (VendorOverlap * 0.25)
          + (TechStack * 0.20)
          + (ContractFlowSync * 0.20)
          + (ACE_Anomaly_Linkage * 0.20)
          + (ProgrammaticContinuity * 0.15)

Author: GitHub Copilot Agent
Date: 2025-12-06
"""

import argparse
import csv
import json
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
ICM_VERSION = "1.0"

# ICM scoring weights (same as CAIM)
WEIGHT_VENDOR_OVERLAP = 0.25
WEIGHT_TECH_STACK = 0.20
WEIGHT_CONTRACT_FLOW_SYNC = 0.20
WEIGHT_ACE_ANOMALY_LINKAGE = 0.20
WEIGHT_PROGRAMMATIC_CONTINUITY = 0.15


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


def calculate_jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets.

    Returns:
        Jaccard similarity (0-1)
    """
    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    return intersection / union if union > 0 else 0.0


def build_agency_maps(
    agency_index: dict[str, Any],
    vendor_data: dict[str, Any] | None,
    ace_report: dict[str, Any] | None,
) -> tuple[
    dict[str, set[str]],
    dict[str, set[str]],
    dict[str, set[str]],
    dict[str, set[str]],
    dict[str, set[str]],
]:
    """Build maps for agency relationships.

    Returns:
        Tuple of (vendor_map, tech_map, years_map, hist_map, anomaly_map)
    """
    agency_vendor_map: dict[str, set[str]] = defaultdict(set)
    agency_tech_map: dict[str, set[str]] = defaultdict(set)
    agency_years_map: dict[str, set[str]] = defaultdict(set)
    agency_hist_map: dict[str, set[str]] = defaultdict(set)
    agency_anomaly_map: dict[str, set[str]] = defaultdict(set)

    # Build basic maps from agency_index
    for agency_name, agency_info in agency_index.items():
        agency_hist_map[agency_name] = set(agency_info.get("hist_ids", []))
        agency_years_map[agency_name] = set(agency_info.get("years", []))

    # Process vendor data if available
    if vendor_data:
        vendor_index = vendor_data.get("vendor_index", {})
        for vendor_name, vendor_info in vendor_index.items():
            hist_ids = vendor_info.get("hist_ids", [])
            for hist_id in hist_ids:
                for agency_name, agency_info in agency_index.items():
                    if hist_id in agency_info.get("hist_ids", []):
                        agency_vendor_map[agency_name].add(vendor_name)

        # Process tech programs
        tech_programs = vendor_data.get("tech_programs", {})
        for prog_name, prog_info in tech_programs.items():
            hist_ids = prog_info.get("hist_ids", [])
            for hist_id in hist_ids:
                for agency_name, agency_info in agency_index.items():
                    if hist_id in agency_info.get("hist_ids", []):
                        agency_tech_map[agency_name].add(prog_name)

    # Process ACE anomalies if available
    if ace_report:
        by_hist_id = ace_report.get("by_hist_id", {})
        for hist_id, anomalies in by_hist_id.items():
            for anomaly in anomalies:
                anomaly_type = anomaly.get("type", "unknown")
                for agency_name, agency_info in agency_index.items():
                    if hist_id in agency_info.get("hist_ids", []):
                        agency_anomaly_map[agency_name].add(f"{hist_id}:{anomaly_type}")

    return (
        agency_vendor_map,
        agency_tech_map,
        agency_years_map,
        agency_hist_map,
        agency_anomaly_map,
    )


def calculate_icm_score(
    agency_a: str,
    agency_b: str,
    vendor_map: dict[str, set[str]],
    tech_map: dict[str, set[str]],
    years_map: dict[str, set[str]],
    hist_map: dict[str, set[str]],
    anomaly_map: dict[str, set[str]],
) -> dict[str, float]:
    """Calculate ICM score between two agencies.

    Returns:
        Dictionary with component scores and total
    """
    vendor_overlap = calculate_jaccard_similarity(
        vendor_map.get(agency_a, set()),
        vendor_map.get(agency_b, set()),
    )

    tech_stack = calculate_jaccard_similarity(
        tech_map.get(agency_a, set()),
        tech_map.get(agency_b, set()),
    )

    contract_flow_sync = calculate_jaccard_similarity(
        years_map.get(agency_a, set()),
        years_map.get(agency_b, set()),
    )

    ace_anomaly_linkage = calculate_jaccard_similarity(
        anomaly_map.get(agency_a, set()),
        anomaly_map.get(agency_b, set()),
    )

    programmatic_continuity = calculate_jaccard_similarity(
        hist_map.get(agency_a, set()),
        hist_map.get(agency_b, set()),
    )

    total_score = (
        (vendor_overlap * WEIGHT_VENDOR_OVERLAP)
        + (tech_stack * WEIGHT_TECH_STACK)
        + (contract_flow_sync * WEIGHT_CONTRACT_FLOW_SYNC)
        + (ace_anomaly_linkage * WEIGHT_ACE_ANOMALY_LINKAGE)
        + (programmatic_continuity * WEIGHT_PROGRAMMATIC_CONTINUITY)
    )

    return {
        "vendor_overlap": round(vendor_overlap, 4),
        "tech_stack": round(tech_stack, 4),
        "contract_flow_sync": round(contract_flow_sync, 4),
        "ace_anomaly_linkage": round(ace_anomaly_linkage, 4),
        "programmatic_continuity": round(programmatic_continuity, 4),
        "total_score": round(total_score, 4),
    }


def build_correlation_matrix(
    agency_index: dict[str, Any],
    vendor_data: dict[str, Any] | None,
    ace_report: dict[str, Any] | None,
) -> tuple[list[str], list[list[float]], dict[str, dict[str, dict[str, float]]]]:
    """Build the interdepartmental correlation matrix.

    Returns:
        Tuple of (agency_names, matrix, detailed_scores)
    """
    # Build agency maps
    (
        vendor_map,
        tech_map,
        years_map,
        hist_map,
        anomaly_map,
    ) = build_agency_maps(agency_index, vendor_data, ace_report)

    # Get sorted list of agencies
    agency_names = sorted(agency_index.keys())
    n = len(agency_names)

    # Initialize matrix
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    detailed_scores: dict[str, dict[str, dict[str, float]]] = {}

    # Calculate pairwise scores
    for i, agency_a in enumerate(agency_names):
        detailed_scores[agency_a] = {}
        for j, agency_b in enumerate(agency_names):
            if i == j:
                # Self-correlation is 1.0
                matrix[i][j] = 1.0
                detailed_scores[agency_a][agency_b] = {
                    "vendor_overlap": 1.0,
                    "tech_stack": 1.0,
                    "contract_flow_sync": 1.0,
                    "ace_anomaly_linkage": 1.0,
                    "programmatic_continuity": 1.0,
                    "total_score": 1.0,
                }
            else:
                scores = calculate_icm_score(
                    agency_a,
                    agency_b,
                    vendor_map,
                    tech_map,
                    years_map,
                    hist_map,
                    anomaly_map,
                )
                matrix[i][j] = scores["total_score"]
                detailed_scores[agency_a][agency_b] = scores

    return agency_names, matrix, detailed_scores


def generate_influence_matrix_csv(
    agency_names: list[str],
    matrix: list[list[float]],
) -> list[list[str]]:
    """Generate influence_matrix.csv data.

    Returns:
        List of CSV rows
    """
    # Header row with agency names
    header = ["Agency"] + agency_names
    rows = [header]

    # Data rows
    for i, agency_name in enumerate(agency_names):
        row = [agency_name] + [str(round(score, 4)) for score in matrix[i]]
        rows.append(row)

    return rows


def generate_matrix_numpy_format(
    agency_names: list[str],
    matrix: list[list[float]],
) -> dict[str, Any]:
    """Generate NumPy-compatible format for the matrix.

    Returns:
        Dictionary with matrix data and metadata
    """
    return {
        "agency_names": agency_names,
        "matrix": matrix,
        "shape": [len(agency_names), len(agency_names)],
        "dtype": "float64",
    }


def identify_high_correlation_pairs(
    agency_names: list[str],
    matrix: list[list[float]],
    threshold: float = 0.3,
) -> list[dict[str, Any]]:
    """Identify agency pairs with high correlation.

    Returns:
        List of high-correlation pairs
    """
    pairs = []
    n = len(agency_names)

    for i in range(n):
        for j in range(i + 1, n):
            score = matrix[i][j]
            if score >= threshold:
                pairs.append(
                    {
                        "agency_a": agency_names[i],
                        "agency_b": agency_names[j],
                        "correlation_score": round(score, 4),
                        "tier": categorize_correlation(score),
                    }
                )

    # Sort by score descending
    pairs.sort(key=lambda x: x["correlation_score"], reverse=True)
    return pairs


def categorize_correlation(score: float) -> str:
    """Categorize correlation score into tier.

    Returns:
        Tier string (Critical, High, Moderate, Low, Minimal)
    """
    if score >= 0.8:
        return "Critical"
    elif score >= 0.6:
        return "High"
    elif score >= 0.4:
        return "Moderate"
    elif score >= 0.2:
        return "Low"
    else:
        return "Minimal"


def calculate_matrix_statistics(
    matrix: list[list[float]],
) -> dict[str, float]:
    """Calculate statistics for the correlation matrix.

    Returns:
        Dictionary of statistics
    """
    n = len(matrix)
    if n == 0:
        return {
            "mean": 0.0,
            "max": 0.0,
            "min": 0.0,
            "density": 0.0,
        }

    # Collect off-diagonal values
    values = []
    for i in range(n):
        for j in range(n):
            if i != j:
                values.append(matrix[i][j])

    if not values:
        return {
            "mean": 0.0,
            "max": 0.0,
            "min": 0.0,
            "density": 0.0,
        }

    # Calculate statistics
    mean_val = sum(values) / len(values)
    max_val = max(values)
    min_val = min(values)

    # Density: proportion of non-zero values
    non_zero = sum(1 for v in values if v > 0)
    density = non_zero / len(values)

    return {
        "mean": round(mean_val, 4),
        "max": round(max_val, 4),
        "min": round(min_val, 4),
        "density": round(density, 4),
    }


def load_agency_extraction(extraction_path: Path) -> dict[str, Any]:
    """Load agency extraction results.

    Returns:
        Extraction data dictionary
    """
    if extraction_path.exists():
        try:
            with open(extraction_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_vendor_data(vendor_path: Path | None) -> dict[str, Any]:
    """Load vendor extraction data.

    Returns:
        Vendor data dictionary
    """
    if vendor_path and vendor_path.exists():
        try:
            with open(vendor_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_ace_report(ace_path: Path | None) -> dict[str, Any]:
    """Load ACE report.

    Returns:
        ACE report dictionary
    """
    if ace_path is None:
        ace_path = Path("ACE_REPORT.json")

    if ace_path.exists():
        try:
            with open(ace_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def run_icm_generation(
    agency_data: dict[str, Any],
    year_range: str,
    output_dir: Path | None = None,
    vendor_data: dict[str, Any] | None = None,
    ace_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the ICM generation pipeline.

    Returns:
        Dictionary with matrix and analysis results
    """
    print(f"Interdepartmental Correlation Matrix v{ICM_VERSION}")
    print("=" * 60)

    agency_index = agency_data.get("agency_index", {})

    print(f"Year Range: {year_range}")
    print(f"Agencies: {len(agency_index)}")
    print("=" * 60)

    # Build correlation matrix
    print("\n[1/3] Building correlation matrix...")
    agency_names, matrix, detailed_scores = build_correlation_matrix(
        agency_index, vendor_data, ace_report
    )
    print(f"  - Matrix size: {len(agency_names)} x {len(agency_names)}")

    # Calculate statistics
    print("\n[2/3] Calculating matrix statistics...")
    stats = calculate_matrix_statistics(matrix)
    print(f"  - Mean correlation: {stats['mean']}")
    print(f"  - Max correlation: {stats['max']}")
    print(f"  - Matrix density: {stats['density']}")

    # Identify high correlation pairs
    high_pairs = identify_high_correlation_pairs(agency_names, matrix)
    print(f"  - High correlation pairs (≥0.3): {len(high_pairs)}")

    # Generate outputs
    print("\n[3/3] Generating output files...")
    timestamp = get_utc_timestamp()

    csv_rows = generate_influence_matrix_csv(agency_names, matrix)
    numpy_format = generate_matrix_numpy_format(agency_names, matrix)

    icm_result = {
        "version": ICM_VERSION,
        "generated_at": timestamp,
        "year_range": year_range,
        "summary": {
            "agency_count": len(agency_names),
            "matrix_dimensions": f"{len(agency_names)}x{len(agency_names)}",
            "statistics": stats,
            "high_correlation_pairs": len(high_pairs),
        },
        "scoring_weights": {
            "vendor_overlap": WEIGHT_VENDOR_OVERLAP,
            "tech_stack": WEIGHT_TECH_STACK,
            "contract_flow_sync": WEIGHT_CONTRACT_FLOW_SYNC,
            "ace_anomaly_linkage": WEIGHT_ACE_ANOMALY_LINKAGE,
            "programmatic_continuity": WEIGHT_PROGRAMMATIC_CONTINUITY,
        },
        "agency_names": agency_names,
        "matrix": matrix,
        "numpy_format": numpy_format,
        "detailed_scores": detailed_scores,
        "high_correlation_pairs": high_pairs,
    }

    # Write files
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # influence_matrix.csv
        csv_path = output_dir / "influence_matrix.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
        print(f"  - Wrote {csv_path}")

        # icm_matrix.json (full result)
        json_path = output_dir / "icm_matrix.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(icm_result, f, indent=2, default=str)
        print(f"  - Wrote {json_path}")

    print("\n" + "=" * 60)
    print("ICM GENERATION COMPLETE")
    print("=" * 60)

    # Print top pairs
    if high_pairs:
        print("\nTop 5 Correlated Agency Pairs:")
        for i, pair in enumerate(high_pairs[:5], 1):
            print(
                f"  {i}. {pair['agency_a']} ↔ {pair['agency_b']}: "
                f"{pair['correlation_score']} ({pair['tier']})"
            )

    return icm_result


def main():
    """Run ICM generation from command line."""
    parser = argparse.ArgumentParser(
        description="Interdepartmental Correlation Matrix v1.0"
    )
    parser.add_argument(
        "--agency-data",
        type=str,
        required=True,
        help="Path to agency extraction JSON file",
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2014-2025",
        help="Year range to analyze",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Output directory for matrix files",
    )
    parser.add_argument(
        "--vendor-data",
        type=str,
        default=None,
        help="Path to vendor extraction JSON file",
    )
    parser.add_argument(
        "--ace-report",
        type=str,
        default=None,
        help="Path to ACE_REPORT.json",
    )

    args = parser.parse_args()

    agency_data_path = Path(args.agency_data)
    if not agency_data_path.exists():
        print(f"Error: Agency data file not found: {agency_data_path}")
        sys.exit(1)

    agency_data = load_agency_extraction(agency_data_path)
    if not agency_data:
        print("Error: Failed to load agency extraction data")
        sys.exit(1)

    vendor_data = None
    if args.vendor_data:
        vendor_data = load_vendor_data(Path(args.vendor_data))

    ace_report = None
    if args.ace_report:
        ace_report = load_ace_report(Path(args.ace_report))

    run_icm_generation(
        agency_data,
        args.years,
        Path(args.output),
        vendor_data,
        ace_report,
    )


if __name__ == "__main__":
    main()
