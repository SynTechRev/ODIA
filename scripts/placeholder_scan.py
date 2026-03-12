#!/usr/bin/env python
"""Fail build if placeholder validation logic remains.

Scans source tree for known placeholder patterns that indicate incomplete
constraint enforcement. Exits with code 1 if any matches are found.
"""

from __future__ import annotations

import sys
from pathlib import Path

PATTERNS = [
    "return True  # Placeholder",
    "Simplified rule checking logic",
    "# WARNING: This placeholder",
]

ROOT = Path(__file__).resolve().parent.parent / "src"

matches: list[tuple[str, int, str]] = []

for path in ROOT.rglob("*.py"):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    for lineno, line in enumerate(lines, start=1):
        for pattern in PATTERNS:
            if pattern in line:
                matches.append((str(path), lineno, pattern))

if matches:
    print("Found placeholder validation patterns (must be removed):")
    for file, lineno, pattern in matches:
        print(f" - {file}:{lineno} -> {pattern}")
    sys.exit(1)
else:
    print("Placeholder scan passed: no placeholder validation patterns present.")
    sys.exit(0)
