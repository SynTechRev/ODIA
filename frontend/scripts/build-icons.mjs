// ============================================================================
// build-icons.mjs — Rasterize the Oraculus mark SVG into all PNG sizes.
//
// Why Node + sharp: rsvg-convert + ImageMagick + iconutil aren't reliably
// available cross-platform (Windows in particular). sharp ships with the
// Next.js frontend (transitive dep) so it's always present once
// `npm install` has been run in frontend/.
//
// `electron-builder` auto-derives .ico (Windows) and .icns (macOS) from
// the master 1024×1024 desktop/resources/icon.png at build time. So we
// only need to rasterize PNGs here — the platform-specific containers
// are produced by the Electron build itself.
//
// Run from repo root:
//   node scripts/build-icons.mjs
// or via npm:
//   cd frontend && npm run build:icons
//
// Inputs:
//   frontend/public/icons/oraculus-mark.svg
//
// Outputs:
//   frontend/public/icons/icon-192.png            (PWA standard)
//   frontend/public/icons/icon-512.png            (PWA standard)
//   frontend/public/icons/icon-maskable-512.png   (PWA Android adaptive)
//   desktop/resources/icon.png                    (1024px master raster)
// ============================================================================

import { mkdir } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Script lives at frontend/scripts/build-icons.mjs; repo root is two up.
const repoRoot = path.resolve(__dirname, '../..');

const SRC = path.join(repoRoot, 'frontend/public/icons/oraculus-mark.svg');
const ICONS_DIR = path.join(repoRoot, 'frontend/public/icons');
const DESKTOP_DIR = path.join(repoRoot, 'desktop/resources');

if (!existsSync(SRC)) {
  console.error(`ERROR: source SVG not found at ${SRC}`);
  process.exit(1);
}

await mkdir(ICONS_DIR, { recursive: true });
await mkdir(DESKTOP_DIR, { recursive: true });

const svgBuffer = readFileSync(SRC);

const targets = [
  { out: path.join(ICONS_DIR, 'icon-192.png'),          size: 192,  label: 'PWA 192' },
  { out: path.join(ICONS_DIR, 'icon-512.png'),          size: 512,  label: 'PWA 512' },
  { out: path.join(ICONS_DIR, 'icon-maskable-512.png'), size: 512,  label: 'PWA maskable 512' },
  { out: path.join(DESKTOP_DIR, 'icon.png'),            size: 1024, label: 'Desktop master 1024' },
];

for (const { out, size, label } of targets) {
  // density 384 = 16x the default 24 — keeps the gradient + filter
  // detail intact at large output sizes. sharp's libvips renderer
  // preserves SVG gradients cleanly (unlike ImageMagick's MSVG).
  await sharp(svgBuffer, { density: 384 })
    .resize(size, size, { fit: 'contain', background: { r: 7, g: 7, b: 10, alpha: 1 } })
    .png({ compressionLevel: 9 })
    .toFile(out);
  console.log(`[icons] ${label.padEnd(28)} → ${path.relative(repoRoot, out)}`);
}

console.log('[icons] Done. Electron-builder will derive .ico + .icns from desktop/resources/icon.png at build time.');
