#!/usr/bin/env python3
"""ACE v1.0 - Anomaly Correlation Engine.

A deterministic pipeline that cross-references anomalies, missing data patterns,
metadata irregularities, and multi-year deviations across the finalized 11-year
corpus (2014-2025).

ACE correlates: structure → integrity → extraction → metadata → chronology
into a single unified anomaly model.

Author: GitHub Copilot Agent
Date: 2025-12-05
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import HIST_FILES  # noqa: E402

# Constants
CORPUS_ROOT = Path("oraculus/corpus")
CORPUS_PATTERN = re.compile(r"(HIST-\d{4,5}|#\d{2}-\d{4})")
EXPECTED_CATEGORIES = ["agendas", "minutes", "staff_reports", "attachments"]

# ACE Configuration
ACE_VERSION = "1.0"
ACE_SCHEMA_VERSION = "1.0"

# Anomaly Categories
ANOMALY_CATEGORIES = [
    "chronological_drift",
    "extraction_inconsistency",
    "attachment_signature_deviation",
    "structural_gap",
    "schema_irregularity",
    "high_risk_flag",
    "semantic_misalignment",  # MSH-v1: Semantic Harmonization integration
]

# Scoring thresholds
SCORE_MILD = 1
SCORE_REPEATED = 2
SCORE_MULTI_YEAR = 3
SCORE_STRUCTURAL = 4
SCORE_HIGH_RISK = 5

# High-risk threshold: anomaly type repeated across different years
HIGH_RISK_THRESHOLD = 3

# Surveillance vendor patterns (for attachment signature detection)
SURVEILLANCE_PATTERNS = [
    r"ALPR",
    r"Axon",
    r"Flock",
    r"license.?plate.?reader",
    r"body.?cam",
    r"surveillance",
    r"tracking",
    r"biometric",
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


def load_reports(corpus_root: Path) -> dict[str, Any]:
    """Load all relevant reports for ACE analysis.

    Inputs:
    - ingestion_report.json
    - VALIDATION_REPORT.json
    - audit_extension_report.json
    - missing_items_log.json
    - All metadata.json files across all corpus items

    Returns:
        Dictionary containing all loaded report data
    """
    reports: dict[str, Any] = {
        "ingestion_report": None,
        "validation_report": None,
        "audit_extension_report": None,
        "missing_items_log": None,
        "metadata_files": {},
        "corpus_indexes": {},
    }

    # Load ingestion report
    ingestion_path = corpus_root / "ingestion_report.json"
    if ingestion_path.exists():
        with open(ingestion_path, encoding="utf-8") as f:
            reports["ingestion_report"] = json.load(f)

    # Load validation report (from project root)
    validation_path = Path("VALIDATION_REPORT.json")
    if validation_path.exists():
        with open(validation_path, encoding="utf-8") as f:
            reports["validation_report"] = json.load(f)

    # Load audit extension report
    audit_path = corpus_root / "audit_extension_report.json"
    if audit_path.exists():
        with open(audit_path, encoding="utf-8") as f:
            reports["audit_extension_report"] = json.load(f)

    # Load missing items log
    missing_path = corpus_root / "missing_items_log.json"
    if missing_path.exists():
        with open(missing_path, encoding="utf-8") as f:
            reports["missing_items_log"] = json.load(f)

    # Load all metadata.json files and corpus indexes
    for entry in corpus_root.iterdir():
        if entry.is_dir() and CORPUS_PATTERN.match(entry.name):
            # Load metadata files
            metadata_dir = entry / "metadata"
            if metadata_dir.exists():
                for meta_file in metadata_dir.glob("*.json"):
                    if meta_file.name not in ("index.json",):
                        try:
                            with open(meta_file, encoding="utf-8") as f:
                                key = f"{entry.name}/{meta_file.name}"
                                reports["metadata_files"][key] = json.load(f)
                        except (json.JSONDecodeError, OSError):
                            pass

            # Load corpus index
            index_path = entry / "index.json"
            if index_path.exists():
                try:
                    with open(index_path, encoding="utf-8") as f:
                        reports["corpus_indexes"][entry.name] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass

    return reports


def scan_metadata_for_outliers(reports: dict[str, Any]) -> list[dict[str, Any]]:
    """Scan metadata files for outliers and irregularities.

    Detects:
    - Missing required fields
    - Malformed field values
    - Inconsistent field patterns
    - Schema deviations

    Returns:
        List of detected metadata anomalies
    """
    anomalies = []
    required_fields = [
        "meeting_date",
        "source_url",
        "file_hash",
        "corpus_id",
    ]

    for meta_key, meta_data in reports.get("metadata_files", {}).items():
        if not isinstance(meta_data, dict):
            anomalies.append(
                {
                    "type": "schema_irregularity",
                    "subtype": "invalid_metadata_format",
                    "hist_id": meta_key.split("/")[0] if "/" in meta_key else "unknown",
                    "file": meta_key,
                    "details": "Metadata is not a valid JSON object",
                    "severity": "high",
                }
            )
            continue

        hist_id = meta_key.split("/")[0] if "/" in meta_key else "unknown"

        # Check for missing required fields
        missing_fields = []
        for field in required_fields:
            if field not in meta_data or not meta_data[field]:
                missing_fields.append(field)

        if missing_fields:
            anomalies.append(
                {
                    "type": "schema_irregularity",
                    "subtype": "missing_required_fields",
                    "hist_id": hist_id,
                    "file": meta_key,
                    "details": f"Missing required fields: {', '.join(missing_fields)}",
                    "missing_fields": missing_fields,
                    "severity": "medium",
                }
            )

        # Check for malformed meeting_date
        if "meeting_date" in meta_data and meta_data["meeting_date"]:
            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            if not date_pattern.match(str(meta_data["meeting_date"])):
                malformed_date = meta_data["meeting_date"]
                anomalies.append(
                    {
                        "type": "schema_irregularity",
                        "subtype": "malformed_date",
                        "hist_id": hist_id,
                        "file": meta_key,
                        "details": f"Malformed meeting_date: {malformed_date}",
                        "severity": "medium",
                    }
                )

        # Check for placeholder source URLs
        if "source_url" in meta_data:
            url = str(meta_data.get("source_url", ""))
            if "NEEDS_USER_INPUT" in url or url == "":
                anomalies.append(
                    {
                        "type": "schema_irregularity",
                        "subtype": "placeholder_source_url",
                        "hist_id": hist_id,
                        "file": meta_key,
                        "details": "Source URL is placeholder or empty",
                        "severity": "low",
                    }
                )

    return anomalies


def correlate_anomalies_by_hist_id(
    reports: dict[str, Any], anomalies: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Correlate all anomalies by hist_id for unified view.

    Returns:
        Dictionary mapping hist_id to list of associated anomalies
    """
    correlated: dict[str, list[dict[str, Any]]] = defaultdict(list)

    # Add existing anomalies
    for anomaly in anomalies:
        hist_id = anomaly.get("hist_id", "unknown")
        correlated[hist_id].append(anomaly)

    # Add anomalies from validation report
    validation = reports.get("validation_report")
    if validation:
        # Check for missing categories from details
        details = validation.get("details", {})
        for year, year_data in details.items():
            if isinstance(year_data, list):
                for entry in year_data:
                    hist_id = entry.get("folder", "unknown")
                    missing_cats = entry.get("missing_categories", [])
                    for cat in missing_cats:
                        correlated[hist_id].append(
                            {
                                "type": "structural_gap",
                                "subtype": "missing_category",
                                "hist_id": hist_id,
                                "year": year,
                                "details": f"Missing category: {cat}",
                                "severity": "medium",
                            }
                        )

    # Add anomalies from ingestion report
    ingestion = reports.get("ingestion_report")
    if ingestion:
        flagged = ingestion.get("flagged_irregularities", [])
        for flag in flagged:
            if isinstance(flag, dict):
                details = flag.get("details", {})
                hist_id = (
                    details.get("hist_id", "unknown")
                    if isinstance(details, dict)
                    else "unknown"
                )
                correlated[hist_id].append(
                    {
                        "type": "structural_gap",
                        "subtype": flag.get("type", "unknown"),
                        "hist_id": hist_id,
                        "details": str(details),
                        "severity": "medium",
                    }
                )

    # Add anomalies from audit extension report
    audit_ext = reports.get("audit_extension_report")
    if audit_ext:
        flagged = audit_ext.get("flagged_irregularities", [])
        for flag in flagged:
            if isinstance(flag, dict):
                details = flag.get("details", {})
                hist_id = (
                    details.get("hist_id", "unknown")
                    if isinstance(details, dict)
                    else "unknown"
                )
                correlated[hist_id].append(
                    {
                        "type": "structural_gap",
                        "subtype": flag.get("type", "unknown"),
                        "hist_id": hist_id,
                        "details": str(details),
                        "severity": "medium",
                    }
                )

    # Add anomalies from missing items log
    missing_log = reports.get("missing_items_log")
    if missing_log:
        for category in [
            "missing_agendas",
            "missing_minutes",
            "missing_staff_reports",
            "missing_attachments",
        ]:
            items = missing_log.get(category, [])
            for item in items:
                if isinstance(item, dict):
                    hist_id = item.get("hist_id", "unknown")
                    correlated[hist_id].append(
                        {
                            "type": "structural_gap",
                            "subtype": category,
                            "hist_id": hist_id,
                            "year": item.get("year", "unknown"),
                            "empty": item.get("empty", False),
                            "details": f"Missing data: {category}",
                            "severity": "medium" if item.get("empty") else "low",
                        }
                    )

    return dict(correlated)


def detect_cross_year_irregularities(
    correlated: dict[str, list[dict[str, Any]]], corpora: dict[str, str]
) -> list[dict[str, Any]]:
    """Detect irregularities that span multiple years.

    Detects:
    - Chronological drift (meeting date mismatches)
    - Time-gap irregularities
    - Patterns repeated across years

    Returns:
        List of cross-year anomalies
    """
    anomalies = []

    # Group anomalies by type and year
    anomalies_by_type_year: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for hist_id, hist_anomalies in correlated.items():
        if hist_id in corpora:
            meeting_date = corpora[hist_id]
            year = meeting_date[:4]
        else:
            year = "unknown"

        for anomaly in hist_anomalies:
            atype = anomaly.get("type", "unknown")
            anomalies_by_type_year[atype][year] += 1

    # Detect patterns repeated across multiple years
    for atype, year_counts in anomalies_by_type_year.items():
        years_affected = [y for y, count in year_counts.items() if count > 0]
        if len(years_affected) >= HIGH_RISK_THRESHOLD:
            total_count = sum(year_counts.values())
            anomalies.append(
                {
                    "type": "high_risk_flag",
                    "subtype": "multi_year_pattern",
                    "pattern_type": atype,
                    "years_affected": sorted(years_affected),
                    "total_occurrences": total_count,
                    "details": (
                        f"Anomaly type '{atype}' repeated across "
                        f"{len(years_affected)} years ({total_count} total)"
                    ),
                    "severity": "critical",
                }
            )

    # Detect chronological drift
    sorted_corpora = sorted(corpora.items(), key=lambda x: x[1])
    prev_date = None
    for i, (hist_id, meeting_date) in enumerate(sorted_corpora):
        if prev_date:
            try:
                current = datetime.strptime(meeting_date, "%Y-%m-%d")
                previous = datetime.strptime(prev_date, "%Y-%m-%d")
                gap_days = (current - previous).days

                # Large gaps (>180 days) within same year could indicate issues
                prev_year = int(prev_date[:4])
                curr_year = int(meeting_date[:4])

                if gap_days > 180 and prev_year == curr_year:
                    anomalies.append(
                        {
                            "type": "chronological_drift",
                            "subtype": "large_time_gap",
                            "hist_id": hist_id,
                            "previous_hist_id": sorted_corpora[i - 1][0],
                            "gap_days": gap_days,
                            "year": str(curr_year),
                            "details": (
                                f"Large gap of {gap_days} days within year {curr_year}"
                            ),
                            "severity": "low",
                        }
                    )
            except ValueError:
                pass

        prev_date = meeting_date

    # Check for duplicate dates (potential data quality issue)
    date_counts: dict[str, list[str]] = defaultdict(list)
    for hist_id, date in corpora.items():
        date_counts[date].append(hist_id)

    for date, hist_ids in date_counts.items():
        if len(hist_ids) > 1:
            hist_ids_str = ", ".join(hist_ids)
            details_msg = f"Multiple corpora share date {date}: {hist_ids_str}"
            anomalies.append(
                {
                    "type": "chronological_drift",
                    "subtype": "duplicate_dates",
                    "date": date,
                    "hist_ids": hist_ids,
                    "details": details_msg,
                    "severity": "low",
                }
            )

    return anomalies


def detect_attachment_signatures(
    reports: dict[str, Any], corpora: dict[str, str]
) -> list[dict[str, Any]]:
    """Detect surveillance-related attachment patterns in 2021-2025 data.

    Looks for patterns like:
    - ALPR (Automated License Plate Reader)
    - Axon body cameras
    - Flock surveillance systems

    Returns:
        List of attachment signature anomalies
    """
    anomalies = []
    surveillance_hits: dict[str, list[dict]] = defaultdict(list)

    # Compile patterns
    patterns = [re.compile(p, re.IGNORECASE) for p in SURVEILLANCE_PATTERNS]

    # Scan corpus indexes for attachment information
    for hist_id, index_data in reports.get("corpus_indexes", {}).items():
        if hist_id not in corpora:
            continue

        meeting_date = corpora.get(hist_id, "")
        year = int(meeting_date[:4]) if meeting_date else 0

        # Focus on 2021-2025 as specified
        if year < 2021:
            continue

        # Check statistics for attachment counts
        stats = index_data.get("statistics", {})
        by_type = stats.get("by_type", {})
        attachment_count = by_type.get("attachment", 0)

        if attachment_count > 0:
            # Check file names/descriptions for surveillance patterns
            files = index_data.get("files", [])
            for file_info in files:
                if isinstance(file_info, dict):
                    file_name = str(file_info.get("file_name", ""))
                    for pattern in patterns:
                        if pattern.search(file_name):
                            surveillance_hits[pattern.pattern].append(
                                {
                                    "hist_id": hist_id,
                                    "year": str(year),
                                    "file_name": file_name,
                                }
                            )
                            break

    # Report surveillance pattern findings
    for pattern, hits in surveillance_hits.items():
        if len(hits) >= 2:  # Only report if pattern appears multiple times
            years = set(h["year"] for h in hits)
            anomalies.append(
                {
                    "type": "attachment_signature_deviation",
                    "subtype": "surveillance_pattern",
                    "pattern": pattern,
                    "occurrences": len(hits),
                    "years_affected": sorted(years),
                    "hits": hits,
                    "details": (
                        f"Surveillance pattern '{pattern}' found {len(hits)} times "
                        f"across {len(years)} years"
                    ),
                    "severity": "medium" if len(years) >= 2 else "low",
                }
            )

    return anomalies


def detect_extraction_inconsistencies(
    reports: dict[str, Any], corpora: dict[str, str]
) -> list[dict[str, Any]]:
    """Detect PDF text extraction failures and patterns.

    Returns:
        List of extraction-related anomalies
    """
    anomalies = []

    # Check ingestion report for extraction stats
    ingestion = reports.get("ingestion_report")
    if ingestion:
        text_extraction = ingestion.get("text_extraction", {})
        failed = text_extraction.get("extraction_failed", 0)
        errors = text_extraction.get("errors", [])

        if failed > 0:
            anomalies.append(
                {
                    "type": "extraction_inconsistency",
                    "subtype": "extraction_failures",
                    "failed_count": failed,
                    "errors": errors[:10],  # Limit to first 10
                    "details": f"{failed} PDF extraction failures detected",
                    "severity": "medium" if failed > 5 else "low",
                }
            )

    # Check missing items log for low extraction rates
    missing_log = reports.get("missing_items_log")
    if missing_log:
        low_rate = missing_log.get("low_extraction_rate", [])
        if low_rate:
            years_affected = set()
            for item in low_rate:
                if isinstance(item, dict):
                    years_affected.add(item.get("year", "unknown"))

            anomalies.append(
                {
                    "type": "extraction_inconsistency",
                    "subtype": "low_extraction_rate",
                    "affected_count": len(low_rate),
                    "years_affected": sorted(years_affected),
                    "items": low_rate,
                    "details": f"{len(low_rate)} corpora with low extraction rates",
                    "severity": "medium" if len(years_affected) >= 2 else "low",
                }
            )

    return anomalies


def detect_structural_gaps(
    reports: dict[str, Any], corpora: dict[str, str]
) -> list[dict[str, Any]]:
    """Detect missing agenda/minutes patterns by quarter.

    Returns:
        List of structural gap anomalies
    """
    anomalies = []

    # Analyze missing data by quarter
    missing_log = reports.get("missing_items_log")
    if not missing_log:
        return anomalies

    # Group missing items by year and quarter
    quarterly_gaps: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for category in ["missing_agendas", "missing_minutes"]:
        items = missing_log.get(category, [])
        for item in items:
            if isinstance(item, dict):
                year = item.get("year", "unknown")
                hist_id = item.get("hist_id", "")
                if hist_id in corpora:
                    meeting_date = corpora[hist_id]
                    month = int(meeting_date[5:7])
                    quarter = f"Q{(month - 1) // 3 + 1}"
                    key = f"{year}-{quarter}"
                    quarterly_gaps[key][category] += 1

    # Report quarters with multiple missing items
    for quarter_key, gaps in quarterly_gaps.items():
        total_gaps = sum(gaps.values())
        if total_gaps >= 2:
            year = quarter_key.split("-")[0]
            quarter = quarter_key.split("-")[1]
            anomalies.append(
                {
                    "type": "structural_gap",
                    "subtype": "quarterly_pattern",
                    "year": year,
                    "quarter": quarter,
                    "gap_counts": dict(gaps),
                    "total_gaps": total_gaps,
                    "details": (
                        f"{total_gaps} missing items in {year} {quarter}: "
                        f"{dict(gaps)}"
                    ),
                    "severity": "medium" if total_gaps >= 4 else "low",
                }
            )

    return anomalies


def score_anomaly(anomaly: dict[str, Any]) -> int:
    """Score an anomaly based on severity and type.

    Scoring Model (1-5):
    1. Mild irregularity
    2. Repeated pattern
    3. Multi-year repeated pattern
    4. Structural or chronological anomaly
    5. High-risk (cross-category correlation)

    Returns:
        Score from 1 to 5
    """
    atype = anomaly.get("type", "")
    subtype = anomaly.get("subtype", "")
    severity = anomaly.get("severity", "low")

    # Start with base score
    if severity == "critical":
        base_score = 5
    elif severity == "high":
        base_score = 4
    elif severity == "medium":
        base_score = 2
    else:
        base_score = 1

    # Adjust based on type
    if atype == "high_risk_flag":
        return SCORE_HIGH_RISK

    if atype == "chronological_drift" and subtype == "large_time_gap":
        return max(base_score, SCORE_STRUCTURAL)

    if subtype == "multi_year_pattern":
        return max(base_score, SCORE_MULTI_YEAR)

    # Check for repeated patterns
    occurrences = anomaly.get("occurrences", 1)
    total_occurrences = anomaly.get("total_occurrences", occurrences)
    years_affected = len(anomaly.get("years_affected", []))

    if years_affected >= HIGH_RISK_THRESHOLD:
        return max(base_score, SCORE_MULTI_YEAR)

    if total_occurrences >= 3 or occurrences >= 3:
        return max(base_score, SCORE_REPEATED)

    return base_score


def generate_ace_report(
    reports: dict[str, Any],
    all_anomalies: list[dict[str, Any]],
    correlated: dict[str, list[dict[str, Any]]],
    year_range: str,
) -> dict[str, Any]:
    """Generate the comprehensive ACE report.

    Returns:
        Complete ACE_REPORT structure
    """
    timestamp = get_utc_timestamp()
    report_id = sha256(timestamp.encode()).hexdigest()[:16]

    # Score all anomalies
    scored_anomalies = []
    for anomaly in all_anomalies:
        scored = anomaly.copy()
        scored["ace_score"] = score_anomaly(anomaly)
        scored_anomalies.append(scored)

    # Sort by score (highest first)
    scored_anomalies.sort(key=lambda x: -x.get("ace_score", 0))

    # Group by category
    by_category: dict[str, list[dict]] = defaultdict(list)
    for anomaly in scored_anomalies:
        atype = anomaly.get("type", "unknown")
        by_category[atype].append(anomaly)

    # Count by score
    score_counts = defaultdict(int)
    for anomaly in scored_anomalies:
        score_counts[anomaly.get("ace_score", 0)] += 1

    # Identify high-risk (score 5) anomalies
    high_risk_anomalies = [a for a in scored_anomalies if a.get("ace_score") == 5]

    # Calculate statistics
    total_anomalies = len(scored_anomalies)
    unique_hist_ids = len(correlated)
    avg_score = (
        sum(a.get("ace_score", 0) for a in scored_anomalies) / total_anomalies
        if total_anomalies > 0
        else 0
    )

    report = {
        "report_id": report_id,
        "generated_at": timestamp,
        "ace_version": ACE_VERSION,
        "schema_version": ACE_SCHEMA_VERSION,
        "year_range": year_range,
        "description": (
            f"ACE v{ACE_VERSION} Anomaly Correlation Report for "
            f"Legislative Corpus ({year_range})"
        ),
        "summary": {
            "total_anomalies": total_anomalies,
            "unique_corpora_affected": unique_hist_ids,
            "average_score": round(avg_score, 2),
            "high_risk_count": len(high_risk_anomalies),
            "score_distribution": dict(score_counts),
        },
        "high_risk_alerts": high_risk_anomalies,
        "by_category": {cat: anomalies for cat, anomalies in by_category.items()},
        "by_hist_id": {
            hist_id: [{**a, "ace_score": score_anomaly(a)} for a in anomalies]
            for hist_id, anomalies in correlated.items()
        },
        "all_anomalies": scored_anomalies,
        "scoring_model": {
            "1": "Mild irregularity",
            "2": "Repeated pattern",
            "3": "Multi-year repeated pattern",
            "4": "Structural or chronological anomaly",
            "5": "High-risk (cross-category correlation)",
        },
    }

    return report


def generate_ace_summary_md(report: dict[str, Any]) -> str:
    """Generate ACE_SUMMARY.md content.

    Returns:
        Markdown string for the summary
    """
    lines = [
        "# ACE v1.0 - Anomaly Correlation Engine Summary",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Report ID:** {report['report_id']}",
        f"**Year Range:** {report['year_range']}",
        "",
        "## Executive Summary",
        "",
    ]

    summary = report["summary"]
    lines.extend(
        [
            f"- **Total Anomalies Detected:** {summary['total_anomalies']}",
            f"- **Corpora Affected:** {summary['unique_corpora_affected']}",
            f"- **Average Anomaly Score:** {summary['average_score']}",
            f"- **High-Risk Alerts (Score 5):** {summary['high_risk_count']}",
            "",
            "## Score Distribution",
            "",
            "| Score | Count | Meaning |",
            "|-------|-------|---------|",
        ]
    )

    scoring_model = report["scoring_model"]
    score_dist = summary["score_distribution"]
    for score in range(1, 6):
        count = score_dist.get(score, 0)
        meaning = scoring_model.get(str(score), "Unknown")
        lines.append(f"| {score} | {count} | {meaning} |")

    lines.extend(
        [
            "",
            "## Anomalies by Category",
            "",
        ]
    )

    for category, anomalies in report.get("by_category", {}).items():
        count = len(anomalies)
        lines.append(f"### {category.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**Count:** {count}")
        lines.append("")

        # Show top 5 from each category
        for anomaly in anomalies[:5]:
            score = anomaly.get("ace_score", 0)
            details = anomaly.get("details", "No details")
            lines.append(f"- [Score {score}] {details}")
        if len(anomalies) > 5:
            lines.append(f"- *... and {len(anomalies) - 5} more*")
        lines.append("")

    if report.get("high_risk_alerts"):
        lines.extend(
            [
                "## High-Risk Alerts",
                "",
                "The following anomalies scored 5 (highest risk):",
                "",
            ]
        )
        for alert in report["high_risk_alerts"]:
            hist_id = alert.get("hist_id", alert.get("pattern_type", "System"))
            details = alert.get("details", "No details")
            lines.append(f"- **{hist_id}:** {details}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*Generated by ACE v1.0 - Anomaly Correlation Engine*",
        ]
    )

    return "\n".join(lines)


def _get_anomaly_year(anomaly: dict[str, Any]) -> str:
    """Extract year from anomaly, preferring 'year' field over 'years_affected'."""
    if anomaly.get("year"):
        return str(anomaly.get("year"))
    years_affected = anomaly.get("years_affected", [])
    if years_affected:
        return str(years_affected[0])
    return ""


def generate_anomaly_map_csv(report: dict[str, Any]) -> list[list[str]]:
    """Generate ANOMALY_MAP.csv data as list of rows.

    Returns:
        List of CSV rows (each row is a list of strings)
    """
    headers = [
        "hist_id",
        "type",
        "subtype",
        "ace_score",
        "severity",
        "year",
        "details",
    ]

    rows = [headers]

    for anomaly in report.get("all_anomalies", []):
        row = [
            str(anomaly.get("hist_id", "")),
            str(anomaly.get("type", "")),
            str(anomaly.get("subtype", "")),
            str(anomaly.get("ace_score", 0)),
            str(anomaly.get("severity", "")),
            _get_anomaly_year(anomaly),
            str(anomaly.get("details", ""))[:200],  # Truncate long details
        ]
        rows.append(row)

    return rows


def generate_network_graph(report: dict[str, Any]) -> dict[str, Any]:
    """Generate ace_network_graph.json for graph database ingestion.

    Returns:
        Graph structure with nodes and edges
    """
    nodes = []
    edges = []
    node_ids = set()

    # Create nodes for each hist_id
    for hist_id, anomalies in report.get("by_hist_id", {}).items():
        if hist_id not in node_ids:
            nodes.append(
                {
                    "id": hist_id,
                    "type": "corpus",
                    "anomaly_count": len(anomalies),
                    "max_score": max(
                        (a.get("ace_score", 0) for a in anomalies), default=0
                    ),
                }
            )
            node_ids.add(hist_id)

    # Create nodes for anomaly types
    for category, anomalies in report.get("by_category", {}).items():
        if category not in node_ids:
            nodes.append(
                {
                    "id": category,
                    "type": "anomaly_type",
                    "count": len(anomalies),
                }
            )
            node_ids.add(category)

        # Create edges from corpus to anomaly type
        affected_hist_ids = set()
        for anomaly in anomalies:
            hist_id = anomaly.get("hist_id")
            if hist_id and hist_id in node_ids:
                affected_hist_ids.add(hist_id)

        for hist_id in affected_hist_ids:
            edges.append(
                {
                    "source": hist_id,
                    "target": category,
                    "type": "has_anomaly",
                }
            )

    # Create edges between corpora that share anomaly types
    for category, anomalies in report.get("by_category", {}).items():
        hist_ids = list(
            {
                a.get("hist_id")
                for a in anomalies
                if a.get("hist_id") and a.get("hist_id") in node_ids
            }
        )
        # Link pairs of corpora that share the same anomaly type
        for i in range(len(hist_ids)):
            for j in range(i + 1, len(hist_ids)):
                edges.append(
                    {
                        "source": hist_ids[i],
                        "target": hist_ids[j],
                        "type": "shares_anomaly_type",
                        "shared_type": category,
                    }
                )

    return {
        "generated_at": report.get("generated_at", get_utc_timestamp()),
        "ace_version": ACE_VERSION,
        "nodes": nodes,
        "edges": edges,
        "statistics": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "corpus_nodes": len([n for n in nodes if n.get("type") == "corpus"]),
            "anomaly_type_nodes": len(
                [n for n in nodes if n.get("type") == "anomaly_type"]
            ),
        },
    }


def run_ace_analysis(
    corpus_root: Path, year_range: str, output_dir: Path | None = None
) -> dict[str, Any]:
    """Run the complete ACE analysis pipeline.

    Returns:
        The generated ACE report
    """
    start_year, end_year = parse_year_range(year_range)
    corpora = filter_corpora_by_years(start_year, end_year)

    print(f"ACE v{ACE_VERSION} - Anomaly Correlation Engine")
    print("=" * 60)
    print(f"Corpus Root: {corpus_root}")
    print(f"Year Range: {year_range}")
    print(f"Corpora to analyze: {len(corpora)}")
    print("=" * 60)

    # Step 1: Load all reports
    print("\n[1/6] Loading reports...")
    reports = load_reports(corpus_root)
    print(f"  - Loaded {len(reports['metadata_files'])} metadata files")
    print(f"  - Loaded {len(reports['corpus_indexes'])} corpus indexes")

    # Step 2: Scan metadata for outliers
    print("\n[2/6] Scanning metadata for outliers...")
    metadata_anomalies = scan_metadata_for_outliers(reports)
    print(f"  - Found {len(metadata_anomalies)} metadata anomalies")

    # Step 3: Correlate anomalies by hist_id
    print("\n[3/6] Correlating anomalies by hist_id...")
    correlated = correlate_anomalies_by_hist_id(reports, metadata_anomalies)
    print(f"  - Correlated anomalies across {len(correlated)} corpora")

    # Step 4: Detect cross-year irregularities
    print("\n[4/6] Detecting cross-year irregularities...")
    cross_year_anomalies = detect_cross_year_irregularities(correlated, corpora)
    print(f"  - Found {len(cross_year_anomalies)} cross-year anomalies")

    # Step 5: Detect additional patterns
    print("\n[5/6] Detecting additional patterns...")
    attachment_anomalies = detect_attachment_signatures(reports, corpora)
    extraction_anomalies = detect_extraction_inconsistencies(reports, corpora)
    structural_anomalies = detect_structural_gaps(reports, corpora)

    print(f"  - Attachment signatures: {len(attachment_anomalies)}")
    print(f"  - Extraction issues: {len(extraction_anomalies)}")
    print(f"  - Structural gaps: {len(structural_anomalies)}")

    # Combine all anomalies
    all_anomalies = (
        metadata_anomalies
        + cross_year_anomalies
        + attachment_anomalies
        + extraction_anomalies
        + structural_anomalies
    )

    # Add to correlated
    for anomaly in (
        cross_year_anomalies
        + attachment_anomalies
        + extraction_anomalies
        + structural_anomalies
    ):
        hist_id = anomaly.get("hist_id", "system")
        if hist_id not in correlated:
            correlated[hist_id] = []
        correlated[hist_id].append(anomaly)

    # Step 6: Generate report
    print("\n[6/6] Generating ACE report...")
    ace_report = generate_ace_report(reports, all_anomalies, correlated, year_range)

    # Determine output directory
    if output_dir is None:
        output_dir = Path(".")

    # Write outputs
    # ACE_REPORT.json
    report_path = output_dir / "ACE_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(ace_report, f, indent=2, default=str)
        f.write("\n")
    print(f"  - Wrote {report_path}")

    # ACE_SUMMARY.md
    summary_path = output_dir / "ACE_SUMMARY.md"
    summary_md = generate_ace_summary_md(ace_report)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
        f.write("\n")
    print(f"  - Wrote {summary_path}")

    # ANOMALY_MAP.csv
    csv_path = output_dir / "ANOMALY_MAP.csv"
    csv_rows = generate_anomaly_map_csv(ace_report)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
    print(f"  - Wrote {csv_path}")

    # ace_network_graph.json (optional)
    graph_path = output_dir / "ace_network_graph.json"
    graph_data = generate_network_graph(ace_report)
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)
        f.write("\n")
    print(f"  - Wrote {graph_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("ACE ANALYSIS COMPLETE")
    print("=" * 60)
    summary = ace_report["summary"]
    print(f"\nTotal Anomalies: {summary['total_anomalies']}")
    print(f"Corpora Affected: {summary['unique_corpora_affected']}")
    print(f"Average Score: {summary['average_score']}")
    print(f"High-Risk Alerts: {summary['high_risk_count']}")

    if summary["high_risk_count"] > 0:
        print("\n⚠️  HIGH-RISK ANOMALIES DETECTED:")
        for alert in ace_report.get("high_risk_alerts", [])[:5]:
            print(f"  - {alert.get('details', 'No details')}")

    return ace_report


def main():
    """Run the ACE analyzer from command line."""
    parser = argparse.ArgumentParser(
        description="ACE v1.0 - Anomaly Correlation Engine"
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
        help="Year range to analyze (e.g., 2014-2025 or single year like 2024)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for ACE reports (defaults to current directory)",
    )
    parser.add_argument(
        "--fail-on-high-risk",
        action="store_true",
        help="Exit with error code if any score 5 anomalies are detected",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output JSON only, minimal console output",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()
    output_dir = Path(args.output).resolve() if args.output else None

    if not corpus_root.exists():
        print(f"Error: Corpus root not found: {corpus_root}")
        return 1

    report = run_ace_analysis(corpus_root, args.years, output_dir)

    # Check for high-risk anomalies if fail flag is set
    if args.fail_on_high_risk and report["summary"]["high_risk_count"] > 0:
        print(
            f"\n❌ FAILURE: {report['summary']['high_risk_count']} "
            f"high-risk anomalies detected"
        )
        return 1

    print("\n✅ ACE analysis completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
