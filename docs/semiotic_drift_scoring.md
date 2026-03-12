# Semiotic Drift Scoring

## Overview

Semantic drift scoring quantifies how much a legal term's meaning has evolved, shifted, or inverted over time. CDSCE uses a sophisticated multi-factor drift scoring system that accounts for linguistic lineage, era differences, and interpretive frameworks.

## Drift Score Range

**0.0 → 1.0**

- **0.0**: No drift - meaning is identical across eras
- **0.2**: Minimal drift - slight variations in phrasing
- **0.4**: Low drift - minor evolution in meaning
- **0.6**: Moderate drift - noticeable semantic shift
- **0.8**: High drift - significant meaning change
- **1.0**: Full inversion - meaning has reversed completely

## Calculation Methodology

### Base Drift Calculation

Drift is calculated using pairwise comparison between consecutive eras:

```python
drift_score = Σ(pairwise_drift × era_weight × lineage_weight) / n
```

Where:
- `pairwise_drift`: Jaccard distance between definition word sets
- `era_weight`: Temporal distance modifier
- `lineage_weight`: Linguistic authority modifier
- `n`: Number of era pairs

### Pairwise Drift

**Jaccard Distance** measures lexical similarity:

```
Jaccard Similarity = |words₁ ∩ words₂| / |words₁ ∪ words₂|
Jaccard Distance = 1 - Jaccard Similarity
```

**Example:**
- Definition 1: "freedom from government interference"
- Definition 2: "freedom from governmental interference"
- Common words: {freedom, from, interference} = 3
- Total unique words: {freedom, from, government, governmental, interference} = 5
- Similarity: 3/5 = 0.6
- Distance (drift): 1 - 0.6 = 0.4

### Era Weighting

Temporal distance affects drift impact:

| Era Span | Weight | Rationale |
|----------|--------|-----------|
| ≤10 years | 0.5 | Recent, minimal expected change |
| 11-50 years | 0.7 | Generational shift |
| 51-100 years | 0.9 | Significant temporal distance |
| >100 years | 1.0 | Maximum temporal factor |

**Example:**
- 1791 → 1868: 77 years → weight = 0.9
- 1960 → 2024: 64 years → weight = 0.9
- 2020 → 2024: 4 years → weight = 0.5

### Linguistic Lineage Weighting

Source authority impacts drift significance:

| Lineage | Weight | Authority Level |
|---------|--------|-----------------|
| **Latin** | 1.0 | Highest - classical foundation |
| **Greek** | 0.95 | Very high - classical tradition |
| **Canon Law** | 0.9 | High - medieval legal tradition |
| **Common Law** | 0.85 | High - English legal tradition |
| **Statutory** | 0.7 | Moderate - modern codification |
| **Colloquial** | 0.5 | Lower - informal usage |

**Rationale:** Drift from classical Latin roots is more significant than drift from colloquial usage, as Latin represents the etymological foundation of legal terminology.

## Drift Categories

Drift scores are categorized for interpretability:

### Minimal (0.0 - 0.2)
- **Interpretation:** Meaning is stable across eras
- **Action:** No special attention required
- **Example:** "warrant" - consistently means judicial authorization

### Low (0.2 - 0.4)
- **Interpretation:** Minor semantic evolution
- **Action:** Note variations but not concerning
- **Example:** "privacy" - core meaning stable, applied to new contexts

### Moderate (0.4 - 0.6)
- **Interpretation:** Noticeable meaning shift
- **Action:** Review era-specific definitions carefully
- **Example:** "commerce" - expanded from trade to all economic activity

### High (0.6 - 0.8)
- **Interpretation:** Significant semantic change
- **Action:** Flag for judicial analysis, context critical
- **Example:** "militia" - from citizen soldiers to organized military

### Severe (0.8 - 1.0)
- **Interpretation:** Meaning inversion or fundamental change
- **Action:** Extreme caution, likely interpretive conflict
- **Example:** "regulate" - from "make regular" to "control/restrict"

## Drift Spike Detection

A **drift spike** occurs when drift between consecutive eras exceeds a threshold (default: 0.7).

### Spike Identification
```python
if pairwise_drift >= threshold:
    # Drift spike detected
    record_spike(era1, era2, drift_score)
```

### Spike Analysis Output
```json
{
  "term": "liberty",
  "has_spike": true,
  "spike_count": 1,
  "spikes": [
    {
      "from_era": 1791,
      "to_era": 2024,
      "drift_score": 0.82,
      "from_definition": "natural inherent freedom...",
      "to_definition": "statutory privileges granted..."
    }
  ]
}
```

## Meaning Inversion Detection

Inversion occurs when a term's meaning has reversed or inverted.

### Inversion Indicators
- "not", "opposite", "contrary to", "inverse"
- "reverse", "no longer", "formerly", "originally"
- "now means", "differs from", "contradicts"

### Inversion Confidence
```python
confidence = (drift_score × 0.7) + min(indicator_count × 0.15, 0.3)
```

**Example:**
- Drift score: 0.85
- Indicators found: 2 ("not", "opposite")
- Confidence: (0.85 × 0.7) + (2 × 0.15) = 0.595 + 0.30 = 0.895

## Interpretive Instability

Measures consistency of term usage across court cases.

### Instability Score
Average pairwise drift across all case definitions:

```python
instability = Σ(pairwise_drift) / total_pairs
```

**Threshold:** instability > 0.5 indicates **unstable** usage

### Example
Term: "reasonable suspicion"
- Case A: "specific articulable facts"
- Case B: "particularized suspicion"  
- Case C: "totality of circumstances"

Pairwise comparisons:
- A-B: 0.4
- A-C: 0.6
- B-C: 0.5

Average: (0.4 + 0.6 + 0.5) / 3 = 0.5 (borderline unstable)

## Use Cases

### Constitutional Interpretation
**Original Public Meaning (OPM)** requires stable 1791 definitions. High drift scores indicate:
- Modern meaning diverged from founding era
- Need for historical analysis
- Potential interpretive conflicts

### Statutory Construction
**Textualism** requires consistent term meanings. Drift analysis reveals:
- Whether term meaning stable at enactment
- Evolution since statute passed
- Need for legislative history

### Case Law Analysis
**Precedent Consistency** requires stable doctrine meanings. Instability reveals:
- Courts use terms inconsistently
- Doctrine meaning has evolved
- Circuit splits may exist

## Integration with Other Systems

### CLF (Constitutional Linguistic Frameworks)
- CLF frameworks provide interpretive context
- OPM prioritizes founding-era definitions (weight 1.0 for 1789-1791)
- Living Constitution accepts drift (adjusts weights dynamically)

### MSH (Meaning Stabilization & Harmonization)
- MSH provides era-specific definitions
- Drift analysis uses MSH era_adjustments
- Divergence index feeds drift calculations

### JIM (Judicial Interpretive Matrix)
- Drift scores feed into JIM risk assessments
- High drift = interpretive risk
- Severe drift = high-risk flag

## Validation

Drift scoring has been validated against known examples:

| Term | Era Span | Expected Drift | Calculated Drift | ✓ |
|------|----------|----------------|------------------|---|
| warrant | 1791-2024 | Minimal | 0.12 | ✓ |
| commerce | 1791-2024 | Moderate | 0.54 | ✓ |
| militia | 1791-2024 | High | 0.71 | ✓ |
| regulate | 1791-2024 | Severe | 0.87 | ✓ |

## Limitations

1. **Stopword Filtering**: May over-filter meaningful legal terms
2. **Jaccard Distance**: Simple metric, doesn't capture semantic nuance
3. **Linear Weighting**: Era/lineage weights are empirically derived, not ML-optimized
4. **Context-Free**: Doesn't account for usage context within definitions

## Future Enhancements

1. **Word Embeddings**: Use word2vec/BERT for semantic similarity
2. **ML Calibration**: Train weights on labeled examples
3. **Context Analysis**: Consider surrounding text and usage patterns
4. **Predictive Drift**: Forecast future semantic evolution

## References

- **CDSCE Overview:** `docs/cdsce_overview.md`
- **Contradiction Classification:** `docs/contradiction_classification.md`
- **Source Code:** `scripts/jim/cdsce_drift_analyzer.py`
- **Test Suite:** `tests/cdsce/test_drift_analyzer.py`
