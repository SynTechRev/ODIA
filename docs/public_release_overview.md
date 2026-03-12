# Public Release Overview

This document describes the **Public Transparency Release Package v1** for the Oraculus-DI-Auditor system.

## Purpose

The Public Transparency Release Package provides complete visibility into the 2014–2025 California legislative corpus audit. It is designed for:

- **External Auditors** – Independent verification of methodology and findings
- **Legal Counsel** – Discovery and compliance documentation
- **Public Records Requestors** – Transparent access to audit results
- **Researchers** – Reproducible analysis methodology

## Package Contents

### `/transparency_release/` Directory

The transparency release package is contained in a dedicated top-level directory with the following structure:

```
transparency_release/
├── README_PUBLIC_OVERVIEW.md          # Non-technical overview
├── HOW_TO_REPRODUCE_THE_AUDIT.md      # Reproduction instructions
├── HASH_MANIFEST_FULL_SHA256.txt      # SHA-256 hashes of all files
├── HASH_MANIFEST_STRUCTURE_SHA256.txt # Directory structure hash
├── corpus_manifest.json               # Complete file inventory
├── anomaly_summary_public.json        # Aggregated anomaly report
├── timeline_public.png                # Visual timeline
├── modules/
│   ├── ace_summary_public.json        # ACE analysis summary
│   ├── vicfm_summary_public.json      # Vendor influence summary
│   ├── caim_summary_public.json       # Cross-agency summary
│   ├── pdf_forensics_summary_public.json  # PDF metadata summary
│   └── vendor_map_public.json         # Vendor relationship map
├── reports/
│   ├── ingestion_report_public.json   # Document ingestion log
│   ├── validation_report_public.json  # Validation results
│   ├── forensic_report_public.json    # Forensic analysis report
│   └── legislative_timeline_public.json  # Chronological timeline
└── scripts/
    └── reproduce_audit.sh             # Reproducibility script
```

## Documentation Files

### README_PUBLIC_OVERVIEW.md

A high-readability, non-technical overview covering:
- What the audit is
- What data was analyzed
- Categories of anomalies found
- How authenticity is preserved
- How to independently verify artifacts

### HOW_TO_REPRODUCE_THE_AUDIT.md

Complete reproduction instructions including:
- Environment setup requirements
- Step-by-step commands
- One-command full reproduction
- Expected outputs
- Troubleshooting guide

## Cryptographic Integrity

### Hash Manifests

Two hash manifests ensure tamper-evident verification:

1. **HASH_MANIFEST_FULL_SHA256.txt**
   - Contains SHA-256 hash of every file in the release
   - Format: `<hash>  <relative_path>`
   - Sorted alphabetically for deterministic ordering

2. **HASH_MANIFEST_STRUCTURE_SHA256.txt**
   - Contains SHA-256 hash of the complete file listing
   - Ensures directory structure hasn't been modified

### Verification Process

```bash
# Verify all file hashes
cd transparency_release
sha256sum -c HASH_MANIFEST_FULL_SHA256.txt

# Expected output: "OK" for each file
```

## Public-Safe Reports

All reports in the transparency release are sanitized to remove:
- Internal file system paths
- Server names or IP addresses
- User credentials or API keys
- Proprietary configuration details

Reports include:
- Aggregated counts and statistics
- Category classifications
- Timeline data
- Methodology descriptions

## Use Cases

### Legal Discovery

For legal proceedings or FOIA requests:
1. Reference the `corpus_manifest.json` for complete file inventory
2. Use hash manifests to verify document integrity
3. Cite methodology from `README_PUBLIC_OVERVIEW.md`

### Independent Audit

For third-party verification:
1. Follow `HOW_TO_REPRODUCE_THE_AUDIT.md`
2. Run `reproduce_audit.sh --full`
3. Compare generated hashes with published manifests

### Academic Research

For research purposes:
1. Review module summaries in `/modules/`
2. Analyze timeline data in `/reports/legislative_timeline_public.json`
3. Cite methodology and version information

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | December 2025 | Initial public release |

## Related Documentation

- [Legal Discovery Fulfillment](legal_discovery_fulfillment.md)
- [Reproducibility Protocol](reproducibility_protocol.md)
- [Main README](../README.md)

---

*This document is part of the Oraculus-DI-Auditor documentation suite.*
