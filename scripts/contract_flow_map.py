#!/usr/bin/env python3
"""Contract Flow Map v1.0.

This module generates the Contract Flow Map (2014-2025) showing:
- Year-by-year vendor activity
- New vendor arrivals
- Vendor exits
- Contract renewals
- Technology program expansions

Outputs:
- CONTRACT_FLOW_MAP.json
- CONTRACT_FLOW_MAP.md

Author: GitHub Copilot Agent
Date: 2025-12-06
"""

import argparse
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
VICFM_VERSION = "1.0"


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


def build_yearly_vendor_activity(
    vendor_index: dict[str, Any], year_range: str
) -> dict[str, dict[str, Any]]:
    """Build year-by-year vendor activity summary.

    Returns:
        Dictionary mapping year to activity data
    """
    start_year, end_year = parse_year_range(year_range)
    yearly_data: dict[str, dict[str, Any]] = {}

    # Initialize all years
    for year in range(start_year, end_year + 1):
        year_str = str(year)
        yearly_data[year_str] = {
            "year": year_str,
            "active_vendors": [],
            "new_vendors": [],
            "exiting_vendors": [],
            "continuing_vendors": [],
            "total_active": 0,
        }

    # Track vendor activity across years
    vendor_years: dict[str, list[str]] = {}
    for vendor_name, vendor_data in vendor_index.items():
        vendor_years[vendor_name] = sorted(vendor_data.get("years", []))

    # Populate yearly data
    all_years = [str(y) for y in range(start_year, end_year + 1)]
    prev_active: set[str] = set()

    for year_str in all_years:
        current_active = set()

        for vendor_name, years in vendor_years.items():
            if year_str in years:
                current_active.add(vendor_name)
                yearly_data[year_str]["active_vendors"].append(vendor_name)

        # Determine new, exiting, continuing
        new_vendors = current_active - prev_active
        exiting_vendors = prev_active - current_active
        continuing_vendors = current_active & prev_active

        yearly_data[year_str]["new_vendors"] = sorted(new_vendors)
        yearly_data[year_str]["continuing_vendors"] = sorted(continuing_vendors)
        yearly_data[year_str]["total_active"] = len(current_active)

        # Track exiters for previous year
        if year_str != all_years[0]:
            prev_year = str(int(year_str) - 1)
            yearly_data[prev_year]["exiting_vendors"] = sorted(exiting_vendors)

        prev_active = current_active

    return yearly_data


def detect_contract_renewals(
    vendor_index: dict[str, Any],
) -> list[dict[str, Any]]:
    """Detect potential contract renewals.

    A renewal is inferred when a vendor appears in consecutive years.

    Returns:
        List of renewal patterns
    """
    renewals = []

    for vendor_name, vendor_data in vendor_index.items():
        years = sorted(vendor_data.get("years", []))
        if len(years) < 2:
            continue

        # Find consecutive year sequences
        consecutive_start = years[0]
        consecutive_count = 1

        for i in range(1, len(years)):
            if int(years[i]) == int(years[i - 1]) + 1:
                consecutive_count += 1
            else:
                if consecutive_count >= 2:
                    renewals.append(
                        {
                            "vendor": vendor_name,
                            "start_year": consecutive_start,
                            "end_year": years[i - 1],
                            "consecutive_years": consecutive_count,
                            "type": "consecutive_renewal",
                        }
                    )
                consecutive_start = years[i]
                consecutive_count = 1

        # Check last sequence
        if consecutive_count >= 2:
            renewals.append(
                {
                    "vendor": vendor_name,
                    "start_year": consecutive_start,
                    "end_year": years[-1],
                    "consecutive_years": consecutive_count,
                    "type": "consecutive_renewal",
                }
            )

    return renewals


def build_tech_program_timeline(
    tech_programs: dict[str, Any], year_range: str
) -> dict[str, dict[str, Any]]:
    """Build technology program timeline.

    Returns:
        Dictionary of program timelines
    """
    start_year, end_year = parse_year_range(year_range)
    timeline: dict[str, dict[str, Any]] = {}

    for prog_name, prog_data in tech_programs.items():
        years = prog_data.get("years", [])
        if not years:
            continue

        timeline[prog_name] = {
            "program": prog_name,
            "first_appearance": min(years) if years else None,
            "last_appearance": max(years) if years else None,
            "years_active": sorted(years),
            "year_count": len(years),
            "vendors_associated": prog_data.get("vendors", []),
            "status": _determine_program_status(years, str(end_year)),
        }

    return timeline


def _determine_program_status(years: list[str], current_year: str) -> str:
    """Determine program status based on activity.

    Returns:
        Status string
    """
    if not years:
        return "inactive"

    max_year = max(years)
    if max_year == current_year:
        return "active"
    elif int(current_year) - int(max_year) <= 2:
        return "recent"
    else:
        return "historical"


def generate_contract_flow_map(
    vendor_index: dict[str, Any],
    relationships: list[dict[str, Any]],
    tech_programs: dict[str, Any],
    year_range: str,
) -> dict[str, Any]:
    """Generate the complete contract flow map.

    Returns:
        Contract flow map dictionary
    """
    timestamp = get_utc_timestamp()
    start_year, end_year = parse_year_range(year_range)

    # Build components
    yearly_activity = build_yearly_vendor_activity(vendor_index, year_range)
    renewals = detect_contract_renewals(vendor_index)
    program_timeline = build_tech_program_timeline(tech_programs, year_range)

    # Calculate summary statistics
    all_vendors = set(vendor_index.keys())
    vendors_by_year_count: dict[int, list[str]] = defaultdict(list)
    for vendor_name, vendor_data in vendor_index.items():
        year_count = len(vendor_data.get("years", []))
        vendors_by_year_count[year_count].append(vendor_name)

    # Find long-term vendors (5+ years)
    long_term_vendors = []
    for count in sorted(vendors_by_year_count.keys(), reverse=True):
        if count >= 5:
            long_term_vendors.extend(vendors_by_year_count[count])

    # Calculate contract amounts by year
    amounts_by_year: dict[str, float] = defaultdict(float)
    for rel in relationships:
        year = rel.get("year", "")
        amount = rel.get("total_amount", 0) or 0
        if year:
            amounts_by_year[year] += amount

    flow_map = {
        "version": VICFM_VERSION,
        "generated_at": timestamp,
        "year_range": year_range,
        "summary": {
            "total_vendors": len(all_vendors),
            "years_covered": end_year - start_year + 1,
            "total_renewals_detected": len(renewals),
            "long_term_vendors": len(long_term_vendors),
            "technology_programs_tracked": len(program_timeline),
        },
        "yearly_activity": yearly_activity,
        "contract_renewals": renewals,
        "program_timeline": program_timeline,
        "amounts_by_year": dict(amounts_by_year),
        "vendor_longevity": {
            "long_term_5plus": sorted(long_term_vendors),
            "by_year_count": {
                str(k): sorted(v)
                for k, v in sorted(vendors_by_year_count.items(), reverse=True)
            },
        },
    }

    return flow_map


def generate_contract_flow_map_md(flow_map: dict[str, Any]) -> str:
    """Generate CONTRACT_FLOW_MAP.md markdown content.

    Returns:
        Markdown string
    """
    lines = [
        "# Contract Flow Map (2014–2025)",
        "",
        f"**Generated:** {flow_map['generated_at']}",
        f"**Version:** {flow_map['version']}",
        "",
        "## Executive Summary",
        "",
    ]

    summary = flow_map.get("summary", {})
    lines.extend(
        [
            f"- **Total Vendors Tracked:** {summary.get('total_vendors', 0)}",
            f"- **Years Covered:** {summary.get('years_covered', 0)}",
            f"- **Contract Renewals Detected:** {summary.get('total_renewals_detected', 0)}",
            f"- **Long-term Vendors (5+ years):** {summary.get('long_term_vendors', 0)}",
            f"- **Technology Programs Tracked:** {summary.get('technology_programs_tracked', 0)}",
            "",
            "---",
            "",
            "## Year-by-Year Vendor Activity",
            "",
        ]
    )

    # Yearly activity table
    yearly = flow_map.get("yearly_activity", {})
    lines.extend(
        [
            "| Year | Active | New | Exiting | Continuing |",
            "|------|--------|-----|---------|------------|",
        ]
    )

    for year in sorted(yearly.keys()):
        data = yearly[year]
        lines.append(
            f"| {year} | {data.get('total_active', 0)} | "
            f"{len(data.get('new_vendors', []))} | "
            f"{len(data.get('exiting_vendors', []))} | "
            f"{len(data.get('continuing_vendors', []))} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## New Vendor Arrivals by Year",
            "",
        ]
    )

    for year in sorted(yearly.keys()):
        new_vendors = yearly[year].get("new_vendors", [])
        if new_vendors:
            lines.append(f"### {year}")
            for vendor in new_vendors[:10]:  # Limit display
                lines.append(f"- {vendor}")
            if len(new_vendors) > 10:
                lines.append(f"- *...and {len(new_vendors) - 10} more*")
            lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Contract Renewal Patterns",
            "",
            "Vendors with consecutive-year contracts (potential renewals):",
            "",
        ]
    )

    renewals = flow_map.get("contract_renewals", [])
    # Sort by consecutive years (descending)
    sorted_renewals = sorted(
        renewals, key=lambda x: x.get("consecutive_years", 0), reverse=True
    )

    for renewal in sorted_renewals[:15]:  # Top 15
        lines.append(
            f"- **{renewal.get('vendor', 'Unknown')}**: "
            f"{renewal.get('start_year')} – {renewal.get('end_year')} "
            f"({renewal.get('consecutive_years', 0)} consecutive years)"
        )

    if len(renewals) > 15:
        lines.append(f"- *...and {len(renewals) - 15} more renewal patterns*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Technology Program Timeline",
            "",
        ]
    )

    program_timeline = flow_map.get("program_timeline", {})
    for prog_name, prog_data in sorted(
        program_timeline.items(), key=lambda x: x[1].get("first_appearance", "9999")
    ):
        status = prog_data.get("status", "unknown")
        status_emoji = {"active": "🟢", "recent": "🟡", "historical": "⚪"}.get(
            status, "⚪"
        )
        lines.extend(
            [
                f"### {prog_name} {status_emoji}",
                "",
                f"- **First Appearance:** {prog_data.get('first_appearance', 'N/A')}",
                f"- **Last Appearance:** {prog_data.get('last_appearance', 'N/A')}",
                f"- **Years Active:** {prog_data.get('year_count', 0)}",
                f"- **Status:** {status.title()}",
            ]
        )

        vendors = prog_data.get("vendors_associated", [])
        if vendors:
            lines.append(f"- **Associated Vendors:** {', '.join(vendors[:5])}")
            if len(vendors) > 5:
                lines.append(f"  - *(+{len(vendors) - 5} more)*")

        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Long-term Vendors (5+ Years)",
            "",
        ]
    )

    longevity = flow_map.get("vendor_longevity", {})
    long_term = longevity.get("long_term_5plus", [])
    for vendor in long_term[:20]:
        # Get years for this vendor
        by_count = longevity.get("by_year_count", {})
        year_count = 0
        for count_str, vendors in by_count.items():
            if vendor in vendors:
                year_count = int(count_str)
                break
        lines.append(f"- {vendor} ({year_count} years)")

    if len(long_term) > 20:
        lines.append(f"- *...and {len(long_term) - 20} more*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Contract Amounts by Year",
            "",
            "| Year | Total Amount |",
            "|------|--------------|",
        ]
    )

    amounts = flow_map.get("amounts_by_year", {})
    for year in sorted(amounts.keys()):
        amount = amounts[year]
        lines.append(f"| {year} | ${amount:,.0f} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "*Generated by Vendor Influence & Contract Flow Map v1.0*",
        ]
    )

    return "\n".join(lines)


def load_vendor_data(path: Path) -> dict[str, Any]:
    """Load vendor extraction data from JSON file.

    Returns:
        Vendor data dictionary
    """
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def run_contract_flow_map(
    vendor_data: dict[str, Any],
    year_range: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the contract flow map generation pipeline.

    Returns:
        Contract flow map dictionary
    """
    print(f"Contract Flow Map Generator v{VICFM_VERSION}")
    print("=" * 60)
    print(f"Year Range: {year_range}")
    print("=" * 60)

    vendor_index = vendor_data.get("vendor_index", {})
    relationships = vendor_data.get("relationships", [])
    tech_programs = vendor_data.get("tech_programs", {})

    print(f"\nVendors: {len(vendor_index)}")
    print(f"Relationships: {len(relationships)}")
    print(f"Tech Programs: {len(tech_programs)}")

    # Generate flow map
    print("\n[1/2] Generating contract flow map...")
    flow_map = generate_contract_flow_map(
        vendor_index, relationships, tech_programs, year_range
    )

    # Generate markdown
    print("[2/2] Generating markdown report...")
    flow_map_md = generate_contract_flow_map_md(flow_map)

    # Write output files
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / "CONTRACT_FLOW_MAP.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(flow_map, f, indent=2, default=str)
        print(f"  - Wrote {json_path}")

        md_path = output_dir / "CONTRACT_FLOW_MAP.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(flow_map_md)
        print(f"  - Wrote {md_path}")

    print("\n" + "=" * 60)
    print("CONTRACT FLOW MAP GENERATION COMPLETE")
    print("=" * 60)

    summary = flow_map.get("summary", {})
    print(f"\nTotal Vendors: {summary.get('total_vendors', 0)}")
    print(f"Contract Renewals: {summary.get('total_renewals_detected', 0)}")
    print(f"Long-term Vendors: {summary.get('long_term_vendors', 0)}")

    return flow_map


def main():
    """Run the contract flow map generator from command line."""
    parser = argparse.ArgumentParser(description="Contract Flow Map Generator v1.0")
    parser.add_argument(
        "--vendor-data",
        type=str,
        required=True,
        help="Path to vendor extraction JSON file",
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
        help="Output directory for flow map files",
    )

    args = parser.parse_args()

    vendor_data_path = Path(args.vendor_data)
    if not vendor_data_path.exists():
        print(f"Error: Vendor data file not found: {vendor_data_path}")
        sys.exit(1)

    vendor_data = load_vendor_data(vendor_data_path)
    if not vendor_data:
        print("Error: Failed to load vendor data")
        sys.exit(1)

    run_contract_flow_map(vendor_data, args.years, Path(args.output))


if __name__ == "__main__":
    main()
