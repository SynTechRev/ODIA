# ODIA (Oraculus DI Auditor) — Project Brief

## What This Project Is

ODIA is a **general-purpose legal document ingestion, normalization, and anomaly auditing platform**. It ingests legal documents (PDF, XML, JSON, TXT), normalizes and chunks them, generates deterministic TF-IDF embeddings, detects anomalies (fiscal, constitutional, surveillance, cross-jurisdiction, procurement), orchestrates multi-document analysis, and enforces governance policies — all with full provenance tracking.

**Repository**: https://github.com/SynTechRev/ODIA
**License**: MIT

## Current State

- **Version**: 2.0.0
- **Python**: 3.11+ required (tested on 3.13)
- **Tests**: 2719 passing, 9 skipped (data-dependent corpus/transparency tests)
- **Working core**: Phases 5–9 (ingestion, analysis, orchestration, governance) are functional and tested
- **Higher phases** (12–20): Architectural scaffolding exists — these are experimental/theoretical
- **Frontend**: Next.js 14 app in `frontend/` (production-ready skeleton)
- **API**: FastAPI backend in `src/oraculus_di_auditor/interface/api.py`

## Architecture

Two source packages under `src/`:

- `oraculus_di_auditor/` — Main platform: ingestion, analysis, orchestrator, governor, API, frontend generation, higher-phase engines
- `oraculus/` — Legacy thin wrapper; empty `__init__.py`. Submodules (core, ingestion, pipelines, etc.) remain for backward compatibility but new code goes in `oraculus_di_auditor/`

Key module groups inside `oraculus_di_auditor/`:
- `analysis/` — Anomaly detectors: fiscal, constitutional, surveillance, cross-reference, procurement timeline, scalar scoring
- `adapters/` — External data source adapters (Sprint 9): `base.py` (DataSourceAdapter ABC with cache-aside), `ccops_adapter.py` (11 ACLU CCOPS mandates), `atlas_adapter.py` (EFF Atlas of Surveillance, JSON/CSV), `compliance_engine.py` (ComplianceAssessmentEngine — maps ODIA findings to CCOPS mandates, produces ComplianceScorecard)
- `orchestrator/` — Multi-agent task graph coordination (Phase 5/8)
- `governor/` — Pipeline governance and policy enforcement (Phase 9)
- `ingestion/` — XML parser, checksum tracker, document engine
- `interface/` — FastAPI REST API with routes for orchestrator, governor, mesh, GCN, compliance (`POST /compliance/assess`, `GET /compliance/mandates`)
- `frontend/` — Phase 6 frontend generation system (component specs, API client, gap detection)
- `rec17/`, `rgk18/`, `aei19/`, `aer20/` — Higher-phase experimental engines (Phases 17–20)
- `mesh/` — Adaptive agent mesh (Phase 13/14)
- `scalar_convergence/` — Recursive scalar scoring (Phase 12)
- `qdcl/` — Quantum-inspired decision/cognition layer (Phase 11)
- `otge15/` — Temporal governance engine (Phase 15)
- `evolution/` — Evolution engine

## Development Priorities

All six original priorities are complete. Active work areas:

1. ~~README rewrite~~ — Done. `docs/PHASES.md` created; README is ~150 lines.
2. ~~Package consolidation~~ — Done. `oraculus/` is now a thin wrapper; `oraculus_di_auditor/` is authoritative.
3. ~~Configurable jurisdiction system~~ — Done. `scripts/corpus_manager.py` loads from `config/corpus_manifest.json`. Jurisdiction config in `config/jurisdiction.json`.
4. ~~Stabilize core pipeline~~ — Done. 2100+ tests pass; Windows cp1252 and datetime compat fixed.
5. ~~Rename higher-phase terminology~~ — Done. Mythological names replaced with plain engineering terms.
6. ~~Clean public presentation~~ — Done. Contributing guide added; repo is approachable.

**Next areas to consider**: extend `analyze_document()` in `audit_engine.py` to include the procurement timeline detector; add more detector coverage (grant funding trails, vote-date alignment).

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

## What NOT to Do

- Do NOT add jurisdiction-specific data (city names, Legistar URLs, personnel names, dollar amounts from any specific audit)
- Do NOT hardcode API keys — use environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
- Do NOT commit data files to `oraculus/corpus/` — that's for user-generated corpus data at runtime
- Do NOT commit generated analysis outputs to `analysis/` or `AUDIT_REPORT.txt` — those are runtime artifacts
- Do NOT use overly abstract/mythological naming for new code — prefer clear engineering terminology
- Do NOT use `datetime.utcnow()` — use `datetime.now(UTC)` (UTC imported from `datetime`)
- Do NOT open files without `encoding="utf-8"` when reading JSON or text on Windows

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
├── tests/                     # ~2130 tests organized by module
├── scripts/                   # Utility and pipeline scripts
│   └── examples/              # Jurisdiction-specific example scripts
├── config/                    # Configuration files (YAML, JSON)
│   ├── corpus_manifest.json   # Maps corpus IDs to meeting dates
│   └── jurisdiction.json      # Active jurisdiction config (gitignored)
├── frontend/                  # Next.js 14 application
├── docs/                      # Documentation (PHASES.md, contributing guide, etc.)
├── legal/                     # Legal reference data (case law, lexicon)
├── constitutional/            # Constitutional linguistic frameworks
├── schemas/                   # JSON Schema definitions
├── templates/                 # Report templates
├── tools/                     # Shell/PowerShell utilities
├── pyproject.toml             # Build config and dependencies
├── CLAUDE.md                  # This file
└── LICENSE                    # MIT
```
