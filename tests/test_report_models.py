"""Tests for the unified audit report data models."""

from __future__ import annotations

import json

from oraculus_di_auditor.reporting import (
    AuditReport,
    Finding,
    SeveritySummary,
    build_report_from_analysis,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_analysis_result(
    doc_id: str = "doc-1",
    fiscal: list[dict] | None = None,
    constitutional: list[dict] | None = None,
    surveillance: list[dict] | None = None,
) -> dict:
    return {
        "metadata": {"document_id": doc_id, "title": f"Document {doc_id}"},
        "findings": {
            "fiscal": fiscal or [],
            "constitutional": constitutional or [],
            "surveillance": surveillance or [],
        },
    }


def _anomaly(
    id_: str = "fiscal:test",
    issue: str = "Test issue",
    severity: str = "medium",
    layer: str = "fiscal",
) -> dict:
    return {
        "id": id_,
        "issue": issue,
        "severity": severity,
        "layer": layer,
        "details": {},
    }


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------


def test_finding_validates_correctly():
    f = Finding(
        finding_id="F-001",
        title="Missing provenance",
        severity="high",
        category="fiscal",
        description="Provenance hash absent",
    )
    assert f.finding_id == "F-001"
    assert f.severity == "high"
    assert f.document_id is None
    assert f.recommendation is None
    assert f.metadata == {}


def test_finding_accepts_optional_fields():
    f = Finding(
        finding_id="F-002",
        title="Test",
        severity="low",
        category="surveillance",
        description="desc",
        evidence="line 42",
        recommendation="Remove clause",
        jurisdiction="City of Test",
        document_id="doc-99",
        metadata={"extra": True},
    )
    assert f.jurisdiction == "City of Test"
    assert f.document_id == "doc-99"
    assert f.metadata == {"extra": True}


# ---------------------------------------------------------------------------
# SeveritySummary
# ---------------------------------------------------------------------------


def test_severity_summary_total_computes_correctly():
    s = SeveritySummary(critical=2, high=3, medium=5, low=1)
    assert s.total == 11


def test_severity_summary_defaults_to_zero():
    s = SeveritySummary()
    assert s.total == 0
    assert s.critical == 0


# ---------------------------------------------------------------------------
# AuditReport serialization
# ---------------------------------------------------------------------------


def test_audit_report_serializes_to_dict():
    report = AuditReport(
        report_id="RPT-ABC123",
        report_type="single_jurisdiction",
        generated_at="2026-03-14T00:00:00+00:00",
        title="Test Report",
    )
    d = report.model_dump()
    assert d["report_id"] == "RPT-ABC123"
    assert d["report_type"] == "single_jurisdiction"
    assert isinstance(d["findings"], list)
    assert isinstance(d["documents"], list)


def test_audit_report_serializes_to_json():
    report = AuditReport(
        report_id="RPT-XYZ",
        report_type="triage",
        generated_at="2026-03-14T00:00:00+00:00",
    )
    raw = report.model_dump_json()
    parsed = json.loads(raw)
    assert parsed["report_id"] == "RPT-XYZ"
    # `total` is a @property — not serialized by Pydantic v2. Check the fields.
    assert "total" not in parsed["severity_summary"]
    assert parsed["severity_summary"]["critical"] == 0


# ---------------------------------------------------------------------------
# build_report_from_analysis
# ---------------------------------------------------------------------------


def test_build_report_from_analysis_converts_raw_results():
    results = [
        _make_analysis_result(
            doc_id="doc-1",
            fiscal=[_anomaly("fiscal:a", "Fiscal issue", "high", "fiscal")],
        )
    ]
    report = build_report_from_analysis(results, jurisdiction="Test City")
    assert report.report_type == "single_jurisdiction"
    assert report.jurisdiction == "Test City"
    assert report.document_count == 1
    assert len(report.findings) == 1
    assert report.severity_summary.high == 1
    assert report.severity_summary.total == 1


def test_findings_numbered_sequentially():
    results = [
        _make_analysis_result(
            doc_id="doc-1",
            fiscal=[
                _anomaly("fiscal:a", "A", "low"),
                _anomaly("fiscal:b", "B", "high"),
            ],
        )
    ]
    report = build_report_from_analysis(results)
    ids = [f.finding_id for f in report.findings]
    assert ids == ["F-001", "F-002"]


def test_findings_sorted_by_severity_critical_first():
    results = [
        _make_analysis_result(
            doc_id="doc-1",
            fiscal=[
                _anomaly("f:low", "Low", "low"),
                _anomaly("f:critical", "Critical", "critical"),
                _anomaly("f:medium", "Medium", "medium"),
                _anomaly("f:high", "High", "high"),
            ],
        )
    ]
    report = build_report_from_analysis(results)
    severities = [f.severity for f in report.findings]
    assert severities == ["critical", "high", "medium", "low"]


def test_empty_analysis_produces_valid_empty_report():
    report = build_report_from_analysis([])
    assert report.document_count == 0
    assert report.findings == []
    assert report.severity_summary.total == 0
    assert report.detector_summaries == []
    assert "no anomalies" in report.executive_summary.lower()


def test_report_id_starts_with_rpt():
    report = build_report_from_analysis([])
    assert report.report_id.startswith("RPT-")


def test_executive_summary_mentions_counts():
    results = [
        _make_analysis_result(
            doc_id="doc-1",
            fiscal=[_anomaly("f:h", "High issue", "high")],
            surveillance=[_anomaly("s:m", "Med issue", "medium")],
        )
    ]
    report = build_report_from_analysis(results, jurisdiction="Alpha City")
    assert "2" in report.executive_summary
    assert "Alpha City" in report.executive_summary


def test_detector_summaries_populated():
    results = [
        _make_analysis_result(
            doc_id="doc-1",
            fiscal=[
                _anomaly("f:1", "F1", "high"),
                _anomaly("f:2", "F2", "low"),
            ],
            surveillance=[_anomaly("s:1", "S1", "medium")],
        )
    ]
    report = build_report_from_analysis(results)
    names = {d.detector_name for d in report.detector_summaries}
    assert "fiscal" in names
    assert "surveillance" in names
    fiscal_det = next(
        d for d in report.detector_summaries if d.detector_name == "fiscal"
    )
    assert fiscal_det.anomaly_count == 2


def test_document_summary_populated():
    results = [
        _make_analysis_result(
            doc_id="doc-42",
            fiscal=[_anomaly("f:1", "F1", "critical")],
        )
    ]
    report = build_report_from_analysis(results)
    assert len(report.documents) == 1
    doc = report.documents[0]
    assert doc.document_id == "doc-42"
    assert doc.anomaly_count == 1
    assert doc.max_severity == "critical"


def test_multiple_documents():
    results = [
        _make_analysis_result("doc-A", fiscal=[_anomaly("f:1", "F1", "high")]),
        _make_analysis_result("doc-B", constitutional=[_anomaly("c:1", "C1", "low")]),
        _make_analysis_result("doc-C"),
    ]
    report = build_report_from_analysis(results)
    assert report.document_count == 3
    assert len(report.findings) == 2
    assert report.severity_summary.high == 1
    assert report.severity_summary.low == 1
