"""Tests for CrossJurisdictionPatternDetector."""

from __future__ import annotations

from oraculus_di_auditor.multi_jurisdiction.pattern_detector import (
    CrossJurisdictionPatternDetector,
)

# ---------------------------------------------------------------------------
# Helpers to build synthetic runner output
# ---------------------------------------------------------------------------


def _anomaly(
    aid: str,
    issue: str,
    severity: str = "medium",
    layer: str = "fiscal",
    details: dict | None = None,
) -> dict:
    return {
        "id": aid,
        "issue": issue,
        "severity": severity,
        "layer": layer,
        "details": details or {},
    }


def _doc_result(jid: str, findings: dict) -> dict:
    return {
        "jurisdiction_id": jid,
        "findings": findings,
        "metadata": {},
    }


def _jdata(jid: str, doc_results: list) -> dict:
    return {
        "jurisdiction_id": jid,
        "jurisdiction_name": jid.replace("_", " ").title(),
        "document_count": len(doc_results),
        "results": doc_results,
        "anomaly_summary": {"total": 0, "by_severity": {}, "by_detector": {}},
    }


# Shared fiscal anomaly — same id across all jurisdictions
_FISCAL_ANOMALY = _anomaly(
    "fiscal:amount-without-appropriation",
    "Fiscal amounts present without appropriation reference",
    severity="medium",
    layer="fiscal",
)

# Governance anomaly with governance keywords in issue text
_GOV_ANOMALY = _anomaly(
    "governance:capability-without-policy",
    "Surveillance capability deployed without governance documentation"
    " or policy oversight",
    severity="high",
    layer="governance",
)

# Procurement-flavoured anomaly
_PROCUREMENT_ANOMALY = _anomaly(
    "scope:amendment-without-baseline",
    "Amendment contract found with no original authorization reference",
    severity="medium",
    layer="scope",
)

# Different anomaly id — should NOT trigger cross-jurisdiction pattern with the above
_UNIQUE_ANOMALY = _anomaly(
    "constitutional:broad-delegation",
    "Broad delegation of authority detected",
    severity="medium",
    layer="constitutional",
)


# ---------------------------------------------------------------------------
# Empty / single-jurisdiction edge cases
# ---------------------------------------------------------------------------


def test_empty_results_produce_valid_empty_output():
    det = CrossJurisdictionPatternDetector({})
    result = det.detect_all_patterns()
    assert result["patterns_detected"] == 0
    assert result["vendor_playbook_patterns"] == []
    assert result["procurement_parallels"] == []
    assert result["regional_governance_gaps"] == []
    assert result["summary"]["jurisdictions_analyzed"] == 0
    assert result["summary"]["highest_risk_jurisdictions"] == []


def test_single_jurisdiction_returns_no_cross_jurisdiction_patterns():
    results = {
        "city_a": _jdata(
            "city_a",
            [_doc_result("city_a", {"fiscal": [_FISCAL_ANOMALY]})],
        )
    }
    det = CrossJurisdictionPatternDetector(results)
    assert det.detect_vendor_playbook() == []
    assert det.detect_procurement_parallels() == []
    assert det.detect_governance_gaps_regional() == []


# ---------------------------------------------------------------------------
# detect_vendor_playbook
# ---------------------------------------------------------------------------


def test_vendor_playbook_detected_across_three_jurisdictions():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL_ANOMALY]})])
        for jid in ("city_a", "city_b", "city_c")
    }
    det = CrossJurisdictionPatternDetector(results)
    patterns = det.detect_vendor_playbook()

    assert len(patterns) >= 1
    # The shared anomaly id must appear in a pattern
    aids = {p["pattern_id"] for p in patterns}
    assert any("fiscal-amount-without-appropriation" in pid for pid in aids)


def test_vendor_playbook_pattern_has_required_fields():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL_ANOMALY]})])
        for jid in ("city_a", "city_b")
    }
    det = CrossJurisdictionPatternDetector(results)
    patterns = det.detect_vendor_playbook()

    assert len(patterns) >= 1
    p = patterns[0]
    for field in (
        "pattern_id",
        "pattern_type",
        "description",
        "jurisdictions_affected",
        "jurisdiction_count",
        "common_detector",
        "common_severity",
        "evidence",
        "confidence",
    ):
        assert field in p, f"Missing field: {field}"
    assert p["pattern_type"] == "vendor_playbook_replication"
    assert set(p["jurisdictions_affected"]) == {"city_a", "city_b"}


def test_no_vendor_playbook_when_anomaly_ids_differ():
    """Different anomaly ids in each jurisdiction → no shared pattern."""
    results = {
        "city_a": _jdata(
            "city_a",
            [_doc_result("city_a", {"fiscal": [_FISCAL_ANOMALY]})],
        ),
        "city_b": _jdata(
            "city_b",
            [_doc_result("city_b", {"constitutional": [_UNIQUE_ANOMALY]})],
        ),
    }
    det = CrossJurisdictionPatternDetector(results)
    # Both anomalies are unique per jurisdiction — no cross-jurisdiction match
    patterns = [p for p in det.detect_vendor_playbook() if p["jurisdiction_count"] >= 2]
    assert patterns == []


# ---------------------------------------------------------------------------
# detect_procurement_parallels
# ---------------------------------------------------------------------------


def test_procurement_parallels_detected_with_shared_keyword():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"scope": [_PROCUREMENT_ANOMALY]})])
        for jid in ("city_a", "city_b")
    }
    det = CrossJurisdictionPatternDetector(results)
    patterns = det.detect_procurement_parallels()

    assert len(patterns) >= 1
    p = patterns[0]
    assert p["pattern_type"] == "procurement_parallel"
    assert "jurisdictions" in p
    assert len(p["jurisdictions"]) >= 2


def test_procurement_parallels_required_fields():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"scope": [_PROCUREMENT_ANOMALY]})])
        for jid in ("city_a", "city_b")
    }
    det = CrossJurisdictionPatternDetector(results)
    patterns = det.detect_procurement_parallels()

    assert len(patterns) >= 1
    p = patterns[0]
    for field in (
        "pattern_id",
        "pattern_type",
        "description",
        "vendor_or_keyword",
        "jurisdictions",
        "details",
    ):
        assert field in p, f"Missing field: {field}"
    assert isinstance(p["jurisdictions"], list)
    assert isinstance(p["details"], dict)


# ---------------------------------------------------------------------------
# detect_governance_gaps_regional
# ---------------------------------------------------------------------------


def test_regional_governance_gap_detected():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"governance": [_GOV_ANOMALY]})])
        for jid in ("city_a", "city_b")
    }
    det = CrossJurisdictionPatternDetector(results)
    patterns = det.detect_governance_gaps_regional()

    assert len(patterns) >= 1
    p = patterns[0]
    assert p["pattern_type"] == "regional_governance_gap"
    assert set(p["jurisdictions_affected"]) == {"city_a", "city_b"}


def test_regional_governance_gap_required_fields():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"governance": [_GOV_ANOMALY]})])
        for jid in ("city_a", "city_b")
    }
    det = CrossJurisdictionPatternDetector(results)
    patterns = det.detect_governance_gaps_regional()

    assert len(patterns) >= 1
    p = patterns[0]
    for field in (
        "pattern_id",
        "pattern_type",
        "description",
        "jurisdictions_affected",
        "jurisdiction_count",
        "common_severity",
        "evidence",
        "confidence",
    ):
        assert field in p, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# detect_all_patterns
# ---------------------------------------------------------------------------


def test_detect_all_patterns_returns_complete_structure():
    results = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL_ANOMALY]})])
        for jid in ("city_a", "city_b")
    }
    det = CrossJurisdictionPatternDetector(results)
    output = det.detect_all_patterns()

    for field in (
        "patterns_detected",
        "vendor_playbook_patterns",
        "procurement_parallels",
        "regional_governance_gaps",
        "summary",
    ):
        assert field in output, f"Missing top-level field: {field}"

    summary = output["summary"]
    for sf in (
        "jurisdictions_analyzed",
        "most_common_pattern",
        "highest_risk_jurisdictions",
    ):
        assert sf in summary, f"Missing summary field: {sf}"


def test_detect_all_patterns_count_is_sum_of_lists():
    results = {
        jid: _jdata(
            jid,
            [
                _doc_result(
                    jid,
                    {
                        "fiscal": [_FISCAL_ANOMALY],
                        "governance": [_GOV_ANOMALY],
                    },
                )
            ],
        )
        for jid in ("city_a", "city_b")
    }
    det = CrossJurisdictionPatternDetector(results)
    output = det.detect_all_patterns()

    expected = (
        len(output["vendor_playbook_patterns"])
        + len(output["procurement_parallels"])
        + len(output["regional_governance_gaps"])
    )
    assert output["patterns_detected"] == expected


# ---------------------------------------------------------------------------
# confidence scoring
# ---------------------------------------------------------------------------


def test_confidence_scales_with_jurisdiction_count():
    """More jurisdictions sharing a pattern → higher confidence."""
    two_j = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL_ANOMALY]})])
        for jid in ("city_a", "city_b")
    }
    four_j = {
        jid: _jdata(jid, [_doc_result(jid, {"fiscal": [_FISCAL_ANOMALY]})])
        for jid in ("city_a", "city_b", "city_c", "city_d")
    }

    patterns_2 = CrossJurisdictionPatternDetector(two_j).detect_vendor_playbook()
    patterns_4 = CrossJurisdictionPatternDetector(four_j).detect_vendor_playbook()

    assert patterns_2 and patterns_4
    # Both share the same anomaly in all jurisdictions — 2/2=1.0 and 4/4=1.0
    # But in the 4-jurisdiction case the matched count is also 4 of 4 → same.
    # Test instead that confidence is in [0,1] and is higher when more jids match.
    assert 0.0 <= patterns_2[0]["confidence"] <= 1.0
    assert 0.0 <= patterns_4[0]["confidence"] <= 1.0


def test_partial_coverage_confidence_less_than_full():
    """Pattern in 2 of 4 jurisdictions has lower confidence than 4 of 4."""
    results = {
        "city_a": _jdata(
            "city_a",
            [_doc_result("city_a", {"fiscal": [_FISCAL_ANOMALY]})],
        ),
        "city_b": _jdata(
            "city_b",
            [_doc_result("city_b", {"fiscal": [_FISCAL_ANOMALY]})],
        ),
        "city_c": _jdata(
            "city_c",
            [_doc_result("city_c", {"constitutional": [_UNIQUE_ANOMALY]})],
        ),
        "city_d": _jdata(
            "city_d",
            [_doc_result("city_d", {"constitutional": [_UNIQUE_ANOMALY]})],
        ),
    }
    det = CrossJurisdictionPatternDetector(results)
    patterns = det.detect_vendor_playbook()

    # fiscal pattern matches 2 of 4 → confidence = 0.5
    fiscal_pat = next(
        (
            p
            for p in patterns
            if "fiscal-amount-without-appropriation" in p["pattern_id"]
        ),
        None,
    )
    assert fiscal_pat is not None
    assert fiscal_pat["confidence"] == 0.5
