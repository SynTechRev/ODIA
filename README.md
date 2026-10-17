<div align="center">

# O.D.I.A.
### Oraculus Decimus Intellect Analyst

**A civic accountability intelligence platform for forensic analysis of legal and government documents.**

[![Version](https://img.shields.io/badge/version-v3.9.2-00ff9d?style=flat-square&labelColor=0e0e14)](https://github.com/SynTechRev/ODIA/releases/tag/v3.9.2)
[![Python](https://img.shields.io/badge/python-3.11%2B-d8b13c?style=flat-square&labelColor=0e0e14)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-00ff9d?style=flat-square&labelColor=0e0e14)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-d8b13c?style=flat-square&labelColor=0e0e14)](https://github.com/SynTechRev/ODIA/releases/latest)
[![Tests](https://img.shields.io/badge/tests-4339%20passing-00ff9d?style=flat-square&labelColor=0e0e14)](https://github.com/SynTechRev/ODIA/actions)
[![Local First](https://img.shields.io/badge/local--first-no%20cloud%20required-d8b13c?style=flat-square&labelColor=0e0e14)](#privacy--security)

<br>

### [⬇ &nbsp; Download Latest Release &nbsp; →](https://github.com/SynTechRev/ODIA/releases/latest)
**[All Releases & Changelogs](https://github.com/SynTechRev/ODIA/releases)**

</div>

---

Ingest legal and government documents (PDF, XML, JSON, TXT, DOCX, HTML, scanned TIFF). Run them through **30 detection layers** — ten civic-integrity detectors, ten legal-reasoning detectors, and ten commercial-contract detectors — to surface fiscal anomalies, constitutional concerns, surveillance outsourcing, procurement irregularities, statutory misapplication, case-law currency issues, and consumer contract asymmetries. Reconstruct contract lineages, evaluate compliance against the ACLU CCOPS framework, query the full audit corpus in natural language via a fine-tuned local LLM, and generate litigation-grade reports — all **locally**, with full SHA-256 provenance. No cloud, no telemetry, no required API keys.

---

## Download

### Desktop App (recommended)

Standalone installer — no Python, Docker, or command line required.

| Platform | Installer | Architecture |
|---|---|---|
| **Windows** | [ODIA-Setup-3.9.2.exe](https://github.com/SynTechRev/ODIA/releases/download/v3.9.2/ODIA-Setup-3.9.2.exe) | x64 |
| **macOS (Apple Silicon)** | [ODIA-3.9.2-arm64.dmg](https://github.com/SynTechRev/ODIA/releases/download/v3.9.2/ODIA-3.9.2-arm64.dmg) | arm64 (M1/M2/M3/M4) |
| **macOS (Intel)** | [ODIA-3.9.2-x64.dmg](https://github.com/SynTechRev/ODIA/releases/download/v3.9.2/ODIA-3.9.2-x64.dmg) | x64 |
| **Linux** | [ODIA-3.9.2.AppImage](https://github.com/SynTechRev/ODIA/releases/download/v3.9.2/ODIA-3.9.2.AppImage) | x64 |

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

### v3.9.2 — City of Fresno Ingest · RAG Hardening · CI Stability · S.A.B.E.R. Phase 1

<div align="center">

**271,245 findings across 16 jurisdictions — 83% increase from v3.9.0**

</div>

---

#### Corpus Expansion

**City of Fresno Legistar ingest complete** — 14,409 legislative documents now in corpus. Key findings: Flock Safety $1.5M surveillance contract confirmed (cross-jurisdiction lattice now spans Visalia PD · Fresno County · Fresno City), TASER sole-source procurement without Gov. Code citation, JAG anti-supplanting patterns extending the Tulare County lattice into the city tier.

**TCPD ingest complete** — CPRA-004 returns processed and ingested; full Tulare County Probation public-records corpus now in analysis pipeline. SEU field-action patterns resolved against record absence.

---

#### odia-v1 — Fine-Tuned Civic Accountability LLM

The RAG pipeline now defaults to **odia-v1**, a QLoRA fine-tuned Llama-3.1-8B trained on 87,618 civic-accountability examples (13,498 forensic audit reports + 74,120 domain explanations). This replaces base `llama3.1:8b` as the default query model.

| Field | Value |
|---|---|
| Base model | Llama-3.1-8B-Instruct |
| Training method | QLoRA (r=16, α=32), 2 epochs |
| Training examples | 87,618 |
| Quantization | Q4\_K\_M GGUF (4.92 GB) |
| HuggingFace | `SynTechRev/odia-v1` (private) |
| Ollama name | `odia-v1` |

---

#### RAG Pipeline — Memory and Correctness Fixes

The retriever was refactored to handle 271k-document corpora without out-of-memory errors:

- **float16 vector storage** — full corpus vectors fit in ~1.1 GiB (vs. ~2.2 GiB for float32)
- **Lazy vstack flush** — `add_vector()` accumulates into a `_pending` list; a single `np.vstack` materializes at `search()` or `save()` time, replacing the per-add O(n²) pattern
- **`Retriever.reset()`** — atomically clears `vectors`, `_pending`, and `metadata` in one call; fixes a correctness bug in `_refit()` where stale pending vectors from a previous vocabulary caused dimension mismatches on re-indexing
- **Similarity threshold** — lowered from 0.3 → 0.05 to surface relevant results on smaller corpora

---

#### 7 CPRA Letters — Automated Generation Pipeline

Seven California Public Records Act request letters generated and committed covering Fresno County Sheriff, BOS Clerk, IT/CEO, City of Fresno, and Fresno PD — targeting unsigned instruments, surveillance contracts, and fiscal anomalies surfaced by the audit corpus.

---

#### S.A.B.E.R. Phase 1 — AI Security Evaluation

**S.A.B.E.R.** (Security Analysis and Behavioral Evaluation Regimen) is ODIA's adversarial AI defense framework. Phase 1 is complete:

- **A.R.C.A.D.E. Layer 13** — garak v0.17.0 probing odia-v1 across `packagehallucination`, `web_injection`, and `DanInTheWild` probe families
- CPU-safe DanInTheWild config (`context_len: 512`) for local evaluation without GPU requirement
- Results feed back into odia-v2 adversarial training corpus

---

#### CI / Engineering Stability

| Fix | Detail |
|---|---|
| **Formatter unification** | Replaced `ruff-format` with `black@24.10.0` in pre-commit hooks — eliminates perpetual divergence between commit-time formatting and CI `black --check` |
| **Self-healing scope** | Auto-commit step in `python-ci.yml` now stages only `src/ tests/ scripts/` — prevents workflow push failures from accidentally staging `.github/workflows/` files |
| **Supply-chain scanner** | `google/osv-scanner-action/osv-scanner-action@v2.7.0` (corrected subdirectory path); `--skip-git` flag removed (v2.x API change); `continue-on-error: true` prevents pre-existing CVEs from blocking green CI |
| **pyproject.toml ignores** | Broad `scripts/*.py` per-file-ignores for E501/N806/C901/B007/E741/F841 — operational scripts no longer block pre-commit |

<details>
<summary><strong>v3.9.1 — C.O.N.T.R.A. Frontend · Desktop RAG Pipeline</strong></summary>

**v3.9.1** — C.O.N.T.R.A. frontend tab live (`/contra` page): detector registry, entity registry, CASI status tiles. Desktop RAG pipeline end-to-end fix: vectors correctly located at install directory on all platforms; `dataRoot` path resolution bug fixed in Electron backend.

</details>

<details>
<summary><strong>v3.9.0 — C.O.N.T.R.A. Complete · Fresno Corpus · odia-v1 Fine-Tune</strong></summary>

This release marks the full completion of **C.O.N.T.R.A.** (Commercial Contract Asymmetry) — ODIA's extension into consumer and commercial contract analysis — alongside a major corpus expansion to Fresno County (50,699 total documents), and the deployment of **odia-v1**, a fine-tuned LLM specialized to civic-accountability domain reasoning.

---

#### C.O.N.T.R.A. — Commercial Contract Asymmetry Framework (Phases A–G)

C.O.N.T.R.A. applies the same forensic methodology ODIA uses on government documents to commercial adhesion contracts, terms of service, privacy notices, and arbitration agreements — surfacing the legal mechanisms that foreclose consumer remedies before a dispute begins.

**Ten commercial-contract detectors (L-11 through L-20):**

| Detector | Name | What it catches |
|---|---|---|
| **L-11** | Arbitration Architecture | Mandatory arbitration, class action waivers, AAA/JAMS routing, bilateral vs. unilateral scope, opt-out window adequacy |
| **L-12** | Choice of Law / Forum | Inconvenient forum selection, Delaware/NY governing law bias, anti-consumer jurisdiction stacking |
| **L-13** | Unilateral Modification | Sole-discretion amendment, no-notice changes, "continued use = acceptance" |
| **L-14** | Data Collection Depth | Inferred data, third-party data purchase, sensor/biometric collection breadth |
| **L-15** | Data Retention | Indefinite retention, vague deletion language, backup carve-outs post-deletion |
| **L-16** | Onward Transfer | Affiliate-without-limit transfers, acquisition continuity, "de-identified" reassembly risk |
| **L-17** | ML / AI Training | Opt-out absence, generative AI training use, model distillation from user data |
| **L-18** | Remedy Foreclosure | Limitation of liability + arbitration compound stacking; consequential damage blanket waivers |
| **L-19** | Enforcement Asymmetry | Fee-shifting asymmetry; attorney fee clauses that deter consumer claims; IP carve-out one-sidedness |
| **L-20** | Dark Pattern | Pre-checked consent, hidden arbitration in footer, deceptive interface asymmetry |

**CASI — Consumer Adhesion Severity Index:**
Five-axis 0–100 composite score (`remedy_foreclosure`, `data_extraction_depth`, `modification_and_consent`, `procedural_adhesion`, `enforcement_cost_asymmetry`). Band labels: Baseline / Elevated / Substantial / Severe / Foreclosure Regime. Deterministic — same document always produces the same score.

**Entity Registry:**
Canonical company name → `entity_id` resolution with fuzzy matching (rapidfuzz token-sort, 0.88 threshold). 32 entities pre-seeded (telecoms, utilities, banks, platforms). Auto-creates on first ingest.

**CCP § 1281.96 Pipeline (California mandatory arbitration disclosure):**
Retrieves and normalizes consumer arbitration case records from AAA, JAMS, ADRS, JUDICATE_WEST, FEDARB, and NAM. Computes Wilson (1927) confidence intervals on consumer prevailing rates; arbitrator and corporate repeat-player concentration (HHI); cross-references entity_ids against the C.O.N.T.R.A. corpus.

**T.C.A.M.S. — Targeted Contract Asymmetry Monitoring Summary:**
Corpus-level DOCX report across all ingested commercial documents: CASI band distribution, top-10 entities by aggregate score, axis dominance analysis, doctrinal anchor frequency (cross-entity prevalence), L-detector heatmap.

**C.C.C.E.A. — Commercial Contract Clause Exposure Analysis (D-13.H):**
Clusters `evidence_excerpt` strings by Jaccard token overlap; classifies each cluster by clause type (8 types); maps to probable drafting law firm (Cooley, Wilson Sonsini, Fenwick, Latham, Gibson Dunn, DLA Piper) via regex heuristics. All firm attributions explicitly labeled PROBABLE.

**12-step commercial ingest pipeline:**
`odia contra-ingest --source contract.pdf --entity "Corp Name" --doc-type tos` runs: PDF detect/OCR → SHA-256 hash → duplicate check (idempotent) → provenance → entity resolve → L-11–L-20 detectors → CASI score → Wayback snapshot → DB insert → Analytical Card DOCX → IngestionResult.

**Wayback Machine client:**
`find_capture(url, target_date)` and `retrieve_prior_versions(url, years=5)` via the Internet Archive Availability API. Retrieves historical contract snapshots to establish timeline of term evolution.

**Database tables (all live in `oraculus_audit.db`):**
`commercial_entities` (32 seeded), `commercial_entity_aliases`, `commercial_documents`, `contra_findings`, `casi_scores`, `s1281_96_cases`.

**CLI — `odia contra-ingest`:**
```bash
odia contra-ingest \
  --source path/to/contract.pdf \
  --entity "Company Name" \
  --doc-type tos \
  --output reports/
```

---

#### Fresno County + Fresno PD — V4.0 Multi-Agent Synthesis

Corpus expansion to 50,699 documents across 16 jurisdictions. Fresno County (32,340 docs / 73,547 findings) and Fresno PD (126 docs / 526 findings) completed V4.0 Multi-Agent Synthesis reports with full cross-jurisdiction RAIA pattern correlation.

Significant findings: $14.97B in unsigned instruments (Fresno County); Flock Safety surveillance across 3 agencies (1 county confirmation, 22 Visalia PD docs, Fresno City $1.5M contract pending); McMillian anchor cross-jurisdiction echo; $18.8M Axon MSA (TCSO).

---

#### odia-v1 — First ODIA Fine-Tune

QLoRA fine-tuned Llama-3.1-8B on 87,618 civic-accountability examples. Q4_K_M GGUF (4.92 GB). Deployed in Ollama as `odia-v1` and wired as the default RAG model. Full details: [docs/RAG_SETUP.md](docs/RAG_SETUP.md).

</details>

<details>
<summary><strong>Earlier versions (v3.8.x and before)</strong></summary>

**v3.8.0–v3.8.2** — Electron desktop app stabilized across Windows, macOS, Linux; RAG proxy + `rag_config.py` fix; `dataRoot` env-var wired from Electron to FastAPI backend; `odia-v1` registered in Ollama.

**v3.7.0** — `odia_legal` Phase 1 foundation: 10 legal-reasoning detectors (L-1–L-10); CPRA crosswalk; citation parser with NetworkX graph (`CITES / AMENDS / IMPLEMENTS / OVERRULED_BY`); California statutes (68 sections), 2 CFR Part 200, 28 CFR Part 23, CPRA case-law corpus (7 annotated cases).

**v3.6.0** — Multi-jurisdiction comparative analysis: registry, runner, pattern detector, 16-jurisdiction jurisdiction configs, comparative DOCX report.

**v3.5.0** — CCOPS compliance scorecard: 11 ACLU model bill mandates, per-mandate status and risk level, compliance dashboard route.

**v3.4.0–v3.4.8** — Temporal governance engine: contract lineage reconstruction, evolution detectors, `TemporalStabilityField` scoring, OTGE-15 orchestration.

**v3.3.1** — PyYAML declared as explicit dependency; `LegalResolver` CWD-independence fix.

**v3.3.0** — Full United States Code corpus (53 titles, 52,586 sections) as a git submodule; `LegalResolver` pre-warms at boot.

**v3.2.5** — `.docx`, `.doc` (OLE + antiword), and multi-page TIFF OCR ingestion; magic-byte sniffing for extension-less archive URLs (Questys CMX).

**v3.2.0–v3.2.4** — 5 new DB-backed list endpoints; Suspense wrapper for Next.js static-export compatibility; 15-test audit-consistency suite; Drupal semantic-container HTML extraction.

**v3.1.0–v3.1.1** — `curl_cffi` Chrome impersonation as Tier-2 HTTP fallback (bypasses Akamai/Cloudflare bot detection); HTML ingestion branch.

**v3.0.0–v3.0.5** — Production multi-platform desktop release; backend-side URL scraping; async fire-and-forget scrape worker; RAIA pattern detection hardening.

Full changelog: [CHANGELOG.md](CHANGELOG.md)

</details>

---

## Empirical State (live as of v3.9.2)

ODIA has ingested and fully analyzed **65,108 documents across 16 California jurisdictions**, surfacing **271,245 findings** with full cross-jurisdiction RAIA synthesis, V4.0 MAS reports for Fresno County and Fresno PD, and active Fresno City synthesis underway:

| Jurisdiction | Docs | Findings | MAS | Notes |
|---|---|---|---|---|
| **Fresno County** | 32,340 | 73,547 | **V4.0** | $14.97B unsigned instruments · CPRA matrix 10 targets |
| **Fresno PD** | 126 | 526 | **V4.0** | 3 Flock Safety detections · AB 481 · Policy Manual |
| **Fresno (City)** | 14,409 | 64,489 | **Active** | Flock $1.5M confirmed · TASER sole-source · JAG lattice |
| Visalia | 7,928 | 20,824 | Done | Scalar 0.8871 compliance baseline |
| Tulare | 3,062 | 10,750 | Done | Questys CMX + Drupal |
| Farmersville | 1,643 | 7,525 | Done | CivicPlus |
| Exeter | 1,396 | 4,838 | Done | — |
| Dinuba | 1,105 | 13,506 | Done | Highest anomaly density |
| TCSO | 573 | 4,474 | Done | McMillian anchor · $18.8M Axon MSA · 35 CRITICAL |
| Lindsay | 805 | 4,799 | Done | — |
| Visalia PD | 340 | 4,571 | Done | 22 Flock Safety docs / 355 findings |
| Porterville | 350 | 1,756 | Done | Revize |
| TCDA | 660 | 102 | Done | Scalar 0.9240 · Zero CRITICAL |
| Woodlake | 103 | 773 | Done | — |
| Tulare County | 95 | 119 | Done | BOS umbrella |
| TCPD | 161 | 415 | Done | Full CPRA-004 returns · SEU field-action records |
| Multi-jurisdiction | 12 | 231 | Done | Cross-entity index · Flock lattice docs |
| **TOTAL** | **65,108** | **271,245** | | **16 jurisdictions** |

**Cross-jurisdiction findings:** `admin:missing-final-action` (universal), `signature:unsigned-instrument`, `fiscal:amount-without-appropriation`, `scope:significant-expansion`, `vendor-convergence:sole-source`, `governance:sole-source-without-gov-code-citation`, `grant:jag-without-anti-supplanting` (34 U.S.C. § 10152), `surveillance:flock-safety-contract` (cross-jurisdiction lattice: VPD 22 docs · Fresno County 1 confirmed · Fresno City $1.5M contract).

**C.O.N.T.R.A. corpus (commercial contracts):** 32 entities seeded · schema fully deployed · first `contra-ingest` pilot run pending on commercial contract PDFs.

---

## Features

### Analysis Pipeline

- **10-detector civic analysis engine** — fiscal, constitutional, surveillance, procurement, signature, scope, governance, administrative integrity, grant compliance (JAG / COPS / Byrne anti-supplanting), and cross-entity reference detection — all local, no cloud calls
- **10 legal-reasoning detectors** — L-1 through L-10 covering statutory applicability, procedural compliance, exemption misapplication, ministerial duty, federal grant compliance, constitutional implication, regulatory authority chains, case-law currency, recodification translation, and balancing-test analysis
- **10 commercial-contract detectors (C.O.N.T.R.A.)** — L-11 through L-20: arbitration architecture, choice of law/forum, unilateral modification, data collection depth, data retention, onward transfer, ML/AI training, remedy foreclosure, enforcement asymmetry, dark pattern
- **Multi-format ingestion** — PDF (with PyMuPDF OCR fallback), XML, JSON, TXT, DOCX, DOC, HTML, multi-page TIFF
- **Legistar retrieval** — pull legislative documents from 50 preconfigured city portals
- **CCP § 1281.96 retrieval** — consumer arbitration statistics from AAA, JAMS, ADRS, JUDICATE_WEST, FEDARB, NAM; normalized case records with prevailing-rate analysis and repeat-player concentration

### C.O.N.T.R.A. — Commercial Contract Asymmetry

- **CASI scoring** — five-axis 0–100 Consumer Adhesion Severity Index; deterministic per-document score with band labels (Baseline / Elevated / Substantial / Severe / Foreclosure Regime)
- **Entity registry** — fuzzy-match resolution (rapidfuzz 0.88 threshold); 32 entities pre-seeded; auto-creates on first ingest
- **12-step ingest pipeline** — `odia contra-ingest` CLI with PDF/OCR, SHA-256 deduplication, entity resolution, full detector suite, CASI computation, Wayback archival, DB persistence, Analytical Card DOCX
- **Analytical Card DOCX** — per-document report: entity profile, CASI axis breakdown, findings table, recommended actions block
- **T.C.A.M.S.** — corpus-level DOCX: CASI distribution, top-10 entities, axis dominance, doctrinal anchor frequency, L-detector heatmap
- **C.C.C.E.A.** — Jaccard-clustered clause exposure analysis with probable drafting firm attribution (8 clause types, 6 firms)
- **Wayback Machine client** — `find_capture()` / `retrieve_prior_versions()` for historical contract version tracking

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

- **RAG query engine** — `POST /api/v1/rag/query` backed by local `odia-v1` (QLoRA Llama-3.1-8B); multi-index routing across `corpus`, `ace`, and `jim` sub-indexes; two-layer legal domain enrichment; float16 vector storage with lazy-flush retriever for 271k-document scale
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

### S.A.B.E.R. — AI Security Evaluation

- **A.R.C.A.D.E. Layer 13** — adversarial probing of `odia-v1` via garak v0.17.0: `packagehallucination`, `web_injection`, and `DanInTheWild` probe families
- **CPU-safe evaluation** — DanInTheWild config with `context_len: 512` cap for local evaluation without GPU
- **Findings pipeline** — probe results feed into odia-v2 adversarial training corpus for the next fine-tune cycle

---

## Architecture

```
src/
├── oraculus_di_auditor/   # Main platform (200+ modules)
│   ├── analysis/          # 10 civic-integrity detectors
│   ├── contra/            # C.O.N.T.R.A.: L-11–L-20 commercial-contract detectors
│   │   ├── l11_arbitration_architecture.py
│   │   ├── l12_choice_of_law_forum.py
│   │   ├── l13_unilateral_modification.py
│   │   ├── l14_data_collection_depth.py
│   │   ├── l15_data_retention.py
│   │   ├── l16_onward_transfer.py
│   │   ├── l17_ml_ai_training.py
│   │   ├── l18_remedy_foreclosure.py
│   │   ├── l19_enforcement_asymmetry.py
│   │   └── l20_dark_pattern.py
│   ├── cards/             # Analytical report card generators (DOCX)
│   │   ├── analytical_card.py  # Per-document Analytical Card
│   │   ├── tcams.py            # T.C.A.M.S. corpus monitoring summary
│   │   └── ccceak.py           # C.C.C.E.A. Jaccard clause clustering
│   ├── ingest/            # Document ingestion package
│   │   ├── _document_ingest.py # Legacy folder ingest (backward compat)
│   │   ├── commercial.py       # 12-step commercial ingest pipeline + IngestionResult
│   │   └── wayback.py          # Wayback Machine availability client
│   ├── ingestion/         # PDF / XML / JSON / TXT / DOCX / HTML / TIFF + OCR
│   ├── orchestrator/      # Multi-agent task graph (Phase 5/8)
│   ├── governor/          # Policy enforcement, security gatekeeper (Phase 9)
│   ├── interface/         # FastAPI app + modular route modules
│   │   └── routes/        # 20+ route modules (upload, audit, legal, rag, …)
│   ├── reporting/         # Pydantic models, Jinja2 templates, plain-language,
│   │                      # evidence-packet ZIP generator
│   ├── rag/               # Retrieval engine, context builder, prompt router
│   ├── retriever.py       # Float16 vector storage · lazy-flush · reset()
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
├── app/                   # App Router pages (Dashboard, Upload, Legal, RAG, C.O.N.T.R.A., …)
├── components/            # Gemstone HUD component library
└── lib/                   # API client, navigation, Zustand stores

desktop/                   # Electron main process + build config
scripts/                   # Pipeline, ingestion, triage, training data export
data/
├── legal_corpora/         # us-code git submodule (52,586 USC sections)
├── saber/                 # S.A.B.E.R. adversarial probe configs (garak)
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
| `POST` | `/api/v1/rag/query` | Natural language query (odia-v1 via Ollama) |
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
  default_model: "odia-v1"
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

Anomaly detector contract (enforced across all 30 detectors):

```python
{
    "id":       str,   # stable dot-namespaced: "fiscal:missing-final-action"
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
| [docs/RAG_SETUP.md](docs/RAG_SETUP.md) | Developers — Ollama + odia-v1 RAG setup |
| [docs/LEGAL_REFERENCE.md](docs/LEGAL_REFERENCE.md) | Everyone — legal reference dataset |
| [docs/OCR_SETUP.md](docs/OCR_SETUP.md) | Developers — Tesseract / Poppler setup |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Developers — system architecture |
| [docs/PHASES.md](docs/PHASES.md) | Developers — phase-by-phase engine reference |
| [docs/database-design.md](docs/database-design.md) | Developers — schema reference |
| [CHANGELOG.md](CHANGELOG.md) | Everyone — full version history |

---

<div align="center">

**Copyright © 2026 Synthetic Technology Revolution — MIT License**

[Issues](https://github.com/SynTechRev/ODIA/issues) · [Releases](https://github.com/SynTechRev/ODIA/releases) · [Docs](docs/)

</div>
