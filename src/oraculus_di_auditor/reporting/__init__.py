"""Unified reporting module for Oraculus-DI-Auditor.

Provides canonical data models for audit reports and a Jinja2 template
rendering engine, shared across all report generators: single-jurisdiction,
multi-jurisdiction, and triage pipeline.
"""

from oraculus_di_auditor.reporting.auto_classify import (
    FINDING_CATEGORIES,
    classify_finding,
    enrich_findings,
    generate_executive_summary,
    generate_recommendation,
)
from oraculus_di_auditor.reporting.format_converters import (
    export_report,
    get_available_formats,
    markdown_to_docx,
    markdown_to_html,
    markdown_to_pdf,
)
from oraculus_di_auditor.reporting.models import (
    AuditReport,
    DetectorSummary,
    DocumentSummary,
    Finding,
    SeveritySummary,
    build_report_from_analysis,
)
from oraculus_di_auditor.reporting.template_engine import ReportTemplateEngine

__all__ = [
    "AuditReport",
    "DetectorSummary",
    "DocumentSummary",
    "FINDING_CATEGORIES",
    "Finding",
    "ReportTemplateEngine",
    "SeveritySummary",
    "build_report_from_analysis",
    "classify_finding",
    "enrich_findings",
    "export_report",
    "generate_executive_summary",
    "generate_recommendation",
    "get_available_formats",
    "markdown_to_docx",
    "markdown_to_html",
    "markdown_to_pdf",
]
