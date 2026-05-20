"""Tests for /api/v1/legal/status endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from oraculus_di_auditor.legal import legal_resolver as _resolver_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _reset():
    _resolver_mod.reset_resolver_for_testing()
    yield
    _resolver_mod.reset_resolver_for_testing()


@pytest.fixture
def client():
    from oraculus_di_auditor.interface.api import create_app

    return TestClient(create_app())


def test_legal_status_reports_us_code(client):
    """Without the USC submodule the endpoint should still return 200
    (the resolver is initialised-but-empty). With it, us-code stats
    appear in the corpora dict."""
    r = client.get("/api/v1/legal/status")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert "corpora" in body
    # If the submodule is initialized, us-code will be present.
    submodule_present = Path("data/legal_corpora/us-code/uscode").exists()
    if submodule_present:
        assert "us-code" in body["corpora"], body
        assert body["corpora"]["us-code"]["sections_indexed"] > 5000
    # If not, corpora is just empty (no enabled corpus successfully loaded)
    # but the endpoint itself doesn't fail.
