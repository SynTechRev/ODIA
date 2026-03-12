"""Reporting module for audit findings.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

from csv import DictWriter
from datetime import UTC, datetime
from json import dump
from pathlib import Path
from typing import Any


def generate_json_report(findings: list[dict[str, Any]], output_path: str):
    """Generate JSON report with provenance.

    Args:
        findings: List of finding dictionaries
        output_path: Path to save JSON report
    """
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "findings_count": len(findings),
        "findings": findings,
        "provenance": {
            "tool": "Oraculus DI Auditor",
            "version": "0.0.0",
        },
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        dump(report, f, indent=2, ensure_ascii=False)

    print(f"JSON report saved to {output_path}")


def generate_csv_report(findings: list[dict[str, Any]], output_path: str):
    """Generate CSV summary report.

    Args:
        findings: List of finding dictionaries
        output_path: Path to save CSV report
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Flatten findings for CSV
    rows = []
    for finding in findings:
        base_row = {
            "document_id": finding.get("id", ""),
            "anomaly_count": finding.get("count", 0),
        }

        # Add each anomaly as a separate row
        anomalies = finding.get("anomalies", [])
        if anomalies:
            for anomaly in anomalies:
                row = base_row.copy()
                row.update(
                    {
                        "type": anomaly.get("type", ""),
                        "severity": anomaly.get("severity", ""),
                        "evidence": anomaly.get("evidence", ""),
                    }
                )
                rows.append(row)
        else:
            rows.append(base_row)

    if rows:
        fieldnames = list(rows[0].keys())
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"CSV report saved to {output_path}")
