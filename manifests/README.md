# Manifests Directory

This directory stores JSON manifest files for audited documents. Each manifest contains metadata, flags, notes, and chain-of-custody information for a single document.

## File Naming Convention

Manifest files should be named: `{document_id}.json`

Example: `DOC123.json`, `FDA_2024_001.json`

## Manifest Schema

All manifest files must validate against `audit_manifest.schema.json` in the repository root.

## Security Warning

⚠️ **Do NOT commit manifests containing PII or sensitive information without proper redaction.**

Manifests may reference external PDF files stored outside the repository. The default configuration (`config/defaults.yaml`) stores PDFs externally for security and size management.

## Usage

Create manifests using the triage script:

```bash
python scripts/triage.py --doc-id DOC123 --path /external/storage/file.pdf --flag "Missing certification" --severity high --author "Your Name"
```

## Contents

Each manifest includes:
- **Document ID and metadata**: Unique identifier, source, path, uploader, checksum
- **Extraction info**: OCR status, text extraction confidence, page count
- **Forensics**: File size, MIME type, dates, PDF metadata
- **Flags**: Audit findings with severity levels
- **Citations**: Legal references within the document
- **Notes**: Audit observations and comments
- **Redaction status**: PII detection and redaction tracking
- **Chain of custody**: Complete audit trail

## Example

See the triage script for examples of creating and updating manifests.
