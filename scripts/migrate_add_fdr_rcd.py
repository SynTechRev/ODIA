"""One-time migration: add finding_density_ratio and regulated_content_delta to casi_scores.

SQLAlchemy create_all() never alters existing tables, so new columns defined in the
model must be added to an already-created DB via ALTER TABLE.

Usage:
    python scripts/migrate_add_fdr_rcd.py
    python scripts/migrate_add_fdr_rcd.py --db-path "D:/CONTRA Contract Corpus/contra_corpus.db"
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"


def migrate(db_path: str) -> None:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    con = sqlite3.connect(str(path))
    try:
        cur = con.cursor()

        cur.execute("PRAGMA table_info(casi_scores)")
        existing_cols = {row[1] for row in cur.fetchall()}
        print(f"Existing casi_scores columns: {sorted(existing_cols)}")

        added: list[str] = []

        if "finding_density_ratio" not in existing_cols:
            cur.execute(
                "ALTER TABLE casi_scores ADD COLUMN finding_density_ratio REAL"
            )
            added.append("finding_density_ratio REAL")

        if "regulated_content_delta" not in existing_cols:
            cur.execute(
                "ALTER TABLE casi_scores ADD COLUMN regulated_content_delta INTEGER"
            )
            added.append("regulated_content_delta INTEGER")

        con.commit()

        if added:
            print(f"Migration complete. Added {len(added)} column(s):")
            for col in added:
                print(f"  + {col}")
            print("Existing rows will have NULL for these columns (nullable by design).")
            print("New ingests will populate them via the updated pipeline.")
        else:
            print("Schema already up to date — no changes needed.")

    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add FDR/RCD columns to casi_scores in contra_corpus.db"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    args = parser.parse_args()
    migrate(args.db_path)


if __name__ == "__main__":
    main()
