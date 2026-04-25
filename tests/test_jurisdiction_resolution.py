"""Tests for the v2.7.6 X2 frozen-aware jurisdiction discovery + Seed
endpoint.

The desktop installer needs jurisdictions to be discoverable from
*somewhere* on a fresh install where ``$ODIA_JURISDICTIONS_DIR`` is
unset, the user-writable seed dir is empty, and the only jurisdictions
available are inside the read-only PyInstaller bundle. These tests
pin the resolution chain and the Seed endpoint's idempotent behavior.
"""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402


# ---------------------------------------------------------------------------
# default_multi_jurisdiction_root() resolution chain
# ---------------------------------------------------------------------------


def test_env_override_wins_over_user_dir(monkeypatch, tmp_path):
    """``$ODIA_JURISDICTIONS_DIR`` must trump every other resolution
    branch — used by tests + CI to point at a sandboxed dir."""
    override = tmp_path / "override"
    override.mkdir()
    monkeypatch.setenv("ODIA_JURISDICTIONS_DIR", str(override))

    from oraculus_di_auditor.config.jurisdiction_loader import (
        default_multi_jurisdiction_root,
    )

    assert default_multi_jurisdiction_root() == override


def test_user_dir_wins_when_env_unset(monkeypatch, tmp_path):
    """With no env override, an existing user-writable seed dir
    out-ranks the bundled / repo / CWD fallbacks."""
    monkeypatch.delenv("ODIA_JURISDICTIONS_DIR", raising=False)

    user_root = tmp_path / "userdata" / "config" / "multi_jurisdiction"
    user_root.mkdir(parents=True)

    from oraculus_di_auditor.config import jurisdiction_loader

    monkeypatch.setattr(
        jurisdiction_loader,
        "user_multi_jurisdiction_root",
        lambda: user_root,
    )

    assert jurisdiction_loader.default_multi_jurisdiction_root() == user_root


def test_discover_jurisdictions_loads_bundled_examples(monkeypatch, tmp_path):
    """When the env override points at a directory full of jurisdiction
    subdirs, ``discover_jurisdictions(None)`` must return them."""
    monkeypatch.delenv("ODIA_JURISDICTIONS_DIR", raising=False)

    root = tmp_path / "jurisdictions"
    root.mkdir()
    for name in ("alpha", "beta"):
        sub = root / name
        sub.mkdir()
        (sub / "jurisdiction.json").write_text(
            f'{{"name": "{name.title()} City", "state": "CA"}}',
            encoding="utf-8",
        )

    monkeypatch.setenv("ODIA_JURISDICTIONS_DIR", str(root))

    from oraculus_di_auditor.config.jurisdiction_loader import (
        discover_jurisdictions,
    )

    found = discover_jurisdictions()
    assert set(found.keys()) == {"alpha", "beta"}
    assert found["alpha"].name == "Alpha City"


def test_discover_jurisdictions_explicit_root_overrides_default(tmp_path):
    """Passing an explicit root_dir bypasses the resolution chain
    entirely — useful when callers know exactly where to look."""
    root = tmp_path / "explicit"
    root.mkdir()
    (root / "gamma").mkdir()
    (root / "gamma" / "jurisdiction.json").write_text(
        '{"name": "Gamma City"}', encoding="utf-8"
    )

    from oraculus_di_auditor.config.jurisdiction_loader import (
        discover_jurisdictions,
    )

    found = discover_jurisdictions(root)
    assert list(found.keys()) == ["gamma"]


# ---------------------------------------------------------------------------
# /api/v1/dashboard/seed-jurisdictions
# ---------------------------------------------------------------------------


@pytest.fixture
def seed_client(monkeypatch, tmp_path):
    """Spin up create_app() with both the bundled root and the user
    root pointed at sandboxed temp dirs."""
    db_path = tmp_path / "seed.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    for name in ("example_city_a", "example_city_b"):
        sub = bundle / name
        sub.mkdir()
        (sub / "jurisdiction.json").write_text(
            f'{{"name": "{name}", "state": "CA"}}', encoding="utf-8"
        )

    user = tmp_path / "userdata" / "config" / "multi_jurisdiction"

    from oraculus_di_auditor.config import jurisdiction_loader

    monkeypatch.setattr(
        jurisdiction_loader,
        "bundled_multi_jurisdiction_root",
        lambda: bundle,
    )
    monkeypatch.setattr(
        jurisdiction_loader,
        "user_multi_jurisdiction_root",
        lambda: user,
    )

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app), bundle, user


def test_seed_copies_bundled_examples(seed_client):
    """First call must copy every subdir from the bundle into the
    user-writable target."""
    client, _bundle, user = seed_client
    resp = client.post("/api/v1/dashboard/seed-jurisdictions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert sorted(body["copied"]) == ["example_city_a", "example_city_b"]
    assert body["skipped"] == []
    assert (user / "example_city_a" / "jurisdiction.json").exists()
    assert (user / "example_city_b" / "jurisdiction.json").exists()


def test_seed_is_idempotent(seed_client):
    """Second call must skip subdirs that already exist (default
    force=False), so re-clicking the button is safe."""
    client, _bundle, _user = seed_client
    client.post("/api/v1/dashboard/seed-jurisdictions")
    resp = client.post("/api/v1/dashboard/seed-jurisdictions")
    body = resp.json()
    assert body["copied"] == []
    assert sorted(body["skipped"]) == ["example_city_a", "example_city_b"]


def test_seed_force_overwrites(seed_client):
    """``force=True`` must overwrite existing copies (the 'reset to
    defaults' code path — not surfaced in the UI button but exposed
    on the endpoint for power users)."""
    client, _bundle, user = seed_client
    client.post("/api/v1/dashboard/seed-jurisdictions")

    # Mutate one of the copied files to detect overwrite.
    target_file = user / "example_city_a" / "jurisdiction.json"
    target_file.write_text('{"name": "MUTATED"}', encoding="utf-8")

    resp = client.post(
        "/api/v1/dashboard/seed-jurisdictions",
        params={"force": True},
    )
    body = resp.json()
    assert sorted(body["copied"]) == ["example_city_a", "example_city_b"]
    # Mutation must be gone — the file is back to bundle contents.
    assert "MUTATED" not in target_file.read_text(encoding="utf-8")
