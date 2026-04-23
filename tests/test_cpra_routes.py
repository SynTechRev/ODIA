"""Integration tests for the C3 CPRA deadline-watcher routes.

Cover the three flows n8n WF-005 actually exercises, plus the operator-
side create/list/update that the frontend will use.

Tests seed a fresh SQLite DB per-test via DATABASE_URL + init_db() so
CPRARequest rows don't leak across tests.
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Fresh app + fresh DB per test."""
    db_path = tmp_path / "odia_cpra_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


def _seed_request(client, *, jurisdiction, days_until_deadline, status="open"):
    """POST a CPRA request with deadline offset from now; return the body."""
    deadline = datetime.now(UTC) + timedelta(days=days_until_deadline)
    resp = client.post(
        "/api/v1/cpra/requests",
        json={
            "jurisdiction_id": jurisdiction,
            "statutory_deadline": deadline.isoformat(),
            "status": status,
            "description": f"{jurisdiction} — {days_until_deadline}d out",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# /deadlines-within/{window}
# ---------------------------------------------------------------------------


def test_deadlines_within_72h_filters_correctly(client):
    """2 requests within 48h, 1 at 5 days, 1 overdue → 72h window
    returns the two near-term ones only."""
    _seed_request(client, jurisdiction="woodlake", days_until_deadline=1)
    _seed_request(client, jurisdiction="lindsay", days_until_deadline=2)
    _seed_request(client, jurisdiction="porterville", days_until_deadline=5)
    # Overdue row — deadline already passed
    _seed_request(client, jurisdiction="farmersville", days_until_deadline=-1)

    resp = client.get("/api/v1/cpra/deadlines-within/72h")
    assert resp.status_code == 200
    body = resp.json()
    assert body["window"] == "72h"
    assert body["count"] == 2
    jids = {it["jurisdiction_id"] for it in body["items"]}
    assert jids == {"woodlake", "lindsay"}


def test_deadlines_within_7d_includes_mid_range(client):
    _seed_request(client, jurisdiction="a", days_until_deadline=1)
    _seed_request(client, jurisdiction="b", days_until_deadline=5)
    _seed_request(client, jurisdiction="c", days_until_deadline=10)

    resp = client.get("/api/v1/cpra/deadlines-within/7d")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    jids = {it["jurisdiction_id"] for it in body["items"]}
    assert jids == {"a", "b"}


def test_deadlines_within_30d_returns_all_future(client):
    _seed_request(client, jurisdiction="a", days_until_deadline=1)
    _seed_request(client, jurisdiction="b", days_until_deadline=20)
    _seed_request(client, jurisdiction="c", days_until_deadline=29)
    _seed_request(client, jurisdiction="d", days_until_deadline=31)

    resp = client.get("/api/v1/cpra/deadlines-within/30d")
    assert resp.status_code == 200
    assert resp.json()["count"] == 3


def test_deadlines_within_filters_by_jurisdiction(client):
    _seed_request(client, jurisdiction="woodlake", days_until_deadline=2)
    _seed_request(client, jurisdiction="lindsay", days_until_deadline=2)

    resp = client.get(
        "/api/v1/cpra/deadlines-within/7d",
        params={"jurisdiction_id": "woodlake"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["items"][0]["jurisdiction_id"] == "woodlake"


def test_deadlines_within_skips_responded_withdrawn(client):
    """Responded / withdrawn / already-overdue rows must NOT appear in
    the watcher output — those are handled by other workflows."""
    _seed_request(client, jurisdiction="a", days_until_deadline=1)
    _seed_request(client, jurisdiction="b", days_until_deadline=1, status="responded")
    _seed_request(client, jurisdiction="c", days_until_deadline=1, status="withdrawn")
    _seed_request(client, jurisdiction="d", days_until_deadline=1, status="extended")

    resp = client.get("/api/v1/cpra/deadlines-within/72h")
    body = resp.json()
    jids = {it["jurisdiction_id"] for it in body["items"]}
    # `extended` is still watchable (14-day § 7922.535(b) extension); the
    # other two non-open statuses drop out.
    assert jids == {"a", "d"}


def test_deadlines_within_rejects_invalid_window(client):
    resp = client.get("/api/v1/cpra/deadlines-within/99d")
    assert resp.status_code == 400
    assert "invalid window" in resp.text


# ---------------------------------------------------------------------------
# CRUD — list / patch
# ---------------------------------------------------------------------------


def test_list_requests_pagination(client):
    for i in range(5):
        _seed_request(client, jurisdiction=f"city_{i}", days_until_deadline=i + 1)

    resp = client.get("/api/v1/cpra/requests", params={"limit": 2, "offset": 1})
    body = resp.json()
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2


def test_patch_extends_deadline(client):
    row = _seed_request(client, jurisdiction="a", days_until_deadline=5)
    new_deadline = (datetime.now(UTC) + timedelta(days=19)).isoformat()
    resp = client.patch(
        f"/api/v1/cpra/requests/{row['id']}",
        json={"status": "extended", "statutory_deadline": new_deadline},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "extended"
    # DB stores tz-naive; compare prefix.
    assert new_deadline.startswith(body["statutory_deadline"][:10])


def test_patch_404_on_missing_id(client):
    resp = client.patch("/api/v1/cpra/requests/99999", json={"status": "responded"})
    assert resp.status_code == 404


def test_create_rejects_missing_fields(client):
    resp = client.post("/api/v1/cpra/requests", json={})
    assert resp.status_code == 400


def test_create_rejects_malformed_deadline(client):
    resp = client.post(
        "/api/v1/cpra/requests",
        json={"jurisdiction_id": "x", "statutory_deadline": "not-a-date"},
    )
    assert resp.status_code == 400
