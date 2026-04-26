#!/usr/bin/env bash
# ============================================================================
# build-icons.sh — Rasterize the Oraculus mark SVG into all icon sizes.
#
# Run this whenever frontend/public/icons/oraculus-mark.svg changes so
# the rasterized PWA + Electron icon variants stay in sync with the
# source artwork.
#
# Requirements
# ------------
#   • rsvg-convert (librsvg2-bin) — preserves SVG gradients faithfully;
#     ImageMagick's SVG renderer drops them, so do NOT substitute.
#       Ubuntu / Debian : sudo apt install librsvg2-bin imagemagick
#       macOS           : brew install librsvg imagemagick
#       Windows         : install via WSL2 + apt, or Chocolatey:
#                          choco install rsvg-convert imagemagick
#
#   • ImageMagick (`convert`) — for the multi-size Windows .ico bundle.
#
#   • iconutil (macOS only) — for the .icns Apple icon container. The
#     script silently skips .icns generation on non-Darwin hosts; run
#     this script on a Mac at least once per release to refresh
#     desktop/resources/icon.icns and commit the result.
#
# Outputs (paths relative to repo root)
# -------------------------------------
#   frontend/public/icons/icon-192.png            PWA standard
#   frontend/public/icons/icon-512.png            PWA standard
#   frontend/public/icons/icon-maskable-512.png   PWA Android adaptive
#   desktop/resources/icon.png                    1024px master raster
#   desktop/resources/icon.ico                    multi-size Windows
#   desktop/resources/icon.icns                   multi-size macOS (Mac only)
#
# Usage
# -----
#   ./scripts/build-icons.sh
# ============================================================================

set -euo pipefail

# Resolve repo root regardless of where the script is invoked from.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/frontend/public/icons/oraculus-mark.svg"
ICONS="$REPO_ROOT/frontend/public/icons"
DESKTOP="$REPO_ROOT/desktop/resources"

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: source SVG not found at $SRC" >&2
  exit 1
fi

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "ERROR: rsvg-convert is required (do NOT substitute ImageMagick" >&2
  echo "       — its SVG renderer drops gradients). Install:" >&2
  echo "         apt install librsvg2-bin   (Linux)" >&2
  echo "         brew install librsvg       (macOS)" >&2
  exit 1
fi

mkdir -p "$ICONS" "$DESKTOP"

echo "[icons] PWA standard 192/512..."
rsvg-convert -w 192  -h 192  "$SRC" -o "$ICONS/icon-192.png"
rsvg-convert -w 512  -h 512  "$SRC" -o "$ICONS/icon-512.png"
rsvg-convert -w 512  -h 512  "$SRC" -o "$ICONS/icon-maskable-512.png"

echo "[icons] Desktop master 1024..."
rsvg-convert -w 1024 -h 1024 "$SRC" -o "$DESKTOP/icon.png"

# Windows .ico — multi-size resource
if command -v convert >/dev/null 2>&1; then
  echo "[icons] Windows .ico (multi-size)..."
  convert "$ICONS/icon-512.png" \
    -define icon:auto-resize=16,32,48,64,128,256 \
    "$DESKTOP/icon.ico"
else
  echo "[icons] WARN: ImageMagick 'convert' not found; skipping .ico" >&2
  echo "             Install ImageMagick to regenerate desktop/resources/icon.ico" >&2
fi

# macOS .icns — multi-size Apple icon container, requires iconutil
if [[ "$(uname)" == "Darwin" ]]; then
  echo "[icons] macOS .icns (multi-size, requires iconutil)..."
  ICONSET="$(mktemp -d)/icon.iconset"
  mkdir -p "$ICONSET"
  for s in 16 32 64 128 256 512 1024; do
    rsvg-convert -w $s -h $s "$SRC" -o "$ICONSET/icon_${s}x${s}.png"
    d=$((s * 2))
    rsvg-convert -w $d -h $d "$SRC" -o "$ICONSET/icon_${s}x${s}@2x.png"
  done
  iconutil -c icns "$ICONSET" -o "$DESKTOP/icon.icns"
else
  echo "[icons] Skipping .icns (requires macOS iconutil)." >&2
  echo "             Run this script on a Mac to refresh desktop/resources/icon.icns" >&2
fi

echo "[icons] Done. Generated:"
file "$ICONS"/icon-192.png "$ICONS"/icon-512.png "$ICONS"/icon-maskable-512.png "$DESKTOP"/icon.png 2>/dev/null || true
[[ -f "$DESKTOP/icon.ico" ]]  && file "$DESKTOP/icon.ico"
[[ -f "$DESKTOP/icon.icns" ]] && file "$DESKTOP/icon.icns"
