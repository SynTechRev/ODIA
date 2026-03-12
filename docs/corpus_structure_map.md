# Corpus Structure Map

## Overview

This document describes the 11-year legislative corpus architecture for the the target jurisdiction (2014-2025). The corpus is organized chronologically with consistent directory structures for ingestion, metadata management, and audit pipelines.

## Directory Structure

```
oraculus/corpus/
├── index.json                    # Global corpus index
├── ingestion_report.json         # Full ingestion status
├── audit_extension_report.json   # Extended audit (2021-2025)
├── missing_items_log.json        # Missing data tracking
├── README.md                     # Corpus documentation
│
├── HIST-6225/                    # 2014-06-02 (First entry)
├── HIST-7722/                    # 2015-01-20
├── HIST-8213/                    # 2015-06-15
├── HIST-9493/                    # 2016-07-18
├── HIST-11153/                   # 2017-09-18
├── HIST-11740/                   # 2017-11-06 (Recovered corpus)
├── HIST-11877/                   # 2017-12-04
├── HIST-11887/                   # 2017-12-18
├── HIST-12077/                   # 2018-03-19
├── HIST-12223/                   # 2018-06-18
├── HIST-13175/                   # 2018-12-17
├── HIST-13397/                   # 2019-03-04
├── HIST-13594/                   # 2019-05-06
├── HIST-13848/                   # 2019-10-07
├── HIST-14845/                   # 2019-12-16
├── HIST-14973/                   # 2020-03-16
├── HIST-15517/                   # 2020-09-21
│
├── #21-0443/                     # 2021-08-02 (Modern format begins)
├── #21-0588/                     # 2021-10-29
├── #22-0012/                     # 2022-01-05
├── #22-0080/                     # 2022-02-24
├── #22-0463/                     # 2022-12-13
├── #23-0148/                     # 2023-04-14
├── #23-0214/                     # 2023-05-16
├── #24-0034/                     # 2024-01-30
├── #24-0039/                     # 2024-01-31
├── #24-0163/                     # 2024-04-22
├── #24-0403/                     # 2024-09-20
├── #24-0410/                     # 2024-09-23
├── #24-0415/                     # 2024-09-24
├── #24-0477/                     # 2024-10-30
├── #24-0559/                     # 2024-12-16
├── #25-0171/                     # 2025-04-30
├── #25-0202/                     # 2025-05-20
├── #25-0203/                     # 2025-05-20
└── #25-0333/                     # 2025-07-23 (Latest entry)
```

## Corpus Entry Structure

Each corpus entry follows this structure:

```
{CORPUS_ID}/
├── index.json              # Corpus metadata and file index
├── agendas/               # Agenda documents
│   ├── *.pdf
│   └── .gitkeep
├── minutes/               # Meeting minutes
│   ├── *.pdf
│   └── .gitkeep
├── staff_reports/         # Staff reports and recommendations
│   ├── *.pdf
│   └── .gitkeep
├── attachments/           # Supporting documents
│   ├── *.pdf
│   └── .gitkeep
├── extracted/             # Extracted text content
│   ├── *.txt
│   └── .gitkeep
└── metadata/              # Per-file metadata JSON
    ├── *.json
    └── .gitkeep
```

## Year-by-Year Summary

| Year | Corpora Count | ID Format | Notes |
|------|--------------|-----------|-------|
| 2014 | 1 | HIST-XXXXX | First corpus entry |
| 2015 | 2 | HIST-XXXXX | |
| 2016 | 1 | HIST-XXXXX | |
| 2017 | 4 | HIST-XXXXX | Includes recovered corpus HIST-11740 |
| 2018 | 3 | HIST-XXXXX | |
| 2019 | 4 | HIST-XXXXX | |
| 2020 | 2 | HIST-XXXXX | |
| 2021 | 2 | #YY-XXXX | Format transition begins |
| 2022 | 3 | #YY-XXXX | |
| 2023 | 2 | #YY-XXXX | |
| 2024 | 8 | #YY-XXXX | Highest annual count |
| 2025 | 4 | #YY-XXXX | Projected through July |
| **Total** | **36** | | 11-year span |

## Naming Conventions

### Historic Format (2014-2020)
- Pattern: `HIST-{5-digit ID}`
- Example: `HIST-6225`, `HIST-15517`
- Source: Legacy Legistar system IDs

### Modern Format (2021-2025)
- Pattern: `#{YY}-{4-digit ID}`
- Example: `#21-0443`, `#25-0333`
- Source: Current Legistar legislation numbers

## Document Categories

1. **Agendas** (`agendas/`)
   - Meeting agendas with item numbers
   - Published before meetings

2. **Minutes** (`minutes/`)
   - Official meeting minutes
   - Approved after meetings

3. **Staff Reports** (`staff_reports/`)
   - Staff analysis and recommendations
   - Supporting justifications

4. **Attachments** (`attachments/`)
   - Contracts, resolutions, exhibits
   - Supporting documentation

5. **Agenda Item Transmittals**
   - Tracked separately in missing_items_log.json
   - Internal routing documents

6. **Agenda Packets**
   - Complete meeting packages
   - May be consolidated PDFs

## Metadata Schema

### Corpus-Level (`index.json`)

```json
{
  "corpus_id": "HIST-6225",
  "file_id": "HIST-6225",
  "meeting_date": "2014-06-02",
  "meeting_type": "City Council Regular Meeting",
  "jurisdiction": "the target jurisdiction",
  "source_url": "https://example.legistar.com/...",
  "ingest_version": "2.1",
  "ingestion_timestamp": "2025-12-05T06:30:00.000Z",
  "provenance_flags": {
    "manual_date_entry": true,
    "manual_source_entry": true,
    "extended_ingest": true,
    "recovered_corpus": false
  },
  "category_flags": {
    "has_agendas": true,
    "has_minutes": true,
    "has_staff_reports": false,
    "has_attachments": false
  },
  "statistics": {
    "total_files": 2,
    "by_type": {
      "agenda": 1,
      "minutes": 1
    }
  }
}
```

### Per-File (`metadata/*.json`)

```json
{
  "file_name": "Agenda-2014-06-02.pdf",
  "file_type": "agenda",
  "meeting_date": "2014-06-02",
  "meeting_type": "City Council Regular Meeting",
  "jurisdiction": "the target jurisdiction",
  "source_url": "https://example.legistar.com/...",
  "file_hash": "sha256:...",
  "text_hash": "sha256:...",
  "document_titles": [],
  "document_urls": {},
  "ingest_version": "2.1",
  "provenance_flags": {
    "manual_date_entry": true,
    "manual_source_entry": true,
    "extended_ingest": true
  }
}
```

## Ingestion Pipeline

### Scripts

1. **Full Ingestion** (`scripts/full_ingestion.py`)
   - Complete corpus validation and metadata generation
   - Text extraction from PDFs
   - Global index building
   - Usage: `python scripts/full_ingestion.py --corpus-root oraculus/corpus`

2. **Extended Ingestion** (`scripts/ingest_hist8123.py`)
   - Year-aware ingestion for 2021-2025 extension
   - Directory scaffolding
   - Usage: `python scripts/ingest_hist8123.py --years 2021-2025`

3. **Corpus Audit** (`scripts/audit_hist8123.py`)
   - Year-aware corpus auditing
   - Missing data flagging
   - Usage: `python scripts/audit_hist8123.py --years 2014-2025`

4. **Unified Audit** (`scripts/audit_corpora.py`)
   - Legacy audit script
   - Generates VALIDATION_REPORT.json

### Reports

1. **ingestion_report.json** - Full ingestion status
2. **audit_extension_report.json** - Extended audit results
3. **missing_items_log.json** - Missing data tracking
4. **VALIDATION_REPORT.json** - Legacy validation report

## Source URLs

All corpus entries have source URLs to the the configured jurisdiction Legistar system:
- Base URL: `https://example.legistar.com/LegislationDetail.aspx`
- Parameters include legislation ID, GUID, and search context

## Missing Data Categories

The `missing_items_log.json` tracks:

1. **Missing Directories** - Corpus folders not yet created
2. **Missing Agendas** - Corpora without agenda documents
3. **Missing Minutes** - Corpora without minutes documents
4. **Missing Staff Reports** - Corpora without staff reports
5. **Missing Attachments** - Corpora without attachments
6. **Missing Agenda Item Transmittals** - Internal routing docs
7. **Missing Agenda Packets** - Complete meeting packages
8. **Incomplete Metadata** - Files with missing metadata fields
9. **Low Extraction Rate** - PDFs with failed text extraction

## Provenance Flags

- `manual_date_entry` - Date was manually verified
- `manual_source_entry` - Source URL was manually verified
- `extended_ingest` - Processed by extended ingestion (2021-2025)
- `recovered_corpus` - Special flag for HIST-11740 (recovered data)

## Validation Requirements

1. All corpus entries must have valid `index.json`
2. All PDF files must have corresponding metadata JSON
3. Text extraction should complete for all PDFs
4. Source URLs should be verified and accessible
5. Meeting dates must follow YYYY-MM-DD format
6. File hashes must be consistent between runs

## ACE Integration Layer

The **Anomaly Correlation Engine (ACE)** is integrated into the corpus architecture to provide automated anomaly detection and pattern analysis.

### ACE Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        ACE v1.0                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Corpus Data         →    Analysis         →    Reports       │
│   ─────────────            ──────────            ────────       │
│   • index.json             • Metadata           • ACE_REPORT   │
│   • metadata/              • Cross-Year         • ACE_SUMMARY  │
│   • Reports                • Structural         • ANOMALY_MAP  │
│                            • Extraction         • Network Graph│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion** → `ingestion_report.json`
2. **Validation** → `VALIDATION_REPORT.json`
3. **Audit** → `audit_extension_report.json`, `missing_items_log.json`
4. **ACE Analysis** → `ACE_REPORT.json`, `ACE_SUMMARY.md`, `ANOMALY_MAP.csv`

### Anomaly Categories

| Category | Description |
|----------|-------------|
| Chronological Drift | Date mismatches, time-gap irregularities |
| Extraction Inconsistencies | PDF extraction failures |
| Attachment Signatures | Surveillance vendor patterns (2021-2025) |
| Structural Gaps | Missing agenda/minutes patterns |
| Schema Irregularities | Metadata field issues |
| High-Risk Flags | Cross-category correlations |

### ACE Scoring Model

| Score | Meaning |
|-------|---------|
| 1 | Mild irregularity |
| 2 | Repeated pattern |
| 3 | Multi-year repeated pattern |
| 4 | Structural or chronological anomaly |
| 5 | High-risk (cross-category correlation) |

### Running ACE

```bash
# Full corpus analysis
python scripts/ace_analyzer.py --years 2014-2025

# CI integration with failure on high-risk
python scripts/ace_analyzer.py --fail-on-high-risk
```

See [ACE Overview](ace_overview.md) for detailed documentation.

## Vendor Influence & Contract Flow Map (VICFM)

The **Vendor Influence & Contract Flow Map (VICFM)** provides vendor-level analysis integrated with the corpus structure.

### VICFM Generated Artifacts

| File | Description |
|------|-------------|
| `vendor_graph.json` | Graph model with vendor-corpus-year nodes and edges |
| `vendor_scores.json` | Ranked vendors with influence scores and tiers |
| `vendor_influence_network.csv` | Flat edge list for spreadsheet analysis |
| `CONTRACT_FLOW_MAP.json` | Year-by-year vendor activity timeline |
| `CONTRACT_FLOW_MAP.md` | Human-readable contract flow report |
| `PROCUREMENT_FLAGS.json` | Detected procurement irregularities |
| `VENDOR_ANOMALY_LINKS.json` | Vendor-ACE anomaly correlations |
| `VENDOR_TECH_DEPENDENCIES.json` | Technology program dependencies |

### VICFM Scripts

| Script | Description |
|--------|-------------|
| `vendor_map_extractor.py` | Extract vendors from corpus data |
| `vendor_graph_builder.py` | Build vendor influence graph |
| `contract_flow_map.py` | Generate contract flow timeline |

### Running VICFM

```bash
# Extract vendors from corpus
python scripts/vendor_map_extractor.py --corpus-root oraculus/corpus --years 2014-2025

# Build vendor graph (requires vendor extraction first)
python scripts/vendor_graph_builder.py --vendor-data vendor_index.json --output .

# Generate contract flow map
python scripts/contract_flow_map.py --vendor-data vendor_index.json --output .
```

See [Vendor Mapping Overview](vendor_mapping_overview.md) for detailed documentation.

## Cross-Agency Influence Map (CAIM)

The **Cross-Agency Influence Map (CAIM)** and **Interdepartmental Correlation Matrix (ICM)** provide agency-level analysis integrated with the corpus structure.

### CAIM Generated Artifacts

| File | Description |
|------|-------------|
| `agency_graph.json` | Graph model with agency-corpus-year nodes and edges |
| `cross_agency_edges.csv` | Agency relationship edge list |
| `influence_matrix.csv` | Full correlation matrix between agencies |
| `agency_correlation_heatmap.png` | Visual heatmap of agency correlations |
| `AGENCY_INFLUENCE_REPORT.md` | Human-readable agency analysis |
| `ICM_EXPLANATION.md` | Scoring methodology explanation |

### CAIM Scripts

| Script | Description |
|--------|-------------|
| `agency_map_extractor.py` | Extract agencies from corpus data |
| `cross_agency_influence.py` | Build CAIM graph |
| `interdepartmental_matrix.py` | Generate ICM correlation matrix |
| `generate_caim_reports.py` | Complete CAIM-ICM pipeline |

### Running CAIM

```bash
# Run complete CAIM-ICM pipeline
python scripts/generate_caim_reports.py --years 2014-2025 --output .

# Or run individual steps
python scripts/agency_map_extractor.py --corpus-root oraculus/corpus --output .
python scripts/cross_agency_influence.py --agency-data agency_index.json --output .
python scripts/interdepartmental_matrix.py --agency-data agency_index.json --output .
```

See [CAIM Overview](caim_overview.md) for detailed documentation.

## PDF Forensics Layer (DPMM)

### Output Files

| File | Description |
|------|-------------|
| `analysis/pdf_forensics/forensic_report.json` | Complete forensic metadata analysis |
| `analysis/pdf_forensics/metadata_inconsistency_map.json` | Detected inconsistencies by year |
| `analysis/pdf_forensics/pdf_origin_clusters.json` | Origin clustering results |
| `analysis/pdf_forensics/pdf_forensics_graph.json` | Graph for visualization |
| `analysis/pdf_forensics/DPMM_SUMMARY.md` | Executive summary |
| `analysis/pdf_forensics/FORENSIC_ANOMALY_LINKS.json` | ACE cross-links |
| `analysis/pdf_forensics/FORENSIC_VENDOR_OVERLAPS.json` | Vendor cross-links |
| `analysis/pdf_forensics/FORENSIC_AGENCY_PATTERNS.json` | Agency patterns |

### DPMM Scripts

| Script | Description |
|--------|-------------|
| `pdf_forensics/pdf_metadata_miner.py` | Extract and analyze PDF metadata |
| `pdf_forensics/forensic_integration.py` | ACE/VICFM/CAIM integration |

### Running DPMM

```bash
# Run complete PDF forensics pipeline
python scripts/pdf_forensics/pdf_metadata_miner.py --years 2014-2025

# With ACE integration
python scripts/pdf_forensics/pdf_metadata_miner.py --ace-report ACE_REPORT.json

# Run integration reports
python scripts/pdf_forensics/forensic_integration.py \
  --forensic-report analysis/pdf_forensics/forensic_report.json \
  --ace-report ACE_REPORT.json
```

See [PDF Forensics Overview](pdf_forensics_overview.md) for detailed documentation.

---

*Generated: 2025-12-06*
*Schema Version: 2.3*
*Corpus Span: 2014-2025 (11 years, 36 corpora)*
