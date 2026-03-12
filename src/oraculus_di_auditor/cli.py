"""Command-line interface for Oraculus DI Auditor.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

import argparse

from .ingest import ingest_folder


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Oraculus DI Auditor - Legal Document Ingestion and Analysis"
    )
    subparsers = parser.add_subparsers(dest="cmd", help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents from folder")
    ingest_parser.add_argument(
        "--source", default="data/sources", help="Source directory path"
    )

    args = parser.parse_args()

    if args.cmd == "ingest":
        ingest_folder(args.source)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
