"""Jurisdiction configuration loader.

Reads jurisdiction.json, agencies.json, corpus_manifest.json, and
source_urls.json from a config directory and exposes them as a single
JurisdictionConfig dataclass.  Falls back to *.example.json files when the
primary files are absent so the project works out-of-the-box on a fresh clone.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

_COMMENT_KEYS = {"_comment", "_format"}


def _strip_comments(data: dict[str, Any]) -> dict[str, Any]:
    """Remove JSON comment-convention keys (underscore-prefixed metadata)."""
    return {k: v for k, v in data.items() if k not in _COMMENT_KEYS}


@dataclass
class JurisdictionConfig:
    """Unified jurisdiction configuration."""

    name: str = "Unknown Jurisdiction"
    state: str = ""
    country: str = ""
    legistar_base_url: str = ""
    meeting_type: str = ""
    agencies: dict[str, list[str]] = field(default_factory=dict)
    corpus_manifest: dict[str, str] = field(default_factory=dict)
    source_urls: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------


def _resolve_config_dir(config_dir: Path | str) -> Path:
    """Resolve and validate the config directory path."""
    path = Path(config_dir)
    if not path.exists():
        raise FileNotFoundError(f"Config directory not found: {path.resolve()}")
    if not path.is_dir():
        raise NotADirectoryError(f"Config path is not a directory: {path.resolve()}")
    return path


def _load_json_with_fallback(
    config_dir: Path,
    stem: str,
    *,
    required: bool = False,
) -> dict[str, Any]:
    """Load <stem>.json, falling back to <stem>.example.json.

    Args:
        config_dir: Directory to search.
        stem: Filename without extension (e.g. "jurisdiction").
        required: If True, raise FileNotFoundError when neither file exists.

    Returns:
        Parsed JSON dict, stripped of comment keys.  Empty dict when not
        found and *required* is False.
    """
    primary = config_dir / f"{stem}.json"
    fallback = config_dir / f"{stem}.example.json"

    for candidate in (primary, fallback):
        if candidate.exists():
            with open(candidate, encoding="utf-8") as fh:
                raw = json.load(fh)
            return _strip_comments(raw)

    if required:
        raise FileNotFoundError(
            f"Required config file not found: {primary} " f"(also tried {fallback})"
        )
    return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_jurisdiction_config(
    config_dir: Path | str = "config",
) -> JurisdictionConfig:
    """Load and return a JurisdictionConfig from *config_dir*.

    Files loaded (primary, then .example.json fallback):
      - jurisdiction.json   — required; provides name, state, country, URLs
      - agencies.json       — optional
      - corpus_manifest.json — optional
      - source_urls.json    — optional

    Args:
        config_dir: Path to the directory containing config files.
                    Defaults to ``"config"`` (relative to CWD).

    Returns:
        Populated :class:`JurisdictionConfig`.

    Raises:
        FileNotFoundError: If *config_dir* does not exist or jurisdiction
                           config cannot be found.
        NotADirectoryError: If *config_dir* is not a directory.
    """
    resolved = _resolve_config_dir(config_dir)

    jurisdiction = _load_json_with_fallback(resolved, "jurisdiction", required=True)
    agencies = _load_json_with_fallback(resolved, "agencies")
    corpus_manifest = _load_json_with_fallback(resolved, "corpus_manifest")
    source_urls = _load_json_with_fallback(resolved, "source_urls")

    return JurisdictionConfig(
        name=jurisdiction.get("name", "Unknown Jurisdiction"),
        state=jurisdiction.get("state", ""),
        country=jurisdiction.get("country", ""),
        legistar_base_url=jurisdiction.get("legistar_base_url", ""),
        meeting_type=jurisdiction.get("meeting_type", ""),
        agencies={k: v for k, v in agencies.items() if isinstance(v, list)},
        corpus_manifest={
            k: v for k, v in corpus_manifest.items() if isinstance(v, str)
        },
        source_urls={k: v for k, v in source_urls.items() if isinstance(v, str)},
    )


# ---------------------------------------------------------------------------
# Singleton cache
# ---------------------------------------------------------------------------

_cache_lock = threading.Lock()
_cached_config: JurisdictionConfig | None = None
_cached_config_dir: str | None = None


def get_config(config_dir: Path | str = "config") -> JurisdictionConfig:
    """Return a cached :class:`JurisdictionConfig`, loading it on first call.

    The cache is keyed on the resolved absolute path of *config_dir*.
    Calling with a different directory invalidates the cache.

    Args:
        config_dir: Passed through to :func:`load_jurisdiction_config`.

    Returns:
        Cached (or freshly loaded) :class:`JurisdictionConfig`.
    """
    global _cached_config, _cached_config_dir

    resolved_str = str(Path(config_dir).resolve())

    with _cache_lock:
        if _cached_config is None or _cached_config_dir != resolved_str:
            _cached_config = load_jurisdiction_config(config_dir)
            _cached_config_dir = resolved_str

    return _cached_config


def clear_config_cache() -> None:
    """Invalidate the singleton cache.  Primarily useful in tests."""
    global _cached_config, _cached_config_dir

    with _cache_lock:
        _cached_config = None
        _cached_config_dir = None
