"""Multi-jurisdiction registry.

Manages multiple JurisdictionConfig instances simultaneously so ODIA can
analyze and compare documents across jurisdictions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from oraculus_di_auditor.config.jurisdiction_loader import (
    JurisdictionConfig,
    load_jurisdiction_config,
)


class JurisdictionRegistry:
    """Manages multiple jurisdiction configurations for cross-jurisdiction analysis."""

    def __init__(self) -> None:
        self._jurisdictions: dict[str, JurisdictionConfig] = {}

    def register(self, jurisdiction_id: str, config: JurisdictionConfig) -> None:
        """Add a jurisdiction to the registry."""
        self._jurisdictions[jurisdiction_id] = config

    def get(self, jurisdiction_id: str) -> JurisdictionConfig:
        """Get a jurisdiction by ID. Raises KeyError if not found."""
        if jurisdiction_id not in self._jurisdictions:
            raise KeyError(f"Jurisdiction not found: {jurisdiction_id!r}")
        return self._jurisdictions[jurisdiction_id]

    def list_jurisdictions(self) -> list[str]:
        """Return all registered jurisdiction IDs."""
        return list(self._jurisdictions.keys())

    def count(self) -> int:
        """Number of registered jurisdictions."""
        return len(self._jurisdictions)

    def remove(self, jurisdiction_id: str) -> None:
        """Remove a jurisdiction from the registry."""
        if jurisdiction_id not in self._jurisdictions:
            raise KeyError(f"Jurisdiction not found: {jurisdiction_id!r}")
        del self._jurisdictions[jurisdiction_id]

    @classmethod
    def from_directory(cls, multi_config_dir: Path | str) -> JurisdictionRegistry:
        """Load all jurisdictions from a directory structure.

        Expected structure::

            multi_config_dir/
              jurisdiction_a/
                jurisdiction.json
                agencies.json          (optional)
                corpus_manifest.json   (optional)
                source_urls.json       (optional)
              jurisdiction_b/
                jurisdiction.json
                ...

        Each subdirectory is treated as a separate jurisdiction.
        The subdirectory name becomes the jurisdiction_id.

        Raises:
            FileNotFoundError: If *multi_config_dir* does not exist.
            NotADirectoryError: If *multi_config_dir* is not a directory.
        """
        root = Path(multi_config_dir)
        if not root.exists():
            raise FileNotFoundError(
                f"Multi-jurisdiction config directory not found: {root.resolve()}"
            )
        if not root.is_dir():
            raise NotADirectoryError(
                f"Multi-jurisdiction config path is not a directory: {root.resolve()}"
            )

        registry = cls()
        for subdir in sorted(root.iterdir()):
            if not subdir.is_dir():
                continue
            # Only load subdirectories that contain at least jurisdiction.json
            # or jurisdiction.example.json (load_jurisdiction_config handles fallback).
            primary = subdir / "jurisdiction.json"
            fallback = subdir / "jurisdiction.example.json"
            if not primary.exists() and not fallback.exists():
                continue
            config = load_jurisdiction_config(subdir)
            registry.register(subdir.name, config)

        return registry

    def summary(self) -> dict[str, Any]:
        """Return a summary of all registered jurisdictions."""
        return {
            "count": self.count(),
            "jurisdictions": {
                jid: {
                    "name": cfg.name,
                    "state": cfg.state,
                    "country": cfg.country,
                    "meeting_type": cfg.meeting_type,
                    "agency_count": len(cfg.agencies),
                    "corpus_entry_count": len(cfg.corpus_manifest),
                }
                for jid, cfg in self._jurisdictions.items()
            },
        }
