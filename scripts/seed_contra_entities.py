"""Seed the C.O.N.T.R.A. entity registry from config/contra_entities.json.

Reads canonical entity names and aliases from the config file and inserts
them into the commercial_entities and commercial_entity_aliases tables.
Safe to run multiple times — skips entities that already exist.

Usage (from repo root):
    .venv\\Scripts\\python scripts\\seed_contra_entities.py
    .venv\\Scripts\\python scripts\\seed_contra_entities.py --dry-run
    .venv\\Scripts\\python scripts\\seed_contra_entities.py --db-url sqlite:///other.db
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oraculus_di_auditor.db.session import DEFAULT_DATABASE_URL, init_db, get_db  # noqa: E402
from oraculus_di_auditor.entity.registry import Entity, EntityRegistry  # noqa: E402

_CONFIG = Path(__file__).resolve().parent.parent / "config" / "contra_entities.json"


def load_config() -> list[dict]:
    with open(_CONFIG, encoding="utf-8") as f:
        data = json.load(f)
    return data["entities"]


def seed(db_url: str, dry_run: bool) -> None:
    entities = load_config()
    print(f"Loaded {len(entities)} entities from {_CONFIG.name}")

    if dry_run:
        for e in entities:
            print(f"  [dry-run] would seed: {e['canonical_name']}")
        return

    init_db(db_url)

    with get_db() as session:
        registry = EntityRegistry(db_session=session)

        added = 0
        skipped = 0
        for spec in entities:
            existing = registry.get_by_canonical_name(spec["canonical_name"])
            if existing is not None:
                skipped += 1
                continue

            entity = Entity.new(
                canonical_name=spec["canonical_name"],
                naics=spec.get("naics"),
                corporate_family=spec.get("corporate_family"),
                in_contra_corpus=True,
                in_tulare_priority_list=spec.get("in_tulare_priority_list", False),
                aliases=spec.get("aliases", []),
            )
            registry.add_entity(entity)
            added += 1
            print(f"  seeded: {entity.canonical_name}")

    print(f"\nDone. Added: {added}  Skipped (already present): {skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed C.O.N.T.R.A. entity registry")
    parser.add_argument("--db-url", default=DEFAULT_DATABASE_URL)
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be seeded without writing"
    )
    args = parser.parse_args()
    print(f"Target database: {args.db_url}")
    seed(args.db_url, args.dry_run)


if __name__ == "__main__":
    main()
