# O.D.I.A. — Maturity Report

> **Question asked:** *"What is necessary for this application to be
> fully matured and containing all that is necessary for outstanding
> performance?"*
>
> **Answered at:** v2.8.2 baseline, post-mineral-calibration.

---

## 1 · Where the project actually is

This is not a "MVP" or a "polished prototype." It is a **production-
grade forensic accountability platform** with a depth that very few
solo or small-team projects ever reach. To set context honestly:

- **184 backend test files**, ~12 detector modules with statute
  citations, real OCR fallback, SHA-256 dedup, plain-language
  narrative templates that read like abbreviated MAS reports.
- **21 backend route modules** including webhook ingest, RAIA
  cross-jurisdictional synthesis, CPRA deadline tracking, field
  observation capture, orchestrator task graph, automation API
  proxy.
- **A working PWA** with manifest, service worker, install prompts,
  camera capture, offline shell.
- **A working Electron desktop app** with custom URL resolution
  (`publicAssetURL()`), the runtime texture resolver
  (`TextureResolver`), and an icon system.
- **A fully designed visual identity** locked in `BRAND.md` and
  measured against reference photography — the mineral palette is
  literally pixels sampled from vetted images.
- **A 25-second cinematic intro** with five animation phases.
- **n8n workflow integration** via webhook surface + 8 registered
  workflows.
- **Multi-jurisdiction audit pipeline** with cross-jurisdictional
  synthesis (RAIA service).
- **Plain-language MAS-grade narrative generation** for every
  finding ID — no boilerplate fallback firings remaining.

Few civic-tech tools at any scale (commercial or otherwise) ship
with this combination. The remaining work to reach "outstanding"
status is **finish work and reach work** — not foundation work.

---

## 2 · The six dimensions of outstanding performance

A platform that aspires to "outstanding" needs strength in six
distinct dimensions. The current state of each:

### Dimension 1 — Visual identity coherence
**Status: 85% complete after v2.8.2.**

Strong: locked palette, photography-anchored colors, gold-swirl
mark in chrome and PNG icons, mineral textures on every page,
intro plays cleanly through to declaration.

Remaining work:
- **(Low priority)** macOS `.icns` icon — operator step (run
  `iconutil` on a Mac, commit the .icns).
- **(Optional)** Production-fidelity rasterisation via
  `rsvg-convert` for the icon set (current PIL composites are good;
  rsvg renders are better).
- **(Future)** Brand video / motion clips for outreach use, derived
  from the intro.

### Dimension 2 — Forensic analytical depth
**Status: 95% complete.**

Strong: 12-detector suite, statute-anchored narrative templates,
SHA-256 dedup, OCR fail-loud fallback, plain-language MAS-grade
output. The v2.7.2 audit symptoms (boilerplate, dedup misses,
silent PDF extraction failures) are all resolved. Evidence packets
read like abbreviated MAS reports.

Remaining work:
- **(Medium priority)** A **detector calibration sweep** — run the
  full audit corpus across the 12 detectors and verify every finding
  ID is accurate to its underlying evidence. Some `admin:blank-
  required-fields` findings (Screenshot 7) appear at MEDIUM severity
  for what may be optional fields; calibrate.
- **(Medium priority)** **Cross-detector deduplication** — if two
  detectors (e.g., `surveillance` and `governance`) both fire on the
  same evidence chunk, surface ONE finding with both detector tags
  rather than two findings competing for attention. Reduces the
  total finding count noise.
- **(Future)** **Confidence scoring per finding** — already partially
  in the data model. Surface as a 0-100 score next to severity.
  Helps the auditor triage.

### Dimension 3 — Operational reliability
**Status: 75%.**

Strong: backend health probe, n8n health gate, intro fallback
timer, file-protocol path resolution, dedup table, fail-soft DB
patterns, structured logging.

Remaining work:
- **(High priority)** **Application telemetry** — local-only
  structured event log (file-based, never network). Currently the
  only diagnostic is `console.info('[odia] intro:complete')`. Add
  a local event log for: ingestion start/end, detector fire,
  finding emit, evidence packet generated, audit completion. Key
  for post-mortem on production audits.
- **(High priority)** **Crash recovery** — what happens if Electron
  crashes mid-audit? Currently: lose the audit. Need: in-progress
  audits persist to disk every 30s, recover on restart.
- **(High priority)** **Backend liveness probe** — the
  `Backend Online / Offline` indicator (sidebar bottom-left) is
  good but it's a binary signal. Add: backend version match
  validation (frontend v2.8.2 talking to backend v2.8.2, not v2.7.x).
- **(Medium priority)** **Full PWA offline** — service worker
  currently caches the shell but not the React bundles. After a
  cold offline launch, page navigation 404s. Fix via runtime
  cache strategy (specified in v2.9.0 mobile handoff B4).

### Dimension 4 — Data governance + privacy
**Status: 90%.**

Strong: 100% local processing (no outbound network), SHA-256
provenance per document, no third-party analytics SDKs, CJIS-style
hash chain in evidence packets.

Remaining work:
- **(High priority)** **Encryption at rest** — sqlite databases
  and uploaded documents currently stored unencrypted. For an audit
  tool handling pre-publication evidence, this is a real exposure.
  Add: SQLCipher for the database, Fernet-encrypted document store
  for uploads. Document the threat model in `docs/SECURITY.md`.
- **(High priority)** **CPRA correspondence draft protection** —
  CPRA letter drafts in the database can include strategic content.
  Add a "redact and export" path that generates a sanitised version
  for sharing while keeping the working copy locked.
- **(Medium priority)** **Audit log** — every ingest, every detector
  fire, every export should log to an append-only journal. Helps
  with chain-of-custody requirements when an audit becomes a court
  exhibit.

### Dimension 5 — Distribution
**Status: 50%.**

Strong: Web + PWA work today. Electron Windows + macOS + Linux
build artefacts produce. Docker Compose stack defined. n8n
optional companion service.

Remaining work:
- **(Highest priority)** **Mobile** — v2.9.0 Capacitor track
  (already specified). Two paths: A+B alone delivers installable
  PWA; full A+B+C delivers iOS + Android store-ready apps.
- **(High priority)** **Code-signed installers** — Electron builds
  currently produce unsigned `.exe`, `.dmg`, `.AppImage`. Windows
  flags unsigned exes as malware risk; macOS requires notarization
  for non-store distribution. Cost: ~$300/year (Apple Developer
  Program $99 + EV code-signing cert ~$200). Without this, every
  user has to click through "untrusted publisher" warnings.
- **(High priority)** **Auto-update** — Electron's `autoUpdater`
  works against an update server. Without it, users on v2.7.x
  don't know to upgrade to v2.8.2. Set up via `electron-updater`
  + a static GitHub release feed.
- **(Medium priority)** **Documentation site** — `docs/` directory
  has good content but no static-site generation. Use VitePress or
  similar to publish at `docs.odia.app` (or wherever).
- **(Low priority)** **`brew tap` recipe** for macOS installation
  via `brew install odia`. Adds discovery for the technical user
  base.

### Dimension 6 — Community + adoption
**Status: 10%.**

This is the dimension where the project has the most ROOM to grow.
The platform is technically excellent but has zero external
adoption signals.

Remaining work:
- **(Highest priority)** **README polish for first-time visitors** —
  current README is functional but doesn't sell the platform. Add:
  a short demo video (the intro is perfect for this), a "what does
  this do" example walkthrough, a "who is this for" section.
- **(High priority)** **Public demo deployment** — a hosted
  read-only demo that shows the dashboard with synthetic data so
  prospective users don't have to install to try. Vercel/Render
  free tier handles this.
- **(High priority)** **Case study writeups** — the user's own
  Tulare County / Sunshine Dragnet investigation work IS the case
  study. Publish 1-2 redacted case studies at `docs/case-studies/`
  showing how O.D.I.A. found specific compliance gaps. Massively
  increases credibility.
- **(Medium priority)** **Contributor docs** —
  `CONTRIBUTING.md` exists but the bar for new contributors is
  high. Add: "your first detector" tutorial, "your first
  jurisdiction" tutorial, "your first audit" tutorial.
- **(Medium priority)** **License clarity** — current `LICENSE` is
  good but the dual nature (open source + intended for civic use)
  could benefit from a `CODE_OF_CONDUCT.md` and a `GOVERNANCE.md`
  explaining how the project is run.
- **(Low priority)** **Public roadmap** — a `ROADMAP.md` listing
  v2.9.x mobile, v2.10.x reach features, v3.0.x next-gen items.
  Helps prospective users decide whether to invest.

---

## 3 · Recommended sequence to "outstanding"

If the goal is to move from v2.8.2 → "fully matured outstanding"
in roughly 90 days, here's the priority ordering:

### Sprint 1 (weeks 1-2) — Visible polish
- v2.8.2 lands (this handoff): intro fix, page-hero textures,
  light-class sweep, icon refresh.
- v2.8.3: detector calibration sweep, cross-detector dedup,
  confidence scoring (Dimension 2 finish).

### Sprint 2 (weeks 3-4) — Distribution prep
- Code-signed installers (Apple Developer enrollment + EV cert).
- Auto-update via `electron-updater` + GitHub releases.
- README polish + first demo video.

### Sprint 3 (weeks 5-7) — Mobile track
- v2.9.0 mobile (Capacitor) — already fully specified in the
  prior handoff. ~14 commits.

### Sprint 4 (weeks 8-9) — Reliability + privacy
- Application telemetry (local-only structured event log).
- Crash recovery (in-progress audit checkpointing).
- Encryption at rest (SQLCipher + Fernet).
- `docs/SECURITY.md`.

### Sprint 5 (weeks 10-12) — Reach
- Documentation site (VitePress).
- Public demo deployment.
- Case study writeups (1-2 redacted Tulare County stories).
- Contributor docs.

At the end of Sprint 5, the project is at **v2.10.0** and meets
every criterion in this report.

---

## 4 · What "outstanding" looks like, concretely

When all six dimensions are at 95%+, a new user's experience is:

1. They land on `odia.app` (the docs site) via a search for
   "civic accountability software." The README opens with the
   intro video — gold swirl, ODIA glyph, recursive scalar formula,
   "We the People" declaration. They feel the gravity.

2. They click "Try the demo." A hosted read-only deployment loads.
   The dashboard shows the gold-veined malachite hero, severity
   tiles in mineral tones, real synthetic finding data in the
   panels below. They click around for 3 minutes and understand
   the product.

3. They click "Install for desktop." A code-signed `.exe` /
   `.dmg` / `.AppImage` downloads. No "untrusted publisher"
   warnings. The installer runs the intro once on first launch.

4. They upload their first PDF. The audit runs in 8 seconds. The
   evidence packet reads like an abbreviated MAS report — vendor
   names, dollar amounts, statutes inline, plain-language
   explanations. They share the packet with a colleague.

5. Six weeks later their workflow includes: capture Flock cameras
   on their phone via the iOS app (v2.9.0), pull CPRA responses
   into the desktop app, run RAIA synthesis across 5 jurisdictions,
   export a litigation-grade chain-of-custody DOCX. The platform
   is invisible — it does what they need without ceremony.

That's the "outstanding" target. Every item in the maturity report
above is a concrete step toward that experience.

---

## 5 · The honest summary

v2.8.2 is **production-grade**. It would not be embarrassing to
ship today. The brand identity is locked, the analysis layer is
mature, the visual surfaces are coherent.

To reach "outstanding" requires **~90 days of sustained finish
work** plus the v2.9.0 mobile sprint. The work is well-defined,
relatively low-risk, and broken into tractable sprints.

The biggest risk is NOT under-engineering — it's the opposite.
Adding more features will dilute focus. The maturity work is
about **completing what's been started** in the six dimensions
above, not adding new dimensions.

— maturity report, generated v2.8.2 baseline
