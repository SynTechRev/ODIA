/**
 * OraculusMarkIcon — gold swirl mark for the Oraculus Decimus brand.
 *
 * Replaces OctopusMarkIcon as the primary brand glyph in the top-left
 * application chrome. The two deprecated aliases (StrategyMarkIcon,
 * OdiaMarkIcon) are repointed to OraculusMarkIcon so existing call
 * sites keep compiling.
 *
 * Design notes
 * ------------
 * The mark is a single golden swirl — a thick crescent inner curve that
 * tapers as it rotates, ringed by lighter wisps and a flick of paint
 * splatter. It reads as a precision-instrument glyph at 16px in the
 * sidebar and scales cleanly to 64px+ on the splash and tray icons.
 *
 * Geometry: viewBox 24×24, three concentric arcs (heavy primary,
 * mid wisp, outer wisp) plus four splatter dots at gold-200 opacity.
 * No fills except the splatter — strokes only — so the glyph inherits
 * `currentColor` from CSS like every other icon in this family.
 *
 * Token mapping (when used inline, parent passes color via `style`):
 *   • Primary curve  → var(--gold-200)         (highest catch-light)
 *   • Mid wisp       → var(--gold-400) at 0.7  (primary gold)
 *   • Outer wisp     → var(--gold-500) at 0.4  (mid-tone)
 *   • Splatter dots  → var(--gold-300)         (highlight)
 *
 * For the application icon (Electron BrowserWindow, PWA manifest,
 * Capacitor), use the standalone `oraculus-mark.svg` asset in
 * `frontend/public/icons/` — the SVG is rasterised at build time into
 * 192/512/maskable variants. See docs/BRAND.md.
 */

import React from 'react';
import { IconBase } from './IconBase';
import type { IconProps } from './IconProps';

export const OraculusMarkIcon: React.FC<IconProps> = (p) => (
  <IconBase {...p}>
    {/*
     * Primary swirl — the thick golden crescent. A single open arc that
     * starts at upper-left, rotates through ~270°, and tapers as it
     * approaches the centre. Drawn as a stroked path so it inherits
     * currentColor; the stroke-width is heavy (2.4) at this 24-unit
     * viewBox, which gives the painted-impasto feel of the reference
     * artwork without busy interior detail.
     */}
    <path
      d="M 18.4 6.2
         A 8.6 8.6 0 1 0 12 20.6
         A 6.2 6.2 0 1 1 12 8.2
         A 4.0 4.0 0 1 0 14.2 14.2"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />

    {/*
     * Mid wisp — a thinner companion arc echoing the primary curve at a
     * larger radius. Reduced opacity gives the layered-paint feel of the
     * reference image. Open arc, no closure.
     */}
    <path
      d="M 19.6 9.0
         A 9.0 9.0 0 0 0 9.4 4.8"
      strokeWidth="0.9"
      strokeLinecap="round"
      opacity="0.55"
    />

    {/*
     * Outer wisp — a final faint arc near the bounding edge, echoing the
     * white-paint splash in the reference artwork. Sits at low opacity
     * so the overall mark stays readable at 16px.
     */}
    <path
      d="M 4.6 14.4
         A 9.4 9.4 0 0 0 7.2 19.8"
      strokeWidth="0.6"
      strokeLinecap="round"
      opacity="0.32"
    />

    {/*
     * Splatter dots — four off-axis specks that read as gold flecks. At
     * 16px these dissolve into a faint golden halo; at 64px+ they're
     * crisp and intentional. Filled rather than stroked so they stay
     * solid at small sizes.
     */}
    <circle cx="20.6" cy="14.8" r="0.45" fill="currentColor" stroke="none" opacity="0.7" />
    <circle cx="3.6" cy="9.4" r="0.35" fill="currentColor" stroke="none" opacity="0.6" />
    <circle cx="16.4" cy="20.4" r="0.35" fill="currentColor" stroke="none" opacity="0.55" />
    <circle cx="6.8" cy="3.8" r="0.30" fill="currentColor" stroke="none" opacity="0.5" />
  </IconBase>
);

/**
 * @deprecated v2.6 octopus-era name retained as an alias so existing
 * imports keep compiling. New code imports `OraculusMarkIcon` directly.
 */
export const OctopusMarkIcon = OraculusMarkIcon;

/**
 * @deprecated v2.5 strategy-era name retained as an alias.
 */
export const StrategyMarkIcon = OraculusMarkIcon;

/**
 * @deprecated v2.4 ODIA-era name retained as an alias.
 */
export const OdiaMarkIcon = OraculusMarkIcon;
