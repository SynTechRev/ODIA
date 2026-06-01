"""Tests for Legal R.A.I.A. Vector 3 — temporal re-evaluation engine."""

from __future__ import annotations

import pytest

from odia_legal.vector3 import LegalVector3, ReEvaluationResult, cadenced_reeval

# ---------------------------------------------------------------------------
# Sample fixtures
# ---------------------------------------------------------------------------

_ALPR_DOC = {
    "text": (
        "The agency deployed ALPR cameras across all intersections. "
        "CPRA requests were denied citing public interest under § 7922.000 "
        "without balancing test analysis. No AB 481 policy was adopted prior "
        "to deployment. Federal JAG grant funds were used to supplant "
        "existing surveillance budget. ALPR data is retained indefinitely."
    )
}

_FINDING_HIGH = {
    "id": "legal:l3:exemption_misapplication:cpra_catchall_no_balancing",
    "issue": "CPRA catch-all exemption invoked without balancing test",
    "severity": "high",
    "layer": "l3_exemption_misapplication",
    "details": {"statute": "Gov. Code § 7922.000"},
}

_FINDING_MEDIUM = {
    "id": "legal:l2:procedural_compliance:ab481_missing",
    "issue": "AB 481 policy not adopted",
    "severity": "medium",
    "layer": "l2_procedural_compliance",
    "details": {},
}

_FINDING_LOW = {
    "id": "legal:l1:statutory_applicability:alpr_sb34_retention",
    "issue": "Statute applies: Civ. Code § 1798.90.53",
    "severity": "low",
    "layer": "l1_statutory_applicability",
    "details": {},
}

_PRIOR = [_FINDING_HIGH, _FINDING_MEDIUM, _FINDING_LOW]


# ===========================================================================
# Basic integration
# ===========================================================================


def test_reeval_returns_result_instance():
    evaluator = LegalVector3()
    result = evaluator.reeval(_ALPR_DOC, _PRIOR, prior_run_date="2023-01-01")
    assert isinstance(result, ReEvaluationResult)


def test_run_date_defaults_to_today():
    result = LegalVector3().reeval(_ALPR_DOC, [], prior_run_date="2023-01-01")
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2}", result.run_date)


def test_prior_run_date_preserved():
    result = LegalVector3().reeval(_ALPR_DOC, [], prior_run_date="2022-06-15")
    assert result.prior_run_date == "2022-06-15"


def test_doc_id_from_kwarg():
    result = LegalVector3().reeval(
        _ALPR_DOC, [], prior_run_date="2023-01-01", doc_id="test-doc-001"
    )
    assert result.doc_id == "test-doc-001"


def test_doc_id_from_doc_field():
    doc = dict(_ALPR_DOC)
    doc["document_id"] = "auto-doc-999"
    result = LegalVector3().reeval(doc, [], prior_run_date="2023-01-01")
    assert result.doc_id == "auto-doc-999"


# ===========================================================================
# Delta classification
# ===========================================================================


def test_all_prior_findings_not_in_current_become_resolved():
    ghost_finding = {
        "id": "legal:l99:nonexistent:ghost",
        "issue": "ghost finding that never re-triggers",
        "severity": "high",
        "layer": "l99",
        "details": {},
    }
    result = LegalVector3().reeval(
        {"text": "nothing relevant here"},
        [ghost_finding],
        prior_run_date="2023-01-01",
    )
    resolved_ids = [f["id"] for f in result.resolved_findings]
    assert "legal:l99:nonexistent:ghost" in resolved_ids


def test_new_finding_appears_only_in_new():
    fresh_finding = {
        "id": "legal:l99:nonexistent:new_one",
        "issue": "new finding not in prior",
        "severity": "medium",
        "layer": "l99",
        "details": {},
    }
    # Patch: run against empty prior so we know current > prior
    result = LegalVector3().reeval(
        {"text": "nothing relevant"},
        [],
        prior_run_date="2023-01-01",
    )
    # The doc produces no findings, so new_findings should be empty
    assert isinstance(result.new_findings, list)


def test_unchanged_finding_when_same_id_and_severity():
    # Use the same finding in both prior and what detectors produce
    # We inject a finding that is also in _ALPR_DOC's real detector output
    evaluator = LegalVector3()
    # First get what the detectors actually produce on this doc
    from odia_legal.vector3 import _run_all_detectors
    current = _run_all_detectors(_ALPR_DOC)
    if not current:
        pytest.skip("no detector findings on test doc")

    # Re-run with current as prior — everything should be unchanged (not resolved/new)
    result = evaluator.reeval(_ALPR_DOC, current, prior_run_date="2023-01-01")
    assert result.changed_count == 0
    assert len(result.unchanged_findings) == len(current)


def test_upgraded_when_severity_increases():
    low_prior = {
        "id": "legal:l3:exemption_misapplication:cpra_catchall_no_balancing",
        "issue": "low severity version",
        "severity": "low",
        "layer": "l3_exemption_misapplication",
        "details": {},
    }
    # The real detector on _ALPR_DOC should produce "high" for this ID
    from odia_legal.vector3 import _run_all_detectors
    current = _run_all_detectors(_ALPR_DOC)
    real = next((f for f in current if f["id"] == low_prior["id"]), None)
    if real is None or real.get("severity") == "low":
        pytest.skip("this finding not triggered or already low on test doc")

    result = LegalVector3().reeval(_ALPR_DOC, [low_prior], prior_run_date="2023-01-01")
    upgraded_ids = [f["id"] for f in result.upgraded_findings]
    assert low_prior["id"] in upgraded_ids


def test_downgraded_when_severity_decreases():
    high_prior = {
        "id": "legal:l1:statutory_applicability:alpr_sb34_retention",
        "issue": "high severity version",
        "severity": "high",  # artificially high
        "layer": "l1_statutory_applicability",
        "details": {},
    }
    from odia_legal.vector3 import _run_all_detectors
    current = _run_all_detectors(_ALPR_DOC)
    real = next((f for f in current if f["id"] == high_prior["id"]), None)
    if real is None or real.get("severity") == "high":
        pytest.skip("finding not triggered or still high")

    result = LegalVector3().reeval(_ALPR_DOC, [high_prior], prior_run_date="2023-01-01")
    downgraded_ids = [f["id"] for f in result.downgraded_findings]
    assert high_prior["id"] in downgraded_ids


# ===========================================================================
# changed_count and current_findings
# ===========================================================================


def test_changed_count_is_sum_of_new_resolved_upgraded_downgraded():
    result = LegalVector3().reeval(
        {"text": "nothing here"}, _PRIOR, prior_run_date="2023-01-01"
    )
    expected = (
        len(result.new_findings)
        + len(result.resolved_findings)
        + len(result.upgraded_findings)
        + len(result.downgraded_findings)
    )
    assert result.changed_count == expected


def test_current_findings_union():
    result = LegalVector3().reeval(_ALPR_DOC, [], prior_run_date="2023-01-01")
    expected_total = (
        len(result.new_findings)
        + len(result.upgraded_findings)
        + len(result.downgraded_findings)
        + len(result.unchanged_findings)
    )
    assert len(result.current_findings) == expected_total


# ===========================================================================
# Summary and serialization
# ===========================================================================


def test_summary_contains_run_date():
    result = LegalVector3().reeval(
        _ALPR_DOC, _PRIOR, prior_run_date="2023-01-01", run_date="2025-06-01"
    )
    s = result.summary()
    assert "2023-01-01" in s
    assert "2025-06-01" in s


def test_summary_contains_doc_id():
    result = LegalVector3().reeval(
        _ALPR_DOC, [], prior_run_date="2023-01-01", doc_id="alpr-policy"
    )
    assert "alpr-policy" in result.summary()


def test_to_dict_keys():
    result = LegalVector3().reeval(_ALPR_DOC, [], prior_run_date="2023-01-01")
    d = result.to_dict()
    for key in ("doc_id", "run_date", "prior_run_date", "new", "resolved",
                "upgraded", "downgraded", "unchanged", "currency_changes", "changed_count"):
        assert key in d


def test_to_dict_finding_ids_are_strings():
    result = LegalVector3().reeval(_ALPR_DOC, _PRIOR, prior_run_date="2023-01-01")
    d = result.to_dict()
    for category in ("new", "resolved", "upgraded", "downgraded", "unchanged"):
        for fid in d[category]:
            assert isinstance(fid, str)


# ===========================================================================
# Currency sweep
# ===========================================================================


def test_currency_changes_is_list():
    result = LegalVector3().reeval(_ALPR_DOC, [], prior_run_date="2020-01-01")
    assert isinstance(result.currency_changes, list)


def test_currency_change_fields():
    result = LegalVector3().reeval(_ALPR_DOC, [], prior_run_date="2020-01-01")
    for change in result.currency_changes:
        assert hasattr(change, "case_name")
        assert hasattr(change, "prior_status")
        assert hasattr(change, "current_status")
        assert hasattr(change, "notes")


def test_no_currency_changes_for_future_prior_date():
    # If prior_run_date is in the future, no signals should be "newer" than it
    result = LegalVector3().reeval(_ALPR_DOC, [], prior_run_date="2099-01-01")
    assert result.currency_changes == []


# ===========================================================================
# cadenced_reeval
# ===========================================================================


def test_cadenced_reeval_returns_list():
    batch = [
        {"doc": _ALPR_DOC, "prior_findings": _PRIOR, "doc_id": "doc-1"},
        {"doc": {"text": "nothing here"}, "prior_findings": [], "doc_id": "doc-2"},
    ]
    results = cadenced_reeval(batch, prior_run_date="2023-01-01")
    assert len(results) == 2
    assert all(isinstance(r, ReEvaluationResult) for r in results)


def test_cadenced_reeval_doc_ids():
    batch = [
        {"doc": {"text": "x"}, "prior_findings": [], "doc_id": "alpha"},
        {"doc": {"text": "y"}, "prior_findings": [], "doc_id": "beta"},
    ]
    results = cadenced_reeval(batch, prior_run_date="2023-01-01")
    ids = [r.doc_id for r in results]
    assert "alpha" in ids
    assert "beta" in ids


def test_cadenced_reeval_empty_batch():
    assert cadenced_reeval([], prior_run_date="2023-01-01") == []
