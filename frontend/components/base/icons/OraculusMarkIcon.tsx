/**
 * OraculusMarkIcon — O.D.I.A. monogram crosshair (v3.0).
 *
 * Geometric four-letter overlay mark designed against the user brief:
 * "an overlaying of each letter O D I A — the I has both lines on top
 * creating a four-piece triangle in a circle, where the circle is part
 * of the capital D. Clean geometric mark like a custom crosshair with
 * gem-like quality, gold and emerald mix."
 *
 * Construction (24×24 viewBox)
 * ----------------------------
 *   O  → outer circle (cx=12 cy=12 r=10) — gold stroke.
 *   D  → vertical stem tangent to the LEFT inner edge of the O at x=3,
 *        so the same circle outline reads as both O and D's curve.
 *   I  → vertical stem on the center axis (x=12) spanning apex to base
 *        of the inscribed triangle.  Double crossbar at the top —
 *        primary at y=5, lighter echo at y=7.25 — gives the "both lines
 *        on top" feature that subdivides the upper triangle into two.
 *   A  → equilateral triangle inscribed in the circle, apex at (12,3),
 *        base spanning (4.5,18.5)→(19.5,18.5).  Bisected by the I's
 *        stem and the top crossbar into four geometric facets:
 *          1. upper-left   (above crossbar, left of stem)
 *          2. upper-right  (above crossbar, right of stem)
 *          3. lower-left   (below crossbar, left of stem)
 *          4. lower-right  (below crossbar, right of stem)
 *        Upper pair tinted gold, lower pair tinted emerald — establishes
 *        the gem-facet feel while keeping the silhouette crosshair-clean.
 *
 * Palette uses CSS custom properties from globals.css so the mark
 * tracks the v2.8.0 mineral palette automatically and inherits theme
 * overrides without recompilation:
 *
 *   --gold-200          highlight gold
 *   --gold-500          mid gold
 *   --neon-emerald      vivid emerald
 *   --emerald-deep      deep emerald
 *
 * Strokes use round caps + joins so corners read crisp at 16px in the
 * sidebar chrome and don't develop antialias artifacts at 64px+ for
 * the splash and tray icons.  No fills on the silhouette — the four
 * triangle facets carry the only filled regions, at 0.18 opacity, so
 * the mark stays legible against any background.
 */

import React from 'react';
import type { IconProps } from './IconProps';

export const OraculusMarkIcon: React.FC<IconProps> = ({
  size = 20,
  className = '',
  style,
  'aria-hidden': ariaHidden = true,
  'aria-label': ariaLabel,
}) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    style={style}
    aria-hidden={ariaLabel ? undefined : ariaHidden}
    aria-label={ariaLabel}
    role={ariaLabel ? 'img' : undefined}
  >
    {/*
     * Four-facet fills (triangle interior).  Drawn FIRST so the gold-
     * stroked circle + I stems overlay them cleanly.  Opacity kept low
     * so they read as gem facets, not solid colour blocks.
     */}
    {/* upper-left facet (above crossbar, left of stem) — gold */}
    <polygon
      points="12,3 12,5 7.75,5"
      fill="var(--gold-200, #d8b13c)"
      opacity="0.22"
    />
    {/* upper-right facet — gold */}
    <polygon
      points="12,3 12,5 16.25,5"
      fill="var(--gold-200, #d8b13c)"
      opacity="0.22"
    />
    {/* lower-left facet (below crossbar, left of stem) — emerald */}
    <polygon
      points="7.75,5 12,5 12,18.5 4.5,18.5"
      fill="var(--neon-emerald, #1fe88f)"
      opacity="0.16"
    />
    {/* lower-right facet — emerald */}
    <polygon
      points="16.25,5 12,5 12,18.5 19.5,18.5"
      fill="var(--neon-emerald, #1fe88f)"
      opacity="0.16"
    />

    {/*
     * O + D shared outer circle — primary brand silhouette.  Gold
     * stroke reads first at any size.  The circle is read as O when
     * scanned in isolation, and as D's right curve when the left stem
     * is registered.
     */}
    <circle
      cx="12"
      cy="12"
      r="10"
      stroke="var(--gold-200, #d8b13c)"
      strokeWidth="1.6"
    />

    {/*
     * D's left stem — vertical tangent inside the O at the leftmost
     * edge.  Length stops short of the circle top/bottom so the D's
     * stem reads as a chord, not a diameter.  Lighter gold so the
     * O remains visually dominant.
     */}
    <line
      x1="3"
      y1="4.5"
      x2="3"
      y2="19.5"
      stroke="var(--gold-500, #997545)"
      strokeWidth="1.4"
    />

    {/*
     * A's inscribed equilateral triangle.  Emerald stroke so it pairs
     * against the gold circle.  Vertices placed exactly so the apex
     * sits on the circle top and the base corners touch the circle
     * at ~30°/150° — gives the gem-facet inscribed-shape look.
     */}
    <polygon
      points="12,3 4.5,18.5 19.5,18.5"
      stroke="var(--neon-emerald, #1fe88f)"
      strokeWidth="1.3"
    />

    {/*
     * I's vertical stem — center column.  Emerald, slightly thicker
     * than the triangle so it reads as the central crosshair axis.
     * Endpoints aligned with triangle apex (top) and base (bottom).
     */}
    <line
      x1="12"
      y1="3"
      x2="12"
      y2="18.5"
      stroke="var(--neon-emerald, #1fe88f)"
      strokeWidth="1.55"
    />

    {/*
     * I's double top crossbar — the "both lines on top" feature.
     * Primary bar at y=5 spans the triangle width at that height
     * (≈±4.25 from center), creating the cross-axis that bisects the
     * upper triangle.  Secondary echo bar at y=7.25 is narrower and
     * lighter, giving the gem-engraved depth and reinforcing the
     * crosshair signature.
     */}
    <line
      x1="7.75"
      y1="5"
      x2="16.25"
      y2="5"
      stroke="var(--gold-200, #d8b13c)"
      strokeWidth="1.6"
    />
    <line
      x1="9.6"
      y1="7.25"
      x2="14.4"
      y2="7.25"
      stroke="var(--gold-500, #997545)"
      strokeWidth="1.1"
    />

    {/*
     * Centre catch-light.  A 0.5-radius dot at dead-centre gives the
     * crosshair its sighting point and adds the only specular gem
     * highlight on the mark.  Small enough to dissolve at 16px into
     * a faint emerald spark.
     */}
    <circle
      cx="12"
      cy="12"
      r="0.55"
      fill="var(--neon-emerald, #1fe88f)"
      opacity="0.9"
    />
  </svg>
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
