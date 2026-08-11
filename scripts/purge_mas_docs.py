"""purge_mas_docs.py — Remove accidentally-ingested MAS synthesis outputs from DB.

MAS (Master Audit Synthesis) documents are ODIA output artifacts, not source
documents. Ingesting them creates circular-reference noise in the RAG index
(the system analyzing its own outputs). This script removes them while
preserving legitimate source documents that happen to contain "master" in the
title (e.g., FLOCK Master Service Agreements, Downtown Master Plan docs).

Usage:
    python scripts/purge_mas_docs.py --dry-run   # preview what will be removed
    python scripts/purge_mas_docs.py              # execute removal

After running, rebuild the RAG index:
    python scripts/build_rag_index.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from oraculus_di_auditor.db.models import Analysis, Anomaly, Document  # noqa: E402
from oraculus_di_auditor.db.session import get_db, init_db  # noqa: E402

# Patterns that identify MAS synthesis OUTPUT documents (version-stamped)
_MAS_INCLUDE = [
    "%_MAS_V%",  # Dinuba_MAS_V10_0, TCSO_MAS_V4_1, etc.
    "%Master Audit Synthesis%",
    "%Master Audit Record%",
    "% MAS V%",  # space-separated variant
    "%Audit Synthesis%",  # VPD_Audit_Synthesis_2026, etc.
    "%Filing TOC%",  # VPD_Master_Filing_TOC
    "%Initial MAS%",  # Tulare_Initial_MAS_V1_0
    "%County MAS%",  # Tulare_County_MAS
]

# Patterns that must NOT be deleted (legitimate source documents)
_MAS_EXCLUDE = [
    "%Master Service Agreement%",  # FLOCK contracts
    "%Master Plan%",  # City planning documents
    "%Downtown Master%",  # Study session planning docs
    "%Utility Master%",  # Engineering plans
]


def _fetch_mas_docs(session) -> list:
    from sqlalchemy import and_, or_

    include_filters = or_(*[Document.title.like(p) for p in _MAS_INCLUDE])
    exclude_filters = and_(*[~Document.title.like(p) for p in _MAS_EXCLUDE])
    return session.query(Document).filter(include_filters, exclude_filters).all()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview only, no changes"
    )
    args = parser.parse_args()

    init_db()

    with get_db() as session:
        mas_docs = _fetch_mas_docs(session)

        if not mas_docs:
            print("No MAS synthesis documents found. Nothing to remove.")
            return

        print(f"Found {len(mas_docs)} MAS synthesis documents across jurisdictions:\n")
        by_jur: dict[str, int] = {}
        for doc in mas_docs:
            jur = doc.jurisdiction or "unknown"
            by_jur[jur] = by_jur.get(jur, 0) + 1

        for jur, count in sorted(by_jur.items()):
            print(f"  {jur:20s}  {count} docs")

        print(f"\nTotal: {len(mas_docs)} documents")

        if args.dry_run:
            print("\n[dry-run] No changes made. Remove --dry-run to execute.")
            return

        confirm = (
            input("\nDelete these documents and their analyses/anomalies? [y/N] ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Aborted.")
            return

        doc_ids = [d.document_id for d in mas_docs]
        removed_anomalies = 0
        removed_analyses = 0

        for doc_id in doc_ids:
            analyses = (
                session.query(Analysis).filter(Analysis.document_id == doc_id).all()
            )
            for an in analyses:
                removed_anomalies += (
                    session.query(Anomaly).filter(Anomaly.analysis_id == an.id).delete()
                )
                session.delete(an)
                removed_analyses += 1

        for doc in mas_docs:
            session.delete(doc)

        session.commit()

        print("\nRemoved:")
        print(f"  {len(doc_ids)} MAS documents")
        print(f"  {removed_analyses} analyses")
        print(f"  {removed_anomalies} anomaly findings")
        print("\nNext: python scripts/build_rag_index.py")


if __name__ == "__main__":
    main()
