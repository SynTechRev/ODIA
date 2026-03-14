"""Tests for ReportTemplateEngine."""

from __future__ import annotations

import tempfile
from pathlib import Path

import jinja2
import pytest

from oraculus_di_auditor.reporting import AuditReport, ReportTemplateEngine
from oraculus_di_auditor.reporting.models import (
    DetectorSummary,
    DocumentSummary,
    Finding,
    SeveritySummary,
    build_report_from_analysis,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _sample_report() -> AuditReport:
    """Minimal AuditReport with one finding of each severity."""
    findings = [
        Finding(
            finding_id="F-001",
            title="Critical fiscal gap",
            severity="critical",
            category="fiscal",
            description="Missing budget appropriation reference.",
            evidence="Line 42: unsigned allocation",
            recommendation="Obtain signed authorization.",
            document_id="doc-1",
        ),
        Finding(
            finding_id="F-002",
            title="High surveillance concern",
            severity="high",
            category="surveillance",
            description="Surveillance procurement lacks governance controls.",
            document_id="doc-2",
        ),
        Finding(
            finding_id="F-003",
            title="Medium constitutional flag",
            severity="medium",
            category="constitutional",
            description="Clause may limit due-process rights.",
        ),
        Finding(
            finding_id="F-004",
            title="Low metadata gap",
            severity="low",
            category="fiscal",
            description="Document metadata incomplete.",
        ),
    ]
    return AuditReport(
        report_id="RPT-TEST001",
        report_type="single_jurisdiction",
        generated_at="2026-03-14T00:00:00+00:00",
        jurisdiction="City of Test",
        title="Test Audit Report",
        executive_summary="4 anomalies found across 2 documents.",
        document_count=2,
        documents=[
            DocumentSummary(
                document_id="doc-1",
                title="Budget Resolution 2026",
                anomaly_count=1,
                max_severity="critical",
                checksum="abcdef1234567890",
            ),
            DocumentSummary(
                document_id="doc-2",
                title="Surveillance Contract",
                anomaly_count=1,
                max_severity="high",
            ),
        ],
        severity_summary=SeveritySummary(critical=1, high=1, medium=1, low=1),
        detector_summaries=[
            DetectorSummary(
                detector_name="fiscal",
                anomaly_count=2,
                severities=SeveritySummary(critical=1, low=1),
            ),
            DetectorSummary(
                detector_name="surveillance",
                anomaly_count=1,
                severities=SeveritySummary(high=1),
            ),
            DetectorSummary(
                detector_name="constitutional",
                anomaly_count=1,
                severities=SeveritySummary(medium=1),
            ),
        ],
        findings=findings,
        recommendations=[
            "Obtain signed authorization.",
            "Review surveillance contract.",
        ],
    )


# ---------------------------------------------------------------------------
# render_markdown
# ---------------------------------------------------------------------------


def test_render_markdown_produces_string():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    report = _sample_report()
    md = engine.render_markdown(report)
    assert isinstance(md, str)
    assert len(md) > 0


def test_render_markdown_contains_report_id():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    md = engine.render_markdown(_sample_report())
    assert "RPT-TEST001" in md


def test_render_markdown_contains_findings():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    md = engine.render_markdown(_sample_report())
    assert "Critical fiscal gap" in md
    assert "CRITICAL" in md


def test_render_markdown_contains_severity_table():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    md = engine.render_markdown(_sample_report())
    assert "Severity Distribution" in md or "CRITICAL" in md


# ---------------------------------------------------------------------------
# render_to_file
# ---------------------------------------------------------------------------


def test_render_to_file_creates_file():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "report.md"
        result = engine.render_to_file(_sample_report(), out)
        assert result.exists()
        assert result.read_text(encoding="utf-8").startswith("#")


def test_render_to_file_creates_parent_dirs():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "nested" / "deep" / "report.md"
        result = engine.render_to_file(_sample_report(), out)
        assert result.exists()


def test_render_to_file_returns_resolved_path():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "report.md"
        result = engine.render_to_file(_sample_report(), out)
        assert result.is_absolute()


# ---------------------------------------------------------------------------
# available_templates
# ---------------------------------------------------------------------------


def test_available_templates_lists_files():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    templates = engine.available_templates()
    assert isinstance(templates, list)
    assert len(templates) > 0


def test_available_templates_includes_audit_report():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    templates = engine.available_templates()
    assert "audit_report.md" in templates


def test_available_templates_missing_dir_returns_empty():
    engine = ReportTemplateEngine(template_dir="/nonexistent/path")
    assert engine.available_templates() == []


# ---------------------------------------------------------------------------
# Missing template raises TemplateNotFound
# ---------------------------------------------------------------------------


def test_missing_template_raises_error():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    with pytest.raises(jinja2.TemplateNotFound):
        engine.render_markdown(_sample_report(), template_name="does_not_exist.md")


# ---------------------------------------------------------------------------
# Executive template is shorter than full template
# ---------------------------------------------------------------------------


def test_executive_template_shorter_than_full():
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    report = _sample_report()
    full = engine.render_markdown(report, template_name="audit_report.md")
    exec_md = engine.render_markdown(report, template_name="audit_report_executive.md")
    assert len(exec_md) < len(full)


# ---------------------------------------------------------------------------
# All three templates render without Jinja2 errors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "template_name",
    [
        "audit_report.md",
        "audit_report_executive.md",
        "multi_jurisdiction_report.md",
    ],
)
def test_all_templates_render_without_errors(template_name):
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    report = _sample_report()
    md = engine.render_markdown(report, template_name=template_name)
    assert isinstance(md, str)
    assert len(md) > 50


# ---------------------------------------------------------------------------
# build_report_from_analysis integration
# ---------------------------------------------------------------------------


def test_engine_renders_report_from_analysis():
    """End-to-end: build report from raw analysis then render via template."""
    results = [
        {
            "metadata": {"document_id": "doc-A", "title": "Test Doc"},
            "findings": {
                "fiscal": [
                    {
                        "id": "fiscal:test",
                        "issue": "Test fiscal issue",
                        "severity": "high",
                        "layer": "fiscal",
                        "details": {},
                    }
                ],
                "constitutional": [],
                "surveillance": [],
            },
        }
    ]
    report = build_report_from_analysis(results, jurisdiction="Test Jurisdiction")
    engine = ReportTemplateEngine(template_dir=TEMPLATE_DIR)
    md = engine.render_markdown(report)
    assert "Test fiscal issue" in md
    assert "Test Jurisdiction" in md
