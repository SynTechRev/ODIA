"""setup_jurisdiction.py — Interactive configuration wizard for O.D.I.A.

Guides a user through creating config/jurisdiction.json, config/agencies.json,
and config/corpus_manifest.json through prompted questions.  No external
dependencies — pure Python standard library only.

Usage:
    python scripts/setup_jurisdiction.py
    python scripts/setup_jurisdiction.py --config-dir config/
    python scripts/setup_jurisdiction.py --non-interactive  # for testing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: make src/ importable when run as a script
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

# ---------------------------------------------------------------------------
# Agency catalogue (mirrors agencies.example.json)
# ---------------------------------------------------------------------------

_AGENCY_CATALOGUE: dict[str, list[str]] = {
    "Police Department": ["police", "police department", "law enforcement", "pd"],
    "Fire Department": ["fire", "fire department", "fire services"],
    "City Council": ["city council", "council", "council meeting"],
    "City Manager": ["city manager", "city manager's office"],
    "Finance Department": ["finance", "finance department"],
    "Public Works": ["public works", "public works department"],
    "Information Technology": ["information technology", "it department"],
    "Legal/City Attorney": ["city attorney", "legal department"],
}

_AGENCY_MENU: list[str] = list(_AGENCY_CATALOGUE.keys()) + ["All of the above"]

_DEFAULT_SOURCE = "data/demo/"

# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------


def _prompt(message: str, default: str = "") -> str:
    """Display *message* and return stripped user input.

    If *default* is non-empty it is shown in brackets and returned when the
    user presses Enter without typing anything.
    """
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{message}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return value if value else default


def _confirm(message: str, default: bool = True) -> bool:
    """Ask a yes/no question.  Returns True for yes, False for no."""
    hint = " (Y/n)" if default else " (y/N)"
    raw = _prompt(message + hint).lower()
    if not raw:
        return default
    return raw.startswith("y")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_state_code(value: str) -> bool:
    """Return True if *value* is a non-empty 2-letter alphabetic string."""
    return len(value) == 2 and value.isalpha()


def validate_source_path(value: str) -> bool:
    """Return True if *value* is an empty string or an existing directory."""
    if not value:
        return True
    return Path(value).is_dir()


# ---------------------------------------------------------------------------
# Collection steps (each returns the collected value or raises SystemExit)
# ---------------------------------------------------------------------------


def _ask_jurisdiction_name() -> str:
    for _ in range(5):
        name = _prompt("What city or jurisdiction are you auditing?")
        if name:
            return name
        print("  Jurisdiction name is required.")
    print("Too many invalid attempts. Exiting.")
    sys.exit(1)


def _ask_state_code() -> str:
    for _ in range(5):
        code = _prompt("What state is this in? (2-letter code, e.g., CA)").upper()
        if validate_state_code(code):
            return code
        print("  Please enter a valid 2-letter state code (e.g., CA, TX, NY).")
    print("Too many invalid attempts. Exiting.")
    sys.exit(1)


def _ask_legistar_url() -> str:
    url = _prompt(
        "What is the Legistar URL for this jurisdiction?"
        " (Press Enter to skip if unknown)"
    )
    return url


def _ask_agencies() -> dict[str, list[str]]:
    """Present a numbered menu and return the selected agency dict."""
    print("\nWhich agencies do you want to track?")
    print("Enter numbers separated by commas, or press Enter to select all.")
    for i, name in enumerate(_AGENCY_MENU, 1):
        print(f"  {i:2d}. {name}")

    raw = _prompt("Your selection").strip()

    if not raw:
        # Default: all real agencies (skip the "All" sentinel)
        return dict(_AGENCY_CATALOGUE)

    selected: dict[str, list[str]] = {}
    for token in raw.split(","):
        token = token.strip()
        if not token.isdigit():
            continue
        idx = int(token) - 1
        if idx < 0 or idx >= len(_AGENCY_MENU):
            continue
        menu_name = _AGENCY_MENU[idx]
        if menu_name == "All of the above":
            return dict(_AGENCY_CATALOGUE)
        if menu_name in _AGENCY_CATALOGUE:
            selected[menu_name] = _AGENCY_CATALOGUE[menu_name]

    return selected if selected else dict(_AGENCY_CATALOGUE)


def _ask_source_path() -> str:
    for _ in range(5):
        path = _prompt(
            "Where are your documents? Enter a folder path,"
            " or press Enter to use the demo data",
            default=_DEFAULT_SOURCE,
        )
        if validate_source_path(path):
            return path
        print(f"  Directory not found: {path!r}. Please enter a valid path.")
    print("Too many invalid attempts. Exiting.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config assembly
# ---------------------------------------------------------------------------


def build_jurisdiction_config(
    name: str,
    state: str,
    legistar_url: str = "",
    country: str = "US",
    meeting_type: str = "City Council Regular Meeting",
) -> dict[str, Any]:
    """Return a jurisdiction.json-compatible dict."""
    cfg: dict[str, Any] = {
        "name": name,
        "state": state,
        "country": country,
        "meeting_type": meeting_type,
    }
    if legistar_url:
        cfg["legistar_base_url"] = legistar_url
    return cfg


def build_agencies_config(selected: dict[str, list[str]]) -> dict[str, list[str]]:
    """Return an agencies.json-compatible dict (no comment keys)."""
    return dict(selected)


def build_corpus_manifest() -> dict[str, str]:
    """Return an empty corpus_manifest.json-compatible dict."""
    return {}


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _config_exists(config_dir: Path) -> bool:
    """Return True if a non-example jurisdiction.json already exists."""
    return (config_dir / "jurisdiction.json").exists()


def save_config(
    config_dir: Path,
    jurisdiction: dict[str, Any],
    agencies: dict[str, list[str]],
    corpus_manifest: dict[str, str],
) -> None:
    """Write all three config files to *config_dir*."""
    _write_json(config_dir / "jurisdiction.json", jurisdiction)
    _write_json(config_dir / "agencies.json", agencies)
    _write_json(config_dir / "corpus_manifest.json", corpus_manifest)


# ---------------------------------------------------------------------------
# Main wizard
# ---------------------------------------------------------------------------


def run_wizard(config_dir: Path | str = "config") -> dict[str, Any]:
    """Run the interactive setup wizard.

    Returns a summary dict with keys: jurisdiction, agencies, corpus_manifest,
    source_path, config_dir.

    Raises SystemExit on user abort.
    """
    config_dir = Path(config_dir)

    print()
    print("=" * 60)
    print("O.D.I.A. — Jurisdiction Setup Wizard")
    print("=" * 60)
    print(
        "This wizard creates the configuration files needed to run an audit.\n"
        "It generates config/jurisdiction.json, config/agencies.json, and\n"
        "config/corpus_manifest.json from your answers.\n"
    )

    # Overwrite check
    if _config_exists(config_dir):
        existing = json.loads(
            (config_dir / "jurisdiction.json").read_text(encoding="utf-8")
        )
        print(f"Configuration already exists for: {existing.get('name', '(unknown)')}")
        if not _confirm("Overwrite existing configuration?", default=False):
            print("Setup cancelled. Existing configuration unchanged.")
            sys.exit(0)

    # Collect inputs
    name = _ask_jurisdiction_name()
    state = _ask_state_code()
    legistar_url = _ask_legistar_url()
    agencies = _ask_agencies()
    source_path = _ask_source_path()

    # Build config objects
    jurisdiction = build_jurisdiction_config(name, state, legistar_url)
    corpus_manifest = build_corpus_manifest()

    # Summary
    print()
    print("-" * 40)
    print("Configuration Summary")
    print("-" * 40)
    print(f"  Jurisdiction : {name}")
    print(f"  State        : {state}")
    print(f"  Legistar URL : {legistar_url or '(not set)'}")
    print(f"  Agencies     : {len(agencies)} selected")
    print(f"  Documents    : {source_path or _DEFAULT_SOURCE}")
    print()

    if not _confirm("Save this configuration?", default=True):
        print("Setup cancelled.")
        sys.exit(0)

    save_config(config_dir, jurisdiction, agencies, corpus_manifest)

    effective_source = source_path or _DEFAULT_SOURCE
    print()
    print("[OK] Configuration saved to config/")
    print()
    print(
        "Run your audit with:\n"
        f"    python scripts/run_audit.py"
        f" --source {effective_source} --output reports/"
    )
    print()

    return {
        "jurisdiction": jurisdiction,
        "agencies": agencies,
        "corpus_manifest": corpus_manifest,
        "source_path": effective_source,
        "config_dir": str(config_dir),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="setup_jurisdiction",
        description="Interactive wizard to configure O.D.I.A. for your jurisdiction.",
    )
    p.add_argument(
        "--config-dir",
        default="config",
        metavar="DIR",
        help="Directory to write config files to (default: config/)",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    run_wizard(config_dir=args.config_dir)


if __name__ == "__main__":
    main()
