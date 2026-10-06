"""Backfill finding_density_ratio and regulated_content_delta for pre-existing casi_scores rows.

Rows ingested before V2.0-B have NULL for these two columns because the ingest pipeline
was updated after the initial 144-document run. This script computes and writes the values
for every casi_scores row that currently has NULL for finding_density_ratio.

Usage:
    python scripts/backfill_fdr_rcd.py
    python scripts/backfill_fdr_rcd.py --db-path "D:/CONTRA Contract Corpus/contra_corpus.db"
    python scripts/backfill_fdr_rcd.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_REGULATED_TYPES = {"privacy_notice"}


def _engine(db_path: str):
    from sqlalchemy import create_engine

    return create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )


def backfill(db_path: str, dry_run: bool = False) -> None:
    from oraculus_di_auditor.db.models import (
        CasiScore,
        CommercialDocument,
        ContraFinding,
    )
    from sqlalchemy import func
    from sqlalchemy.orm import sessionmaker

    engine = _engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Rows missing FDR (i.e., ingested before V2.0-B)
    null_rows = (
        session.query(CasiScore).filter(CasiScore.finding_density_ratio.is_(None)).all()
    )
    print(f"Rows needing backfill: {len(null_rows)}")

    if not null_rows:
        print("Nothing to do.")
        session.close()
        return

    # Pre-load finding counts per document
    finding_counts: dict[str, int] = {}
    for doc_hash, count in (
        session.query(ContraFinding.document_hash, func.count(ContraFinding.id))
        .group_by(ContraFinding.document_hash)
        .all()
    ):
        finding_counts[doc_hash] = count

    # Pre-load doc_type per document
    doc_types: dict[str, str] = {}
    for doc_hash, dtype in session.query(
        CommercialDocument.document_hash, CommercialDocument.doc_type
    ).all():
        doc_types[doc_hash] = dtype

    updated = 0
    skipped = 0

    for score in null_rows:
        h = score.document_hash
        agg = score.aggregate or 0
        finding_count = finding_counts.get(h, 0)
        doc_type = doc_types.get(h, "")

        # agg=0 is a valid scored state (all five axes returned 0).
        # FDR is 0.0 (no base score → no density); RCD does not apply.
        fdr = round(finding_count / agg, 3) if agg > 0 else 0.0
        rcd = (agg - 30) if doc_type in _REGULATED_TYPES and agg > 30 else None

        if dry_run:
            print(
                f"  DRY RUN [{h[:12]}...] doc_type={doc_type:<18} "
                f"findings={finding_count:<4} agg={agg:<4} "
                f"FDR={fdr}  RCD={rcd}"
            )
        else:
            score.finding_density_ratio = fdr
            score.regulated_content_delta = rcd

        updated += 1

    if not dry_run:
        session.commit()
        print(f"Backfill complete: {updated} rows updated, {skipped} skipped (agg=0).")
    else:
        print(f"\nDry run: {updated} rows would be updated, {skipped} skipped.")

    session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill FDR/RCD for pre-V2.0-B casi_scores rows"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing to DB",
    )
    args = parser.parse_args()
    backfill(args.db_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
