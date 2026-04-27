#!/usr/bin/env bash
#
# build-icons.sh — regenerate the application raster icon set from the
# Oraculus mark SVG.
#
# Usage:
#   ./scripts/build-icons.sh           # regenerate PNGs + .ico
#   ./scripts/build-icons.sh macos     # additionally build .icns (macOS only)
#
# Dependencies:
#   - rsvg-convert (librsvg2-bin on Linux, librsvg via Homebrew on macOS)
#   - convert (ImageMagick)
#   - iconutil (macOS only, for .icns)
#
# Outputs:
#   frontend/public/icons/icon-192.png
#   frontend/public/icons/icon-512.png
#   frontend/public/icons/icon-maskable-512.png
#   desktop/resources/icon.png         (1024x1024)
#   desktop/resources/icon.ico         (multi-size Windows icon)
#   desktop/resources/icon.icns        (macOS only)

set -euo pipefail

SRC="frontend/public/icons/oraculus-mark.svg"
PUB="frontend/public/icons"
DESK="desktop/resources"

# --- preflight ---------------------------------------------------------------
if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "ERROR: rsvg-convert not found. Install with:"
  echo "  Ubuntu/Debian:  sudo apt install librsvg2-bin"
  echo "  macOS:          brew install librsvg"
  echo "  Windows:        choco install rsvg-convert"
  exit 1
fi

if ! command -v convert >/dev/null 2>&1; then
  echo "ERROR: ImageMagick 'convert' not found. Install with:"
  echo "  Ubuntu/Debian:  sudo apt install imagemagick"
  echo "  macOS:          brew install imagemagick"
  exit 1
fi

if [ ! -f "$SRC" ]; then
  echo "ERROR: source SVG missing at $SRC"
  exit 1
fi

mkdir -p "$PUB" "$DESK"

# --- PNG raster set ----------------------------------------------------------
echo "Rendering PNG raster set..."
rsvg-convert -w 192  -h 192  "$SRC" -o "$PUB/icon-192.png"
rsvg-convert -w 512  -h 512  "$SRC" -o "$PUB/icon-512.png"
cp "$PUB/icon-512.png" "$PUB/icon-maskable-512.png"
rsvg-convert -w 1024 -h 1024 "$SRC" -o "$DESK/icon.png"
echo "  $PUB/icon-192.png             $(du -h $PUB/icon-192.png | cut -f1)"
echo "  $PUB/icon-512.png             $(du -h $PUB/icon-512.png | cut -f1)"
echo "  $PUB/icon-maskable-512.png    $(du -h $PUB/icon-maskable-512.png | cut -f1)"
echo "  $DESK/icon.png (1024)         $(du -h $DESK/icon.png | cut -f1)"

# --- Windows .ico ------------------------------------------------------------
echo "Building Windows .ico (multi-size)..."
convert "$DESK/icon.png" \
  -define icon:auto-resize=16,32,48,64,128,256 \
  "$DESK/icon.ico"
echo "  $DESK/icon.ico                $(du -h $DESK/icon.ico | cut -f1)"

# --- macOS .icns (optional) --------------------------------------------------
if [[ "${1:-}" == "macos" ]]; then
  if [[ "$(uname)" != "Darwin" ]]; then
    echo "WARNING: 'macos' option requested but not running on macOS. Skipping .icns."
    exit 0
  fi
  if ! command -v iconutil >/dev/null 2>&1; then
    echo "ERROR: iconutil not found (this is macOS-only)."
    exit 1
  fi

  echo "Building macOS .icns..."
  ICONSET=$(mktemp -d)/icon.iconset
  mkdir -p "$ICONSET"
  for s in 16 32 64 128 256 512 1024; do
    rsvg-convert -w $s -h $s "$SRC" -o "$ICONSET/icon_${s}x${s}.png"
    d=$((s*2))
    rsvg-convert -w $d -h $d "$SRC" -o "$ICONSET/icon_${s}x${s}@2x.png"
  done
  iconutil -c icns "$ICONSET" -o "$DESK/icon.icns"
  rm -rf "$ICONSET"
  echo "  $DESK/icon.icns               $(du -h $DESK/icon.icns | cut -f1)"
fi

echo "Done."
