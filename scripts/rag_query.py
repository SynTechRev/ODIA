#!/usr/bin/env python3
"""RAG query CLI for natural language document querying.

This script provides a command-line interface for asking natural language
questions about the legislative corpus using RAG (Retrieval-Augmented Generation).

Author: GitHub Copilot Agent
Date: 2025-12-18

Examples:
    # Basic query
    python scripts/rag_query.py --query "What Axon contracts exist?"

    # With custom top_k
    python scripts/rag_query.py --query "Show surveillance vendors" --top-k 10

    # JSON output
    python scripts/rag_query.py --query "Fourth Amendment issues" --json

    # Filter by corpus
    python scripts/rag_query.py \
        --query "Show body-worn camera contracts" \
        --corpus-filter "#23-0148,#23-0214"

    # Dry run (retrieval only, no LLM)
    python scripts/rag_query.py --query "test query" --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.rag import OracRAG


def main():
    """Run RAG query from command line."""
    parser = argparse.ArgumentParser(
        description="Query legislative documents using natural language (RAG)"
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Natural language question",
    )
    parser.add_argument(
        "--index",
        type=str,
        default="collection",
        help="Vector index name (default: collection)",
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
        help="Number of documents to retrieve (default: 5)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Minimum similarity threshold (default: 0.3)",
    )
    parser.add_argument(
        "--corpus-filter",
        type=str,
        help="Comma-separated list of corpus IDs to filter by",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (for JSON output)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Retrieval only, skip LLM generation (useful for testing)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="LLM provider (openai, anthropic, ollama). Defaults to config.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="LLM model name. Defaults to config.",
    )

    args = parser.parse_args()

    # Check if index exists
    index_path = Path(f"data/vectors/{args.index}_vectors.npy")
    if not index_path.exists():
        print(
            f"[FAIL] Vector index not found: {index_path}",
            file=sys.stderr,
        )
        print("  Run 'python scripts/ingest_and_index.py' first", file=sys.stderr)
        return 1

    vocab_path = Path(args.vocab)
    if not vocab_path.exists():
        print(f"[FAIL] Vocabulary file not found: {vocab_path}", file=sys.stderr)
        print("  Run 'python scripts/ingest_and_index.py' first", file=sys.stderr)
        return 1

    # Initialize RAG system
    try:
        kwargs = {}
        if args.provider:
            kwargs["llm_provider"] = args.provider
        if args.model:
            kwargs["llm_model"] = args.model

        orac_rag = OracRAG(**kwargs)
        orac_rag.load_index(index_name=args.index, vocab_path=str(vocab_path))
    except Exception as e:
        print(f"[FAIL] Failed to initialize RAG: {e}", file=sys.stderr)
        return 1

    # Override LLM to None for dry-run
    if args.dry_run:
        orac_rag.llm = None
        print("🔍 Dry run mode: retrieval only, no LLM generation\n")

    # Execute query
    try:
        if args.corpus_filter:
            corpus_ids = [cid.strip() for cid in args.corpus_filter.split(",")]
            result = orac_rag.query_with_filter(
                question=args.query,
                corpus_ids=corpus_ids,
                top_k=args.top_k,
            )
        else:
            result = orac_rag.query(
                question=args.query,
                top_k=args.top_k,
                include_sources=True,
                threshold=args.threshold,
            )
    except Exception as e:
        print(f"[FAIL] Query failed: {e}", file=sys.stderr)
        return 1

    # Handle errors
    if "error" in result and result["error"]:
        print(f"[FAIL] Error: {result['error']}", file=sys.stderr)
        return 1

    # Output results
    if args.json:
        output_data = {
            "query": args.query,
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"],
        }

        if args.output:
            # Write to file
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
            print(f"[OK] Results written to {output_path}")
        else:
            # Print to stdout
            print(json.dumps(output_data, indent=2))
    else:
        # Human-readable format
        print("=" * 70)
        print(f"Query: {args.query}")
        print("=" * 70)
        print(f"\nAnswer:\n{result['answer']}\n")

        if result["sources"]:
            print(f"\nSources (Confidence: {result['confidence']:.2f}):")
            print("-" * 70)
            for i, source in enumerate(result["sources"], 1):
                print(f"\n[{i}] {source['title']}")
                print(f"    ID:        {source['corpus_id']}")
                print(f"    File:      {source['file']}")
                print(f"    Relevance: {source['relevance_score']:.3f}")
                if source.get("snippet"):
                    print(f"    Snippet:   {source['snippet']}")

        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
