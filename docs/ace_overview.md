# ACE v1.0 - Anomaly Correlation Engine

## Overview

The **Anomaly Correlation Engine (ACE)** is a deterministic pipeline that cross-references anomalies, missing data patterns, metadata irregularities, and multi-year deviations across the finalized 11-year the target jurisdiction legislative corpus (2014–2025).

ACE correlates **structure → integrity → extraction → metadata → chronology** into a single unified anomaly model.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ACE v1.0 Pipeline                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │
│  │   INPUTS      │    │   ANALYSIS    │    │   OUTPUTS     │       │
│  ├───────────────┤    ├───────────────┤    ├───────────────┤       │
│  │ • ingestion   │    │ • Metadata    │    │ • ACE_REPORT  │       │
│  │   _report.json│ -> │   Outliers    │ -> │   .json       │       │
│  │ • VALIDATION  │    │ • Cross-Year  │    │ • ACE_SUMMARY │       │
│  │   _REPORT.json│    │   Drift       │    │   .md         │       │
│  │ • audit_ext   │    │ • Attachment  │    │ • ANOMALY_MAP │       │
│  │   _report.json│    │   Signatures  │    │   .csv        │       │
│  │ • missing     │    │ • Structural  │    │ • ace_network │       │
│  │   _items_log  │    │   Gaps        │    │   _graph.json │       │
│  │ • metadata/   │    │ • Extraction  │    │               │       │
│  │   *.json      │    │   Issues      │    │               │       │
│  └───────────────┘    └───────────────┘    └───────────────┘       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    SCORING ENGINE (1-5)                      │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ 1: Mild Irregularity                                         │   │
│  │ 2: Repeated Pattern                                          │   │
│  │ 3: Multi-Year Repeated Pattern                               │   │
│  │ 4: Structural or Chronological Anomaly                       │   │
│  │ 5: High-Risk (Cross-Category Correlation)                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Sources

### Input Files

| File | Location | Description |
|------|----------|-------------|
| `ingestion_report.json` | `oraculus/corpus/` | Full ingestion status and extraction results |
| `VALIDATION_REPORT.json` | Project root | Legacy validation report with corpus audit details |
| `audit_extension_report.json` | `oraculus/corpus/` | Extended audit for 2021-2025 corpus |
| `missing_items_log.json` | `oraculus/corpus/` | Comprehensive missing data tracking |
| `metadata/*.json` | `oraculus/corpus/{CORPUS_ID}/` | Per-corpus metadata files |
| `index.json` | `oraculus/corpus/{CORPUS_ID}/` | Per-corpus index with file listings |

### Output Files

| File | Description |
|------|-------------|
| `ACE_REPORT.json` | Complete JSON report with all anomalies, scores, and correlations |
| `ACE_SUMMARY.md` | Human-readable markdown summary of key findings |
| `ANOMALY_MAP.csv` | Tabular, flattened view for spreadsheet analysis |
| `ace_network_graph.json` | Graph structure for database ingestion (nodes and edges) |

## Anomaly Categories

### 1. Chronological Drift

Detects temporal inconsistencies in the corpus:

- **Meeting date mismatches** across agenda/minutes/metadata
- **Time-gap irregularities** inside the same legislative chain
- **Duplicate dates** where multiple corpora share the same meeting date
- **Large gaps** (>180 days) within a single calendar year

### 2. Extraction Inconsistencies

Identifies PDF text extraction problems:

- **Extraction failures** clustered around specific patterns
- **Low extraction rates** across multiple corpora
- **Missing extracted text** for PDFs with expected content

### 3. Attachment Signature Deviations

Tracks surveillance-related patterns (2021-2025 focus):

- **ALPR** (Automated License Plate Reader) references
- **Axon** body camera mentions
- **Flock** surveillance system references
- **Other surveillance** keywords (biometric, tracking, etc.)

### 4. Structural Gaps

Monitors missing document patterns:

- **Missing agendas** by quarter
- **Missing minutes** by quarter
- **Missing staff reports** patterns
- **Empty category directories**

### 5. Schema Irregularities

Validates metadata quality:

- **Missing required fields** (meeting_date, source_url, file_hash, corpus_id)
- **Malformed dates** (not in YYYY-MM-DD format)
- **Placeholder URLs** (NEEDS_USER_INPUT or empty)
- **Invalid metadata format** (non-dict structures)

### 6. High-Risk Flags

Flags critical issues requiring attention:

- **Cross-category correlation** - anomaly type repeated ≥3 times across different years
- **Multi-year patterns** - same issue persisting across the corpus timeline
- **Critical severity** assignments from any category

## Scoring Logic

ACE assigns scores from 1-5 based on severity and pattern analysis:

| Score | Meaning | Triggers |
|-------|---------|----------|
| 1 | Mild irregularity | Low severity, single occurrence |
| 2 | Repeated pattern | Medium severity, or 3+ occurrences |
| 3 | Multi-year repeated pattern | Pattern across 3+ years |
| 4 | Structural or chronological anomaly | High severity, large time gaps |
| 5 | High-risk (cross-category correlation) | Critical severity, `high_risk_flag` type |

### Scoring Algorithm

```python
def score_anomaly(anomaly):
    # Base score from severity
    if severity == "critical": base_score = 5
    elif severity == "high": base_score = 4
    elif severity == "medium": base_score = 2
    else: base_score = 1
    
    # Override for high-risk flags
    if type == "high_risk_flag": return 5
    
    # Elevate for multi-year patterns
    if years_affected >= 3: return max(base_score, 3)
    
    # Elevate for repeated occurrences
    if occurrences >= 3: return max(base_score, 2)
    
    return base_score
```

## Cross-Year Anomaly Detection

The engine specifically looks for patterns that span multiple years:

1. **Temporal Analysis**: Groups anomalies by year of occurrence
2. **Pattern Detection**: Identifies the same anomaly type across different years
3. **Threshold Check**: Flags as high-risk if pattern appears in 3+ years
4. **Correlation**: Links related corpora that share anomaly patterns

### Example: Multi-Year Structural Gap

```json
{
  "type": "high_risk_flag",
  "subtype": "multi_year_pattern",
  "pattern_type": "structural_gap",
  "years_affected": ["2014", "2015", "2016", "2017", "2018"],
  "total_occurrences": 47,
  "details": "Anomaly type 'structural_gap' repeated across 5 years (47 total)",
  "severity": "critical"
}
```

## Usage

### Command Line

```bash
# Run ACE analyzer on full corpus
python scripts/ace_analyzer.py --years 2014-2025

# Run on specific year range
python scripts/ace_analyzer.py --years 2021-2025

# Output to specific directory
python scripts/ace_analyzer.py --output ./reports/

# Fail CI on high-risk anomalies
python scripts/ace_analyzer.py --fail-on-high-risk
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--corpus-root` | `oraculus/corpus` | Root directory for corpus files |
| `--years` | `2014-2025` | Year range to analyze |
| `--output` | Current directory | Output directory for reports |
| `--fail-on-high-risk` | False | Exit with error if score 5 anomalies detected |
| `--json-only` | False | Minimal console output |

## Output File Glossary

### ACE_REPORT.json

The primary output containing:

```json
{
  "report_id": "16-char hex identifier",
  "generated_at": "ISO timestamp",
  "ace_version": "1.0",
  "schema_version": "1.0",
  "year_range": "2014-2025",
  "summary": {
    "total_anomalies": 33,
    "unique_corpora_affected": 37,
    "average_score": 1.76,
    "high_risk_count": 1,
    "score_distribution": {"1": 20, "2": 10, "5": 1}
  },
  "high_risk_alerts": [...],
  "by_category": {...},
  "by_hist_id": {...},
  "all_anomalies": [...],
  "scoring_model": {...}
}
```

### ACE_SUMMARY.md

Human-readable summary including:

- Executive summary with key metrics
- Score distribution table
- Anomalies grouped by category
- High-risk alert highlights

### ANOMALY_MAP.csv

Flat CSV with columns:

| Column | Description |
|--------|-------------|
| `hist_id` | Corpus identifier |
| `type` | Anomaly category |
| `subtype` | Specific anomaly type |
| `ace_score` | Score 1-5 |
| `severity` | low/medium/high/critical |
| `year` | Year affected |
| `details` | Description (truncated to 200 chars) |

### ace_network_graph.json

Graph structure for visualization and database ingestion:

```json
{
  "nodes": [
    {"id": "HIST-6225", "type": "corpus", "anomaly_count": 3},
    {"id": "structural_gap", "type": "anomaly_type", "count": 47}
  ],
  "edges": [
    {"source": "HIST-6225", "target": "structural_gap", "type": "has_anomaly"},
    {"source": "HIST-6225", "target": "HIST-7722", "type": "shares_anomaly_type"}
  ],
  "statistics": {
    "total_nodes": 50,
    "total_edges": 120,
    "corpus_nodes": 36,
    "anomaly_type_nodes": 6
  }
}
```

## CI Integration

ACE is integrated into the GitHub Actions pre-commit workflow:

```yaml
- name: Run ACE analyzer
  run: python scripts/ace_analyzer.py --years 2014-2025
  
- name: Check for high-risk anomalies
  run: python scripts/ace_analyzer.py --fail-on-high-risk
```

The CI will fail if any score 5 anomalies are detected when `--fail-on-high-risk` is used.

## Determinism

ACE produces deterministic output for identical inputs:

- Report ID is derived from timestamp hash
- Anomalies are sorted by score (descending)
- All JSON outputs use consistent key ordering
- CSV rows maintain consistent column order

## Vendor Layer Integration (VICFM)

ACE integrates with the **Vendor Influence & Contract Flow Map (VICFM)** to provide vendor-aware anomaly analysis.

### Vendor Layer Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACE + VICFM Integration                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ACE Anomalies              VICFM Vendors                      │
│   ─────────────              ─────────────                      │
│   • Structural gaps          • Vendor index                     │
│   • Metadata issues    ──>   • Influence scores                 │
│   • Chronological drift      • Procurement flags                │
│                                                                 │
│                    ↓                                            │
│   ┌─────────────────────────────────────────────┐              │
│   │         VENDOR_ANOMALY_LINKS.json           │              │
│   │         VENDOR_TECH_DEPENDENCIES.json       │              │
│   └─────────────────────────────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Vendor Influence Scoring with ACE

VICFM incorporates ACE anomalies into vendor influence scoring:

```
Influence Score = (Frequency × 0.25) + (Value × 0.25) 
                + (ACE_Anomaly_Intersection × 0.20)
                + (Centrality × 0.15) + (Continuity × 0.15)
```

**ACE Anomaly Intersection**: Vendors appearing in corpus items with ACE-flagged anomalies receive a weighted contribution to their influence score.

### Cross-Link Anomalies

ACE generates cross-link anomalies when:

1. **Vendor in High-Risk Corpus**: A vendor appears in a corpus with ACE score ≥4
2. **Multi-Year Vendor + Anomaly Pattern**: Same vendor across years with recurring anomaly types
3. **Procurement + Structural Flags**: Sole-source procurement in anomaly-flagged documents

### Output Files

| File | Description |
|------|-------------|
| `VENDOR_ANOMALY_LINKS.json` | Maps vendors to their associated ACE anomalies |
| `VENDOR_TECH_DEPENDENCIES.json` | Technology program dependencies with anomaly flags |

See [Vendor Mapping Overview](vendor_mapping_overview.md) for complete VICFM documentation.

## Cross-Agency Influence Map (CAIM) Integration

ACE integrates with the **Cross-Agency Influence Map (CAIM)** to provide agency-level anomaly correlation.

### CAIM Integration Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACE + CAIM Integration                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ACE Anomalies              CAIM Agencies                      │
│   ─────────────              ─────────────                      │
│   • Structural gaps          • Agency index                     │
│   • Metadata issues    ──>   • Influence scores                 │
│   • Chronological drift      • Correlation matrix               │
│                                                                 │
│                    ↓                                            │
│   ┌─────────────────────────────────────────────┐              │
│   │      ICM Score Component (20% weight)       │              │
│   │      ACE Anomaly Linkage                    │              │
│   └─────────────────────────────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ACE Anomaly Linkage Scoring

ACE anomalies contribute to the ICM score with a 20% weight:

```
ICM Score = (VendorOverlap × 0.25) + (TechStack × 0.20)
          + (ContractFlowSync × 0.20) + (ACE_Anomaly_Linkage × 0.20)
          + (ProgrammaticContinuity × 0.15)
```

Agencies sharing anomaly patterns receive higher correlation scores, indicating:
- Shared data quality issues
- Coordinated procurement patterns
- Common structural gaps

### Output Integration

| File | Description |
|------|-------------|
| `icm_matrix.json` | Includes ACE anomaly linkage scores |
| `agency_graph.json` | Edge weights incorporate ACE correlations |
| `AGENCY_INFLUENCE_REPORT.md` | References ACE-flagged patterns |

See [CAIM Overview](caim_overview.md) for complete CAIM-ICM documentation.

## PDF Forensics Integration (DPMM)

ACE integrates with the **Deep Packet Metadata Miner (DPMM)** to provide PDF-level forensic metadata analysis.

### DPMM Integration Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACE + DPMM Integration                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ACE Anomalies              DPMM Forensics                     │
│   ─────────────              ──────────────                     │
│   • Structural gaps          • PDF metadata                     │
│   • Metadata issues    ──>   • Temporal anomalies               │
│   • Chronological drift      • Producer forensics               │
│                                                                 │
│                    ↓                                            │
│   ┌─────────────────────────────────────────────┐              │
│   │     FORENSIC_ANOMALY_LINKS.json             │              │
│   │     Cross-correlated anomalies              │              │
│   └─────────────────────────────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ACE-DPMM Cross-Linking

DPMM uses ACE anomaly counts in its scoring model:

```
ForensicScore = (TimestampIntegrity × 0.25) +
                (ProducerConsistency × 0.20) +
                (XMPIntegrity × 0.20) +
                (OriginSignatureStability × 0.20) +
                (ACE_Linkage × 0.15)  ← ACE integration
```

See [PDF Forensics Overview](pdf_forensics_overview.md) for complete DPMM documentation.

## Future Enhancements

- Graph database integration for relationship queries
- Machine learning-based anomaly classification
- Real-time monitoring for new corpus entries
- Interactive visualization dashboard
- Enhanced CAIM-ACE cross-correlation analysis
- Extended PDF forensics integration

---

*ACE v1.0 - Part of the Oraculus DI Auditor Project*  
*Generated: 2025-12-06*
