"""fetch_documents.py — Automated document retrieval from Legistar API.

Downloads legislative documents (contracts, resolutions, ordinances, agendas)
from a city's public Legistar portal for use with the O.D.I.A. audit pipeline.

Usage (non-interactive):
    python scripts/fetch_documents.py --city visalia --start 2024-01-01 --end 2024-12-31
    python scripts/fetch_documents.py --city chicago --state IL --types Contract Resolution

Interactive mode (no --city argument):
    python scripts/fetch_documents.py

The retrieval manifest is written to output_dir/retrieval_manifest.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# Bootstrap: make src/ importable when run as a script
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

_CITIES_FILE = _REPO_ROOT / "config" / "legistar_cities.json"


def _load_cities() -> list[dict]:
    if _CITIES_FILE.exists():
        return json.loads(_CITIES_FILE.read_text(encoding="utf-8"))
    return []


def _find_client_id(city: str, state: str | None, cities: list[dict]) -> str | None:
    """Resolve a city name (or direct client_id) to a Legistar client ID."""
    normalized = city.lower().replace(" ", "").replace("-", "")
    for entry in cities:
        if entry.get("client_id", "").lower() == normalized:
            return entry["client_id"]
        city_key = entry.get("city", "").lower().replace(" ", "").replace("-", "")
        if city_key == normalized:
            if state is None or entry.get("state", "").upper() == state.upper():
                return entry["client_id"]
    # Treat input directly as a client_id
    return city.lower().strip()


def _interactive_mode(cities: list[dict]) -> tuple[str, str, str, list[str] | None]:
    """Prompt user for city, dates, and types. Returns (client_id, start, end, types)."""
    print()
    print("=" * 60)
    print("O.D.I.A. — Legistar Document Retrieval")
    print("=" * 60)
    print()

    if cities:
        print("Known cities (showing first 20):")
        for i, c in enumerate(cities[:20], 1):
            print(f"  {i:2}. {c['city']}, {c['state']}  ({c['client_id']})")
        print()

    city_input = input("Enter city name or Legistar client ID: ").strip()
    if not city_input:
        print("[ERROR] City name is required.")
        sys.exit(1)

    state_input = input("State abbreviation (optional, press Enter to skip): ").strip() or None
    client_id = _find_client_id(city_input, state_input, cities)
    if not client_id:
        client_id = city_input.lower().strip()
    print(f"Using Legistar client ID: {client_id}")

    today = date.today().isoformat()
    start = input(f"Start date YYYY-MM-DD [2020-01-01]: ").strip() or "2020-01-01"
    end = input(f"End date   YYYY-MM-DD [{today}]: ").strip() or today

    print()
    print("Document types (comma-separated, or press Enter for all):")
    print("  Examples: Contract, Resolution, Ordinance, Minutes, Agenda")
    types_input = input("Types: ").strip()
    types = [t.strip() for t in types_input.split(",") if t.strip()] if types_input else None

    return client_id, start, end, types


def run(
    city: str,
    start: str,
    end: str,
    output_dir: str | Path = "data/retrieved",
    state: str | None = None,
    types: list[str] | None = None,
) -> dict:
    """Run a Legistar retrieval job.

    Returns the retrieval manifest dict.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cities = _load_cities()
    client_id = _find_client_id(city, state, cities)

    print(f"Connecting to Legistar API: client={client_id}")
    print(f"Date range: {start} — {end}")
    if types:
        print(f"Document types: {', '.join(types)}")
    else:
        print("Document types: all")
    print(f"Output directory: {output_dir}")
    print()

    try:
        from oraculus_di_auditor.adapters.legistar_adapter import LegistarAdapter

        adapter = LegistarAdapter(client_id)
        manifest = adapter.retrieve_corpus(
            start_date=start,
            end_date=end,
            output_dir=output_dir,
            matter_types=types,
        )
    except ImportError as exc:
        print(f"[ERROR] Legistar adapter not available: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Retrieval failed: {exc}")
        sys.exit(1)

    print(f"[OK] Retrieved {manifest['downloaded_count']} documents")
    if manifest["failed_count"]:
        print(f"[!] {manifest['failed_count']} downloads failed (see log)")
    print(f"Manifest written to: {output_dir}/retrieval_manifest.json")
    return manifest


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fetch_documents",
        description="Retrieve legislative documents from Legistar API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/fetch_documents.py --city visalia --start 2024-01-01 --end 2024-12-31\n"
            "  python scripts/fetch_documents.py --city chicago --state IL --types Contract Resolution\n"
            "  python scripts/fetch_documents.py  # interactive mode\n"
        ),
    )
    p.add_argument("--city", metavar="NAME", help="City name or Legistar client ID")
    p.add_argument("--state", metavar="ST", help="State abbreviation (e.g. CA)")
    p.add_argument("--start", metavar="DATE", help="Start date YYYY-MM-DD")
    p.add_argument(
        "--end",
        metavar="DATE",
        default=date.today().isoformat(),
        help="End date YYYY-MM-DD (default: today)",
    )
    p.add_argument(
        "--output",
        metavar="DIR",
        default="data/retrieved",
        help="Output directory (default: data/retrieved/)",
    )
    p.add_argument(
        "--types",
        nargs="*",
        metavar="TYPE",
        help="Matter types to retrieve (e.g. Contract Resolution Ordinance). Omit for all.",
    )
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    cities = _load_cities()

    if not args.city:
        # Interactive mode
        client_id, start, end, types = _interactive_mode(cities)
        run(
            city=client_id,
            start=start,
            end=end,
            output_dir=args.output,
            types=types,
        )
    else:
        run(
            city=args.city,
            start=args.start or "2020-01-01",
            end=args.end,
            output_dir=args.output,
            state=args.state,
            types=args.types,
        )


if __name__ == "__main__":
    main()
