// ============================================================================
// build-icons.mjs — Rasterize the Oraculus mark into all PNG sizes.
//
// v2.7.10 — source switched from the procedural SVG to the actual brand
// reference artwork at docs/brand/reference/reference_5_gold-swirl-
// icon-source.png. The SVG approximation read as a stylized "C/E" curve
// in the v2.7.9 builds; the reference PNG is a fluid gold paint-swirl
// with white-paint counterpoint on dark stone — the v2.7.9 sign-off
// review flagged this gap.
//
// The reference is 270x271; sharp upscales with high-quality lanczos3
// for the 512/1024 PWA + desktop variants. The maskable variant gets
// 12% inner padding so the swirl stays inside Android's adaptive-icon
// safe zone when the launcher applies a circle/squircle mask.
//
// `electron-builder` auto-derives .ico (Windows) and .icns (macOS) from
// the master 1024×1024 desktop/resources/icon.png at build time.
//
// Run from repo root:
//   cd frontend && npm run build:icons
//
// Inputs:
//   docs/brand/reference/reference_5_gold-swirl-icon-source.png
//   frontend/public/icons/oraculus-mark.svg              (kept; used by
//                                                         the in-app SVG
//                                                         component for
//                                                         the 16-24px
//                                                         sidebar glyph)
//
// Outputs:
//   frontend/public/icons/icon-192.png            (PWA standard)
//   frontend/public/icons/icon-512.png            (PWA standard)
//   frontend/public/icons/icon-maskable-512.png   (PWA Android adaptive)
//   desktop/resources/icon.png                    (1024px master raster)
// ============================================================================

import { mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../..');

const SRC = path.join(
  repoRoot,
  'docs/brand/reference/reference_5_gold-swirl-icon-source.png',
);
const ICONS_DIR = path.join(repoRoot, 'frontend/public/icons');
const DESKTOP_DIR = path.join(repoRoot, 'desktop/resources');

if (!existsSync(SRC)) {
  console.error(`ERROR: source artwork not found at ${SRC}`);
  console.error('       Restore docs/brand/reference/ from the brand bundle.');
  process.exit(1);
}

await mkdir(ICONS_DIR, { recursive: true });
await mkdir(DESKTOP_DIR, { recursive: true });

// Smoke-950 background fill behind any transparent margin (matches the
// gemstone palette body background). The reference itself is opaque so
// this only fires on the maskable padding.
const SMOKE_950 = { r: 7, g: 7, b: 10, alpha: 1 };

const targets = [
  {
    out: path.join(ICONS_DIR, 'icon-192.png'),
    size: 192,
    padding: 0,
    label: 'PWA 192',
  },
  {
    out: path.join(ICONS_DIR, 'icon-512.png'),
    size: 512,
    padding: 0,
    label: 'PWA 512',
  },
  {
    // Maskable: pad the swirl into the inner 76% so launcher masks
    // (circle, squircle, teardrop) don't crop the artwork.
    out: path.join(ICONS_DIR, 'icon-maskable-512.png'),
    size: 512,
    padding: 0.12, // 12% on every side → 76% safe zone
    label: 'PWA maskable 512',
  },
  {
    out: path.join(DESKTOP_DIR, 'icon.png'),
    size: 1024,
    padding: 0,
    label: 'Desktop master 1024',
  },
];

for (const { out, size, padding, label } of targets) {
  if (padding > 0) {
    const inner = Math.round(size * (1 - 2 * padding));
    const margin = Math.round((size - inner) / 2);
    const innerBuffer = await sharp(SRC)
      .resize(inner, inner, { fit: 'contain', background: SMOKE_950, kernel: 'lanczos3' })
      .png()
      .toBuffer();
    await sharp({
      create: { width: size, height: size, channels: 4, background: SMOKE_950 },
    })
      .composite([{ input: innerBuffer, top: margin, left: margin }])
      .png({ compressionLevel: 9 })
      .toFile(out);
  } else {
    await sharp(SRC)
      .resize(size, size, { fit: 'contain', background: SMOKE_950, kernel: 'lanczos3' })
      .png({ compressionLevel: 9 })
      .toFile(out);
  }
  console.log(`[icons] ${label.padEnd(28)} → ${path.relative(repoRoot, out)}`);
}

console.log(
  '[icons] Done. Electron-builder will derive .ico + .icns from desktop/resources/icon.png at build time.',
);
