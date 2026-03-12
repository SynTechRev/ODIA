# ODIA (Oraculus DI Auditor) — Project Brief

## What This Project Is

ODIA is a **general-purpose legal document ingestion, normalization, and anomaly auditing platform**. It ingests legal documents (PDF, XML, JSON, TXT), normalizes and chunks them, generates deterministic TF-IDF embeddings, detects anomalies (fiscal, constitutional, surveillance, cross-jurisdiction), orchestrates multi-document analysis, and enforces governance policies — all with full provenance tracking.

**Repository**: https://github.com/SynTechRev/ODIA
**License**: MIT

## Current State

- **Version**: 2.0.0 (post-generalization cleanup)
- **Python**: 3.11+ required
- **Tests**: 827 tests across `tests/` (organized by module/phase)
- **Working core**: Phases 5–9 (ingestion, analysis, orchestration, governance) are functional and tested
- **Higher phases** (12–20): Architectural scaffolding exists — these are experimental/theoretical
- **Frontend**: Next.js 14 app in `frontend/` (production-ready skeleton)
- **API**: FastAPI backend in `src/oraculus_di_auditor/interface/api.py`

## Architecture

Two source packages under `src/`:

- `oraculus_di_auditor/` — Main platform: ingestion, analysis, orchestrator, governor, API, frontend generation, higher-phase engines
- `oraculus/` — Legislative scaffold: document loaders, provenance tracker, pipeline abstractions

Key module groups:
- `analysis/` — Anomaly detectors (fiscal, constitutional, surveillance, cross-reference, scalar scoring)
- `orchestrator/` — Multi-agent task graph coordination (Phase 5/8)
- `governor/` — Pipeline governance and policy enforcement (Phase 9)
- `ingestion/` — XML parser, checksum tracker, document engine
- `interface/` — FastAPI REST API with routes for orchestrator, governor, mesh, GCN
- `frontend/` — Phase 6 frontend generation system (component specs, API client, gap detection)
- `rec17/`, `rgk18/`, `aei19/`, `aer20/` — Higher-phase experimental engines (Phases 17–20)
- `mesh/` — Adaptive agent mesh (Phase 13/14)
- `scalar_convergence/` — Recursive scalar scoring (Phase 12)
- `qdcl/` — Quantum-inspired decision/cognition layer (Phase 11)
- `otge15/` — Temporal governance engine (Phase 15)
- `evolution/` — Evolution engine

## Development Priorities

The project is pivoting from a single-jurisdiction audit tool to a **general-purpose legal auditing platform**. Current priorities in order:

1. **README rewrite** — Lead with clear overview, one Quick Start, then architecture. Move phase details to `docs/PHASES.md`. Target ~150–200 lines.
2. **Package consolidation** — Evaluate merging `src/oraculus/` into `src/oraculus_di_auditor/` under a unified namespace.
3. **Configurable jurisdiction system** — The corpus loader (`scripts/corpus_manager.py`) now loads from `config/corpus_manifest.json`. Extend this pattern across the pipeline so any Legistar-based jurisdiction can be configured.
4. **Stabilize core pipeline** — Ensure Phases 5–9 run end-to-end with the new configurable data sources. Integration tests.
5. **Rename higher-phase terminology** — Replace mythological/abstract names with plain engineering language (e.g., "Ascendant Unified Field" → "Composite Feature Vector", "Recursive Ascension Loop" → "Validation Pipeline").
6. **Clean public presentation** — Improve docs, add contributing guide, ensure the repo is approachable.

## Conventions

- Format: `black` (line-length 88)
- Lint: `ruff` (select E, F, W, I, N, UP, C90, B)
- Tests: `pytest` in `tests/`, mirrors `src/` structure
- All anomaly detectors return structured dicts with `type`, `severity`, `description`, `evidence`
- Provenance: SHA-256 hashing throughout
- Config: YAML in `config/` for settings, JSON for corpus manifests
- Phase docs: `PHASE*_OVERVIEW.md` at repo root (to be moved to `docs/`)

## What NOT to Do

- Do NOT add jurisdiction-specific data (city names, Legistar URLs, personnel names, dollar amounts from any specific audit)
- Do NOT hardcode API keys — use environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
- Do NOT commit data files to `oraculus/corpus/` — that's for user-generated corpus data at runtime
- Do NOT commit generated analysis outputs to `analysis/` — those are runtime artifacts
- Do NOT use overly abstract/mythological naming for new code — prefer clear engineering terminology

## Running the Project

```bash
# Install
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/oraculus --cov=src/oraculus_di_auditor --cov-report=term-missing

# Start API server
uvicorn oraculus_di_auditor.interface.api:app --reload

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev

# Lint and format
black --check src tests
ruff check src tests
```

## File Structure Quick Reference

```
ODIA/
├── src/
│   ├── oraculus_di_auditor/   # Main platform package (157 modules)
│   └── oraculus/              # Legislative scaffold package
├── tests/                     # 827 tests organized by module
├── scripts/                   # Utility and pipeline scripts
│   └── examples/              # Jurisdiction-specific example scripts
├── frontend/                  # Next.js 14 application
├── config/                    # Configuration files (YAML, JSON)
├── docs/                      # Documentation (45 files)
├── legal/                     # Legal reference data (case law, lexicon)
├── constitutional/            # Constitutional linguistic frameworks
├── schemas/                   # JSON Schema definitions
├── templates/                 # Report templates
├── tools/                     # Shell/PowerShell utilities
├── pyproject.toml             # Build config and dependencies
├── CLAUDE.md                  # This file
└── LICENSE                    # MIT
```
