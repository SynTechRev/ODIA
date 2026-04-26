# O.D.I.A. — Brand Reference

> **Locked at v2.7.9.** Subsequent palette changes require explicit
> review against this document. New surfaces (mobile, store listings,
> social cards, evidence-packet covers) consult this file first.

---

## 1. Identity in one paragraph

O.D.I.A. — *Oraculus Decimus Intellect Analyst* — is a forensic
civic-accountability platform. The visual identity is **precision
instrument meets archaic codex**: dark stone (smoke), antique gold,
and neon emerald, rendered with the layered depth of polished mineral.
Surfaces are slate-deep with hairline gold edging and gem-facet
clip-paths; readouts use monospaced numerals; severity tones flash
through saturated rose / orange / yellow / blue. The mark is a single
gold paint-swirl — a brushstroke caught mid-rotation — set on smoke.

Three things must be true of every surface:
1. **Dark by default.** No light theme. Evidentiary work is done in
   dim rooms, late at night, on devices that should not glare.
2. **Numerals are mono.** Findings, dollar amounts, hash digests,
   timestamps — every quantitative readout is JetBrains Mono, tabular.
3. **Gold is the chrome, emerald is the signal, rose is the alarm.**
   These three roles never swap. Gold = "ODIA". Emerald = "live /
   healthy". Rose = "critical".

---

## 2. Palette

The complete palette lives in `frontend/app/globals.css` as CSS custom
properties. This section is the **explanatory reference** — token
descriptions, intent, and where each token gets used. Code authors
import the tokens; they don't redefine them.

### 2.1 Smoke spine — chrome surfaces

The grayscale spine of the design system. Every panel, card, modal,
and chrome surface lives somewhere on this scale.

| Token | Hex | Use |
|---|---|---|
| `--smoke-950` | `#07070a` | Body background. The deepest stone. |
| `--smoke-900` | `#0e0e14` | Hero panels, app shell. |
| `--smoke-800` | `#18181f` | Card surfaces, sidebar background. |
| `--smoke-700` | `#25252f` | Hover states, secondary buttons. |
| `--smoke-600` | `#34343f` | Borders, dividers (subtle). |
| `--smoke-500` | `#5a5a66` | Muted body text, inactive labels. |
| `--smoke-300` | `#cbcbd1` | Body text, primary readout text. |
| `--smoke-200` | `#e6e6ea` | Headings, emphasized text. |
| `--smoke-100` | `#f4f4f6` | Highest-contrast text on darkest bg. |

**Rule:** Surfaces step from `950` (background) up through `900` (panel)
to `800` (inset card). Never skip more than one step within a single
component.

### 2.2 Gold vein — accent and chrome edging

The brand colour. Gold is the warm catch-light on every chrome edge,
the active border on focus, and the colour of the `O.D.I.A.` wordmark.

| Token | Hex | Use |
|---|---|---|
| `--gold-200` | `#f5dc9a` | Highest catch-light — active focus rings, hover edges. |
| `--gold-300` | `#ecc870` | Highlight — wordmark, brand glyph fill. |
| `--gold-400` | `#d8b13c` | Primary gold — `ODIA` lettermark. |
| `--gold-500` | `#b8941f` | Mid-tone — bracket pulses, hairline rules. |
| `--gold-600` | `#8a6f3e` | Shadow gold — inset edges, deep facets. |

**Rule:** Gold is reserved for chrome, identity, and accent. Never use
gold for body text or for severity indication.

### 2.3 Neon emerald — signal and live state

The cool counterweight to gold. Emerald means "live", "healthy", "active",
"connected". Used sparingly so it stays meaningful.

| Token | Hex | Use |
|---|---|---|
| `--emerald-300` | `#34d399` | Healthy status, "System Online" indicator. |
| `--emerald-400` | `#10b981` | Active workflow nodes, running indicators. |
| `--emerald-500` | `#059669` | Mid-tone, secondary live states. |
| `--neon-emerald` | `#1fe88f` | The hot signal — primary live glow, mobile tab-bar active state. Use with `text-shadow: 0 0 8px var(--neon-emerald)`. |
| `--jade-800` | `#065f46` | Deep emerald edging on inset panels. |

**Rule:** Emerald glows. Always pair with `text-shadow` or `box-shadow`
when used at signal strength (`--neon-emerald`). When used as a static
status pill, no glow.

### 2.4 Severity scale — alarm tones

Reserved exclusively for finding severity. Each tone has one job.

| Token | Hex | Severity | Tailwind alias |
|---|---|---|---|
| `--severity-critical` | `#f43f5e` | CRITICAL | rose-500 |
| `--severity-high` | `#f97316` | HIGH | orange-500 |
| `--severity-medium` | `#eab308` | MEDIUM | yellow-500 |
| `--severity-low` | `#3b82f6` | LOW | blue-500 |
| `--severity-info` | `#06b6d4` | INFO | cyan-500 |

**Rule:** Critical is rose, not red. The rose-orange split keeps
CRITICAL distinct from HIGH on a stacked tile row — a problem that
caused real defects in the v2.7.2 audit.

### 2.5 Automation channel — violet

Distinct colour for the n8n workflow / automation surfaces, so they
read as a different layer from the audit data (cyan) and chrome (gold).

| Token | Hex | Use |
|---|---|---|
| `--hud-flow` | `#a78bfa` | Workflow nodes, automation panel edges. |
| `--hud-flow-bright` | `#c4b5fd` | Active workflow, focused automation. |
| `--hud-flow-dim` | `#7c3aed` | Inactive workflows, deep edges. |

---

## 3. Reference imagery

Five vetted reference images live in `docs/brand/reference/`. Each one
captures a different facet of the visual identity. Designers consulting
this file should match the *texture and mood* of the references, not
copy them.

### 3.1 `reference_1_marble-veins.jpg`
**Smoke + gold + emerald tri-pole.** Black marble streaked with
gold leaf, transitioning to rough cut emerald crystal. This is the
**core composition** — three layers with gold serving as the seam
between dark stone and saturated emerald. Translates to the design
system as: chrome (smoke) → accent edging (gold) → signal (emerald).

### 3.2 `reference_2_emerald-marble-quartz.jpg`
**Primary emerald + gold marble flow.** Polished malachite-green marble
with gold veining and white quartz inclusions. The reference for any
surface that needs to feel **deep and polished** — splash screens,
hero panels, the app icon background. Note the gold is *thin and
veined*, never bulky.

### 3.3 `reference_3_emerald-malachite-flux.jpg`
**Saturated malachite swirl.** Higher saturation than 3.2; the
reference for **active states** — hovered panels, running workflows,
the live execution console. The gold here is denser and more
ornamental. Use sparingly.

### 3.4 `reference_4_alcohol-ink-triptych.jpg`
**Smoke + gold layered alcohol ink (triptych).** Three panels of gold
flowing through smoke and pearl. The reference for **mobile splash
screens, app store hero shots, and large empty states** where the
canvas needs visual weight without competing with content.

### 3.5 `reference_5_gold-swirl-icon-source.png`
**Direct icon source artwork.** A single gold paint swirl — thick
crescent inner curve, lighter wisps, splatter dots — on a smoke
background with white paint counterpoint. This is the **literal
source for the OraculusMark icon**. Geometry, weight distribution,
and splatter pattern in `oraculus-mark.svg` derive from this image.

---

## 4. The Oraculus mark

### 4.1 Geometry

A single gold swirl — a thick crescent inner curve that rotates
through ~270° and tapers as it approaches the centre. Surrounded by:
- one mid-weight wisp at slightly larger radius
- one faint outer wisp at the bounding edge
- 8 gold paint-splatter dots at golden-ratio offsets
- 3 white paint-splatter counterpoints

### 4.2 Component vs. asset

Two implementations, same geometry:

- **`OraculusMarkIcon.tsx`** — outline-only React component, used
  in-app at 16–24px (sidebar, tab bar, header glyph). Strokes only,
  inherits `currentColor` for theming.
- **`oraculus-mark.svg`** — rich rendered version with gradients,
  filters, and the dark-stone background. Used for application icons
  (Electron window, PWA manifest, Capacitor splash) at 192–1024px.

### 4.3 Sizing

| Context | Size | Variant |
|---|---|---|
| Sidebar header chrome | 16px | Component (outline) |
| Mobile tab bar active state | 20px | Component (outline) |
| Document chrome / header | 24px | Component (outline) |
| Settings page section header | 32px | Component (outline) |
| PWA manifest icon | 192/512px | SVG (rich) |
| Electron window icon | 1024px | SVG → PNG (rich) |
| iOS app icon | 1024px | SVG → PNG (rich, no rounded corners — iOS adds them) |
| Android adaptive icon (maskable) | 512px | SVG (rich), centered in inner 80% |
| Splash screen hero | 256–512px | SVG (rich) |

### 4.4 Don't

- Don't recolour the mark. The gradient is integral.
- Don't omit the splatter dots — they're the identity.
- Don't rotate. The swirl reads at 0° rotation as drawn.
- Don't use the mark as a divider, bullet, or decorative repeat.
  It's a brand glyph, not a graphic motif.
- Don't outline it on a light background. The mark is dark-mode native.
  If you must use it on light, render the white-paint variant (TBD —
  not yet drawn; surface the ask before improvising).

---

## 5. Typography

The type stack is locked at v2.7.1 and remains correct.

| Family | Use | Weight |
|---|---|---|
| **Cinzel** | Hero headings on the intro / splash. Brand surfaces only. | 700, 900 |
| **Cinzel Decorative** | Wordmark only. Never body. | 700, 900 |
| **Pinyon Script** | Inscription / declaration text on the intro. | 400 |
| **IM Fell English SC** | Small caps on declaration text. | 400 |
| **Inter** | Body text, UI labels, buttons. | 400, 500, 600, 700 |
| **JetBrains Mono** | All numerals, hashes, timestamps, code. | 400, 500, 700 |
| **Share Tech Mono** | Telemetry / boot text on the intro. | 400 |

Cinzel + Cinzel Decorative + Pinyon Script + IM Fell English are
loaded only on the intro page. The dashboard uses Inter + JetBrains
Mono exclusively.

---

## 6. Motion

Motion conventions are locked at v2.7.1. Reference for completeness:

- **`odia-pulse`** — 2s slow opacity pulse. "Heartbeat" indicators.
- **`odia-fade`** — 180ms fade-in on mount. Page transitions.
- **`odia-sheen`** — 2.5s diagonal gradient sweep. Hero panels on first paint.
- **`odia-scan`** — 2.4s top-to-bottom scan line. Live consoles.
- **`odia-tick`** — 600ms numeric flash on update. Readout changes.
- **`odia-breath`** — 2s expanding glow pulse. Running workflow nodes.
- **`hud-bracket-pulse`** — 3.5s bracket-corner opacity pulse.

All respect `prefers-reduced-motion: reduce`.

---

## 7. The intro sequence

The Oraculus intro (`frontend/public/intro/index.html`) is a
~25-second cinematic boot animation that plays on first launch. Five
phases:

1. **Phase 0 — Deep grid.** Hex mesh, data rings, drifting embers.
   Sets the "precision instrument" tone.
2. **Phase 1 — Boot text.** Share Tech Mono telemetry lines stream in.
   `> initiating Oraculus`, `> loading detectors`, etc.
3. **Phase 2 — ODIA glyph assembly.** Letters flicker in, lock to gold.
4. **Phase 3 — Equation row + code block.** The recursive scalar
   formula renders, supporting code lines type out.
5. **Phase 4 — Parchment glow.** Background shifts to parchment;
   smoke layer attenuates.
6. **Phase 5 — Declaration.** "We the People" inscribed in Pinyon
   Script + IM Fell English SC, with gold rules opening above and
   below. Brand tag fades in. Progress bar fills to 100%.

The intro asset is **never modified** without bumping
`INTRO_VERSION` in `frontend/lib/stores/intro.ts`. Version-bumping
forces the intro to play once more for returning users so they see
the new version.

---

## 8. Surface treatments

### 8.1 Chamfer + clip-path

Every chrome panel uses a `clip-path: polygon(...)` that cuts the
top-left and bottom-right corners. Default `--hud-chamfer: 10px`.
Dense panels use 6px. This is the gemstone-facet language — surfaces
look cut, not rounded.

### 8.2 Brackets

Hairline corner brackets (`.hud-brackets`) appear on hero panels
and on critical-finding panels. Two L-shaped strokes top-left and
bottom-right, 16×16px, with a 3.5s opacity pulse offset between them.

### 8.3 Hairline edging

All chrome surfaces have a `1px solid` edge in `--gold-500` at 35%
opacity (`--hud-edge`). Active states bump to 70% (`--hud-edge-strong`).
Critical states use rose at 55% (`--hud-edge-critical`).

### 8.4 Glow halos

Used sparingly, only on accent / hover / active states. Five named
glows: `--glow-amber`, `--glow-amber-strong`, `--glow-cyan`,
`--glow-violet`, `--glow-critical`. Apply as `box-shadow:
var(--glow-*);`.

---

## 9. Don't list (consolidated)

- No light theme. No light-themed surfaces. Period.
- No emoji in chrome. (One exception: console.info markers.)
- No gradients on body text. Gradients are reserved for chrome edges,
  the wordmark, and the brand glyph.
- No round corners on panels. Chamfer (`clip-path`) is the language.
- No serif body text. Serif is reserved for the intro.
- No analytics / telemetry SDKs. The audit-tool privacy story forbids
  third-party trackers on any surface.
- No ad-network glyphs. Even reference imagery from stock libraries
  must be vetted for licence; the bundled references are placeholders
  pending final licensed artwork.

---

**This document is normative.** When in doubt, the design system in
`globals.css` is the implementation; this document is the reasoning.
