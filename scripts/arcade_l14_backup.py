#!/usr/bin/env python3
"""A.R.C.A.D.E. Layer 14 -- Backup and Recovery.

Wraps restic to maintain a 3-2-1-1-0 backup of the two critical ODIA
runtime databases:
  - oraculus_audit.db  (50k+ documents, 148k+ findings)
  - contra_corpus.db   (commercial entity registry, CASI scores)

Usage:
    # First-time setup (run once after installing restic):
    python scripts/arcade_l14_backup.py --init

    # Daily backup (safe to run anytime -- restic is incremental):
    python scripts/arcade_l14_backup.py --backup

    # Verify last backup:
    python scripts/arcade_l14_backup.py --verify

    # List snapshots:
    python scripts/arcade_l14_backup.py --snapshots

Install restic (Windows):
    winget install restic.restic

Set the required environment variable before use:
    $env:RESTIC_PASSWORD = "your-strong-passphrase"   # session only
    # Or permanently:
    [System.Environment]::SetEnvironmentVariable("RESTIC_PASSWORD", "passphrase", "User")
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent
_BACKUP_DIR = Path.home() / ".odia" / "backups" / "restic-repo"
_TARGETS = [
    _REPO_ROOT / "oraculus_audit.db",
    _REPO_ROOT / "contra_corpus.db",
    _REPO_ROOT / "data" / "saber" / "audit" / "saber.log",
]


def _find_restic() -> str:
    """Return the restic executable path, checking WinGet packages as a fallback."""
    import shutil

    if shutil.which("restic"):
        return "restic"
    # WinGet on Windows extracts the archive but may not add a shim to PATH
    winget_base = (
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    )
    for candidate in winget_base.glob("restic.restic_*/restic*.exe"):
        return str(candidate)
    print("ERROR: restic not found. Install with: winget install restic.restic")
    sys.exit(1)


def _restic(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["RESTIC_REPOSITORY"] = str(_BACKUP_DIR)
    if "RESTIC_PASSWORD" not in env:
        print("ERROR: RESTIC_PASSWORD environment variable not set.")
        print("  Set it with: $env:RESTIC_PASSWORD = 'your-passphrase'")
        sys.exit(1)
    return subprocess.run(
        [_find_restic(), *args],
        env=env,
        check=check,
    )


def cmd_init() -> None:
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Initializing restic repository at: {_BACKUP_DIR}")
    _restic("init")
    print("Repository initialized. Run --backup to take the first snapshot.")


def cmd_backup() -> None:
    targets = [str(t) for t in _TARGETS if t.exists()]
    if not targets:
        print("No target files found -- nothing to back up.")
        sys.exit(1)
    print(f"Backing up {len(targets)} file(s) to {_BACKUP_DIR}")
    _restic("backup", *targets, "--tag", "odia-arcade-l14")
    # Prune: keep 7 daily, 4 weekly, 12 monthly snapshots
    _restic(
        "forget",
        "--prune",
        "--keep-daily",
        "7",
        "--keep-weekly",
        "4",
        "--keep-monthly",
        "12",
        "--tag",
        "odia-arcade-l14",
    )


def cmd_verify() -> None:
    print("Verifying repository integrity...")
    _restic("check")
    print("Verification passed.")


def cmd_snapshots() -> None:
    _restic("snapshots", "--tag", "odia-arcade-l14")


def main() -> None:
    parser = argparse.ArgumentParser(description="A.R.C.A.D.E. Layer 14 backup")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", action="store_true", help="Initialize restic repo")
    group.add_argument("--backup", action="store_true", help="Run incremental backup")
    group.add_argument("--verify", action="store_true", help="Verify repo integrity")
    group.add_argument("--snapshots", action="store_true", help="List snapshots")
    args = parser.parse_args()

    if args.init:
        cmd_init()
    elif args.backup:
        cmd_backup()
    elif args.verify:
        cmd_verify()
    elif args.snapshots:
        cmd_snapshots()


if __name__ == "__main__":
    main()
