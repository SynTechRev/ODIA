# CDSCE Overview - Cross-Dictionary Semiotic Correlation Engine v1

## Executive Summary

CDSCE-v1 (Cross-Dictionary Semiotic Correlation Engine) is the **semantic fusion layer** for Oraculus, providing unprecedented cross-dictionary intelligence that correlates legal meanings across time, sources, and traditions. CDSCE becomes the *interpreter of interpreters*, revealing how legal meanings relate, conflict, evolve, or degrade across:

- Legal dictionaries (Black's, Bouvier's, Webster, Oxford, Latin)
- Case law doctrines  
- Etymology (Latin, Greek, Canon Law)
- Era-based meaning shifts (1789→2025)
- Constitutional linguistic frameworks (CLF-v1)
- JIM semantic weights
- MSH harmonization layers

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                   CDSCE Engine Core                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Multi-Dictionary Correlation System               │ │
│  │  • Black's Law Dictionary (11th ed)                │ │
│  │  • Bouvier's Law Dictionary (1856)                 │ │
│  │  • Merriam-Webster Legal                           │ │
│  │  • Oxford Law Dictionary                           │ │
│  │  • Latin Legal Maxims                              │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Etymology Integration (LGCEP-v1)                  │ │
│  │  • Latin roots                                     │ │
│  │  • Greek roots                                     │ │
│  │  • Canon Law origins                               │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Case Law & Doctrine (CLEP-v2)                     │ │
│  │  • 159 Supreme Court cases                         │ │
│  │  • 57 doctrinal frameworks                         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Constitutional Frameworks (CLF-v1)                │ │
│  │  • 10 interpretive methods                         │ │
│  │  • Era-specific analysis                           │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Analysis & Detection Layer                  │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Drift Analyzer  │  │ Anomaly Detector│              │
│  │ • 0.0→1.0 score │  │ • 6 anomaly types│             │
│  │ • Era weighting │  │ • Severity scoring│            │
│  └─────────────────┘  └─────────────────┘              │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Contradiction   │  │ Graph Builder   │              │
│  │ Engine          │  │ • 5 graph types │              │
│  │ • 6 types       │  │ • Clusters      │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     Output Layer                         │
│  • SEMIOTIC_CORPUS.json                                 │
│  • SEMIOTIC_ANOMALY_INDEX.json                          │
│  • SEMIOTIC_GRAPH_INDEX.json                            │
└─────────────────────────────────────────────────────────┘
```

## Key Capabilities

### 1. Multi-Dictionary Correlation

CDSCE correlates every term across all available sources, creating a **unified semantic map** that shows:

- Which dictionaries define a term
- How definitions align or conflict
- Source authority weights
- Era-specific variations
- Etymological foundations

**Example Correlation Chain:**
```
liberty → 
  ├─ Black's (2019): "freedom from government interference"
  ├─ Bouvier's (1856): "natural inherent freedom from restraint"
  ├─ Webster (2023): "state of being free within society"
  ├─ Latin: "libertas" = "freedom, independence"
  └─ Doctrine: due_process, equal_protection
```

### 2. Semiotic Anomaly Detection

CDSCE detects six types of anomalies:

| Anomaly Type | Severity | Description |
|-------------|----------|-------------|
| **Contradiction** | 0.80 | Two dictionaries define term incompatibly |
| **Doctrine Meaning Inversion** | 0.90 | Doctrine meaning reversed over time |
| **Constitutional Framework Conflict** | 0.80 | CLF frameworks provide conflicting guidance |
| **Temporal Contradiction** | 0.75 | Meaning changed incompatibly over time |
| **Cross-Dictionary Conflict** | 0.75 | Competing roots or philosophical origins |
| **Semantic Drift Spike** | 0.70 | Sharp divergence from classical meaning |
| **Etymology Divergence** | 0.65 | Lost connection to etymological roots |
| **Interpretive Instability** | 0.60 | Courts use word inconsistently |

### 3. Semantic Drift Analysis

**Drift Score Range:** 0.0 (no drift) → 1.0 (full meaning inversion)

**Weighting Factors:**
- **Linguistic lineage:** Latin (1.0), Greek (0.95), Canon Law (0.9), Common Law (0.85), Statutory (0.7), Colloquial (0.5)
- **Era difference:** ≤10 years (0.5), ≤50 years (0.7), ≤100 years (0.9), >100 years (1.0)
- **CLF interpretive method:** Varies by framework

**Drift Categories:**
- **Minimal** (0.0–0.2): Term meaning stable
- **Low** (0.2–0.4): Minor evolution
- **Moderate** (0.4–0.6): Noticeable shift
- **High** (0.6–0.8): Significant change
- **Severe** (0.8–1.0): Meaning inversion

### 4. Contradiction Detection

CDSCE identifies six types of contradictions:

1. **Lexical**: Dictionary definitions conflict at word level
2. **Doctrinal**: Legal doctrine interpretations conflict
3. **Interpretive**: Constitutional interpretation methods conflict
4. **Temporal**: Meaning changed incompatibly over time
5. **Constitutional Framework**: CLF frameworks conflict
6. **Etymological**: Root origins suggest conflicting meanings

### 5. Graph Generation

CDSCE builds five types of semantic graphs:

- **Synonym Graph**: Terms with similar meanings
- **Antonym Graph**: Terms with opposite meanings
- **Etymology Lineage Graph**: Etymological relationships and derivations
- **Doctrine-Meaning Graph**: Doctrines mapped to terms
- **Concept Clusters**: Groups of semantically related terms

## Integration Points

### Input Systems

1. **LLEP-v1** (Legal Lexicon Expansion Pack)
   - 167 terms across 5 dictionaries
   - Provides base definitions

2. **LGCEP-v1** (Latin, Greek, Canon Etymology Pack)
   - Etymology roots and lineage
   - Classical meanings

3. **CLEP-v2** (Case Law Expansion Pack)
   - 159 Supreme Court cases
   - 57 doctrinal frameworks

4. **CLF-v1** (Constitutional Linguistic Frameworks)
   - 10 interpretive methods
   - Era-specific guidance

5. **MSH** (Meaning Stabilization & Harmonization)
   - Semantic weights
   - Era adjustments
   - Divergence scores

### Output Systems

1. **JIM** (Judicial Interpretive Matrix)
   - Receives semiotic correlations
   - Uses for risk scoring

2. **ACE** (Anomaly Correlation Engine)
   - Receives semiotic anomalies
   - Correlates with other anomaly types

## Data Structures

### Semiotic Corpus
```json
{
  "version": "1.0.0",
  "term": "liberty",
  "dictionary_sources": [...],
  "etymology_lineage": [...],
  "doctrinal_mappings": [...],
  "era_definitions": {...},
  "framework_context": [...],
  "semantic_drift": {...},
  "contradictions": [...],
  "correlation_strength": 0.85
}
```

### Anomaly Index
```json
{
  "total_anomalies": 42,
  "by_term": {...},
  "by_type": {...},
  "statistics": {
    "average_severity": 0.73,
    "high_severity_count": 15
  }
}
```

### Graph Index
```json
{
  "synonym_graph": {...},
  "antonym_graph": {...},
  "etymology_graph": {...},
  "doctrine_graph": {...},
  "concept_clusters": [...]
}
```

## Usage

### Initialize CDSCE
```python
from scripts.jim.cdsce_engine import CDSCEEngine

engine = CDSCEEngine()
result = engine.initialize()

if result["success"]:
    print(f"Loaded {result['components']['lexicon_terms']} terms")
```

### Correlate a Term
```python
correlation = engine.correlate_term("liberty")

print(f"Found {len(correlation['dictionary_sources'])} sources")
print(f"Correlation strength: {correlation['correlation_strength']}")
```

### Analyze Semantic Drift
```python
from scripts.jim.cdsce_drift_analyzer import CDSCEDriftAnalyzer

analyzer = CDSCEDriftAnalyzer()
drift_report = analyzer.generate_drift_report("liberty", correlation)

print(f"Drift score: {drift_report['overall_drift_score']}")
print(f"Category: {drift_report['drift_category']}")
```

### Detect Contradictions
```python
from scripts.jim.cdsce_contradiction_engine import CDSCEContradictionEngine

contradiction_engine = CDSCEContradictionEngine()
contradictions = contradiction_engine.scan_term_contradictions("liberty", correlation)

print(f"Found {len(contradictions)} contradictions")
```

### Build Semantic Graphs
```python
from scripts.jim.cdsce_graph_builder import CDSCEGraphBuilder

builder = CDSCEGraphBuilder()
graphs = builder.build_all_graphs(corpus)

print(f"Etymology nodes: {graphs['etymology_graph']['node_count']}")
print(f"Concept clusters: {graphs['concept_clusters']['cluster_count']}")
```

## Performance

- **Initialization:** ~2-5 seconds
- **Term correlation:** ~10-50ms per term
- **Corpus generation:** ~5-30 seconds for 167 terms
- **Anomaly detection:** ~50-200ms per term
- **Graph generation:** ~1-5 seconds for full corpus

## Testing

**Test Coverage:** 149 tests across 6 test files

- Drift Analyzer: 36 tests
- Contradiction Engine: 40 tests
- Graph Builder: 23 tests
- CDSCE Engine: 24 tests
- Anomaly Detector: 14 tests
- Integration: 12 tests

## Future Enhancements

1. **Machine Learning Integration**
   - Automated drift prediction
   - Contradiction likelihood scoring

2. **Expanded Sources**
   - Additional legal dictionaries
   - International law sources
   - Historical legal texts

3. **Real-Time Analysis**
   - Live case law monitoring
   - Automatic corpus updates

4. **Visualization**
   - Interactive graph exploration
   - Drift timeline visualization
   - Contradiction network maps

## References

- **CDSCE Schema:** `schemas/cdsce_schema.json`
- **Semiotic Schema:** `legal/semiotics/SEMIOTIC_SCHEMA.json`
- **Drift Scoring:** `docs/semiotic_drift_scoring.md`
- **Contradiction Classification:** `docs/contradiction_classification.md`
- **Graph Structures:** `docs/semiotic_graph_structures.md`

## Version

**CDSCE v1.0.0**
- Schema Version: 1.0
- Released: 2025-12-07
- Status: Production Ready
