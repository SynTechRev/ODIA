#!/usr/bin/env python3
"""Fix _next/ asset paths in non-root subpage HTML files for Electron file:// loading.

When Next.js builds a static export with assetPrefix="./" the root index.html
is correct, but subpages at e.g. out/upload/index.html get ./_next/ which
resolves to out/upload/_next/ (nonexistent) under file://.  This script
rewrites ./_next/ -> ../_next/ in every non-root HTML file.

Run from the frontend/ directory:
    python3 ../scripts/fix_electron_paths.py
"""

import os
import sys


def fix(out_dir: str = "out") -> int:
    count = 0
    for dirpath, _, filenames in os.walk(out_dir):
        for fname in filenames:
            if not fname.endswith(".html"):
                continue
            rel = os.path.relpath(out_dir, dirpath).replace("\\", "/")
            if rel == ".":
                continue  # root index.html: assetPrefix already correct
            fpath = os.path.join(dirpath, fname)
            with open(fpath, encoding="utf-8") as f:
                text = f.read()
            fixed = text.replace("./_next/", rel + "/_next/")
            if fixed != text:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(fixed)
                count += 1
                print(f"  Patched: {fpath}")
    print(f"Fixed {count} subpage HTML file(s)")
    return count


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "out"
    fix(out_dir)
