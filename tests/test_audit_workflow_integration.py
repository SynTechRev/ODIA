"""
Integration test for the complete audit workflow.
Demonstrates end-to-end usage of triage, report generation, and issue creation.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def test_complete_audit_workflow():
    """
    Test the complete audit workflow:
    1. Create a test document
    2. Triage the document with flags
    3. Generate a report
    4. Generate issue drafts
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Setup directories
        manifests_dir = tmpdir / "manifests"
        reports_dir = tmpdir / "reports"
        issues_dir = tmpdir / "issues"
        manifests_dir.mkdir()
        reports_dir.mkdir()
        issues_dir.mkdir()

        # Create a test document
        test_doc = tmpdir / "test_document.pdf"
        test_doc.write_text("Sample audit document content for testing")

        # Step 1: Create manifest with high-severity flag
        result = subprocess.run(
            [
                sys.executable,
                "scripts/triage.py",
                "--doc-id",
                "INTEG_TEST_001",
                "--path",
                str(test_doc),
                "--flag",
                "Critical compliance issue detected",
                "--severity",
                "critical",
                "--category",
                "doj_certification",
                "--author",
                "Integration Test",
                "--note",
                "This is a test document for workflow validation",
                "--manifests-dir",
                str(manifests_dir),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Triage failed: {result.stderr}"
        assert (manifests_dir / "INTEG_TEST_001.json").exists()

        # Verify manifest content
        with open(manifests_dir / "INTEG_TEST_001.json") as f:
            manifest = json.load(f)

        assert manifest["document_id"] == "INTEG_TEST_001"
        assert len(manifest["flags"]) == 1
        assert manifest["flags"][0]["severity"] == "critical"
        assert len(manifest["notes"]) == 1
        assert len(manifest["chain_of_custody"]) >= 1

        # Step 2: Generate audit report
        report_output = reports_dir / "test_report.md"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/render_report.py",
                "--manifests-dir",
                str(manifests_dir),
                "--output",
                str(report_output),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Report generation failed: {result.stderr}"
        assert report_output.exists()

        # Verify report content
        report_content = report_output.read_text()
        assert "INTEG_TEST_001" in report_content
        assert "Critical compliance issue detected" in report_content
        assert "CRITICAL" in report_content or "Critical" in report_content

        # Step 3: Generate issue drafts
        result = subprocess.run(
            [
                sys.executable,
                "scripts/auto_issue_generator.py",
                "--manifests-dir",
                str(manifests_dir),
                "--output",
                str(issues_dir),
                "--severity",
                "critical",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Issue generation failed: {result.stderr}"

        # Find generated issue files
        issue_files = list(issues_dir.glob("*.md"))
        assert len(issue_files) == 1, f"Expected 1 issue file, found {len(issue_files)}"

        # Verify issue content
        issue_content = issue_files[0].read_text()
        assert "INTEG_TEST_001" in issue_content
        assert "Critical compliance issue detected" in issue_content
        assert (
            "doj_certification" in issue_content or "DOJ Certification" in issue_content
        )


def test_triage_update_workflow():
    """
    Test updating an existing manifest with additional flags and notes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        manifests_dir = tmpdir / "manifests"
        manifests_dir.mkdir()

        test_doc = tmpdir / "document.pdf"
        test_doc.write_text("Test content")

        doc_id = "UPDATE_TEST_001"

        # Create initial manifest
        result1 = subprocess.run(
            [
                sys.executable,
                "scripts/triage.py",
                "--doc-id",
                doc_id,
                "--path",
                str(test_doc),
                "--author",
                "User 1",
                "--note",
                "Initial review",
                "--manifests-dir",
                str(manifests_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result1.returncode == 0

        # Add a flag
        result2 = subprocess.run(
            [
                sys.executable,
                "scripts/triage.py",
                "--doc-id",
                doc_id,
                "--flag",
                "Found issue during second review",
                "--severity",
                "medium",
                "--author",
                "User 2",
                "--manifests-dir",
                str(manifests_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result2.returncode == 0

        # Add another note
        result3 = subprocess.run(
            [
                sys.executable,
                "scripts/triage.py",
                "--doc-id",
                doc_id,
                "--note",
                "Awaiting legal review",
                "--author",
                "User 3",
                "--manifests-dir",
                str(manifests_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result3.returncode == 0

        # Verify final state
        with open(manifests_dir / f"{doc_id}.json") as f:
            manifest = json.load(f)

        assert len(manifest["notes"]) == 2
        assert len(manifest["flags"]) == 1
        assert len(manifest["chain_of_custody"]) >= 3  # At least 3 updates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
