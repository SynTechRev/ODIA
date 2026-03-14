"""Tests for auto_classify: finding classification and recommendation generation."""

from __future__ import annotations

from oraculus_di_auditor.reporting import (
    AuditReport,
    Finding,
    SeveritySummary,
    classify_finding,
    enrich_findings,
    generate_executive_summary,
    generate_recommendation,
)
from oraculus_di_auditor.reporting.models import build_report_from_analysis

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _anomaly(layer: str, doc_id: str = "doc-1") -> dict:
    return {
        "id": f"{layer}:test",
        "issue": f"Test {layer} issue",
        "severity": "high",
        "layer": layer,
        "details": {"document_id": doc_id},
    }


def _finding(
    category: str = "fiscal",
    doc_id: str = "doc-1",
    recommendation: str | None = None,
) -> Finding:
    return Finding(
        finding_id="F-001",
        title="Test finding",
        severity="high",
        category=category,
        document_id=doc_id,
        description="Test description",
        recommendation=recommendation,
    )


def _sample_report(findings: list[Finding] | None = None) -> AuditReport:
    return AuditReport(
        report_id="RPT-TEST",
        report_type="single_jurisdiction",
        generated_at="2026-03-14T00:00:00+00:00",
        jurisdiction="Test City",
        document_count=2,
        severity_summary=SeveritySummary(critical=1, high=2, medium=1),
        findings=findings or [],
        detector_summaries=[],
    )


# ---------------------------------------------------------------------------
# classify_finding
# ---------------------------------------------------------------------------


def test_procurement_timeline_classified_as_procurement_violation():
    cat = classify_finding(_anomaly("procurement_timeline"))
    assert cat == "procurement_violation"


def test_scope_expansion_classified_as_procurement_violation():
    cat = classify_finding(_anomaly("scope_expansion"))
    assert cat == "procurement_violation"


def test_signature_chain_classified_as_document_integrity():
    cat = classify_finding(_anomaly("signature_chain"))
    assert cat == "document_integrity"


def test_administrative_integrity_classified_as_document_integrity():
    cat = classify_finding(_anomaly("administrative_integrity"))
    assert cat == "document_integrity"


def test_governance_gap_classified_correctly():
    cat = classify_finding(_anomaly("governance_gap"))
    assert cat == "governance_gap"


def test_surveillance_classified_as_governance_gap():
    cat = classify_finding(_anomaly("surveillance"))
    assert cat == "governance_gap"


def test_fiscal_classified_as_fiscal_compliance():
    cat = classify_finding(_anomaly("fiscal"))
    assert cat == "fiscal_compliance"


def test_constitutional_classified_as_constitutional_concern():
    cat = classify_finding(_anomaly("constitutional"))
    assert cat == "constitutional_concern"


def test_cross_reference_classified_as_constitutional_concern():
    cat = classify_finding(_anomaly("cross_reference"))
    assert cat == "constitutional_concern"


def test_unknown_detector_falls_back_to_general():
    cat = classify_finding(_anomaly("totally_unknown_detector"))
    assert cat == "general_finding"


def test_empty_layer_falls_back_to_general():
    cat = classify_finding({"layer": ""})
    assert cat == "general_finding"


# ---------------------------------------------------------------------------
# generate_recommendation
# ---------------------------------------------------------------------------


def test_generate_recommendation_produces_nonempty_string():
    rec = generate_recommendation(_anomaly("fiscal"), "fiscal_compliance")
    assert isinstance(rec, str)
    assert len(rec) > 0


def test_generate_recommendation_unknown_category_uses_generic():
    rec = generate_recommendation(_anomaly("fiscal"), "general_finding")
    assert isinstance(rec, str)
    assert len(rec) > 10


def test_generate_recommendation_includes_document_id():
    rec = generate_recommendation(
        {"layer": "fiscal", "_document_id": "budget_resolution_2026"},
        "fiscal_compliance",
    )
    # The fiscal template doesn't include {document_id}, so we test
    # procurement which does include it.
    rec2 = generate_recommendation(
        {"layer": "procurement_timeline", "_document_id": "contract_xyz.pdf"},
        "procurement_violation",
    )
    assert "contract_xyz.pdf" in rec2


def test_generate_recommendation_fallback_doc_id():
    """When no doc_id is available uses placeholder."""
    rec = generate_recommendation(
        {"layer": "procurement_timeline"},
        "procurement_violation",
    )
    assert "referenced document" in rec


# ---------------------------------------------------------------------------
# enrich_findings
# ---------------------------------------------------------------------------


def test_enrich_findings_adds_recommendations_when_none():
    findings = [_finding("fiscal", recommendation=None)]
    enriched = enrich_findings(findings)
    assert len(enriched) == 1
    assert enriched[0].recommendation is not None
    assert len(enriched[0].recommendation) > 0


def test_enrich_findings_does_not_overwrite_existing_recommendations():
    original_rec = "My custom recommendation."
    findings = [_finding("fiscal", recommendation=original_rec)]
    enriched = enrich_findings(findings)
    assert enriched[0].recommendation == original_rec


def test_enrich_findings_adds_auto_category_metadata():
    findings = [_finding("surveillance")]
    enriched = enrich_findings(findings)
    assert enriched[0].metadata.get("auto_category") == "governance_gap"
    assert "Governance" in enriched[0].metadata.get("auto_category_display", "")


def test_enrich_findings_does_not_mutate_originals():
    original = _finding("fiscal", recommendation=None)
    enrich_findings([original])
    assert original.recommendation is None  # original untouched


def test_enrich_findings_empty_list():
    assert enrich_findings([]) == []


def test_enrich_findings_preserves_all_other_fields():
    f = Finding(
        finding_id="F-042",
        title="Custom Title",
        severity="critical",
        category="constitutional",
        document_id="doc-X",
        description="Custom desc",
        evidence="Evidence text",
        jurisdiction="City A",
    )
    enriched = enrich_findings([f])[0]
    assert enriched.finding_id == "F-042"
    assert enriched.title == "Custom Title"
    assert enriched.severity == "critical"
    assert enriched.evidence == "Evidence text"
    assert enriched.jurisdiction == "City A"


# ---------------------------------------------------------------------------
# generate_executive_summary
# ---------------------------------------------------------------------------


def test_generate_executive_summary_produces_readable_paragraph():
    report = _sample_report([_finding("fiscal")])
    summary = generate_executive_summary(report)
    assert isinstance(summary, str)
    assert len(summary) > 50
    assert "Test City" in summary


def test_generate_executive_summary_handles_zero_anomalies():
    report = AuditReport(
        report_id="RPT-EMPTY",
        report_type="single_jurisdiction",
        generated_at="2026-03-14T00:00:00+00:00",
        jurisdiction="Empty City",
        document_count=3,
        severity_summary=SeveritySummary(),
        findings=[],
        detector_summaries=[],
    )
    summary = generate_executive_summary(report)
    assert "no anomalies" in summary.lower() or "No anomalies" in summary
    assert "Empty City" in summary


def test_generate_executive_summary_mentions_critical_count():
    report = AuditReport(
        report_id="RPT-CRIT",
        report_type="single_jurisdiction",
        generated_at="2026-03-14T00:00:00+00:00",
        jurisdiction="Alert City",
        document_count=1,
        severity_summary=SeveritySummary(critical=3),
        findings=[_finding("constitutional")],
        detector_summaries=[],
    )
    summary = generate_executive_summary(report)
    assert "3" in summary
    assert "critical" in summary.lower()


def test_generate_executive_summary_mentions_jurisdiction():
    report = _sample_report()
    summary = generate_executive_summary(report)
    assert "Test City" in summary


def test_generate_executive_summary_mentions_document_count():
    report = _sample_report()
    summary = generate_executive_summary(report)
    assert "2" in summary


# ---------------------------------------------------------------------------
# build_report_from_analysis enrichment integration
# ---------------------------------------------------------------------------


def test_build_report_enriches_by_default():
    results = [
        {
            "metadata": {"document_id": "doc-1"},
            "findings": {
                "fiscal": [
                    {
                        "id": "fiscal:test",
                        "issue": "Fiscal issue",
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
    report = build_report_from_analysis(results)
    assert len(report.findings) == 1
    f = report.findings[0]
    assert f.recommendation is not None
    assert f.metadata.get("auto_category") is not None


def test_build_report_enrich_false_skips_enrichment():
    results = [
        {
            "metadata": {"document_id": "doc-1"},
            "findings": {
                "fiscal": [
                    {
                        "id": "fiscal:test",
                        "issue": "Fiscal issue",
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
    report = build_report_from_analysis(results, enrich=False)
    f = report.findings[0]
    # With enrich=False, no auto_category in metadata and recommendation is None
    assert f.recommendation is None
    assert "auto_category" not in f.metadata
