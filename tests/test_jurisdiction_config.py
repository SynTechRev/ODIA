"""Tests for the jurisdiction configuration loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oraculus_di_auditor.config import (
    JurisdictionConfig,
    clear_config_cache,
    get_config,
    load_jurisdiction_config,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_cache():
    """Clear the singleton cache before and after every test."""
    clear_config_cache()
    yield
    clear_config_cache()


@pytest.fixture()
def config_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A temp directory populated with all four config files."""
    tmp_path = tmp_path_factory.mktemp("config_dir")
    jurisdiction = {
        "name": "City of Testville",
        "state": "TX",
        "country": "US",
        "legistar_base_url": "https://testville.legistar.com",
        "meeting_type": "City Council Regular Meeting",
    }
    agencies = {
        "_comment": "ignored",
        "Police Department": ["police", "pd"],
        "Fire Department": ["fire", "fire department"],
    }
    corpus_manifest = {
        "_comment": "ignored",
        "TV-001": "2024-01-15",
        "TV-002": "2024-02-20",
    }
    source_urls = {
        "_comment": "ignored",
        "TV-001": "https://testville.legistar.com/Detail.aspx?ID=1",
        "TV-002": "https://testville.legistar.com/Detail.aspx?ID=2",
    }

    (tmp_path / "jurisdiction.json").write_text(
        json.dumps(jurisdiction), encoding="utf-8"
    )
    (tmp_path / "agencies.json").write_text(json.dumps(agencies), encoding="utf-8")
    (tmp_path / "corpus_manifest.json").write_text(
        json.dumps(corpus_manifest), encoding="utf-8"
    )
    (tmp_path / "source_urls.json").write_text(
        json.dumps(source_urls), encoding="utf-8"
    )
    return tmp_path


@pytest.fixture()
def example_only_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A temp directory with only .example.json files (no primary files)."""
    tmp_path = tmp_path_factory.mktemp("example_only_dir")
    jurisdiction = {
        "name": "Example City",
        "state": "CA",
        "country": "US",
        "legistar_base_url": "https://example.legistar.com",
        "meeting_type": "City Council Regular Meeting",
    }
    agencies = {"City Council": ["council"]}
    corpus_manifest = {"EX-001": "2024-03-01"}
    source_urls = {"EX-001": "https://example.legistar.com/Detail.aspx?ID=1"}

    (tmp_path / "jurisdiction.example.json").write_text(
        json.dumps(jurisdiction), encoding="utf-8"
    )
    (tmp_path / "agencies.example.json").write_text(
        json.dumps(agencies), encoding="utf-8"
    )
    (tmp_path / "corpus_manifest.example.json").write_text(
        json.dumps(corpus_manifest), encoding="utf-8"
    )
    (tmp_path / "source_urls.example.json").write_text(
        json.dumps(source_urls), encoding="utf-8"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Load from primary files
# ---------------------------------------------------------------------------


def test_loads_jurisdiction_fields(config_dir: Path):
    cfg = load_jurisdiction_config(config_dir)
    assert cfg.name == "City of Testville"
    assert cfg.state == "TX"
    assert cfg.country == "US"
    assert cfg.legistar_base_url == "https://testville.legistar.com"
    assert cfg.meeting_type == "City Council Regular Meeting"


def test_loads_agencies(config_dir: Path):
    cfg = load_jurisdiction_config(config_dir)
    assert "Police Department" in cfg.agencies
    assert "pd" in cfg.agencies["Police Department"]


def test_loads_corpus_manifest(config_dir: Path):
    cfg = load_jurisdiction_config(config_dir)
    assert cfg.corpus_manifest["TV-001"] == "2024-01-15"
    assert cfg.corpus_manifest["TV-002"] == "2024-02-20"


def test_loads_source_urls(config_dir: Path):
    cfg = load_jurisdiction_config(config_dir)
    assert "TV-001" in cfg.source_urls
    assert cfg.source_urls["TV-001"].startswith("https://")


def test_comment_keys_stripped(config_dir: Path):
    cfg = load_jurisdiction_config(config_dir)
    assert "_comment" not in cfg.agencies
    assert "_comment" not in cfg.corpus_manifest
    assert "_comment" not in cfg.source_urls


# ---------------------------------------------------------------------------
# Fallback to .example.json
# ---------------------------------------------------------------------------


def test_loads_from_example_files(example_only_dir: Path):
    """When no primary files exist, .example.json files are used."""
    cfg = load_jurisdiction_config(example_only_dir)
    assert cfg.name == "Example City"
    assert cfg.state == "CA"
    assert "EX-001" in cfg.corpus_manifest


def test_primary_takes_precedence_over_example(tmp_path: Path):
    """Primary file is preferred when both exist."""
    primary = {"name": "Primary City", "state": "NY", "country": "US"}
    example = {"name": "Example City", "state": "CA", "country": "US"}
    (tmp_path / "jurisdiction.json").write_text(json.dumps(primary), encoding="utf-8")
    (tmp_path / "jurisdiction.example.json").write_text(
        json.dumps(example), encoding="utf-8"
    )
    cfg = load_jurisdiction_config(tmp_path)
    assert cfg.name == "Primary City"
    assert cfg.state == "NY"


# ---------------------------------------------------------------------------
# Partial config (some files missing)
# ---------------------------------------------------------------------------


def test_missing_optional_files_use_empty_defaults(tmp_path: Path):
    """agencies, corpus_manifest, source_urls are optional — omitting them
    yields empty dicts."""
    (tmp_path / "jurisdiction.json").write_text(
        json.dumps({"name": "Minimal City", "state": "OR", "country": "US"}),
        encoding="utf-8",
    )
    cfg = load_jurisdiction_config(tmp_path)
    assert cfg.name == "Minimal City"
    assert cfg.agencies == {}
    assert cfg.corpus_manifest == {}
    assert cfg.source_urls == {}


def test_missing_legistar_url_defaults_to_empty_string(tmp_path: Path):
    (tmp_path / "jurisdiction.json").write_text(
        json.dumps({"name": "No URL City", "state": "WA", "country": "US"}),
        encoding="utf-8",
    )
    cfg = load_jurisdiction_config(tmp_path)
    assert cfg.legistar_base_url == ""


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_missing_config_dir_raises_file_not_found():
    with pytest.raises(FileNotFoundError, match="not found"):
        load_jurisdiction_config("/nonexistent/path/to/config")


def test_config_path_is_file_raises_not_a_directory(tmp_path: Path):
    file_path = tmp_path / "notadir.json"
    file_path.write_text("{}", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        load_jurisdiction_config(file_path)


def test_missing_jurisdiction_file_raises_file_not_found(tmp_path: Path):
    """No jurisdiction.json and no jurisdiction.example.json → error."""
    # Only write optional files; jurisdiction file is absent entirely
    (tmp_path / "agencies.json").write_text(
        json.dumps({"City Council": ["council"]}), encoding="utf-8"
    )
    with pytest.raises(FileNotFoundError, match="jurisdiction"):
        load_jurisdiction_config(tmp_path)


# ---------------------------------------------------------------------------
# get_config singleton
# ---------------------------------------------------------------------------


def test_get_config_returns_jurisdiction_config(config_dir: Path):
    cfg = get_config(config_dir)
    assert isinstance(cfg, JurisdictionConfig)
    assert cfg.name == "City of Testville"


def test_get_config_caches_result(config_dir: Path):
    cfg1 = get_config(config_dir)
    cfg2 = get_config(config_dir)
    assert cfg1 is cfg2


def test_get_config_different_dir_invalidates_cache(
    config_dir: Path, example_only_dir: Path
):
    cfg1 = get_config(config_dir)
    cfg2 = get_config(example_only_dir)
    assert cfg1 is not cfg2
    assert cfg1.name != cfg2.name


def test_clear_cache_forces_reload(config_dir: Path):
    cfg1 = get_config(config_dir)
    clear_config_cache()
    cfg2 = get_config(config_dir)
    # After clearing, a new object is returned
    assert cfg1 is not cfg2
    assert cfg1.name == cfg2.name  # but with same values


# ---------------------------------------------------------------------------
# Custom config dir (accepts str or Path)
# ---------------------------------------------------------------------------


def test_accepts_string_path(config_dir: Path):
    cfg = load_jurisdiction_config(str(config_dir))
    assert cfg.name == "City of Testville"


def test_accepts_path_object(config_dir: Path):
    cfg = load_jurisdiction_config(config_dir)
    assert isinstance(cfg, JurisdictionConfig)


# ---------------------------------------------------------------------------
# Config values are accessible via dataclass attributes
# ---------------------------------------------------------------------------


def test_config_is_dataclass_instance(config_dir: Path):
    cfg = load_jurisdiction_config(config_dir)
    assert isinstance(cfg, JurisdictionConfig)
    # All expected fields are present
    for attr in (
        "name",
        "state",
        "country",
        "legistar_base_url",
        "meeting_type",
        "agencies",
        "corpus_manifest",
        "source_urls",
    ):
        assert hasattr(cfg, attr)


def test_loads_from_real_example_config():
    """Smoke test: loads successfully from the project's own config/ dir."""
    cfg = load_jurisdiction_config("config")
    assert isinstance(cfg, JurisdictionConfig)
    assert cfg.name  # non-empty name from example file
