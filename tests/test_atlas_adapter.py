"""Tests for AtlasAdapter (Prompt 9.3)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from oraculus_di_auditor.adapters.atlas_adapter import AtlasAdapter, AtlasRecord

# Path to the bundled sample dataset
SAMPLE_JSON = Path(__file__).parent.parent / "data" / "reference" / "atlas_sample.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_adapter(tmp_path: Path) -> AtlasAdapter:
    return AtlasAdapter(cache_dir=tmp_path)


@pytest.fixture()
def loaded_adapter(tmp_path: Path) -> AtlasAdapter:
    return AtlasAdapter(local_dataset_path=SAMPLE_JSON, cache_dir=tmp_path)


# ---------------------------------------------------------------------------
# Placeholder / empty mode
# ---------------------------------------------------------------------------


def test_empty_adapter_has_no_records(empty_adapter):
    assert empty_adapter.record_count() == 0


def test_empty_adapter_is_not_loaded(empty_adapter):
    assert empty_adapter.is_loaded() is False


def test_empty_adapter_fetch_returns_empty(empty_adapter):
    assert empty_adapter.fetch({}) == []


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------


def test_sample_json_loads_30_records(loaded_adapter):
    assert loaded_adapter.record_count() == 30


def test_loaded_adapter_is_loaded(loaded_adapter):
    assert loaded_adapter.is_loaded() is True


def test_loaded_records_are_atlas_records(loaded_adapter):
    results = loaded_adapter.fetch({})
    for r in results:
        assert isinstance(r, dict)
        assert "atlas_id" in r
        assert "agency_name" in r
        assert "state" in r
        assert "technology_type" in r


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------


def test_csv_loading(tmp_path: Path):
    csv_path = tmp_path / "atlas_test.csv"
    rows = [
        {
            "agency": "Test Agency",
            "state": "TX",
            "technology": "ALPR",
            "vendor": "SecureTech",
            "source": "",
            "year": "2021",
        },
        {
            "agency": "Other Agency",
            "state": "TX",
            "technology": "drones",
            "vendor": "",
            "source": "",
            "year": "",
        },
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["agency", "state", "technology", "vendor", "source", "year"]
        )
        writer.writeheader()
        writer.writerows(rows)

    adapter = AtlasAdapter(local_dataset_path=csv_path, cache_dir=tmp_path)
    assert adapter.record_count() == 2
    results = adapter.fetch({"state": "TX"})
    assert len(results) == 2


def test_csv_optional_fields_become_none(tmp_path: Path):
    csv_path = tmp_path / "atlas_sparse.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["agency", "state", "technology", "vendor", "source", "year"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "agency": "Sparse Agency",
                "state": "OR",
                "technology": "drones",
                "vendor": "",
                "source": "",
                "year": "",
            }
        )

    adapter = AtlasAdapter(local_dataset_path=csv_path, cache_dir=tmp_path)
    r = AtlasRecord(**adapter.fetch({})[0])
    assert r.vendor is None
    assert r.source_url is None
    assert r.year_identified is None


# ---------------------------------------------------------------------------
# fetch() filtering
# ---------------------------------------------------------------------------


def test_fetch_no_filter_returns_all(loaded_adapter):
    results = loaded_adapter.fetch({})
    assert len(results) == 30


def test_fetch_by_state(loaded_adapter):
    results = loaded_adapter.fetch({"state": "CA"})
    assert len(results) == 30
    assert all(r["state"] == "CA" for r in results)


def test_fetch_by_technology_alpr(loaded_adapter):
    results = loaded_adapter.fetch({"technology": "ALPR"})
    assert len(results) >= 5
    assert all("alpr" in r["technology_type"].lower() for r in results)


def test_fetch_by_vendor_securetech(loaded_adapter):
    results = loaded_adapter.fetch({"vendor": "SecureTech"})
    assert len(results) >= 5
    assert all(r["vendor"] == "SecureTech" for r in results)


def test_fetch_by_agency_partial_match(loaded_adapter):
    results = loaded_adapter.fetch({"agency": "Harborview"})
    assert len(results) >= 1
    assert all("harborview" in r["agency_name"].lower() for r in results)


def test_fetch_combined_agency_and_technology(loaded_adapter):
    results = loaded_adapter.fetch({"agency": "Harborview", "technology": "ALPR"})
    assert len(results) == 1
    assert results[0]["agency_name"] == "Harborview PD"
    assert results[0]["technology_type"] == "ALPR"


def test_fetch_nonexistent_agency_returns_empty(loaded_adapter):
    results = loaded_adapter.fetch({"agency": "Nonexistent Agency XYZ"})
    assert results == []


def test_fetch_by_state_case_insensitive(loaded_adapter):
    lower = loaded_adapter.fetch({"state": "ca"})
    upper = loaded_adapter.fetch({"state": "CA"})
    assert len(lower) == len(upper) == 30


# ---------------------------------------------------------------------------
# fetch_by_agency / fetch_by_technology / fetch_by_vendor
# ---------------------------------------------------------------------------


def test_fetch_by_agency_returns_atlas_records(loaded_adapter):
    records = loaded_adapter.fetch_by_agency("Riverside County Sheriff")
    assert len(records) == 4
    assert all(isinstance(r, AtlasRecord) for r in records)


def test_fetch_by_technology_drones(loaded_adapter):
    records = loaded_adapter.fetch_by_technology("drones")
    assert len(records) >= 3
    assert all("drone" in r.technology_type.lower() for r in records)


def test_fetch_by_vendor_visionguard(loaded_adapter):
    records = loaded_adapter.fetch_by_vendor("VisionGuard")
    assert len(records) >= 5
    assert all(r.vendor == "VisionGuard" for r in records)


def test_fetch_by_technology_with_state_filter(loaded_adapter):
    records = loaded_adapter.fetch_by_technology("predictive policing", state="CA")
    assert len(records) >= 1
    assert all(r.state == "CA" for r in records)


# ---------------------------------------------------------------------------
# Summary methods
# ---------------------------------------------------------------------------


def test_technology_summary_has_alpr(loaded_adapter):
    summary = loaded_adapter.get_technology_summary()
    assert "ALPR" in summary
    assert summary["ALPR"] >= 5


def test_technology_summary_total_equals_record_count(loaded_adapter):
    summary = loaded_adapter.get_technology_summary()
    assert sum(summary.values()) == loaded_adapter.record_count()


def test_vendor_summary_has_securetech(loaded_adapter):
    summary = loaded_adapter.get_vendor_summary()
    assert "SecureTech" in summary
    assert summary["SecureTech"] >= 5


def test_vendor_summary_has_unknown_for_null_vendor(loaded_adapter):
    summary = loaded_adapter.get_vendor_summary()
    assert "Unknown" in summary


def test_technology_summary_with_state_filter(loaded_adapter):
    summary = loaded_adapter.get_technology_summary(state="CA")
    assert sum(summary.values()) == 30


# ---------------------------------------------------------------------------
# normalize passthrough
# ---------------------------------------------------------------------------


def test_normalize_is_passthrough(loaded_adapter):
    records = [{"atlas_id": "x"}, {"atlas_id": "y"}]
    assert loaded_adapter.normalize(records) == records


# ---------------------------------------------------------------------------
# TECHNOLOGY_TYPES constant
# ---------------------------------------------------------------------------


def test_technology_types_list_has_12_entries():
    assert len(AtlasAdapter.TECHNOLOGY_TYPES) == 12


def test_alpr_in_technology_types():
    assert "ALPR" in AtlasAdapter.TECHNOLOGY_TYPES


def test_facial_recognition_in_technology_types():
    assert "facial recognition" in AtlasAdapter.TECHNOLOGY_TYPES
