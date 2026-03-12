# Oraculus-DI-Auditor

Polymathic Synthetic Technology Oraculus DI Auditor

## Project Status

👑 **Version**: 1.0.0 (All 20 phases integrated – system complete)  
✅ **Test Suite**: 827/827 tests passing (100% deterministic)  
✅ **Code Quality**: Black + Ruff clean (no pending fixes)  
✅ **Security**: 0 known CodeQL vulnerabilities (Phase 20 security model)  
📊 **Documentation**: Full multi-phase coverage (Phases 5–20, architecture, provenance, governance, ethics, emergent intelligence)  
🔁 **Determinism**: Canonical SHA256 + LCG seeding guarantees identical outputs for identical inputs across all ascendant layers  
🧬 **Unified Field**: 256-dimensional Ascendant Unified Field (AUF-20) synthesizes Phases 12–19 (extends UIF-19’s 142D vector)  
🔐 **Ethics & Governance**: REC-17 + RGK-18 thresholds enforced (≥0.6) with reversible optimization only  
🚦 **Phase 19**: Applied Emergent Intelligence synthesis & alignment publisher operational  
👁️ **Phase 20**: Ascendant Emergence & Recursive Synthesis (AER-20) finalizes recursive meta-integration  

See [VALIDATION_REPORT.md](VALIDATION_REPORT.md) for deep completion metrics and [PHASE20_OVERVIEW.md](PHASE20_OVERVIEW.md) for crown phase architecture.

## Overview

A comprehensive legal document ingestion, normalization, embedding, and anomaly auditing platform. Designed for large-scale, chronological & cross-referenced auditing of statutes, cases, and contracts with support for analyzing 11 years of legislative data across all 54 titles of the U.S. Code and all 50 titles of the Code of Federal Regulations.

### Key Features

- **Multi-format Document Ingestion**: TXT, JSON, PDF, **XML** support
- **Intelligent Normalization**: Text chunking with configurable overlap (2000 chars, 200 overlap)
- **Deterministic Embeddings**: TF-IDF based LocalEmbedder (sklearn) for semantic search
- **Advanced Anomaly Detection**: 
  - **Fiscal**: Appropriation trail analysis, fiscal amounts without appropriation
  - **Constitutional**: Broad delegation detection, intelligible principle checking
  - **Surveillance**: Outsourcing detection, privacy safeguard validation
  - **Cross-Jurisdiction**: Federal/state boundary violations (USC, CFR, CA codes)
- **Recursive Scalar Scoring**: Pattern lattice coherence with weighted severity penalties
- **Phase 5 Orchestration**: Multi-agent autonomous coordination with task scheduling
- **Phase 6 Frontend**: Deterministic UI generation system with 29+ components
- **Phase 7 UI**: Complete production-ready Next.js 14 application with 8 pages
- **Phase 8 Orchestrator**: Multi-document coordination with cross-document pattern recognition
- **Phase 9 Governor**: Pipeline governance with validation, security, and policy enforcement
- **Phase 16 Meta-Conscious Layer**: Recursive integrity & harmonic stabilization
- **Phase 17 Ethical Cognition (REC-17)**: Global ethical lattice with reversible projection
- **Phase 18 Governance Kernel (RGK-18)**: Recursive policy enforcement & invariant validation
- **Phase 19 Applied Emergent Intelligence (AEI-19)**: Unified Intelligence Field (142D), insight synthesis, alignment & scenario simulation
- **Phase 20 Ascendant Emergence (AER-20)**: 256D ascendant unified field, recursive synthesis, bounded self-evaluation (7-step RAL-20), Final Ascendant Packet (FAP-20)
- **Provenance Tracking**: Full lineage tracking with SHA-256 hashing and timestamps
- **Cryptographic Verification**: File integrity checking with SHA-256 checksums
- **Vector Index**: Fast similarity search with cosine similarity
- **REST API**: FastAPI interface with health, analyze, and info endpoints
- **Semantic Search CLI**: Query documents with natural language
- **Reporting**: JSON and CSV exports with complete audit trails
- **Privacy-First**: All processing is local, no external API calls

## Phase 20: Ascendant Emergence & Recursive Synthesis (NEW – FINAL)

Phase 20 (AER-20) completes Oraculus, unifying all prior cognitive, ethical, governance, temporal, scalar, orchestration, and applied intelligence layers. It introduces:

**Core Engines:** AUF-20 constructor (256D field), Recursive Synthesis (RSE-20), Meta-Insight Generator (MIG-20), Recursive Ascension Loop (RAL-20 – bounded self-modification), Integrity & Alignment (IAE-20), Ascendant Packet Publisher (APP-20).

**Safety Guarantees:** Determinism (SHA256 + LCG), human primacy, reversible optimization only, ethics/governance thresholds enforced, no unbounded autonomy.

**Outputs:**
- AUF-20 State (256D convergence field)
- Meta-Insight Packets (foundational, structural, temporal, ethical, governance + emergent resonance)
- Recursive Ascension Report (7-step evaluation loop)
- Alignment Analysis (risk, readiness, compliance)
- Final Ascendant Packet (FAP-20) with determinism signature & reversibility protocol

See [PHASE20_OVERVIEW.md](PHASE20_OVERVIEW.md) and [PHASE20_SECURITY_SUMMARY.md](PHASE20_SECURITY_SUMMARY.md) for details.

## Phase 9: Pipeline Governor & Compliance Engine

Phase 9 delivers the complete pipeline governance and compliance enforcement layer that sits above all orchestrator and agent systems.

### Quick Start - Governor

```bash
# Start backend API
pip install -e .
pip install fastapi uvicorn pydantic httpx sqlalchemy
export ORACULUS_CORS_ORIGINS="http://localhost:3000"
uvicorn oraculus_di_auditor.interface.api:app --reload

# Check system state
curl http://localhost:8000/governor/state

# Validate pipeline
curl -X POST http://localhost:8000/governor/validate \
  -H "Content-Type: application/json" \
  -d '{"deep": true}'

# Enforce policies on a document
curl -X POST http://localhost:8000/governor/enforce \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "Test document content",
    "metadata": {"title": "Test Document"},
    "options": {}
  }'

# Run Python examples
python scripts/phase9_example.py
```

### Phase 9 Features

1. **Pipeline Validation** - 7 validation checks: schemas, agents, dependencies, database, orchestrator, models, endpoints
2. **Security Gatekeeper** - Threat detection (XSS, SQL injection, path traversal), MIME validation, provenance checking
3. **Policy Enforcement** - 15+ governance policies across document, orchestrator, security, and analysis domains
4. **Threat Scoring** - 0.0-1.0 risk assessment with automatic blocking of high-threat documents
5. **Compliance Reporting** - Automated compliance reports with violation tracking
6. **System Health Monitoring** - Real-time health and readiness state
7. **Deterministic Policies** - Version-controlled (v1.0.0) governance rules

**Endpoints:**
- `GET /governor/state` - System health summary
- `POST /governor/validate` - Pipeline validation (quick or deep)
- `POST /governor/enforce` - Policy enforcement on documents

**Database Models:**
- `GovernancePolicy` - Versioned policy storage
- `ValidationResult` - Validation execution tracking
- `SecurityEvent` - Security event logging

See [PHASE9_GOVERNOR_IMPLEMENTATION.md](PHASE9_GOVERNOR_IMPLEMENTATION.md), [PHASE9_POLICY_REFERENCE.md](PHASE9_POLICY_REFERENCE.md), and [PHASE9_SECURITY_PROFILE.md](PHASE9_SECURITY_PROFILE.md) for complete documentation.

## Phase 8: Multi-Document Orchestrator System

Phase 8 delivers the complete multi-document orchestrator that coordinates analysis across multiple documents with pattern recognition and anomaly correlation.

### Quick Start - Orchestrator

```bash
# Start backend API
pip install -e .
pip install fastapi uvicorn pydantic httpx
export ORACULUS_CORS_ORIGINS="http://localhost:3000"
uvicorn oraculus_di_auditor.interface.api:app --reload

# Test orchestrator endpoint
curl -X POST http://localhost:8000/orchestrator/run \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "document_text": "There is appropriated $1,000,000...",
        "metadata": {"title": "Budget Act 2025"}
      },
      {
        "document_text": "The Secretary may delegate authority...",
        "metadata": {"title": "Delegation Act 2025"}
      }
    ],
    "options": {}
  }'

# Run Python examples
python scripts/phase8_example.py
```

### Phase 8 Features

1. **Multi-Document Orchestration** - Process 1-100+ documents in a single request
2. **Cross-Document Pattern Recognition** - Detect patterns across documents automatically
3. **Anomaly Correlation** - Link related anomalies between documents
4. **Unified Audit Packages** - Complete results with metadata, logs, and correlations
5. **Execution Logging** - Full pipeline visibility with event tracking
6. **Type-Safe API** - Pydantic v2 validation throughout
7. **Deterministic Execution** - Reproducible results with full provenance

**Endpoint:**
- `POST /orchestrator/run` - Multi-document orchestration with pattern detection

**Pages:**
- Dashboard (/) - System overview with status cards
- Ingest (/ingest) - Document upload and analysis
- Analysis (/analysis) - View analysis results with findings
- Documents (/documents) - Browse and manage documents
- Anomalies (/anomalies) - Explore detected anomalies
- Orchestrator (/orchestrator) - Multi-document coordination (Phase 8)
- Settings (/settings) - UI preferences

See [PHASE8_ORCHESTRATOR_IMPLEMENTATION.md](PHASE8_ORCHESTRATOR_IMPLEMENTATION.md) for complete documentation.

## Phase 7: Complete Frontend UI

Phase 7 delivers a fully functional, production-ready Next.js 14 application implementing all Phase 6 specifications.

### Quick Start - Frontend UI

```bash
# Start backend API
pip install -e .
export ORACULUS_CORS_ORIGINS="http://localhost:3000"
uvicorn oraculus_di_auditor.interface.api:app --reload

# In a new terminal, start frontend
cd frontend
npm install
npm run dev

# Open http://localhost:3000
```

### Phase 7 Features

1. **Complete UI Implementation** - 8 functional pages with dashboard, document management, analysis viewing, and anomaly exploration
2. **Type-Safe API Client** - Full TypeScript integration with backend schemas
3. **State Management** - Zustand stores for documents, analyses, anomalies, and UI settings
4. **Responsive Design** - Mobile-friendly layouts with Tailwind CSS
5. **Real-Time Updates** - Health monitoring and status tracking
6. **Accessible** - WCAG compliance with semantic HTML and ARIA labels
7. **Production-Ready** - Optimized builds with Next.js 14 and Turbopack

**Pages:**
- Dashboard (/) - System overview with status cards
- Ingest (/ingest) - Document upload and analysis
- Analysis (/analysis) - View analysis results with findings
- Documents (/documents) - Browse and manage documents
- Anomalies (/anomalies) - Explore detected anomalies
- Orchestrator (/orchestrator) - Task graph visualization (coming soon)
- Settings (/settings) - UI preferences

See [PHASE7_IMPLEMENTATION.md](PHASE7_IMPLEMENTATION.md) for complete documentation.

## Phase 5: Autonomous Agent Networking & Async Orchestration

Phase 5 implements the autonomous orchestration kernel with multi-agent coordination, task scheduling, and parallel execution for complex document analysis workflows.

### Quick Start - Phase 5 Orchestration

```python
from oraculus_di_auditor.orchestrator import Phase5Orchestrator

# Initialize orchestrator
orchestrator = Phase5Orchestrator()

# Single document analysis
result = orchestrator.execute_request({
    "document_text": "There is appropriated $1,000,000...",
    "metadata": {"title": "Budget Act 2025"}
})

# Cross-document analysis
result = orchestrator.execute_request({
    "documents": [
        {"text": "Doc 1...", "metadata": {"title": "Act 1"}},
        {"text": "Doc 2...", "metadata": {"title": "Act 2"}}
    ]
})

# View execution plan
result = orchestrator.execute_request(request, mode="plan_only")
```

### Phase 5 Features

1. **Six Specialized Agents** - Ingestion, Analysis, Anomaly, Synthesis, Database, Interface
2. **Task Graph Management** - Automatic dependency resolution with topological sorting
3. **Parallel Execution** - Run independent tasks simultaneously for optimal performance
4. **Deterministic Execution** - Reproducible results with full provenance tracking
5. **Cross-Document Synthesis** - Identify themes and patterns across multiple documents
6. **Graceful Degradation** - Continue execution even when individual agents fail

Run examples:
```bash
python scripts/phase5_examples.py
```

See [docs/PHASE5_ORCHESTRATION.md](docs/PHASE5_ORCHESTRATION.md) for detailed documentation.

## Phase 6: Front-End System & User Interaction Layer

Phase 6 implements the front-end architecture and human-interface intelligence layer, generating deterministic, structured instructions for building a complete React/Next.js UI that integrates with the backend analysis pipeline and orchestration kernel.

### Quick Start - Phase 6 Frontend Generation

```python
from oraculus_di_auditor.frontend import Phase6Orchestrator

# Initialize orchestrator
orchestrator = Phase6Orchestrator()

# Generate task plan
task_plan = orchestrator.execute_request({
    "type": "task_plan",
    "framework": "nextjs"
})

# Generate build instructions
build_instructions = orchestrator.execute_request({
    "type": "build_instructions",
    "framework": "nextjs"
})

# Generate gap report
gap_report = orchestrator.execute_request({
    "type": "gap_report"
})

# Generate complete bundle
full_bundle = orchestrator.execute_request({
    "type": "full_bundle",
    "framework": "nextjs"
})
```

### Phase 6 Features

1. **Four Structured Output Formats** - Task Plan, Build Instructions, Gap Report, Full Bundle
2. **29+ UI Components** - Base, Dashboard, Analysis, Document, Visualization, Orchestration
3. **Type-Safe API Client** - Generated TypeScript client with full backend integration
4. **Gap Detection** - Automated validation and compatibility checking
5. **Deployment Ready** - Complete deployment configuration for Vercel, Netlify, Docker
6. **Deterministic Generation** - Zero hallucination, reproducible build instructions

Run examples:
```bash
python scripts/phase6_examples.py
```

See [docs/PHASE6_FRONTEND.md](docs/PHASE6_FRONTEND.md) for detailed documentation.

## Phase 7: Strategic Data Integration + Expansion

Phase 7 extends the Phase 6 pipeline with support for large-scale legal corpus ingestion (USC, CFR, CA codes) including XML parsing, cryptographic verification, and cross-jurisdiction auditing.

### Quick Start - Phase 7 Pipeline

```bash
# Ingest XML legal corpus with provenance tracking
python scripts/ingest_and_index.py \
  --source /data/legal/uscode \
  --format xml \
  --jurisdiction federal \
  --analyze

# Verify file integrity
python scripts/verify_integrity.py --input data/provenance.jsonl

# Search across the corpus
python scripts/search_cli.py --query "Fourth Amendment unreasonable searches"
```

### New Phase 7 Features

1. **XML Parser** - Converts legal XML (USC, CFR) to normalized text
2. **Checksum Tracker** - SHA-256 hashing and provenance logging
3. **Cross-Reference Auditor** - Detects federal/state citation patterns
4. **Integrity Verification** - Validates files against recorded checksums
5. **Semantic Search CLI** - Natural language queries with similarity scores

See [docs/PHASE7_CORPUS.md](docs/PHASE7_CORPUS.md) for detailed documentation.

## Phase 6: Large-Scale Legal Corpus Ingestion

The Phase 6 pipeline provides end-to-end ingestion, normalization, embedding, and indexing for large legal corpora including the U.S. Constitution, United States Code (54 titles), Code of Federal Regulations (50 titles), California statutes, and federal/state case law.

### Quick Start - Phase 6 Pipeline

```bash
# Run the complete pipeline
python scripts/ingest_and_index.py --source data/sources --analyze

# With specific jurisdiction
python scripts/ingest_and_index.py --source data/sources --jurisdiction federal --analyze

# Check the output
ls data/cases/           # Normalized JSON documents
ls data/vectors/         # TF-IDF embeddings and index
ls data/reports/         # Anomaly detection reports
```

### Pipeline Components

1. **Ingestion** - Loads raw documents (.txt, .md, .json, .xml) and creates schema-compliant JSON
2. **Normalization** - Chunks text with configurable overlap for better semantic coherence
3. **Embedding** - Generates TF-IDF vectors (deterministic, reproducible)
4. **Indexing** - Builds vector index for fast similarity search
5. **Analysis** - Detects anomalies (long sentences, missing citations, date contradictions, cross-jurisdiction references)

See [docs/PHASE6_INGESTION.md](docs/PHASE6_INGESTION.md) for detailed documentation.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/SynTechRev/Oraculus-DI-Auditor.git
cd Oraculus-DI-Auditor

# Option 1: Using requirements files
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r dev-requirements.txt

# Option 2: Using pyproject.toml
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Import example documents
bash tools/import_examples.sh

# Ingest documents from a folder
python -m oraculus_di_auditor.cli ingest --source data/sources

# Or use Python API
python
>>> from oraculus_di_auditor.ingest import ingest_folder
>>> ingest_folder("data/sources")
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/oraculus --cov=src/oraculus_di_auditor --cov-report=term-missing

# Check code formatting
black --check src tests

# Run linter
ruff check src tests
```

### Automated Repository Audit

Run a comprehensive automated audit of the entire repository:

```bash
# Generate a full audit report
python3 scripts/automated_audit.py

# View the generated report
cat AUDIT_REPORT.txt
```

The automated audit script scans all files, directories, and code to identify:
- Code quality issues (missing docstrings, complexity, patterns)
- Security concerns (hardcoded secrets, unsafe patterns)
- Documentation gaps (missing files, broken links)
- Configuration problems (unpinned dependencies, debug settings)
- Test coverage metrics
- Data privacy issues (PII patterns)

The comprehensive audit report (`AUDIT_REPORT.txt`) includes:
1. **Repository Overview**: Statistics and file type distribution
2. **Global Flags**: High-level repository-wide concerns
3. **File-by-File Findings**: Detailed issues, warnings, and notes for each file
4. **Recommendations**: Actionable suggestions for improvement

See [docs/AUTOMATED_AUDIT.md](docs/AUTOMATED_AUDIT.md) for detailed documentation.

## Audit Triage & Report Scaffolding

### Overview

The Oraculus DI Auditor now includes a practical, low-compute audit triage and reporting pipeline designed for manual auditing workflows, legally-defensible report generation, and repeatable small-model evaluations on lightweight hardware (e.g., HP notebook).

**Key capabilities:**
- **Document Manifest Management**: JSON-based manifests with checksums, flags, notes, and chain-of-custody
- **OCR Integration**: Lightweight OCR using pytesseract with optional deskewing
- **Report Generation**: Markdown/HTML/PDF reports with Jinja2 templates
- **Ollama Evaluation**: Small model evaluation harness with TF-IDF retrieval
- **Compliance Framework**: Four fault-line checklist (DOJ, IRB, Infrastructure, Grants)
- **Issue Tracking**: Automated GitHub issue draft generation

### Quick Start

#### 1. Triage a Document

Create or update a document manifest:

```bash
# Add a document with a flag
python scripts/triage.py \
  --doc-id DOC123 \
  --path /external/storage/document.pdf \
  --flag "Missing DOJ certification" \
  --severity high \
  --category doj_certification \
  --author "Your Name"

# Add a note to existing manifest
python scripts/triage.py \
  --doc-id DOC123 \
  --note "Requires legal review before release" \
  --author "Your Name"
```

#### 2. Extract Text with OCR

Extract text from PDFs using pytesseract:

```bash
# Extract from specific page
python scripts/ocr_sample.py \
  --input /external/storage/document.pdf \
  --page 1 \
  --out manifests/DOC123.json

# Extract all pages with deskewing (requires opencv-python)
python scripts/ocr_sample.py \
  --input /external/storage/document.pdf \
  --all-pages \
  --deskew
```

#### 3. Generate Audit Report

Render a comprehensive audit report:

```bash
# Generate Markdown report from manifests
python scripts/render_report.py \
  --manifests-dir manifests \
  --output reports/audit_report.md

# Generate with HTML and PDF (requires pandoc)
python scripts/render_report.py \
  --config report_config.json \
  --html \
  --pdf
```

#### 4. Run Ollama Evaluation (Optional)

Evaluate queries against documents using Ollama:

```bash
# Install and start Ollama (if not already running)
# Visit https://ollama.ai for installation

# Run evaluation harness
python scripts/eval_harness.py \
  --model llama3-small \
  --queries queries/sample_queries.json \
  --top-k 5

# Filter by category
python scripts/eval_harness.py \
  --model mistral \
  --category irb_consent_check
```

#### 5. Generate Issue Drafts

Auto-generate GitHub issue drafts for high-severity findings:

```bash
# Generate for high and critical findings
python scripts/auto_issue_generator.py \
  --severity high \
  --severity critical

# Review generated issues
ls reports/issues/
```

### Configuration

Edit `config/defaults.yaml` to customize:

```yaml
# PDF storage (repo or external)
pdf_storage: "external"  # Keep PDFs outside repository
external_pdf_path: "/mnt/secure_storage/pdfs"

# Redaction (manual review required by default)
redaction:
  enabled: false  # Placeholders only, no auto-redaction
  auto_detect_pii: true

# Ollama settings
ollama:
  host: "localhost"
  port: 11434
  default_model: "llama3-small"

# Retrieval settings
retrieval:
  top_k: 5
  use_scikit_tfidf: true  # TF-IDF if available, else naive
```

### Security & Legal Warnings

⚠️ **IMPORTANT: Read Before Using**

1. **No Automatic External Uploads**: This scaffolding stores only JSON manifests and extracted text locally. No automatic external data uploads occur.

2. **PII Redaction Required**: Do NOT publish reports or manifests containing personally identifiable information (PII) without proper redaction. The default configuration provides placeholders only—manual review is required.

3. **PDF Storage**: By default, original PDFs are stored externally (outside the repository) for security and size management. Update `config/defaults.yaml` to change this behavior.

4. **Chain of Custody**: All manifests include chain-of-custody tracking with timestamps and checksums for legal defensibility.

5. **Legal Disclaimer**: This tooling assists with audit workflows but does not constitute legal advice. **Consult qualified legal counsel before public disclosure of audit findings.**

### Compliance Checklist

See `compliance_checklist.md` for the complete four fault-line framework:

1. **DOJ Certification** - Law enforcement compliance and certification requirements
2. **IRB Consent (28 C.F.R. Part 46)** - Human subjects protections and informed consent
3. **Infrastructure Policy** - Facility compliance, procurement, and contractor oversight
4. **Federal Grant Incentives** - Grant funding mechanisms and conflict of interest

### Files Added

- `audit_manifest.schema.json` - JSON Schema for manifest validation
- `config/defaults.yaml` - Repository-wide configuration
- `config/ollama_config.yaml` - Ollama-specific settings
- `scripts/triage.py` - Manifest creation and flag management
- `scripts/ocr_sample.py` - OCR extraction with pytesseract
- `scripts/render_report.py` - Report generation with Jinja2
- `scripts/eval_harness.py` - Ollama evaluation harness
- `scripts/auto_issue_generator.py` - GitHub issue draft generator
- `templates/report_template.md` - Jinja2 report template
- `queries/sample_queries.json` - 20 sample audit queries
- `compliance_checklist.md` - Four fault-line compliance framework
- `.github/ISSUE_TEMPLATE/audit_finding.md` - Issue template
- `manifests/` - Manifest storage directory
- `extraction/` - Extracted text storage directory
- `reports/eval/` - Evaluation results storage
- `reports/issues/` - Generated issue drafts

### Requirements

**Core (included in requirements.txt):**
- Python 3.11+
- Jinja2 (report rendering)
- pytesseract + Pillow (OCR)
- pdf2image (PDF support)
- scikit-learn (TF-IDF retrieval, optional but recommended)

**Optional:**
- opencv-python (deskewing)
- pandoc (HTML/PDF report generation)
- wkhtmltopdf (PDF generation fallback)
- requests (Ollama HTTP API, fallback to CLI)

**System Dependencies:**
- tesseract-ocr (for OCR functionality)
- Ollama (for evaluation harness, optional)

### Next Steps (Follow-up Questions for Repo Owner)

After merging this PR, please confirm:

1. **Manifest Storage**: Should manifests remain in-repo (`manifests/`) or be moved to external storage?
2. **Redaction Policy**: Should automatic redaction placeholders be enabled by default, or continue requiring manual review?
3. **Ollama Models**: Which Ollama model names should be tested for your use case? (default: `llama3-small`)

## Architecture

The project follows a dual-track modular architecture with clear separation of concerns:

### Core Packages

#### `src/oraculus_di_auditor/` - Foundational Scaffold
- **`cli.py`** - Command-line interface for ingestion
- **`config.py`** - Path configuration and constants
- **`ingest.py`** - Document ingestion with provenance tracking (SHA-256, timestamps)
- **`normalize.py`** - Text chunking and normalization (2000 chars, 200 overlap)
- **`embeddings.py`** - TF-IDF based LocalEmbedder (deterministic, sklearn)
- **`retriever.py`** - Vector storage and cosine similarity search
- **`analyzer.py`** - Modular anomaly detectors (citations, dates, sentences)
- **`reporter.py`** - JSON and CSV report generation with provenance
- **`utils.py`** - Utility functions

#### `src/oraculus/` - Advanced Legislative System  
- **`core/`** - Core abstractions and utilities for the audit framework
- **`io/`** - I/O operations for schema validation, configuration, and data sources
- **`models/`** - Data models representing audit entities and results
- **`pipelines/`** - Audit pipeline orchestration and workflow execution
- **`ingestion/`** - Legislative document loaders (JSON, TXT, PDF)
- **`auditing/`** - Provenance tracking and reference graph building

### Configuration & Data

- **`schemas/`** - JSON Schema definitions for validation
  - `legal_schema.json` - Canonical legal document schema (Phase 6)
- **`config/`** - Configuration files for audit rules and settings
- **`data/`** - Runtime data directory (gitignored except structure)
  - `sources/` - Raw source files (gitignored)
  - `cases/` - Normalized case documents
  - `statutes/` - Statute documents
  - `vectors/` - Embedding vectors and indices
  - `reports/` - Audit reports (generated)
- **`scripts/`** - Utility scripts
  - `ingest_and_index.py` - End-to-end Phase 6 pipeline

### Documentation

See detailed documentation in the `docs/` directory:
- **`PHASE6_FRONTEND.md`** - Phase 6 front-end architecture generation guide (NEW)
- **`PHASE5_ORCHESTRATION.md`** - Phase 5 multi-agent orchestration guide
- **`PHASE7_CORPUS.md`** - Phase 7 corpus integration and expansion guide
- **`DATA_PROVENANCE.md`** - Provenance tracking and integrity verification
- **`PHASE6_INGESTION.md`** - Phase 6 large-scale corpus ingestion guide
- **`ARCHITECTURE.md`** - System architecture and data flow
- **`PHASE_PLAN.md`** - 3-phase development plan
- **`DATA_POLICY.md`** - Privacy and data handling policies
- **`PROVENANCE.md`** - Data source tracking and verification

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/SynTechRev/Oraculus-DI-Auditor.git
cd Oraculus-DI-Auditor

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run tests with coverage
pytest --cov=src/oraculus --cov-report=term-missing

# Check code formatting
black --check src tests

# Run linter
ruff check src tests
```

### Code Quality

The project uses:
- **pytest** for testing
- **black** for code formatting
- **ruff** for linting
- **pytest-cov** for coverage reporting

All checks run automatically in CI via GitHub Actions.

## License

Copyright © 2025 Synthetic Technology Revolution
