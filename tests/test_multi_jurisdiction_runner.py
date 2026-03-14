"""Tests for MultiJurisdictionRunner."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.config.jurisdiction_loader import JurisdictionConfig
from oraculus_di_auditor.multi_jurisdiction.registry import JurisdictionRegistry
from oraculus_di_auditor.multi_jurisdiction.runner import MultiJurisdictionRunner

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_config(name: str = "Test City", state: str = "CA") -> JurisdictionConfig:
    return JurisdictionConfig(name=name, state=state, country="US")


def _make_registry(*id_name_pairs: tuple[str, str]) -> JurisdictionRegistry:
    registry = JurisdictionRegistry()
    for jid, name in id_name_pairs:
        registry.register(jid, _make_config(name=name))
    return registry


_CLEAN_DOC = {
    "document_text": "This document contains routine policy language.",
    "metadata": {"title": "Policy Doc", "document_id": "doc-001"},
}

_FISCAL_DOC = {
    "document_text": "The program receives $1,000,000 for operations.",
    "metadata": {"title": "Budget Doc", "document_id": "doc-fiscal"},
}


# ---------------------------------------------------------------------------
# Single jurisdiction
# ---------------------------------------------------------------------------


def test_analyze_single_jurisdiction_returns_correct_shape():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    result = runner.analyze_jurisdiction("city_a", [_CLEAN_DOC])

    assert result["jurisdiction_id"] == "city_a"
    assert result["jurisdiction_name"] == "City A"
    assert result["document_count"] == 1
    assert isinstance(result["results"], list)
    assert len(result["results"]) == 1
    assert "anomaly_summary" in result


def test_analyze_single_jurisdiction_anomaly_summary_keys():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    result = runner.analyze_jurisdiction("city_a", [_CLEAN_DOC])

    summary = result["anomaly_summary"]
    assert "total" in summary
    assert "by_severity" in summary
    assert "by_detector" in summary
    for level in ("critical", "high", "medium", "low"):
        assert level in summary["by_severity"]


def test_results_tagged_with_jurisdiction_id():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    result = runner.analyze_jurisdiction("city_a", [_CLEAN_DOC, _FISCAL_DOC])

    for doc_result in result["results"]:
        assert doc_result["jurisdiction_id"] == "city_a"


def test_anomaly_summary_counts_are_correct():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    result = runner.analyze_jurisdiction("city_a", [_FISCAL_DOC])

    summary = result["anomaly_summary"]
    # fiscal doc should trigger at least one anomaly
    assert summary["total"] > 0
    # totals must be consistent
    severity_sum = sum(summary["by_severity"].values())
    assert severity_sum == summary["total"]


def test_empty_document_list_returns_valid_result():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    result = runner.analyze_jurisdiction("city_a", [])

    assert result["jurisdiction_id"] == "city_a"
    assert result["document_count"] == 0
    assert result["results"] == []
    assert result["anomaly_summary"]["total"] == 0
    assert all(v == 0 for v in result["anomaly_summary"]["by_severity"].values())


def test_analyze_jurisdiction_not_in_registry_raises():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    with pytest.raises(KeyError):
        runner.analyze_jurisdiction("does_not_exist", [_CLEAN_DOC])


# ---------------------------------------------------------------------------
# get_results / get_all_results
# ---------------------------------------------------------------------------


def test_get_results_returns_cached_result():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    runner.analyze_jurisdiction("city_a", [_CLEAN_DOC])

    cached = runner.get_results("city_a")
    assert cached is not None
    assert cached["jurisdiction_id"] == "city_a"


def test_get_results_returns_none_before_analysis():
    registry = _make_registry(("city_a", "City A"))
    runner = MultiJurisdictionRunner(registry)
    assert runner.get_results("city_a") is None


def test_get_all_results_returns_all_cached():
    registry = _make_registry(("city_a", "City A"), ("city_b", "City B"))
    runner = MultiJurisdictionRunner(registry)
    runner.analyze_jurisdiction("city_a", [_CLEAN_DOC])
    runner.analyze_jurisdiction("city_b", [_CLEAN_DOC])

    all_results = runner.get_all_results()
    assert set(all_results.keys()) == {"city_a", "city_b"}


# ---------------------------------------------------------------------------
# analyze_all
# ---------------------------------------------------------------------------


def test_analyze_all_two_jurisdictions():
    registry = _make_registry(("city_a", "City A"), ("city_b", "City B"))
    runner = MultiJurisdictionRunner(registry)
    result = runner.analyze_all(
        {
            "city_a": [_CLEAN_DOC],
            "city_b": [_FISCAL_DOC],
        }
    )

    assert result["jurisdictions_analyzed"] == 2
    assert result["total_documents"] == 2
    assert "per_jurisdiction" in result
    assert "city_a" in result["per_jurisdiction"]
    assert "city_b" in result["per_jurisdiction"]


def test_analyze_all_total_anomalies_sum():
    registry = _make_registry(("city_a", "City A"), ("city_b", "City B"))
    runner = MultiJurisdictionRunner(registry)
    result = runner.analyze_all(
        {
            "city_a": [_FISCAL_DOC],
            "city_b": [_FISCAL_DOC],
        }
    )

    # total_anomalies must equal the sum of each jurisdiction's totals
    expected = sum(
        v["anomaly_summary"]["total"] for v in result["per_jurisdiction"].values()
    )
    assert result["total_anomalies"] == expected


def test_analyze_all_caches_results():
    registry = _make_registry(("city_a", "City A"), ("city_b", "City B"))
    runner = MultiJurisdictionRunner(registry)
    runner.analyze_all(
        {
            "city_a": [_CLEAN_DOC],
            "city_b": [_CLEAN_DOC],
        }
    )

    assert runner.get_results("city_a") is not None
    assert runner.get_results("city_b") is not None
