"""Tests for discover_jurisdictions() — v2.7.1 C2 multi-jurisdiction auto-loader.

Covers the three paths that matter at startup:
  1. Parent dir with N valid jurisdictions → dict of N configs.
  2. Parent dir missing entirely → empty dict (never raises).
  3. One malformed jurisdiction among valid ones → the malformed one
     is skipped; the rest load.

Tests seed jurisdiction directories under tmp_path so they don't
touch the real config/multi_jurisdiction/ tree.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oraculus_di_auditor.config.jurisdiction_loader import (
    JurisdictionConfig,
    discover_jurisdictions,
)


def _write_jurisdiction(dir_path: Path, name: str, state: str = "CA") -> None:
    """Create a minimal valid jurisdiction dir at dir_path."""
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "jurisdiction.json").write_text(
        json.dumps(
            {
                "name": name,
                "state": state,
                "country": "US",
                "meeting_type": "City Council Regular Meeting",
                "legistar_base_url": f"https://{name.lower().replace(' ', '-')}.legistar.com",
            }
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Happy path — three valid subdirs
# ---------------------------------------------------------------------------


def test_discover_three_jurisdictions(tmp_path):
    root = tmp_path / "multi_jurisdiction"
    _write_jurisdiction(root / "woodlake", "Woodlake")
    _write_jurisdiction(root / "farmersville", "Farmersville")
    _write_jurisdiction(root / "lindsay", "Lindsay")

    configs = discover_jurisdictions(root)

    assert len(configs) == 3
    assert set(configs.keys()) == {"woodlake", "farmersville", "lindsay"}
    assert all(isinstance(c, JurisdictionConfig) for c in configs.values())
    assert configs["woodlake"].name == "Woodlake"
    assert configs["farmersville"].state == "CA"


# ---------------------------------------------------------------------------
# Root missing — returns empty, does not raise
# ---------------------------------------------------------------------------


def test_discover_missing_root_returns_empty(tmp_path):
    # tmp_path/does_not_exist is guaranteed not to exist
    configs = discover_jurisdictions(tmp_path / "does_not_exist")
    assert configs == {}


def test_discover_empty_root_returns_empty(tmp_path):
    empty = tmp_path / "multi_jurisdiction"
    empty.mkdir()
    configs = discover_jurisdictions(empty)
    assert configs == {}


# ---------------------------------------------------------------------------
# Partial failure — malformed jurisdiction.json shouldn't block siblings
# ---------------------------------------------------------------------------


def test_discover_skips_malformed_jurisdiction(tmp_path, caplog):
    root = tmp_path / "multi_jurisdiction"
    _write_jurisdiction(root / "good_one", "Good One")

    # Malformed — valid file present but not valid JSON
    bad = root / "bad_one"
    bad.mkdir()
    (bad / "jurisdiction.json").write_text("{ not valid json }", encoding="utf-8")

    _write_jurisdiction(root / "good_two", "Good Two")

    with caplog.at_level("WARNING"):
        configs = discover_jurisdictions(root)

    assert set(configs.keys()) == {"good_one", "good_two"}
    # The bad one must have logged a warning (not crashed the whole scan)
    assert any("bad_one" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# Non-jurisdiction subdirs are ignored (not all subdirs are jurisdictions)
# ---------------------------------------------------------------------------


def test_discover_ignores_non_jurisdiction_subdirs(tmp_path):
    """A subdirectory without a jurisdiction.json (or .example) is NOT a
    jurisdiction — could be a README dir, a credentials cache, a
    per-jurisdiction exports folder. Must be silently skipped.
    """
    root = tmp_path / "multi_jurisdiction"
    _write_jurisdiction(root / "real", "Real City")

    # Noise subdir — has files, but no jurisdiction.json
    noise = root / "not_a_jurisdiction"
    noise.mkdir()
    (noise / "README.md").write_text("notes", encoding="utf-8")

    configs = discover_jurisdictions(root)
    assert set(configs.keys()) == {"real"}


# ---------------------------------------------------------------------------
# .example.json fallback still registers (fresh-clone compatibility)
# ---------------------------------------------------------------------------


def test_discover_uses_example_json_fallback(tmp_path):
    """On a fresh clone the example_city_a/b/c directories only ship
    .example.json files. The loader's existing fallback must register
    them so n8n workflow imports have something to bind against."""
    root = tmp_path / "multi_jurisdiction"
    dir_ = root / "example_fresh"
    dir_.mkdir(parents=True)
    (dir_ / "jurisdiction.example.json").write_text(
        json.dumps({"name": "Example Fresh", "state": "CA", "country": "US"}),
        encoding="utf-8",
    )

    configs = discover_jurisdictions(root)
    assert "example_fresh" in configs
    assert configs["example_fresh"].name == "Example Fresh"


# ---------------------------------------------------------------------------
# Real seed data — the existing example_city_a/b/c tree parses cleanly
# ---------------------------------------------------------------------------


def test_discover_real_seed_registers_three_examples():
    """Sanity check against the tree shipped in config/multi_jurisdiction/.
    Three example cities (a/b/c) must each round-trip through the discoverer.
    """
    repo_root = Path(__file__).resolve().parents[1]
    seed = repo_root / "config" / "multi_jurisdiction"
    if not seed.exists():
        pytest.skip("config/multi_jurisdiction seed not present")

    configs = discover_jurisdictions(seed)
    assert "example_city_a" in configs
    assert "example_city_b" in configs
    assert "example_city_c" in configs
