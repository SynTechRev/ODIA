#!/usr/bin/env python3
"""Migrate oraculus_audit.db to the Electron app's userData directory.

v3.8.2 changed the desktop backend to store its database at:
  Windows: %APPDATA%\ODIA\oraculus_audit.db
  macOS:   ~/Library/Application Support/ODIA/oraculus_audit.db
  Linux:   ~/.config/ODIA/oraculus_audit.db

Previously, the database was created adjacent to the PyInstaller bundle at:
  Windows: C:\\Users\\<user>\\AppData\\Local\\Programs\\ODIA\\oraculus_audit.db

This script merges the dev/source database (which holds the full audit corpus)
with the old install database (which may have recent upload audits), writing
the combined result to the new userData path.

Usage:
    python scripts/migrate_db_to_userdata.py

Optional flags:
    --src   PATH   Source DB to copy from (default: auto-detected)
    --dest  PATH   Destination DB path (default: auto-detected userData path)
    --dry-run      Print what would happen without writing anything
"""

import argparse
import os
import platform
import shutil
import sqlite3
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_src() -> Path:
    """The dev/source database — lives at the repo root."""
    return _repo_root() / "oraculus_audit.db"


def _default_dest() -> Path:
    """The Electron app userData path for the current OS."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "ODIA" / "oraculus_audit.db"
    elif system == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "ODIA"
            / "oraculus_audit.db"
        )
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "ODIA" / "oraculus_audit.db"
    raise RuntimeError(f"Cannot determine userData path for platform: {system}")


def _count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:
        return 0


def _stats(path: Path) -> str:
    if not path.exists():
        return "NOT FOUND"
    try:
        conn = sqlite3.connect(path)
        docs = _count(conn, "documents")
        analyses = _count(conn, "analyses")
        anomalies = _count(conn, "anomalies")
        jobs = _count(conn, "mesh_execution_jobs")
        conn.close()
        size_kb = path.stat().st_size // 1024
        return (
            f"{size_kb} KB — {docs} docs / {analyses} analyses / "
            f"{anomalies} anomalies / {jobs} jobs"
        )
    except Exception as e:
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# Merge logic — insert rows from src that don't exist in dest (by primary key
# or natural key) so no data is overwritten or duplicated.
# ---------------------------------------------------------------------------


def _merge(src_path: Path, dest_path: Path, dry_run: bool) -> None:
    print(f"\nSource:      {src_path}")
    print(f"  {_stats(src_path)}")
    print(f"\nDestination: {dest_path}")
    print(f"  {_stats(dest_path)}")

    if not src_path.exists():
        print("\nERROR: source database not found — nothing to migrate.")
        sys.exit(1)

    if dry_run:
        print("\n[dry-run] No changes written.")
        return

    # Ensure destination directory exists.
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # If destination doesn't exist at all, just copy the source directly.
    if not dest_path.exists():
        print(f"\nDestination does not exist — copying source to destination…")
        shutil.copy2(src_path, dest_path)
        print(f"Done. {_stats(dest_path)}")
        return

    # Both exist — merge: attach src to dest and INSERT OR IGNORE.
    print(
        "\nBoth databases exist — merging (INSERT OR IGNORE by document_id / sha256)…"
    )

    dest_conn = sqlite3.connect(dest_path)
    dest_conn.execute("PRAGMA journal_mode=WAL")

    src_abs = str(src_path.resolve()).replace("\\", "/")
    dest_conn.execute(f"ATTACH DATABASE '{src_abs}' AS src")

    tables = [
        ("documents", "document_id"),
        ("analyses", None),  # no unique natural key — skip merging
        ("anomalies", None),  # tied to analysis IDs — skip merging
        ("mesh_execution_jobs", "job_id"),
    ]

    for table, natural_key in tables:
        if natural_key is None:
            print(
                f"  {table}: skipped (no stable natural key — run a fresh audit to populate)"
            )
            continue
        try:
            dest_conn.execute(
                f"INSERT OR IGNORE INTO {table} " f"SELECT * FROM src.{table}"
            )
            dest_conn.commit()
            after = _count(dest_conn, table)
            print(f"  {table}: merged → {after} rows total")
        except Exception as e:
            print(f"  {table}: WARNING — {e}")

    dest_conn.execute("DETACH DATABASE src")
    dest_conn.close()

    print(f"\nFinal destination state:")
    print(f"  {_stats(dest_path)}")
    print(
        "\nNOTE: analyses and anomalies were NOT merged from the source "
        "(they reference analysis IDs that differ between databases). "
        "Re-run the audit pipeline or upload a batch to repopulate these tables "
        "with fresh findings from the merged document set."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=None, help="Source DB path")
    parser.add_argument("--dest", type=Path, default=None, help="Destination DB path")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()

    src = args.src or _default_src()
    dest = args.dest or _default_dest()

    print("=" * 60)
    print("O.D.I.A. — Database Migration to userData")
    print("=" * 60)
    _merge(src, dest, dry_run=args.dry_run)
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
