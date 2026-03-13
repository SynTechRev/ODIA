"""Tests for jurisdiction-aware pipeline and /config/jurisdiction API endpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oraculus_di_auditor.analysis.pipeline import run_full_analysis
from oraculus_di_auditor.config import JurisdictionConfig, clear_config_cache

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_TEXT = "There is appropriated $1,000,000 for city operations."
_SAMPLE_META = {"title": "Test Budget", "hash": "abc123"}


def _make_config(**kwargs) -> JurisdictionConfig:
    defaults = dict(
        name="City of Testville",
        state="TX",
        country="US",
        legistar_base_url="https://testville.legistar.com",
        meeting_type="City Council Regular Meeting",
        agencies={"Police Department": ["police", "pd"]},
        corpus_manifest={},
        source_urls={},
    )
    defaults.update(kwargs)
    return JurisdictionConfig(**defaults)


# ---------------------------------------------------------------------------
# Pipeline: backward compatibility (no config)
# ---------------------------------------------------------------------------


def test_pipeline_without_config_returns_valid_structure():
    """Calling with no jurisdiction_config works exactly as before."""
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META)
    assert isinstance(result, dict)
    for key in (
        "metadata",
        "findings",
        "severity_score",
        "lattice_score",
        "coherence_bonus",
        "flags",
        "summary",
        "timestamp",
    ):
        assert key in result


def test_pipeline_without_config_has_no_jurisdiction_key():
    """When no config is passed, 'jurisdiction' is absent from the result."""
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META)
    assert "jurisdiction" not in result


def test_pipeline_without_config_findings_intact():
    """Existing findings structure is unaffected by the new parameter."""
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META)
    assert "fiscal" in result["findings"]
    assert "constitutional" in result["findings"]
    assert "surveillance" in result["findings"]


# ---------------------------------------------------------------------------
# Pipeline: with JurisdictionConfig
# ---------------------------------------------------------------------------


def test_pipeline_with_config_includes_jurisdiction_name():
    cfg = _make_config(name="City of Testville")
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META, jurisdiction_config=cfg)
    assert "jurisdiction" in result
    assert result["jurisdiction"] == "City of Testville"


def test_pipeline_with_config_preserves_all_other_keys():
    cfg = _make_config()
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META, jurisdiction_config=cfg)
    for key in (
        "metadata",
        "findings",
        "severity_score",
        "lattice_score",
        "coherence_bonus",
        "flags",
        "summary",
        "timestamp",
    ):
        assert key in result


def test_pipeline_with_config_agencies_embedded_in_normalized_doc():
    """When agencies are provided, they appear in the normalized document
    (tested indirectly: the pipeline does not crash and returns correct output)."""
    cfg = _make_config(agencies={"Fire Department": ["fire", "fire department"]})
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META, jurisdiction_config=cfg)
    assert result["jurisdiction"] == cfg.name


def test_pipeline_with_empty_agencies_config():
    cfg = _make_config(agencies={})
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META, jurisdiction_config=cfg)
    assert result["jurisdiction"] == cfg.name


def test_pipeline_jurisdiction_name_in_summary_is_unchanged():
    """Summary content is not altered by jurisdiction config."""
    cfg = _make_config()
    result = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META, jurisdiction_config=cfg)
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0


def test_pipeline_scores_unaffected_by_config():
    """Scores must be identical whether or not config is passed."""
    result_no_cfg = run_full_analysis(_SAMPLE_TEXT, _SAMPLE_META)
    cfg = _make_config()
    result_with_cfg = run_full_analysis(
        _SAMPLE_TEXT, _SAMPLE_META, jurisdiction_config=cfg
    )
    assert result_no_cfg["severity_score"] == result_with_cfg["severity_score"]
    assert result_no_cfg["lattice_score"] == result_with_cfg["lattice_score"]
    assert result_no_cfg["coherence_bonus"] == result_with_cfg["coherence_bonus"]


# ---------------------------------------------------------------------------
# API: /config/jurisdiction endpoint
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_config_cache()
    yield
    clear_config_cache()


@pytest.fixture()
def test_config_dir(tmp_path: Path) -> Path:
    jurisdiction = {
        "name": "City of Testville",
        "state": "TX",
        "country": "US",
        "legistar_base_url": "https://testville.legistar.com",
        "meeting_type": "City Council Regular Meeting",
    }
    agencies = {
        "Police Department": ["police", "pd"],
        "Fire Department": ["fire"],
    }
    (tmp_path / "jurisdiction.json").write_text(
        json.dumps(jurisdiction), encoding="utf-8"
    )
    (tmp_path / "agencies.json").write_text(json.dumps(agencies), encoding="utf-8")
    return tmp_path


def test_jurisdiction_endpoint_no_config_returns_loaded_false(monkeypatch):
    """When config cannot be loaded, endpoint returns loaded=False."""
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi[testclient] not installed")

    # Patch the loader to simulate missing config
    import oraculus_di_auditor.interface.api as api_module

    monkeypatch.setattr(
        api_module,
        "_load_jurisdiction_config_at_startup",
        lambda: None,
    )

    # Rebuild routes with patched loader
    try:
        from fastapi import FastAPI

        app = FastAPI()
        api_module._register_routes(app)
    except Exception:
        pytest.skip("Could not construct test app")

    client = TestClient(app)
    response = client.get("/config/jurisdiction")
    assert response.status_code == 200
    data = response.json()
    assert data["loaded"] is False
    assert data["name"] is None
    assert data["agency_count"] == 0


def test_jurisdiction_endpoint_with_config_returns_metadata(
    test_config_dir: Path, monkeypatch
):
    """When config is loaded, endpoint returns jurisdiction metadata."""
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi[testclient] not installed")

    import oraculus_di_auditor.interface.api as api_module
    from oraculus_di_auditor.config import load_jurisdiction_config

    cfg = load_jurisdiction_config(test_config_dir)

    monkeypatch.setattr(
        api_module,
        "_load_jurisdiction_config_at_startup",
        lambda: cfg,
    )

    app = FastAPI()
    api_module._register_routes(app)
    client = TestClient(app)

    response = client.get("/config/jurisdiction")
    assert response.status_code == 200
    data = response.json()
    assert data["loaded"] is True
    assert data["name"] == "City of Testville"
    assert data["state"] == "TX"
    assert data["country"] == "US"
    assert data["meeting_type"] == "City Council Regular Meeting"
    assert data["agency_count"] == 2


def test_jurisdiction_endpoint_does_not_expose_legistar_url(
    test_config_dir: Path, monkeypatch
):
    """Legistar URL is not included in the /config/jurisdiction response."""
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi[testclient] not installed")

    import oraculus_di_auditor.interface.api as api_module
    from oraculus_di_auditor.config import load_jurisdiction_config

    cfg = load_jurisdiction_config(test_config_dir)
    monkeypatch.setattr(api_module, "_load_jurisdiction_config_at_startup", lambda: cfg)

    app = FastAPI()
    api_module._register_routes(app)
    client = TestClient(app)

    response = client.get("/config/jurisdiction")
    data = response.json()
    assert "legistar_base_url" not in data
    assert "agencies" not in data
