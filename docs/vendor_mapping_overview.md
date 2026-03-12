# Vendor Influence & Contract Flow Map (VICFM) v1.0

## Overview

The **Vendor Influence & Contract Flow Map (VICFM)** is an intelligence layer that maps vendors, contract flows, renewal patterns, technology dependencies, procurement irregularities, and cross-year continuity across the the target jurisdiction legislative corpus (2014–2025).

VICFM integrates with the **Anomaly Correlation Engine (ACE)** to provide comprehensive vendor analysis with anomaly correlation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VICFM v1.0 Pipeline                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐            │
│  │ EXTRACTION     │    │ GRAPH ENGINE   │    │ CONTRACT FLOW  │            │
│  ├────────────────┤    ├────────────────┤    ├────────────────┤            │
│  │ • Metadata     │    │ • Vendor nodes │    │ • Year-by-year │            │
│  │ • Filenames    │ -> │ • Contract     │ -> │   activity     │            │
│  │ • Extracted    │    │   edges        │    │ • Renewals     │            │
│  │   text         │    │ • Influence    │    │ • Tech program │            │
│  │ • Amounts      │    │   scores       │    │   timeline     │            │
│  └────────────────┘    └────────────────┘    └────────────────┘            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   INFLUENCE SCORING ENGINE                           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Score = (Frequency × 0.25) + (Value × 0.25) + (ACE Anomaly × 0.20) │   │
│  │       + (Centrality × 0.15) + (Continuity × 0.15)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Vendor Extraction Pipeline (`vendor_map_extractor.py`)

Extracts vendor information from multiple sources:

| Source | Description |
|--------|-------------|
| Metadata fields | Direct vendor/contractor/supplier fields in metadata JSON |
| Document titles | Vendor mentions in document titles |
| Filenames | Vendor patterns in attachment filenames (e.g., "Axon Quote.pdf") |
| Extracted text | Vendor mentions in PDF text extraction cache |

#### Key Functions

- `extract_vendors_from_metadata()` - Extract from metadata JSON files
- `extract_contract_amounts()` - Find and parse contract amounts
- `detect_vendor_aliases()` - Group vendor name variations
- `build_vendor_index()` - Create comprehensive vendor mapping
- `infer_contract_relationships()` - Link vendors to contracts
- `scan_for_procurement_irregularities()` - Detect red flags

### 2. Vendor Graph Engine (`vendor_graph_builder.py`)

Builds a graph model representing vendor relationships:

#### Node Types

| Type | Description |
|------|-------------|
| `vendor` | A vendor/contractor entity |
| `corpus` | A legislative corpus item (meeting) |
| `year` | A calendar year |
| `program` | A technology program (ALPR, Body Cams, etc.) |

#### Edge Types

| Type | Description |
|------|-------------|
| `mentioned_in` | Vendor appears in a corpus |
| `contract_with` | Vendor has contract in corpus (with amount) |
| `active_in` | Vendor active in a year |
| `occurred_in` | Corpus occurred in a year |
| `associated_with` | Vendor associated with tech program |

### 3. Contract Flow Map (`contract_flow_map.py`)

Generates timeline visualizations:

- **Yearly activity** - Vendors active each year
- **New arrivals** - Vendors appearing for first time
- **Exits** - Vendors leaving the ecosystem
- **Renewals** - Consecutive-year contract patterns
- **Program timeline** - Technology program evolution

## Influence Scoring

### Formula

```
Influence Score = (F × 0.25) + (V × 0.25) + (A × 0.20) + (C × 0.15) + (T × 0.15)
```

Where:
- **F** = Frequency score (normalized appearance count)
- **V** = Value score (normalized contract value)
- **A** = Anomaly intersection score (ACE correlation × 0.2)
- **C** = Centrality score (graph degree centrality)
- **T** = Continuity score (year span coverage)

### Dependency Tiers

| Tier | Score Range | Description |
|------|-------------|-------------|
| Critical | ≥ 0.80 | High dependency, requires attention |
| High | 0.60 - 0.79 | Significant dependency |
| Moderate | 0.40 - 0.59 | Normal engagement |
| Low | < 0.40 | Minimal engagement |

## Detecting Procurement Irregularities

VICFM scans for the following procurement red flags:

### Flag Types

| Type | Description | Severity |
|------|-------------|----------|
| `sole_source_flag` | Sole/single source procurement mention | Medium |
| `inconsistent_labeling` | Same vendor, different source patterns | Low |
| `cost_escalation` | >40% year-over-year cost increase | Medium/High |
| `multi_year_vendor` | Vendor active >3 consecutive years | Low |

### Patterns Detected

- Sole-source procurement
- Single-source contracts
- Non-competitive procurement
- Emergency procurement
- Piggyback contracts

### Cost Escalation Rules

- **Medium severity**: 40-100% year-over-year increase
- **High severity**: >100% year-over-year increase

## Understanding Contract Continuity

### Renewal Detection

A contract renewal is inferred when a vendor appears in consecutive years:

```
Vendor A: 2020 → 2021 → 2022 = 3-year renewal pattern
Vendor B: 2019 → 2020 → (gap) → 2022 → 2023 = Two separate 2-year patterns
```

### Continuity Metrics

| Metric | Description |
|--------|-------------|
| `consecutive_years` | Number of consecutive years active |
| `year_span` | Total years from first to last appearance |
| `gap_count` | Number of gaps in activity timeline |

## Integration with ACE

VICFM integrates with the Anomaly Correlation Engine in several ways:

### Data Flow

```
ACE_REPORT.json → VICFM Analysis → VENDOR_ANOMALY_LINKS.json
                                 → VENDOR_TECH_DEPENDENCIES.json
```

### Anomaly Correlation

- Vendors appearing in corpus items with ACE anomalies receive elevated scores
- Cross-reference: Vendor mentions in anomaly-flagged documents
- High-risk vendors: Those with both procurement irregularities AND ACE anomalies

### Output Integration

| File | Description |
|------|-------------|
| `VENDOR_ANOMALY_LINKS.json` | Mapping of vendors to ACE anomalies |
| `VENDOR_TECH_DEPENDENCIES.json` | Technology dependency analysis |

## Output Files

### Primary Outputs

| File | Format | Description |
|------|--------|-------------|
| `vendor_graph.json` | JSON | Complete graph model with nodes and edges |
| `vendor_scores.json` | JSON | Ranked vendors with influence scores |
| `vendor_influence_network.csv` | CSV | Flat edge list for spreadsheet analysis |
| `CONTRACT_FLOW_MAP.json` | JSON | Complete contract flow timeline |
| `CONTRACT_FLOW_MAP.md` | Markdown | Human-readable flow map report |

### Report Outputs

| File | Format | Description |
|------|--------|-------------|
| `VENDOR_INFLUENCE_REPORT.md` | Markdown | Top 25 vendors with analysis |
| `PROCUREMENT_FLAGS.json` | JSON | All detected irregularities |
| `PROCUREMENT_FLAGS.md` | Markdown | Human-readable irregularity summary |

## Usage

### Command Line

```bash
# Run vendor extraction
python scripts/vendor_map_extractor.py --corpus-root oraculus/corpus --years 2014-2025

# Build vendor graph
python scripts/vendor_graph_builder.py --vendor-data vendor_index.json --output .

# Generate contract flow map
python scripts/contract_flow_map.py --vendor-data vendor_index.json --output .
```

### Programmatic Usage

```python
from scripts.vendor_map_extractor import run_vendor_extraction
from scripts.vendor_graph_builder import run_vendor_graph_builder
from scripts.contract_flow_map import run_contract_flow_map
from pathlib import Path

# Extract vendors
vendor_data = run_vendor_extraction(
    corpus_root=Path("oraculus/corpus"),
    year_range="2014-2025",
    output_dir=Path(".")
)

# Build graph
graph_result = run_vendor_graph_builder(
    vendor_data=vendor_data,
    year_range="2014-2025",
    output_dir=Path(".")
)

# Generate flow map
flow_map = run_contract_flow_map(
    vendor_data=vendor_data,
    year_range="2014-2025",
    output_dir=Path(".")
)
```

## Glossary

| Term | Definition |
|------|------------|
| **ALPR** | Automated License Plate Reader |
| **BWC** | Body-Worn Camera |
| **Continuity** | Measure of vendor presence across years |
| **Cost Escalation** | Significant year-over-year contract increase |
| **Dependency Tier** | Classification of vendor importance |
| **Influence Score** | Weighted measure of vendor significance |
| **Piggyback Contract** | Contract leveraging another jurisdiction's bid |
| **Renewal Pattern** | Consecutive-year vendor activity |
| **Sole Source** | Non-competitive procurement |
| **VICFM** | Vendor Influence & Contract Flow Map |

## Known Vendors

VICFM tracks the following vendor categories:

### Surveillance Technology
- Axon (body cameras, Tasers)
- Vendor B (ALPR, surveillance)
- Vigilant Solutions (ALPR)
- Leonardo/ELSAG (ALPR)
- Motorola Solutions (communications)

### Telecommunications
- T-Mobile
- Verizon
- AT&T

### IT/Software
- Microsoft
- Oracle
- Tyler Technologies

### Professional Services
- NBS Government Finance
- HdL Companies

## Technology Programs Tracked

| Program | Description |
|---------|-------------|
| ALPR | Automated License Plate Recognition |
| Body-Worn Cameras | Police body camera systems |
| Cellular Infrastructure | Cell towers, wireless networks |
| Video Surveillance | CCTV, security cameras |
| JAG Grants | Justice Assistance Grant funded items |
| Capital Improvement | Infrastructure projects |
| Software/IT | Enterprise software contracts |

## Agency-Vendor-Anomaly Triangulation

VICFM integrates with both **ACE** (anomaly detection) and **CAIM** (agency mapping) to provide a three-way triangulation analysis.

### Triangulation Model

```
                        ┌─────────────┐
                        │   VENDORS   │
                        │   (VICFM)   │
                        └──────┬──────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  AGENCIES   │◄───►│  CONTRACTS  │◄───►│  ANOMALIES  │
    │   (CAIM)    │     │  (Corpus)   │     │   (ACE)     │
    └─────────────┘     └─────────────┘     └─────────────┘
```

### Triangulation Analysis

| Relationship | Description | Indicator |
|--------------|-------------|-----------|
| Agency ↔ Vendor | Shared procurement patterns | Vendor overlap in ICM |
| Vendor ↔ Anomaly | Vendor in anomaly-flagged docs | ACE intersection score |
| Agency ↔ Anomaly | Agency in anomaly clusters | ACE anomaly linkage |

### Use Cases

#### 1. High-Risk Vendor Identification

```python
# Find vendors appearing in multiple anomaly-flagged corpora
high_risk_vendors = [
    v for v in vendor_scores
    if v['anomaly_intersection'] > 0.3
]
```

#### 2. Agency-Vendor Dependency Analysis

```python
# Find agencies with high vendor overlap
from scripts.cross_agency_influence import build_agency_graph

graph = build_agency_graph(agency_index, relationships, corpora, vendor_data)
vendor_edges = [e for e in graph.edges if e['type'] == 'shares_vendor']
```

#### 3. Anomaly Propagation Risk

```python
# Find agencies that share both vendors AND anomalies
high_risk_pairs = [
    pair for pair in icm_result['detailed_scores']
    if pair['vendor_overlap'] > 0.3 and pair['ace_anomaly_linkage'] > 0.2
]
```

### Output Files

| File | Description |
|------|-------------|
| `agency_graph.json` | Includes agency-vendor edges |
| `influence_matrix.csv` | Vendor overlap contributes 25% |
| `icm_matrix.json` | Full triangulation scores |

See [CAIM Overview](caim_overview.md) for complete agency mapping documentation.

## PDF Forensics Integration (DPMM)

VICFM integrates with the **Deep Packet Metadata Miner (DPMM)** to link vendor software detection with PDF forensic analysis.

### Forensic Vendor Overlaps

DPMM generates `FORENSIC_VENDOR_OVERLAPS.json` which:
- Maps PDF producer/creator fields to known vendors
- Identifies vendor-linked software patterns in document metadata
- Cross-references with VICFM vendor index

```python
# Example: Finding PDFs with Microsoft vendor software
from scripts.pdf_forensics.forensic_integration import generate_forensic_vendor_overlaps

overlaps = generate_forensic_vendor_overlaps(forensic_report, vendor_report)
microsoft_pdfs = [
    o for o in overlaps['overlaps']
    if o.get('vendor') == 'Microsoft'
]
```

See [PDF Forensics Overview](pdf_forensics_overview.md) for complete DPMM documentation.

---

*VICFM v1.0 - Part of the Oraculus DI Auditor Project*  
*Generated: 2025-12-06*
