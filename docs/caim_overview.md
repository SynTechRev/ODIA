# Cross-Agency Influence Map & Interdepartmental Correlation Matrix (CAIM-ICM) v1.0

## Overview

The **Cross-Agency Influence Map (CAIM)** and **Interdepartmental Correlation Matrix (ICM)** form an analytic layer that maps relationships, overlaps, co-dependencies, and coordinated patterns across all departments, agencies, divisions, programs, and legislative hubs represented in the 2014–2025 corpus.

This layer integrates with:
- **ACE v1.0** (Anomaly Correlation Engine)
- **VICFM v1.0** (Vendor Influence & Contract Flow Map)
- **Corpus Metadata v2.1**

## Architecture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                        CAIM-ICM v1.0 Pipeline                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐              │
│  │ EXTRACTION     │    │ CAIM GRAPH     │    │ ICM MATRIX     │              │
│  ├────────────────┤    ├────────────────┤    ├────────────────┤              │
│  │ • Metadata     │    │ • Agency nodes │    │ • Correlation  │              │
│  │ • Filenames    │ -> │ • Relationship │ -> │   matrix       │              │
│  │ • Staff reports│    │   edges        │    │ • Influence    │              │
│  │ • Grant docs   │    │ • Influence    │    │   scores       │              │
│  │ • Contracts    │    │   weights      │    │ • Tier ranking │              │
│  └────────────────┘    └────────────────┘    └────────────────┘              │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    SCORING ENGINE                                        │ │
│  ├─────────────────────────────────────────────────────────────────────────┤ │
│  │ Score = (VendorOverlap × 0.25) + (TechStack × 0.20)                     │ │
│  │       + (ContractFlowSync × 0.20) + (ACE_Anomaly_Linkage × 0.20)        │ │
│  │       + (ProgrammaticContinuity × 0.15)                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Agency Map Extractor (`agency_map_extractor.py`)

Extracts agency information from multiple sources:

| Source | Description |
|--------|-------------|
| Metadata fields | Direct agency/department/jurisdiction fields |
| Document titles | Agency mentions in document titles |
| Filenames | Agency patterns in attachment filenames |
| Extracted text | Agency mentions in PDF text content |

#### Key Functions

- `detect_agency_in_text()` - Pattern-based agency detection
- `extract_agencies_from_metadata()` - Metadata field extraction
- `extract_agencies_from_filenames()` - Filename pattern extraction
- `build_agency_index()` - Comprehensive agency mapping
- `extract_agency_relationships()` - Co-occurrence detection

### 2. Cross-Agency Influence Engine (`cross_agency_influence.py`)

Builds a graph model of agency relationships:

#### Node Types

| Type | Description |
|------|-------------|
| `agency` | A department, agency, or program |
| `vendor` | A vendor/contractor entity |
| `corpus` | A legislative corpus item |
| `year` | A calendar year |

#### Edge Types

| Type | Description |
|------|-------------|
| `mentioned_in` | Agency appears in a corpus |
| `active_in` | Agency active in a year |
| `interacts_with` | Agency-agency relationship (weighted) |
| `shares_vendor` | Agency shares vendor with another |
| `occurred_in` | Corpus occurred in a year |

### 3. Interdepartmental Matrix (`interdepartmental_matrix.py`)

Creates a correlation matrix between all agencies:

- **Symmetric matrix**: Score(A,B) = Score(B,A)
- **Self-correlation**: Diagonal values are 1.0
- **Bounded scores**: All values between 0.0 and 1.0

## Scoring System

### Influence Score Formula

```
Score = (VendorOverlap × 0.25)
      + (TechStack × 0.20)
      + (ContractFlowSync × 0.20)
      + (ACE_Anomaly_Linkage × 0.20)
      + (ProgrammaticContinuity × 0.15)
```

### Component Weights

| Component | Weight | Description |
|-----------|--------|-------------|
| Vendor Overlap | 25% | Shared vendors (Jaccard similarity) |
| Tech Stack | 20% | Similar technology deployments |
| Contract Flow Sync | 20% | Temporal alignment of activities |
| ACE Anomaly Linkage | 20% | Shared anomaly patterns |
| Programmatic Continuity | 15% | Co-occurrence in corpus items |

### Correlation Tiers

| Score Range | Tier | Interpretation |
|-------------|------|----------------|
| ≥ 0.80 | Critical | Highly interdependent, strong formal ties |
| 0.60 - 0.79 | High | Significant relationship, shared resources |
| 0.40 - 0.59 | Moderate | Notable interaction, some shared vendors |
| 0.20 - 0.39 | Low | Occasional interaction, limited overlap |
| < 0.20 | Minimal | Little to no detected relationship |

## Integration with ACE & VICFM

### ACE Integration

- **Anomaly weights**: ACE anomalies weight agency-agency edges
- **Shared patterns**: Agencies appearing in anomaly-flagged documents
- **Risk correlation**: High-risk agencies identified by anomaly clusters

### VICFM Integration

- **Vendor influence**: Vendor scores propagate to agency metrics
- **Contract flow**: Procurement timing affects correlation scores
- **Technology programs**: Shared tech deployments increase similarity

## Output Files

### Primary Outputs

| File | Format | Description |
|------|--------|-------------|
| `agency_graph.json` | JSON | Complete graph model with nodes and edges |
| `cross_agency_edges.csv` | CSV | Flat edge list for spreadsheet analysis |
| `influence_matrix.csv` | CSV | Full correlation matrix |
| `agency_correlation_heatmap.png` | PNG | Visual heatmap of correlations |

### Report Outputs

| File | Format | Description |
|------|--------|-------------|
| `AGENCY_INFLUENCE_REPORT.md` | Markdown | Top agencies with analysis |
| `ICM_EXPLANATION.md` | Markdown | Scoring methodology explanation |
| `icm_matrix.json` | JSON | Detailed scores and metadata |

## Usage

### Command Line

```bash
# Run complete CAIM-ICM pipeline
python scripts/generate_caim_reports.py --years 2014-2025 --output ./reports

# Run individual components
python scripts/agency_map_extractor.py --corpus-root oraculus/corpus --output .
python scripts/cross_agency_influence.py --agency-data agency_index.json --output .
python scripts/interdepartmental_matrix.py --agency-data agency_index.json --output .
```

### Programmatic Usage

```python
from scripts.agency_map_extractor import run_agency_extraction
from scripts.cross_agency_influence import run_cross_agency_influence
from scripts.interdepartmental_matrix import run_icm_generation
from pathlib import Path

# Step 1: Extract agencies
agency_data = run_agency_extraction(
    corpus_root=Path("oraculus/corpus"),
    year_range="2014-2025",
    output_dir=Path(".")
)

# Step 2: Build CAIM graph
caim_result = run_cross_agency_influence(
    agency_data=agency_data,
    year_range="2014-2025",
    output_dir=Path(".")
)

# Step 3: Generate ICM matrix
icm_result = run_icm_generation(
    agency_data=agency_data,
    year_range="2014-2025",
    output_dir=Path(".")
)
```

## Known Agencies

### Municipal Departments

- City Council
- City Manager
- Finance Department
- Police Department
- Fire Department
- Public Works
- Parks & Recreation
- Community Development
- Human Resources
- Information Technology
- Legal/City Attorney
- Utilities

### County/Regional

- Tulare County
- Tulare County Sheriff

### State Agencies

- State of California
- CalTrans
- DMV
- CalOES

### Federal Agencies

- Department of Justice
- DOT (Department of Transportation)
- HUD
- FEMA
- EPA

### Grant Programs

- JAG Program (Justice Assistance Grant)
- COPS Program
- CDBG Program

## Risk Indicators

### High Correlation Indicators

1. **Procurement Clustering**: Multiple agencies with same vendors
2. **Technology Convergence**: Shared surveillance/IT systems
3. **Budget Synchronization**: Aligned fiscal year activities
4. **Anomaly Propagation**: Shared data quality issues

### Monitoring Thresholds

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| Vendor Overlap | > 0.5 | Review procurement coordination |
| Tech Stack Similarity | > 0.6 | Assess technology dependencies |
| ACE Anomaly Linkage | > 0.3 | Investigate shared issues |
| Correlation Score | > 0.8 | Flag for detailed review |

## Examples of Detected Patterns

### Cross-Agency Vendor Sharing

```
Police Department ↔ Fire Department
- Shared vendors: Axon, Motorola
- Vendor overlap: 0.67
- Tech stack similarity: 0.50
- Correlation: High tier
```

### Grant Program Coordination

```
JAG Program ↔ Police Department
- Co-occurrence: 12 corpus items
- Years active: 2019-2024
- Programmatic continuity: 0.85
- Correlation: Critical tier
```

## CI Integration

CAIM-ICM is integrated into the GitHub Actions workflow:

```yaml
caim-analyzer:
  runs-on: ubuntu-latest
  needs: [ace-analyzer, vendor-map]
  steps:
    - name: Run CAIM tests
      run: python -m pytest tests/caim/ -v
    
    - name: Run agency extraction
      run: python scripts/agency_map_extractor.py
    
    - name: Run CAIM graph builder
      run: python scripts/cross_agency_influence.py
    
    - name: Run ICM matrix generator
      run: python scripts/interdepartmental_matrix.py
```

## Test Coverage

| Test File | Test Count | Description |
|-----------|------------|-------------|
| `test_agency_extraction.py` | 30 | Agency detection and indexing |
| `test_caim_graph.py` | 31 | Graph building and weights |
| `test_icm_matrix.py` | 34 | Matrix generation and statistics |
| `test_caim_ace_integration.py` | 11 | ACE anomaly integration |
| `test_reports_generation.py` | 24 | Report formatting |
| **Total** | **130** | Verified by pytest |

## PDF Forensics Integration (DPMM)

CAIM integrates with the **Deep Packet Metadata Miner (DPMM)** to identify agency-level forensic patterns.

### Forensic Agency Patterns

DPMM generates `FORENSIC_AGENCY_PATTERNS.json` which:
- Groups forensic anomalies by origin cluster (scanner signature, software engine)
- Identifies multi-year anomaly patterns across agencies
- Correlates PDF producer patterns with agency technology profiles

### DPMM-CAIM Cross-Correlation

```python
# Example: Finding agencies with forensic anomalies
from scripts.pdf_forensics.forensic_integration import generate_forensic_agency_patterns

patterns = generate_forensic_agency_patterns(forensic_report, agency_report)
multi_year = [p for p in patterns['patterns'] if p['type'] == 'multi_year_pattern']
```

See [PDF Forensics Overview](pdf_forensics_overview.md) for complete DPMM documentation.

---

*CAIM-ICM v1.0 - Part of the Oraculus DI Auditor Project*  
*Generated: 2025-12-06*
