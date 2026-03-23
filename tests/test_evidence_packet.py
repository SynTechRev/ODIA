"""Tests for src/oraculus_di_auditor/reporting/evidence_packet.py."""

from __future__ import annotations

import io
import json
import zipfile

from oraculus_di_auditor.reporting.evidence_packet import (
    generate_evidence_packet,
)

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _make_finding(index: int, severity: str = "high", layer: str = "fiscal") -> dict:
    return {
        "id": f"{layer}:amount_without_appropriation",
        "issue": f"Test finding {index}",
        "severity": severity,
        "layer": layer,
        "document_id": f"doc_{index:03d}",
        "details": {"amount": "$50,000", "context": "test"},
        "plain_summary": f"Plain summary for finding {index}.",
        "plain_impact": f"Plain impact for finding {index}.",
        "plain_action": f"Plain action for finding {index}.",
    }


def _make_results(num_findings: int = 3, num_docs: int = 2) -> dict:
    findings = [
        _make_finding(i, severity=["critical", "high", "medium", "low"][i % 4])
        for i in range(1, num_findings + 1)
    ]
    manifests = [
        {
            "document_id": f"doc_{i:03d}",
            "filename": f"contract_{i}.pdf",
            "sha256": "a" * 64,
            "size": 1024 * i,
            "format": "pdf",
            "finding_count": 1,
        }
        for i in range(1, num_docs + 1)
    ]
    sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev[f["severity"]] += 1

    return {
        "job_id": "test-job-1234",
        "document_count": num_docs,
        "finding_count": num_findings,
        "severity_summary": sev,
        "findings": findings,
        "document_manifest": manifests,
        "generated_at": "2026-03-25T12:00:00+00:00",
    }


# ---------------------------------------------------------------------------
# ZIP structure tests
# ---------------------------------------------------------------------------


class TestZipStructure:
    def _open_zip(self, results: dict) -> zipfile.ZipFile:
        raw = generate_evidence_packet(results)
        return zipfile.ZipFile(io.BytesIO(raw))

    def test_returns_bytes(self):
        raw = generate_evidence_packet(_make_results())
        assert isinstance(raw, bytes)
        assert len(raw) > 0

    def test_is_valid_zip(self):
        raw = generate_evidence_packet(_make_results())
        assert zipfile.is_zipfile(io.BytesIO(raw))

    def test_readme_present(self):
        zf = self._open_zip(_make_results())
        assert "README.md" in zf.namelist()

    def test_audit_report_md_present(self):
        zf = self._open_zip(_make_results())
        assert "audit_report.md" in zf.namelist()

    def test_audit_report_html_present(self):
        zf = self._open_zip(_make_results())
        assert "audit_report.html" in zf.namelist()

    def test_executive_summary_present(self):
        zf = self._open_zip(_make_results())
        assert "executive_summary.md" in zf.namelist()

    def test_document_manifest_present(self):
        zf = self._open_zip(_make_results())
        assert "document_manifest.json" in zf.namelist()

    def test_findings_directory_present(self):
        zf = self._open_zip(_make_results(num_findings=3))
        finding_files = [n for n in zf.namelist() if n.startswith("findings/")]
        assert len(finding_files) == 3

    def test_finding_files_named_by_severity(self):
        zf = self._open_zip(_make_results(num_findings=1))
        finding_files = [n for n in zf.namelist() if n.startswith("findings/")]
        assert len(finding_files) == 1
        # Should contain severity in name
        assert any(
            sev in finding_files[0] for sev in ("critical", "high", "medium", "low")
        )

    def test_empty_findings_still_creates_valid_zip(self):
        results = _make_results(num_findings=0, num_docs=0)
        raw = generate_evidence_packet(results)
        assert zipfile.is_zipfile(io.BytesIO(raw))


# ---------------------------------------------------------------------------
# Content tests
# ---------------------------------------------------------------------------


class TestZipContents:
    def _read_file(self, results: dict, filename: str) -> str:
        raw = generate_evidence_packet(results)
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            return zf.read(filename).decode("utf-8")

    def test_readme_mentions_packet(self):
        content = self._read_file(_make_results(), "README.md")
        assert "Evidence Packet" in content

    def test_readme_lists_files(self):
        content = self._read_file(_make_results(), "README.md")
        assert "audit_report.md" in content

    def test_audit_report_contains_finding_count(self):
        results = _make_results(num_findings=5)
        content = self._read_file(results, "audit_report.md")
        assert "5" in content

    def test_executive_summary_has_severity_table(self):
        content = self._read_file(_make_results(), "executive_summary.md")
        assert "Critical" in content or "critical" in content.lower()
        assert "High" in content or "high" in content.lower()

    def test_document_manifest_is_valid_json(self):
        results = _make_results(num_docs=3)
        raw_json = self._read_file(results, "document_manifest.json")
        parsed = json.loads(raw_json)
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_document_manifest_has_sha256(self):
        results = _make_results(num_docs=1)
        raw_json = self._read_file(results, "document_manifest.json")
        parsed = json.loads(raw_json)
        assert "sha256" in parsed[0]

    def test_finding_sheet_has_severity(self):
        raw = generate_evidence_packet(_make_results(num_findings=1))
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            finding_files = [n for n in zf.namelist() if n.startswith("findings/")]
            content = zf.read(finding_files[0]).decode("utf-8")
        assert any(
            sev in content.upper() for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        )

    def test_finding_sheet_has_plain_summary(self):
        raw = generate_evidence_packet(_make_results(num_findings=1))
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            finding_files = [n for n in zf.namelist() if n.startswith("findings/")]
            content = zf.read(finding_files[0]).decode("utf-8")
        assert "Plain summary for finding 1" in content

    def test_html_report_is_valid_html(self):
        content = self._read_file(_make_results(), "audit_report.html")
        assert "<html" in content
        assert "</html>" in content

    def test_finding_sheets_sorted_critical_first(self):
        results = _make_results(num_findings=4)
        # Ensure at least one critical finding
        results["findings"][0]["severity"] = "critical"
        results["findings"][1]["severity"] = "low"

        raw = generate_evidence_packet(results)
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            finding_files = sorted(
                n for n in zf.namelist() if n.startswith("findings/")
            )
        # F-001 should be the critical one
        assert "critical" in finding_files[0]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_findings_without_plain_language(self):
        """Findings without plain_* fields should still produce valid sheets."""
        results = {
            "job_id": "test",
            "document_count": 1,
            "finding_count": 1,
            "severity_summary": {"critical": 0, "high": 1, "medium": 0, "low": 0},
            "findings": [
                {
                    "id": "fiscal:amount",
                    "issue": "No appropriation found",
                    "severity": "high",
                    "layer": "fiscal",
                    "document_id": "doc_001",
                    "details": {},
                }
            ],
            "document_manifest": [],
            "generated_at": "2026-01-01T00:00:00+00:00",
        }
        raw = generate_evidence_packet(results)
        assert zipfile.is_zipfile(io.BytesIO(raw))

    def test_very_large_finding_count(self):
        """Should handle 50+ findings without error."""
        results = _make_results(num_findings=50, num_docs=10)
        raw = generate_evidence_packet(results)
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            finding_files = [n for n in zf.namelist() if n.startswith("findings/")]
        assert len(finding_files) == 50
