# Phase 7: Strategic Data Integration + Expansion

This document describes the Phase 7 corpus integration framework for ingesting and analyzing large-scale legal datasets including the United States Code (USC), Code of Federal Regulations (CFR), California codes, and other statutory corpora.

## Overview

Phase 7 extends the Phase 6 ingestion pipeline with:
- **XML parsing** for legal document formats
- **Cryptographic verification** (SHA-256) for file integrity
- **Cross-jurisdiction auditing** to detect references across federal/state boundaries
- **Provenance tracking** for complete data lineage
- **Semantic search interface** for querying across corpora

## Supported Corpora

| Corpus | Source | Format | Notes |
|--------|--------|--------|-------|
| **United States Code** | [uscode.house.gov/download](https://uscode.house.gov/download/download.shtml) | XML/TXT | 54 titles, updated regularly |
| **Code of Federal Regulations** | [ecfr.gov bulk data](https://www.ecfr.gov/bulkdata/ECFR_xml.zip) | XML | 50 titles |
| **U.S. Constitution** | public domain TXT | TXT | Baseline reference |
| **California Constitution + Statutes** | [leginfo.legislature.ca.gov](https://leginfo.legislature.ca.gov/) | HTML/XML | Requires normalization |
| **Supreme Court Opinions** | [CourtListener API](https://www.courtlistener.com/api/rest-info/) | JSON | For case law ingestion |

## Architecture

### New Components

#### Ingestion Modules (`src/oraculus_di_auditor/ingestion/`)

- **`xml_parser.py`** - Converts legal XML documents to normalized plain text
  - Supports nested XML structures
  - Extracts text while preserving document hierarchy
  - Fallback to built-in XML parser if lxml unavailable

- **`checksum.py`** - SHA-256 checksums and provenance tracking
  - `file_checksum()` - Calculate SHA-256 hash for files
  - `record_provenance()` - Log file metadata to JSONL format
  - `verify_integrity()` - Verify files against recorded checksums

#### Analysis Modules (`src/oraculus_di_auditor/analysis/`)

- **`cross_reference.py`** - Cross-jurisdiction reference detection
  - Identifies citations across federal/state boundaries
  - Detects jurisdiction mismatches
  - Pattern matching for USC, CFR, CA codes, Public Laws, etc.

#### Interface Modules (`src/oraculus_di_auditor/interface/`)

- Future home for API server and graph visualizer
- Currently houses search CLI interface

### Enhanced Scripts

#### `scripts/ingest_and_index.py`

Updated to support XML format ingestion:

```bash
# Standard ingestion (TXT, JSON, auto-detect)
python scripts/ingest_and_index.py --source data/sources --analyze

# XML corpus ingestion with provenance tracking
python scripts/ingest_and_index.py \
  --source /data/legal/uscode \
  --format xml \
  --jurisdiction federal \
  --analyze

# California statutes
python scripts/ingest_and_index.py \
  --source /data/legal/ca \
  --format xml \
  --jurisdiction california \
  --analyze
```

**New features:**
- `--format` flag supports `xml`, `txt`, `json`, or `auto` (default)
- `--provenance` specifies output path for provenance log (default: `data/provenance.jsonl`)
- Automatic SHA-256 checksumming for XML files
- Cross-jurisdiction audit during analysis phase

#### `scripts/verify_integrity.py` (NEW)

Verify file integrity using provenance checksums:

```bash
# Verify all files in provenance log
python scripts/verify_integrity.py --input data/provenance.jsonl

# Show detailed results
python scripts/verify_integrity.py --input data/provenance.jsonl --verbose
```

**Output:**
- Summary: total records, verified, failed, missing files
- Success rate percentage
- Detailed hash comparison (with `--verbose`)

#### `scripts/search_cli.py` (NEW)

Semantic search interface for querying legal corpus:

```bash
# Basic search
python scripts/search_cli.py --query "Fourth Amendment unreasonable searches"

# Get top 10 results
python scripts/search_cli.py \
  --query "due process clause" \
  --top-k 10

# JSON output for programmatic use
python scripts/search_cli.py \
  --query "equal protection" \
  --json

# Filter by similarity threshold
python scripts/search_cli.py \
  --query "commerce clause" \
  --threshold 0.5
```

## Data Flow

```
1. External Corpus Sources
   └─> XML files (USC, CFR, CA codes)

2. XML Parser (xml_parser.py)
   └─> Normalized plain text

3. Checksum Tracker (checksum.py)
   └─> SHA-256 hash + provenance record → data/provenance.jsonl

4. Document Ingestion
   └─> Normalized JSON → data/cases/*.json

5. Embedding (LocalEmbedder)
   └─> TF-IDF vectors → data/vectors/

6. Vector Index (Retriever)
   └─> Searchable index

7. Analysis
   ├─> Standard anomaly detection (analyzer.py)
   └─> Cross-jurisdiction audit (cross_reference.py)

8. Reports
   └─> JSON/CSV audit reports → data/reports/
```

## Configuration

### Data Paths (`src/oraculus_di_auditor/config.py`)

External corpus mount points (outside Git repo):

```python
DATA_PATHS = {
    "uscode": "/data/legal/uscode",
    "cfr": "/data/legal/cfr",
    "california": "/data/legal/ca",
}
```

These paths should be configured to point to external storage locations containing downloaded legal corpora.

### .gitignore

Phase 7 additions to prevent large corpus files from being committed:

```
# Phase 7: External legal corpus data paths
/data/legal/
*.tar.gz
*.zip

# Provenance and integrity files
data/provenance.jsonl
data/ledger.db
```

## Corpus Acquisition

### 1. United States Code

```bash
# Create external directory
mkdir -p /data/legal/uscode

# Download latest release (118th Congress)
wget https://uscode.house.gov/download/releasepoints/us/pl/118/xml_uscAll.zip \
  -O uscode.zip

# Extract
unzip uscode.zip -d /data/legal/uscode

# Ingest
python scripts/ingest_and_index.py \
  --source /data/legal/uscode \
  --format xml \
  --jurisdiction federal \
  --analyze
```

### 2. Code of Federal Regulations

```bash
# Create external directory
mkdir -p /data/legal/cfr

# Download bulk data
wget https://www.ecfr.gov/bulkdata/ECFR_xml.zip -O cfr.zip

# Extract
unzip cfr.zip -d /data/legal/cfr

# Ingest
python scripts/ingest_and_index.py \
  --source /data/legal/cfr \
  --format xml \
  --jurisdiction federal \
  --analyze
```

### 3. California Codes

```bash
# Create external directory
mkdir -p /data/legal/ca

# Download from leginfo.legislature.ca.gov
# (Manual download or scraping required)

# Ingest
python scripts/ingest_and_index.py \
  --source /data/legal/ca \
  --format xml \
  --jurisdiction california \
  --analyze
```

## Provenance Tracking

### Provenance Log Format

The provenance log (`data/provenance.jsonl`) records metadata for each ingested file:

```json
{
  "file": "/absolute/path/to/file.xml",
  "sha256": "a3b2c1d4e5f6...",
  "source": "https://source.url/or/file/path",
  "jurisdiction": "federal",
  "size": 12345,
  "metadata": {
    "format": "xml",
    "filename": "title42.xml"
  }
}
```

### Integrity Verification

Verify that all files still match their recorded checksums:

```bash
python scripts/verify_integrity.py --input data/provenance.jsonl
```

**Sample output:**
```
======================================================================
Verification Results
======================================================================
Total records:   150
✓ Verified:      148
✗ Failed:        1
⚠ Missing:       1

Success rate:    98.7%
```

## Cross-Jurisdiction Auditing

### Detected Patterns

The cross-reference auditor detects:

1. **Federal-State Cross-References**
   - Documents citing both USC and CA codes
   - Example: "42 U.S.C. § 1983" + "Cal. Penal Code"

2. **CFR-State Cross-References**
   - Federal regulations referencing state law
   - Example: "21 CFR § 50.25" + "Cal. Health Code"

3. **Jurisdiction Mismatches**
   - Federal documents with predominantly state citations
   - State documents with predominantly federal citations

### Sample Findings

```json
{
  "id": "doc_12345",
  "jurisdiction": "federal",
  "issue": "federal_state_cross_reference",
  "severity": "info",
  "description": "Document contains both federal (USC) and California state code references",
  "details": {
    "federal": ["42 U.S.C. § 1983"],
    "state": ["Cal. Penal Code"]
  }
}
```

## Search Interface

### Query Examples

```bash
# Constitutional law
python scripts/search_cli.py --query "Fourth Amendment unreasonable searches"

# Federal regulations
python scripts/search_cli.py --query "administrative procedure act notice and comment"

# State law
python scripts/search_cli.py --query "California consumer privacy rights"

# Cross-jurisdiction
python scripts/search_cli.py --query "supremacy clause preemption state law"
```

### Output Format

Human-readable:
```
======================================================================
Search Results for: 'Fourth Amendment unreasonable searches'
======================================================================

[1] United States Constitution - Amendment IV
    ID:           usc_const_amend4
    Jurisdiction: federal
    Similarity:   0.8542
    Source:       constitution/amendments.xml

[2] USC Title 42 - Civil Rights
    ID:           usc_t42_s1983
    Jurisdiction: federal
    Similarity:   0.7231
    Source:       uscode/title42/section1983.xml

Total results: 2
```

JSON format (`--json`):
```json
{
  "query": "Fourth Amendment unreasonable searches",
  "results": [
    {
      "metadata": {
        "id": "usc_const_amend4",
        "title": "United States Constitution - Amendment IV",
        "jurisdiction": "federal",
        "source": "constitution/amendments.xml"
      },
      "score": 0.8542
    }
  ],
  "count": 2
}
```

## Performance Considerations

### Storage Estimates

- **U.S. Code (54 titles)**: ~2-3 GB XML
- **CFR (50 titles)**: ~5-7 GB XML
- **Vector index (TF-IDF 2048-dim)**: ~8 GB for 250,000 documents
- **Provenance log**: ~10-50 MB (depending on metadata)

### Processing Time

- **XML parsing**: ~100-500 documents/minute (depends on file size)
- **Embedding**: ~1000-5000 documents/minute (TF-IDF)
- **Search**: <100ms for top-k=10 (in-memory index)

### Optimization Options

1. **Incremental Ingestion**: Skip files with existing checksums
2. **Batch Processing**: Process large corpora in chunks
3. **FAISS Integration**: For >1M documents, use FAISS for vector search
4. **SQLite Storage**: Migrate vectors to SQLite for efficient storage

## Testing

### XML Parser Tests

```bash
pytest tests/test_xml_parser.py -v
```

### Checksum Tests

```bash
pytest tests/test_checksum.py -v
```

### Cross-Reference Tests

```bash
pytest tests/test_cross_reference.py -v
```

### Integration Tests

```bash
pytest tests/test_phase7_integration.py -v
```

## Phase 7 Completion Criteria

| Metric | Target | Status |
|--------|--------|--------|
| Corpus coverage | 54 U.S.C. titles + 50 CFR titles + CA codes + Constitution | Scaffold ready |
| Documents indexed | ≥ 250,000 | Pending corpus acquisition |
| Vector index size | ≤ 8 GB (2048-dim TF-IDF) | Architecture supports |
| Anomaly reports | JSON + CSV for each corpus | ✓ Implemented |
| Integrity | 100% SHA-256 verified | ✓ Implemented |
| Tests passing | ≥ 95% coverage | Pending test addition |

## Next Steps

1. **Acquire Corpus Data**: Download USC, CFR, and CA codes
2. **Run Ingestion**: Process corpora with `ingest_and_index.py`
3. **Verify Integrity**: Run `verify_integrity.py` on all files
4. **Test Search**: Query corpus with `search_cli.py`
5. **Review Reports**: Examine cross-jurisdiction findings
6. **Optimize**: Add FAISS or SQLite if needed for scale

## Future Enhancements (Phase 7+)

### Graph Intelligence Layer
- Neo4j or NetworkX for statutory relationships
- Node types: Title, Section, Subsection, Cross-ref
- Edge types: amends, repeals, references, conflicts
- Visualization of legislative drift

### Blockchain-Style Provenance Ledger
- SQLite table with append-only semantics
- Cryptographic chain of custody
- Tamper-evident audit log

### LLM-Assisted Summarization
- Lightweight local model integration (Ollama)
- Context-aware clause summarization
- No external API calls (privacy-first)

### API Server
- FastAPI REST interface
- GraphQL for complex queries
- WebSocket for real-time updates

### Visual Dashboard
- Plotly/Dash for anomaly visualization
- Interactive graph exploration
- Public-facing audit interface

## References

- [PHASE6_INGESTION.md](PHASE6_INGESTION.md) - Phase 6 pipeline documentation
- [DATA_PROVENANCE.md](DATA_PROVENANCE.md) - Provenance tracking details
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
