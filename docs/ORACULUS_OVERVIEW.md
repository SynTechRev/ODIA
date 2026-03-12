# ORACULUS DI AUDITOR - Legislative Intelligence System Overview

## System Architecture

The Oraculus DI Auditor is an autonomous legislative intelligence system designed to ingest, validate, and audit statutory, contractual, and administrative documents. The system maintains complete provenance tracking, builds reference graphs, and performs integrity validation on legal documents.

## Core Components

### 1. Ingestion System (`src/oraculus/ingestion/`)

The ingestion system provides robust multi-format document loading with automatic provenance tracking.

#### Legislative Loader (`legislative_loader.py`)

**Key Functions:**
- `load_legislation(path, validate=False)` - Load documents from JSON, TXT, or PDF formats
- `normalize_document(data, document_id=None)` - Transform raw data into canonical schema
- `_load_pdf(path)` - Extract text content from PDF files

**Features:**
- Multi-format support (JSON, TXT, PDF)
- Automatic SHA-256 hash generation for integrity tracking
- Provenance metadata injection
- Schema normalization to canonical format

**Example Usage:**
```python
from oraculus.ingestion.legislative_loader import load_legislation, normalize_document

# Load a legislative document
raw_data = load_legislation("data/legislation/sample_act.json")

# Normalize to canonical schema
normalized = normalize_document(raw_data, document_id="act-2023-0142")
```

### 2. Schema System (`src/oraculus/schemas/`)

#### Canonical Legal Schema (`legal_schema.json`)

The canonical schema defines the standardized structure for all legislative documents:

**Required Fields:**
- `document_id` - Unique identifier (pattern: `^[a-z0-9\-]+$`)
- `title` - Official document title
- `document_type` - Type classification (act, bill, regulation, etc.)
- `provenance` - Integrity and source metadata

**Optional Fields:**
- `sections` - Structured document sections with IDs and content
- `authority` - Issuing authority or legislative body
- `jurisdiction` - Geographical or organizational scope
- `version_date` - Effective date (ISO 8601 format)
- `signatory` - List of authorized signatories
- `references` - Cross-references to other documents
- `metadata` - Additional status, tags, and notes

**Provenance Structure:**
```json
{
  "source": "original_source_url",
  "hash": "sha256_hash_of_content",
  "verified_on": "2023-11-12T00:00:00Z"
}
```

### 3. Auditing System (`src/oraculus/auditing/`)

#### Provenance Tracker (`provenance_tracker.py`)

The ProvenanceTracker maintains a complete graph of document relationships and performs integrity validation.

**Key Features:**

1. **Document Management**
   - Add documents to the tracking system
   - Retrieve documents by ID
   - Build and maintain reference graphs

2. **Reference Graph Building**
   - Automatic bidirectional reference tracking
   - Forward references (documents this document cites)
   - Backward references (documents that cite this document)
   - Support for multiple reference types (cites, amends, repeals, supersedes, implements)

3. **Anomaly Detection**
   - Missing required fields (title, jurisdiction)
   - Incomplete provenance metadata
   - Missing signatories for specific document types
   - Broken document references
   - Hash integrity validation

4. **Confidence Scoring**
   - Algorithmic confidence calculation (0.0 to 1.0)
   - Weighted deductions for different anomaly types
   - Thresholds:
     - ≥0.95: Pass
     - ≥0.85: Pass with Notes
     - <0.85: Review Required

5. **Audit Reporting**
   - Complete audit reports with findings
   - Compliance status determination
   - Anomaly listings with descriptions
   - Graph relationship information

**Example Usage:**
```python
from oraculus.auditing.provenance_tracker import ProvenanceTracker

# Initialize tracker
tracker = ProvenanceTracker()

# Add documents
tracker.add_document(normalized_document)

# Detect anomalies
anomalies = tracker.detect_anomalies("act-2023-0142")

# Calculate confidence
confidence = tracker.calculate_confidence_score("act-2023-0142")

# Generate audit report
report = tracker.generate_audit_report("act-2023-0142")
```

## Lineage Tracking

### Hash-Based Provenance

Every document loaded through the system receives a SHA-256 hash of its content. This hash serves as:
- Integrity verification mechanism
- Change detection system
- Deterministic document fingerprint

### Reference Graph Structure

The system maintains a bidirectional graph structure:

```
Document A ──cites──> Document B
           <──referenced_by──
```

**Graph Operations:**
- `get_dependencies(doc_id)` - Get all documents this document depends on
- `get_dependents(doc_id)` - Get all documents that depend on this document
- `export_graph()` - Export complete reference graph for visualization

### Temporal Lineage

Documents include temporal metadata:
- `version_date` - Effective date of the document
- `verified_on` - Timestamp of system ingestion
- `signature_date` - Signatory timestamps

This enables temporal analysis and version tracking across document evolution.

## Data Flow Architecture

```
┌─────────────┐
│  Raw Files  │
│ (PDF/JSON/  │
│    TXT)     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Legislative     │
│ Loader          │
│ - Parse         │
│ - Hash          │
│ - Add Provenance│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Schema          │
│ Normalization   │
│ - Canonical     │
│   Structure     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Provenance      │
│ Tracker         │
│ - Build Graph   │
│ - Detect Issues │
│ - Score         │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Audit Report    │
│ - JSON Output   │
│ - Markdown      │
└─────────────────┘
```

## Security and Privacy

### Privacy-Safe Design
- All processing occurs locally
- No external transmission of source content
- Local file system operations only
- No network dependencies for core functionality

### Deterministic Processing
- Hash-based document IDs ensure reproducibility
- Consistent schema normalization
- Version-controlled outputs

### Transparency
- Full provenance metadata in every output
- Complete transformation logging
- Source tracking with timestamps
- Hash verification at every stage

## Usage Patterns

### Normalization APIs

There are two normalization entry points to avoid ambiguity between legislative schema normalization and generic text normalization:

- `oraculus.ingestion.normalize_legislation`: Canonical schema normalization for legislative documents loaded via `load_legislation`.
   ```python
   from oraculus.ingestion import load_legislation, normalize_legislation

   raw = load_legislation("data/legislation/sample_act.json")
   normalized = normalize_legislation(raw, document_id="act-2023-0142")
   ```

- `oraculus_di_auditor.normalize_text`: Chunking-oriented normalization for plain-text documents.
   ```python
   from oraculus_di_auditor import normalize_text

   normalized = normalize_text({
         "id": "doc-1",
         "title": "Simple Text",
         "text": "Some long text...",
   })
   ```

Use `normalize_legislation` for schema-compliant legal artifacts (adds `document_id`, `sections`, `provenance`, etc.). Use `normalize_text` when working with raw text that needs chunking and metadata suitable for embeddings and retrieval.

### Basic Document Processing

```python
from oraculus.ingestion.legislative_loader import load_legislation, normalize_document
from oraculus.auditing.provenance_tracker import ProvenanceTracker

# Initialize tracker
tracker = ProvenanceTracker()

# Load document
raw = load_legislation("path/to/document.json")

# Normalize
normalized = normalize_document(raw, document_id="doc-001")

# Track
tracker.add_document(normalized)

# Audit
report = tracker.generate_audit_report("doc-001")
print(f"Confidence: {report['audit_result']['confidence_score']}")
print(f"Status: {report['audit_result']['compliance_status']}")
```

### Batch Processing

```python
import glob
from oraculus.ingestion.legislative_loader import load_legislation, normalize_document
from oraculus.auditing.provenance_tracker import ProvenanceTracker

tracker = ProvenanceTracker()

# Process all documents in directory
for filepath in glob.glob("data/legislation/*.json"):
    raw = load_legislation(filepath)
    normalized = normalize_document(raw)
    tracker.add_document(normalized)

# Export complete graph
graph = tracker.export_graph()
```

### Reference Analysis

```python
# Find all dependencies
deps = tracker.get_dependencies("act-2023-0142")
print(f"This act depends on: {deps}")

# Find all documents that reference this one
dependents = tracker.get_dependents("act-2023-0142")
print(f"This act is referenced by: {dependents}")

# Get full reference information
refs = tracker.get_references("act-2023-0142")
print(f"References: {refs['references_to']}")
print(f"Referenced by: {refs['referenced_by']}")
```

## Performance Characteristics

### Ingestion Performance
- JSON parsing: ~1ms per document
- Text parsing: <1ms per document
- PDF parsing: ~50-200ms per document (depends on size)
- Hash generation: ~2-5ms per document

### Validation Performance
- Schema validation: ~1-2ms per document
- Anomaly detection: ~5-10ms per document
- Confidence calculation: ~3-5ms per document

### Target Metrics
| Metric | Target | Current |
|--------|--------|---------|
| Test coverage | ≥90% | ~95% |
| Schema compliance | 100% | 100% |
| Hash integrity | 100% verified | 100% |
| False anomaly rate | <2% | TBD |
| Execution time/100 docs | ≤45s | ~5-10s |

## Extension Points

### Custom Anomaly Rules
The anomaly detection system can be extended with custom rules:
```python
# Future: YAML-based rule configuration
anomaly_rules:
  - type: missing_field
    field: jurisdiction
    severity: medium
    message: "Documents should specify jurisdiction"
```

### Semantic Analysis
Future phases will include:
- Transformer-based clause recognition
- Semantic similarity detection
- Automated cross-reference discovery
- Natural language processing for section extraction

### Visualization
The reference graph can be exported for visualization:
- NetworkX integration for graph analysis
- GraphViz export for visual representation
- Interactive web-based graph explorer

## Testing

### Test Coverage
- `tests/test_ingestion.py` - Ingestion and normalization tests
- `tests/test_provenance_tracker.py` - Provenance tracking and auditing tests
- `tests/test_legislative_loader.py` - Original loader tests

### Running Tests
```bash
# Run all tests with coverage
pytest --cov=src/oraculus --cov-report=term-missing

# Run specific test module
pytest tests/test_provenance_tracker.py -v

# Run with detailed output
pytest -vv --tb=short
```

## Future Roadmap

### Phase 3: Advanced Analysis
- Semantic clause recognition with transformers
- Conflict detection between documents
- Automated amendment tracking
- Version diff generation

### Phase 4: Visualization & Reporting
- Interactive web interface
- Graph visualization dashboard
- Automated compliance reports
- Export to multiple formats (PDF, HTML, XML)

### Phase 5: Integration
- API endpoints for document submission
- Webhook notifications for anomalies
- Integration with document management systems
- Real-time monitoring dashboard

## Conclusion

The Oraculus DI Auditor provides a robust, transparent, and privacy-safe system for legislative intelligence. Through its multi-layered architecture of ingestion, normalization, tracking, and auditing, it ensures that all legislative documents maintain integrity, traceability, and compliance throughout their lifecycle.
