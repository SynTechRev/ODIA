# ODIA (Oraculus Decimus Intellect Analyst) — Project Brief

## What This Project Is

ODIA is a **general-purpose legal document ingestion, normalization, and anomaly auditing platform**. It ingests legal documents (PDF, XML, JSON, TXT), normalizes and chunks them, generates deterministic TF-IDF embeddings, detects anomalies (fiscal, constitutional, surveillance, cross-jurisdiction, procurement), orchestrates multi-document analysis, enforces governance policies, and supports natural language querying of the full audit corpus via a local RAG pipeline backed by a fine-tuned LLM — all with full provenance tracking.

**Repository**: https://github.com/SynTechRev/ODIA
**License**: MIT

## Current State (as of 2026-10-19)

- **Version**: 3.9.2 (active development, master branch)
- **Python**: 3.11+ required (tested on 3.14)
- **Tests**: 4339+ passing, 15 skipped (data-dependent corpus/transparency tests)
- **Working core**: Ingestion, analysis, orchestration, governance, compliance, auth, RAG, C.O.N.T.R.A. commercial analysis — all functional and tested
- **Higher phases** (12–20): Architectural scaffolding exists — experimental/theoretical
- **Frontend**: Next.js 14 production app in `frontend/` — Upload, Results History, Synthesis/RAIA, RAG Query, Compliance, Legal, C.O.N.T.R.A., Config
- **API**: FastAPI backend in `src/oraculus_di_auditor/interface/api.py` + modular routes in `interface/routes/`
- **Desktop**: Electron app ships via GitHub Actions (`Build and Release Desktop Apps` workflow). v3.9.2 CI build triggered 2026-08-11. v3.9.1 installer on GitHub Release.
- **LLM**: `odia-v1` — QLoRA fine-tuned Llama-3.1-8B (87,618 examples, Q4_K_M GGUF, 4.92 GB). Registered in Ollama. Live in RAG pipeline as default LLM. Artifacts: `D:\ODIA\models\odia-v1.q4_k_m.gguf` (local) + HuggingFace `SynTechRev/odia-v1` (private).
- **RAG**: `OracRAG` class loads TF-IDF index from disk at startup (`collection`, `ace_collection`, `jim_collection`). Default: provider=ollama, model=odia-v1. Config: `config/rag_config.py` + `config/ollama_config.yaml`. Desktop backend reads ODIA_VECTORS_DIR from installDir (fixed v3.9.1). Similarity threshold fixed 0.3→0.05 (v3.9.2). Retriever `.tolist()` perf bug fixed (v3.9.2).
- **DB**: SQLAlchemy + SQLite (`oraculus_audit.db`) — **81,309 documents / 271,245 anomaly findings** across 16 jurisdictions (Tulare + Fresno Counties + City of Fresno + TCPD). Finding-bearing docs: ~68,000 (remainder have zero anomalies).
- **RAG Index**: Full production index rebuilt 2026-10-16 (81,309 corpus / 271,245 ACE / 3,937 JIM). float16 dims, 2048 ace dims. Copied to `C:\Users\yahua\AppData\Roaming\ODIA\data\vectors\` (Electron userData).
- **Case law corpus**: 133 cases in `legal/cases/` — CourtListener authenticated harvest complete 2026-10-19 (commit 84fbf83). Topics: CPRA exemptions, 4th Amendment ALPR/GPS, AB 481, JAG compliance, Brown Act, biometric privacy.

## Corpus Status (Tulare + Fresno Counties + City of Fresno)

| Jurisdiction | Docs | Findings | MAS Status | Notes |
|---|---|---|---|---|
| **fresnocounty** | **27,413** | **123,736** | **V4.0 DONE 2026-07-31** | NSU complete. ~23,000 finding-bearing docs. Zero Flock (1 in hex-named PDF confirmed). ~4,120 unsigned instruments. CPRA matrix 10 targets. CPRA letters drafted (BOS Clerk, Sheriff, CAO+ITS). |
| **fresno (city)** | **14,409** | **64,489** | **V2.0 ACTIVE** | DONE 2026-10-08 (16,692 matters / 29,308 files). $1.5M Flock contract. 2,956 unsigned instruments (94.4% of criticals). CPRA letters: City Clerk + unsigned instruments drafted. |
| **fresno-pd** | **~261** | **~526** | **V4.0 DONE 2026-07-31** | FPD operational reports, AB 481, Policy Manual 7-16-26. 3 Flock detections. CPRA letter drafted. |
| visalia | 5,814 | 20,824 | DONE 2026-06-16 | 20 detector layers. Scalar 0.8871 (compliance baseline). |
| farmersville | 1,292 | 7,525 | Complete | MAS purged |
| exeter | 1,048 | 4,838 | Complete | MAS purged |
| dinuba | 1,087 | 13,506 | Complete | MAS purged |
| lindsay | 661 | 4,799 | Complete | MAS purged |
| tcso | 458 | 4,474 | DONE 2026-06-16 | McMillian anchor. $18.8M Axon MSA. 35 CRITICAL. L-detectors active. |
| visalia-pd | 337 | 4,571 | Complete | 22 Flock Safety docs / 355 findings. F-13 corpus apex (140). CPRA letter CPRA-VPD-FLOCK-001 drafted 2026-10-17. |
| porterville | 340 | 1,756 | Complete | MAS purged |
| tcda | 97 | 102 | DONE 2026-06-16 | Compliance baseline anchor. Scalar 0.9240. Zero CRITICAL. |
| woodlake | 85 | 773 | Complete | MAS purged |
| tulare | 2,244 | 10,750 | Complete | MAS purged |
| tulare-county | 49 | 119 | Complete | County umbrella |
| **tcpd** | **~1,262** | **significant** | **DONE 2026-10-08** | 1,262 PDFs via PrimeGov BOS portal (2006–2026). 60 JAG anti-supplanting. CPRA letter drafted. SEU operationally present. |
| multi-jurisdiction | 7 | 107 | Complete | Cross-jurisdiction index docs |
| **TOTAL** | **~81,309** | **271,245** | | 16 jurisdictions |

## Architecture

Two source packages under `src/`:

- `oraculus_di_auditor/` — Main platform: all active development
- `oraculus/` — Legacy thin wrapper; empty `__init__.py`. Submodules remain for backward compatibility; new code goes in `oraculus_di_auditor/`

Key module groups inside `oraculus_di_auditor/`:
- `analysis/` — Anomaly detectors: fiscal, constitutional, surveillance, cross-reference, procurement timeline, scalar scoring
- `adapters/` — External data source adapters: `base.py` (DataSourceAdapter ABC), `ccops_adapter.py` (ACLU CCOPS mandates), `atlas_adapter.py` (EFF Atlas of Surveillance), `compliance_engine.py` (ComplianceAssessmentEngine → ComplianceScorecard), `questys_adapter.py`
- `auth/` — JWT-based authentication and session management
- `db/` — SQLAlchemy models, session management, migration helpers (`models.py`, `session.py`)
- `rag/` — RAG pipeline: `OracRAG` class, vector store, query/filter logic
- `raia/` — Synthesis and inline analysis engine
- `registry/` — Detector and adapter registry
- `scrapers/` — Data source scrapers
- `multi_jurisdiction/` — Cross-jurisdiction analysis and comparison
- `reporting/` — Report generation pipeline
- `self_healing/` — CI self-healing pipeline hooks
- `orchestrator/` — Multi-agent task graph coordination
- `governor/` — Pipeline governance and policy enforcement
- `gcn/` — Governance constraint network and validator
- `ingestion/` — XML parser, checksum tracker, document engine
- `legal/` — Legal reference resolver (34 U.S.C. § 10152 / JAG, etc.)
- `mesh/` — Adaptive agent mesh
- `scalar_convergence/` — Recursive scalar scoring
- `qdcl/` — Quantum-inspired decision/cognition layer (Phase 11)
- `temporal/` — Temporal governance engine
- `workspace/` — Workspace and session management
- `rec17/`, `rgk18/`, `aei19/`, `aer20/`, `emcs16/`, `rpg14/` — Higher-phase experimental engines
- `llm_providers.py` — Ollama/OpenAI/Anthropic LLM abstraction
- `rag_context.py`, `rag_prompts.py` — RAG context builder and civic-accountability prompt templates
- `retriever.py`, `embeddings.py` — TF-IDF vector retrieval and embedding generation

API routes in `interface/routes/`:
`auth_routes`, `automation`, `compliance`, `config_routes`, `cpra`, `dashboard`, `detectors`, `field`, `gcn`, `governor`, `legal_routes`, `mesh`, `multi_jurisdiction`, `orchestrator`, `query`, `rag`, `reports`, `retrieval`, `temporal`, `triggers`, `upload`, `webhook`, `workspace_routes`

## Development Priorities

All original priorities are complete. Active work:

1. ~~README rewrite~~ — Done.
2. ~~Package consolidation~~ — Done.
3. ~~Configurable jurisdiction system~~ — Done.
4. ~~Stabilize core pipeline~~ — Done.
5. ~~Rename higher-phase terminology~~ — Done.
6. ~~Clean public presentation~~ — Done.
7. ~~DB-persisted audits~~ — Done. 18,072 docs / 74,144 findings in SQLite.
8. ~~SynTechRev brand + desktop builds~~ — Done. Electron CI ships `.exe`/`.dmg`/`.AppImage`.
9. ~~RAG on Ollama~~ — Done. Index live. `OracRAG` loads `collection` on startup.
10. ~~Fine-tune odia-v1~~ — Done. 87,618 examples, QLoRA, Q4_K_M GGUF, deployed in Ollama.
11. ~~Desktop RAG pipeline wired to odia-v1~~ — Done. Proxy + rag_config.py fix in v3.8.0. dataRoot bug fixed in v3.9.1.
12. ~~C.O.N.T.R.A. Phases A–G~~ — Done 2026-08-07. L-11–L-20 detectors, CASI, entity registry, §1281.96 pipeline, T.C.A.M.S., C.C.C.E.A., 12-step commercial ingest, Wayback client, 6 DB tables, CLI. v3.9.0 released.
13. ~~C.O.N.T.R.A. frontend nav tab~~ — Done 2026-08-11. /contra page live in v3.9.1. Detector registry, entity registry, CASI status tiles.
14. ~~RAG pipeline end-to-end fix~~ — Done 2026-08-11. vectors copied to install dir, similarity threshold 0.3→0.05, retriever perf bug fixed. v3.9.2.

**Active next steps**:
- ~~RAG index rebuild~~ — Done 2026-10-16. 81,309 corpus / 271,245 ACE / 3,937 JIM. Copied to `Roaming\ODIA\data\vectors`.
- ~~split_mas_export.py~~ — Done 2026-07-31. Files in `data/mas_export/fresnocounty_splits/` and `data/mas_export/fresno_splits/` (35 files).
- ~~Fresno County + Fresno PD MAS via Opus~~ — Done 2026-07-31. V4.0 Full-Scope Comprehensive Synthesis complete.
- ~~C.O.N.T.R.A. framework~~ — Done 2026-08-07. 10 detectors, CASI, 12-step ingest pipeline. v3.9.0.
- ~~v3.9.1 CI build~~ — Done 2026-08-11. All 4 platform installers on GitHub Release.
- ~~v3.9.2 CI build~~ — Done 2026-08-11. RAG threshold fix + retriever perf fix + CONTRA nav.
- ~~City of Fresno NSU ingest~~ — Done 2026-10-08. 16,692 matters / 29,308 files / 64,489 findings. Watchdog TCP fix + WAL mode performance enhancements committed.
- ~~TCPD harvest~~ — Done 2026-10-08. 1,262 PDFs via PrimeGov portal.
- ~~CPRA letters (7 letters)~~ — All committed db6c064. Fresno City Clerk, FPD Records, Fresno City unsigned instruments, Fresno County Sheriff, Fresno County BOS Clerk, Fresno County CAO+ITS, TCPD Probation. VPD Flock (CPRA-VPD-FLOCK-001) committed separately.
- ~~Flock Safety cross-jurisdiction lattice~~ — Committed `data/jim/flock_safety_cross_jurisdiction_lattice.json` to jim_collection. Covers Fresno City ($1.5M), VPD (22 docs/355 findings), Fresno County (1 doc).
- ~~CourtListener case law corpus~~ — 133 cases in `legal/cases/`. Authenticated harvest complete 2026-10-19 (commit 84fbf83). Bugs fixed: sub_opinions URL strings (v4 API), Retry-After cap, fast ping.
- ~~CI workflow fixes~~ — Done 2026-10-17. osv-scanner @v2.7.0, git add scope fix, pyproject lint rules.
- ~~Fresno City MAS V2.0~~ — **COMPLETE 2026-10-21**. `docs/synthesis/Fresno_City_MAS_V2_0.md`. 14,409 docs / 64,489 findings / $33.6B unsigned instrument exposure (2,956 critical) / 79 JAG anti-supplanting / 204 Carpenter gaps. CPRA letters to City of Fresno + FPD pending deployment.
- **P0**: Fresno Metropolitan MAS V4.0 — next synthesis integrating City of Fresno MAS V2 + Fresno County MAS V4.0 + FPD MAS V4.0
- **P0**: First `odia contra-ingest` pilot run on actual commercial contract PDFs (DB has 32 entities seeded, schema ready — blocked on ToS/contract PDF source files)
- ~~S.A.B.E.R. ARCADE L-13 DanInTheWild~~ — **COMPLETE 2026-10-20** (Run 7). 512 attempts / 253 passed / 253 bypassed (50% bypass rate) / 6 null. 214 unique jailbreak prompts. MitigationBypass detector. Hitlog: `garak_runs/garak.5ae38736-2858-48be-be6a-4907d49a86a9.hitlog.jsonl`. Config: `data/saber/ai-defense/garak-l13-dan-cpu-config.yaml`. web_injection COMPLETE (8/8 probes).
- **P1**: odia-v2 training — **327,717 examples** in `data/training/` (327,503 + 214 adversarial DAN Type 8 from ARCADE L-13). Blocked: Vast.ai credits $0 + SSH key not uploaded. Starting from odia-v1 weights: 1 epoch (~12–15h) recommended.
- `odia_legal` submodule — Phase 1 foundation (CPRA crosswalk, L-9 recodification, citation parser). Critical deadline: 2028-07-02 (Sunshine Dragnet Phase Zero).
- Multi-index RAG routing — expose `ace_collection` and `jim_collection` via `corpus_filter` in the API
- ~~Migrate `@app.on_event("startup")` → FastAPI `lifespan` handler~~ — Already done; `api.py` uses `@asynccontextmanager` + `lifespan=_lifespan` correctly (verified 2026-10-21)

## odia-v1 Model Reference

| Field | Value |
|---|---|
| Base | `unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit` |
| Method | QLoRA (r=16, alpha=32), 2 epochs |
| Training examples | 87,618 (13,498 reports + 74,120 explanations) |
| Quantization | Q4_K_M GGUF (4.92 GB) |
| Local GGUF | `D:\ODIA\models\odia-v1.q4_k_m.gguf` |
| HuggingFace | `SynTechRev/odia-v1` (private) — GGUF + LoRA adapters |
| Ollama name | `odia-v1` |
| RAG default | Yes — `config/rag_config.py` and `config/ollama_config.yaml` |

## odia_legal Submodule (Planned — Sunshine Dragnet)

10 legal reasoning detectors (L-1 through L-10) to integrate US Code, CFR, California Codes, and case law into the detector pipeline. Transforms observations into litigation-grade legal conclusions.

- **Critical deadline: 2028-07-02** — Sunshine Dragnet Phase Zero.
- Phase 1 (next): `odia_legal` skeleton + CPRA crosswalk + L-9 recodification + basic citation parser.
- Already exists: `legal/` directory, `legal_resolver.py` (partial L-9), `grant_compliance.py` (partial L-5), `legal_routes.py`.

## Conventions

- Format: `black` (line-length 88)
- Lint: `ruff` (select E, F, W, I, N, UP, C90, B)
- Tests: `pytest` in `tests/`, mirrors `src/` structure
- All anomaly detectors are pure functions: `(doc_or_docs) -> list[dict]`
- Anomaly dict shape (enforced across all detectors):
  ```python
  {
      "id":       str,               # stable dot-namespaced identifier, e.g. "fiscal:missing-provenance-hash"
      "issue":    str,               # concise human-readable description
      "severity": "low|medium|high|critical",
      "layer":    str,               # detector name, e.g. "fiscal", "procurement"
      "details":  dict,              # structured, explainable fields
  }
  ```
- Provenance: SHA-256 hashing throughout
- Config: YAML in `config/` for settings, JSON for corpus manifests
- Skipped tests: data-dependent tests use `@pytest.mark.skip` with a reason string; do not delete them
- RAG request schema: `query` (str), `top_k` (int, default 15), `corpus_filter` (list[str]|None), `date_range` (list[str]|None)
- RAG response schema: `answer` (str), `sources` (list[dict]), `confidence` (float), `error` (str|None)

## What NOT to Do

- Do NOT add jurisdiction-specific data (city names, Legistar URLs, personnel names, dollar amounts from any specific audit) to source code
- Do NOT hardcode API keys — use environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
- Do NOT commit data files to `oraculus/corpus/` — that's for user-generated corpus data at runtime
- Do NOT commit generated analysis outputs to `analysis/` or `AUDIT_REPORT.txt` — those are runtime artifacts
- Do NOT commit `oraculus_audit.db` — runtime database, gitignored
- Do NOT commit `data/vectors/*.npy` / `*.pkl` — RAG index artifacts, gitignored
- Do NOT commit `D:\ODIA\models\` or any GGUF — model artifacts, not source
- Do NOT use overly abstract/mythological naming for new code — prefer clear engineering terminology
- Do NOT use `datetime.utcnow()` — use `datetime.now(UTC)` (UTC imported from `datetime`)
- Do NOT open files without `encoding="utf-8"` when reading JSON or text on Windows
- Do NOT use `@app.on_event("startup")` — all new handlers go in the `lifespan` context manager (`api.py:116`)
- Do NOT re-run odia-v1 training — model is complete and deployed; odia-v2 (327,717 examples in `data/training/`) is ready but blocked on Vast.ai credits + SSH key

## Running the Project

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/oraculus_di_auditor --cov-report=term-missing

# Start API server
uvicorn oraculus_di_auditor.interface.api:app --reload

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev

# Build RAG index (requires oraculus_audit.db populated with audit data)
python scripts/build_rag_index.py

# TCPD harvest (pending)
python scripts/ingest_tcpd.py --dry-run
python scripts/ingest_tcpd.py

# Lint and format
black --check src tests
ruff check src tests
```

## File Structure Quick Reference

```
ODIA/
├── src/
│   ├── oraculus_di_auditor/   # Main platform package
│   └── oraculus/              # Legacy thin wrapper (backward compat only)
├── tests/                     # ~3400 tests organized by module
├── scripts/                   # Utility and pipeline scripts
│   ├── build_rag_index.py     # Builds TF-IDF RAG index from live DB
│   ├── ingest_tcpd.py         # TCPD Questys harvest (pending first run)
│   └── examples/              # Jurisdiction-specific example scripts
├── config/                    # Configuration files
│   ├── rag_config.py          # RAG defaults — provider=ollama, model=odia-v1
│   ├── ollama_config.yaml     # Ollama model config — default: odia-v1
│   ├── corpus_manifest.json   # Maps corpus IDs to meeting dates
│   └── jurisdiction.json      # Active jurisdiction config (gitignored)
├── data/vectors/              # RAG vector index artifacts (gitignored)
├── frontend/                  # Next.js 14 production application
├── desktop/                   # Electron desktop app (src/main.js, src/backend.js)
├── docs/                      # Documentation (PHASES.md, RAG_SETUP.md, etc.)
├── legal/                     # Legal reference data (case law, lexicon)
├── constitutional/            # Constitutional linguistic frameworks
├── schemas/                   # JSON Schema definitions
├── templates/                 # Report templates
├── tools/                     # Shell/PowerShell utilities
├── pyproject.toml             # Build config and dependencies
├── CLAUDE.md                  # This file
└── LICENSE                    # MIT
```
