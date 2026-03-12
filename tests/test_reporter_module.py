"""Tests for reporter module.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

import csv
import json

from oraculus_di_auditor.reporter import generate_csv_report, generate_json_report


def test_generate_json_report(tmp_path):
    """Test JSON report generation."""
    findings = [
        {
            "id": "doc-1",
            "count": 2,
            "anomalies": [
                {"type": "long_sentence", "severity": "medium", "evidence": "..."},
                {
                    "type": "cross_reference_mismatch",
                    "severity": "high",
                    "evidence": "...",
                },
            ],
        }
    ]

    output_path = tmp_path / "report.json"
    generate_json_report(findings, str(output_path))

    assert output_path.exists()

    with open(output_path) as f:
        report = json.load(f)

    assert report["findings_count"] == 1
    assert len(report["findings"]) == 1
    assert "generated_at" in report
    assert "provenance" in report


def test_generate_csv_report(tmp_path):
    """Test CSV report generation."""
    findings = [
        {
            "id": "doc-1",
            "count": 1,
            "anomalies": [
                {"type": "long_sentence", "severity": "medium", "evidence": "..."}
            ],
        },
        {"id": "doc-2", "count": 0, "anomalies": []},
    ]

    output_path = tmp_path / "report.csv"
    generate_csv_report(findings, str(output_path))

    assert output_path.exists()

    with open(output_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 2
    assert rows[0]["document_id"] == "doc-1"


def test_generate_reports_empty(tmp_path):
    """Test report generation with empty findings."""
    findings = []

    json_path = tmp_path / "empty.json"
    generate_json_report(findings, str(json_path))

    assert json_path.exists()

    with open(json_path) as f:
        report = json.load(f)

    assert report["findings_count"] == 0
