"""build_courtlistener_corpus.py — Harvest ODIA case law from CourtListener.

Runs ODIA_HARVEST_QUERIES against the CourtListener public API and saves
each case as a CaseLawRecord JSON file in legal/cases/. These files are
the live case law corpus consumed by L-8 (Case Law Currency detector) and
the CourtListenerCorpusLoader.

Rate limits:
  - Anonymous: 5,000 requests/day
  - With free API key: 50,000 requests/day

Set COURTLISTENER_API_KEY environment variable to use your free key:
  https://www.courtlistener.com/sign-in/ → Settings → API Key

Usage:
    .venv\\Scripts\\python scripts\\build_courtlistener_corpus.py --dry-run
    .venv\\Scripts\\python scripts\\build_courtlistener_corpus.py
    .venv\\Scripts\\python scripts\\build_courtlistener_corpus.py --topic cpra
    .venv\\Scripts\\python scripts\\build_courtlistener_corpus.py --list-topics
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Harvest case law from CourtListener")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show queries, don't fetch"
    )
    parser.add_argument(
        "--topic", metavar="TOPIC", help="Only harvest queries with this topic"
    )
    parser.add_argument(
        "--list-topics", action="store_true", help="List available topics"
    )
    parser.add_argument(
        "--cases-dir",
        default=str(_REPO_ROOT / "legal" / "cases"),
        metavar="DIR",
        help="Where to write CaseLawRecord JSON files (default: legal/cases/)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip cases already on disk (default: true)",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="Re-fetch even if case already on disk",
    )
    args = parser.parse_args()

    try:
        from oraculus_di_auditor.legal.courtlistener_client import CourtListenerClient
        from oraculus_di_auditor.legal.courtlistener_corpus import (
            ODIA_HARVEST_QUERIES,
            CourtListenerCorpusLoader,
        )
    except ImportError as exc:
        print(f"ERROR: {exc}\nRun: pip install -e '.[dev]'")
        sys.exit(1)

    queries = ODIA_HARVEST_QUERIES
    if args.topic:
        queries = [q for q in queries if q.get("topic") == args.topic]
        if not queries:
            print(f"ERROR: no queries for topic {args.topic!r}")
            print(
                "Available topics:", sorted({q["topic"] for q in ODIA_HARVEST_QUERIES})
            )
            sys.exit(1)

    if args.list_topics:
        topics = sorted({q["topic"] for q in ODIA_HARVEST_QUERIES})
        print("Available topics:")
        for t in topics:
            count = sum(1 for q in ODIA_HARVEST_QUERIES if q["topic"] == t)
            total_max = sum(
                q["max_results"] for q in ODIA_HARVEST_QUERIES if q["topic"] == t
            )
            print(f"  {t}: {count} queries, up to {total_max} cases")
        return

    api_key = os.environ.get("COURTLISTENER_API_KEY", "").strip()
    print("CourtListener case law corpus builder")
    print(
        f"API key: {'SET (' + api_key[:8] + '...)' if api_key else 'NOT SET (anonymous, 5k/day limit)'}"
    )
    print(f"Cases dir: {args.cases_dir}")
    print(f"Queries: {len(queries)}")
    print(f"Total max cases: {sum(q['max_results'] for q in queries)}")
    print()

    if args.dry_run:
        print("Queries that would run:")
        for q in queries:
            print(
                f"  [{q['topic']}] {q['query']!r} courts={q.get('courts')} max={q['max_results']}"
            )
        return

    cases_dir = Path(args.cases_dir)
    cases_dir.mkdir(parents=True, exist_ok=True)

    client = CourtListenerClient(api_key=api_key or None)
    print("Pinging CourtListener API...")
    if not client.ping():
        print("WARNING: CourtListener API ping failed. Check your network or API key.")

    loader = CourtListenerCorpusLoader(cases_dir=cases_dir, client=client)

    print("Harvesting...")
    stats = loader.harvest(queries=queries, skip_existing=args.skip_existing)

    print()
    print("==== Done ====")
    print(f"Queries run:  {stats['total_queries']}")
    print(f"New cases:    {stats['new_cases']}")
    print(f"Skipped:      {stats['skipped']}")
    print(f"Errors:       {stats['errors']}")

    corpus_stats = loader.statistics()
    print()
    print(f"Corpus now:   {corpus_stats['total_cases']} cases")
    print(f"  with citations: {corpus_stats['with_citations']}")
    print(f"  doctrines: {corpus_stats['doctrines']}")
    if stats["new_cases"] > 0:
        print("\nNext: rebuild RAG index to include new case law")
        print("  .venv\\Scripts\\python scripts\\build_rag_index.py")


if __name__ == "__main__":
    main()
