# ODIA — Oraculus DI Auditor

A general-purpose legal document ingestion, normalization, and anomaly auditing platform.

Ingest legal documents (PDF, XML, JSON, TXT), detect anomalies (fiscal, constitutional,
surveillance, cross-jurisdiction), orchestrate multi-document analysis, and enforce
governance policies — all with full SHA-256 provenance tracking. Configurable for any
Legistar-based jurisdiction or custom legal corpus.

**Repository**: https://github.com/SynTechRev/ODIA
**License**: MIT
**Python**: 3.11+

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/SynTechRev/ODIA.git
cd ODIA
pip install -e ".[dev]"

# Run tests
pytest

# Start the API server
uvicorn oraculus_di_auditor.interface.api:app --reload

# Start the frontend (separate terminal)
cd frontend && npm install && npm run dev
# Open http://localhost:3000
```

---

## Features

- **Multi-format ingestion** — TXT, JSON, PDF, XML
- **Anomaly detection** — fiscal (appropriation trails), constitutional (broad delegation), surveillance (outsourcing, privacy), cross-jurisdiction (federal/state boundary violations)
- **Deterministic embeddings** — TF-IDF via scikit-learn; reproducible across runs
- **Multi-document orchestration** — task graph with dependency resolution and parallel execution
- **Pipeline governance** — policy enforcement, threat scoring, compliance reporting (Phase 9)
- **Configurable corpus** — jurisdiction-agnostic; configure any corpus via `config/corpus_manifest.json`
- **Provenance tracking** — SHA-256 hashing and full lineage on every document
- **REST API** — FastAPI with endpoints for analysis, orchestration, and governance
- **Frontend** — Next.js 14 dashboard (ingest, analysis, anomalies, documents, orchestrator)
- **Audit triage pipeline** — manifest management, OCR extraction, report generation, issue drafts
- **RAG query engine** — multi-source retrieval (documents, findings, analysis results, legal reference) with LLM-ready context building
- **Legal reference system** — 255 searchable terms (Bouvier 1856, Anderson 1889, Cornell Wex, Latin maxims), 64 SCOTUS/federal cases, 35 extracted holdings, superseded-doctrine tracking; all public domain / open access; 433 RAG-indexed chunks ([docs/LEGAL_REFERENCE.md](docs/LEGAL_REFERENCE.md))
- **Privacy-first** — all processing is local; no external API calls required

---

## Architecture

Two source packages under `src/`:

```
src/
├── oraculus_di_auditor/   # Main platform (ingestion → analysis → API)
│   ├── analysis/          # Anomaly detectors: fiscal, constitutional, surveillance, cross-reference
│   ├── ingestion/         # XML parser, checksum tracker, document engine
│   ├── orchestrator/      # Multi-agent task graph (Phase 5/8)
│   ├── governor/          # Policy enforcement, security gatekeeper (Phase 9)
│   ├── interface/         # FastAPI app + route handlers
│   ├── frontend/          # Frontend generation system (component specs, API client)
│   ├── db/                # SQLAlchemy models, CRUD, session
│   └── ...                # Higher-phase engines (see docs/PHASES.md)
└── oraculus/              # Legislative scaffold (loaders, provenance, pipeline abstractions)
```

Full architecture details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
Phase-by-phase engine reference: [docs/PHASES.md](docs/PHASES.md)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | System health |
| `POST` | `/analyze` | Analyze a single document |
| `POST` | `/orchestrator/run` | Multi-document orchestration |
| `GET` | `/governor/state` | Pipeline health summary |
| `POST` | `/governor/validate` | Validate pipeline (quick or deep) |
| `POST` | `/governor/enforce` | Policy enforcement on a document |

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
- Vendor playbook replication — same anomaly patterns from the same vendor across multiple jurisdictions
- Procurement parallels — shared sole-source justifications or timeline irregularities
- Regional governance gaps — common policy absences across a geographic cluster

**Output:** JSON + Markdown comparative reports with risk ranking and recommendations.

A synthetic sample dataset covering three California jurisdictions is included in
`data/multi_jurisdiction/`. See [docs/MULTI_JURISDICTION.md](docs/MULTI_JURISDICTION.md)
for full setup and configuration guidance.

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
available via `POST /compliance/assess` in the API.

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
```

All anomaly detectors return structured results:
```python
{"type": str, "severity": str, "description": str, "evidence": str}
```

See [docs/developer-setup.md](docs/developer-setup.md) for full setup instructions.

---

## Legal & Security

- No automatic external data uploads
- PII redaction is **not** automatic — manual review required before publishing reports
- Original PDFs stored externally by default (`config/defaults.yaml`)
- All manifests include chain-of-custody timestamps and checksums
- **Consult qualified legal counsel before public disclosure of audit findings**

See [docs/DATA_POLICY.md](docs/DATA_POLICY.md) and [compliance_checklist.md](compliance_checklist.md).

---

## License

Copyright © 2025 Synthetic Technology Revolution — MIT License
