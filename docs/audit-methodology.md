# Audit Methodology

## Overview

The Oraculus-DI-Auditor (ODIA) employs a multi-layered anomaly detection approach grounded in recursive scalar intelligence principles derived from Robert Edward Grant's architectural model. This document describes the audit methodology, detection heuristics, and scoring framework.

## Core Principles

### 1. Hierarchical Analysis
Documents are analyzed across multiple conceptual layers:
- **Fiscal Layer**: Appropriation trails, budget lineage, financial transparency
- **Constitutional Layer**: Delegation patterns, constitutional conformity
- **Surveillance Layer**: Privacy implications, outsourcing to private vendors
- **Structural Layer**: Cross-references, citations, metadata integrity

### 2. Explainability First
Every anomaly detected must include:
- **ID**: Stable, machine-readable identifier
- **Issue**: Human-readable description
- **Severity**: low, medium, or high
- **Layer**: Which detection layer found it
- **Details**: Structured, explainable evidence

### 3. Conservative Heuristics
Initial detectors use intentionally conservative rules to minimize false positives. Detection logic evolves iteratively as patterns emerge from real-world corpus analysis.

## Detection Layers

### Fiscal Trail Analyzer (`fiscal.py`)

**Purpose**: Detect gaps or inconsistencies in appropriation and fiscal lineage.

**Current Heuristics**:
- Missing provenance hash (integrity trail incomplete)
- Future: Budget reference pattern analysis
- Future: Appropriation chain verification
- Future: Fiscal amendment tracking

**Example Anomaly**:
```json
{
  "id": "fiscal:missing-provenance-hash",
  "issue": "Provenance hash missing; integrity trail incomplete",
  "severity": "low",
  "layer": "fiscal",
  "details": {"provenance_present": false}
}
```

### Constitutional Conformity Analyzer (`constitutional.py`)

**Purpose**: Flag patterns suggestive of unconstitutional delegation or statutory conflicts.

**Current Status**: Placeholder (returns no anomalies)

**Planned Heuristics**:
- Unconstitutional delegation keywords (e.g., "Secretary may determine")
- Conflicts between statute and Bill of Rights
- Enumerated powers boundary detection
- Commerce clause overreach patterns

### Surveillance Outsourcing Detector (`surveillance.py`)

**Purpose**: Surface outsourcing of surveillance functions to private vendors and privacy risks.

**Current Status**: Placeholder (returns no anomalies)

**Planned Heuristics**:
- Private contractor surveillance keywords
- Data sharing agreements
- Third-party access provisions
- Warrantless surveillance indicators
- Biometric data collection patterns

### Cross-Reference Auditor (`cross_reference.py`)

**Purpose**: Detect cross-jurisdictional citations and reference mismatches.

**Current Heuristics**:
- USC (United States Code) pattern detection
- CFR (Code of Federal Regulations) pattern detection
- California code references
- Public Law citations
- Statutes at Large references
- Cross-jurisdiction boundary violations

**Example Anomaly**:
```json
{
  "id": "cross-ref:federal-in-state",
  "issue": "Federal statute cited in state jurisdiction document",
  "severity": "medium",
  "layer": "cross-reference",
  "details": {
    "document_jurisdiction": "california",
    "detected_citations": ["42 U.S.C. § 1983"]
  }
}
```

## Recursive Scalar Model

### Pattern Lattice Scoring (`scalar_core.py`)

The recursive scalar core implements a confidence-like scoring system inspired by:
- Hierarchical information geometry
- Self-similar pattern detection
- Node collapse detection
- Anomaly geometry mapping

**Current Formula**:
```
score = max(0.0, min(1.0, 1.0 - 0.05 * anomaly_count))
```

**Interpretation**:
- `1.0` = Perfect consistency, no anomalies
- `0.95` = 1 anomaly detected
- `0.0` = 20+ anomalies (critical structural failure)

**Future Enhancements**:
- Weighted anomaly scoring by severity
- Pattern lattice interference detection
- Temporal drift analysis
- Legislative lineage coherence metrics

## Audit Engine Architecture

### Entry Point: `analyze_document(doc)`

The audit engine (`audit_engine.py`) provides a unified interface:

```python
from oraculus_di_auditor.analysis import analyze_document

result = analyze_document(normalized_doc)
# Returns:
# {
#   "count": 2,
#   "score": 0.90,
#   "anomalies": [...]
# }
```

### Execution Flow

1. **Input Validation**: Ensure document is a valid dict
2. **Fiscal Analysis**: `detect_fiscal_anomalies(doc)`
3. **Constitutional Analysis**: `detect_constitutional_anomalies(doc)`
4. **Surveillance Analysis**: `detect_surveillance_anomalies(doc)`
5. **Cross-Reference Analysis**: Separate module, run via analyzer
6. **Scalar Scoring**: `compute_recursive_scalar_score(doc, anomalies)`
7. **Result Aggregation**: Return structured result with count, score, anomalies

### Detector Requirements

All detectors must be **pure functions** with signature:
```python
def detect_X_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect anomalies in layer X.
    
    Args:
        doc: Normalized document dict
        
    Returns:
        List of anomaly dicts with id, issue, severity, layer, details
    """
```

## Integration with Pipeline

### Document Normalization
Documents must be normalized to canonical schema before analysis:
```python
from oraculus.ingestion import load_legislation, normalize_document

data = load_legislation("statute.json")
normalized = normalize_document(data)
result = analyze_document(normalized)
```

### Provenance Tracking
All analyzed documents should have provenance metadata:
```json
{
  "provenance": {
    "source": "/path/to/file",
    "hash": "sha256:...",
    "verified_on": "2025-01-15T12:00:00Z"
  }
}
```

### Report Generation
Audit results can be exported via `reporter.py`:
```python
from oraculus_di_auditor.reporter import generate_json_report, generate_csv_report

generate_json_report([result1, result2], "output/audit_results.json")
generate_csv_report([result1, result2], "output/audit_results.csv")
```

## Testing and Validation

### Test Coverage Requirements
- Each detector must have unit tests
- Edge cases: empty docs, missing fields, malformed data
- Integration tests: full pipeline execution
- Regression tests: known anomaly patterns

### Test Examples
See `tests/test_fiscal_detector.py`, `tests/test_audit_engine.py`

## Future Roadmap

### Phase 1: Enhanced Detection
- [ ] Fiscal appropriation chain analyzer
- [ ] Constitutional delegation keyword detector
- [ ] Surveillance keyword pattern matching

### Phase 2: Advanced Modeling
- [ ] Weighted scalar scoring by severity
- [ ] Pattern lattice interference detection
- [ ] Temporal coherence analysis

### Phase 3: Machine Learning Integration
- [ ] Anomaly clustering
- [ ] Supervised classification for severity
- [ ] Embedding-based similarity detection

## References

- **Recursive Scalar Model**: See `docs/recursive-scalar-model.md`
- **Architecture Overview**: See `docs/ARCHITECTURE.md`
- **Data Provenance**: See `docs/DATA_PROVENANCE.md`
- **Phase Planning**: See `docs/PHASE_PLAN.md`
