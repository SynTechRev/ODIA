# Contradiction Classification

## Overview

CDSCE detects and classifies six types of contradictions across legal dictionaries, doctrines, interpretive frameworks, eras, and etymological sources. Each contradiction type has distinct characteristics, severity weighting, and resolution strategies.

## Contradiction Types

### 1. Lexical Contradiction

**Definition:** Two or more dictionaries provide incompatible definitions of the same term at the word level.

**Weight:** 0.7  
**Severity Range:** 0.7 - 1.0

**Detection Criteria:**
- Semantic similarity < 0.25 (Jaccard distance)
- Presence of contradiction markers ("not", "contrary to", "opposite")

**Example:**
```json
{
  "term": "liberty",
  "conflict_type": "lexical",
  "sources_involved": ["Black's", "Bouvier's"],
  "severity": 0.82,
  "notes": "Black's defines civil liberty; Bouvier's defines natural liberty; meanings diverge post-1900"
}
```

**Resolution Strategy:**
- Apply source authority weights (Black's: 0.35, Bouvier's: 0.20)
- Consider era-specific context
- Check CLF framework guidance

---

### 2. Doctrinal Contradiction

**Definition:** Legal doctrine interpretations conflict or provide incompatible frameworks for term analysis.

**Weight:** 0.9  
**Severity:** Fixed at 0.85

**Detection Criteria:**
- Known conflicting doctrine pairs:
  - strict_scrutiny ↔ rational_basis
  - originalism ↔ living_constitution
  - textualism ↔ purposivism

**Example:**
```json
{
  "term": "liberty",
  "conflict_type": "doctrinal",
  "sources_involved": ["strict_scrutiny", "rational_basis"],
  "severity": 0.85,
  "notes": "Strict scrutiny requires compelling interest; rational basis accepts any legitimate purpose"
}
```

**Resolution Strategy:**
- Identify applicable standard of review
- Consider constitutional provision involved
- Apply ACE weight balancing

---

### 3. Interpretive Contradiction

**Definition:** Constitutional interpretation frameworks provide conflicting guidance on term meaning.

**Weight:** 0.85  
**Severity:** Fixed at 0.8

**Detection Criteria:**
- Known conflicting framework pairs:
  - originalism ↔ living_constitutionalism
  - textualism ↔ purposivism
  - strict_construction ↔ loose_construction
  - framers_intent ↔ contemporary_interpretation

**Example:**
```json
{
  "term": "commerce",
  "conflict_type": "interpretive",
  "sources_involved": ["originalism", "living_constitutionalism"],
  "severity": 0.8,
  "notes": "Originalism: 1791 trade meaning; Living Constitution: expanded to all economic activity"
}
```

**Resolution Strategy:**
- Check CLF-v1 framework weights
- Consider Supreme Court era
- Apply JIM framework selection logic

---

### 4. Temporal Contradiction

**Definition:** A term's meaning has changed incompatibly between two eras.

**Weight:** 0.75  
**Severity Range:** 0.75 - 1.0 (scaled by semantic distance)

**Detection Criteria:**
- Semantic similarity between eras < 0.3
- Time span typically >100 years

**Example:**
```json
{
  "term": "regulate",
  "conflict_type": "temporal",
  "sources_involved": ["era_1791", "era_2024"],
  "severity": 0.87,
  "details": {
    "era1": {"year": 1791, "definition": "to make regular, orderly"},
    "era2": {"year": 2024, "definition": "to control, restrict by law"},
    "time_span_years": 233
  }
}
```

**Resolution Strategy:**
- For constitutional terms, prefer founding-era meaning (OPM)
- For statutory terms, use meaning at enactment
- Consider doctrine evolution via CLEP-v2

---

### 5. Constitutional Framework Contradiction

**Definition:** Multiple CLF frameworks provide conflicting interpretive guidance for the same term.

**Weight:** 0.8  
**Severity:** Fixed at 0.8

**Detection Criteria:**
- Multiple frameworks reference term
- Frameworks are in known conflict pairs
- Framework weights differ significantly

**Example:**
```json
{
  "term": "cruel and unusual",
  "conflict_type": "constitutional_framework",
  "sources_involved": ["framers_intent", "contemporary_interpretation"],
  "severity": 0.8,
  "details": {
    "framework1": {"name": "framers_intent", "era": "founding", "weight": 0.25},
    "framework2": {"name": "contemporary_interpretation", "era": "modern", "weight": 0.15}
  }
}
```

**Resolution Strategy:**
- Sum framework weights
- Higher total weight = preferred interpretation
- Consider Supreme Court precedent

---

### 6. Etymological Contradiction

**Definition:** Different etymological roots suggest conflicting meanings for the term.

**Weight:** 0.65  
**Severity:** Fixed at 0.7

**Detection Criteria:**
- Multiple language origins (Latin, Greek, Canon Law)
- Root meanings have semantic similarity < 0.35
- Different language families involved

**Example:**
```json
{
  "term": "jurisdiction",
  "conflict_type": "etymological",
  "sources_involved": ["latin", "canon_law"],
  "severity": 0.7,
  "details": {
    "etymology1": {
      "language": "latin",
      "root": "ius dicere",
      "meaning": "to speak the law"
    },
    "etymology2": {
      "language": "canon_law",
      "root": "jurisdictio",
      "meaning": "ecclesiastical authority"
    }
  }
}
```

**Resolution Strategy:**
- Prefer legal Latin over other sources (weight 1.0)
- Consider historical legal context
- Check case law usage patterns

## Severity Calculation

### Base Severity
Each contradiction type has a base severity weight reflecting its interpretive significance.

### Semantic Distance Modifier
For types that vary (lexical, temporal, etymological):

```python
severity = base_severity + (semantic_distance × modifier)
```

Where:
- `semantic_distance`: 1.0 - Jaccard_similarity
- `modifier`: Type-specific multiplier

**Example (Lexical):**
```python
base_severity = 0.7
semantic_distance = 0.8  # Very different definitions
modifier = 0.5

severity = 0.7 + (0.8 × 0.5) = 0.7 + 0.4 = 1.0 (capped at 1.0)
```

### Contradiction Marker Bonus
Explicit contradiction markers add +0.1 to severity:

```python
if has_contradiction_marker:
    severity += 0.1
```

## Contradiction Report Structure

```json
{
  "version": "1.0.0",
  "generated": "2025-12-07T00:00:00Z",
  "total_contradictions": 42,
  "by_type": {
    "lexical": 12,
    "doctrinal": 8,
    "interpretive": 7,
    "temporal": 9,
    "constitutional_framework": 4,
    "etymological": 2
  },
  "by_severity": {
    "high": 15,   // ≥0.8
    "medium": 18, // 0.5-0.8
    "low": 9      // <0.5
  },
  "statistics": {
    "average_severity": 0.73,
    "max_severity": 0.95,
    "min_severity": 0.45
  },
  "contradictions": [...]
}
```

## Resolution Strategies

### General Principles

1. **Source Authority**: Apply dictionary source weights
2. **Temporal Priority**: Founding-era for constitutional, enactment for statutory
3. **Framework Weights**: Sum CLF weights for competing interpretations
4. **Case Law Precedent**: Supreme Court usage takes precedence
5. **Etymology Foundation**: Latin roots highest authority

### Decision Matrix

| Contradiction Type | Primary Resolution | Secondary Factor |
|-------------------|-------------------|------------------|
| Lexical | Source weights | Era context |
| Doctrinal | Applicable standard | Constitutional provision |
| Interpretive | Framework weights | Supreme Court era |
| Temporal | Original meaning (OPM) | Doctrine evolution |
| Constitutional Framework | Weight summation | Precedent |
| Etymological | Latin preference | Legal tradition |

## Integration with Other Systems

### JIM (Judicial Interpretive Matrix)
- Contradictions feed into JIM risk scoring
- High-severity contradictions = high interpretive risk
- Multiple contradictions = compound risk

### ACE (Anomaly Correlation Engine)
- Contradictions classified as "semantic_misalignment" anomalies
- Severity maps to ACE anomaly scores
- Cross-referenced with metadata irregularities

### MSH (Meaning Stabilization & Harmonization)
- MSH attempts to resolve contradictions via weighted harmonization
- Unresolvable contradictions flagged for human review
- Divergence index tracks contradiction severity over time

### CLF (Constitutional Linguistic Frameworks)
- Framework contradictions inform CLF selection logic
- Competing frameworks trigger multi-framework analysis
- Resolution recorded in CLF audit trail

## Use Cases

### Constitutional Analysis
Identify competing interpretive frameworks for key terms:
- "liberty" → substantive due process vs. negative rights
- "commerce" → narrow trade vs. broad economic activity

### Statutory Construction
Detect temporal meaning shifts since statute enactment:
- "broadcast" (1934 Communications Act) → modern streaming?
- "vehicle" (National Parks Act) → drones?

### Case Law Consistency
Find doctrinal contradictions across circuits:
- "reasonable suspicion" standards vary
- "exigent circumstances" applied inconsistently

## Validation

Contradiction detection validated against known conflicts:

| Term | Contradiction Type | Detected | Severity | ✓ |
|------|-------------------|----------|----------|---|
| liberty | Lexical | Yes | 0.82 | ✓ |
| regulate | Temporal | Yes | 0.87 | ✓ |
| commerce | Interpretive | Yes | 0.80 | ✓ |
| militia | Temporal | Yes | 0.76 | ✓ |

## Future Enhancements

1. **ML Severity Prediction**: Train models on labeled contradictions
2. **Auto-Resolution**: Propose resolutions based on context
3. **Contradiction Chains**: Track contradictions across related terms
4. **Visualization**: Network graphs of conflicting interpretations

## References

- **CDSCE Overview:** `docs/cdsce_overview.md`
- **Drift Scoring:** `docs/semiotic_drift_scoring.md`
- **Source Code:** `scripts/jim/cdsce_contradiction_engine.py`
- **Test Suite:** `tests/cdsce/test_contradiction_engine.py`
