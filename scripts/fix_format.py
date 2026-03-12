#!/usr/bin/env python
"""
Run pre-commit on the full repo and auto-commit any formatting/lint fixes.
Cross-platform alternative to shell scripts for consistent developer workflow.
"""
from __future__ import annotations

import subprocess
import sys
from shutil import which


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def main() -> int:
    # Ensure pip and pre-commit are available
    py = sys.executable
    run([py, "-m", "pip", "install", "--upgrade", "pip"])  # best-effort
    run([py, "-m", "pip", "install", "pre-commit"])  # idempotent

    # Verify pre-commit availability
    if which("pre-commit") is None:
        print("pre-commit not found on PATH; install failed.", file=sys.stderr)
        return 1

    # Run pre-commit on all files; ignore exit code (we commit changes below if any)
    run(
        ["pre-commit", "run", "--all-files", "--show-diff-on-failure"]
    )  # formatting/lint run

    # Check git status for changes
    try:
        changed = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip()
    except Exception as e:  # pragma: no cover
        print(f"Failed to check git status: {e}", file=sys.stderr)
        return 1

    if changed:
        print("Detected changes from pre-commit; committing...")
        if run(["git", "add", "."]) != 0:
            return 1
        if (
            run(["git", "commit", "-m", "chore: apply pre-commit formatting fixes"])
            != 0
        ):
            return 1
        print("Committed formatting fixes. Push to remote with: git push")
    else:
        print("No changes from pre-commit.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
