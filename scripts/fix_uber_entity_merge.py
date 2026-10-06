"""One-time migration: merge duplicate Uber entity records.

'contra:uber_technologies_inc'  (4 docs, no period) → merged into
'contra:uber_technologies_inc.' (8 docs, with period) which becomes canonical.

After merge: 12 docs total under the canonical ID; the no-period variant
is registered as an alias so future ingests resolve correctly.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from sqlalchemy import create_engine, text

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"

CANONICAL_ID = "contra:uber_technologies_inc."  # keep (8 docs, with period)
DUPLICATE_ID = "contra:uber_technologies_inc"  # merge away (4 docs, no period)
DUPLICATE_NAME = "Uber Technologies Inc"  # becomes alias


def run(db_path: str = _DEFAULT_DB, dry_run: bool = False) -> None:
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as conn:
        # Verify current state
        rows = conn.execute(
            text(
                "SELECT entity_id, canonical_name FROM commercial_entities "
                "WHERE entity_id IN (:cid, :did)"
            ),
            {"cid": CANONICAL_ID, "did": DUPLICATE_ID},
        ).fetchall()

        found = {r[0]: r[1] for r in rows}
        if CANONICAL_ID not in found:
            print(f"ERROR: canonical entity '{CANONICAL_ID}' not found in DB")
            return
        if DUPLICATE_ID not in found:
            print(
                f"SKIP: duplicate entity '{DUPLICATE_ID}' not found — already merged or never existed"
            )
            return

        print(f"Canonical : {CANONICAL_ID!r}  →  {found[CANONICAL_ID]!r}")
        print(f"Duplicate : {DUPLICATE_ID!r}  →  {found[DUPLICATE_ID]!r}")

        # Count affected rows
        doc_count = conn.execute(
            text("SELECT COUNT(*) FROM commercial_documents WHERE entity_id = :did"),
            {"did": DUPLICATE_ID},
        ).scalar()
        print(f"\nDocuments to re-point  : {doc_count}")

        if dry_run:
            print("\n[DRY RUN] No changes written.")
            return

        # 1. Re-point commercial_documents
        conn.execute(
            text(
                "UPDATE commercial_documents SET entity_id = :cid WHERE entity_id = :did"
            ),
            {"cid": CANONICAL_ID, "did": DUPLICATE_ID},
        )

        # 2. Register duplicate name as alias (idempotent: ignore if already exists)
        existing_alias = conn.execute(
            text(
                "SELECT id FROM commercial_entity_aliases "
                "WHERE entity_id = :cid AND alias = :alias"
            ),
            {"cid": CANONICAL_ID, "alias": DUPLICATE_NAME},
        ).fetchone()

        if not existing_alias:
            conn.execute(
                text(
                    "INSERT INTO commercial_entity_aliases (entity_id, alias) VALUES (:cid, :alias)"
                ),
                {"cid": CANONICAL_ID, "alias": DUPLICATE_NAME},
            )
            print(f"Alias registered: {DUPLICATE_NAME!r} → {CANONICAL_ID!r}")

        # 4. Delete the duplicate entity record
        conn.execute(
            text("DELETE FROM commercial_entities WHERE entity_id = :did"),
            {"did": DUPLICATE_ID},
        )

        # Verify
        final_docs = conn.execute(
            text("SELECT COUNT(*) FROM commercial_documents WHERE entity_id = :cid"),
            {"cid": CANONICAL_ID},
        ).scalar()
        print(f"\nMerge complete. Canonical entity now has {final_docs} documents.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge duplicate Uber entity records")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(db_path=args.db_path, dry_run=args.dry_run)
