#!/usr/bin/env python3
"""Forensic Integration Module - ACE/VICFM/CAIM Cross-linking.

This module provides integration between the PDF Forensics layer and
existing ACE, VICFM, and CAIM analysis layers.

Author: GitHub Copilot Agent
Date: 2025-12-06
"""

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

DPMM_VERSION = "1.0"


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_json_report(path: Path) -> dict[str, Any] | None:
    """Load a JSON report file.

    Returns:
        Loaded JSON dict or None if file doesn't exist/is invalid
    """
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def generate_forensic_anomaly_links(
    forensic_report: dict[str, Any],
    ace_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate cross-links between forensic anomalies and ACE anomalies.

    Links forensic findings to ACE-flagged anomalies by:
    - Matching hist_ids
    - Correlating anomaly types
    - Calculating overlap scores

    Returns:
        FORENSIC_ANOMALY_LINKS.json structure
    """
    result: dict[str, Any] = {
        "version": DPMM_VERSION,
        "generated_at": get_utc_timestamp(),
        "links": [],
        "summary": {
            "total_links": 0,
            "forensic_anomalies_linked": 0,
            "ace_anomalies_linked": 0,
            "overlap_by_hist_id": {},
        },
    }

    if not ace_report:
        return result

    # Get forensic anomalies by hist_id
    forensic_by_hist: dict[str, list[dict]] = defaultdict(list)
    for anomaly in forensic_report.get("anomalies", []):
        hist_id = anomaly.get("hist_id")
        if hist_id:
            forensic_by_hist[hist_id].append(anomaly)

    # Get ACE anomalies by hist_id
    ace_by_hist = ace_report.get("by_hist_id", {})

    # Find overlapping hist_ids
    overlapping_ids = set(forensic_by_hist.keys()) & set(ace_by_hist.keys())

    forensic_linked_count = 0
    ace_linked_count = 0

    for hist_id in overlapping_ids:
        forensic_anomalies = forensic_by_hist[hist_id]
        ace_anomalies = ace_by_hist[hist_id]

        # Create links for each pairing
        for f_anomaly in forensic_anomalies:
            for a_anomaly in ace_anomalies:
                link = {
                    "hist_id": hist_id,
                    "forensic_anomaly": {
                        "type": f_anomaly.get("type"),
                        "subtype": f_anomaly.get("subtype"),
                        "severity": f_anomaly.get("severity"),
                        "details": f_anomaly.get("details", "")[:100],
                    },
                    "ace_anomaly": {
                        "type": a_anomaly.get("type"),
                        "subtype": a_anomaly.get("subtype"),
                        "ace_score": a_anomaly.get("ace_score"),
                        "details": a_anomaly.get("details", "")[:100],
                    },
                    "correlation_type": _determine_correlation_type(
                        f_anomaly, a_anomaly
                    ),
                }
                result["links"].append(link)
                forensic_linked_count += 1

        ace_linked_count += len(ace_anomalies)

        result["summary"]["overlap_by_hist_id"][hist_id] = {
            "forensic_count": len(forensic_anomalies),
            "ace_count": len(ace_anomalies),
        }

    result["summary"]["total_links"] = len(result["links"])
    result["summary"]["forensic_anomalies_linked"] = forensic_linked_count
    result["summary"]["ace_anomalies_linked"] = ace_linked_count

    return result


def _determine_correlation_type(
    forensic_anomaly: dict[str, Any],
    ace_anomaly: dict[str, Any],
) -> str:
    """Determine the correlation type between forensic and ACE anomalies."""
    f_type = forensic_anomaly.get("type", "")
    a_type = ace_anomaly.get("type", "")

    # Direct type matches
    if "temporal" in f_type and "chronological" in a_type:
        return "temporal_correlation"
    if "xmp" in f_type and "schema" in a_type:
        return "metadata_correlation"
    if "producer" in f_type and "attachment" in a_type:
        return "software_correlation"
    if "retroactive" in f_type:
        return "edit_pattern_correlation"

    return "general_correlation"


def generate_forensic_vendor_overlaps(
    forensic_report: dict[str, Any],
    vendor_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate overlaps between forensic findings and vendor data.

    Links producer/creator forensics to vendor influence patterns.

    Returns:
        FORENSIC_VENDOR_OVERLAPS.json structure
    """
    result: dict[str, Any] = {
        "version": DPMM_VERSION,
        "generated_at": get_utc_timestamp(),
        "overlaps": [],
        "vendor_software_map": {},
        "summary": {
            "total_overlaps": 0,
            "vendors_with_forensic_flags": [],
        },
    }

    # Build vendor software map from forensic data
    vendor_software_counts: dict[str, int] = defaultdict(int)

    for anomaly in forensic_report.get("anomalies", []):
        if anomaly.get("type") == "producer_anomaly":
            if anomaly.get("subtype") == "vendor_software_detected":
                vendor = anomaly.get("vendor", "unknown")
                vendor_software_counts[vendor] += 1

                result["overlaps"].append(
                    {
                        "hist_id": anomaly.get("hist_id"),
                        "file_path": anomaly.get("file_path"),
                        "vendor": vendor,
                        "producer": anomaly.get("producer"),
                        "creator": anomaly.get("creator"),
                        "pattern_matched": anomaly.get("pattern_matched"),
                    }
                )

    result["vendor_software_map"] = dict(vendor_software_counts)
    result["summary"]["total_overlaps"] = len(result["overlaps"])
    result["summary"]["vendors_with_forensic_flags"] = list(
        vendor_software_counts.keys()
    )

    # Cross-reference with vendor report if available
    if vendor_report:
        vendor_index = vendor_report.get("vendor_index", {})
        for vendor in result["summary"]["vendors_with_forensic_flags"]:
            if vendor in vendor_index:
                vendor_data = vendor_index[vendor]
                result["overlaps"].append(
                    {
                        "type": "vendor_index_match",
                        "vendor": vendor,
                        "appearance_count": vendor_data.get("appearance_count", 0),
                        "years": vendor_data.get("years", []),
                    }
                )

    return result


def generate_forensic_agency_patterns(
    forensic_report: dict[str, Any],
    agency_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate agency-level patterns from forensic findings.

    Links forensic anomalies to agency/CAIM patterns.

    Returns:
        FORENSIC_AGENCY_PATTERNS.json structure
    """
    result: dict[str, Any] = {
        "version": DPMM_VERSION,
        "generated_at": get_utc_timestamp(),
        "patterns": [],
        "by_origin_cluster": {},
        "summary": {
            "total_patterns": 0,
            "clusters_with_anomalies": 0,
        },
    }

    # Group anomalies by origin cluster
    clusters = forensic_report.get("clusters", {}).get("clusters", {})

    for cluster_name, cluster_data in clusters.items():
        members = cluster_data.get("members", [])
        member_paths = {m.get("file_path") for m in members}

        # Find anomalies for files in this cluster
        cluster_anomalies = []
        for anomaly in forensic_report.get("anomalies", []):
            if anomaly.get("file_path") in member_paths:
                cluster_anomalies.append(
                    {
                        "type": anomaly.get("type"),
                        "subtype": anomaly.get("subtype"),
                        "severity": anomaly.get("severity"),
                    }
                )

        if cluster_anomalies:
            result["by_origin_cluster"][cluster_name] = {
                "member_count": cluster_data.get("member_count", 0),
                "origin_type": cluster_data.get("origin_type"),
                "vendor": cluster_data.get("vendor"),
                "anomaly_count": len(cluster_anomalies),
                "anomalies": cluster_anomalies[:10],  # Limit for readability
            }
            result["summary"]["clusters_with_anomalies"] += 1

    # Generate patterns based on anomaly clustering
    anomaly_type_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for anomaly in forensic_report.get("anomalies", []):
        meeting_date = anomaly.get("meeting_date", "")
        year = meeting_date[:4] if meeting_date else "unknown"
        anomaly_type = anomaly.get("type", "unknown")
        anomaly_type_counts[anomaly_type][year] += 1

    for anomaly_type, year_counts in anomaly_type_counts.items():
        if len(year_counts) >= 2:  # Pattern spans multiple years
            result["patterns"].append(
                {
                    "type": "multi_year_pattern",
                    "anomaly_type": anomaly_type,
                    "years_affected": sorted(year_counts.keys()),
                    "counts_by_year": dict(year_counts),
                    "total_count": sum(year_counts.values()),
                }
            )

    result["summary"]["total_patterns"] = len(result["patterns"])

    return result


def run_forensic_integration(
    forensic_report_path: Path,
    output_dir: Path,
    ace_report_path: Path | None = None,
    vendor_report_path: Path | None = None,
    agency_report_path: Path | None = None,
) -> dict[str, Any]:
    """Run the complete forensic integration pipeline.

    Generates:
    - FORENSIC_ANOMALY_LINKS.json
    - FORENSIC_VENDOR_OVERLAPS.json
    - FORENSIC_AGENCY_PATTERNS.json

    Returns:
        Summary of integration results
    """
    print(f"DPMM v{DPMM_VERSION} - Forensic Integration")
    print("=" * 60)

    # Load forensic report
    forensic_report = load_json_report(forensic_report_path)
    if not forensic_report:
        print(f"Error: Could not load forensic report from {forensic_report_path}")
        return {"error": "forensic report not found"}

    print(
        f"Loaded forensic report with {len(forensic_report.get('anomalies', []))} anomalies"
    )

    # Load optional reports
    ace_report = load_json_report(ace_report_path) if ace_report_path else None
    vendor_report = load_json_report(vendor_report_path) if vendor_report_path else None
    agency_report = load_json_report(agency_report_path) if agency_report_path else None

    if ace_report:
        print(
            f"Loaded ACE report with {len(ace_report.get('all_anomalies', []))} anomalies"
        )
    if vendor_report:
        print("Loaded vendor report")
    if agency_report:
        print("Loaded agency report")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate ACE links
    print("\n[1/3] Generating forensic-ACE anomaly links...")
    anomaly_links = generate_forensic_anomaly_links(forensic_report, ace_report)
    links_path = output_dir / "FORENSIC_ANOMALY_LINKS.json"
    with open(links_path, "w", encoding="utf-8") as f:
        json.dump(anomaly_links, f, indent=2)
        f.write("\n")
    print(f"  - Generated {anomaly_links['summary']['total_links']} links")
    print(f"  - Wrote {links_path}")

    # Generate vendor overlaps
    print("\n[2/3] Generating forensic-vendor overlaps...")
    vendor_overlaps = generate_forensic_vendor_overlaps(forensic_report, vendor_report)
    overlaps_path = output_dir / "FORENSIC_VENDOR_OVERLAPS.json"
    with open(overlaps_path, "w", encoding="utf-8") as f:
        json.dump(vendor_overlaps, f, indent=2)
        f.write("\n")
    print(f"  - Generated {vendor_overlaps['summary']['total_overlaps']} overlaps")
    print(f"  - Wrote {overlaps_path}")

    # Generate agency patterns
    print("\n[3/3] Generating forensic-agency patterns...")
    agency_patterns = generate_forensic_agency_patterns(forensic_report, agency_report)
    patterns_path = output_dir / "FORENSIC_AGENCY_PATTERNS.json"
    with open(patterns_path, "w", encoding="utf-8") as f:
        json.dump(agency_patterns, f, indent=2)
        f.write("\n")
    print(f"  - Generated {agency_patterns['summary']['total_patterns']} patterns")
    print(f"  - Wrote {patterns_path}")

    print("\n" + "=" * 60)
    print("FORENSIC INTEGRATION COMPLETE")
    print("=" * 60)

    return {
        "anomaly_links": anomaly_links["summary"],
        "vendor_overlaps": vendor_overlaps["summary"],
        "agency_patterns": agency_patterns["summary"],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="DPMM v1.0 - Forensic Integration Module"
    )
    parser.add_argument(
        "--forensic-report",
        type=str,
        required=True,
        help="Path to forensic_report.json",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="analysis/pdf_forensics",
        help="Output directory for integration reports",
    )
    parser.add_argument(
        "--ace-report",
        type=str,
        default=None,
        help="Path to ACE_REPORT.json",
    )
    parser.add_argument(
        "--vendor-report",
        type=str,
        default=None,
        help="Path to vendor_index.json",
    )
    parser.add_argument(
        "--agency-report",
        type=str,
        default=None,
        help="Path to agency_index.json",
    )

    args = parser.parse_args()

    run_forensic_integration(
        forensic_report_path=Path(args.forensic_report).resolve(),
        output_dir=Path(args.output).resolve(),
        ace_report_path=Path(args.ace_report).resolve() if args.ace_report else None,
        vendor_report_path=(
            Path(args.vendor_report).resolve() if args.vendor_report else None
        ),
        agency_report_path=(
            Path(args.agency_report).resolve() if args.agency_report else None
        ),
    )
