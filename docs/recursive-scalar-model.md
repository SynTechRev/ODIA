# Recursive Scalar Model

## Overview

The **Recursive Scalar Model** is the theoretical foundation for the Oraculus-DI-Auditor's anomaly detection and confidence scoring system. It is inspired by **Robert Edward Grant's** architectural principles of hierarchical information geometry, self-similarity, pattern lattices, and node collapse detection.

## Core Concepts

### 1. Hierarchical Layers

Legislative systems are inherently hierarchical:
- **Constitutional Layer**: Foundational principles (Bill of Rights, enumerated powers)
- **Statutory Layer**: Enacted legislation (U.S. Code, state statutes)
- **Regulatory Layer**: Administrative rules (CFR, state regulations)
- **Fiscal Layer**: Appropriations, budgets, spending authority
- **Implementation Layer**: Agency procedures, contracts, enforcement

Each layer should be **coherent** with the layers above and below it.

### 2. Latticed Information Geometry

Documents exist in a **lattice structure** where:
- **Nodes** represent individual documents, sections, or provisions
- **Edges** represent references, citations, amendments, repeals
- **Paths** represent lineage chains (e.g., statute → regulation → budget → contract)

**Key Properties**:
- **Connectivity**: Well-formed systems have dense reference networks
- **Consistency**: References should resolve to valid nodes
- **Coherence**: Referenced content should align semantically

### 3. Self-Similarity

Legitimate legislative systems exhibit **self-similar patterns**:
- **Citation Patterns**: Similar documents cite in similar ways
- **Structure Patterns**: Sections follow predictable organization
- **Language Patterns**: Legal terminology maintains consistency
- **Fiscal Patterns**: Budget allocations follow appropriation chains

**Anomalies** break self-similarity:
- Novel citation patterns (possible fabrication)
- Structural outliers (possible manipulation)
- Terminology shifts (possible obfuscation)

### 4. Pattern Collapse / Emergence

In complex legislative systems:
- **Emergence**: New patterns arise from interaction of simpler rules
- **Collapse**: Loss of structural coherence signals system failure

**Detection Strategy**:
- Baseline patterns from known-good corpus
- Detect deviations using statistical and geometric measures
- Flag collapse nodes where multiple anomalies cluster

### 5. Anomaly Node Detection

An **anomaly node** is a document or provision that exhibits:
- Missing or broken references
- Inconsistent metadata (dates, jurisdictions, authorities)
- Semantic misalignment with cited sources
- Fiscal opacity (missing appropriation chains)
- Privacy violations or surveillance indicators

## Mathematical Framework

### Scalar Score Function

The recursive scalar score is a **confidence metric** in the range `[0.0, 1.0]`:

```
score(doc, anomalies) = max(0, min(1, base - penalty(anomalies)))
```

**Current Implementation** (`scalar_core.py`):
```python
def compute_recursive_scalar_score(doc, anomalies):
    base = 1.0
    penalty = 0.05 * len(anomalies)
    return max(0.0, min(1.0, base - penalty))
```

**Interpretation**:
- `score = 1.0`: Perfect consistency, no anomalies
- `score = 0.95`: One minor anomaly
- `score = 0.5`: Ten anomalies (moderate issues)
- `score = 0.0`: 20+ anomalies (critical failure)

### Future Enhancement: Weighted Scoring

```python
def compute_recursive_scalar_score(doc, anomalies):
    base = 1.0
    weights = {"low": 0.02, "medium": 0.05, "high": 0.10}
    penalty = sum(weights.get(a["severity"], 0.05) for a in anomalies)
    return max(0.0, min(1.0, base - penalty))
```

### Future Enhancement: Pattern Lattice Coherence

```python
def compute_lattice_coherence(doc, corpus):
    """Measure structural similarity to known-good corpus."""
    # Extract features: citation density, section structure, terminology
    features = extract_features(doc)
    corpus_centroid = compute_centroid([extract_features(d) for d in corpus])
    distance = euclidean_distance(features, corpus_centroid)
    coherence = 1.0 / (1.0 + distance)  # Normalize to [0, 1]
    return coherence
```

### Future Enhancement: Temporal Drift

```python
def compute_temporal_drift(doc, historical_versions):
    """Detect if amendments deviate from expected evolution."""
    deltas = [diff(v1, v2) for v1, v2 in zip(historical_versions[:-1], historical_versions[1:])]
    expected_delta = mean(deltas)
    actual_delta = diff(historical_versions[-1], doc)
    drift = abs(actual_delta - expected_delta) / expected_delta
    return 1.0 / (1.0 + drift)
```

## Anomaly Geometry

### Node Types

In the legislative lattice:

1. **Source Node**: Original statute or constitutional provision
2. **Reference Node**: Document that cites others
3. **Sink Node**: Implementation (regulation, budget, contract)
4. **Orphan Node**: No incoming or outgoing references (suspicious)
5. **Hub Node**: Many incoming/outgoing references (central provision)
6. **Collapse Node**: Anomaly cluster center

### Anomaly Detection via Geometry

**Density Analysis**:
```
If degree(node) < threshold → potential orphan anomaly
If degree(node) >> mean(degree) → potential hub or manipulation
```

**Path Integrity**:
```
For each reference edge:
  If target does not exist → broken reference anomaly
  If semantic similarity(source, target) < threshold → misalignment anomaly
```

**Collapse Detection**:
```
If anomaly_count(neighborhood(node)) > threshold → collapse node
```

## Detector Integration

Each anomaly detector contributes to the scalar score:

### Fiscal Detector
- **Input**: Document with provenance
- **Output**: List of fiscal anomalies
- **Contribution**: Integrity of appropriation chains

### Constitutional Detector
- **Input**: Document with statutory content
- **Output**: List of constitutional conflicts
- **Contribution**: Conformity to foundational principles

### Surveillance Detector
- **Input**: Document with privacy-relevant keywords
- **Output**: List of surveillance risks
- **Contribution**: Privacy and civil liberties protection

### Cross-Reference Auditor
- **Input**: Document with citations
- **Output**: List of reference anomalies
- **Contribution**: Structural integrity of lattice

## Recursive Nature

The model is **recursive** because:

1. **Layer-by-Layer Analysis**: Constitutional → Statutory → Regulatory → Fiscal
2. **Self-Reference**: Documents cite earlier versions of themselves (amendments)
3. **Feedback Loops**: Anomalies at one layer propagate to dependent layers
4. **Iterative Refinement**: Detection rules improve as corpus grows

### Example: Recursive Anomaly Propagation

```
1. Statute X cites Constitutional Amendment Y
2. Amendment Y detector finds no conflict → score += 0
3. Statute X contains fiscal allocation Z
4. Fiscal detector finds missing appropriation → score -= 0.05
5. Regulation W implements Statute X
6. Cross-reference detector finds Statute X citation but with anomaly
7. Propagated anomaly → score -= 0.02
8. Final score for Regulation W = 0.93
```

## Practical Applications

### Use Case 1: Appropriation Trail Auditing

**Scenario**: Verify that a federal contract has complete appropriation lineage.

**Process**:
1. Load contract document
2. Extract budget line item reference
3. Trace to appropriations bill
4. Verify bill passed both chambers
5. Check presidential signature
6. Validate effective dates
7. Compute scalar score based on completeness

**Expected Score**:
- Complete trail: `1.0`
- Missing signature: `0.95`
- Missing appropriations bill: `0.85`
- Orphan contract (no trail): `0.0`

### Use Case 2: Constitutional Conformity Check

**Scenario**: Flag statutes with potentially unconstitutional delegations.

**Process**:
1. Load statute
2. Parse for delegation keywords ("Secretary may", "as determined by")
3. Check if delegation has intelligible principle
4. Verify non-delegation doctrine compliance
5. Compute scalar score

**Expected Score**:
- Clear standards: `1.0`
- Vague delegation: `0.90`
- No standards + broad authority: `0.70`

### Use Case 3: Surveillance Outsourcing Detection

**Scenario**: Identify contracts that outsource surveillance to private vendors.

**Process**:
1. Load contract
2. Scan for surveillance keywords (biometric, monitoring, tracking, data collection)
3. Identify private contractor involvement
4. Check for privacy safeguards (warrants, minimization, oversight)
5. Compute scalar score

**Expected Score**:
- No surveillance: `1.0`
- Surveillance with robust safeguards: `0.95`
- Surveillance with weak safeguards: `0.80`
- Warrantless surveillance outsourced: `0.50`

## Implementation Roadmap

### Phase 1: Foundation (Current)
- [x] Basic scalar scoring (penalty per anomaly)
- [x] Fiscal detector stub
- [x] Constitutional detector stub
- [x] Surveillance detector stub
- [x] Audit engine integration

### Phase 2: Enhanced Heuristics
- [ ] Weighted scoring by severity
- [ ] Appropriation chain analyzer
- [ ] Constitutional delegation keywords
- [ ] Surveillance keyword patterns

### Phase 3: Geometric Analysis
- [ ] Reference graph builder
- [ ] Density and degree analysis
- [ ] Path integrity verification
- [ ] Collapse node detection

### Phase 4: Advanced Modeling
- [ ] Pattern lattice coherence
- [ ] Temporal drift analysis
- [ ] Semantic similarity scoring
- [ ] Machine learning integration

## Testing and Validation

### Unit Tests
- `tests/test_scalar_core.py`: Basic scoring logic
- `tests/test_fiscal_detector.py`: Fiscal anomaly detection
- `tests/test_audit_engine.py`: Integration tests

### Integration Tests
- Full pipeline: load → normalize → detect → score
- Regression tests: known anomaly patterns
- Performance tests: large corpus processing

### Validation Metrics
- **Precision**: % of flagged anomalies that are true positives
- **Recall**: % of true anomalies that are flagged
- **F1 Score**: Harmonic mean of precision and recall

## References

- **Robert Edward Grant's Architectural Principles**: Hierarchical geometry, self-similarity, pattern lattices
- **Audit Methodology**: See `docs/audit-methodology.md`
- **Architecture Overview**: See `docs/ARCHITECTURE.md`
- **Provenance Tracking**: See `docs/DATA_PROVENANCE.md`

## Conclusion

The Recursive Scalar Model provides a **theoretical and practical framework** for detecting anomalies in complex legislative systems. By modeling documents as nodes in a hierarchical lattice and computing coherence scores based on self-similarity and pattern integrity, ODIA can identify:

- Fiscal opacity
- Constitutional violations
- Surveillance overreach
- Structural incoherence
- Fabricated or manipulated documents

The model is **explainable**, **testable**, and **iteratively improvable**, ensuring that detection logic remains transparent and auditable as the system evolves.
