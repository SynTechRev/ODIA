"""Integration tests for v2.7.1 C4 field-verification routes.

Covers:
  - POST create with/without exclusion_zone flag
  - verification_type enum validation (photo / pass_by / deflock_cross_ref)
  - lat/lng coordinate validation (must be numbers, must be in range)
  - GET list with filters (jurisdiction, type, exclusion_zone, pagination)
  - GET exclusion-zones shortcut returns only exclusion_zone=true rows
    sorted newest-first (MAS generator contract)
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "odia_field_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


def _observation(
    *,
    jurisdiction="woodlake",
    lat=36.4135,
    lng=-119.0982,
    verification_type="photo",
    exclusion_zone=False,
    notes=None,
    observed_at=None,
):
    payload = {
        "jurisdiction_id": jurisdiction,
        "lat": lat,
        "lng": lng,
        "verification_type": verification_type,
        "exclusion_zone": exclusion_zone,
    }
    if notes is not None:
        payload["notes"] = notes
    if observed_at is not None:
        payload["observed_at"] = observed_at
    return payload


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_photo_observation(client):
    resp = client.post(
        "/api/v1/field/flock-observation",
        json=_observation(notes="Flock camera mounted on light pole, corner of Valencia + Naranjo"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] > 0
    assert body["jurisdiction_id"] == "woodlake"
    assert body["verification_type"] == "photo"
    assert body["exclusion_zone"] is False
    assert abs(body["lat"] - 36.4135) < 1e-6
    assert abs(body["lng"] - -119.0982) < 1e-6


def test_create_exclusion_zone_flag_persists(client):
    resp = client.post(
        "/api/v1/field/flock-observation",
        json=_observation(
            jurisdiction="porterville",
            exclusion_zone=True,
            notes="Inside 500ft of elementary school perimeter — contract §4.2 forbids",
            verification_type="pass_by",
        ),
    )
    assert resp.status_code == 200
    assert resp.json()["exclusion_zone"] is True


def test_create_all_three_verification_types(client):
    for t in ("photo", "pass_by", "deflock_cross_ref"):
        resp = client.post(
            "/api/v1/field/flock-observation",
            json=_observation(verification_type=t),
        )
        assert resp.status_code == 200
        assert resp.json()["verification_type"] == t


def test_create_rejects_invalid_verification_type(client):
    resp = client.post(
        "/api/v1/field/flock-observation",
        json=_observation(verification_type="made_up_type"),
    )
    assert resp.status_code == 400
    assert "verification_type" in resp.text


def test_create_rejects_missing_jurisdiction(client):
    payload = _observation()
    del payload["jurisdiction_id"]
    resp = client.post("/api/v1/field/flock-observation", json=payload)
    assert resp.status_code == 400


def test_create_rejects_non_numeric_coords(client):
    resp = client.post(
        "/api/v1/field/flock-observation",
        json=_observation(lat="not-a-number"),
    )
    assert resp.status_code == 400


def test_create_rejects_out_of_range_lat(client):
    resp = client.post(
        "/api/v1/field/flock-observation",
        json=_observation(lat=91.0),
    )
    assert resp.status_code == 400


def test_create_rejects_out_of_range_lng(client):
    resp = client.post(
        "/api/v1/field/flock-observation",
        json=_observation(lng=-200.0),
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_filters_by_jurisdiction(client):
    client.post("/api/v1/field/flock-observation", json=_observation(jurisdiction="a"))
    client.post("/api/v1/field/flock-observation", json=_observation(jurisdiction="a"))
    client.post("/api/v1/field/flock-observation", json=_observation(jurisdiction="b"))

    resp = client.get(
        "/api/v1/field/observations", params={"jurisdiction_id": "a"}
    )
    body = resp.json()
    assert body["total"] == 2
    assert all(it["jurisdiction_id"] == "a" for it in body["items"])


def test_list_filters_by_verification_type(client):
    client.post(
        "/api/v1/field/flock-observation", json=_observation(verification_type="photo")
    )
    client.post(
        "/api/v1/field/flock-observation",
        json=_observation(verification_type="pass_by"),
    )
    client.post(
        "/api/v1/field/flock-observation",
        json=_observation(verification_type="deflock_cross_ref"),
    )

    resp = client.get(
        "/api/v1/field/observations",
        params={"verification_type": "deflock_cross_ref"},
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["verification_type"] == "deflock_cross_ref"


def test_list_filters_by_exclusion_zone(client):
    client.post(
        "/api/v1/field/flock-observation", json=_observation(exclusion_zone=False)
    )
    client.post(
        "/api/v1/field/flock-observation", json=_observation(exclusion_zone=True)
    )
    client.post(
        "/api/v1/field/flock-observation", json=_observation(exclusion_zone=True)
    )

    resp = client.get(
        "/api/v1/field/observations", params={"exclusion_zone": True}
    )
    assert resp.json()["total"] == 2


def test_list_pagination(client):
    for _ in range(7):
        client.post(
            "/api/v1/field/flock-observation", json=_observation()
        )
    resp = client.get(
        "/api/v1/field/observations", params={"limit": 3, "offset": 2}
    )
    body = resp.json()
    assert body["total"] == 7
    assert body["limit"] == 3
    assert body["offset"] == 2
    assert len(body["items"]) == 3


# ---------------------------------------------------------------------------
# Exclusion-zone shortcut (the MAS generator's input contract)
# ---------------------------------------------------------------------------


def test_exclusion_zones_returns_only_flagged_rows(client):
    now = datetime.now(UTC)
    for i in range(4):
        client.post(
            "/api/v1/field/flock-observation",
            json=_observation(
                exclusion_zone=(i % 2 == 0),
                observed_at=(now - timedelta(hours=i)).isoformat(),
            ),
        )

    resp = client.get("/api/v1/field/exclusion-zones")
    body = resp.json()
    assert body["count"] == 2
    assert all(it["exclusion_zone"] is True for it in body["items"])


def test_exclusion_zones_newest_first(client):
    now = datetime.now(UTC)
    # Seed in reverse-chronological order explicitly
    for hours_ago in (5, 2, 8, 1, 4):
        client.post(
            "/api/v1/field/flock-observation",
            json=_observation(
                exclusion_zone=True,
                observed_at=(now - timedelta(hours=hours_ago)).isoformat(),
                notes=f"{hours_ago}h ago",
            ),
        )

    resp = client.get("/api/v1/field/exclusion-zones")
    items = resp.json()["items"]
    observed = [it["observed_at"] for it in items]
    assert observed == sorted(observed, reverse=True)


def test_exclusion_zones_jurisdiction_filter(client):
    client.post(
        "/api/v1/field/flock-observation",
        json=_observation(jurisdiction="a", exclusion_zone=True),
    )
    client.post(
        "/api/v1/field/flock-observation",
        json=_observation(jurisdiction="b", exclusion_zone=True),
    )

    resp = client.get(
        "/api/v1/field/exclusion-zones", params={"jurisdiction_id": "a"}
    )
    body = resp.json()
    assert body["count"] == 1
    assert body["items"][0]["jurisdiction_id"] == "a"
