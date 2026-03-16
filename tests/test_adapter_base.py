"""Tests for DataSourceAdapter base class (Prompt 9.1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from oraculus_di_auditor.adapters.base import DataSourceAdapter

# ---------------------------------------------------------------------------
# Minimal concrete adapter for testing
# ---------------------------------------------------------------------------


class _StubAdapter(DataSourceAdapter):
    """Minimal adapter that returns fixed records."""

    def __init__(self, cache_dir: Path, records: list[dict] | None = None):
        super().__init__("stub", cache_dir=cache_dir)
        self._records = records or [{"id": "1", "value": "a"}]
        self.fetch_call_count = 0

    def fetch(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        self.fetch_call_count += 1
        return list(self._records)

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return raw_records


# ---------------------------------------------------------------------------
# cache_key
# ---------------------------------------------------------------------------


def test_cache_key_is_deterministic(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "contract", "year": 2023}
    assert adapter.cache_key(query) == adapter.cache_key(query)


def test_cache_key_differs_for_different_queries(tmp_path):
    adapter = _StubAdapter(tmp_path)
    assert adapter.cache_key({"a": 1}) != adapter.cache_key({"a": 2})


def test_cache_key_is_16_chars(tmp_path):
    adapter = _StubAdapter(tmp_path)
    key = adapter.cache_key({"x": "y"})
    assert len(key) == 16


def test_cache_key_order_independent(tmp_path):
    adapter = _StubAdapter(tmp_path)
    assert adapter.cache_key({"a": 1, "b": 2}) == adapter.cache_key({"b": 2, "a": 1})


# ---------------------------------------------------------------------------
# save_cache / fetch_cached round-trip
# ---------------------------------------------------------------------------


def test_save_and_fetch_cached_round_trip(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "resolution"}
    records = [{"id": "r1", "text": "Approved budget"}]

    adapter.save_cache(query, records)
    result = adapter.fetch_cached(query)

    assert result == records


def test_fetch_cached_returns_none_when_no_cache(tmp_path):
    adapter = _StubAdapter(tmp_path)
    assert adapter.fetch_cached({"type": "missing"}) is None


def test_fetch_cached_returns_none_when_expired(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "old"}
    records = [{"id": "x"}]

    # Write cache with timestamp 48 hours in the past
    key = adapter.cache_key(query)
    cache_file = adapter.cache_dir / f"{key}.json"
    stale_time = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
    data = {
        "cached_at": stale_time,
        "query": query,
        "record_count": len(records),
        "records": records,
    }
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    assert adapter.fetch_cached(query, max_age_hours=24) is None


def test_fetch_cached_respects_max_age_hours(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "recent"}
    records = [{"id": "y"}]

    # Write cache 2 hours old
    key = adapter.cache_key(query)
    cache_file = adapter.cache_dir / f"{key}.json"
    recent_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    data = {
        "cached_at": recent_time,
        "query": query,
        "record_count": len(records),
        "records": records,
    }
    cache_file.write_text(json.dumps(data), encoding="utf-8")

    # max_age_hours=1 → expired
    assert adapter.fetch_cached(query, max_age_hours=1) is None
    # max_age_hours=3 → fresh
    assert adapter.fetch_cached(query, max_age_hours=3) == records


def test_save_cache_writes_metadata(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "meta"}
    records = [{"id": "m1"}, {"id": "m2"}]

    adapter.save_cache(query, records)

    key = adapter.cache_key(query)
    cache_file = adapter.cache_dir / f"{key}.json"
    data = json.loads(cache_file.read_text(encoding="utf-8"))

    assert data["record_count"] == 2
    assert data["query"] == query
    assert "cached_at" in data


# ---------------------------------------------------------------------------
# fetch_with_cache
# ---------------------------------------------------------------------------


def test_fetch_with_cache_calls_fetch_on_miss(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "fresh"}

    result = adapter.fetch_with_cache(query)

    assert adapter.fetch_call_count == 1
    assert result == adapter._records


def test_fetch_with_cache_returns_cache_on_hit(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "cached"}
    records = [{"id": "c1"}]
    adapter.save_cache(query, records)

    result = adapter.fetch_with_cache(query)

    assert adapter.fetch_call_count == 0
    assert result == records


def test_fetch_with_cache_saves_after_fetch(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "save_check"}

    adapter.fetch_with_cache(query)

    # Second call should hit cache, not fetch again
    adapter.fetch_with_cache(query)
    assert adapter.fetch_call_count == 1


def test_fetch_with_cache_refetches_on_expiry(tmp_path):
    adapter = _StubAdapter(tmp_path)
    query = {"type": "refetch"}

    # Plant stale cache
    key = adapter.cache_key(query)
    cache_file = adapter.cache_dir / f"{key}.json"
    stale = {
        "cached_at": (datetime.now(UTC) - timedelta(hours=48)).isoformat(),
        "query": query,
        "record_count": 0,
        "records": [],
    }
    cache_file.write_text(json.dumps(stale), encoding="utf-8")

    result = adapter.fetch_with_cache(query, max_age_hours=24)

    assert adapter.fetch_call_count == 1
    assert result == adapter._records


# ---------------------------------------------------------------------------
# get_cache_stats
# ---------------------------------------------------------------------------


def test_get_cache_stats_empty(tmp_path):
    adapter = _StubAdapter(tmp_path)
    stats = adapter.get_cache_stats()

    assert stats["adapter"] == "stub"
    assert stats["cached_queries"] == 0
    assert "cache_dir" in stats


def test_get_cache_stats_counts_files(tmp_path):
    adapter = _StubAdapter(tmp_path)

    adapter.save_cache({"q": 1}, [{"id": "a"}])
    adapter.save_cache({"q": 2}, [{"id": "b"}])

    stats = adapter.get_cache_stats()
    assert stats["cached_queries"] == 2


def test_get_cache_stats_adapter_name(tmp_path):
    adapter = _StubAdapter(tmp_path)
    assert adapter.get_cache_stats()["adapter"] == "stub"


# ---------------------------------------------------------------------------
# Adapter initialization
# ---------------------------------------------------------------------------


def test_adapter_creates_cache_dir(tmp_path):
    cache_root = tmp_path / "my_cache"
    adapter = _StubAdapter(cache_root)
    assert adapter.cache_dir.exists()
    assert adapter.cache_dir.is_dir()


def test_adapter_name_stored(tmp_path):
    adapter = _StubAdapter(tmp_path)
    assert adapter.name == "stub"


def test_abstract_methods_enforced():
    with pytest.raises(TypeError):
        DataSourceAdapter("test")  # type: ignore[abstract]
