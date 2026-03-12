# DPMM v1.0 - Deep Packet Metadata Miner (PDF Forensics)

## Overview

The **Deep Packet Metadata Miner (DPMM)** is a PDF-level forensic metadata analysis module that extends the Oraculus-DI Auditor into forensic document analysis. It extracts, analyzes, and correlates metadata across the 11-year legislative corpus (2014–2025).

DPMM correlates **metadata → timestamps → producers → XMP → origin patterns** into a unified forensic model.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DPMM v1.0 Pipeline                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │
│  │   INPUTS      │    │   ANALYSIS    │    │   OUTPUTS     │       │
│  ├───────────────┤    ├───────────────┤    ├───────────────┤       │
│  │ • PDF files   │    │ • Metadata    │    │ • forensic    │       │
│  │ • ACE_REPORT  │ -> │   Extraction  │ -> │   _report.json│       │
│  │   .json       │    │ • Temporal    │    │ • metadata    │       │
│  │ • Vendor      │    │   Analysis    │    │   _inconsis   │       │
│  │   Reports     │    │ • XMP Parsing │    │   tency_map   │       │
│  │               │    │ • Producer    │    │ • pdf_origin  │       │
│  │               │    │   Forensics   │    │   _clusters   │       │
│  │               │    │ • Origin      │    │ • DPMM_SUMMARY│       │
│  │               │    │   Clustering  │    │   .md         │       │
│  └───────────────┘    └───────────────┘    └───────────────┘       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    SCORING ENGINE (0-100)                    │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ ForensicScore = (TimestampIntegrity × 0.25) +                │   │
│  │                 (ProducerConsistency × 0.20) +               │   │
│  │                 (XMPIntegrity × 0.20) +                      │   │
│  │                 (OriginSignatureStability × 0.20) +          │   │
│  │                 (ACE_Linkage × 0.15)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Sources

### Input Files

| File | Location | Description |
|------|----------|-------------|
| PDF files | `oraculus/corpus/{CORPUS_ID}/attachments/*.pdf` | PDF documents to analyze |
| ACE_REPORT.json | Project root | ACE anomaly report for cross-linking |
| vendor_index.json | Analysis output | Vendor extraction results |
| agency_index.json | Analysis output | Agency extraction results |

### Output Files

| File | Description |
|------|-------------|
| `forensic_report.json` | Complete forensic analysis with metadata and scores |
| `metadata_inconsistency_map.json` | Detected mismatches grouped by year |
| `pdf_origin_clusters.json` | K-means/deterministic origin clustering |
| `pdf_forensics_graph.json` | Graph structure for visualization |
| `DPMM_SUMMARY.md` | Human-readable executive summary |
| `FORENSIC_ANOMALY_LINKS.json` | Cross-links to ACE anomalies |
| `FORENSIC_VENDOR_OVERLAPS.json` | Overlaps with vendor patterns |
| `FORENSIC_AGENCY_PATTERNS.json` | Agency-level forensic patterns |

## Metadata Extraction

### PDF Info Dictionary

Extracts standard PDF metadata fields:

- `/Producer` - Software that created the PDF
- `/Creator` - Original application that created content
- `/Author` - Document author
- `/CreationDate` - When the PDF was created
- `/ModDate` - When the PDF was last modified
- `/Title`, `/Subject` - Document metadata

### XMP Metadata Block

Parses XML-based XMP metadata:

- `xmp:CreateDate` - XMP creation timestamp
- `xmp:ModifyDate` - XMP modification timestamp
- `xmp:CreatorTool` - Tool that created XMP
- `pdf:Producer` - PDF producer from XMP
- `pdfaid:part` / `pdfaid:conformance` - PDF/A compliance

### File Integrity

Generates hash fingerprints:

- MD5 hash for quick comparison
- SHA256 hash for integrity verification

## Anomaly Detection

### 1. Temporal Anomalies

Detects time-related inconsistencies:

| Subtype | Description | Severity |
|---------|-------------|----------|
| `creation_after_modification` | Creation date later than modification date | Medium |
| `modification_after_meeting` | File modified years after meeting date | High |
| `future_dated` | Timestamp in the future | High |
| `producer_timeline_mismatch` | Software released after document date | High |

### 2. Producer/Creator Forensics

Identifies software-related anomalies:

| Subtype | Description | Severity |
|---------|-------------|----------|
| `platform_mismatch` | e.g., Apple software on Windows agency | Medium |
| `vendor_software_detected` | Links producer to known vendor | Low |

### 3. XMP Anomalies

Tracks XMP metadata issues:

| Subtype | Description | Severity |
|---------|-------------|----------|
| `missing_xmp` | No XMP metadata block | Low |
| `malformed_xmp` | Invalid XMP structure | Medium |
| `truncated_xmp` | Incomplete XMP packet | Medium |
| `multiple_xmp_packets` | Version stacking detected | Medium |
| `ocr_regenerated` | OCR software in XMP | Low |

### 4. Retroactive Edit Indicators

Detects possible post-hoc modifications:

| Subtype | Description | Severity |
|---------|-------------|----------|
| `significant_year_gap` | 2+ year gap between creation/modification | Medium-High |
| `rescan_detected` | Digital document re-scanned | Medium |
| `producer_mismatch` | Info dict ≠ XMP producer | Medium |

## Origin Classification

### Classification Types

| Type | Indicators |
|------|------------|
| `scanned` | Scanner vendor (Xerox, Canon, Ricoh, etc.) or OCR software detected |
| `digital` | Office software (Word, Acrobat, etc.) detected |
| `unknown` | Insufficient metadata to classify |

### Clustering

PDFs are clustered by:
- Scanner signature (vendor)
- Software engine
- Compression patterns

## Scoring Model

### Formula

```
ForensicScore = (TimestampIntegrity × 0.25) +
                (ProducerConsistency × 0.20) +
                (XMPIntegrity × 0.20) +
                (OriginSignatureStability × 0.20) +
                (ACE_Linkage × 0.15)
```

### Components

| Component | Weight | Description |
|-----------|--------|-------------|
| TimestampIntegrity | 25% | Fewer temporal anomalies = higher score |
| ProducerConsistency | 20% | Consistent producer/creator metadata |
| XMPIntegrity | 20% | Present, well-formed XMP = higher score |
| OriginSignatureStability | 20% | Fewer retroactive edit indicators |
| ACE_Linkage | 15% | Fewer ACE-flagged anomalies for corpus |

### Score Interpretation

| Score Range | Interpretation |
|-------------|----------------|
| 90-100 | Excellent metadata integrity |
| 70-89 | Good integrity, minor issues |
| 50-69 | Moderate concerns, review recommended |
| 30-49 | Significant anomalies detected |
| 0-29 | Critical issues, forensic review needed |

## ACE/VICFM/CAIM Integration

### ACE Anomaly Links

DPMM cross-references forensic findings with ACE-flagged anomalies by:
- Matching `hist_id` between systems
- Correlating anomaly types (temporal ↔ chronological)
- Calculating overlap scores

### Vendor Overlaps

Links producer/creator forensics to vendor influence patterns:
- Matches vendor software patterns
- Cross-references with VICFM vendor index
- Flags vendor-linked PDFs with forensic issues

### Agency Patterns

Identifies agency-level forensic trends:
- Multi-year anomaly patterns
- Origin cluster distributions
- Departmental forensic profiles

## Usage

### Command Line

```bash
# Run full PDF forensics analysis
python scripts/pdf_forensics/pdf_metadata_miner.py --years 2014-2025

# Run with specific year range
python scripts/pdf_forensics/pdf_metadata_miner.py --years 2021-2025

# Run with ACE report integration
python scripts/pdf_forensics/pdf_metadata_miner.py --ace-report ACE_REPORT.json

# Custom output directory
python scripts/pdf_forensics/pdf_metadata_miner.py --output ./reports/pdf_forensics/
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--corpus-root` | `oraculus/corpus` | Root directory for corpus files |
| `--years` | `2014-2025` | Year range to analyze |
| `--output` | `analysis/pdf_forensics` | Output directory for reports |
| `--ace-report` | None | Path to ACE_REPORT.json for cross-linking |

## CI Integration

DPMM is integrated into the GitHub Actions pre-commit workflow:

```yaml
pdf-forensics:
  runs-on: ubuntu-latest
  needs: ace-analyzer
  steps:
    - name: Run PDF forensics tests
      run: python -m pytest tests/pdf_forensics/ -v --tb=short
      
    - name: Run PDF forensics analyzer
      run: python scripts/pdf_forensics/pdf_metadata_miner.py --years 2014-2025
```

## Test Coverage

The DPMM module includes 122 tests across 9 test files:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_metadata_parsing.py | 20 | Metadata extraction functions |
| test_date_normalization.py | 15 | PDF date format parsing |
| test_producer_validation.py | 10 | Producer/creator forensics |
| test_xmp_extraction.py | 14 | XMP metadata parsing and anomalies |
| test_scanned_classifier.py | 14 | Scanned vs digital classification |
| test_cluster_generation.py | 10 | Origin clustering |
| test_anomaly_scoring.py | 12 | Forensic scoring and temporal anomalies |
| test_ace_vicfm_crosslinks.py | 5 | Integration tests |
| test_malformed_recovery.py | 9 | Malformed PDF recovery |
| test_missing_xmp_handling.py | 9 | Missing XMP graceful handling |

## Determinism

DPMM produces deterministic output for identical inputs:
- SHA256 hashes are consistent for same file content
- Anomaly detection uses consistent thresholds
- Clustering produces reproducible groupings

## Future Enhancements

- Machine learning-based scanned vs digital classification
- Extended XMP schema detection (custom namespaces)
- PDF structure analysis (stream objects, compression)
- Interactive visualization dashboard
- Real-time monitoring for new documents
- Integration with external PDF/A validators

---

*DPMM v1.0 - Part of the Oraculus DI Auditor Project*  
*Generated: 2025-12-06*
