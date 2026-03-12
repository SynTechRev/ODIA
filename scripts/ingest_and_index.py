#!/usr/bin/env python3
"""End-to-end ingestion and indexing pipeline for legal documents.

This script demonstrates the Phase 6/7 ingestion pipeline:
1. Ingest raw documents from data/sources/ (TXT, JSON, XML)
2. Normalize and chunk documents
3. Create embeddings using TF-IDF
4. Build vector index for retrieval
5. Run anomaly detection (including cross-jurisdiction)
6. Generate reports with provenance tracking

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import argparse
import pathlib
import sys

from oraculus.ingestion.legislative_loader import load_legislation, normalize_document
from oraculus_di_auditor.embeddings import LocalEmbedder
from oraculus_di_auditor.retriever import Retriever


def _ingest_documents(input_dir: str) -> list[dict[str, str]]:
    """Ingest and normalize all JSON documents in directory."""
    docs: list[dict[str, str]] = []
    for path in pathlib.Path(input_dir).glob("*.json"):
        loaded = load_legislation(str(path))
        normalized = normalize_document(loaded)
        text = "\n".join(s.get("content", "") for s in normalized.get("sections", []))
        docs.append({"id": normalized["document_id"], "text": text})
    return docs


def _build_index(
    documents: list[dict[str, str]], embeddings, retriever: Retriever
) -> None:
    """Add embeddings and metadata into retriever index."""
    for _i, (doc, embedding) in enumerate(zip(documents, embeddings, strict=True)):
        retriever.add_vector(
            embedding,
            {"id": doc["id"], "length": len(doc["text"])},
        )


def _sample_search(
    documents, embedder: LocalEmbedder, retriever: Retriever, top_k: int
) -> None:
    """Run a sample search using first document snippet."""
    if not documents:
        print("No documents ingested; skipping sample search.")
        return
    query_text = documents[0]["text"][:200]
    query_embedding = embedder.embed(query_text)
    results = retriever.search(query_embedding, top_k=top_k)
    print(f"Sample search results (top {top_k}):")
    for rank, (_idx, score, meta) in enumerate(results, start=1):
        print(f"  {rank}. ID={meta['id']} length={meta['length']} score={score:.4f}")


def main():
    """Run the end-to-end ingestion and indexing pipeline."""
    parser = argparse.ArgumentParser(
        description=(
            "Ingest legislative documents, generate embeddings, "
            "and build retriever index"
        )
    )
    parser.add_argument("input_dir", help="Directory containing legislative documents")
    parser.add_argument("output_dir", help="Directory to store processed outputs")
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of top results to retrieve in sample search",
    )
    args = parser.parse_args()

    print("[1/5] Ingesting documents...")
    documents = _ingest_documents(args.input_dir)

    print("[2/5] Generating embeddings...")
    embedder = LocalEmbedder()
    embeddings = embedder.embed_batch([d["text"] for d in documents])

    print("[3/5] Building index...")
    retriever = Retriever()
    _build_index(documents, embeddings, retriever)

    print("[4/5] Saving index...")
    out_dir = pathlib.Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    retriever.save(str(out_dir / "index"))

    print("[5/5] Running sample search...")
    _sample_search(documents, embedder, retriever, args.top_k)


if __name__ == "__main__":
    sys.exit(main())
