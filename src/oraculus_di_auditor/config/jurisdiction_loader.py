"""Jurisdiction configuration loader.

Reads jurisdiction.json, agencies.json, corpus_manifest.json, and
source_urls.json from a config directory and exposes them as a single
JurisdictionConfig dataclass.  Falls back to *.example.json files when the
primary files are absent so the project works out-of-the-box on a fresh clone.

v2.7.1 — `discover_jurisdictions()` scans a parent directory (typically
`config/multi_jurisdiction/`) for subdirectories each containing a
jurisdiction.json, and returns all configs in one dict. This is what the
n8n workflow bundle's per-jurisdiction WF-001 duplicates bind against:
each activation picks a jurisdiction_id that maps to a known entry here.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# v2.7.1 — Multi-jurisdiction auto-loader
# v2.7.6 X2 — frozen-aware path resolution for desktop installs
# ---------------------------------------------------------------------------


def _user_data_root() -> Path:
    """Cross-platform per-user writable data dir for ODIA.

    Avoids a hard dependency on appdirs/platformdirs by replicating the
    standard XDG / Win32 / macOS conventions inline:

        Windows:  %APPDATA%\\ODIA
        macOS:    ~/Library/Application Support/ODIA
        Linux:    $XDG_DATA_HOME/odia  or  ~/.local/share/odia

    The directory is NOT created here — callers that need to write
    invoke ``mkdir(parents=True, exist_ok=True)`` themselves.
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "ODIA"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ODIA"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "odia"
    return Path.home() / ".local" / "share" / "odia"


def user_multi_jurisdiction_root() -> Path:
    """Per-user writable jurisdictions directory.

    This is where the Seed button (``POST /api/v1/dashboard/seed-
    jurisdictions``) copies the bundled examples on first run. Users
    can also drop hand-edited jurisdiction subdirectories here without
    touching the read-only bundle.
    """
    return _user_data_root() / "config" / "multi_jurisdiction"


def bundled_multi_jurisdiction_root() -> Path | None:
    """Read-only seed dir bundled with the desktop installer.

    Returns the in-bundle path under PyInstaller (``sys._MEIPASS``),
    or the repo path during dev. Returns ``None`` when neither exists
    (e.g. a wheel install with no bundled examples).
    """
    # Frozen path — PyInstaller sets sys._MEIPASS to the extracted
    # bundle root. The spec file's `datas` entry copies `config/` →
    # `config/`, so the multi_jurisdiction dir lives at <meipass>/
    # config/multi_jurisdiction.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled = Path(meipass) / "config" / "multi_jurisdiction"
        if bundled.exists():
            return bundled

    # Repo-dev path — this file lives at
    # src/oraculus_di_auditor/config/jurisdiction_loader.py, so the
    # repo root is parents[3].
    repo_root_candidate = Path(__file__).resolve().parents[3]
    repo_dir = repo_root_candidate / "config" / "multi_jurisdiction"
    if repo_dir.exists():
        return repo_dir

    return None


def default_multi_jurisdiction_root() -> Path:
    """Resolution chain used when ``discover_jurisdictions()`` is called
    without an explicit ``root_dir``.

    Priority (first match wins):
        1. ``$ODIA_JURISDICTIONS_DIR`` environment override
        2. User-writable seed dir (set up by the Seed button)
        3. PyInstaller bundle (read-only seed)
        4. Repo dev directory
        5. CWD ``config/multi_jurisdiction`` (legacy fallback)

    The returned path is NOT guaranteed to exist; the caller must
    handle ``Path.exists()`` returning False (which yields an empty
    registry, not an exception).
    """
    env_override = os.environ.get("ODIA_JURISDICTIONS_DIR")
    if env_override:
        return Path(env_override)

    user_root = user_multi_jurisdiction_root()
    if user_root.exists():
        return user_root

    bundled = bundled_multi_jurisdiction_root()
    if bundled is not None:
        return bundled

    return Path("config/multi_jurisdiction")


def discover_jurisdictions(
    root_dir: Path | str | None = None,
) -> dict[str, JurisdictionConfig]:
    """Scan *root_dir* for per-jurisdiction subdirectories and load them all.

    Each subdirectory must contain a ``jurisdiction.json`` (or the
    ``.example.json`` fallback) to be registered. Other config files
    (agencies.json, corpus_manifest.json, source_urls.json) are picked up
    per the existing `load_jurisdiction_config` rules.

    Args:
        root_dir: Parent directory that holds per-jurisdiction subdirs.
                  When ``None`` (the default), resolves via
                  :func:`default_multi_jurisdiction_root` — which checks
                  ``$ODIA_JURISDICTIONS_DIR`` → user-writable seed dir
                  → PyInstaller bundle → repo dev dir → CWD fallback.
                  Pass an explicit Path to bypass the resolution chain.

    Returns:
        Mapping of ``subdirectory_name → JurisdictionConfig``. The
        subdirectory name is the stable jurisdiction_id — n8n workflows
        reference it verbatim as `jurisdictionId` in their Code nodes.
        Returns an empty dict when *root_dir* is missing or contains no
        loadable jurisdictions (never raises for that case — startup
        should proceed even on a fresh clone).

    Error semantics:
        A subdirectory that fails to load (missing jurisdiction.json,
        malformed JSON, etc.) is logged at WARNING and skipped. One bad
        jurisdiction must not block the other 21 from registering in a
        production deployment.
    """
    out: dict[str, JurisdictionConfig] = {}
    if root_dir is None:
        root_dir = default_multi_jurisdiction_root()
    root = Path(root_dir)
    if not root.exists() or not root.is_dir():
        logger.info(
            "discover_jurisdictions: %s does not exist; returning empty registry",
            root.resolve(),
        )
        return out

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        # The existing loader requires jurisdiction.json (or .example); skip
        # subdirs that don't have one at all — they're not jurisdiction
        # directories (could be a README dir, a credentials cache, etc.).
        has_jurisdiction = (child / "jurisdiction.json").exists() or (
            child / "jurisdiction.example.json"
        ).exists()
        if not has_jurisdiction:
            continue
        try:
            config = load_jurisdiction_config(child)
        except Exception as exc:  # noqa: BLE001 — log + skip, never propagate
            logger.warning(
                "discover_jurisdictions: skipping %s (%s: %s)",
                child.name,
                type(exc).__name__,
                exc,
            )
            continue
        out[child.name] = config

    logger.info(
        "discover_jurisdictions: loaded %d jurisdiction(s) from %s",
        len(out),
        root.resolve(),
    )
    return out
