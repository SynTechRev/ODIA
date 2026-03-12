#!/usr/bin/env python3
"""Search CLI for semantic queries across legal corpora.

This script provides a command-line interface for searching across
ingested legal documents using semantic similarity.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.embeddings import LocalEmbedder
from oraculus_di_auditor.retriever import Retriever


def main():
    """Run semantic search queries on legal corpus."""
    parser = argparse.ArgumentParser(
        description="Search legal documents using semantic similarity"
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Search query text",
    )
    parser.add_argument(
        "--index",
        type=str,
        default="data/vectors/collection",
        help="Path to vector index (without extension)",
    )
    parser.add_argument(
        "--vocab",
        type=str,
        default="data/vectors/collection_vocab.pkl",
        help="Path to vocabulary file",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum similarity threshold (0.0-1.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Use RAG to generate natural language answer (requires LLM)",
    )

    args = parser.parse_args()

    # Check if index exists
    index_path = Path(args.index)
    vocab_path = Path(args.vocab)

    vectors_file = index_path.parent / f"{index_path.name}_vectors.npy"
    metadata_file = index_path.parent / f"{index_path.name}_metadata.npy"

    if not vectors_file.exists() or not metadata_file.exists():
        print(
            f"[FAIL] Vector index not found: {vectors_file} or {metadata_file}",
            file=sys.stderr,
        )
        print("  Run 'python scripts/ingest_and_index.py' first", file=sys.stderr)
        return 1

    if not vocab_path.exists():
        print(f"[FAIL] Vocabulary file not found: {vocab_path}", file=sys.stderr)
        print("  Run 'python scripts/ingest_and_index.py' first", file=sys.stderr)
        return 1

    # RAG mode
    if args.rag:
        try:
            from oraculus_di_auditor.rag import OracRAG
        except ImportError:
            print("[FAIL] RAG module not available", file=sys.stderr)
            return 1

        try:
            orac_rag = OracRAG()
            orac_rag.load_index(index_name=index_path.name, vocab_path=str(vocab_path))
            result = orac_rag.query(args.query, top_k=args.top_k)
        except Exception as e:
            print(f"[FAIL] RAG query failed: {e}", file=sys.stderr)
            return 1

        if "error" in result and result["error"]:
            print(f"[FAIL] Error: {result['error']}", file=sys.stderr)
            return 1

        # Output RAG result
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=" * 70)
            print(f"RAG Answer for: '{args.query}'")
            print("=" * 70)
            print(f"\nAnswer:\n{result['answer']}\n")
            print("\nSources:")
            for source in result["sources"]:
                print(
                    f"  - [{source['corpus_id']}] {source['file']} "
                    f"(score: {source['relevance_score']:.2f})"
                )
            print()
        return 0

    # Standard semantic search mode
    # Load vocabulary and retriever
    try:
        embedder = LocalEmbedder(max_features=2048)
        embedder.load_vocabulary(vocab_path)

        retriever = Retriever()
        retriever.load(index_path.name)
    except Exception as e:
        print(f"[FAIL] Failed to load index: {e}", file=sys.stderr)
        return 1

    # Embed query
    try:
        query_vector = embedder.embed(args.query)
    except Exception as e:
        print(f"[FAIL] Failed to embed query: {e}", file=sys.stderr)
        return 1

    # Search
    results = retriever.search(query_vector, top_k=args.top_k)

    # Convert tuple format to dict format for easier handling
    formatted_results = []
    for idx, score, metadata in results:
        formatted_results.append({"index": idx, "score": score, "metadata": metadata})

    # Filter by threshold
    if args.threshold > 0:
        formatted_results = [
            r for r in formatted_results if r["score"] >= args.threshold
        ]

    # Output results
    if args.json:
        # JSON format
        output = {
            "query": args.query,
            "results": formatted_results,
            "count": len(formatted_results),
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable format
        print("=" * 70)
        print(f"Search Results for: '{args.query}'")
        print("=" * 70)

        if not formatted_results:
            print("\nNo results found.")
        else:
            for i, result in enumerate(formatted_results, 1):
                metadata = result.get("metadata", {})
                score = result.get("score", 0)

                print(f"\n[{i}] {metadata.get('title', 'Untitled')}")
                print(f"    ID:           {metadata.get('id', 'N/A')}")
                print(f"    Jurisdiction: {metadata.get('jurisdiction', 'N/A')}")
                print(f"    Similarity:   {score:.4f}")
                print(f"    Source:       {metadata.get('source', 'N/A')}")

        print(f"\nTotal results: {len(formatted_results)}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
