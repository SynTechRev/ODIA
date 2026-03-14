"""Tests for ComparativeReportGenerator."""

from __future__ import annotations

from oraculus_di_auditor.multi_jurisdiction.report_generator import (
    ComparativeReportGenerator,
)

# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _anomaly(aid, issue, severity="medium", layer="fiscal"):
    return {
        "id": aid,
        "issue": issue,
        "severity": severity,
        "layer": layer,
        "details": {},
    }


def _jdata(jid, doc_results, name=None):
    total = sum(len(a) for dr in doc_results for a in dr.get("findings", {}).values())
    by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_det = {}
    for dr in doc_results:
        for det, anomalies in dr.get("findings", {}).items():
            by_det[det] = by_det.get(det, 0) + len(anomalies)
            for a in anomalies:
                s = a.get("severity", "medium")
                by_sev[s] = by_sev.get(s, 0) + 1
    return {
        "jurisdiction_id": jid,
        "jurisdiction_name": name or jid.replace("_", " ").title(),
        "document_count": len(doc_results),
        "results": doc_results,
        "anomaly_summary": {
            "total": total,
            "by_severity": by_sev,
            "by_detector": by_det,
        },
    }


def _doc_result(jid, findings):
    return {"jurisdiction_id": jid, "findings": findings, "metadata": {}}


# shared anomalies
_FISCAL = _anomaly(
    "fiscal:amount-without-appropriation",
    "Fiscal amounts present without appropriation reference",
)
_HIGH = _anomaly(
    "governance:capability-without-policy",
    "Capability deployed without policy",
    severity="high",
    layer="governance",
)
_CRITICAL = _anomaly(
    "governance:data-retention-gap",
    "Data retention gap detected",
    severity="critical",
    layer="governance",
)

# Minimal cross-jurisdiction patterns dict (as returned by detect_all_patterns)
_EMPTY_PATTERNS = {
    "patterns_detected": 0,
    "vendor_playbook_patterns": [],
    "procurement_parallels": [],
    "regional_governance_gaps": [],
    "summary": {
        "jurisdictions_analyzed": 0,
        "most_common_pattern": "none",
        "highest_risk_jurisdictions": [],
    },
}


def _patterns_with_vp(jids):
    """Minimal vendor-playbook pattern affecting the given jids."""
    return {
        "patterns_detected": 1,
        "vendor_playbook_patterns": [
            {
                "pattern_id": "vp:fiscal-amount-without-appropriation",
                "pattern_type": "vendor_playbook_replication",
                "description": "Same fiscal anomaly across jurisdictions.",
                "jurisdictions_affected": list(jids),
                "jurisdiction_count": len(jids),
                "common_detector": "fiscal",
                "common_severity": "medium",
                "vendor_keywords": [],
                "evidence": [],
                "confidence": 1.0,
            }
        ],
        "procurement_parallels": [],
        "regional_governance_gaps": [],
        "summary": {
            "jurisdictions_analyzed": len(jids),
            "most_common_pattern": "vendor_playbook_replication",
            "highest_risk_jurisdictions": list(jids),
        },
    }


# ---------------------------------------------------------------------------
# JSON report structure
# ---------------------------------------------------------------------------


def test_json_report_has_all_required_sections():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL]})])
        for jid in ("city_a", "city_b")
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    report = gen.generate_json_report()

    for key in (
        "report_type",
        "generated_at",
        "jurisdictions",
        "comparison_matrix",
        "cross_jurisdiction_patterns",
        "risk_ranking",
        "recommendations",
    ):
        assert key in report, f"Missing key: {key}"
    assert report["report_type"] == "multi_jurisdiction_comparison"


def test_json_jurisdictions_block_contains_expected_fields():
    results = {
        "city_a": _jdata("city_a", [_doc_result("city_a", {"fiscal": [_FISCAL]})]),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    report = gen.generate_json_report()

    entry = report["jurisdictions"]["city_a"]
    for field in ("name", "document_count", "anomaly_count", "top_severity"):
        assert field in entry, f"Missing jurisdictions field: {field}"


# ---------------------------------------------------------------------------
# Comparison matrix
# ---------------------------------------------------------------------------


def test_comparison_matrix_has_correct_dimensions():
    results = {
        jid: _jdata(
            jid, [_doc_result(jid, {"fiscal": [_FISCAL], "governance": [_HIGH]})]
        )
        for jid in ("city_a", "city_b")
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    matrix = gen.generate_json_report()["comparison_matrix"]

    # Both detectors should be rows
    assert "fiscal" in matrix
    assert "governance" in matrix
    # Both jurisdictions should be columns in each row
    for det in ("fiscal", "governance"):
        assert "city_a" in matrix[det]
        assert "city_b" in matrix[det]


def test_comparison_matrix_counts_are_correct():
    results = {
        "city_a": _jdata(
            "city_a",
            [_doc_result("city_a", {"fiscal": [_FISCAL, _FISCAL]})],
        ),
        "city_b": _jdata(
            "city_b",
            [_doc_result("city_b", {"fiscal": [_FISCAL]})],
        ),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    matrix = gen.generate_json_report()["comparison_matrix"]

    assert matrix["fiscal"]["city_a"] == 2
    assert matrix["fiscal"]["city_b"] == 1


def test_comparison_matrix_missing_detector_is_zero():
    """Jurisdiction with no fiscal anomalies should show 0 in the fiscal column."""
    results = {
        "city_a": _jdata("city_a", [_doc_result("city_a", {"fiscal": [_FISCAL]})]),
        "city_b": _jdata("city_b", [_doc_result("city_b", {"governance": [_HIGH]})]),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    matrix = gen.generate_json_report()["comparison_matrix"]

    assert matrix["fiscal"]["city_b"] == 0
    assert matrix["governance"]["city_a"] == 0


# ---------------------------------------------------------------------------
# Risk ranking
# ---------------------------------------------------------------------------


def test_risk_ranking_sorted_by_score_descending():
    results = {
        "city_low": _jdata(
            "city_low", [_doc_result("city_low", {"fiscal": [_FISCAL]})]
        ),
        "city_high": _jdata(
            "city_high",
            [_doc_result("city_high", {"governance": [_CRITICAL, _HIGH]})],
        ),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    ranking = gen.generate_json_report()["risk_ranking"]

    scores = [r["risk_score"] for r in ranking]
    assert scores == sorted(scores, reverse=True)
    assert ranking[0]["jurisdiction_id"] == "city_high"


def test_risk_ranking_includes_all_jurisdictions():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL]})])
        for jid in ("city_a", "city_b", "city_c")
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    ranking = gen.generate_json_report()["risk_ranking"]

    assert len(ranking) == 3
    ranked_ids = {r["jurisdiction_id"] for r in ranking}
    assert ranked_ids == {"city_a", "city_b", "city_c"}


def test_risk_ranking_pattern_involvement_increases_score():
    """A jurisdiction involved in cross-jurisdiction patterns gets a bonus."""
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL]})])
        for jid in ("city_a", "city_b")
    }
    # No patterns → base score only
    gen_no_pat = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    base_score = {
        r["jurisdiction_id"]: r["risk_score"]
        for r in gen_no_pat.generate_json_report()["risk_ranking"]
    }

    # With vendor playbook pattern → city_a and city_b both get bonus
    gen_with_pat = ComparativeReportGenerator(
        results, _patterns_with_vp(["city_a", "city_b"])
    )
    bonus_score = {
        r["jurisdiction_id"]: r["risk_score"]
        for r in gen_with_pat.generate_json_report()["risk_ranking"]
    }

    assert bonus_score["city_a"] > base_score["city_a"]
    assert bonus_score["city_b"] > base_score["city_b"]


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def test_markdown_report_contains_all_section_headers():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL]})])
        for jid in ("city_a", "city_b")
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    md = gen.generate_markdown_report()

    for header in (
        "# Multi-Jurisdiction Comparative Audit Report",
        "## Executive Summary",
        "## Jurisdiction Comparison Table",
        "## Cross-Jurisdiction Patterns",
        "## Risk Ranking",
        "## Recommendations",
    ):
        assert header in md, f"Missing Markdown header: {header!r}"


def test_markdown_report_is_string():
    results = {
        "city_a": _jdata("city_a", [_doc_result("city_a", {"fiscal": [_FISCAL]})]),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    assert isinstance(gen.generate_markdown_report(), str)


def test_markdown_report_includes_jurisdiction_names():
    results = {
        "city_alpha": _jdata(
            "city_alpha",
            [_doc_result("city_alpha", {"fiscal": [_FISCAL]})],
            name="City of Alpha",
        ),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    md = gen.generate_markdown_report()
    assert "City of Alpha" in md


# ---------------------------------------------------------------------------
# Timeline comparison
# ---------------------------------------------------------------------------


def test_timeline_comparison_returns_correct_keys():
    results = {
        "city_a": _jdata("city_a", [_doc_result("city_a", {"fiscal": [_FISCAL]})]),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    timeline = gen.generate_timeline_comparison()

    assert "timeline_events" in timeline
    assert "parallel_timelines" in timeline
    assert isinstance(timeline["timeline_events"], list)
    assert isinstance(timeline["parallel_timelines"], list)


def test_timeline_extracts_dates_from_procurement_anomaly():
    """Procurement anomaly with explicit date fields should appear as events."""
    dated_anomaly = {
        "id": "procurement:execution-precedes-authorization",
        "issue": "Contract executed 10 day(s) before council authorization",
        "severity": "high",
        "layer": "procurement",
        "details": {
            "execution_date": "2024-03-01",
            "authorization_date": "2024-03-11",
        },
    }
    results = {
        "city_a": _jdata(
            "city_a",
            [_doc_result("city_a", {"procurement_timeline": [dated_anomaly]})],
        ),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    events = gen.generate_timeline_comparison()["timeline_events"]

    event_types = {e["event_type"] for e in events}
    assert "contract_execution" in event_types
    assert "council_authorization" in event_types
    dates = {e["date"] for e in events}
    assert "2024-03-01" in dates
    assert "2024-03-11" in dates


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


def test_recommendations_non_empty_when_patterns_found():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL]})])
        for jid in ("city_a", "city_b")
    }
    gen = ComparativeReportGenerator(results, _patterns_with_vp(["city_a", "city_b"]))
    recs = gen.generate_json_report()["recommendations"]

    assert len(recs) > 0
    assert isinstance(recs[0], str)


def test_recommendations_present_when_no_patterns():
    results = {
        "city_a": _jdata("city_a", [_doc_result("city_a", {"fiscal": [_FISCAL]})]),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    recs = gen.generate_json_report()["recommendations"]

    # Should still produce at least one recommendation (the no-patterns default)
    assert len(recs) >= 1


# ---------------------------------------------------------------------------
# Single jurisdiction (degenerate case)
# ---------------------------------------------------------------------------


def test_single_jurisdiction_produces_valid_report():
    results = {
        "city_solo": _jdata(
            "city_solo",
            [_doc_result("city_solo", {"fiscal": [_FISCAL]})],
            name="Solo City",
        ),
    }
    gen = ComparativeReportGenerator(results, _EMPTY_PATTERNS)
    report = gen.generate_json_report()

    assert report["jurisdictions"]["city_solo"]["name"] == "Solo City"
    assert len(report["risk_ranking"]) == 1
    # With one jurisdiction there can be no cross-jurisdiction patterns
    assert report["cross_jurisdiction_patterns"] == []
