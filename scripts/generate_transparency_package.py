#!/usr/bin/env python3
"""Transparency Release Package generator.

This script lives at scripts/ level (one level below repo root).
It delegates all logic to scripts/examples/generate_transparency_package.py.
"""

import runpy
from pathlib import Path

_impl_path = Path(__file__).parent / "examples" / "generate_transparency_package.py"

if __name__ == "__main__":
    runpy.run_path(str(_impl_path), run_name="__main__")
