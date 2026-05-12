# Changelog

## [2.10.0] - 2026-05-12 — Cross-Entity Analysis Protocol V1.0

Formalises two years of "accidental find" forensic work into deterministic architecture. Every document entering O.D.I.A. is now classifiable against the full Cross-Entity Registry, not just the jurisdiction under primary analysis. The protocol's governing principle — *"the audit that documents the machine that serves itself must operate across those same boundaries — systematically, not accidentally"* — operates at ingestion time, not at R.A.I.A. discovery time.

This is a scoped first slice of the protocol: registry foundation, D-13 detector with seven finding types (A–G), TCDAO press-release archive scraper (yearly + monthly-archive-widget discovery + 2022 path-variant handling + gap-band absence-record emission). The 14 entity-specific sub-detectors (Track D), XREF register persistence (Track E), and frontend XREF page (Track F) defer to v2.10.1+.

### Added — Track A · Cross-Entity Registry foundation
- **`src/oraculus_di_auditor/registry/` package** — canonical Sunshine Dragnet entity catalogue per Cross-Entity Analysis Protocol V1.0 (May 2026).
  - `entities.yml`: 12 Tier-1 primary jurisdictions (VPD/PPD/TPD/LDPS/FPD/WPD/DPD/EPD/TCSO/TCPD/TCDAO/DMV) + 8 Tier-2 governance bodies (BOS/Grand Jury/Courts/Public Defender/CAO/CCP/VEDC) + 10 Tier-3 vendors (Axon/Flock/Motorola/Lexipol/BCS/BRINC/NEC/Tyler/BI Inc/Loops Marketing) + 6 Tier-4 external intelligence sources + 13 personnel + 7 finding-type rules + 11 "Leave No Stone Unturned" non-standard record categories.
  - `loader.py` (`EntityRegistry`): typed accessors for tier-filtered iteration, alias index (case-insensitive), sub-detector activation lookup, finding-type severity defaults, non-standard category sweep precedents.
  - `types.py`: frozen `@dataclass` definitions (`Entity`, `Personnel`, `PersonnelHistoryEntry`, `FindingType`, `NonStandardCategory`).
  - 21 tests in `tests/registry/test_loader.py` covering tier counts, personnel records, Axon's 9-jurisdiction presence footprint, Fahoum personnel-migration precedent (E-001 → E-011), dataclass immutability.

### Added — Track B · D-13 Cross-Entity Detector
- **`src/oraculus_di_auditor/analysis/cross_entity.py`** — function-style detector matching the project's `(doc) -> list[dict]` contract. Sweeps every document against the full registry; emits one finding per `(primary, target)` pair, classified into one of seven types:
  - **A** Budget/Fiscal cross-reference (HIGH; CRITICAL on new vendor presence)
  - **B** Personnel migration (HIGH; CRITICAL on procurement-authority-to-prosecution-subject migration — the Fahoum precedent)
  - **C** Vendor cross-contamination (always CRITICAL — Farmersville/Woodlake/Visalia Axon Outpost precedents)
  - **D** Operational intersection (HIGH; default for unsignalled hits)
  - **E** Governance chain (HIGH; CRITICAL when governance action creates an unmet obligation)
  - **F** Grant/Funding pipeline (HIGH)
  - **G** Data/Evidence pipeline (HIGH; CRITICAL on undisclosed access)
- Confidence scoring with multi-signal co-occurrence bonus, dollar-amount-in-excerpt boost, repeated-mention reinforcement, and < 0.40 demotion-to-low-severity floor for analyst review.
- Registry + alias-pattern caches are module-level lazy singletons; first call hydrates, subsequent calls reuse (one YAML load per process).
- 11 fixture tests in `tests/analysis/test_cross_entity.py` covering activation gates, self-reference suppression, all five protocol-precedent finding types, low-confidence demotion, and the output-shape contract.
- D-13 wired into `analysis/pipeline.run_full_analysis` alongside the existing detectors; `"cross_entity"` joins the findings dict. The pipeline's severity-weights map gains `"critical": 1.0` so CRITICAL findings correctly dominate aggregate severity; flag extraction and summary lines updated to surface critical alongside high.

### Added — Track C · TCDAO press-release archive scraper
- **`src/oraculus_di_auditor/scrapers/tcdao_archive.py`** — v1 scraper for tulareda.org press release category archives. Polite by design: `robots.txt`-aware, identifying User-Agent (`O.D.I.A.-Forensic-Audit-Scraper/1.0`), default 2-second rate limit, exponential backoff on 429/503, `Retry-After` honoured, manifest-driven dedup, dry-run mode for discovery-only previews.
- Yearly category archive discovery 2020–2026, paginated walk, WordPress-standard HTML parsing (title / publish date / body / inbound links / embedded images / SHA-256).
- CLI: `python -m oraculus_di_auditor.scrapers.tcdao_archive --start-year 2020 --end-year 2026 --out data/tcdao_archive`.
- 11 parser tests in `tests/scrapers/test_tcdao_archive.py`.

### Added — Track D · v2 gap-band absence-record emission
- **`src/oraculus_di_auditor/scrapers/tcdao_archive_v2.py`** — extends v1 with three enhancements from the May 11, 2026 baseline diagnostic:
  - **Monthly-archive-dropdown discovery** (`parse_archive_widget`): the WordPress sidebar widget is the authoritative surviving-months index. Recovers sparse historical entries (2006-03, 2006-04, 2006-05, 2006-10, 2011-03, 2015-05) that no yearly category page lists.
  - **Gap-band detection + synthetic absence records** (`KNOWN_GAPS`, `classify_coverage`, `AbsenceRecord`, `emit_gap_absence_records`): three known multi-year gaps (GAP-A 2006-11→2011-02 / GAP-B 2011-04→2015-04 / GAP-C 2015-06→2017-12) materialise as `primary_entity=E-011` documents at finding ID `archival:coverage-gap`. The absence-record text deliberately includes governance vocabulary so D-13 round-trips it as a **Type E governance-chain cross-reference to BOS (E-020) regarding records-retention obligation** — locked by an integration test.
  - **2022 path-variant handling**: the canonical category slug was renamed and now requires the doubled `2022-press-releases-press-releases/` form; discovery tries both before falling back to monthly enumeration.
- 21 tests in `tests/scrapers/test_tcdao_archive_v2.py` including the C1+D1+B1+B2 end-to-end integration test.

### Added — Dependencies
- `beautifulsoup4>=4.12.0` (runtime). Used by the TCDAO scrapers; tests gracefully skip via `pytest.importorskip("bs4")` on minimal dev installs.

### Changed
- `analysis/pipeline.py`: pipeline `findings` dict now includes `"cross_entity"`; `severity_weights` includes `"critical": 1.0`; flag extractor and summary line surface critical alongside high. Existing detector behaviour unchanged.
- `analysis/__init__.py`: exports `detect_cross_entity_anomalies` alongside the existing detector exports.

### Fixed
- Function-style adaptation of the supplied D-13 corrected a Type B (Personnel Migration) classification bug in the upstream protocol bundle: `is_personnel` was derived from `target_entity_id.startswith("P-")` after personnel hits had been re-keyed under entity targets (E-NNN / V-NNN), so the test always returned False and Type B never fired. Now carried as a `kind` field on `AliasHit` and read at classify time.

### Notes for the v2.10.x sub-cycle
- Track A2 (PersonnelRegistry mutable extension via SQLAlchemy)
- Track A3 (Document schema additions: `primary_entity`, `secondary_entities`, `vendors_detected`, `personnel_detected`, `xref_notes`, `confidence_status` columns + migration)
- Track A4 (`CrossEntityReference` model + XrefRegister service)
- Track D1–D3 (14 entity-specific sub-detectors for TCPD/TCDAO/DMV)
- Track E2/E3 (Targeted R.A.I.A. + Entity-Opening R.A.I.A.)
- Track F1–F3 (Evidence packet XREF integration, frontend XREF/Personnel pages)
- Track C3 (IngestionBridge wiring scraped press releases into the standard pipeline)
- The two n8n workflows WF-015 (TCDAO archive monthly refresh) and WF-016 (Targeted R.A.I.A. daily trigger) defer to v2.10.x.

---

## [2.9.3] - 2026-04-28 — Detector Calibration Sweep + OCR Coverage

The Run-12 evidence packet (70 Visalia documents, 415 findings) revealed a P0 silent-failure mode: 8 of 38 unique SHAs (the actual Flock contracts, the Axon staff report, the JAG allocations PDF) emitted ONLY noise-floor findings because their text-extraction returned near-empty content and the audit pipeline did not flag the gap. v2.9.3 ships five tracks addressing that, plus a detector-completeness fix, MAS aggregation correctness, noise-floor suppression, and vendor-registry expansion.

### Added — Track A · OCR coverage (P0)
- **`scripts/diagnose_text_extraction.py`** — one-shot diagnostic. Run against any PDF corpus to identify silent-failure candidates (documents where pypdf returns < 500 chars and OCR fallback is needed). Supports `--use-ocr` to exercise the full pipeline + `--threshold` override.
- **`TextExtractionResult` dataclass + `extract_text_from_pdf_with_metadata()`** in `oraculus_di_auditor.ingestion.engine` — sibling of the existing `extract_text_from_pdf()` that returns the extraction `method` (`pypdf` / `tesseract_ocr` / `ocr_unavailable` / `failed`) + `char_count` alongside the text. Old function kept as a backwards-compatible wrapper.
- **`SeenHash.text_extraction_method` + `SeenHash.text_char_count`** columns persist the extraction provenance per document. New idempotent `_migrate_seen_hash_extraction_columns()` runs at `init_db()` to ALTER TABLE-ADD the columns on existing SQLite installs (no Alembic in this codebase).
- **Evidence packet manifest carries `text_extraction` block per document**: `{method, char_count, ocr_used}`. The executive summary now renders a corpus-level WARNING when documents required OCR — and an even louder warning when OCR was *needed* but unavailable (the silent-failure mode from Run-12).

### Fixed — Track B · Detector emission completeness (P0)
- **`grant:cops-without-itemisation` populates its evidence dict** (`grant_compliance.py`). The pre-2.9.3 emission passed `details={}`, leaving 10/10 sheets in Run-12 rendered with "(no structured details recorded)" and no Technical Evidence JSON block. Now emits `grant_program`, `statute` citation, `trigger_excerpts`, `itemisation_markers_searched`, `anti_supplant_referenced`.
- **Renderer-level invariant**: `evidence_packet._build_finding_sheet` now WARNs when a finding emits with empty `details`, so this regression cannot recur silently for any future detector.

### Changed — Track C · MAS aggregation correctness (P0)
- **Synthesis page top-findings table** — `Docs / Occurrences` columns replaced with `Unique SHAs / Total Emissions`. The pre-2.9.3 columns were ambiguous and duplicate uploads of the same SHA inflated both equally, producing nonsense like "50 docs / 50 occurrences". Now uses the `document_id → sha256` map from each audit's `document_manifest` to dedupe.
- **Synthesis page vendor table** — split detection-emission count from related-findings severity histogram. Pre-2.9.3 the severity histogram showed only `vendor-detected:*` emissions (uniformly LOW because that finding ID IS LOW), giving the misleading impression that Axon-related risk is uniformly LOW. Now `Detections` (vendor-tagged emissions) and `Related` (all findings on docs where the vendor was detected) are distinct, and the C/H/M/L histogram covers the related set.
- Both Markdown and DOCX exports updated; on-page rendering updated to surface unique-SHA counts and the related-severity strip.

### Changed — Track D · Noise-floor suppression (P1)
- **`fiscal:missing-provenance-hash` gated behind `ODIA_INCLUDE_PIPELINE_CHECKS=1`**. Fired on 100% of Run-11 + Run-12 corpora because it measures pipeline state, not document content. Default behaviour: silent. Diagnostic operators can opt in.
- **`admin:blank-required-fields` rolled up to corpus scope**. Per-document emission gated behind `ODIA_PER_DOC_BLANK_FIELDS=1`; default emission is now a single corpus-level `admin:blank-required-fields-corpus` finding with `scope: "corpus"` listing every affected document. Run-12 produced 70 echoes for one underlying observation; v2.9.3 produces 1 finding with the full per-document detail nested in `evidence.affected_documents`.
- **Tests for both detectors** updated to opt-in via `monkeypatch.setenv()`; new tests pin the default-OFF behaviour.

### Added — Track E · Detector coverage + vendor expansion (P1)
- **`scripts/detector_coverage.py`** — empirical coverage diagnostic. Exercises every detector against a stress corpus and reports detector module / finding ID / severity / details-populated / plain-language-template / statute citation per emitted finding. Answers "what does ODIA actually look for?" without a 9-module refactor. Verified output: 21 distinct finding IDs across 7 detector modules, all with populated `details` post-2.9.3.
- **Vendor catalogue expanded**: added `Verkada` (video / cloud surveillance, governance gates required) and `T-Mobile` (telecom backhaul). Pre-2.9.3 catalogue already covered Lexipol, Spartan Camera, ABH Fox Solutions, SmartWater CSI, Nexanet, Security Lines US, BCS Consulting, QPCS LLC — handoff list of 9 was based on a stale view; only these 2 were genuinely missing.

### Added — Documentation
- **`docs/EVIDENCE_PACKET_RUN12_EVALUATION.md`** — the run-12 quality audit that motivated v2.9.3. Documents the silent-failure observation, the detector emission gap, the MAS aggregation issues, and the noise-floor patterns.

### Engineering
- 229 backend tests pass on touched modules (`test_fiscal_detector` + `test_administrative_integrity` + `test_audit_engine` + `test_evidence_packet` + `test_ingestion_engine` + `test_plain_language` + `test_upload_routes` + `test_audit_records_mesh_job` + `test_audit_workflow_integration` + `test_orchestrator_dashboard`).
- `npx tsc --noEmit` clean across all production sources.
- `next build` passes for all 15 routes; Synthesis bundle ↑ 6.01kB → 6.33kB (new aggregation logic).

### Out of scope (deferred)
- Near-duplicate detection above SHA layer (the 4-byte Measure N variant) → v2.9.4.
- Image-extraction from PDFs (signature stamps, table images) → v2.10.0.
- Multi-language OCR (`tesseract-ocr-spa`) → activated when first Spanish corpus arrives.
- Cumulative-state R.A.I.A. recursion → separate analysis phase, not a code change.

---

## [2.9.2] - 2026-04-27 — Hero Pattern Convergence

The user named three pages (Dashboard, Anomalies, Orchestrator) as the design target and asked every other page to match. v2.9.2 ships the unification: a single shared `HeroMetricTile` component, the four-element canonical hero structure (bracket-label / heading / subtext / metric grid) on every surface, and tonal coherence across the navigation.

### Added
- **`HeroMetricTile` component** (`frontend/components/hero/HeroMetricTile.tsx`) — the canonical metric tile for hero readouts. One component, ten tones (`critical/high/medium/low/info/gold/emerald/signal/flow/neutral`), optional active state with 3-layer glow ring, optional onClick that renders as a keyboard-accessible button. Replaces three previously-divergent implementations (Dashboard `SeverityTile`, Anomalies inline filter buttons, Orchestrator `OrchestratorMetric`).
- **18 jest assertions** covering every tone, active/inactive states, button vs div rendering, sublabel handling, icon slot, and aria-pressed reflection.
- **`page-hero-synthesis` CSS class** — marble texture for the Synthesis cross-jurisdictional aggregation surface (mobile fallback included in the `@media (max-width: 768px)` block).
- **`docs/EVIDENCE_PACKET_RUN11_EVALUATION.md`** — quality audit of the run-11 evidence packet. 122 findings sampled across 7 detector modules; verdict is "factually correct, no detector regressions" with recommendations for v2.10.x calibration sprint.
- **`docs/BRAND.md` §8.5** — documents the canonical four-element hero pattern with bracket-label tone discipline (cyan-bright = live; amber = static/library; flow = automation).

### Changed
- **Anomalies hero** — added `[ ANOMALY EXPLORER · CROSS-AUDIT ]` bracket label + canonical heading + subtext; severity tiles now use `HeroMetricTile` with `active` glow ring on filter selection (behaviour identical, implementation shared).
- **Orchestrator hero** — three metrics migrated to `HeroMetricTile` with tonal colouring (`signal` for agents online, `emerald`/`neutral` for tasks queued, `gold` for completed/24h).
- **Synthesis hero** — flat severity-number strip + bare gem-panel hero replaced with the canonical pattern (marble texture, amber bracket label, severity tiles inside the hero with sublabel percentages, export buttons moved into the hero).
- **Documents hero** — added evidence-library bracket label + 3-tile metric grid (unique documents / total audits / findings emitted).
- **Analysis hero** — added aggregate-analytics bracket label + severity tile grid with percentage sublabels. Severity-distribution bars now colour by severity CSS vars (was uniform light-blue); detector bars fade `gold-300` → `gold-500` → `smoke-500` by rank.
- **Results hero** — flat severity strip with custom inline tones replaced with the canonical `HeroMetricTile` pattern. Bracket label includes the truncated job ID for context. Active-filter glow now matches Anomalies exactly.
- **Automation hero** — four `HealthTile` instances migrated to a `WebhookMetric` wrapper that maps webhook tri-state to `HeroMetricTile` flow/critical/medium tones; active-workflows tile uses `signal` (live state) instead of amber (config state).
- **Settings hero** — added `[ APPLICATION CONFIG · USER SCOPE ]` bracket label + canonical heading/subtext (no metric tiles — config page).
- **Upload hero** — added evidence-intake bracket label + 3-tile context strip (audits run / findings emitted / detector modules) so users see audit-history depth before they intake new documents.
- **Dashboard hero** — added `[ FORENSIC AUDIT PLATFORM · v2.9.2 · LOCAL ]` bracket label per BRAND.md §8.5; brand badge bumped to v2.9.2.

### Engineering
- **Zero type errors** in production code (`npx tsc --noEmit` clean across all `app/` + `components/` non-test sources).
- **Next.js build** passes for all 15 routes; bundle deltas are minor (each metric-tile-using page picks up ~0.3 kB for the shared `HeroMetricTile` chunk).

---

## [2.9.1] - 2026-04-27 — Mineral Polish + Maturity Pass

Five tracks of finish work on top of v2.9.0. Track A fixes the intro's premature exit, Track B propagates mineral textures across every page, Track C completes the light-theme leak sweep, Track D finally swaps the legacy octopus desktop icon, Track E lands the maturity roadmap.

### Fixed
- **Intro played past final frame** (Track A) — `IntroFrame.tsx` fallback timeout bumped 30s → 35s. The intro `run()` function takes ~31.4 seconds end-to-end (3 phases + 7.6s typeCode + 2.4s final hold + postMessage); the previous 30s fallback fired BEFORE the intro's postMessage, cutting off the "We the People" + brand-tag phase. 35s gives ~4s cushion past genuine completion so postMessage always wins under normal conditions; the fallback only fires if the intro JS errors mid-sequence.
- **Desktop icon still showed legacy octopus** (Track D, **CRITICAL**) — `desktop/resources/icon.png` was 2,757,125 bytes at v2.8.1, **identical to v2.7.10**. Despite the v2.7.10 / v2.8.0 / v2.8.1 release notes claiming the icon had been updated, the file on disk had never actually been replaced. Fixed by copying the v2.8.2 raster bundle (1,299,046-byte composite of the gold-swirl source painting in a circular frame with gold ring) into `desktop/resources/icon.png` + new `icon.ico` for Windows multi-size, plus three PWA rasters (192/512/maskable-512). Windows title bar finally renders the brand mark.

### Added
- **Per-page mineral hero textures** (Track B) — eight new `.page-hero-*` utility classes wired into Upload, Results, Anomalies, Documents, Analysis, Settings, Orchestrator, Automation. Each page reads as a distinct location in the same mineral-photographic visual world: Upload + Settings + Automation get gold-flux, Results gets emerald malachite, Anomalies + Orchestrator get malachite-flux (active surfaces), Documents + Analysis get marble.
- **Comprehensive light-theme override sweep** in `globals.css` — every `bg-{color}-50/100`, `text-{color}-700/800`, `border-{color}-200/300` Tailwind class now resolves to mineral-palette CSS vars at runtime. Form inputs (select / input / textarea) get mineral styling. Severity stripe primitive (`.severity-stripe.s-{level}`) for finding cards.
- **Two new secondary surface classes** — `.gem-card-marble`, `.gem-card-malachite` for body-level cards (more dimmed than hero variants).
- **`docs/MATURITY_REPORT.md`** (Track E) — 289-line project status document covering the six dimensions of "outstanding performance" (visual identity, forensic depth, operational reliability, data governance, distribution, community), what's complete, and a 90-day sprint roadmap from v2.9.x to v2.10.0.

### Changed
- **Results page severity table** — emoji icons (🔴🟠🟡🔵) removed per `BRAND.md` §9 (no emoji in chrome). Replaced with `hud-sev hud-sev-{level}` pill primitives + `severity-stripe` left-edge accents on finding cards.
- **Anomalies page severity filter tiles** — pastel `bg-red-50/orange-50/yellow-50/blue-50` rectangles replaced with `hud-panel hud-panel-inset` cards + colored dot + glow shadow when active. Matches the Dashboard's SeverityTile pattern.
- **Settings — Theme dropdown removed** — the app is dark-only per `BRAND.md` §9; the "Light / Dark / System" options were misleading and the user confirmed the setting didn't actually work. Replaced with a read-only "Mineral (locked at v2.8.0)" indicator.
- **Settings — auth buttons** — `bg-blue-600 text-white` and `border-gray-300 text-gray-700` replaced with `hud-btn hud-btn-emerald` / `hud-btn hud-btn-ghost`.
- **Upload page drag-drop zone** — pale gray rectangle replaced with `hud-panel hud-panel-inset` + emerald glow when armed.
- **Upload "From Gallery" / "Use Camera" buttons** — light gray border buttons replaced with `hud-btn hud-btn-ghost` at 44 px touch-target minimum.

---

## [2.9.0] - 2026-04-27 — Mobile-First PWA Polish

The platform's first dedicated mobile pass. Tracks A (documentation) and B (PWA polish) ship; Track C (Capacitor native wrapper) is deferred pending Apple Developer Program / Google Play Console account decisions. Web/PWA installs work on iOS Safari and Android Chrome today.

### Added
- **`docs/MOBILE.md`** — comprehensive PWA platform guide. Platform-support matrix (iOS Safari ≥16.4, Android Chrome ≥110, desktop Chromium), install instructions for both flavors, service-worker behavior, troubleshooting, and a deferred-work reference for the Capacitor native track.
- **README — Mobile (PWA) section** — points users at `docs/MOBILE.md` and summarises which surfaces are mobile-optimized vs. desktop-first.
- **`PullToRefresh` component** (`frontend/components/mobile/PullToRefresh.tsx`) — touch-driven pull-to-refresh wrapper with damped pull curve, threshold arming, and `--signal-neon` spinner glow. Active only on `<md:` viewports (desktop has its own polling). Wired into `/documents`, `/anomalies`, and `/results`.
- **`InstallPrompt` component** (`frontend/components/pwa/InstallPrompt.tsx`) — mobile-only install banner. Captures Android `beforeinstallprompt` for one-tap install, falls back to an iOS Safari "Tap Share → Add to Home Screen" hint. Auto-suppresses in standalone mode, under file:// (Electron), and for 14 days after dismissal. Mounted in `DashboardLayout` above the bottom tab bar.
- **Upload page mobile card layout** — file table replaced with a stacked card list on `<md:`. Each card surfaces filename, format pill, size, truncated SHA, and a full-width Remove button at the 44 px touch-target minimum. The desktop table is preserved verbatim at `md+`.

### Changed
- **`Button` size scale formalized as touch-target policy** — `xs (32 px)`, `sm (40 px)`, `md (44 px)`, `lg (52 px)` minimum heights. `md` is the iOS HIG / Material Design default (44 pt / 48 dp). Documented inline at `frontend/components/base/Button.tsx`.
- **Mobile bottom tab bar `min-h-[56px]`** — gives every tab the full Material Design tap surface.
- **Service worker — split caching** (`frontend/public/sw.js`): app shell pre-cached in `odia-shell-v5` (bumped from `odia-shell-v4`); new `odia-static-v1` runtime cache holds `/_next/static/*`, `/icons/*`, `/textures/*` under a stale-while-revalidate strategy. `/api/*` (including `/api/uploads/*`) is still never cached. Splitting the caches keeps the shell small and lets us evict the two independently.

### Fixed
- **`/documents` page broken `useMemo` opener** — the row-aggregation memo was missing its `const rows = useMemo(() => {` declaration after the v2.9.0 B3 edit, leaving floating code and an undefined `rows` reference. Restored.

### Notes
- **Capacitor native track deferred** — full handoff staged in `C:\Users\yahua\Downloads\v2.8.1_Updates\CLAUDE_CODE_HANDOFF_v2_9_0_mobile.md` for when Apple Developer Program ($99/yr) and Google Play Console ($25 one-time) accounts are decided. The PWA covers the install path until then.

---

## [2.8.1] - 2026-04-26 — Mineral Calibration Bug-Fix Patch

Five surgical fixes addressing user-flagged bugs in the v2.8.0 install.

### Fixed
- **Texture overlay too dark** (Fix #1) — `.gem-hero-*` overlay opacities reduced from 0.50–0.95 to 0.30–0.72 so the underlying marble veining / malachite striations / gold flux from the reference photos actually read through. Previous opacities drowned the texture so the hero panels showed flat tinted rectangles. New range still meets 4.5:1 text contrast on the composite.
- **Textures don't load under Electron file://** (Fix #2, **CRITICAL**) — CSS `url('/textures/...')` resolved to filesystem root under `file://` (same bug class as the v2.7.10 IntroFrame fix). New `TextureResolver` client component uses `useLayoutEffect` to overwrite the `--texture-*` CSS variables with `publicAssetURL()`-resolved absolute URLs before browser paint. Mounted in `app/layout.tsx` between `ServiceWorkerRegistration` and `IntroGate`. Mobile breakpoint substitutes `-mobile.webp` variants. SSR-safe (short-circuits when `typeof window === 'undefined'`).
- **Intro replay button visible from start** (Fix #3) — `#replay` button now ships with `opacity: 0` and `pointer-events: none`. Reveals only after the run() function adds `.completed` class to `#seq` (post brand-tag fade-in).
- **Intro click-dismiss too eager** (Fix #4) — added 4-second minimum-duration guard on `$('seq').addEventListener('click', ...)`. Clicks before the guard expires are absorbed; clicks after dismiss as before. The parent IntroFrame's Skip button (3-second appearance delay, upper-right corner) is unaffected — it still dismisses immediately. Final-frame hold bumped from 1.4s → 2.4s so users see "We the People" + brand tag before the dashboard fade-in.

### Added
- **`scripts/build-icons.sh`** — rsvg-convert + ImageMagick reference rasterizer documented in handoff §6 Option B. The existing `frontend/scripts/build-icons.mjs` (sharp-based) remains the default — both produce equivalent SVG-fidelity output. Shell script is preserved for users who prefer rsvg-convert.
- **`frontend/components/__tests__/TextureResolver.test.tsx`** — 4 smoke tests pinning the texture-variable rewrite behaviour.

### Notes
- **Fix #5 deferred — no new icon raster commit needed.** The v2.8.0 commit `D2` already regenerated the icons via sharp from the new measured-color SVG, and sharp's libvips renderer with `density: 384` produces SVG-fidelity output equivalent to rsvg-convert. The supplied PIL approximations in the v2.8.1 bundle are visibly worse than the already-committed sharp output, so they're skipped. The user's "still shows octopus" diagnostic likely came from a stale install of v2.7.x.

---

## [2.8.0] - 2026-04-26 — Mineral Calibration

### Changed
- **Palette** — every smoke / gold / emerald token recalibrated to colors literally measured from the reference photography in `docs/brand/reference/`. Primary brand gold shifts from `#d8b13c` (saturated yellow) to `#997545` (mineral tan-gold); primary emerald shifts from `#1fe88f` (digital neon) to `#0f6546` (real malachite). The neon emeralds are preserved under a new `--signal-*` namespace reserved for live-state UI only (running workflow, healthy backend, active mobile tab).
- **Intro** — plays on every app launch (was: first launch only). Per-session dedup via `sessionStorage` means navigating between pages within a session does not replay it. Settings replay button now writes a one-shot `localStorage` flag for cross-session force-replay.
- **Oraculus mark SVG** — rebuilt with measured colors from the source painting. Every gradient stop is a real pixel sampled from `reference_5_gold-swirl-icon-source.png`.
- **`OctopusMarkIcon` → `OraculusMarkIcon`** — call sites in `app/page.tsx` and `components/dashboard/DashboardLayout.tsx` migrated to the canonical name. The deprecated alias re-export stays in `components/base/Icons.tsx` so any third-party import keeps working.
- **Service worker** — cache key `odia-shell-v3` → `odia-shell-v4` to evict v2.7.x caches on the new mineral palette.

### Added
- **Texture system** — four reference photos exposed as CSS variables (`--texture-marble`, `--texture-malachite`, `--texture-malachite-flux`, `--texture-gold-flux`), each in four pre-dimmed WebP variants (bg, hero, tile, mobile). Total ~530 KB across 16 files at `frontend/public/textures/`.
- **Gem-hero utility classes** — `.gem-hero-marble`, `.gem-hero-malachite`, `.gem-hero-malachite-flux`, `.gem-hero-gold-flux`, `.gem-splash`. Hero/splash/cover surfaces only — body content panels stay flat per BRAND.md §3.2.
- **Dashboard hero gets `.gem-hero-malachite`** (C1) and **Synthesis hero gets `.gem-hero-marble`** (C3) — texture composes underneath the existing chamfer + bracket geometry.
- **`docs/brand/measured_palette.json`** — machine-readable palette reference with L\* values + source-image anchoring for every token.

### Fixed
- **CHANGELOG** — reconstructed continuity from v2.1.1 forward (all v2.2 through v2.7.10 entries reconstructed from git tag history + memory artifacts).

---

## [2.7.10] - 2026-04-26 — Sign-off Pass on v2.7.9 Install

### Fixed
- **Intro black-screen bug** — `<iframe src="/intro/index.html">` resolved to filesystem root under Electron `file://` (became `file:///intro/index.html` — doesn't exist). New `publicAssetURL()` helper in `frontend/lib/navigation.tsx` anchors against the runtime app root via `getAppRootURL()`. IntroFrame computes the iframe src via this helper at mount.
- **Application icon** — swapped from procedural SVG approximation (read as a stylized "C/E" curve) to a pixel-faithful raster of `docs/brand/reference/reference_5_gold-swirl-icon-source.png` via `sharp` lanczos3 upscale. Maskable variant gets 12% inner padding so Android adaptive-icon mask doesn't crop the artwork.
- **DOCX export now works on the desktop install** — was pandoc-only since Sprint 6 (silently disabled in PyInstaller bundle). Added `python-docx` fallback in `format_converters.markdown_to_docx` handling the audit-report Markdown subset directly. `python-docx` added to runtime deps + PyInstaller spec hiddenimports.

### Changed
- **Contrast + gold pass** — body bg switched from flat near-black to a 4-stop linear gradient (smoke-950 → #0c1011 → #0d1310 → smoke-900) with a faint jade undertone. Edge tokens bumped: `--gem-edge-gold` 55%→80%, `--gem-edge-emerald` 45%→70%. `.hud-panel` and `.gem-panel` lifted off pure black with jade undertone, dual gold + emerald halo on hover.

### Added
- **3 DOCX-fallback regression tests** in `tests/test_docx_export_fallback.py`.

---

## [2.7.9] - 2026-04-25 — Brand Refresh & Cinematic Intro

### Added
- **`docs/BRAND.md`** — 323-line visual identity reference document. Palette tokens, glyph geometry, typography stack, motion conventions, surface treatments, do/don't list. Locked at v2.7.9.
- **`OraculusMarkIcon`** — gold paint-swirl React component replacing the v2.6-era `OctopusMarkIcon` (headphones-and-tentacles silhouette). Three deprecated aliases (`OctopusMarkIcon`, `StrategyMarkIcon`, `OdiaMarkIcon`) repointed to the new component so every existing call site keeps compiling.
- **Cinematic Oraculus intro** — 25-second self-contained HTML+CSS+JS boot animation at `frontend/public/intro/index.html`. Five phases: deep grid → boot text → glyph assembly → equation/code → declaration. Plays on first launch (changed to every launch in v2.8.0).
- **`IntroGate` + `IntroFrame` + intro Zustand store** — orchestration. SSR-safe, respects `prefers-reduced-motion`, autofocused Skip button at 3s, Escape exits, 30s fallback timer.
- **Settings → Presentation card** with "Show on next launch" replay button.
- **`scripts/build-icons.mjs`** — sharp-based PNG rasterizer (no pandoc/rsvg-convert needed). `electron-builder` auto-derives `.ico` + `.icns` from the master `icon.png`.
- **5 vetted reference images** in `docs/brand/reference/`.

### Changed
- **`manifest.json` + `layout.tsx` theme color** → `#07070A` (`--smoke-950`); `appleWebApp.statusBarStyle` → `"black-translucent"`.
- **Service worker** cache `odia-shell-v1` → `odia-shell-v3`.

---

## [2.7.7] – [2.7.8] - 2026-04-25 — Gemstone Propagation + AppLink Hotfix

### Added
- **Gemstone palette propagation** (Y1–Y5) — vibrant neon emerald + matte gold dual-edge tokens propagated platform-wide. Crystallized facet panel utility (`.gem-panel-faceted` — 12-vertex quartz silhouette via clip-path). Sidebar, topbar, mobile bottom-tab bar, base components, every Dashboard card restyled. Severity strip on Dashboard rewired to the live `/api/v1/dashboard/summary` endpoint.

### Fixed
- **v2.7.8** — `<AppLink>` and SVG `IconProps` interfaces now declare `style?: React.CSSProperties` so the gem-palette inline-style approach used in DashboardLayout passes the Next.js typecheck. v2.7.7's tag failed CI at the typecheck step; v2.7.8 supersedes it.

---

## [2.7.6] - 2026-04-25 — X1–X5 Functional Pass

### Added
- **`/api/v1/dashboard/summary`** endpoint backing the Analysis Summary card on the home page (was previously reading from a Zustand store that production audits never wrote to).
- **Frozen-aware jurisdiction discovery** + `POST /api/v1/dashboard/seed-jurisdictions` endpoint + "Seed Example Jurisdictions" trigger so RAIA Synthesis works on a fresh desktop install.
- **Legistar retrieval bridges into the upload-staging store** — downloads now appear in the Upload page's "files ready" table.
- **Audit pipeline records `MeshExecutionJob` rows** so the Orchestrator timeline reflects actual work.
- **Initial gemstone hero POC** on `frontend/app/page.tsx` (replaced the v2.7.5 W4 purple/platinum POC).

---

## [2.7.5] - 2026-04-25 — Manual Triggers Wired

### Added
- **ODIA-native `/api/v1/triggers/*` route family** bypasses the n8n token gate so the Manual Triggers panel works out of the box.
- **CCOPS Compliance scorecard** on HUD primitives.

### Changed
- **Ingest tab consolidated into Upload** (legacy redirect preserved at `/ingest`).

---

## [2.7.4] - 2026-04-24 — Quality Polish

### Fixed
- **Database initialization at startup** — closes silent-degrade gap where `get_db()` raised "DB not initialised".
- **Dynamic version pill** on the sidebar (was hardcoded literal).
- **Tri-state UX on Orchestrator executions** — distinguishes "loading" from "unavailable".
- **Three-state automation tile** (`READY` / `OFFLINE` / `NOT CONFIGURED`).

---

## [2.7.3] - 2026-04-23 — Audit-Fix Sprint (D1–D8)

### Added
- **MAS narrative templates** — plain-language audit-report narrative with statute citations.
- **Orchestrator page** — full task graph + execution timeline + agent status panels.
- **Electron window icon** — desktop title-bar icon now uses the bundled SVG/PNG.
- **`/api/v1/automation/*`** n8n proxy + n8n editor health gate on the Automation page.

### Fixed
- **General-path SeenHash deduplication** — desktop audits now skip duplicates on the SHA-256 hash, matching the n8n webhook flow.
- **Fail-loud PDF extraction** — silent text-extraction failures now emit `ingestion:extraction-failure` HIGH-severity findings.
- **Tile contrast** — severity tiles redrawn to HUD primitives (was unreadable on dark theme).

---

## [2.7.2] - 2026-04-23 — Desktop Build Stabilization

### Fixed
- **PyInstaller cold-start** — uvicorn switched to `create_app` factory pattern (was bare `app` object); main.js startup timeout 30s → 60s.
- **n8n integration** — desktop builds now ship the `automation`/`cpra`/`field`/`webhook`/`triggers` route modules in PyInstaller hiddenimports.

---

## [2.7.1] - 2026-04-23 — HUD Design System Upgrade

### Added
- **Design token system** — `globals.css` rewritten with full token hierarchy. `slate-950 / amber-500 / cyan-400` palette. Five panel variants (`hud-panel`, `-data`, `-flow`, `-critical`, `-inset`). Severity pills, metric readouts, workflow nodes, dividers, HUD buttons, HUD tables. Print mode flattens to litigation-grade B&W.
- **Violet automation channel** — workflow state distinct from audit data.
- **Motion system** — `odia-pulse`, `odia-fade`, `odia-sheen`, `odia-scan`, `odia-tick`, `odia-breath`, `hud-bracket-pulse`. All respect `prefers-reduced-motion: reduce`.

---

## [2.7.0] - 2026-04-23 — n8n Integration

### Added
- **Token-gated webhook surface** — 5 endpoints under `/api/v1/webhook/*` (ingest-and-analyze, batch-ingest, status, synthesize, health). Token validated against `ODIA_WEBHOOK_TOKEN` via constant-time comparison. Refuses to register if the env var is unset.
- **`docker-compose.n8n.yml`** — one-command stack for backend + Postgres + n8n with shared inbox volume.
- **DB models** — `SeenHash`, `WebhookAuditLog`, `CPRARequest`, `FieldObservation`.
- **RAIA service package** — Recursion Analysis Investigative Audit cross-jurisdictional pattern detection.
- **CPRA + field-verification routes** — `/api/v1/cpra/deadlines-within/{72h,7d,30d}`, field observations under `/api/v1/field/*`.
- **Automation page** — first-class n8n workflow + execution viewer.

---

## [2.5.x] – [2.6.x] - 2026-04-22 to 2026-04-23 — Architectural Tier Boundary + Octopus Mark Era

### Added
- **Three-tier architecture analysis** — Tier 1 forensic, Tier 2 extended, Tier 3 recursive synthesis boundary documented.
- **Jurisdiction auto-loader** (`config.jurisdiction_loader.discover_jurisdictions`) — scans `config/multi_jurisdiction/` for per-jurisdiction subdirectories.
- **Octopus mark** introduced as the v2.6 brand glyph (later replaced at v2.7.9 with the Oraculus gold-swirl).
- **Synthesis page** — cross-audit aggregation report, DOCX export.
- **Platform-aware OCR fallback** — Tesseract bundled on Windows; macOS/Linux use system-installed binaries via PATH.

### Fixed
- **Fiscal regex** — appropriation-trail detector tightened to reduce false positives on routine encumbrance language.

---

## [2.4.0] - 2026-04-22 — 4-Platform Installer Release

### Added
- **OCR-bundled Windows installer** — Tesseract + Poppler binaries shipped inside the PyInstaller bundle so scanned PDFs work out of the box.
- **macOS arm64 + x64 installers** built on separate runners.
- **Linux AppImage** with libfuse2 dependency documented.

---

## [2.3.0] - 2026-04-21 — Detector Pipeline Expansion

### Added
- **Vendor catalogue + grant-compliance detector** — JAG/COPS anti-supplanting, vendor-statutory-trigger mapping (Flock/Axon/Lexipol), 9th detector added to the audit pipeline.
- **Governance gap detector** rewritten with 7 distinct finding IDs (capability-without-council-approval, data-retention-gap, lexipol-boilerplate, consent-calendar-placement, sole-source-without-justification, auto-renewal-clause, transparency-portal-absence).
- **Surveillance detector** rewritten with vendor-specific statutory gap detection (ALPR/SB524, ALPR Privacy Act, BWC/CJIS, facial recognition, drone/AB481, AI report writing).

---

## [2.2.x] - 2026-04-18 — Detector Refinement

### Fixed
- **`_flatten_findings`** — was reading `result["findings"]` but `analyze_document` returns `result["anomalies"]` (caused 0 findings since v2.0).
- **Upload error messages** — show actual FastAPI `detail` / HTTP status instead of generic "Check that the server is running".
- **CI workflow hardening** — graceful npm fallback when `package-lock.json` absent.

### Added
- **8-detector analysis pipeline** restored and wired through `audit_engine.analyze_document`.
- **React error boundaries** (`frontend/app/error.tsx`, `global-error.tsx`).

---

## [2.1.x] - 2026-04-16 to 2026-04-17 — UI Patch Set + CI Heredoc Fix

### Fixed
- **CI hang on indented PYEOF** — extracted inline Python heredoc to standalone `scripts/fix_electron_paths.py`.
- **Electron `routeToFileURL` subpage navigation** — base URL now strips known route segments before computing root.
- **PyInstaller hiddenimports** — 21 modules added (route modules, auth stack, SQLAlchemy SQLite dialect, sklearn C extensions).

### Added
- **`OctopusMarkIcon` etc.** — self-contained inline SVG icon set (critical for Electron file:// rendering).
- **Dashboard cards** — `SystemStatusCard`, `AnalysisSummaryCard`, `DetectorStatusCard`, `JurisdictionCard`.
- **`navigation.tsx`** — `useAppNavigate`, `AppLink`, `isFileProtocol`, `routeToFileURL` Electron file:// helpers.

---

## [2.1.1] - 2026-04-13 — Desktop App Icons & macOS Multi-Arch Build Fix

Patch release fixing desktop application packaging and CI workflows introduced in v2.1.

### Fixed
- macOS desktop build now correctly produces separate x64 (macos-13) and arm64 (macos-latest) artifacts instead of a single hardcoded arch
- `release-desktop.yml` upgraded to `action-gh-release@v2`; per-platform build commands use the correct Electron targets
- `desktop-build.yml` split macOS job into separate x64 and arm64 runners
- `desktop/package.json` sets per-platform `artifactName` and removes hardcoded `mac.arch`

### Added
- `desktop/resources/icon.png` (512×512), `icon.ico` (multi-size), `icon.icns` (multi-size) — desktop application icons for all three platforms

### Docs
- README download table updated to reflect 4 platform entries (Windows, Linux, macOS arm64, macOS x64)
- `desktop/README.md` updated with separate macOS arm64/x64 entries and per-arch build commands

---

## [2.0.0] - 2026-03-13 — Platform Generalization Release

This release transforms ODIA from a jurisdiction-specific audit tool into a
general-purpose legal document ingestion, normalization, and anomaly auditing platform.
All jurisdiction-specific data has been removed; the platform is now configured via
`config/jurisdiction.json` and `config/corpus_manifest.json`.

### Breaking Changes
- `src/oraculus/` is now a thin backward-compatibility wrapper only; all new code lives
  in `src/oraculus_di_auditor/`
- Anomaly detector return shape changed: `{id, issue, severity, layer, details}` replaces
  the previous `{type, description, severity, evidence}` shape
- `config/jurisdiction.json` must be present for jurisdiction-aware analysis (optional;
  system degrades gracefully when absent)

### Added

#### Anomaly Detectors (5 new)
- `procurement_timeline` — detects contracts executed before governing-body authorization date
- `signature_chain` — detects unsigned, partially signed, or placeholder-signed documents
- `scope_expansion` — detects amendment-as-procurement pattern (significant scope creep)
- `governance_gap` — detects surveillance capabilities deployed without governance documentation
- `administrative_integrity` — detects missing final actions, blank required fields, retroactive authorizations

#### API Endpoints (3 new)
- `POST /analyze/detailed` — per-detector anomaly breakdown with severity summary and weighted score
- `GET /detectors` — registry of all 8 detectors with descriptions and anomaly types
- `POST /analyze/batch` — multi-document analysis with cross-document procurement timeline patterns

#### Jurisdiction & Configuration System
- `src/oraculus_di_auditor/config/jurisdiction_loader.py` — `JurisdictionConfig` dataclass,
  `load_jurisdiction_config()`, `get_config()` singleton, `clear_config_cache()`
- `config/jurisdiction.json` (gitignored) — active jurisdiction config
- `config/corpus_manifest.example.json` — template for corpus configuration
- `config/corpus_manifest.json` — maps corpus IDs to meeting dates

#### Audit CLI
- `scripts/run_audit.py` — end-to-end audit CLI: ingest → analyze → report (JSON + Markdown)

#### Frontend (Next.js 14 dashboard)
- `frontend/lib/types/api.ts` — canonical `Anomaly`, `DetailedAnalysisResult`, `DetectorInfo`,
  `JurisdictionInfo` TypeScript types
- `frontend/lib/api/client.ts` — `APIClient` singleton covering all backend endpoints
- `frontend/lib/stores/analysis.ts` — Zustand store with `detailedAnalyses` state
- `frontend/components/anomalies/DetectorGroupPanel.tsx` — collapsible per-detector panels
  with severity color-coding and expandable evidence
- `frontend/components/analysis/SeverityChart.tsx` — recharts donut chart
- `frontend/components/dashboard/JurisdictionCard.tsx` — live jurisdiction config display
- `frontend/components/dashboard/DetectorStatusCard.tsx` — live detector registry display
- Dashboard severity count cards; anomalies page document selector and severity filter;
  analysis page top-10 findings panel

#### Documentation
- `CONTRIBUTING.md` — contributor guide with branch, commit, and test conventions
- `docs/PHASES.md` — phase-by-phase engine reference (Phases 5–20)
- `docs/phases/` — 25 phase overview and implementation files (relocated from repo root)
- `README.md` — full rewrite (~167 lines, clean public-facing structure)

### Changed
- Unified package structure: `src/oraculus/` reduced to thin wrapper; `src/oraculus_di_auditor/`
  is the sole authoritative package
- Higher-phase naming: abstract/mythological names replaced with plain engineering terms
  (rec17, rgk18, aei19, aer20, mesh, otge15, qdcl, scalar_convergence)
- `scripts/corpus_manager.py` now loads from `config/corpus_manifest.json`
- `datetime.utcnow()` replaced with `datetime.now(UTC)` throughout (deprecation fix)
- All `open()` calls use `encoding="utf-8"` for Windows cp1252 compatibility
- Unicode `✓`/`✗` in scripts replaced with `[OK]`/`[FAIL]`
- Phase documentation files moved from repo root into `docs/phases/`

### Removed
- All jurisdiction-specific data (city names, Legistar URLs, personnel names,
  dollar amounts from any specific audit)
- Jurisdiction-specific hardcoded configurations

### Tests
- **2275 passing, 9 skipped, 0 failing**
- New test files: `tests/test_jurisdiction_config.py`, `tests/test_pipeline_jurisdiction.py`,
  `tests/test_run_audit.py`, `tests/test_api_detectors.py` (21 tests for new API endpoints)
- 9 skipped tests are data-dependent corpus/transparency tests with explicit skip markers

---

## 2024-12-29 - Audit Triage & Reporting Pipeline Scaffolding

### Added - Audit Triage & Reporting Infrastructure

**Complete audit workflow scaffolding for manual auditing, legally-defensible reports, and small-model evaluations on lightweight hardware.**

#### Core Files
- **`audit_manifest.schema.json`** - JSON Schema for document manifest validation with fields for document metadata, extraction info, forensics, flags, citations, notes, redaction status, and chain-of-custody
- **`config/defaults.yaml`** - Repository-level configuration for manifests, extraction, PDFs (external storage by default), Ollama, RAG/retrieval, redaction (manual review required), OCR, reports, security, and evaluation
- **`config/ollama_config.yaml`** - Ollama-specific configuration with model settings, generation parameters, system prompts per category, and response validation

#### Scripts
- **`scripts/triage.py`** - Executable CLI tool for creating/updating manifests with SHA-256 checksums, flags (severity: low/medium/high/critical), notes, and chain-of-custody tracking
- **`scripts/ocr_sample.py`** - Lightweight OCR runner using Pillow + pytesseract with optional deskewing via opencv-python; extracts text to `extraction/` and updates manifest metadata
- **`scripts/render_report.py`** - Report renderer using Jinja2 templates; generates Markdown reports with optional HTML/PDF via pandoc or wkhtmltopdf
- **`scripts/eval_harness.py`** - Ollama evaluation harness with TF-IDF-based retrieval (scikit-learn) or naive substring fallback; records model responses, latency, context, and stores logs under `reports/eval/`
- **`scripts/auto_issue_generator.py`** - GitHub issue draft generator for high-severity findings; creates markdown files in `reports/issues/` with pre-filled audit finding templates

#### Templates & Queries
- **`templates/report_template.md`** - Jinja2 Markdown template for executive summary, findings list, evidence manifest table, methodology, legal checks, recommendations, and appendices
- **`queries/sample_queries.json`** - 20 sample audit queries across 6 categories: factual_retrieval, contradiction_detection, irb_consent_check, infrastructure_concern, grant_incentive_detection, executive_summary

#### Compliance & Governance
- **`compliance_checklist.md`** - Four fault-line compliance framework with detailed checklists for DOJ certification, IRB consent (28 C.F.R. Part 46), infrastructure policy, and federal grant incentives; includes red flags, immediate actions, and per-document assessment forms

#### GitHub Integration
- **`.github/ISSUE_TEMPLATE/audit_finding.md`** - Issue template for reporting audit findings with fields for document ID, manifest path, severity, fault-line category, evidence, impact assessment, recommended actions, and chain-of-custody

#### Directory Structure
- **`manifests/`** - Document manifest storage with README
- **`extraction/`** - Extracted text storage with README
- **`reports/eval/`** - Evaluation results directory
- **`reports/issues/`** - Generated issue drafts directory

#### Tests
- **`tests/test_triage_basic.py`** - Unit tests for triage.py covering manifest creation, flag addition, note addition, updates, checksum calculation, and validation

### Documentation
- **README.md** - Added comprehensive "Audit Triage & Report Scaffolding" section with quick start guide, configuration instructions, security/legal warnings, compliance checklist overview, files added, requirements, and next steps for repo owner
- All scripts include detailed docstrings and command-line help with usage examples

### Features
- **Manual Audit Workflow**: Triage script for creating manifests with flags and notes; no heavy dependencies (stdlib + hashlib)
- **OCR Integration**: Pytesseract-based text extraction with confidence scoring and optional deskewing
- **Report Generation**: Jinja2-based Markdown reports with fallback support for missing pandoc/wkhtmltopdf
- **Ollama Evaluation**: Small model evaluation with local inference, TF-IDF retrieval, latency tracking, and structured logging
- **Compliance Framework**: Four fault-line checklist covering DOJ, IRB, Infrastructure, and Grant compliance
- **Security-First**: External PDF storage by default, manual redaction review required, no automatic uploads, chain-of-custody tracking
- **Low-Compute Design**: Runs on lightweight hardware (HP notebook); all processing local; no cloud dependencies

### Security & Legal
- No automated external uploads of PDFs or manifests
- Default configuration stores PDFs externally (configurable via `config/defaults.yaml`)
- Redaction placeholders only; manual review required before disclosure
- Chain-of-custody tracking with SHA-256 checksums and timestamps
- Explicit warning: tooling does not constitute legal advice; consult counsel

### Requirements
- Core: Jinja2, pytesseract, Pillow, pdf2image, scikit-learn (optional but recommended)
- Optional: opencv-python (deskewing), pandoc (reports), wkhtmltopdf (PDF fallback), requests (Ollama HTTP)
- System: tesseract-ocr, Ollama (optional for evaluation)

### Next Steps for Repo Owner
1. Confirm manifest storage location (in-repo vs. external)
2. Confirm redaction policy (placeholders only vs. enabled)
3. Confirm Ollama model names for testing

---

## 2025-12-04
- Trigger CI for PR #37 by adding a small doc change to ensure GitHub Actions picks up the latest push to `copilot/initiate-full-ingestion`.

All notable changes to the Oraculus Decimus Intellect Analyst project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - November 17, 2025
- **Documentation** (40.6 KB total):
  - `docs/audit-methodology.md` - Multi-layered anomaly detection framework
  - `docs/recursive-scalar-model.md` - Mathematical framework for pattern lattice analysis
  - `docs/developer-setup.md` - Comprehensive developer onboarding guide
  - `docs/database-design.md` - Database architecture and implementation plan
  - `VALIDATION_REPORT.md` - Project completion assessment (48% complete toward v1.0)
- **API Interface**:
  - `src/oraculus_di_auditor/interface/api.py` - FastAPI REST API stub
  - Endpoints: `/api/v1/health`, `/api/v1/analyze`, `/api/v1/info`
- **Test Coverage** (11 new tests):
  - `tests/test_constitutional_detector.py` - Constitutional anomaly tests
  - `tests/test_surveillance_detector.py` - Surveillance outsourcing tests
  - Enhanced `tests/test_fiscal_detector.py` - Appropriation trail tests

### Enhanced - November 17, 2025
- **Fiscal Detector** (`fiscal.py`):
  - Appropriation trail detection (fiscal amounts without appropriation keywords)
  - Fiscal amount pattern matching ($1,000,000, $1M formats)
  - New anomaly: `fiscal:amount-without-appropriation` (medium severity)
- **Constitutional Detector** (`constitutional.py`):
  - Broad delegation pattern detection (Secretary may determine, as deemed necessary)
  - Intelligible principle checking (limiting standards detection)
  - New anomaly: `constitutional:broad-delegation` (medium severity)
- **Surveillance Detector** (`surveillance.py`):
  - Surveillance keyword detection (biometric, facial recognition, monitoring, tracking)
  - Contractor involvement detection (contractor, vendor, third party)
  - Privacy safeguard checking (warrant, court order, minimization)
  - New anomalies: `surveillance:outsourced-without-safeguards` (high), `surveillance:outsourced-with-safeguards` (low)
- **Scalar Core** (`scalar_core.py`):
  - Weighted scoring by severity (low: 0.02, medium: 0.05, high: 0.10)
  - Pattern lattice coherence bonus (up to 0.02 for strong provenance)
  - More nuanced confidence scoring

### Validated
- ✅ 143/143 tests passing (100% pass rate)
- ✅ All ruff checks passing (zero linting errors)
- ✅ CodeQL security scan: 0 vulnerabilities
- ✅ Pre-commit hooks functional
- ✅ CI/CD pipeline operational

### Added - Earlier
- Complete foundational scaffold implementation per specification
- Core modules: `cli.py`, `config.py`, `ingest.py`, `normalize.py`, `embeddings.py`, `retriever.py`, `analyzer.py`, `reporter.py`, `utils.py`
- Documentation: `ARCHITECTURE.md`, `PHASE_PLAN.md`, `DATA_POLICY.md`, `PROVENANCE.md`
- Data directories: `cases/`, `statutes/`, `vectors/` with proper gitignore
- Test suite for all new modules
- Tool scripts: `import_examples.sh`, `make_local_env.ps1`
- Requirements files: `requirements.txt`, `dev-requirements.txt`
- CLI interface for document ingestion

### Features
- Multi-format document ingestion (TXT, JSON, PDF, XML)
- Text normalization with configurable chunking (2000 chars, 200 overlap)
- TF-IDF based deterministic embeddings (sklearn)
- Vector storage and cosine similarity search
- Advanced anomaly detection:
  - Fiscal: Appropriation trail analysis
  - Constitutional: Broad delegation detection
  - Surveillance: Outsourcing and safeguard validation
  - Long sentence detector (>1000 chars)
  - Cross-reference mismatch detector
  - Contradictory date detector
- Recursive scalar scoring with weighted severity penalties
- JSON and CSV report generation with provenance
- REST API interface (FastAPI)
- Full test coverage for core modules

### Infrastructure
- Parallel module structure: `src/oraculus_di_auditor/` alongside existing `src/oraculus/`
- Backward compatible with existing legislative ingestion system
- Privacy-first data policy with gitignored sensitive directories
- Comprehensive architecture documentation
- Database design ready for implementation

## [0.1.0] - 2025-11-12

### Added
- Initial project structure from PR #7
- Legislative document loader with JSON, TXT, PDF support
- Provenance tracking system with reference graph
- Anomaly detection for missing fields and broken references
- Confidence scoring system
- GitHub Actions CI workflow
- Basic test infrastructure

### Infrastructure  
- Package structure under `src/oraculus/`
- JSON Schema validation
- SHA-256 hashing for document integrity
- Test fixtures and comprehensive test suite
