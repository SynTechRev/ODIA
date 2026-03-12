"""
Tests for the automated_audit.py script.
Verifies that the audit script runs successfully and generates valid reports.
"""

import subprocess
import sys
from pathlib import Path

import pytest


def test_audit_script_runs_successfully(tmp_path):
    """Test that the automated audit script runs without errors."""
    # Run the audit script
    result = subprocess.run(
        [sys.executable, "scripts/automated_audit.py"],
        capture_output=True,
        text=True,
        timeout=120,  # 2 minutes timeout
    )

    assert result.returncode == 0, f"Audit script failed: {result.stderr}"
    assert "Audit Complete" in result.stdout
    assert "Total findings:" in result.stdout
    assert "Report location:" in result.stdout


def test_audit_report_generated():
    """Test that AUDIT_REPORT.txt is generated."""
    report_path = Path("AUDIT_REPORT.txt")

    # Report should exist (created by previous test or manual run)
    # If it doesn't exist, run the script
    if not report_path.exists():
        result = subprocess.run(
            [sys.executable, "scripts/automated_audit.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, "Audit script failed to generate report"

    assert report_path.exists(), "AUDIT_REPORT.txt was not created"


def test_audit_report_structure():
    """Test that the audit report has the required sections."""
    report_path = Path("AUDIT_REPORT.txt")

    if not report_path.exists():
        pytest.skip("AUDIT_REPORT.txt not found, run test_audit_report_generated first")

    content = report_path.read_text(encoding="utf-8")

    # Check for required sections
    required_sections = [
        "AUTOMATED REPOSITORY AUDIT REPORT",
        "REPOSITORY OVERVIEW",
        "GLOBAL FLAGS AND ISSUES",
        "FILE-BY-FILE FINDINGS",
        "RECOMMENDATIONS",
        "END OF AUDIT REPORT",
    ]

    for section in required_sections:
        assert section in content, f"Report missing section: {section}"

    # Check for expected metrics
    assert "Total Directories:" in content
    assert "Total Files:" in content
    assert "Python Files:" in content
    assert "Test Files:" in content

    # Check for generated timestamp
    assert "Generated:" in content


def test_audit_report_has_findings():
    """Test that the audit report contains actual findings."""
    report_path = Path("AUDIT_REPORT.txt")

    assert report_path.exists(), (
        "AUDIT_REPORT.txt not found; run test_audit_report_generated or "
        "generate the report via scripts/automated_audit.py"
    )

    content = report_path.read_text(encoding="utf-8")

    # Report should have at least some findings or notes
    # (even a perfect repo would have notes about TODO comments, etc.)
    assert ("Files with findings:" in content) or ("Total warnings:" in content)


def test_audit_script_deterministic():
    """Test that audit script produces deterministic results."""
    # Run audit twice
    subprocess.run(
        [sys.executable, "scripts/automated_audit.py"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    report1 = Path("AUDIT_REPORT.txt").read_text(encoding="utf-8")

    subprocess.run(
        [sys.executable, "scripts/automated_audit.py"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    report2 = Path("AUDIT_REPORT.txt").read_text(encoding="utf-8")

    # Remove timestamp lines (which will differ)
    report1_lines = [
        line for line in report1.splitlines() if not line.startswith("Generated:")
    ]
    report2_lines = [
        line for line in report2.splitlines() if not line.startswith("Generated:")
    ]

    # The report content (excluding timestamps) should be deterministic
    assert len(report1_lines) > 100, "Report too short"
    assert len(report2_lines) > 100, "Report too short"

    # Verify that the full content (excluding timestamps) is identical
    assert report1_lines == report2_lines, "Audit report is not deterministic"


def test_audit_documentation_exists():
    """Test that the audit documentation exists."""
    doc_path = Path("docs/AUTOMATED_AUDIT.md")
    assert doc_path.exists(), "AUTOMATED_AUDIT.md documentation not found"

    content = doc_path.read_text(encoding="utf-8")
    assert "Automated Repository Audit" in content
    assert "Usage" in content
    assert "scripts/automated_audit.py" in content
