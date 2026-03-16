"""Tests for CCOPSAdapter (Prompt 9.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from oraculus_di_auditor.adapters.ccops_adapter import CCOPSAdapter, CCOPSProfile

# ---------------------------------------------------------------------------
# Known ODIA analysis module names (verified against analysis/ directory)
# ---------------------------------------------------------------------------
_KNOWN_DETECTORS = {
    "administrative_integrity",
    "constitutional",
    "cross_reference",
    "fiscal",
    "governance_gap",
    "procurement_timeline",
    "signature_chain",
    "surveillance",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def adapter(tmp_path: Path) -> CCOPSAdapter:
    return CCOPSAdapter(cache_dir=tmp_path)


# ---------------------------------------------------------------------------
# Mandate enumeration
# ---------------------------------------------------------------------------


def test_get_all_mandates_returns_11(adapter):
    assert len(adapter.get_all_mandates()) == 11


def test_mandate_ids_are_m01_through_m11(adapter):
    ids = [m.mandate_id for m in adapter.get_all_mandates()]
    assert ids == [f"M-{i:02d}" for i in range(1, 12)]


def test_every_mandate_has_title(adapter):
    for m in adapter.get_all_mandates():
        assert m.title.strip() != "", f"{m.mandate_id} has no title"


def test_every_mandate_has_description(adapter):
    for m in adapter.get_all_mandates():
        assert m.description.strip() != "", f"{m.mandate_id} has no description"


def test_every_mandate_has_required_evidence(adapter):
    for m in adapter.get_all_mandates():
        assert len(m.required_evidence) >= 1, f"{m.mandate_id} has no required_evidence"


def test_every_mandate_has_at_least_one_detector(adapter):
    for m in adapter.get_all_mandates():
        assert (
            len(m.verification_detectors) >= 1
        ), f"{m.mandate_id} has no verification_detectors"


def test_all_severity_values_are_valid(adapter):
    valid = {"critical", "high", "medium"}
    for m in adapter.get_all_mandates():
        assert (
            m.severity_if_missing in valid
        ), f"{m.mandate_id} has invalid severity: {m.severity_if_missing}"


# ---------------------------------------------------------------------------
# get_mandate
# ---------------------------------------------------------------------------


def test_get_mandate_by_id_returns_correct(adapter):
    m = adapter.get_mandate("M-01")
    assert m is not None
    assert m.mandate_id == "M-01"
    assert "procurement_timeline" in m.verification_detectors


def test_get_mandate_m06_has_surveillance_detector(adapter):
    m = adapter.get_mandate("M-06")
    assert m is not None
    assert "surveillance" in m.verification_detectors


def test_get_mandate_invalid_id_returns_none(adapter):
    assert adapter.get_mandate("M-99") is None
    assert adapter.get_mandate("") is None


# ---------------------------------------------------------------------------
# fetch (with filtering)
# ---------------------------------------------------------------------------


def test_fetch_no_filter_returns_all_11(adapter):
    results = adapter.fetch({})
    assert len(results) == 11


def test_fetch_by_mandate_id(adapter):
    results = adapter.fetch({"mandate_id": "M-02"})
    assert len(results) == 1
    assert results[0]["mandate_id"] == "M-02"


def test_fetch_by_severity_critical(adapter):
    results = adapter.fetch({"severity": "critical"})
    assert len(results) == 3  # M-01, M-02, M-03
    assert all(r["severity_if_missing"] == "critical" for r in results)


def test_fetch_by_severity_high(adapter):
    results = adapter.fetch({"severity": "high"})
    assert all(r["severity_if_missing"] == "high" for r in results)
    assert len(results) >= 1


def test_fetch_by_severity_medium(adapter):
    results = adapter.fetch({"severity": "medium"})
    assert all(r["severity_if_missing"] == "medium" for r in results)


def test_fetch_combined_filter_id_and_severity(adapter):
    # M-01 is critical — should return 1
    results = adapter.fetch({"mandate_id": "M-01", "severity": "critical"})
    assert len(results) == 1

    # M-01 is not high — should return 0
    results = adapter.fetch({"mandate_id": "M-01", "severity": "high"})
    assert len(results) == 0


def test_fetch_returns_dicts(adapter):
    results = adapter.fetch({})
    for r in results:
        assert isinstance(r, dict)
        assert "mandate_id" in r
        assert "title" in r
        assert "verification_detectors" in r


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------


def test_get_profile_creates_valid_profile(adapter):
    profile = adapter.get_profile("test_city")
    assert isinstance(profile, CCOPSProfile)
    assert profile.jurisdiction == "test_city"
    assert len(profile.mandates) == 11


def test_get_profile_defaults(adapter):
    profile = adapter.get_profile("example_county")
    assert profile.has_ordinance is False
    assert profile.adoption_date is None
    assert profile.ordinance_url is None


def test_get_profile_with_ordinance(adapter):
    profile = adapter.get_profile(
        "oakland",
        has_ordinance=True,
        adoption_date="2018-05-07",
    )
    assert profile.has_ordinance is True
    assert profile.adoption_date == "2018-05-07"


# ---------------------------------------------------------------------------
# get_detectors_for_mandate
# ---------------------------------------------------------------------------


def test_get_detectors_for_m01(adapter):
    detectors = adapter.get_detectors_for_mandate("M-01")
    assert detectors == ["procurement_timeline"]


def test_get_detectors_for_m09(adapter):
    detectors = adapter.get_detectors_for_mandate("M-09")
    assert "signature_chain" in detectors
    assert "governance_gap" in detectors


def test_get_detectors_for_invalid_mandate(adapter):
    assert adapter.get_detectors_for_mandate("M-99") == []


# ---------------------------------------------------------------------------
# get_mandates_for_detector
# ---------------------------------------------------------------------------


def test_get_mandates_for_governance_gap(adapter):
    mandates = adapter.get_mandates_for_detector("governance_gap")
    ids = [m.mandate_id for m in mandates]
    assert "M-02" in ids
    assert "M-04" in ids
    assert "M-05" in ids
    assert "M-08" in ids


def test_get_mandates_for_fiscal(adapter):
    mandates = adapter.get_mandates_for_detector("fiscal")
    assert len(mandates) == 1
    assert mandates[0].mandate_id == "M-10"


def test_get_mandates_for_unknown_detector(adapter):
    assert adapter.get_mandates_for_detector("nonexistent_detector") == []


# ---------------------------------------------------------------------------
# Detector name integrity
# ---------------------------------------------------------------------------


def test_all_referenced_detectors_exist_in_odia(adapter):
    """All detector names referenced in CCOPS mandates are real ODIA detectors."""
    for m in adapter.get_all_mandates():
        for detector in m.verification_detectors:
            assert (
                detector in _KNOWN_DETECTORS
            ), f"{m.mandate_id} references unknown detector: {detector!r}"


# ---------------------------------------------------------------------------
# normalize passthrough
# ---------------------------------------------------------------------------


def test_normalize_is_passthrough(adapter):
    records = [{"id": "x"}, {"id": "y"}]
    assert adapter.normalize(records) == records
