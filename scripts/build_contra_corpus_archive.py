"""CONTRA corpus archive builder — navigable JSON tree for offline analysis.

Produces data/contra_corpus_archive/ with:
  MASTER_INDEX.json         — all 144+ documents, flat list, all metadata
  by_entity/                — one JSON per entity with its documents + findings
  by_doc_type/              — one JSON per doc_type
  by_casi_band/             — one JSON per CASI band
  by_finding_type/          — one JSON per finding layer/type

Analogous to build_corpus_archive.py from v3.9.2.

Usage:
    python scripts/build_contra_corpus_archive.py
    python scripts/build_contra_corpus_archive.py --db-path "D:/CONTRA Contract Corpus/contra_corpus.db"
    python scripts/build_contra_corpus_archive.py --out-dir data/contra_corpus_archive
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_DEFAULT_OUT = "data/contra_corpus_archive"


def _engine(db_path: str):
    from sqlalchemy import create_engine
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def _build_archive(db_path: str, out_dir: Path) -> None:
    from sqlalchemy.orm import sessionmaker
    from oraculus_di_auditor.db.models import (
        CasiScore, CommercialDocument, CommercialEntity, ContraFinding,
        CommercialDocumentProvenance,
    )

    engine = _engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    out_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("by_entity", "by_doc_type", "by_casi_band", "by_finding_type"):
        (out_dir / sub).mkdir(exist_ok=True)

    print("Querying DB...")

    # Load all data
    entities = {e.entity_id: e for e in session.query(CommercialEntity).all()}
    scores = {s.document_hash: s for s in session.query(CasiScore).all()}
    provenance = {p.document_hash: p for p in session.query(CommercialDocumentProvenance).all()}
    findings_by_doc: dict[str, list[dict]] = defaultdict(list)
    for f in session.query(ContraFinding).all():
        findings_by_doc[f.document_hash].append({
            "finding_id": f.finding_id,
            "layer": f.layer,
            "severity": f.severity,
            "issue": f.issue,
        })

    master: list[dict] = []
    by_entity: dict[str, list] = defaultdict(list)
    by_doc_type: dict[str, list] = defaultdict(list)
    by_casi_band: dict[str, list] = defaultdict(list)
    by_finding_type: dict[str, list] = defaultdict(list)

    docs = session.query(CommercialDocument).all()
    print(f"Building archive for {len(docs)} documents...")

    for doc in docs:
        entity = entities.get(doc.entity_id)
        score = scores.get(doc.document_hash)
        prov = provenance.get(doc.document_hash)
        doc_findings = findings_by_doc.get(doc.document_hash, [])

        # Compute FDR
        finding_count = len(doc_findings)
        agg = score.aggregate if score else 0
        fdr = round(finding_count / agg, 2) if agg and agg > 0 else None

        # Compute RCD (regulatory baseline = 30)
        _REGULATED_TYPES = {"privacy_notice"}
        rcd = (agg - 30) if doc.doc_type in _REGULATED_TYPES and agg > 30 else None

        entry = {
            "document_hash": doc.document_hash,
            "entity_name": entity.canonical_name if entity else doc.entity_id,
            "entity_id": doc.entity_id,
            "corporate_family": entity.corporate_family if entity else None,
            "doc_type": doc.doc_type,
            "version_label": doc.version_label,
            "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
            "casi_aggregate": agg,
            "casi_band": score.band if score else None,
            "casi_axes": {
                "procedural_adhesion": score.procedural_adhesion if score else None,
                "modification_and_consent": score.modification_and_consent if score else None,
                "enforcement_cost_asymmetry": score.enforcement_cost_asymmetry if score else None,
                "remedy_foreclosure": score.remedy_foreclosure if score else None,
                "data_extraction_depth": score.data_extraction_depth if score else None,
            } if score else None,
            "finding_count": finding_count,
            "finding_density_ratio": fdr,
            "regulated_content_delta": rcd,
            "source_url": prov.source_url if prov else None,
            "source_tier": prov.source_tier if prov else None,
            "retrieval_ts": prov.retrieval_ts.isoformat() if prov and prov.retrieval_ts else None,
            "findings": doc_findings,
        }

        master.append(entry)
        by_entity[entity.canonical_name if entity else doc.entity_id].append(entry)
        by_doc_type[doc.doc_type or "unknown"].append(entry)
        by_casi_band[score.band if score else "unscored"].append(entry)
        for f in doc_findings:
            by_finding_type[f["layer"]].append({
                "document_hash": doc.document_hash,
                "entity_name": entry["entity_name"],
                "doc_type": doc.doc_type,
                "casi_aggregate": agg,
                "finding": f,
            })

    # Sort master by CASI desc
    master.sort(key=lambda x: x["casi_aggregate"] or 0, reverse=True)

    # MASTER_INDEX.json
    master_path = out_dir / "MASTER_INDEX.json"
    master_path.write_text(
        json.dumps({
            "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "total_documents": len(master),
            "total_entities": len(by_entity),
            "total_findings": sum(e["finding_count"] for e in master),
            "documents": master,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  MASTER_INDEX.json ({len(master)} documents)")

    # by_entity/
    for name, docs_list in by_entity.items():
        slug = name.lower().replace(" ", "_").replace("/", "_").replace("&", "and")[:40]
        out_file = out_dir / "by_entity" / f"{slug}.json"
        docs_list.sort(key=lambda x: x["casi_aggregate"] or 0, reverse=True)
        out_file.write_text(
            json.dumps({"entity": name, "document_count": len(docs_list), "documents": docs_list}, indent=2),
            encoding="utf-8",
        )
    print(f"  by_entity/ ({len(by_entity)} files)")

    # by_doc_type/
    for dtype, docs_list in by_doc_type.items():
        docs_list.sort(key=lambda x: x["casi_aggregate"] or 0, reverse=True)
        out_file = out_dir / "by_doc_type" / f"{dtype}.json"
        out_file.write_text(
            json.dumps({"doc_type": dtype, "document_count": len(docs_list), "documents": docs_list}, indent=2),
            encoding="utf-8",
        )
    print(f"  by_doc_type/ ({len(by_doc_type)} files)")

    # by_casi_band/
    for band, docs_list in by_casi_band.items():
        docs_list.sort(key=lambda x: x["casi_aggregate"] or 0, reverse=True)
        safe = band.lower().replace(" ", "_")
        out_file = out_dir / "by_casi_band" / f"{safe}.json"
        out_file.write_text(
            json.dumps({"band": band, "document_count": len(docs_list), "documents": docs_list}, indent=2),
            encoding="utf-8",
        )
    print(f"  by_casi_band/ ({len(by_casi_band)} bands)")

    # by_finding_type/
    for layer, findings_list in by_finding_type.items():
        safe = layer.lower().replace(" ", "_").replace("-", "_")[:40]
        out_file = out_dir / "by_finding_type" / f"{safe}.json"
        out_file.write_text(
            json.dumps({"layer": layer, "finding_count": len(findings_list), "findings": findings_list}, indent=2),
            encoding="utf-8",
        )
    print(f"  by_finding_type/ ({len(by_finding_type)} layers)")

    session.close()

    total_size = sum(f.stat().st_size for f in out_dir.rglob("*.json"))
    print(f"\nArchive written to: {out_dir.resolve()}")
    print(f"Total size: {total_size / 1024:.1f} KB across {sum(1 for _ in out_dir.rglob('*.json'))} JSON files")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build CONTRA corpus archive")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--out-dir", default=_DEFAULT_OUT)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    _build_archive(args.db_path, out_dir)


if __name__ == "__main__":
    main()
