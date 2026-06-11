"""Build RAG vector indices from the live oraculus_audit.db.

Constructs four searchable collections:

  corpus     — one entry per document (title + jurisdiction + anomaly summary)
  ace        — one entry per anomaly finding (issue + layer + severity + details)
  lexicon    — legal terms from the constitutional/legal reference data
  jim        — cross-jurisdiction pattern summaries

Run from the repo root:
    python scripts/build_rag_index.py

The indices land in data/vectors/ and are immediately usable by OracRAG.
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import os

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "config"))

from oraculus_di_auditor.db.models import Analysis, Anomaly, Document  # noqa: E402
from oraculus_di_auditor.db.session import get_db, init_db  # noqa: E402
from oraculus_di_auditor.embeddings import LocalEmbedder  # noqa: E402
from oraculus_di_auditor.retriever import Retriever  # noqa: E402

# ODIA_VECTORS_DIR lets the script write directly to the desktop app's userData
# path when building an index for the installed app. Falls back to repo default.
_env_vectors = os.environ.get("ODIA_VECTORS_DIR")
VECTORS_DIR = Path(_env_vectors) if _env_vectors else REPO_ROOT / "data" / "vectors"
VECTORS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_details(details_json: str | None) -> str:
    if not details_json:
        return ""
    try:
        d = json.loads(details_json)
        parts = []
        for v in d.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                parts.extend(str(x) for x in v[:3])
        return " ".join(parts)[:500]
    except Exception:
        return ""


def build_corpus_index(session) -> tuple[list[str], list[dict]]:
    """One entry per document — title, jurisdiction, anomaly summary."""
    docs = session.query(Document).all()
    texts, metas = [], []
    for doc in docs:
        analyses = (
            session.query(Analysis)
            .filter(Analysis.document_id == doc.document_id)
            .all()
        )
        anomalies = []
        for an in analyses:
            anomalies.extend(
                session.query(Anomaly).filter(Anomaly.analysis_id == an.id).all()
            )

        anomaly_text = " | ".join(
            f"[{a.severity}:{a.layer}] {a.issue}" for a in anomalies[:10]
        )
        text = (
            f"Document: {doc.title or 'Untitled'} | "
            f"Jurisdiction: {doc.jurisdiction or 'unknown'} | "
            f"Type: {doc.document_type or 'unknown'} | "
            f"Findings: {anomaly_text or 'none'}"
        )
        texts.append(text)
        metas.append(
            {
                "id": doc.document_id,
                "title": doc.title or "Untitled",
                "text": text,  # field name expected by ContextAssembler
                "jurisdiction": doc.jurisdiction,
                "document_type": doc.document_type,
                "anomaly_count": len(anomalies),
            }
        )
    return texts, metas


def build_ace_index(session) -> tuple[list[str], list[dict]]:
    """One entry per anomaly finding (all layers including L-1..L-10 legal).

    Legal-layer findings are included automatically once they have been
    persisted to the Anomaly table — either through the wired analyze_document()
    pipeline (v3.8.0+) or via scripts/backfill_legal_findings.py.
    """
    anomalies = session.query(Anomaly).all()
    texts, metas = [], []

    for a in anomalies:
        analysis = session.query(Analysis).filter(Analysis.id == a.analysis_id).first()
        doc = None
        if analysis:
            doc = (
                session.query(Document)
                .filter(Document.document_id == analysis.document_id)
                .first()
            )

        details_str = _safe_details(a.details_json)
        jur = doc.jurisdiction if doc else "unknown"
        doc_title = doc.title if doc else "unknown"
        text = (
            f"[{a.severity.upper()}] {a.issue} | "
            f"Detector: {a.layer} | "
            f"Jurisdiction: {jur} | "
            f"Document: {doc_title} | "
            f"Details: {details_str}"
        )
        texts.append(text)
        metas.append(
            {
                "id": a.anomaly_id,
                "title": f"{jur} / {doc_title}",
                "text": text,  # field name expected by ContextAssembler
                "issue": a.issue,
                "severity": a.severity,
                "layer": a.layer,
                "document_id": analysis.document_id if analysis else None,
                "jurisdiction": jur,
            }
        )

    legal_count = sum(
        1 for a in anomalies if a.layer.startswith("l") and "_" in a.layer
    )
    if legal_count:
        print(f"  {legal_count} legal-layer findings (L-1..L-10) included in ace index")

    return texts, metas


def build_jim_index(session) -> tuple[list[str], list[dict]]:
    """Cross-jurisdiction pattern summaries."""
    from sqlalchemy import func

    patterns = (
        session.query(
            Anomaly.anomaly_id,
            Anomaly.issue,
            Anomaly.layer,
            Anomaly.severity,
            func.count(Anomaly.id).label("count"),
        )
        .group_by(Anomaly.anomaly_id, Anomaly.issue, Anomaly.layer, Anomaly.severity)
        .order_by(func.count(Anomaly.id).desc())
        .all()
    )

    texts, metas = [], []
    for p in patterns:
        juris = (
            session.query(Document.jurisdiction)
            .join(Analysis, Analysis.document_id == Document.document_id)
            .join(Anomaly, Anomaly.analysis_id == Analysis.id)
            .filter(Anomaly.anomaly_id == p.anomaly_id)
            .distinct()
            .all()
        )
        jur_list = [j[0] for j in juris if j[0]]
        text = (
            f"[{p.severity.upper()} PATTERN x{p.count}] {p.issue} | "
            f"Detector: {p.layer} | "
            f"Jurisdictions ({len(jur_list)}): {', '.join(jur_list)}"
        )
        texts.append(text)
        metas.append(
            {
                "id": p.anomaly_id,
                "title": f"Cross-jurisdiction: {p.issue[:60]}",
                "text": text,  # field name expected by ContextAssembler
                "layer": p.layer,
                "severity": p.severity,
                "count": p.count,
                "jurisdictions": jur_list,
            }
        )
    return texts, metas


def fit_and_save(
    collection_name: str,
    texts: list[str],
    metas: list[dict],
    embedder: LocalEmbedder,
    shared_fit: bool = False,
) -> None:
    retriever = Retriever(vectors_dir=VECTORS_DIR)

    if not shared_fit:
        print(f"  Fitting embedder on {len(texts)} documents…")
        embedder.fit(texts)

    for text, meta in zip(texts, metas, strict=False):
        vec = embedder.embed(text)
        retriever.add_vector(vec, meta)

    retriever.save(collection_name)

    # Save vocab for the corpus collection (used as the shared vocabulary)
    # Save vocab for every collection so each can be loaded independently
    vocab_path = VECTORS_DIR / f"{collection_name}_vocab.pkl"
    vocab_data = {
        "max_features": embedder.max_features,
        "norm": embedder.norm,
        "vocabulary": embedder.vectorizer.vocabulary_,
        "idf": embedder.vectorizer.idf_,
    }
    with open(vocab_path, "wb") as f:
        pickle.dump(vocab_data, f)
    # Keep legacy collection_vocab.pkl alias for corpus index
    if collection_name != "collection":
        pass  # each collection already gets <name>_vocab.pkl
    print(f"  Vocab saved -> {vocab_path}")

    print(f"  {len(texts)} vectors -> data/vectors/{collection_name}_vectors.npy")


def main() -> None:
    print("Initialising database…")
    init_db()

    with get_db() as session:
        print("\n[1/3] Building corpus index (one entry per document)…")
        corpus_texts, corpus_metas = build_corpus_index(session)
        embedder = LocalEmbedder(max_features=4096)
        fit_and_save("collection", corpus_texts, corpus_metas, embedder)

        print("\n[2/3] Building ACE anomaly index (DB findings + L-1..L-10 legal)…")
        ace_texts, ace_metas = build_ace_index(session)
        ace_embedder = LocalEmbedder(max_features=4096)
        fit_and_save("ace_collection", ace_texts, ace_metas, ace_embedder)

        print("\n[3/3] Building JIM cross-jurisdiction pattern index…")
        jim_texts, jim_metas = build_jim_index(session)
        jim_embedder = LocalEmbedder(max_features=2048)
        fit_and_save("jim_collection", jim_texts, jim_metas, jim_embedder)

    print("\nIndex build complete.")
    print(f"  corpus   : {len(corpus_texts)} entries")
    print(f"  ace      : {len(ace_texts)} entries")
    print(f"  jim      : {len(jim_texts)} entries")
    print("\nOllama RAG is ready. Set environment variables:")
    print("  $env:RAG_LLM_PROVIDER='ollama'")
    print("  $env:RAG_LLM_MODEL='llama3.1:8b'")
    print("Then start uvicorn and query POST /api/v1/rag/query")


if __name__ == "__main__":
    main()
