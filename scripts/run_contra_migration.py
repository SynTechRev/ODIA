"""Apply C.O.N.T.R.A. schema extension to the live database.

Creates the six new C.O.N.T.R.A. tables if they do not already exist.
Safe to run multiple times — SQLAlchemy's create_all() is a no-op for
tables that already exist.

Usage (from repo root):
    .venv\\Scripts\\python scripts\\run_contra_migration.py
    .venv\\Scripts\\python scripts\\run_contra_migration.py --db-url sqlite:///path/to/other.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the src package importable from the scripts directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import create_engine, inspect, text  # noqa: E402

from oraculus_di_auditor.db.models import (  # noqa: E402
    Base,
    CasiScore,
    CommercialDocument,
    CommercialEntity,
    CommercialEntityAlias,
    ContraFinding,
    S128196Case,
)
from oraculus_di_auditor.db.session import DEFAULT_DATABASE_URL  # noqa: E402

CONTRA_TABLES = {
    "commercial_entities": CommercialEntity,
    "commercial_entity_aliases": CommercialEntityAlias,
    "commercial_documents": CommercialDocument,
    "contra_findings": ContraFinding,
    "casi_scores": CasiScore,
    "s1281_96_cases": S128196Case,
}


def run_migration(db_url: str) -> None:
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, connect_args=connect_args)

    inspector = inspect(engine)
    existing = set(inspector.get_table_names())

    # create_all with tables= only touches the specified tables
    target_tables = [
        Base.metadata.tables[name]
        for name in CONTRA_TABLES
        if name not in existing
    ]

    if not target_tables:
        print("All C.O.N.T.R.A. tables already exist. Nothing to do.")
        return

    Base.metadata.create_all(bind=engine, tables=target_tables)

    created = [t.name for t in target_tables]
    print(f"Created {len(created)} table(s): {', '.join(created)}")

    # Verify all tables now present
    inspector2 = inspect(engine)
    after = set(inspector2.get_table_names())
    missing = set(CONTRA_TABLES) - after
    if missing:
        print(f"WARNING: tables still missing after migration: {missing}", file=sys.stderr)
        sys.exit(1)

    print("Migration complete. C.O.N.T.R.A. schema is ready.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply C.O.N.T.R.A. DB schema extension")
    parser.add_argument(
        "--db-url",
        default=DEFAULT_DATABASE_URL,
        help="SQLAlchemy database URL (default: repo-root oraculus_audit.db)",
    )
    args = parser.parse_args()
    print(f"Target database: {args.db_url}")
    run_migration(args.db_url)


if __name__ == "__main__":
    main()
