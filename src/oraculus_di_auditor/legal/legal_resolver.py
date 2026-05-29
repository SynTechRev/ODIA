"""LegalResolver — unified entry point for legal-corpus lookups.

Loads loaders registered in config/legal_corpora.yml at boot.
Routes citation lookups to the right loader based on citation
pattern matching.

Singleton — initialised once at backend startup, queried by the
plain_language renderer and any other component that needs to
embed legal text in output.
"""

from __future__ import annotations

import importlib
import logging
from datetime import date
from pathlib import Path

import yaml

from .corpus_base import CorpusLoader, LegalText

logger = logging.getLogger(__name__)


def _default_config_path() -> Path:
    """Locate config/legal_corpora.yml without depending on the CWD.

    uvicorn is frequently launched from a directory other than the repo
    root (it has crashed the resolver in practice). So: prefer the
    CWD-relative path when it exists (lets an operator override per run),
    otherwise fall back to the path derived from this file's location:
    src/oraculus_di_auditor/legal/legal_resolver.py -> parents[3] is the
    repo root.
    """
    cwd_relative = Path("config/legal_corpora.yml")
    if cwd_relative.exists():
        return cwd_relative
    return Path(__file__).resolve().parents[3] / "config" / "legal_corpora.yml"


class LegalResolver:
    def __init__(self, config_path: Path | str | None = None):
        self._config_path = (
            Path(config_path) if config_path else _default_config_path()
        )
        self._loaders: dict[str, CorpusLoader] = {}
        self._initialized = False

    def initialize(self) -> dict[str, dict[str, int]]:
        """Load all enabled corpora. Returns per-corpus stats dict."""
        if not self._config_path.exists():
            logger.warning(
                "legal_corpora.yml not found at %s; resolver disabled",
                self._config_path,
            )
            self._initialized = True  # initialised-but-empty is a valid state
            return {}

        try:
            with self._config_path.open(encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except Exception as exc:  # noqa: BLE001
            logger.warning("legal_corpora.yml parse failed: %s", exc)
            self._initialized = True
            return {}

        stats = {}
        for entry in config.get("corpora", []):
            if not entry.get("enabled", False):
                continue
            try:
                loader = self._instantiate_loader(entry)
                corpus_stats = loader.initialize()
                self._loaders[entry["id"]] = loader
                stats[entry["id"]] = corpus_stats
                logger.info("Loaded legal corpus %s: %s", entry["id"], corpus_stats)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to load corpus %s: %s; continuing without it",
                    entry.get("id", "?"),
                    exc,
                )
        self._initialized = True
        return stats

    def _instantiate_loader(self, entry: dict) -> CorpusLoader:
        """Import the loader class and instantiate with submodule_path.

        A relative submodule_path in the registry is anchored to the repo
        root (the config file's grandparent), not the CWD — same
        CWD-independence the config path itself gets.
        """
        loader_dotted = entry["loader"]
        module_name, class_name = loader_dotted.rsplit(".", 1)
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        submodule_path = Path(entry["submodule_path"])
        if not submodule_path.is_absolute():
            submodule_path = self._config_path.resolve().parent.parent / submodule_path
        return cls(submodule_path=submodule_path)

    def resolve(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        """Resolve a citation, trying each loader in order.

        Returns the first successful resolution or None.
        Future enhancement: route by citation pattern instead of
        try-each (matters when CFR/SCOTUS land alongside USC).
        """
        if not self._initialized:
            return None
        for loader in self._loaders.values():
            try:
                result = loader.resolve_citation(citation, as_of=as_of)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "loader %s raised on resolve(%r): %s",
                    loader.corpus_id,
                    citation,
                    exc,
                )
                continue
            if result is not None:
                return result
        return None

    def statistics(self) -> dict[str, dict[str, int]]:
        return {cid: ldr.statistics() for cid, ldr in self._loaders.items()}


# Module-level singleton — initialised at backend startup
_RESOLVER: LegalResolver | None = None


def get_resolver() -> LegalResolver:
    """Return the singleton resolver. Initialised on first call.

    Idempotent — repeated calls return the same instance.
    """
    global _RESOLVER
    if _RESOLVER is None:
        _RESOLVER = LegalResolver()
        _RESOLVER.initialize()
    return _RESOLVER


def reset_resolver_for_testing() -> None:
    """Drop the singleton. Tests use this to force re-init with a
    different config_path or to verify init-twice behaviour."""
    global _RESOLVER
    _RESOLVER = None
