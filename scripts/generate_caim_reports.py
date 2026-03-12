#!/usr/bin/env python3
"""CAIM Reports Generator v1.0 - Generate all CAIM-ICM artifacts.

This module generates all output artifacts for the Cross-Agency Influence Map
and Interdepartmental Correlation Matrix:
- agency_graph.json
- cross_agency_edges.csv
- influence_matrix.csv
- agency_correlation_heatmap.png
- AGENCY_INFLUENCE_REPORT.md
- ICM_EXPLANATION.md

Author: GitHub Copilot Agent
Date: 2025-12-06
"""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.agency_map_extractor import (  # noqa: E402
    run_agency_extraction,
)
from scripts.cross_agency_influence import (  # noqa: E402
    load_ace_report,
    load_vendor_data,
    run_cross_agency_influence,
)
from scripts.interdepartmental_matrix import (  # noqa: E402
    run_icm_generation,
)

# Constants
CAIM_VERSION = "1.0"

# Scoring weights for documentation
SCORING_WEIGHTS = {
    "vendor_overlap": 0.25,
    "tech_stack": 0.20,
    "contract_flow_sync": 0.20,
    "ace_anomaly_linkage": 0.20,
    "programmatic_continuity": 0.15,
}


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def generate_agency_influence_report_md(
    agency_data: dict[str, Any],
    caim_result: dict[str, Any],
    icm_result: dict[str, Any],
) -> str:
    """Generate AGENCY_INFLUENCE_REPORT.md content.

    Returns:
        Markdown string
    """
    timestamp = get_utc_timestamp()
    agency_index = agency_data.get("agency_index", {})

    lines = [
        "# Agency Influence Report (2014–2025)",
        "",
        f"**Generated:** {timestamp}",
        f"**Version:** {CAIM_VERSION}",
        "",
        "## Executive Summary",
        "",
    ]

    # Summary stats
    summary = agency_data.get("summary", {})
    icm_summary = icm_result.get("summary", {})

    high_pairs_count = icm_summary.get("high_correlation_pairs", 0)
    lines.extend(
        [
            f"- **Total Agencies Analyzed:** {summary.get('unique_agencies', 0)}",
            f"- **Total Agency Mentions:** {summary.get('total_agency_mentions', 0)}",
            f"- **Agency Relationships:** {summary.get('relationships_found', 0)}",
            f"- **High Correlation Pairs:** {high_pairs_count}",
            "",
            "---",
            "",
            "## Top Agencies by Appearance Count",
            "",
            "| Rank | Agency | Type | Years | Appearances |",
            "|------|--------|------|-------|-------------|",
        ]
    )

    # Sort agencies by appearance count
    sorted_agencies = sorted(
        agency_index.items(),
        key=lambda x: x[1].get("appearance_count", 0),
        reverse=True,
    )

    for i, (agency_name, agency_info) in enumerate(sorted_agencies[:15], 1):
        agency_type = agency_info.get("type", "unknown")
        years = agency_info.get("year_span", 0)
        appearances = agency_info.get("appearance_count", 0)
        lines.append(
            f"| {i} | {agency_name} | {agency_type} | {years} | {appearances} |"
        )

    # High correlation pairs
    high_pairs = icm_result.get("high_correlation_pairs", [])

    lines.extend(
        [
            "",
            "---",
            "",
            "## High Correlation Agency Pairs",
            "",
            "These agency pairs show significant interdependence based on "
            "shared vendors, technology stacks, contract timing, and anomaly patterns.",
            "",
            "| Rank | Agency A | Agency B | Score | Tier |",
            "|------|----------|----------|-------|------|",
        ]
    )

    for i, pair in enumerate(high_pairs[:20], 1):
        agency_a = pair.get("agency_a", "")
        agency_b = pair.get("agency_b", "")
        score = pair.get("correlation_score", 0)
        tier = pair.get("tier", "")
        lines.append(f"| {i} | {agency_a} | {agency_b} | {score:.4f} | {tier} |")

    # Agencies by type
    lines.extend(
        [
            "",
            "---",
            "",
            "## Agencies by Type",
            "",
        ]
    )

    by_type: dict[str, list[str]] = {}
    for agency_name, agency_info in agency_index.items():
        agency_type = agency_info.get("type", "unknown")
        if agency_type not in by_type:
            by_type[agency_type] = []
        by_type[agency_type].append(agency_name)

    for agency_type, agencies in sorted(by_type.items()):
        lines.append(f"### {agency_type.title()}")
        lines.append("")
        for agency in sorted(agencies):
            info = agency_index.get(agency, {})
            lines.append(
                f"- **{agency}**: {info.get('appearance_count', 0)} appearances, "
                f"{info.get('year_span', 0)} years"
            )
        lines.append("")

    # Year-by-year activity
    lines.extend(
        [
            "---",
            "",
            "## Year-by-Year Agency Activity",
            "",
        ]
    )

    year_agency_count: dict[str, int] = {}
    for _, agency_info in agency_index.items():
        for year in agency_info.get("years", []):
            if year not in year_agency_count:
                year_agency_count[year] = 0
            year_agency_count[year] += 1

    lines.append("| Year | Active Agencies |")
    lines.append("|------|-----------------|")

    for year in sorted(year_agency_count.keys()):
        count = year_agency_count[year]
        lines.append(f"| {year} | {count} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Matrix Statistics",
            "",
        ]
    )

    stats = icm_summary.get("statistics", {})
    lines.extend(
        [
            f"- **Mean Correlation:** {stats.get('mean', 0)}",
            f"- **Max Correlation:** {stats.get('max', 0)}",
            f"- **Min Correlation:** {stats.get('min', 0)}",
            f"- **Matrix Density:** {stats.get('density', 0)}",
            "",
            "---",
            "",
            "*Generated by CAIM-ICM v1.0*",
        ]
    )

    return "\n".join(lines)


def generate_icm_explanation_md() -> str:
    """Generate ICM_EXPLANATION.md content.

    Returns:
        Markdown string
    """
    timestamp = get_utc_timestamp()

    lines = [
        "# Interdepartmental Correlation Matrix (ICM) - Explanation",
        "",
        f"**Generated:** {timestamp}",
        f"**Version:** {CAIM_VERSION}",
        "",
        "## Overview",
        "",
        "The **Interdepartmental Correlation Matrix (ICM)** is a weighted matrix that ",
        "scores relationships between agencies based on multiple factors derived from ",
        "the legislative corpus, vendor data, and anomaly patterns.",
        "",
        "## Scoring Formula",
        "",
        "The ICM score between two agencies is calculated as:",
        "",
        "```",
        "Score = (VendorOverlap × 0.25)",
        "      + (TechStack × 0.20)",
        "      + (ContractFlowSync × 0.20)",
        "      + (ACE_Anomaly_Linkage × 0.20)",
        "      + (ProgrammaticContinuity × 0.15)",
        "```",
        "",
        "## Component Descriptions",
        "",
        "### 1. Vendor Overlap (25%)",
        "",
        "Measures the proportion of shared vendors between two agencies using ",
        "Jaccard similarity:",
        "",
        "- Agencies sharing common contractors score higher",
        "- Indicates potential procurement coordination or dependencies",
        "- Data sourced from VICFM vendor extraction",
        "",
        "### 2. Technology Stack (20%)",
        "",
        "Measures similarity in technology program deployments:",
        "",
        "- ALPR (Automated License Plate Readers)",
        "- Body-worn cameras",
        "- Cellular infrastructure",
        "- Video surveillance",
        "- Enterprise software",
        "",
        "Agencies with overlapping technology investments show higher correlation.",
        "",
        "### 3. Contract Flow Sync (20%)",
        "",
        "Measures temporal alignment of agency activities:",
        "",
        "- Agencies active in the same fiscal years score higher",
        "- Indicates synchronized budget cycles or coordinated procurement",
        "- Helps identify agencies with aligned planning horizons",
        "",
        "### 4. ACE Anomaly Linkage (20%)",
        "",
        "Measures shared anomaly patterns from the Anomaly Correlation Engine:",
        "",
        "- Agencies appearing in corpus items with similar anomalies",
        "- Structural gaps, extraction issues, chronological drift",
        "- High scores may indicate shared data quality challenges",
        "",
        "### 5. Programmatic Continuity (15%)",
        "",
        "Measures co-occurrence in the same legislative corpus items:",
        "",
        "- Agencies mentioned together in meetings, staff reports, contracts",
        "- Direct indicator of interdepartmental collaboration",
        "- Captures formal relationship documentation",
        "",
        "## Score Interpretation",
        "",
        "### Correlation Tiers",
        "",
        "| Score Range | Tier | Interpretation |",
        "|-------------|------|----------------|",
        "| ≥ 0.80 | Critical | Highly interdependent, strong formal ties |",
        "| 0.60 - 0.79 | High | Significant relationship, shared resources |",
        "| 0.40 - 0.59 | Moderate | Notable interaction, some shared vendors |",
        "| 0.20 - 0.39 | Low | Occasional interaction, limited overlap |",
        "| < 0.20 | Minimal | Little to no detected relationship |",
        "",
        "### Matrix Properties",
        "",
        "- **Symmetric**: Score(A,B) = Score(B,A)",
        "- **Diagonal**: Self-correlation is always 1.0",
        "- **Bounded**: All scores fall between 0.0 and 1.0",
        "",
        "## Data Sources",
        "",
        "### Input Data",
        "",
        "| Source | Purpose |",
        "|--------|---------|",
        "| Agency Index | Agency appearances in corpus |",
        "| VICFM Vendor Index | Vendor-agency relationships |",
        "| VICFM Tech Programs | Technology deployments |",
        "| ACE Report | Anomaly patterns |",
        "| Corpus Metadata | Meeting dates, document types |",
        "",
        "### Output Files",
        "",
        "| File | Description |",
        "|------|-------------|",
        "| `influence_matrix.csv` | Full correlation matrix in CSV format |",
        "| `icm_matrix.json` | Detailed scores and metadata |",
        "| `agency_correlation_heatmap.png` | Visual representation |",
        "",
        "## Integration with CAIM",
        "",
        "The ICM provides the quantitative foundation for the Cross-Agency ",
        "Influence Map (CAIM):",
        "",
        "1. **ICM scores become edge weights** in the CAIM graph",
        "2. **High-correlation pairs** are prioritized for analysis",
        "3. **Component scores** enable decomposition of relationships",
        "",
        "## Limitations",
        "",
        "- **Correlation ≠ Causation**: High scores indicate co-occurrence, ",
        "  not causal relationships",
        "- **Data Availability**: Scores depend on corpus completeness",
        "- **Temporal Resolution**: Annual granularity may miss short-term patterns",
        "- **Name Resolution**: Agency aliases may affect accuracy",
        "",
        "## Usage Examples",
        "",
        "### Identifying Procurement Clusters",
        "",
        "```python",
        "# Find agencies with shared vendor dependencies",
        "high_vendor_overlap = [",
        "    pair for pair in icm_result['detailed_scores']",
        "    if pair['vendor_overlap'] > 0.5",
        "]",
        "```",
        "",
        "### Detecting Anomaly Propagation Risk",
        "",
        "```python",
        "# Find agencies that share anomaly patterns",
        "anomaly_clusters = [",
        "    pair for pair in icm_result['high_correlation_pairs']",
        "    if pair['ace_anomaly_linkage'] > 0.3",
        "]",
        "```",
        "",
        "---",
        "",
        "*Generated by CAIM-ICM v1.0*",
    ]

    return "\n".join(lines)


def generate_heatmap_placeholder(
    agency_names: list[str],
    matrix: list[list[float]],
    output_path: Path,
) -> bool:
    """Generate a placeholder for the heatmap.

    In a full implementation, this would use matplotlib/seaborn.
    For now, generates a text-based representation.

    Returns:
        True if successful
    """
    try:
        # Try to import matplotlib for actual heatmap
        import matplotlib

        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        n = len(agency_names)
        if n == 0:
            return False

        # Truncate agency names for display
        display_names = [
            name[:15] + "..." if len(name) > 15 else name for name in agency_names
        ]

        # Create figure
        fig, ax = plt.subplots(figsize=(max(10, n * 0.5), max(8, n * 0.4)))

        # Create heatmap
        im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")

        # Configure axes
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(display_names, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(display_names, fontsize=8)

        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Correlation Score", rotation=-90, va="bottom")

        # Title
        ax.set_title("Agency Correlation Heatmap (ICM)")

        # Save
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return True
    except ImportError:
        # matplotlib not available, create a text placeholder
        with open(output_path.with_suffix(".txt"), "w") as f:
            f.write("Agency Correlation Heatmap\n")
            f.write("=" * 40 + "\n\n")
            f.write("Note: matplotlib not available for PNG generation.\n")
            f.write("See influence_matrix.csv for the raw data.\n\n")
            f.write(f"Matrix dimensions: {len(agency_names)} x {len(agency_names)}\n")
        return False


def run_caim_reports(
    corpus_root: Path,
    year_range: str,
    output_dir: Path,
    vendor_data_path: Path | None = None,
    ace_report_path: Path | None = None,
) -> dict[str, Any]:
    """Run the complete CAIM reports generation pipeline.

    Returns:
        Dictionary with all results
    """
    print(f"CAIM Reports Generator v{CAIM_VERSION}")
    print("=" * 60)
    print(f"Corpus Root: {corpus_root}")
    print(f"Year Range: {year_range}")
    print(f"Output Directory: {output_dir}")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load optional data
    vendor_data = load_vendor_data(vendor_data_path) if vendor_data_path else None
    ace_report = load_ace_report(ace_report_path)

    # Step 1: Run agency extraction
    print("\n[1/5] Running agency extraction...")
    agency_data = run_agency_extraction(corpus_root, year_range, output_dir)

    # Step 2: Run CAIM graph generation
    print("\n[2/5] Building cross-agency influence graph...")
    caim_result = run_cross_agency_influence(
        agency_data, year_range, output_dir, vendor_data, ace_report
    )

    # Step 3: Run ICM generation
    print("\n[3/5] Generating interdepartmental correlation matrix...")
    icm_result = run_icm_generation(
        agency_data, year_range, output_dir, vendor_data, ace_report
    )

    # Step 4: Generate markdown reports
    print("\n[4/5] Generating markdown reports...")

    # AGENCY_INFLUENCE_REPORT.md
    influence_report = generate_agency_influence_report_md(
        agency_data, caim_result, icm_result
    )
    influence_report_path = output_dir / "AGENCY_INFLUENCE_REPORT.md"
    with open(influence_report_path, "w", encoding="utf-8") as f:
        f.write(influence_report)
    print(f"  - Wrote {influence_report_path}")

    # ICM_EXPLANATION.md
    icm_explanation = generate_icm_explanation_md()
    icm_explanation_path = output_dir / "ICM_EXPLANATION.md"
    with open(icm_explanation_path, "w", encoding="utf-8") as f:
        f.write(icm_explanation)
    print(f"  - Wrote {icm_explanation_path}")

    # Step 5: Generate heatmap
    print("\n[5/5] Generating heatmap visualization...")
    heatmap_path = output_dir / "agency_correlation_heatmap.png"
    agency_names = icm_result.get("agency_names", [])
    matrix = icm_result.get("matrix", [])
    heatmap_generated = generate_heatmap_placeholder(agency_names, matrix, heatmap_path)
    if heatmap_generated:
        print(f"  - Wrote {heatmap_path}")
    else:
        print("  - Heatmap generation skipped (matplotlib not available)")

    print("\n" + "=" * 60)
    print("CAIM REPORTS GENERATION COMPLETE")
    print("=" * 60)
    print("\nGenerated artifacts:")
    print("  - agency_index.json")
    print("  - agency_graph.json")
    print("  - cross_agency_edges.csv")
    print("  - influence_matrix.csv")
    print("  - icm_matrix.json")
    print("  - AGENCY_INFLUENCE_REPORT.md")
    print("  - ICM_EXPLANATION.md")
    if heatmap_generated:
        print("  - agency_correlation_heatmap.png")

    return {
        "agency_data": agency_data,
        "caim_result": caim_result,
        "icm_result": icm_result,
    }


def main():
    """Run CAIM reports generation from command line."""
    parser = argparse.ArgumentParser(description="CAIM Reports Generator v1.0")
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
        help="Year range to analyze",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Output directory for all reports",
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
    corpus_root = Path(args.corpus_root).resolve()
    output_dir = Path(args.output).resolve()

    if not corpus_root.exists():
        print(f"Error: Corpus root not found: {corpus_root}")
        sys.exit(1)

    vendor_data_path = Path(args.vendor_data) if args.vendor_data else None
    ace_report_path = Path(args.ace_report) if args.ace_report else None

    run_caim_reports(
        corpus_root,
        args.years,
        output_dir,
        vendor_data_path,
        ace_report_path,
    )


if __name__ == "__main__":
    main()
