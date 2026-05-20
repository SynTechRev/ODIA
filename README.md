# O.D.I.A. — Oraculus Decimus Intellect Analyst

A general-purpose **civic accountability intelligence platform** for forensic
analysis of legal and government documents.

Ingest legal documents (PDF, XML, JSON, TXT), detect anomalies across ten
specialized layers (fiscal, constitutional, surveillance, procurement, signature,
scope, governance, administrative, grant compliance, **cross-entity**),
reconstruct contract lineages, evaluate compliance against the ACLU CCOPS
framework, sweep cross-entity references via the Cross-Entity Analysis Protocol
V1.0 (May 2026), and produce audit-ready reports — all locally, with full
SHA-256 provenance.

**Repository**: https://github.com/SynTechRev/ODIA
**License**: MIT
**Current version**: **3.2.5** — *Microsoft Word + scanned TIFF ingestion*
([release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.2.5))
**Python**: 3.11+

---

## Try It Now

### Desktop App (recommended for non-developers)

Standalone installer — no Python, Docker, or command line required. All
analysis runs locally on your machine.

Download the latest installer from the
[**Releases page**](https://github.com/SynTechRev/ODIA/releases/latest):

| Platform | Installer | Architecture |
|----------|-----------|--------------|
| **Windows** | `ODIA-Setup-3.2.5.exe` | x64 |
| **macOS (Apple Silicon)** | `ODIA-3.2.5-arm64.dmg` | arm64 (M1 / M2 / M3 / M4) |
| **macOS (Intel)** | `ODIA-3.2.5-x64.dmg` | x64 |
| **Linux** | `ODIA-3.2.5.AppImage` | x64 |

**Direct download links (v3.2.5):**
- [Windows x64](https://github.com/SynTechRev/ODIA/releases/download/v3.2.5/ODIA-Setup-3.2.5.exe)
- [macOS Apple Silicon (arm64)](https://github.com/SynTechRev/ODIA/releases/download/v3.2.5/ODIA-3.2.5-arm64.dmg)
- [macOS Intel (x64)](https://github.com/SynTechRev/ODIA/releases/download/v3.2.5/ODIA-3.2.5-x64.dmg)
- [Linux AppImage](https://github.com/SynTechRev/ODIA/releases/download/v3.2.5/ODIA-3.2.5.AppImage)

**System Requirements:**
- **Windows:** Windows 10 (64-bit) or later
- **macOS:** macOS 10.15 (Catalina) or later
- **Linux:** Ubuntu 18.04+ or equivalent (requires `libfuse2`)

**First-time setup walkthrough**:
[docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md) covers everything from
download through optional scheduled-automation setup, written for non-
developers. Start there if you're new.

### With Docker (containerized; no Python/Node required)

```bash
docker build -t odia . && docker run -p 8080:8080 odia
```

Open `http://localhost:8080`. The full platform runs in a single container.

### With Python (CLI / source workflow)

```bash
git clone https://github.com/SynTechRev/ODIA.git && cd ODIA && pip install -e .
python scripts/run_audit.py --source data/demo/ --output reports/demo/
```

Open `reports/demo/audit_report.md` to see 10 synthetic documents analyzed
across the ten-detector pipeline. Full walkthrough: [QUICKSTART.md](QUICKSTART.md)

### Mobile (PWA — v2.9.0)

Open your O.D.I.A. instance in **Safari (iOS)** or **Chrome / Edge / Samsung
Internet (Android)** and add to home screen — installs as a fullscreen app
with the gold-swirl icon, offline shell, and native-feel pull-to-refresh on
long-list pages. No App Store, no Play Store, no review cycle.

| Platform | Distribution | Install path |
|---|---|---|
| **iOS** | Safari | Share → Add to Home Screen |
| **Android** | Chrome / Edge / Samsung Internet | "Install" prompt in-app, or three-dot menu → Install app |
| **Desktop** | Chromium-based browsers | Install icon in URL bar |

The PWA inherits everything the desktop frontend ships: gemstone palette,
texture system, Manual Triggers panel, RAIA synthesis, evidence packet
export. Mobile-specific: card-layout file table, 44px touch targets,
pull-to-refresh on Documents/Results/Anomalies.

Native iOS + Android (Capacitor / App Store / Play Store) are deferred
to v2.9.1+ pending Apple Developer + Google Play Console accounts.

Full walkthrough: [docs/MOBILE.md](docs/MOBILE.md)

---

## Quick Start (for developers)

```bash
# Clone and install
git clone https://github.com/SynTechRev/ODIA.git
cd ODIA
pip install -e ".[dev]"

# Run tests (3000+ tests across the analysis, ingestion, orchestrator,
#  webhook, dashboard, and Legistar suites)
pytest

# Start the API server
uvicorn oraculus_di_auditor.interface.api:app --reload

# Start the frontend (separate terminal)
cd frontend && npm install && npm run dev
# Open http://localhost:3000
```

---

## What's New in v3.x (current)

The v3 release line shipped automated multi-CMS scraping + ingestion + cross-jurisdiction RAIA synthesis at scale. Empirically validated on **4 jurisdictions / 848 documents / 324 anomalies** across **4 distinct CMS platforms** (CivicPlus, Revize, WordPress, Drupal + Questys CMX).

**v3.2.5 — Microsoft Word + scanned TIFF ingestion** ([release notes](https://github.com/SynTechRev/ODIA/releases/tag/v3.2.5))

Closes the format gap for legacy civic-records archives. Tulare County's Questys CMX archive serves ~20 years of Board of Supervisors agendas, packets, resolutions, and staff reports as a mix of PDF / DOC / DOCX / HTML / scanned TIFF. v3.2.4 recognised only PDF and HTML; v3.2.5 adds:

- **`.docx`** via `python-docx` (paragraphs + tables, headers/footers skipped)
- **`.doc`** (OLE binary, pre-2013 Word) via `antiword` / `libreoffice` subprocess with graceful empty-text fallback
- **`.tif` / `.tiff`** multi-page OCR via `PIL.Image.seek` + `pytesseract` (scanned 2001-2009 microfilm records)
- Magic-byte sniffing in the async-scrape worker for ID-only URLs (Questys `File.ashx?id=N` carries no extension): OLE → `.doc`, ZIP → `.docx`, `II*\x00`/`MM\x00*` → `.tif`
- 4 new tests + v3.2.4 regression guard = 5/5 green

**v3.2.0 → v3.2.4 — Operator UI parity + Drupal extraction + audit-consistency tests**

- **v3.2.0**: 5 new DB-backed list/query endpoints (`/documents`, `/anomalies`, `/analyses`, `/jurisdictions`, `/synthesis/aggregates`) + 4 listing pages swapped from browser localStorage to backend fetches. Closes a year-old gap where webhook-ingested data was invisible in the operator UI.
- **v3.2.1**: Suspense wrapper for `useSearchParams()` (Next.js 15 static-export compatibility) — unblocked desktop builds.
- **v3.2.2 / v3.2.3**: 15-test audit-consistency suite (Test A determinism + Test B MAS faithfulness vs raw SQL + Test C RAIA subphase contract). CRLF-aware fixture-size assertions for Linux CI parity.
- **v3.2.4**: Semantic-container HTML extraction (`<main>` → `<article>` → `[role="main"]`) — fixed Drupal sites where the v3.1.1 generic strip missed `<div>`-wrapped nav cruft and drowned the article body.

**v3.1.0 → v3.1.1 — Tier-2 fetcher + HTML ingest**

- **v3.1.0**: `curl_cffi` Chrome impersonation as a Tier-2 fallback for HTTP 403/429/OSError — defeats Akamai/Cloudflare bot mitigation that pre-v3.1.0 made entire jurisdictions unreachable.
- **v3.1.1**: HTML (`.html`/`.htm`) ingestion branch + filename-suffix logic respecting the recognised types. Unblocked WordPress-based jurisdictions.

**v3.0.0 → v3.0.5 — Live automation goes online**

- **v3.0.0**: Production multi-platform desktop release (Windows / macOS arm64 / macOS Intel / Linux AppImage) — Oraculus monogram, malachite hero, RAIA template hardening, mesh-job zombie reconciliation.
- **v3.0.2**: Backend-side URL scraping via `POST /webhook/scrape-and-ingest` — solves Cloudflare TLS-fingerprint blocks that the n8n HTTP node couldn't bypass.
- **v3.0.3 / v3.0.4**: `POST /webhook/scrape-and-ingest-async` for fire-and-forget downloads + `_DOWNLOAD_SEMAPHORE(4)` concurrency cap + widened OSError catch for `RemoteDisconnected`.
- **v3.0.5**: RAIA pattern-detection polish — `all_anomalies` field surfaces complete shared-finding sets to pattern detectors (previously capped at the top-10 slice).

Older v2.x release cycles (Cross-Entity Analysis Protocol, Mineral Calibration, JARVIS HUD, gemstone palette, OCR coverage) are captured in [CHANGELOG.md](CHANGELOG.md) with full track-by-track detail.

## Empirical State (live as of v3.2.5 + Tulare County BOS bring-up)

ODIA has been live-ingested across 4 California jurisdictions on 4 distinct CMS platforms:

| Jurisdiction | CMS | Docs | Anomalies | Critical | Score |
|---|---|---|---|---|---|
| Tulare County (BOS) | Questys CMX + Drupal | 95 | 119 | 8 | 0.917 |
| Visalia | CivicPlus | 85 | 80 | 5 | 0.932 |
| Porterville | Revize | 8 | 23 | 2 | 0.766 |
| TCDA (DA narratives) | WordPress | 660 | 102 | 0 | 0.989 |
| **TOTAL** | **4 CMS** | **848** | **324** | **15** | — |

**Cross-jurisdiction RAIA synthesis** surfaces **1 universal pattern at 1.00 confidence** (`admin:missing-final-action` — fires in all 4 jurisdictions) and **8 patterns at 0.75 confidence** (3 of 4 jurisdictions): signature-unsigned-instrument, scope-significant-expansion, vendor-convergence:sole-source, shared-layer:administrative, governance:sole-source-without-justification, fiscal:amount-without-appropriation, scope:amendment-without-baseline, procurement:sole-source-without-gov-code-citation. Two **TC-exclusive critical-severity findings** (`grant:jag-without-anti-supplanting`, `admin:retroactive-authorization` × 29) are surfaced exclusively by the BOS corpus.

## What's New in v2.7.x

The v2.7 release line moved O.D.I.A. from a developer tool into a
production-grade desktop application for civic-accountability operators.

**v2.7.8** — TypeScript fix on top of v2.7.7's gemstone palette
propagation: `<AppLink>` and SVG icon components now accept the `style`
prop required by the new CSS-variable-based palette. v2.7.7's tag failed
CI at the typecheck step; v2.7.8 supersedes it with the same gem palette.

**v2.7.7 — Gemstone palette (Y1–Y5)**
- Vibrant neon emerald + matte gold dual-edge tokens propagated platform-wide
- Crystallized facet panel utility (`.gem-panel-faceted` — 12-vertex quartz
  silhouette via clip-path)
- Sidebar, topbar, mobile bottom-tab bar, base components, every Dashboard
  card restyled
- Severity strip on Dashboard rewired to the live `/api/v1/dashboard/summary`
  endpoint (was reading from a dead client-side store)

**v2.7.6 — Functional pass (X1–X5)**
- New dashboard summary endpoint backing the Analysis Summary card
- Frozen-aware jurisdiction discovery + "Seed Example Jurisdictions" trigger
  so RAIA Synthesis works on a fresh desktop install
- Legistar retrieval bridges into the upload-staging store (downloads now
  appear in the Upload page's "files ready" table)
- Audit pipeline records `MeshExecutionJob` rows so the Orchestrator
  timeline reflects actual work
- Initial gemstone hero POC

**v2.7.5 — Manual Triggers wired (W1–W4)**
- ODIA-native `/api/v1/triggers/*` route family bypasses the n8n token
  gate so the Manual Triggers panel works out of the box
- Ingest tab consolidated into Upload (legacy redirect preserved)
- CCOPS Compliance scorecard on HUD primitives

**v2.7.4 — Quality polish (V1–V5)**
- Database initialization at startup (closes silent-degrade gap)
- Dynamic version pill on the sidebar
- Tri-state UX on Orchestrator executions
- Three-state automation tile (`READY` / `OFFLINE` / `NOT CONFIGURED`)

**v2.7.3 — Audit-fix sprint (D1–D8)**
- MAS narrative templates
- General-path SeenHash deduplication
- Fail-loud PDF extraction (no more silent text-extraction failures)
- Orchestrator page rewrite

See [docs/PHASES.md](docs/PHASES.md) for the full version history.

---

## Features

- **Ten-detector analysis engine** — fiscal, constitutional, surveillance,
  procurement, signature, scope, governance, administrative integrity, grant
  compliance (JAG / COPS / Edward Byrne anti-supplanting), and **cross-entity
  reference detection** (D-13, Cross-Entity Analysis Protocol V1.0); all
  executed locally, no cloud calls
- **Multi-format ingestion** — PDF (with OCR fallback), XML, JSON, TXT;
  drag-and-drop or programmatic
- **Legistar retrieval** — pull legislative documents directly from any of 50
  preconfigured city portals (configurable for any city using the Legistar
  platform)
- **Multi-jurisdiction analysis** — compare anomaly patterns across multiple
  jurisdictions in one run; detect vendor-playbook replication, shared
  procurement irregularities, regional governance gaps
- **CCOPS compliance scorecard** — automated assessment against all 11 ACLU
  CCOPS model bill mandates with per-mandate compliance status
- **Temporal pattern detection** — contract lineage reconstruction, six
  evolution-pattern detectors, timeline visualization
- **RAG query engine** — multi-source retrieval across documents, findings,
  analysis results, and legal reference data with LLM-ready context building
- **Legal reference dataset** — 255 searchable terms (Bouvier 1856, Anderson
  1889, Cornell Wex, Latin maxims), 81 SCOTUS / federal cases, 35 extracted
  holdings, superseded-doctrine tracking; all public domain / open access
- **Multi-agent orchestration** — six-stage task graph (ingestion → analysis
  → anomaly → synthesis → database → interface) with dependency resolution
  and execution recording
- **n8n integration** — token-gated webhook surface (`/api/v1/webhook/*`)
  for scheduled scrapes, deadline alerts, and external triggers; bundled
  reference workflows
- **Manual Triggers panel** — RAIA cross-jurisdictional synthesis, CPRA
  deadline checking, jurisdiction seeding from inside the desktop UI; no
  n8n required
- **REST API** — FastAPI backend with 50+ endpoints across analysis,
  orchestration, governance, compliance, retrieval, upload, audit,
  triggers, webhooks, automation, and dashboard surfaces
- **Modern frontend** — Next.js 14 + Electron desktop with the **gemstone
  HUD palette** (smoke-spine background, matte gold + neon emerald dual-edge
  cuts, crystallized quartz-facet panels)
- **PWA support** — installable as a Progressive Web App on mobile with
  responsive layout, camera capture, OCR image upload, navigator.share()
- **Auth + workspace** — JWT + bcrypt with single-user fallback; workspace
  package with chain-of-custody `AuditLog`
- **Provenance tracking** — SHA-256 hashing on every document with
  fingerprinting, lineage, and litigation-grade chain-of-custody export
- **Privacy-first** — all processing is local; no telemetry, no cloud
  dependency, no required LLM API keys, no internet required after install

---

## Architecture

Two source packages under `src/`:

```
src/
├── oraculus_di_auditor/   # Main platform (192+ modules)
│   ├── analysis/          # Nine anomaly detectors
│   ├── ingestion/         # PDF / XML / JSON / TXT parsing + OCR fallback
│   ├── orchestrator/      # Multi-agent task graph (Phase 5/8)
│   ├── governor/          # Policy enforcement, security gatekeeper (Phase 9)
│   ├── interface/         # FastAPI app + 14 route modules
│   ├── reporting/         # Pydantic models, Jinja2 templates, plain-language
│   │                      # translator, evidence-packet ZIP generator
│   ├── rag/               # Retrieval engine, context builder, prompt router
│   ├── legal/             # Case law builder, definition extractor
│   ├── adapters/          # CCOPS adapter (11 mandates), Atlas adapter,
│   │                      # Legistar adapter (50 cities), compliance engine
│   ├── temporal/          # Contract lineage, evolution detectors, timeline
│   ├── multi_jurisdiction/# Registry, runner, pattern detector, comparative
│   │                      # report generator
│   ├── auth/              # User / Session / JWT / bcrypt
│   ├── workspace/         # Workspace, member, AuditLog (chain-of-custody)
│   ├── db/                # SQLAlchemy models, CRUD, session
│   ├── raia/              # Recursion Analysis Investigative Audit service
│   └── ...                # Higher-phase engines (see docs/PHASES.md)
└── oraculus/              # Legislative scaffold (loaders, provenance)
```

Full architecture details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
Phase-by-phase engine reference: [docs/PHASES.md](docs/PHASES.md)

---

## API Endpoints

50+ endpoints across the following surfaces (FastAPI auto-docs at
`/docs` and `/redoc`):

### Core analysis

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health + version |
| `POST` | `/api/v1/analyze` | Analyze a single document |
| `GET` | `/api/v1/detectors` | List registered detectors + anomaly types |

### Upload + audit pipeline

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/upload` | Upload a single PDF / TXT / JSON / XML |
| `POST` | `/api/v1/upload/batch` | Multi-file upload |
| `POST` | `/api/v1/upload/image` | Image upload + OCR (JPEG / PNG) |
| `GET` | `/api/v1/upload/files` | List staged files |
| `POST` | `/api/v1/audit/run` | Start an audit job |
| `GET` | `/api/v1/audit/status/{job_id}` | Poll progress |
| `GET` | `/api/v1/audit/results/{job_id}` | Retrieve full results |
| `GET` | `/api/v1/audit/export/{job_id}` | Export Markdown / HTML / PDF / DOCX |
| `GET` | `/api/v1/audit/evidence-packet/{job_id}` | Download chain-of-custody ZIP |

### Dashboard

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | Aggregated counters for the home page |
| `POST` | `/api/v1/dashboard/seed-jurisdictions` | Copy bundled examples to user dir |

### Orchestrator + Governor

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/orchestrator/task-graph` | Static six-agent topology |
| `GET` | `/api/v1/orchestrator/executions` | Recent MeshExecutionJob rows |
| `GET` | `/api/v1/orchestrator/status` | Live agent / task counters |
| `POST` | `/api/v1/orchestrator/run` | Multi-document orchestration |
| `GET` | `/api/v1/governor/state` | Pipeline health summary |
| `POST` | `/api/v1/governor/validate` | Validate pipeline (quick or deep) |

### Manual Triggers (no auth, no n8n required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/triggers/cpra-deadlines/{72h\|7d\|30d}` | Closing CPRA requests |
| `POST` | `/api/v1/triggers/raia-synthesize-all` | Cross-jurisdictional synthesis |
| `POST` | `/api/v1/triggers/provenance-chain-export` | Litigation-grade export (501 stub at L0) |

### n8n webhooks (token-gated; require `ODIA_WEBHOOK_TOKEN`)

| Method | Path | Used by |
|---|---|---|
| `GET` | `/api/v1/webhook/health` | Liveness probe (no token) |
| `POST` | `/api/v1/webhook/ingest-and-analyze` | WF-001 CivicPlus scraper |
| `POST` | `/api/v1/webhook/batch-ingest` | WF-002 nightly batch |
| `GET` | `/api/v1/webhook/status/{job_id}` | Batch-job status |
| `POST` | `/api/v1/webhook/synthesize` | WF-010 RAIA synthesis distributor |

### Other

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/retrieve/cities` | List 50 known Legistar cities |
| `POST` | `/api/v1/retrieve/legistar` | Start a Legistar retrieval job |
| `POST` | `/api/v1/compliance/assess` | CCOPS scorecard generation |
| `GET` | `/api/v1/compliance/mandates` | List all 11 CCOPS mandates |
| `POST` | `/api/v1/rag/query` | RAG query with LLM-ready context |
| `POST` | `/api/v1/cpra/deadlines-within/{window}` | CPRA deadline range query |

Full automation routes (`/api/v1/automation/*`) proxy to n8n when
`N8N_API_KEY` is configured. See
[docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md) for setup.

---

## Automation (n8n)

O.D.I.A. ships with a token-gated webhook surface for driving automated
ingestion, analysis, and cross-jurisdiction synthesis from
[n8n](https://n8n.io/) workflows.

**For end users:** the desktop install includes a **Manual Triggers** panel
on the Automation tab that works out of the box without n8n — see
[docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md) Level 0.

**For automated / scheduled workflows** (CivicPlus auto-ingest, CPRA
deadline alerts, nightly batch scrapes), bring up the optional n8n stack:

```bash
cp .env.example .env
# Edit .env, set ODIA_WEBHOOK_TOKEN / N8N_ENCRYPTION_KEY / POSTGRES_PASSWORD
#   python -c "import secrets; print(secrets.token_urlsafe(32))"

docker compose -f docker-compose.yml -f docker-compose.n8n.yml up -d
```

Then:

- n8n editor → http://localhost:5678 (basic-auth from `.env`)
- Backend webhook health → `curl -H "X-ODIA-Webhook-Token: $ODIA_WEBHOOK_TOKEN" http://localhost:8000/api/v1/webhook/health`
- Reference workflows → `data/n8n-workflows/bundle.json` (import via n8n
  UI; activate per-jurisdiction after review — **all ship INACTIVE** by
  design)

If `ODIA_WEBHOOK_TOKEN` is unset, the webhook route surface refuses to
register and logs an error — misconfigured deployments fail loud rather
than silently exposing an open pipeline.

Complete walkthrough with troubleshooting:
[docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md)

---

## Audit Triage Pipeline

For manual audit workflows with chain-of-custody tracking:

```bash
# Flag a document
python scripts/triage.py \
  --doc-id DOC001 --path /path/to/document.pdf \
  --flag "Missing certification" --severity high \
  --category doj_certification --author "Your Name"

# Generate audit report
python scripts/render_report.py --output reports/audit_report.md

# Generate GitHub issue drafts for high/critical findings
python scripts/auto_issue_generator.py --severity high --severity critical
```

See [QUICKSTART.md](QUICKSTART.md) for the full triage workflow.

---

## Multi-Jurisdiction Analysis

Compare anomaly patterns across multiple jurisdictions in a single run:

```bash
python scripts/run_multi_audit.py \
    --config-dir config/multi_jurisdiction \
    --source-dir data/multi_jurisdiction \
    --output reports/multi_jurisdiction \
    --verbose
```

Each jurisdiction needs a config directory under `config/multi_jurisdiction/<id>/`
with a `jurisdiction.json` file. Documents go in `data/multi_jurisdiction/<id>/`.

**What it detects across jurisdictions:**
- Vendor playbook replication — same anomaly patterns from the same vendor
  across multiple jurisdictions
- Procurement parallels — shared sole-source justifications or timeline
  irregularities
- Regional governance gaps — common policy absences across a geographic cluster

**Output:** JSON + Markdown comparative reports with risk ranking and
recommendations.

A synthetic sample dataset covering three California jurisdictions is included
in `data/multi_jurisdiction/`. See
[docs/MULTI_JURISDICTION.md](docs/MULTI_JURISDICTION.md) for full setup and
configuration guidance.

---

## Compliance Assessment

Evaluate surveillance technology procurement against the ACLU CCOPS
(Community Control Over Police Surveillance) framework:

```bash
python scripts/run_compliance_check.py \
  --config-dir config/ --source data/sources/ \
  --output reports/compliance/
```

Maps ODIA detector findings to all 11 CCOPS model bill mandates and produces a
`ComplianceScorecard` with per-mandate status (`compliant`, `non_compliant`,
`partial`, `unknown`), overall risk level, and specific recommendations. Also
available via `POST /api/v1/compliance/assess` in the API and the **Compliance**
tab in the desktop UI.

See [docs/COMPLIANCE_FRAMEWORK.md](docs/COMPLIANCE_FRAMEWORK.md) for the full
mandate mapping, risk levels, and programmatic usage guide.

---

## Configuration

```yaml
# config/defaults.yaml
pdf_storage: "external"          # Keep PDFs outside repo
redaction:
  enabled: false                 # Manual review required before publishing
  auto_detect_pii: true
ollama:
  host: "localhost"
  port: 11434
  default_model: "llama3-small"  # Optional: local LLM evaluation
```

Corpus configuration: copy `config/corpus_manifest.example.json` to
`config/corpus_manifest.json` and set your jurisdiction's data sources.

Multi-jurisdiction configuration on the desktop install: use the **Seed
Example Jurisdictions** trigger on the Automation tab (or
`POST /api/v1/dashboard/seed-jurisdictions`), then edit the resulting JSON
files in your user-writable config dir (`%APPDATA%\ODIA\config\multi_jurisdiction\`
on Windows, `~/Library/Application Support/ODIA/config/multi_jurisdiction/` on
macOS, `~/.local/share/odia/config/multi_jurisdiction/` on Linux).

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=src/oraculus --cov=src/oraculus_di_auditor --cov-report=term-missing

# Format and lint
black src tests
ruff check src tests

# Frontend dev server (hot reload)
cd frontend && npm install && npm run dev
```

All anomaly detectors return structured results:
```python
{
    "id":       str,               # stable dot-namespaced identifier
    "issue":    str,               # human-readable description
    "severity": "low|medium|high|critical",
    "layer":    str,               # detector name
    "details":  dict,              # structured evidence
}
```

See [docs/developer-setup.md](docs/developer-setup.md) for full setup
instructions, [docs/development-workflow.md](docs/development-workflow.md)
for the contribution flow, and [docs/RELEASING.md](docs/RELEASING.md) for
the release runbook (six version-string locations to bump per release).

---

## Privacy & Security

- **No automatic external data uploads.** All analysis is local. The only
  outbound calls are the optional Legistar fetch (to public city portals)
  and any actions you explicitly configure in n8n workflows.
- **No telemetry.** O.D.I.A. never phones home with usage data.
- **No required LLM API keys.** OpenAI / Anthropic integration is opt-in
  for the RAG layer only and is not required for any other feature.
- **PII redaction is NOT automatic** — manual review required before
  publishing reports.
- **Original PDFs stored externally by default** (`config/defaults.yaml`).
- **All manifests include chain-of-custody timestamps and SHA-256 checksums.**
- **Webhook endpoints fail loud** if the token isn't configured (refuse to
  register rather than silently exposing an open pipeline).
- **Consult qualified legal counsel before public disclosure of audit findings.**

See [docs/DATA_POLICY.md](docs/DATA_POLICY.md),
[docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md), and
[compliance_checklist.md](compliance_checklist.md).

---

## Documentation

User-facing:
- [QUICKSTART.md](QUICKSTART.md) — 60-second demo + your first audit
- [docs/AUTOMATION_SETUP.md](docs/AUTOMATION_SETUP.md) — desktop install through optional n8n stack, written for non-developers
- [docs/MULTI_JURISDICTION.md](docs/MULTI_JURISDICTION.md) — comparative analysis across cities
- [docs/COMPLIANCE_FRAMEWORK.md](docs/COMPLIANCE_FRAMEWORK.md) — CCOPS mandate mapping
- [docs/LEGAL_REFERENCE.md](docs/LEGAL_REFERENCE.md) — legal reference dataset
- [docs/OCR_SETUP.md](docs/OCR_SETUP.md) — OCR (Tesseract / Poppler) setup
- [docs/RAG_SETUP.md](docs/RAG_SETUP.md) — RAG query engine setup

Developer-facing:
- [docs/developer-setup.md](docs/developer-setup.md) — full dev environment
- [docs/development-workflow.md](docs/development-workflow.md) — contribution flow
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture
- [docs/PHASES.md](docs/PHASES.md) — phase-by-phase engine reference
- [docs/RELEASING.md](docs/RELEASING.md) — release runbook
- [docs/database-design.md](docs/database-design.md) — schema reference

---

## License

Copyright © 2025 Synthetic Technology Revolution — MIT License
