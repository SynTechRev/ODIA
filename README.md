<div align="center">

# O.D.I.A.
### Oraculus Decimus Intellect Analyst

**A civic accountability intelligence platform for forensic analysis of legal and government documents.**

[![Version](https://img.shields.io/badge/version-v3.8.3-00ff9d?style=flat-square&labelColor=0e0e14)](https://github.com/SynTechRev/ODIA/releases/tag/v3.8.3)
[![Python](https://img.shields.io/badge/python-3.11%2B-d8b13c?style=flat-square&labelColor=0e0e14)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-00ff9d?style=flat-square&labelColor=0e0e14)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-d8b13c?style=flat-square&labelColor=0e0e14)](https://github.com/SynTechRev/ODIA/releases/latest)
[![Tests](https://img.shields.io/badge/tests-3400%2B%20passing-00ff9d?style=flat-square&labelColor=0e0e14)](https://github.com/SynTechRev/ODIA/actions)
[![Local First](https://img.shields.io/badge/local--first-no%20cloud%20required-d8b13c?style=flat-square&labelColor=0e0e14)](#privacy--security)

<br>

### [⬇ &nbsp; Download Latest Release &nbsp; →](https://github.com/SynTechRev/ODIA/releases/latest)
**[All Releases & Changelogs](https://github.com/SynTechRev/ODIA/releases)**

</div>

---

Ingest legal and government documents (PDF, XML, JSON, TXT, DOCX, HTML, scanned TIFF). Run them through **20 detection layers** — ten civic-integrity detectors plus ten legal-reasoning detectors — to surface fiscal anomalies, constitutional concerns, surveillance outsourcing, procurement irregularities, statutory misapplication, and case-law currency issues. Reconstruct contract lineages, evaluate compliance against the ACLU CCOPS framework, query the full audit corpus in natural language via a local RAG pipeline, and generate litigation-grade reports — all **locally**, with full SHA-256 provenance. No cloud, no telemetry, no required API keys.

---

## Download

### Desktop App (recommended)

Standalone installer — no Python, Docker, or command line required.

| Platform | Installer | Architecture |
|---|---|---|
| **Windows** | [ODIA-Setup-3.8.3.exe](https://github.com/SynTechRev/ODIA/releases/download/v3.8.3/ODIA-Setup-3.8.3.exe) | x64 |
| **macOS (Apple Silicon)** | [ODIA-3.8.3-arm64.dmg](https://github.com/SynTechRev/ODIA/releases/download/v3.8.3/ODIA-3.8.3-arm64.dmg) | arm64 (M1/M2/M3/M4) |
| **macOS (Intel)** | [ODIA-3.8.3-x64.dmg](https://github.com/SynTechRev/ODIA/releases/download/v3.8.3/ODIA-3.8.3-x64.dmg) | x64 |
| **Linux** | [ODIA-3.8.3.AppImage](https://github.com/SynTechRev/ODIA/releases/download/v3.8.3/ODIA-3.8.3.AppImage) | x64 |

**System requirements:** Windows 10 x64 · macOS 10.15+ · Ubuntu 18.04+ (requires `libfuse2`)

> First-time setup: [docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md) — written for non-developers.

> **Upgrading from v3.8.2 or earlier?** Run `python scripts/migrate_db_to_userdata.py` once after install to move your audit corpus to the new persistent storage location.

### Other Install Methods

<details>
<summary><strong>Docker</strong> (containerized — no Python or Node required)</summary>

```bash
docker build -t odia . && docker run -p 8080:8080 odia
# Open http://localhost:8080
```

</details>

<details>
<summary><strong>Python / CLI</strong> (source workflow)</summary>

```bash
git clone https://github.com/SynTechRev/ODIA.git && cd ODIA
pip install -e .
python scripts/run_audit.py --source data/demo/ --output reports/demo/
```

Full walkthrough: [QUICKSTART.md](QUICKSTART.md)

</details>

<details>
<summary><strong>PWA / Mobile</strong></summary>

Open your O.D.I.A. instance in Safari (iOS) or Chrome/Edge (Android) and add to home screen — installs as a fullscreen app with the gemstone UI, offline shell, and native-feel pull-to-refresh.

| Platform | Install |
|---|---|
| iOS | Safari → Share → Add to Home Screen |
| Android | Chrome/Edge/Samsung Internet → Install prompt or three-dot menu |
| Desktop | Chromium-based browsers → Install icon in URL bar |

</details>

---

## Quick Start (developers)

```bash
git clone https://github.com/SynTechRev/ODIA.git && cd ODIA
pip install -e ".[dev]"

# Start API server
uvicorn oraculus_di_auditor.interface.api:app --reload

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
# Open http://localhost:3000

# Run tests
pytest
```

---

## What's New

### v3.8.3 — Version Badge Fix · ODIA_VERSION Injection
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.8.3)

Corrects the version badge shown in the desktop app's status bar. PyInstaller bundles built from editable installs (`pip install -e .`) lack a traditional dist-info directory, so `importlib.metadata.version("odia")` could surface stale metadata from a prior install. Starting with this release, `backend.js` injects `ODIA_VERSION` from `desktop/package.json` into the backend process environment and `api.py` checks that variable first — the status bar now always reflects the installed package version exactly.

- **`backend.js`** now passes `ODIA_VERSION: <package.json version>` to every backend process spawn
- **`api.py`** checks `ODIA_VERSION` env var before falling back to `importlib.metadata`
- Desktop hero and status bar version strings are now in guaranteed agreement

---

### v3.8.2 — Desktop DB Path · Documents Stat Tiles · Migration Script
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.8.2)

Resolved the root cause of missing corpus data in the desktop app and fixed the Documents page stat tiles that showed 0/0/0 for corpora where all documents carry a null jurisdiction.

- **Desktop DB path fixed** — `backend.js` now routes the database to `app.getPath("userData")` (`%APPDATA%\ODIA\` on Windows; `~/Library/Application Support/ODIA/` on macOS) instead of the PyInstaller bundle directory, so the database survives reinstalls and is never overwritten by an upgrade
- **Documents stat tiles fixed** — `/api/v1/documents` now returns `total_anomaly_count` across all matched documents; the Documents page uses this field directly so totals are correct even when no jurisdiction tags are set
- **`scripts/migrate_db_to_userdata.py`** — one-time migration utility that copies the dev/source corpus to the new userData path. Run once after upgrading from v3.8.1 or earlier:
  ```powershell
  python scripts/migrate_db_to_userdata.py
  ```

---

### v3.8.1 — Desktop Tab-Navigation Fix
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.8.1)

Critical patch for the Electron desktop build. webpack's `publicPath: "auto"` bakes the literal string `"auto"` into `<script>` paths at build time, producing `autostatic/chunks/…` paths that don't exist on disk. The App Router chunks fail to load, React cannot mount, and every tab shows a white page. This release fixes `scripts/fix_electron_paths.py` to rewrite those paths in all 13 HTML files at build time so every tab navigates cleanly on `file://` protocol.

- **Root cause fixed**: `autostatic/chunks/` → correct relative `_next/static/chunks/` path in all HTML files
- **No more white pages** on Legal, Analysis, Documents, Anomalies, Synthesis, or any other tab
- All version strings unified at `v3.8.1`

---

### v3.8.0 — odia_legal Phase 6 · Multi-State Corpus · OCR Pipeline
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.8.0)

The legal corpus reaches full Phase 6 coverage. Ten legal detectors are live, wired into the analyze pipeline, and persisted to the database on every document run.

**Legal corpus (Phase 6):**
- **Federal adjudication corpus** — Office of Administrative Hearings (OAH), Merit Systems Protection Board (MSPB), Equal Employment Opportunity Commission (EEOC), Privacy and Civil Liberties Oversight Board (PCLOB)
- **Multi-state public records corpus** — Oregon, Washington, and Texas public records law (OR, WA, TX), extending L-1 beyond California
- `GET /api/v1/legal/reeval` — Vector 3 temporal re-evaluation endpoint
- Legal analysis page on the frontend with full API client wiring
- RAG index enriched with L-1 through L-10 legal findings at build time

**Pipeline improvements:**
- `odia_legal` fully wired into `analyze_document()` — legal findings now persist to the `anomalies` table on every audit run
- `OCR for image-embedded PDFs` via PyMuPDF + Tesseract with 30MP pixel cap (prevents slow scans on large microfilm images)
- `bulk_ingest.py` text-extraction cache — eliminates multi-hour re-runs on large corpora by caching extracted text per document
- Auto-load `.env` at startup — CORS origin and RAG provider now persisted across restarts
- Two-layer RAG query enrichment with legal domain taxonomy

**Developer tooling:**
- `scripts/triage_agent.py` — ranked document review queue by anomaly density
- `scripts/export_training_data.py` — SFT-format training data export for Oraculus model instruction-tuning
- `scripts/ingest_monitor.py` — live DB stats dashboard

---

### v3.7.0 / v3.7.1 — odia_legal Submodule · 10 Legal Detectors · Vector 3
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.7.0)

The `odia_legal` submodule ships its full detector suite — ten legal-reasoning detectors that apply statutory, procedural, constitutional, and case-law analysis to every document.

**Detectors (L-1 through L-10):**

| Detector | Name | What it catches |
|---|---|---|
| **L-1** | Statutory Applicability | 13 applicability rules across 5 legal domains (CPRA, AB 481, JAG, civil rights, ALPR) |
| **L-2** | Procedural Compliance | CPRA response timing violations, denial without justification, AB 481 + JAG procedural gaps |
| **L-3** | Exemption Misapplication | Overbroad / unsupported exemption claims under CPRA, SB 1421, AB 481, ALPR statutes |
| **L-4** | Ministerial Duty Analysis | Discretionary act misclassified as ministerial; failure to act on non-discretionary duties |
| **L-5** | Federal Grant Compliance | 2 CFR Part 200 + 28 CFR Part 23 violations; JAG / Byrne / COPS anti-supplanting triggers |
| **L-6** | Constitutional Implication | 1st, 4th, 14th Amendment friction; surveillance without judicial oversight |
| **L-7** | Regulatory Authority Chains | Agency action outside delegated authority; ultra vires rulemaking |
| **L-8** | Case-Law Currency | Overruled, superseded, or eroded precedents cited as current authority |
| **L-9** | Recodification Translation | CPRA § 6250–6270 → § 7920.000 family crosswalk; stale citation detection |
| **L-10** | Balancing Test Analyzer | Mathews v. Eldridge, CPRA § 7922.000, Carpenter mosaic-theory analysis |

**Legal infrastructure:**
- **Citation graph** (NetworkX) — `CITES / AMENDS / IMPLEMENTS / OVERRULED_BY` edge types across the full corpus
- **CourtListener integration** — opt-in live case-law lookups via `COURTLISTENER_API_KEY` (never default)
- **Citation formatter** — CA Style Manual, Bluebook, plain English, and Markdown output
- **Memorandum generator** — litigation-grade legal memos with Table of Authorities
- **Plain-language explainer** — community-education summaries of findings for non-lawyers
- **Vector 3 engine** — temporal re-evaluation of case-law currency over time
- **Training data export** — instruction-tuning SFT export from the full legal corpus

**Corpus:**
- California code ingestion: 68 sections across 5 codes (Gov, Pen, Ed, Wel & Inst, Health & Safety)
- CFR: 24 sections (2 CFR Part 200, 28 CFR Part 23)
- CPRA California case law: 7 annotated cases with holdings and treatment signals

---

### v3.6.0 — Detector Expansion · RAG Multi-Index · CI Hardening
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.6.0)

- **Grant funding trails detector** — traces funding provenance through contract chains to surface JAG / COPS / Byrne pass-through irregularities
- **Vote-date alignment detector** — flags contracts executed before authorizing resolutions or board approvals
- **RAG multi-index routing** — `corpus_filter` parameter routes queries to `corpus`, `ace`, or `jim` sub-indexes independently; index builder populates all three
- **FastAPI lifespan migration** — all `@app.on_event("startup")` handlers converted to `lifespan` context manager (eliminates deprecation noise in every test run)
- CI hardening: persistent pre-commit workflow failures resolved; custom schema-validation step for empty-corpus environments

---

### v3.5.0–v3.5.3 — Oraculus RAG on Ollama · RAG Query UI
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.5.3)

- **Oraculus RAG engine live** — `POST /api/v1/rag/query` backed by local Ollama `llama3.1:8b` with 300s timeout for cold model loads; `build_rag_index.py` builds TF-IDF vector index from the live audit database
- **RAG Query page** — natural language interface to the full audit corpus directly in the desktop UI
- **Dual-path status** — `/api/v1/rag/status` reports corpus stats and model availability independently so a missing model doesn't mask an indexed corpus
- Route prefix fixes, Suspense wrapper removal, field-name corrections

---

### v3.4.0 — Operator Experience · Upload DB Persistence · Inline RAIA
> [Release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.4.0)

- **Upload audit DB persistence** — every Upload-page audit run persists documents, analyses, and anomalies to the backend database; Documents, Anomalies, and Synthesis pages now reflect upload-audit data alongside webhook-ingested data
- **Jurisdiction field on Upload** — tag audit batches at submission; value persists in localStorage across navigations
- **Audit history scaled to 10,000 entries** — switched from full payloads (~100–500 KB each) to lightweight metadata summaries (~300 bytes), eliminating the 5–10 MB localStorage ceiling
- **Inline RAIA synthesis** — Run synthesis directly from the Synthesis page; Markdown report renders inline with Copy + Download controls
- **SynTechRev brand** — Oraculus monogram across all icon slots (browser favicon, PWA, Electron dock, Windows ICO)
- **34 U.S.C. § 10152 JAG statute** embedded in grant findings via the legal resolver

<details>
<summary>Earlier v3.x releases (v3.0–v3.3)</summary>

**v3.3.1** — PyYAML declared as explicit dependency; `LegalResolver` CWD-independence fix.

**v3.3.0** — Full United States Code corpus (53 titles, 52,586 sections) as a git submodule; `LegalResolver` pre-warms at boot.

**v3.2.5** — `.docx`, `.doc` (OLE + antiword), and multi-page TIFF OCR ingestion; magic-byte sniffing for extension-less archive URLs (Questys CMX).

**v3.2.0–v3.2.4** — 5 new DB-backed list endpoints; Suspense wrapper for Next.js static-export compatibility; 15-test audit-consistency suite; Drupal semantic-container HTML extraction.

**v3.1.0–v3.1.1** — `curl_cffi` Chrome impersonation as Tier-2 HTTP fallback (bypasses Akamai/Cloudflare bot detection); HTML ingestion branch.

**v3.0.0–v3.0.5** — Production multi-platform desktop release; backend-side URL scraping; async fire-and-forget scrape worker; RAIA pattern detection hardening.

Full changelog: [CHANGELOG.md](CHANGELOG.md)

</details>

---

## Empirical State (live as of v3.8.3)

ODIA has ingested and fully analyzed **9,546 documents across 13 California jurisdictions** on 4 distinct CMS platforms, surfacing **47,251 findings** with a full cross-jurisdiction RAIA synthesis:

| Jurisdiction | Findings | Critical | Notes |
|---|---|---|---|
| Tulare | 9,907 | — | Questys CMX + Drupal |
| Dinuba | 14,011 | — | Highest anomaly density |
| Farmersville | 7,805 | — | CivicPlus |
| Exeter | 5,247 | — | — |
| Lindsay | 5,170 | — | — |
| Visalia PD | 1,699 | — | — |
| Porterville | 1,792 | — | Revize |
| TCSO | 362 | — | — |
| Woodlake | 821 | — | — |
| Visalia | 80 | — | — |
| Tulare County | 119 | — | BOS |
| TCDA | 102 | 0 | DA narratives, WordPress |
| Multi-jurisdiction | 136 | — | Cross-entity references |
| **TOTAL** | **47,251** | **3,234** | **9,546 docs · 13 jurisdictions** |

**Severity breakdown:** Critical 3,234 (6.8%) · High 14,316 (30.3%) · Medium 19,011 (40.2%) · Low 10,690 (22.6%)

Cross-jurisdiction RAIA synthesis surfaces universal patterns including `admin:missing-final-action` (present across all jurisdictions), `signature:unsigned-instrument`, `scope:significant-expansion`, `vendor-convergence:sole-source`, `governance:sole-source-without-justification`, `fiscal:amount-without-appropriation`, and `procurement:sole-source-without-gov-code-citation`. Tulare County critical findings include `grant:jag-without-anti-supplanting` citing 34 U.S.C. § 10152 and `admin:retroactive-authorization` × 29.

---

## Features

### Analysis Pipeline

- **10-detector civic analysis engine** — fiscal, constitutional, surveillance, procurement, signature, scope, governance, administrative integrity, grant compliance (JAG / COPS / Byrne anti-supplanting), and cross-entity reference detection — all local, no cloud calls
- **10 legal-reasoning detectors** — L-1 through L-10 covering statutory applicability, procedural compliance, exemption misapplication, ministerial duty, federal grant compliance, constitutional implication, regulatory authority chains, case-law currency, recodification translation, and balancing-test analysis
- **Multi-format ingestion** — PDF (with PyMuPDF OCR fallback), XML, JSON, TXT, DOCX, DOC, HTML, multi-page TIFF
- **Legistar retrieval** — pull legislative documents from 50 preconfigured city portals

### Legal Corpus

- **California statutes** — 68 sections across Gov, Pen, Ed, Wel & Inst, and Health & Safety codes
- **CFR** — 2 CFR Part 200 (Uniform Guidance) and 28 CFR Part 23 (Criminal Intelligence Systems)
- **U.S. Code** — 52,586 sections (53 titles) via `nickvido/us-code` git submodule
- **Federal adjudication** — OAH, MSPB, EEOC, PCLOB corpora
- **Multi-state public records** — California, Oregon, Washington, Texas
- **CPRA case law** — 7 annotated California cases with holdings and treatment signals
- **Citation graph** — NetworkX graph with `CITES / AMENDS / IMPLEMENTS / OVERRULED_BY` edges
- **CourtListener** — opt-in live lookups via `COURTLISTENER_API_KEY` (never default)

### Intelligence & Reporting

- **RAG query engine** — `POST /api/v1/rag/query` backed by local Ollama `llama3.1:8b`; multi-index routing across `corpus`, `ace`, and `jim` sub-indexes; two-layer legal domain enrichment
- **Cross-jurisdiction RAIA synthesis** — pattern detection across all ingested jurisdictions with confidence-scored shared findings
- **CCOPS compliance scorecard** — 11 ACLU model bill mandates with per-mandate status and risk level
- **Memorandum generator** — litigation-grade legal memos with Table of Authorities
- **Plain-language explainer** — community-facing summaries of legal findings
- **Evidence packet export** — chain-of-custody ZIP with SHA-256 hashes, Markdown, HTML, PDF, and DOCX formats

### Platform

- **Multi-agent orchestration** — six-stage task graph (ingestion → analysis → anomaly → synthesis → database → interface)
- **n8n integration** — token-gated webhook surface for scheduled scrapes and external triggers
- **Manual Triggers panel** — RAIA synthesis, CPRA deadline checking, jurisdiction seeding — no n8n required
- **REST API** — FastAPI with 50+ endpoints; auto-docs at `/docs` and `/redoc`
- **Gemstone HUD** — smoke-spine background, matte gold + neon emerald dual-edge cuts, crystallized quartz-facet panels
- **PWA** — installable mobile app with camera capture, OCR image upload, and `navigator.share()`
- **Auth + workspace** — JWT + bcrypt with single-user fallback; chain-of-custody `AuditLog`
- **Privacy-first** — 100% local processing, no telemetry, no required LLM keys, no internet after install

---

## Architecture

```
src/
├── oraculus_di_auditor/   # Main platform (200+ modules)
│   ├── analysis/          # 10 civic-integrity detectors
│   ├── ingestion/         # PDF / XML / JSON / TXT / DOCX / HTML / TIFF + OCR
│   ├── orchestrator/      # Multi-agent task graph (Phase 5/8)
│   ├── governor/          # Policy enforcement, security gatekeeper (Phase 9)
│   ├── interface/         # FastAPI app + modular route modules
│   │   └── routes/        # 20+ route modules (upload, audit, legal, rag, …)
│   ├── reporting/         # Pydantic models, Jinja2 templates, plain-language,
│   │                      # evidence-packet ZIP generator
│   ├── rag/               # Retrieval engine, context builder, prompt router
│   ├── adapters/          # CCOPS (11 mandates), Atlas, Legistar (50 cities)
│   ├── temporal/          # Contract lineage, evolution detectors, timeline
│   ├── multi_jurisdiction/# Registry, runner, pattern detector, comparative reports
│   ├── auth/              # User / Session / JWT / bcrypt
│   ├── workspace/         # Workspace, member, AuditLog (chain-of-custody)
│   ├── db/                # SQLAlchemy models, CRUD, session
│   └── raia/              # Recursion Analysis Investigative Audit service
├── odia_legal/            # Legal corpus submodule
│   ├── detectors/         # L-1 through L-10 legal-reasoning detectors
│   ├── citations/         # Citation parser, NetworkX graph, formatter
│   ├── corpus/            # Cal. codes, CFR, case law, multistate, adjudication
│   ├── treatment/         # CourtListener client, case-currency tracker
│   ├── reports/           # Memorandum generator, plain-language explainer
│   ├── pipeline.py        # Full legal analysis pipeline
│   └── vector3.py         # Temporal re-evaluation engine
└── oraculus/              # Legacy thin wrapper (backward compat)

frontend/                  # Next.js 14 + Electron desktop
├── app/                   # App Router pages (Dashboard, Upload, Legal, RAG, …)
├── components/            # Gemstone HUD component library
└── lib/                   # API client, navigation, Zustand stores

desktop/                   # Electron main process + build config
scripts/                   # Pipeline, ingestion, triage, training data export
data/
├── legal_corpora/         # us-code git submodule (52,586 USC sections)
└── n8n-workflows/         # Reference automation workflows
```

Full details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/PHASES.md](docs/PHASES.md)

---

## API Reference

FastAPI auto-docs at `/docs` (Swagger) and `/redoc`. Core surfaces:

<details>
<summary><strong>Core Analysis + Upload</strong></summary>

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health + version |
| `POST` | `/api/v1/analyze` | Analyze a single document |
| `GET` | `/api/v1/detectors` | List registered detectors + anomaly types |
| `POST` | `/api/v1/upload` | Upload PDF / TXT / JSON / XML / DOCX |
| `POST` | `/api/v1/upload/batch` | Multi-file upload |
| `POST` | `/api/v1/upload/image` | Image upload + OCR (JPEG / PNG) |
| `POST` | `/api/v1/audit/run` | Start an audit job |
| `GET` | `/api/v1/audit/status/{job_id}` | Poll progress |
| `GET` | `/api/v1/audit/results/{job_id}` | Full results |
| `GET` | `/api/v1/audit/export/{job_id}` | Markdown / HTML / PDF / DOCX export |
| `GET` | `/api/v1/audit/evidence-packet/{job_id}` | Chain-of-custody ZIP |

</details>

<details>
<summary><strong>Legal Analysis</strong></summary>

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/legal/analyze` | Run L-1–L-10 detectors on a document |
| `POST` | `/api/v1/legal/memorandum` | Generate litigation-grade memorandum |
| `POST` | `/api/v1/legal/explain` | Plain-language community explainer |
| `POST` | `/api/v1/legal/reeval` | Vector 3 temporal re-evaluation |
| `GET` | `/api/v1/legal/status` | Corpus health + indexed counts |

</details>

<details>
<summary><strong>RAG · Dashboard · Orchestrator · Compliance</strong></summary>

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/rag/query` | Natural language query (Ollama llama3.1:8b) |
| `GET` | `/api/v1/rag/status` | Model availability + corpus stats |
| `GET` | `/api/v1/dashboard/summary` | Aggregated counters |
| `POST` | `/api/v1/dashboard/seed-jurisdictions` | Seed example jurisdiction configs |
| `GET` | `/api/v1/orchestrator/task-graph` | Six-agent static topology |
| `GET` | `/api/v1/orchestrator/executions` | Recent execution history |
| `POST` | `/api/v1/orchestrator/run` | Multi-document orchestration |
| `GET` | `/api/v1/governor/state` | Pipeline health |
| `POST` | `/api/v1/compliance/assess` | CCOPS scorecard |
| `GET` | `/api/v1/compliance/mandates` | 11 CCOPS mandates |

</details>

<details>
<summary><strong>Triggers · Webhooks</strong></summary>

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/triggers/cpra-deadlines/{72h\|7d\|30d}` | Closing CPRA requests |
| `POST` | `/api/v1/triggers/raia-synthesize-all` | Cross-jurisdictional synthesis |
| `POST` | `/api/v1/triggers/provenance-chain-export` | Litigation-grade export |
| `POST` | `/api/v1/webhook/ingest-and-analyze` | WF-001 CivicPlus scraper (token-gated) |
| `POST` | `/api/v1/webhook/batch-ingest` | WF-002 nightly batch (token-gated) |
| `POST` | `/api/v1/webhook/synthesize` | WF-010 RAIA synthesis distributor (token-gated) |

</details>

---

## Automation (n8n)

O.D.I.A. ships a token-gated webhook surface for scheduled ingestion and synthesis from [n8n](https://n8n.io/) workflows. The **Manual Triggers** panel works without n8n — no additional setup required.

```bash
cp .env.example .env
# Set ODIA_WEBHOOK_TOKEN / N8N_ENCRYPTION_KEY / POSTGRES_PASSWORD

docker compose -f docker-compose.yml -f docker-compose.n8n.yml up -d
# n8n editor → http://localhost:5678
```

Reference workflows: `data/n8n-workflows/bundle.json` (all ship **inactive** by design).
Full setup: [docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md)

---

## Configuration

```yaml
# config/defaults.yaml
pdf_storage: "external"
redaction:
  enabled: false
  auto_detect_pii: true
ollama:
  host: "localhost"
  port: 11434
  default_model: "llama3.1:8b"
```

- **Corpus**: copy `config/corpus_manifest.example.json` → `config/corpus_manifest.json`
- **Multi-jurisdiction configs**: use the **Seed Example Jurisdictions** trigger on the Automation tab, then edit JSON files in `%APPDATA%\ODIA\config\multi_jurisdiction\` (Windows) or the platform equivalent
- **CourtListener**: set `COURTLISTENER_API_KEY` environment variable to enable live case-law lookups — disabled by default

---

## Privacy & Security

- **No automatic external data uploads** — all analysis is local; the only optional outbound calls are Legistar public-portal fetches and explicitly configured n8n webhooks
- **No telemetry** — O.D.I.A. never phones home
- **No required LLM keys** — OpenAI / Anthropic integration is opt-in for RAG only
- **CourtListener lookups are opt-in** — enabled only when `COURTLISTENER_API_KEY` is set
- **Webhook endpoints fail loud** — refuse to register if `ODIA_WEBHOOK_TOKEN` is unset
- **PII redaction is NOT automatic** — manual review required before publishing reports
- **SHA-256 chain-of-custody** on every document

See [docs/DATA_POLICY.md](docs/DATA_POLICY.md) and [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md).

---

## Development

```bash
pip install -e ".[dev]"
pytest --cov=src/oraculus_di_auditor --cov-report=term-missing

black src tests scripts
ruff check src tests scripts

cd frontend && npm install && npm run dev
```

Anomaly detector contract (enforced across all 20 detectors):

```python
{
    "id":       str,   # stable dot-namespaced: "fiscal:missing-provenance-hash"
    "issue":    str,   # concise human-readable description
    "severity": str,   # "low" | "medium" | "high" | "critical"
    "layer":    str,   # detector name: "fiscal", "l1_statutory_applicability", …
    "details":  dict,  # structured evidence
}
```

- [docs/developer-setup.md](docs/developer-setup.md) — full dev environment
- [docs/development-workflow.md](docs/development-workflow.md) — contribution flow
- [docs/RELEASING.md](docs/RELEASING.md) — release runbook
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture
- [docs/PHASES.md](docs/PHASES.md) — phase-by-phase engine reference

---

## Documentation

| Guide | Audience |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | Everyone — 60-second demo + first audit |
| [docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md) | Non-developers — desktop install through optional n8n |
| [docs/MULTI_JURISDICTION.md](docs/MULTI_JURISDICTION.md) | Operators — comparative analysis across cities |
| [docs/COMPLIANCE_FRAMEWORK.md](docs/COMPLIANCE_FRAMEWORK.md) | Operators — CCOPS mandate mapping |
| [docs/RAG_SETUP.md](docs/RAG_SETUP.md) | Developers — Ollama RAG setup |
| [docs/LEGAL_REFERENCE.md](docs/LEGAL_REFERENCE.md) | Everyone — legal reference dataset |
| [docs/OCR_SETUP.md](docs/OCR_SETUP.md) | Developers — Tesseract / Poppler setup |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Developers — system architecture |
| [docs/PHASES.md](docs/PHASES.md) | Developers — phase-by-phase engine reference |
| [docs/database-design.md](docs/database-design.md) | Developers — schema reference |
| [CHANGELOG.md](CHANGELOG.md) | Everyone — full version history |

---

<div align="center">

**Copyright © 2025 Synthetic Technology Revolution — MIT License**

[Issues](https://github.com/SynTechRev/ODIA/issues) · [Releases](https://github.com/SynTechRev/ODIA/releases) · [Docs](docs/)

</div>
