"""Tests for report format conversion utilities."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from oraculus_di_auditor.reporting import (
    AuditReport,
    export_report,
    get_available_formats,
    markdown_to_html,
)
from oraculus_di_auditor.reporting.format_converters import (
    markdown_to_docx,
    markdown_to_pdf,
)
from oraculus_di_auditor.reporting.models import (
    Finding,
    SeveritySummary,
    build_report_from_analysis,
)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_MD = """# Test Report

## Executive Summary

One high-severity finding detected.

## Findings

| Finding | Severity |
|---------|----------|
| F-001   | HIGH     |
"""


def _sample_report() -> AuditReport:
    return AuditReport(
        report_id="RPT-CONV001",
        report_type="single_jurisdiction",
        generated_at="2026-03-14T00:00:00+00:00",
        jurisdiction="Test City",
        title="Converter Test Report",
        executive_summary="One high-severity finding.",
        document_count=1,
        severity_summary=SeveritySummary(high=1),
        findings=[
            Finding(
                finding_id="F-001",
                title="Test fiscal issue",
                severity="high",
                category="fiscal",
                description="Missing budget reference.",
            )
        ],
        recommendations=["Obtain signed budget authorization."],
    )


# ---------------------------------------------------------------------------
# markdown_to_html
# ---------------------------------------------------------------------------


def test_markdown_to_html_produces_string():
    html = markdown_to_html(_SAMPLE_MD)
    assert isinstance(html, str)
    assert len(html) > 0


def test_markdown_to_html_contains_content():
    html = markdown_to_html(_SAMPLE_MD)
    assert "Test Report" in html


def test_markdown_to_html_is_html_like():
    html = markdown_to_html(_SAMPLE_MD)
    # Either pandoc/markdown produces tags, or fallback wraps in <pre>
    assert "<" in html


def test_markdown_to_html_fallback_when_no_pandoc_no_markdown():
    """Fallback to <pre> block when neither pandoc nor markdown library available."""
    with patch("shutil.which", return_value=None):
        with patch.dict("sys.modules", {"markdown": None}):
            # Re-import to pick up patched state.
            from oraculus_di_auditor.reporting import format_converters

            with patch.object(format_converters, "_can_import", return_value=False):
                html = format_converters.markdown_to_html("# Hello")
                assert "<pre>" in html or "Hello" in html


# ---------------------------------------------------------------------------
# get_available_formats
# ---------------------------------------------------------------------------


def test_get_available_formats_always_includes_json_and_markdown():
    formats = get_available_formats()
    assert "json" in formats
    assert "markdown" in formats


def test_get_available_formats_returns_list():
    formats = get_available_formats()
    assert isinstance(formats, list)
    assert len(formats) >= 2


def test_get_available_formats_sorted():
    formats = get_available_formats()
    assert formats == sorted(formats)


def test_get_available_formats_html_when_markdown_available():
    """HTML should be available since Python markdown library is installed."""
    formats = get_available_formats()
    # markdown lib is a core dependency — HTML must be present
    assert "html" in formats


# ---------------------------------------------------------------------------
# export_report — JSON and Markdown always produced
# ---------------------------------------------------------------------------


def test_export_report_creates_json_and_markdown():
    report = _sample_report()
    with tempfile.TemporaryDirectory() as tmpdir:
        written = export_report(
            report,
            output_dir=tmpdir,
            formats=["json", "markdown"],
            template_dir=TEMPLATE_DIR,
        )
        assert "json" in written
        assert "markdown" in written
        assert written["json"].exists()
        assert written["markdown"].exists()


def test_export_report_json_is_valid():
    report = _sample_report()
    with tempfile.TemporaryDirectory() as tmpdir:
        written = export_report(
            report,
            output_dir=tmpdir,
            formats=["json"],
            template_dir=TEMPLATE_DIR,
        )
        data = json.loads(written["json"].read_text(encoding="utf-8"))
        assert data["report_id"] == "RPT-CONV001"
        assert data["report_type"] == "single_jurisdiction"


def test_export_report_markdown_contains_title():
    report = _sample_report()
    with tempfile.TemporaryDirectory() as tmpdir:
        written = export_report(
            report,
            output_dir=tmpdir,
            formats=["markdown"],
            template_dir=TEMPLATE_DIR,
        )
        content = written["markdown"].read_text(encoding="utf-8")
        assert "Converter Test Report" in content


def test_export_report_handles_missing_output_directory():
    report = _sample_report()
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "nested" / "deep" / "output"
        written = export_report(
            report,
            output_dir=nested,
            formats=["json", "markdown"],
            template_dir=TEMPLATE_DIR,
        )
        assert written["json"].exists()
        assert written["markdown"].exists()


def test_export_report_filenames_use_report_id():
    report = _sample_report()
    with tempfile.TemporaryDirectory() as tmpdir:
        written = export_report(
            report,
            output_dir=tmpdir,
            formats=["json", "markdown"],
            template_dir=TEMPLATE_DIR,
        )
        assert "RPT-CONV001" in written["json"].name
        assert "RPT-CONV001" in written["markdown"].name


def test_export_report_explicit_format_list():
    report = _sample_report()
    with tempfile.TemporaryDirectory() as tmpdir:
        written = export_report(
            report,
            output_dir=tmpdir,
            formats=["json"],
            template_dir=TEMPLATE_DIR,
        )
        assert "json" in written
        assert "markdown" not in written
        assert "html" not in written


def test_export_report_html_when_available():
    report = _sample_report()
    formats = get_available_formats()
    if "html" not in formats:
        pytest.skip("HTML not available in this environment")
    with tempfile.TemporaryDirectory() as tmpdir:
        written = export_report(
            report,
            output_dir=tmpdir,
            formats=["html"],
            template_dir=TEMPLATE_DIR,
        )
        if "html" in written:
            assert written["html"].exists()


# ---------------------------------------------------------------------------
# Graceful handling when pandoc/weasyprint not installed
# ---------------------------------------------------------------------------


def test_markdown_to_pdf_returns_none_when_no_converter():
    with patch("shutil.which", return_value=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = markdown_to_pdf(_SAMPLE_MD, Path(tmpdir) / "out.pdf")
            assert result is None


def test_markdown_to_docx_returns_none_when_no_pandoc():
    with patch("shutil.which", return_value=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = markdown_to_docx(_SAMPLE_MD, Path(tmpdir) / "out.docx")
            assert result is None


def test_export_report_skips_pdf_gracefully_when_unavailable():
    """export_report must not raise even when PDF conversion fails."""
    report = _sample_report()
    with patch("shutil.which", return_value=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = export_report(
                report,
                output_dir=tmpdir,
                formats=["json", "markdown", "pdf"],
                template_dir=TEMPLATE_DIR,
            )
            # json and markdown always succeed
            assert "json" in written
            assert "markdown" in written
            # pdf absent (no converter), but no exception raised
            assert "pdf" not in written


# ---------------------------------------------------------------------------
# Integration: build_report_from_analysis → export_report
# ---------------------------------------------------------------------------


def test_export_report_end_to_end_from_analysis():
    results = [
        {
            "metadata": {"document_id": "doc-E2E", "title": "E2E Test"},
            "findings": {
                "fiscal": [
                    {
                        "id": "fiscal:e2e",
                        "issue": "E2E fiscal issue",
                        "severity": "medium",
                        "layer": "fiscal",
                        "details": {},
                    }
                ],
                "constitutional": [],
                "surveillance": [],
            },
        }
    ]
    report = build_report_from_analysis(results, jurisdiction="E2E City")
    with tempfile.TemporaryDirectory() as tmpdir:
        written = export_report(
            report,
            output_dir=tmpdir,
            formats=["json", "markdown"],
            template_dir=TEMPLATE_DIR,
        )
        md = written["markdown"].read_text(encoding="utf-8")
        assert "E2E fiscal issue" in md
        data = json.loads(written["json"].read_text(encoding="utf-8"))
        assert data["jurisdiction"] == "E2E City"
