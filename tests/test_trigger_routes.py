"""Tests for /api/v1/triggers/* (v2.7.4 W1).

The Automation page's Manual Triggers panel now hits these
ODIA-native endpoints instead of proxying to n8n. Locks down:

  1. CPRA deadline trigger (re-export of the existing CPRA route)
     returns the right shape for empty + populated DBs.
  2. RAIA synthesize-all responds with no_jurisdictions when
     config/multi_jurisdiction/ is empty, and runs end-to-end when
     at least one jurisdiction is registered.
  3. Provenance Chain Export returns 501 with a helpful detail —
     the UI uses the message verbatim in the warn banner.
"""

from __future__ import annotations

import importlib
import json
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "triggers.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# /api/v1/triggers/cpra-deadlines/{window}
# ---------------------------------------------------------------------------


def test_cpra_deadlines_rejects_invalid_window(client):
    resp = client.get("/api/v1/triggers/cpra-deadlines/99h")
    assert resp.status_code == 400
    assert "invalid window" in resp.text


def test_cpra_deadlines_empty_db_returns_zero(client):
    resp = client.get("/api/v1/triggers/cpra-deadlines/72h")
    assert resp.status_code == 200
    body = resp.json()
    assert body["window"] == "72h"
    assert body["count"] == 0
    assert body["items"] == []


def test_cpra_deadlines_72h_finds_seeded_request(client):
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    deadline = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=24)
    with get_db() as session:
        session.add(
            db_models.CPRARequest(
                jurisdiction_id="woodlake",
                statutory_deadline=deadline,
                status="open",
                description="test deadline",
            )
        )

    resp = client.get("/api/v1/triggers/cpra-deadlines/72h")
    body = resp.json()
    assert body["count"] == 1
    assert body["items"][0]["jurisdiction_id"] == "woodlake"
    assert body["items"][0]["status"] == "open"


# ---------------------------------------------------------------------------
# /api/v1/triggers/raia-synthesize-all
# ---------------------------------------------------------------------------


def test_raia_synthesize_all_no_jurisdictions(client, tmp_path, monkeypatch):
    """With an empty config/multi_jurisdiction/ root, the trigger
    returns ``no_jurisdictions`` rather than 4xx — the UI surfaces
    this as a warn-level banner."""
    empty_root = tmp_path / "no_juris"
    empty_root.mkdir()

    # Patch discover_jurisdictions to look at the empty root.
    from oraculus_di_auditor.config import jurisdiction_loader

    original = jurisdiction_loader.discover_jurisdictions
    monkeypatch.setattr(
        jurisdiction_loader,
        "discover_jurisdictions",
        lambda root_dir=str(empty_root): original(root_dir=empty_root),
    )

    resp = client.post("/api/v1/triggers/raia-synthesize-all")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "no_jurisdictions"
    assert body["result"] is None


def test_raia_synthesize_all_with_jurisdictions(
    client, tmp_path, monkeypatch
):
    """When a jurisdiction directory exists, the trigger runs
    RAIAService end-to-end and returns the result + markdown.

    The triggers route imports ``discover_jurisdictions`` lazily inside
    the handler, so we patch the loader module's attribute directly —
    the handler's ``from … import discover_jurisdictions`` resolves to
    the stub at call time.
    """
    juris_root = tmp_path / "multi_juris"
    juris_dir = juris_root / "woodlake"
    juris_dir.mkdir(parents=True)
    (juris_dir / "jurisdiction.json").write_text(
        json.dumps(
            {
                "name": "Woodlake",
                "state": "CA",
                "country": "US",
                "meeting_type": "City Council",
            }
        ),
        encoding="utf-8",
    )

    from oraculus_di_auditor.config import jurisdiction_loader

    # Capture the real implementation before monkeypatching.
    real_discover = jurisdiction_loader.discover_jurisdictions

    # Stub matches the real signature (root_dir kwarg with default) so
    # both no-arg calls (the handler does this) and kwarg calls work.
    def _stub_discover(root_dir=None):
        return real_discover(root_dir=juris_root)

    monkeypatch.setattr(
        jurisdiction_loader, "discover_jurisdictions", _stub_discover
    )

    resp = client.post("/api/v1/triggers/raia-synthesize-all")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "woodlake" in body["jurisdictions"]
    assert body["result"]["synthesis_id"]
    assert body["markdown"]
    assert "R.A.I.A." in body["markdown"]


# ---------------------------------------------------------------------------
# /api/v1/triggers/provenance-chain-export
# ---------------------------------------------------------------------------


def test_provenance_chain_export_returns_501_with_help(client):
    resp = client.post("/api/v1/triggers/provenance-chain-export")
    assert resp.status_code == 501
    body = resp.json()
    assert "n8n" in body["detail"].lower()
    assert "docker compose" in body["detail"].lower()
