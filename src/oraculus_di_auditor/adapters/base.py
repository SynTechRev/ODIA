"""Base adapter class for all external data source adapters.

Defines the abstract interface and shared caching infrastructure for CAIP
(Configurable Adapter Ingestion Pipeline) — Layer 1.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class DataSourceAdapter(ABC):
    """Base class for all external data source adapters."""

    def __init__(self, name: str, cache_dir: Path | str = "cache/adapters"):
        self.name = name
        self.cache_dir = Path(cache_dir) / name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def fetch(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Fetch records matching query parameters."""

    @abstractmethod
    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Transform source-specific records into ODIA's internal format."""

    def cache_key(self, query: dict[str, Any]) -> str:
        """Generate deterministic cache key from query."""
        serialized = json.dumps(query, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def fetch_cached(
        self, query: dict[str, Any], max_age_hours: int = 24
    ) -> list[dict[str, Any]] | None:
        """Return cached results if fresh enough, else None."""
        key = self.cache_key(query)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data["cached_at"])
            age_hours = (datetime.now(UTC) - cached_at).total_seconds() / 3600
            if age_hours < max_age_hours:
                return data["records"]
        return None

    def save_cache(self, query: dict[str, Any], records: list[dict[str, Any]]) -> None:
        """Save results to cache."""
        key = self.cache_key(query)
        cache_file = self.cache_dir / f"{key}.json"
        data = {
            "cached_at": datetime.now(UTC).isoformat(),
            "query": query,
            "record_count": len(records),
            "records": records,
        }
        cache_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def fetch_with_cache(
        self, query: dict[str, Any], max_age_hours: int = 24
    ) -> list[dict[str, Any]]:
        """Fetch with automatic caching."""
        cached = self.fetch_cached(query, max_age_hours)
        if cached is not None:
            return cached
        records = self.fetch(query)
        self.save_cache(query, records)
        return records

    def get_cache_stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        return {
            "adapter": self.name,
            "cached_queries": len(cache_files),
            "cache_dir": str(self.cache_dir),
        }
