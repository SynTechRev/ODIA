"""Tests for JurisdictionRegistry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oraculus_di_auditor.config.jurisdiction_loader import JurisdictionConfig
from oraculus_di_auditor.multi_jurisdiction import JurisdictionRegistry


def _make_config(**kwargs) -> JurisdictionConfig:
    defaults = {"name": "Test City", "state": "CA", "country": "US"}
    defaults.update(kwargs)
    return JurisdictionConfig(**defaults)


# ---------------------------------------------------------------------------
# Basic register / get / list / count
# ---------------------------------------------------------------------------


def test_register_and_retrieve():
    registry = JurisdictionRegistry()
    cfg = _make_config(name="City A")
    registry.register("city_a", cfg)
    assert registry.get("city_a") is cfg


def test_list_jurisdictions():
    registry = JurisdictionRegistry()
    registry.register("city_a", _make_config(name="City A"))
    registry.register("city_b", _make_config(name="City B"))
    ids = registry.list_jurisdictions()
    assert set(ids) == {"city_a", "city_b"}


def test_count():
    registry = JurisdictionRegistry()
    assert registry.count() == 0
    registry.register("city_a", _make_config())
    assert registry.count() == 1
    registry.register("city_b", _make_config())
    assert registry.count() == 2


def test_empty_registry():
    registry = JurisdictionRegistry()
    assert registry.count() == 0
    assert registry.list_jurisdictions() == []
    summary = registry.summary()
    assert summary["count"] == 0
    assert summary["jurisdictions"] == {}


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


def test_remove_jurisdiction():
    registry = JurisdictionRegistry()
    registry.register("city_a", _make_config(name="City A"))
    registry.register("city_b", _make_config(name="City B"))
    registry.remove("city_a")
    assert registry.count() == 1
    assert "city_a" not in registry.list_jurisdictions()
    assert "city_b" in registry.list_jurisdictions()


def test_remove_nonexistent_raises():
    registry = JurisdictionRegistry()
    with pytest.raises(KeyError):
        registry.remove("nonexistent")


# ---------------------------------------------------------------------------
# get errors
# ---------------------------------------------------------------------------


def test_get_nonexistent_raises_key_error():
    registry = JurisdictionRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")


# ---------------------------------------------------------------------------
# register duplicate overwrites
# ---------------------------------------------------------------------------


def test_register_duplicate_overwrites():
    registry = JurisdictionRegistry()
    cfg_v1 = _make_config(name="City V1")
    cfg_v2 = _make_config(name="City V2")
    registry.register("city_x", cfg_v1)
    registry.register("city_x", cfg_v2)
    assert registry.count() == 1
    assert registry.get("city_x").name == "City V2"


# ---------------------------------------------------------------------------
# from_directory
# ---------------------------------------------------------------------------


def test_from_directory_loads_multiple(tmp_path: Path):
    for city, name, state in [
        ("city_a", "City A", "CA"),
        ("city_b", "City B", "TX"),
    ]:
        d = tmp_path / city
        d.mkdir()
        (d / "jurisdiction.json").write_text(
            json.dumps({"name": name, "state": state, "country": "US"}),
            encoding="utf-8",
        )

    registry = JurisdictionRegistry.from_directory(tmp_path)
    assert registry.count() == 2
    assert set(registry.list_jurisdictions()) == {"city_a", "city_b"}
    assert registry.get("city_a").name == "City A"
    assert registry.get("city_b").name == "City B"
    assert registry.get("city_b").state == "TX"


def test_from_directory_skips_non_jurisdiction_subdirs(tmp_path: Path):
    # subdirectory without jurisdiction.json — should be skipped
    (tmp_path / "not_a_jurisdiction").mkdir()

    valid = tmp_path / "city_a"
    valid.mkdir()
    (valid / "jurisdiction.json").write_text(
        json.dumps({"name": "City A", "state": "CA", "country": "US"}),
        encoding="utf-8",
    )

    registry = JurisdictionRegistry.from_directory(tmp_path)
    assert registry.count() == 1
    assert "city_a" in registry.list_jurisdictions()


def test_from_directory_falls_back_to_example_json(tmp_path: Path):
    d = tmp_path / "city_example"
    d.mkdir()
    (d / "jurisdiction.example.json").write_text(
        json.dumps({"name": "Example City", "state": "NY", "country": "US"}),
        encoding="utf-8",
    )

    registry = JurisdictionRegistry.from_directory(tmp_path)
    assert registry.count() == 1
    assert registry.get("city_example").name == "Example City"


def test_from_directory_not_found_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        JurisdictionRegistry.from_directory(tmp_path / "does_not_exist")


def test_from_directory_not_a_directory_raises(tmp_path: Path):
    f = tmp_path / "notadir.json"
    f.write_text("{}", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        JurisdictionRegistry.from_directory(f)


def test_from_directory_loads_sample_config():
    """Smoke test: load the committed sample multi-jurisdiction configs."""
    sample_dir = Path("config/multi_jurisdiction")
    if not sample_dir.exists():
        pytest.skip("config/multi_jurisdiction not present")
    registry = JurisdictionRegistry.from_directory(sample_dir)
    assert registry.count() >= 2
    ids = registry.list_jurisdictions()
    assert "example_city_a" in ids
    assert "example_city_b" in ids


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------


def test_summary_returns_correct_data():
    registry = JurisdictionRegistry()
    cfg = JurisdictionConfig(
        name="Summary City",
        state="OR",
        country="US",
        agencies={"Police": ["pd"], "Fire": ["fd"]},
        corpus_manifest={"DOC-001": "2024-01-01"},
    )
    registry.register("summary_city", cfg)
    summary = registry.summary()

    assert summary["count"] == 1
    entry = summary["jurisdictions"]["summary_city"]
    assert entry["name"] == "Summary City"
    assert entry["state"] == "OR"
    assert entry["agency_count"] == 2
    assert entry["corpus_entry_count"] == 1
