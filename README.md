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
