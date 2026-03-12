#!/usr/bin/env python3
"""Rebuild indexes for corpus directories.

This script rebuilds index.json files for individual corpora
and the global index at the corpus root.

Usage:
    python scripts/rebuild_index.py [--corpus-root CORPUS_ROOT] [--hist-id HIST_ID]

Author: GitHub Copilot Agent
Date: 2025-11-25
"""

import argparse
import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import (
    HIST_FILES,
    build_corpus_index,
    rebuild_all_indexes,
)


def main():
    """Rebuild corpus indexes."""
    parser = argparse.ArgumentParser(
        description="Rebuild index.json files for corpus directories"
    )
    parser.add_argument(
        "--corpus-root",
        type=str,
        default="oraculus/corpus",
        help="Root directory for corpus files",
    )
    parser.add_argument(
        "--hist-id",
        type=str,
        default=None,
        help="Specific HIST ID to rebuild (e.g., HIST-6225). Rebuilds all if not specified.",
    )
    parser.add_argument(
        "--global-only",
        action="store_true",
        help="Only rebuild the global index",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()

    if not corpus_root.exists():
        print(f"Error: Corpus root not found: {corpus_root}")
        return 1

    if args.hist_id:
        if args.hist_id not in HIST_FILES:
            print(f"Error: Unknown HIST ID: {args.hist_id}")
            print(f"Valid IDs: {', '.join(sorted(HIST_FILES.keys()))}")
            return 1

        corpus_path = corpus_root / args.hist_id
        if not corpus_path.exists():
            print(f"Error: Corpus directory not found: {corpus_path}")
            return 1

        print(f"Rebuilding index for {args.hist_id}...")
        import json

        index = build_corpus_index(corpus_path)
        index_file = corpus_path / "index.json"
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)

        print(f"  Total files indexed: {index['statistics']['total_files']}")
        if args.verbose and index["statistics"]["by_type"]:
            print("  By type:")
            for file_type, count in index["statistics"]["by_type"].items():
                print(f"    {file_type}: {count}")
    else:
        print("Rebuilding all indexes...")
        results = rebuild_all_indexes(corpus_root)

        for hist_id, info in results["corpus_indexes"].items():
            print(f"  {hist_id}: {info['total_files']} files indexed")
            if args.verbose and info["by_type"]:
                for file_type, count in info["by_type"].items():
                    print(f"    {file_type}: {count}")

        if results["global_index"]:
            print(
                f"\nGlobal index: {results['global_index']['total_corpora']} corpora, "
                f"{results['global_index']['total_files']} total files"
            )

    print("\nIndex rebuild complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
