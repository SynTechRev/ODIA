"""Atlas of Surveillance adapter.

Adapter for EFF's Atlas of Surveillance data. Supports both local dataset
loading (from downloaded JSON or CSV) and placeholder mode when no dataset
is available.

Reference: https://atlasofsurveillance.org
For bulk data access, contact EFF or download available datasets directly
from the Atlas of Surveillance project.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from oraculus_di_auditor.adapters.base import DataSourceAdapter


class AtlasRecord(BaseModel):
    """A single Atlas of Surveillance data point."""

    atlas_id: str
    agency_name: str
    state: str
    technology_type: str
    vendor: str | None = None
    source_url: str | None = None
    year_identified: int | None = None
    notes: str | None = None


class AtlasAdapter(DataSourceAdapter):
    """Adapter for EFF Atlas of Surveillance data.

    Supports two modes:
    1. Local dataset: Load from a downloaded JSON/CSV file.
    2. Placeholder mode: Return empty results with instructions
       for obtaining the dataset.

    The Atlas data is crowdsourced and publicly viewable at
    atlasofsurveillance.org. For bulk data access, users should
    contact EFF or download available datasets.
    """

    TECHNOLOGY_TYPES = [
        "ALPR",
        "body-worn cameras",
        "drones",
        "facial recognition",
        "cell-site simulators",
        "gunshot detection",
        "video surveillance",
        "social media monitoring",
        "predictive policing",
        "real-time crime center",
        "ring/neighbors",
        "fusion center",
    ]

    def __init__(
        self,
        local_dataset_path: Path | str | None = None,
        cache_dir: Path | str = "cache/adapters",
    ):
        super().__init__("atlas", cache_dir)
        self._records: list[AtlasRecord] = []
        if local_dataset_path:
            self._load_local_dataset(Path(local_dataset_path))

    def _load_local_dataset(self, path: Path) -> None:
        """Load Atlas data from local JSON or CSV file."""
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            self._records = [AtlasRecord(**r) for r in data]
        elif path.suffix == ".csv":
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._records.append(
                        AtlasRecord(
                            atlas_id=self.cache_key(dict(row)),
                            agency_name=row.get("agency", ""),
                            state=row.get("state", ""),
                            technology_type=row.get("technology", ""),
                            vendor=row.get("vendor") or None,
                            source_url=row.get("source") or None,
                            year_identified=(
                                int(row["year"]) if row.get("year") else None
                            ),
                        )
                    )

    def fetch(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Query the loaded Atlas dataset.

        Supported query keys: agency, state, technology, vendor.
        All string comparisons are case-insensitive substring matches
        except state, which is an exact match (case-insensitive).
        """
        results = list(self._records)
        if "agency" in query:
            q = query["agency"].lower()
            results = [r for r in results if q in r.agency_name.lower()]
        if "state" in query:
            results = [r for r in results if r.state.upper() == query["state"].upper()]
        if "technology" in query:
            q = query["technology"].lower()
            results = [r for r in results if q in r.technology_type.lower()]
        if "vendor" in query:
            q = query["vendor"].lower()
            results = [r for r in results if r.vendor and q in r.vendor.lower()]
        return [r.model_dump() for r in results]

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Already normalized — pass through."""
        return raw_records

    def fetch_by_agency(
        self, agency_name: str, state: str | None = None
    ) -> list[AtlasRecord]:
        """Get all surveillance technologies for an agency."""
        query: dict[str, Any] = {"agency": agency_name}
        if state:
            query["state"] = state
        return [AtlasRecord(**r) for r in self.fetch(query)]

    def fetch_by_technology(
        self, tech_type: str, state: str | None = None
    ) -> list[AtlasRecord]:
        """Get all agencies using a specific technology."""
        query: dict[str, Any] = {"technology": tech_type}
        if state:
            query["state"] = state
        return [AtlasRecord(**r) for r in self.fetch(query)]

    def fetch_by_vendor(self, vendor_name: str) -> list[AtlasRecord]:
        """Get all deployments by a specific vendor."""
        return [AtlasRecord(**r) for r in self.fetch({"vendor": vendor_name})]

    def get_technology_summary(self, state: str | None = None) -> dict[str, int]:
        """Count of deployments by technology type."""
        records = self._records
        if state:
            records = [r for r in records if r.state.upper() == state.upper()]
        summary: dict[str, int] = {}
        for r in records:
            summary[r.technology_type] = summary.get(r.technology_type, 0) + 1
        return summary

    def get_vendor_summary(self, state: str | None = None) -> dict[str, int]:
        """Count of deployments by vendor."""
        records = self._records
        if state:
            records = [r for r in records if r.state.upper() == state.upper()]
        summary: dict[str, int] = {}
        for r in records:
            vendor = r.vendor or "Unknown"
            summary[vendor] = summary.get(vendor, 0) + 1
        return summary

    def record_count(self) -> int:
        """Total records loaded."""
        return len(self._records)

    def is_loaded(self) -> bool:
        """Whether any data has been loaded."""
        return len(self._records) > 0
