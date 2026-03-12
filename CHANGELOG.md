# Changelog

## 2024-12-29 - Audit Triage & Reporting Pipeline Scaffolding

### Added - Audit Triage & Reporting Infrastructure

**Complete audit workflow scaffolding for manual auditing, legally-defensible reports, and small-model evaluations on lightweight hardware.**

#### Core Files
- **`audit_manifest.schema.json`** - JSON Schema for document manifest validation with fields for document metadata, extraction info, forensics, flags, citations, notes, redaction status, and chain-of-custody
- **`config/defaults.yaml`** - Repository-level configuration for manifests, extraction, PDFs (external storage by default), Ollama, RAG/retrieval, redaction (manual review required), OCR, reports, security, and evaluation
- **`config/ollama_config.yaml`** - Ollama-specific configuration with model settings, generation parameters, system prompts per category, and response validation

#### Scripts
- **`scripts/triage.py`** - Executable CLI tool for creating/updating manifests with SHA-256 checksums, flags (severity: low/medium/high/critical), notes, and chain-of-custody tracking
- **`scripts/ocr_sample.py`** - Lightweight OCR runner using Pillow + pytesseract with optional deskewing via opencv-python; extracts text to `extraction/` and updates manifest metadata
- **`scripts/render_report.py`** - Report renderer using Jinja2 templates; generates Markdown reports with optional HTML/PDF via pandoc or wkhtmltopdf
- **`scripts/eval_harness.py`** - Ollama evaluation harness with TF-IDF-based retrieval (scikit-learn) or naive substring fallback; records model responses, latency, context, and stores logs under `reports/eval/`
- **`scripts/auto_issue_generator.py`** - GitHub issue draft generator for high-severity findings; creates markdown files in `reports/issues/` with pre-filled audit finding templates

#### Templates & Queries
- **`templates/report_template.md`** - Jinja2 Markdown template for executive summary, findings list, evidence manifest table, methodology, legal checks, recommendations, and appendices
- **`queries/sample_queries.json`** - 20 sample audit queries across 6 categories: factual_retrieval, contradiction_detection, irb_consent_check, infrastructure_concern, grant_incentive_detection, executive_summary

#### Compliance & Governance
- **`compliance_checklist.md`** - Four fault-line compliance framework with detailed checklists for DOJ certification, IRB consent (28 C.F.R. Part 46), infrastructure policy, and federal grant incentives; includes red flags, immediate actions, and per-document assessment forms

#### GitHub Integration
- **`.github/ISSUE_TEMPLATE/audit_finding.md`** - Issue template for reporting audit findings with fields for document ID, manifest path, severity, fault-line category, evidence, impact assessment, recommended actions, and chain-of-custody

#### Directory Structure
- **`manifests/`** - Document manifest storage with README
- **`extraction/`** - Extracted text storage with README
- **`reports/eval/`** - Evaluation results directory
- **`reports/issues/`** - Generated issue drafts directory

#### Tests
- **`tests/test_triage_basic.py`** - Unit tests for triage.py covering manifest creation, flag addition, note addition, updates, checksum calculation, and validation

### Documentation
- **README.md** - Added comprehensive "Audit Triage & Report Scaffolding" section with quick start guide, configuration instructions, security/legal warnings, compliance checklist overview, files added, requirements, and next steps for repo owner
- All scripts include detailed docstrings and command-line help with usage examples

### Features
- **Manual Audit Workflow**: Triage script for creating manifests with flags and notes; no heavy dependencies (stdlib + hashlib)
- **OCR Integration**: Pytesseract-based text extraction with confidence scoring and optional deskewing
- **Report Generation**: Jinja2-based Markdown reports with fallback support for missing pandoc/wkhtmltopdf
- **Ollama Evaluation**: Small model evaluation with local inference, TF-IDF retrieval, latency tracking, and structured logging
- **Compliance Framework**: Four fault-line checklist covering DOJ, IRB, Infrastructure, and Grant compliance
- **Security-First**: External PDF storage by default, manual redaction review required, no automatic uploads, chain-of-custody tracking
- **Low-Compute Design**: Runs on lightweight hardware (HP notebook); all processing local; no cloud dependencies

### Security & Legal
- No automated external uploads of PDFs or manifests
- Default configuration stores PDFs externally (configurable via `config/defaults.yaml`)
- Redaction placeholders only; manual review required before disclosure
- Chain-of-custody tracking with SHA-256 checksums and timestamps
- Explicit warning: tooling does not constitute legal advice; consult counsel

### Requirements
- Core: Jinja2, pytesseract, Pillow, pdf2image, scikit-learn (optional but recommended)
- Optional: opencv-python (deskewing), pandoc (reports), wkhtmltopdf (PDF fallback), requests (Ollama HTTP)
- System: tesseract-ocr, Ollama (optional for evaluation)

### Next Steps for Repo Owner
1. Confirm manifest storage location (in-repo vs. external)
2. Confirm redaction policy (placeholders only vs. enabled)
3. Confirm Ollama model names for testing

---

## 2025-12-04
- Trigger CI for PR #37 by adding a small doc change to ensure GitHub Actions picks up the latest push to `copilot/initiate-full-ingestion`.

All notable changes to the Oraculus DI Auditor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - November 17, 2025
- **Documentation** (40.6 KB total):
  - `docs/audit-methodology.md` - Multi-layered anomaly detection framework
  - `docs/recursive-scalar-model.md` - Mathematical framework for pattern lattice analysis
  - `docs/developer-setup.md` - Comprehensive developer onboarding guide
  - `docs/database-design.md` - Database architecture and implementation plan
  - `VALIDATION_REPORT.md` - Project completion assessment (48% complete toward v1.0)
- **API Interface**:
  - `src/oraculus_di_auditor/interface/api.py` - FastAPI REST API stub
  - Endpoints: `/api/v1/health`, `/api/v1/analyze`, `/api/v1/info`
- **Test Coverage** (11 new tests):
  - `tests/test_constitutional_detector.py` - Constitutional anomaly tests
  - `tests/test_surveillance_detector.py` - Surveillance outsourcing tests
  - Enhanced `tests/test_fiscal_detector.py` - Appropriation trail tests

### Enhanced - November 17, 2025
- **Fiscal Detector** (`fiscal.py`):
  - Appropriation trail detection (fiscal amounts without appropriation keywords)
  - Fiscal amount pattern matching ($1,000,000, $1M formats)
  - New anomaly: `fiscal:amount-without-appropriation` (medium severity)
- **Constitutional Detector** (`constitutional.py`):
  - Broad delegation pattern detection (Secretary may determine, as deemed necessary)
  - Intelligible principle checking (limiting standards detection)
  - New anomaly: `constitutional:broad-delegation` (medium severity)
- **Surveillance Detector** (`surveillance.py`):
  - Surveillance keyword detection (biometric, facial recognition, monitoring, tracking)
  - Contractor involvement detection (contractor, vendor, third party)
  - Privacy safeguard checking (warrant, court order, minimization)
  - New anomalies: `surveillance:outsourced-without-safeguards` (high), `surveillance:outsourced-with-safeguards` (low)
- **Scalar Core** (`scalar_core.py`):
  - Weighted scoring by severity (low: 0.02, medium: 0.05, high: 0.10)
  - Pattern lattice coherence bonus (up to 0.02 for strong provenance)
  - More nuanced confidence scoring

### Validated
- ✅ 143/143 tests passing (100% pass rate)
- ✅ All ruff checks passing (zero linting errors)
- ✅ CodeQL security scan: 0 vulnerabilities
- ✅ Pre-commit hooks functional
- ✅ CI/CD pipeline operational

### Added - Earlier
- Complete foundational scaffold implementation per specification
- Core modules: `cli.py`, `config.py`, `ingest.py`, `normalize.py`, `embeddings.py`, `retriever.py`, `analyzer.py`, `reporter.py`, `utils.py`
- Documentation: `ARCHITECTURE.md`, `PHASE_PLAN.md`, `DATA_POLICY.md`, `PROVENANCE.md`
- Data directories: `cases/`, `statutes/`, `vectors/` with proper gitignore
- Test suite for all new modules
- Tool scripts: `import_examples.sh`, `make_local_env.ps1`
- Requirements files: `requirements.txt`, `dev-requirements.txt`
- CLI interface for document ingestion

### Features
- Multi-format document ingestion (TXT, JSON, PDF, XML)
- Text normalization with configurable chunking (2000 chars, 200 overlap)
- TF-IDF based deterministic embeddings (sklearn)
- Vector storage and cosine similarity search
- Advanced anomaly detection:
  - Fiscal: Appropriation trail analysis
  - Constitutional: Broad delegation detection
  - Surveillance: Outsourcing and safeguard validation
  - Long sentence detector (>1000 chars)
  - Cross-reference mismatch detector
  - Contradictory date detector
- Recursive scalar scoring with weighted severity penalties
- JSON and CSV report generation with provenance
- REST API interface (FastAPI)
- Full test coverage for core modules

### Infrastructure
- Parallel module structure: `src/oraculus_di_auditor/` alongside existing `src/oraculus/`
- Backward compatible with existing legislative ingestion system
- Privacy-first data policy with gitignored sensitive directories
- Comprehensive architecture documentation
- Database design ready for implementation

## [0.1.0] - 2025-11-12

### Added
- Initial project structure from PR #7
- Legislative document loader with JSON, TXT, PDF support
- Provenance tracking system with reference graph
- Anomaly detection for missing fields and broken references
- Confidence scoring system
- GitHub Actions CI workflow
- Basic test infrastructure

### Infrastructure  
- Package structure under `src/oraculus/`
- JSON Schema validation
- SHA-256 hashing for document integrity
- Test fixtures and comprehensive test suite
