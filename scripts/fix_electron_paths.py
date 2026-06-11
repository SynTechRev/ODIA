#!/usr/bin/env python3
"""Fix _next/ and autostatic/ asset paths in HTML files for Electron file:// loading.

Two issues are fixed:

1. assetPrefix issue (./_next/ -> ../_next/ for subpages):
   Next.js with assetPrefix="./" emits ./_next/ in all HTML files.  The root
   index.html is fine, but subpages (e.g. out/upload/index.html) get
   ./_next/ which resolves to out/upload/_next/ under file://.  Fixed by
   replacing ./_next/ with ../_next/ in all non-root HTML files.

2. publicPath:"auto" issue (autostatic/chunks/ -> correct path):
   webpack's publicPath:"auto" bakes the literal string "auto" as the
   public-path prefix at build time, so App-Router chunk <script> tags
   are emitted as src="autostatic/chunks/..." (i.e. "auto"+"static/chunks/").
   Those paths do not exist on disk.  The webpack *runtime* correctly
   computes the true public-path at load time from its own script URL,
   but the HTML preload tags must resolve on first parse -- before the
   runtime executes.  If they fail the browser never registers the chunks,
   React cannot mount, and the page stays at opacity:0 (visible as a
   white screen).  Fixed by replacing autostatic/chunks/ with the correct
   relative path in ALL HTML files.

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
            is_root = rel == "."
            fpath = os.path.join(dirpath, fname)
            with open(fpath, encoding="utf-8") as f:
                text = f.read()

            fixed = text

            # Fix 1: ./_next/ -> ../_next/ for subpages (assetPrefix issue).
            # Root index.html already has ./_next/ which resolves correctly.
            if not is_root:
                fixed = fixed.replace("./_next/", rel + "/_next/")

            # Fix 2: autostatic/chunks/ -> correct relative path.
            # "autostatic/" is webpack's literal string "auto" concatenated
            # with "static/" at build time when publicPath is set to "auto".
            # Both root and subpages need this fix.
            if is_root:
                fixed = fixed.replace("autostatic/chunks/", "./_next/static/chunks/")
            else:
                fixed = fixed.replace(
                    "autostatic/chunks/", rel + "/_next/static/chunks/"
                )

            if fixed != text:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(fixed)
                count += 1
                print(f"  Patched: {fpath}")
    print(f"Fixed {count} HTML file(s)")
    return count


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "out"
    fix(out_dir)
