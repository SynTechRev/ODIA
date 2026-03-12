# Quick Start Guide - Audit Triage Pipeline

**5-Minute Setup for HP Notebook or Similar Lightweight Hardware**

---

## Prerequisites

```bash
# Python 3.11+ required
python --version

# Optional: tesseract-ocr (for OCR functionality)
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

---

## Installation

```bash
# 1. Clone repository (if not already done)
git clone https://github.com/SynTechRev/Oraculus-DI-Auditor.git
cd Oraculus-DI-Auditor

# 2. Install dependencies
pip install -e .

# 3. Verify installation
python scripts/triage.py --help
```

---

## Basic Workflow (3 Steps)

### Step 1: Create Document Manifest

```bash
# Example: Flag a document with high-severity issue
python scripts/triage.py \
  --doc-id FDA_2024_001 \
  --path /path/to/document.pdf \
  --flag "Missing IRB approval documentation" \
  --severity high \
  --category irb_consent \
  --author "Your Name"
```

**Result**: Creates `manifests/FDA_2024_001.json` with SHA-256 checksum and chain-of-custody.

### Step 2: Generate Audit Report

```bash
# Generate Markdown report from all manifests
python scripts/render_report.py \
  --output reports/audit_report.md
```

**Result**: Creates `reports/audit_report.md` with findings, evidence table, and recommendations.

### Step 3: Generate Issue Drafts (Optional)

```bash
# Create GitHub issue drafts for high/critical findings
python scripts/auto_issue_generator.py \
  --severity high --severity critical
```

**Result**: Creates issue markdown files in `reports/issues/` ready for GitHub.

---

## Advanced Features

### OCR Text Extraction

```bash
# Extract text from PDF (requires tesseract-ocr)
python scripts/ocr_sample.py \
  --input /path/to/scanned.pdf \
  --all-pages \
  --out manifests/DOC_ID.json
```

### Ollama Evaluation (Optional)

```bash
# Requires Ollama installed and running (https://ollama.ai)

# Run evaluation on IRB compliance queries
python scripts/eval_harness.py \
  --model llama3-small \
  --category irb_consent_check \
  --top-k 5
```

### Custom Report Configuration

```bash
# Use custom report configuration
python scripts/render_report.py \
  --config report_config.example.json \
  --output reports/custom_report.md \
  --html
```

---

## Configuration

Edit `config/defaults.yaml` to customize:

```yaml
# PDF Storage (default: external)
pdf_storage: "external"
external_pdf_path: "/mnt/secure_storage/pdfs"

# Redaction (default: manual review required)
redaction:
  enabled: false  # Keep false for safety
  auto_detect_pii: true  # Detect but don't auto-redact

# Ollama settings
ollama:
  host: "localhost"
  port: 11434
  default_model: "llama3-small"
```

---

## Compliance Framework

Review `compliance_checklist.md` for the four fault-line framework:

1. **DOJ Certification** - Law enforcement compliance
2. **IRB Consent** - Human subjects protections (28 C.F.R. Part 46)
3. **Infrastructure Policy** - Procurement and facilities
4. **Federal Grant Incentives** - Grant funding compliance

---

## Common Commands

```bash
# Add note to existing manifest
python scripts/triage.py --doc-id DOC123 \
  --note "Legal review completed" --author "Legal Team"

# Update file path and recalculate checksum
python scripts/triage.py --doc-id DOC123 \
  --path /new/path/to/file.pdf --author "Admin"

# Generate report with HTML output (requires pandoc)
python scripts/render_report.py --output report.md --html

# Extract specific pages from PDF
python scripts/ocr_sample.py --input doc.pdf --page 1 --page 3 --page 5

# Run evaluation on specific category
python scripts/eval_harness.py --category contradiction_detection
```

---

## Directory Structure

```
manifests/          # Document manifests (JSON)
extraction/         # Extracted text files
reports/
  ├── audit_*.md    # Generated reports
  ├── eval/         # Ollama evaluation results
  └── issues/       # Issue drafts
queries/            # Audit query definitions
templates/          # Report templates
config/             # Configuration files
```

---

## Security Notes

⚠️ **IMPORTANT**

1. **PDFs stored externally** by default (not in repo)
2. **Manual redaction required** before publishing reports
3. **Consult legal counsel** before public disclosure
4. **Do not commit PII** to version control

---

## Troubleshooting

**Issue**: "No manifests found"  
**Fix**: Create manifests first using `triage.py`

**Issue**: "Pillow required" when running ocr_sample.py  
**Fix**: Already in requirements.txt, but ensure `pip install -e .` ran successfully

**Issue**: "pandoc not found" when generating HTML  
**Fix**: Install pandoc (optional) or use Markdown output only

**Issue**: "Ollama connection refused"  
**Fix**: Install and start Ollama service (optional for evaluation)

---

## Next Steps

1. Review `IMPLEMENTATION_SUMMARY.md` for complete details
2. Read `compliance_checklist.md` for framework guidance
3. Check `README.md` audit triage section for comprehensive docs
4. Run `python scripts/SCRIPT.py --help` for any script details

---

## Support

- **Documentation**: README.md, IMPLEMENTATION_SUMMARY.md, compliance_checklist.md
- **Examples**: report_config.example.json, queries/sample_queries.json
- **Tests**: tests/test_triage_basic.py, tests/test_audit_workflow_integration.py

---

**Ready to start auditing!** 🚀

Questions? See the three configuration questions in IMPLEMENTATION_SUMMARY.md for the repository owner.
