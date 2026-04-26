# O.D.I.A. — Brand Reference (v2.8.0)

> **Locked at v2.8.0.** The visual identity is now anchored, literally,
> to the photographic reference imagery in `docs/brand/reference/`.
> Every color in the smoke / gold / emerald ramps is a measured pixel
> from one of four photos. Subsequent palette changes require explicit
> review against this document AND the source images.

---

## 1. Identity in one paragraph

O.D.I.A. — *Oraculus Decimus Intellect Analyst* — is a forensic
civic-accountability platform. The visual identity is **mineral
photography meets precision instrument**: the warm tan-gold and deep
malachite of polished cut stone, layered with hairline gold edging,
gem-facet clip-paths, and precise monospaced numerals. The mark is a
single gold paint-swirl — a brushstroke caught mid-rotation — set on
a near-black mineral ground. Surfaces feel *cut*, not drawn.

Three things must be true of every surface:

1. **Dark by default.** No light theme. Evidentiary work is done in
   dim rooms, late at night, on devices that should not glare.
2. **Numerals are mono.** Findings, dollar amounts, hash digests,
   timestamps — every quantitative readout is JetBrains Mono, tabular.
3. **Gold is the chrome, mineral emerald is the deep field, signal
   neon is the alarm-tier alive indicator.** These three roles never
   swap. Gold = "ODIA". Mineral emerald = "deep state, healthy". Signal
   neon = "live, running". Rose = "critical".

---

## 2. Palette — anchored to reference photography

The complete palette lives in `frontend/app/globals.css` as CSS custom
properties. Every value below is a real measured pixel from one of
the reference images, with the source noted.

### 2.1 Smoke spine — chrome surfaces (warm-leaning grayscale)

| Token | Hex | L\* | Source image | Use |
|---|---|---|---|---|
| `--smoke-50`  | `#e1d7c6` | 0.829 | gold_swirl_source     | warm white — highest contrast |
| `--smoke-100` | `#cdcdc7` | 0.792 | marble_veins          | high-contrast text |
| `--smoke-200` | `#bebeb8` | 0.733 | marble_veins          | emphasized text |
| `--smoke-300` | `#a4a8a9` | 0.653 | marble_veins          | body text |
| `--smoke-400` | `#7c8180` | 0.496 | marble_veins          | inactive labels |
| `--smoke-500` | `#494742` | 0.273 | marble_veins (synth)  | muted dividers |
| `--smoke-600` | `#2d2d2c` | 0.175 | marble_veins          | subtle dividers |
| `--smoke-700` | `#221f20` | 0.127 | gold_swirl_source     | borders |
| `--smoke-750` | `#1a1817` | 0.096 | gold_swirl_source     | hover surfaces |
| `--smoke-800` | `#12160f` | 0.073 | malachite_flux        | raised cards |
| `--smoke-850` | `#0c1113` | 0.061 | emerald_marble_quartz | card surfaces |
| `--smoke-900` | `#080c08` | 0.039 | malachite_flux        | app shell |
| `--smoke-950` | `#050505` | 0.020 | malachite_flux        | body bg |

### 2.2 Gold — antique tan-gold (NOT saturated yellow)

The PRIMARY gold (`--gold-500` `#997545`) is sampled from the actual
mid-stroke of the painted swirl in `reference_5_gold-swirl-icon-source.png`.
This is the literal color of the brushstroke.

| Token | Hex | L\* | Use |
|---|---|---|---|
| `--gold-50`  | `#eae1cf` | 0.865 | paint highlight (catch-light) |
| `--gold-100` | `#ded2be` | 0.808 | catch-light |
| `--gold-200` | `#bfae94` | 0.665 | soft highlight |
| `--gold-300` | `#b89664` | 0.557 | highlight |
| `--gold-400` | `#b59162` | 0.547 | bright primary |
| `--gold-500` | `#997545` | 0.435 | **PRIMARY brand gold** |
| `--gold-600` | `#8e704b` | 0.425 | mid-tone |
| `--gold-700` | `#685339` | 0.316 | shadow gold |
| `--gold-800` | `#4e4033` | 0.253 | inset edge |
| `--gold-900` | `#3a2e1f` | 0.175 | deepest gold shadow |

### 2.3 Emerald — mineral malachite (NOT digital neon)

The PRIMARY emerald (`--emerald-500` `#0f6546`) is sampled from
`reference_2_emerald-marble-quartz.jpg`. This is real polished
malachite green, not a saturated digital green.

| Token | Hex | L\* | Source | Use |
|---|---|---|---|---|
| `--emerald-100` | `#6e9e8f` | 0.525 | marble_veins          | mineral pale |
| `--emerald-200` | `#5fa17f` | 0.502 | emerald_marble_quartz | soft highlight |
| `--emerald-300` | `#3f6a46` | 0.331 | malachite_flux (synth) | desaturated mid |
| `--emerald-400` | `#1c835f` | 0.312 | marble_veins          | mid-light |
| `--emerald-500` | `#0f6546` | 0.227 | emerald_marble_quartz | **PRIMARY emerald** |
| `--emerald-600` | `#0e4028` | 0.153 | malachite_flux        | mid |
| `--emerald-700` | `#0d392c` | 0.137 | emerald_marble_quartz | deep panel bg |
| `--emerald-800` | `#0b291a` | 0.102 | malachite_flux        | deep malachite |
| `--emerald-850` | `#0a1e13` | 0.078 | malachite_flux        | shadow |
| `--emerald-900` | `#080f0a` | 0.045 | malachite_flux        | near-black |
| `--emerald-950` | `#050504` | 0.018 | malachite_flux        | deepest |

### 2.4 Signal — digital neon (live-state ONLY)

These are NOT mineral-derived. They sit alongside the mineral palette
and provide the "this is a UI signal, not chrome" cue. **Reserved
exclusively for live-state UI** — running workflow, healthy backend,
active mobile bottom-nav tab. Never use for chrome, panels, or body
text.

| Token | Hex | Use |
|---|---|---|
| `--signal-300`  | `#5cf5b0` | mint highlight |
| `--signal-400`  | `#1fe88f` | core signal — live workflow |
| `--signal-500`  | `#0fd47a` | healthy status |
| `--signal-neon` | `#00ff9d` | glow — bottom tab active, live pulse |

### 2.5 Severity — semantic-locked

| Token | Hex | Severity |
|---|---|---|
| `--severity-critical` | `#f43f5e` | CRITICAL |
| `--severity-high`     | `#f97316` | HIGH |
| `--severity-medium`   | `#eab308` | MEDIUM |
| `--severity-low`      | `#3b82f6` | LOW |
| `--severity-info`     | `#06b6d4` | INFO |

### 2.6 Flow — automation channel (preserved)

| Token | Hex | Use |
|---|---|---|
| `--flow-300` | `#c4b5fd` | bright |
| `--flow-400` | `#a78bfa` | primary — n8n workflows |
| `--flow-500` | `#7c3aed` | dim |

---

## 3. Texture system

Four reference textures are exposed as CSS variables. Each ships in
four pre-dimmed WebP variants under `frontend/public/textures/`.

| Variable | File pattern | When to use |
|---|---|---|
| `--texture-marble`           | `texture-marble-{bg,hero,tile,mobile}.webp` | hero panels with mineral character |
| `--texture-malachite`        | `texture-malachite-{bg,hero,tile,mobile}.webp` | splash, dashboard hero |
| `--texture-malachite-flux`   | `texture-malachite-flux-{bg,hero,tile,mobile}.webp` | active states, intro outro |
| `--texture-gold-flux`        | `texture-gold-flux-{bg,hero,tile,mobile}.webp` | evidence packet covers, MAS report covers |

### 3.1 Texture utility classes

Defined in `globals.css`. Layer reference photography under chrome
geometry. Use sparingly — texture-heavy surfaces are the EXCEPTION.

- `.gem-hero-marble` — marble texture under smoke + gold edge
- `.gem-hero-malachite` — malachite under emerald edge
- `.gem-hero-malachite-flux` — saturated malachite under signal edge
- `.gem-hero-gold-flux` — gold-swirl painting under gold edge
- `.gem-splash` — fullscreen splash variant, no clip-path

Each class auto-swaps to the `-mobile` WebP variant under
`@media (max-width: 768px)`.

### 3.2 When to apply textures

| Surface | Class | Rationale |
|---|---|---|
| Splash screen | `.gem-splash` | First impression — full mineral ground |
| Dashboard hero panel | `.gem-hero-malachite` | Primary work surface — deep field |
| Evidence packet cover | `.gem-hero-gold-flux` | Output deliverable — gold ground |
| Synthesis page hero | `.gem-hero-marble` | Cross-jurisdictional tri-pole |
| Settings page hero | `.gem-hero-marble` | Calm, neutral |
| Body content panels | (no texture) | Texture would distract from data |
| Result rows | (no texture) | High information density |
| Forms / inputs | (no texture) | Functional, not ornamental |

---

## 4. The Oraculus mark

### 4.1 Color anchoring (v2.8.0)

The mark SVG (`frontend/public/icons/oraculus-mark.svg`) was rebuilt
at v2.8.0 with every gradient stop sampled from the source painting:

| SVG role | Hex | Provenance |
|---|---|---|
| catch_light | `#eae1cf` | painting catch-light (gold_swirl_source) |
| soft_high   | `#ded2be` | raised brushstroke face |
| catch_warm  | `#cdc1b0` | warm catch-light on stroke side |
| mid_light   | `#b89664` | mid-stroke value |
| primary     | `#997545` | PRIMARY brand gold (anchor) |
| mid_dark    | `#8e704b` | mid-stroke shadow |
| deep        | `#4e4033` | inset shadow |
| void        | `#221f1f` | stroke base |

### 4.2 Sizing

| Context | Size | Variant |
|---|---|---|
| Sidebar header chrome | 16px | Component (outline) |
| Mobile tab bar active state | 20px | Component (outline) |
| Document chrome / header | 24px | Component (outline) |
| Settings page section header | 32px | Component (outline) |
| PWA manifest icon | 192/512px | SVG (rich) |
| Electron window icon | 1024px | SVG → PNG (rich) |
| iOS app icon | 1024px | SVG → PNG (rich, iOS adds rounded corners) |
| Android adaptive icon (maskable) | 512px | SVG (rich), centered in inner 80% |
| Splash screen hero | 256–512px | SVG (rich) |

### 4.3 Don't

- Don't recolour the mark. The gradient stops are anchored to the
  painting.
- Don't omit the splatter dots — they're the identity.
- Don't rotate. The swirl reads at 0° rotation.
- Don't use the mark as a divider, bullet, or decorative repeat.
- Don't outline it on a light background. The mark is dark-mode
  native. If light-mode use is ever needed, surface the ask before
  improvising.

---

## 5. Typography

Unchanged at v2.8.0. The type stack is locked.

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

## 6. Motion (unchanged at v2.8.0)

- **`odia-pulse`** — 2s slow opacity pulse. "Heartbeat" indicators.
- **`odia-fade`** — 180ms fade-in on mount. Page transitions.
- **`odia-sheen`** — 2.5s diagonal gradient sweep. Hero panels on first paint.
- **`odia-scan`** — 2.4s top-to-bottom scan line. Live consoles.
- **`odia-tick`** — 600ms numeric flash on update. Readout changes.
- **`odia-breath`** — 2s expanding glow pulse. Running workflow nodes.
- **`hud-bracket-pulse`** — 3.5s bracket-corner opacity pulse.

All respect `prefers-reduced-motion: reduce`.

---

## 7. The intro sequence (v2.8.0 — plays every launch)

The Oraculus intro (`frontend/public/intro/index.html`) is a
~25-second cinematic boot animation that plays on **every** app
launch (changed from "first launch only" at v2.8.0 per user
direction).

Per-session deduplication: once dismissed within a session, it does
NOT replay on page navigation. Dismissal is tracked in
`sessionStorage` under `odia.intro.dismissed.session` and
clears when the tab/window closes.

Force-replay: Settings → "Show on next launch" writes a one-shot
flag to `localStorage` (`odia.intro.forceReplay`) which IntroGate
reads-and-clears on next mount.

Reduced-motion users opt out entirely.

---

## 8. Surface treatments

### 8.1 Chamfer + clip-path

Every chrome panel uses a `clip-path: polygon(...)` that cuts the
top-left and bottom-right corners. Default `--hud-chamfer: 10px`.
Dense panels: 6px. Hero panels with textures use `--gem-facet: 14px`.

### 8.2 Brackets

Hairline corner brackets (`.hud-brackets`) appear on hero panels
and on critical-finding panels. Two L-shaped strokes top-left and
bottom-right, 16×16px, with a 3.5s opacity pulse offset between them.

### 8.3 Hairline edging

All chrome surfaces have a `1px solid` edge in the gold-400 family
at 85% opacity (`--edge-gold`) — bumped at v2.8.0 from 80% to ensure
the gold reads decisively on the new mineral backgrounds. Active
states bump to gold-100 at near-opaque (`--edge-gold-bright`).
Critical states use rose at 65% (`--edge-critical`).

### 8.4 Glow halos

Used sparingly, only on accent / hover / active states. Six named
glows: `--glow-gold`, `--glow-gold-strong`, `--glow-emerald`,
`--glow-signal`, `--glow-signal-neon`, `--glow-flow`,
`--glow-critical`. Apply as `box-shadow: var(--glow-*);`.

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
- No texture under data-heavy panels. Texture is the EXCEPTION,
  reserved for hero / splash / cover surfaces.
- No saturated yellow gold. The brand gold is `#997545` (warm tan-
  gold, sampled from the source painting). Saturation breaks the
  mineral identity.
- No digital neon emerald in chrome. The mineral emerald is
  `#0f6546` (real malachite). Digital neon is `--signal-*`,
  reserved for live-state indication only.

---

**This document is normative.** When in doubt, the design system in
`globals.css` is the implementation; this document is the reasoning.
The reference imagery in `docs/brand/reference/` is the source of
truth for color decisions — every measured value above came from
those photos.
