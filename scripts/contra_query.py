"""CONTRA DB quick inspector — runs after contra_batch_ingest.py.

Usage:
    python scripts/contra_query.py                   # full summary
    python scripts/contra_query.py --entity "Google LLC"
    python scripts/contra_query.py --top-casi 10
    python scripts/contra_query.py --version-chain "Google LLC"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"


def _engine(db_path: str):
    from sqlalchemy import create_engine
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def _summary(session) -> None:
    from sqlalchemy import text
    rows = [
        ("commercial_entities",             "Entities"),
        ("commercial_documents",            "Documents"),
        ("commercial_document_provenance",  "Provenance records"),
        ("contra_findings",                 "Findings"),
        ("casi_scores",                     "CASI scores"),
    ]
    print("\n── CONTRA DB Summary ──")
    for table, label in rows:
        try:
            n = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        except Exception:
            n = "table missing"
        print(f"  {label:<28} {n}")

    # CASI band distribution
    from oraculus_di_auditor.db.models import CasiScore
    print("\n── CASI Band Distribution ──")
    from sqlalchemy import func
    bands = session.query(CasiScore.band, func.count()).group_by(CasiScore.band).all()
    for band, count in sorted(bands, key=lambda x: x[1], reverse=True):
        print(f"  {band:<30} {count}")


def _entity_detail(session, entity_name: str) -> None:
    from oraculus_di_auditor.db.models import (
        CasiScore, CommercialDocument, CommercialEntity, ContraFinding,
    )

    entity = session.query(CommercialEntity).filter(
        CommercialEntity.canonical_name == entity_name
    ).first()

    if not entity:
        print(f"Entity not found: {entity_name}")
        return

    print(f"\n── Entity: {entity.canonical_name} ({entity.entity_id}) ──")
    print(f"  Corporate family: {entity.corporate_family}")

    docs = session.query(CommercialDocument).filter_by(entity_id=entity.entity_id).all()
    print(f"  Documents: {len(docs)}")

    for doc in sorted(docs, key=lambda d: d.version_label or ""):
        score = doc.casi_score
        findings_count = len(doc.findings)
        band = score.band if score else "no score"
        agg = score.aggregate if score else "-"
        vl = doc.version_label or ""
        print(f"    [{doc.doc_type:<16}] {vl:<15} CASI={agg:<4} [{band}] | {findings_count} findings")


def _top_casi(session, n: int) -> None:
    from oraculus_di_auditor.db.models import (
        CasiScore, CommercialDocument, CommercialEntity,
    )

    print(f"\n── Top {n} Documents by CASI Score ──")
    results = (
        session.query(CasiScore, CommercialDocument, CommercialEntity)
        .join(CommercialDocument, CasiScore.document_hash == CommercialDocument.document_hash)
        .join(CommercialEntity, CommercialDocument.entity_id == CommercialEntity.entity_id)
        .order_by(CasiScore.aggregate.desc())
        .limit(n)
        .all()
    )
    for score, doc, entity in results:
        vl = doc.version_label or ""
        print(f"  {score.aggregate:>3} [{score.band:<22}] {entity.canonical_name:<30} {doc.doc_type:<16} {vl}")


def _version_chain(session, entity_name: str) -> None:
    from oraculus_di_auditor.db.models import CommercialDocument, CommercialEntity

    entity = session.query(CommercialEntity).filter(
        CommercialEntity.canonical_name == entity_name
    ).first()
    if not entity:
        print(f"Entity not found: {entity_name}")
        return

    docs = (
        session.query(CommercialDocument)
        .filter_by(entity_id=entity.entity_id)
        .order_by(CommercialDocument.effective_date)
        .all()
    )
    print(f"\n── Version Chain: {entity_name} ──")
    for doc in docs:
        dt = doc.effective_date.strftime("%Y-%m-%d") if doc.effective_date else "no date"
        score = doc.casi_score
        agg = score.aggregate if score else "?"
        print(f"  {dt}  [{doc.doc_type:<16}] {doc.version_label or '':<20} CASI={agg}  {doc.document_hash[:12]}...")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect CONTRA DB")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--entity", default=None)
    parser.add_argument("--top-casi", type=int, default=None)
    parser.add_argument("--version-chain", default=None)
    args = parser.parse_args()

    from sqlalchemy.orm import sessionmaker
    engine = _engine(args.db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    if args.entity:
        _entity_detail(session, args.entity)
    elif args.top_casi:
        _top_casi(session, args.top_casi)
    elif args.version_chain:
        _version_chain(session, args.version_chain)
    else:
        _summary(session)

    session.close()


if __name__ == "__main__":
    main()
