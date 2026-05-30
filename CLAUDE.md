# ODIA (Oraculus Decimus Intellect Analyst) — Project Brief

## What This Project Is

ODIA is a **general-purpose legal document ingestion, normalization, and anomaly auditing platform**. It ingests legal documents (PDF, XML, JSON, TXT), normalizes and chunks them, generates deterministic TF-IDF embeddings, detects anomalies (fiscal, constitutional, surveillance, cross-jurisdiction, procurement), orchestrates multi-document analysis, enforces governance policies, and supports natural language querying of the full audit corpus via a local RAG pipeline — all with full provenance tracking.

**Repository**: https://github.com/SynTechRev/ODIA
**License**: MIT

## Current State

- **Version**: 3.5.3
- **Python**: 3.11+ required (tested on 3.14)
- **Tests**: 3396 passing, 17 skipped (data-dependent corpus/transparency tests)
- **Working core**: Ingestion, analysis, orchestration, governance, compliance, auth, RAG — all functional and tested
- **Higher phases** (12–20): Architectural scaffolding exists — experimental/theoretical
- **Frontend**: Next.js 14 production app in `frontend/` — Upload, Results History, Synthesis/RAIA, RAG Query, Compliance, Legal, Config
- **API**: FastAPI backend in `src/oraculus_di_auditor/interface/api.py` + modular routes in `interface/routes/`
- **Desktop**: Electron builds via GitHub Actions (`Build and Release Desktop Apps` workflow)
- **RAG**: Local Ollama llama3.1:8b — `POST /api/v1/rag/query`, `GET /api/v1/rag/status`; index built by `scripts/build_rag_index.py`
- **DB**: SQLAlchemy + SQLite (`oraculus_audit.db`) — persists documents, audits, anomalies, governance, agent mesh state

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
- `llm_providers.py` — Ollama/OpenAI/Anthropic LLM abstraction (300s timeout for cold model loads)
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
7. ~~DB-persisted audits~~ — Done. SQLAlchemy + SQLite, history backed to 10k scale.
8. ~~SynTechRev brand + desktop builds~~ — Done. Electron CI ships `.exe`/`.dmg`/`.AppImage`.
9. ~~RAG on Ollama~~ — Done. `build_rag_index.py` + `/api/v1/rag/query` + RAG Query UI page.

**Active next steps**:
- Populate `oraculus_audit.db` with real audit corpus and run `build_rag_index.py` to make RAG live
- Extend `analyze_document()` in `audit_engine.py` to include the procurement timeline detector
- Migrate `@app.on_event("startup")` → FastAPI `lifespan` handler (deprecation warnings in every test run)
- Implement multi-index RAG routing — expose `corpus`/`ace`/`jim` sub-indexes via `corpus_filter` in the API (index builder already creates them)

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
      "severity": "low|medium|high",
      "layer":    str,               # detector name, e.g. "fiscal", "procurement"
      "details":  dict,              # structured, explainable fields
  }
  ```
- Provenance: SHA-256 hashing throughout
- Config: YAML in `config/` for settings, JSON for corpus manifests
- Skipped tests: data-dependent tests use `@pytest.mark.skip` with a reason string; do not delete them
- RAG request schema: `query` (str), `top_k` (int, default 5), `corpus_filter` (list[str]|None), `date_range` (list[str]|None)
- RAG response schema: `answer` (str), `sources` (list[dict]), `confidence` (float), `error` (str|None)

## What NOT to Do

- Do NOT add jurisdiction-specific data (city names, Legistar URLs, personnel names, dollar amounts from any specific audit)
- Do NOT hardcode API keys — use environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
- Do NOT commit data files to `oraculus/corpus/` — that's for user-generated corpus data at runtime
- Do NOT commit generated analysis outputs to `analysis/` or `AUDIT_REPORT.txt` — those are runtime artifacts
- Do NOT commit `oraculus_audit.db` — runtime database, gitignored
- Do NOT commit `data/vectors/*.npy` / `*.pkl` — RAG index artifacts, gitignored
- Do NOT use overly abstract/mythological naming for new code — prefer clear engineering terminology
- Do NOT use `datetime.utcnow()` — use `datetime.now(UTC)` (UTC imported from `datetime`)
- Do NOT open files without `encoding="utf-8"` when reading JSON or text on Windows
- Do NOT use `@app.on_event("startup")` — migrate new handlers to the `lifespan` context manager

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
│   └── examples/              # Jurisdiction-specific example scripts
├── config/                    # Configuration files (YAML, JSON)
│   ├── corpus_manifest.json   # Maps corpus IDs to meeting dates
│   └── jurisdiction.json      # Active jurisdiction config (gitignored)
├── data/vectors/              # RAG vector index artifacts (gitignored)
├── frontend/                  # Next.js 14 production application
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
