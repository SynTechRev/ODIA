# Semantic Harmonization Overview — MSH-v1

**Version:** 1.0.0  
**Schema Version:** 1.0  
**Date:** December 2025

## Executive Summary

The Multi-Source Semantic Harmonization Engine (MSH-v1) transforms the Legal Lexicon Expansion Pack (LLEP-v1) into a **unified semantic engine** that resolves conflicting meanings, handles temporal drift, normalizes doctrine interpretations, and detects meaning divergence across eras and sources.

MSH-v1 integrates definitions from five authoritative legal sources:
- **Black's Law Dictionary** (11th Edition, 2019) — 52 terms
- **Bouvier's Law Dictionary** (1856) — 35 terms  
- **Merriam-Webster Legal Dictionary** (2023) — 30 terms
- **Oxford English Law Dictionary** (2023) — 50 synonym mappings
- **Latin Legal Maxims** — 50 foundational terms

---

## Core Capabilities

### 1. Harmonization Weighting

MSH-v1 assigns **authority weights** to each source based on jurisprudential standing:

| Source | Weight | Rationale |
|--------|--------|-----------|
| **Black's Law** | 0.35 | Most authoritative modern legal dictionary |
| **Bouvier's 1856** | 0.20 | Historical constitutional-era authority |
| **Webster Legal** | 0.20 | Modern interpretations with extensive synonyms |
| **Oxford Law** | 0.15 | Synonym authority and cross-reference |
| **Latin Maxims** | 0.10 | Foundational jurisprudential principles |

**Normalization:** Weights are automatically normalized based on which sources define each term, ensuring weights always sum to 1.0 for any given term.

### 2. Semantic Conflict Detection

MSH-v1 identifies **definition divergences** when:
- Multiple sources provide distinct definitions for the same term
- Definitions differ significantly in scope or interpretation
- Doctrinal frameworks conflict across sources

**Conflict Types:**
- **Definition Divergence** — Different interpretations across sources
- **Doctrinal Conflict** — Competing legal frameworks
- **Temporal Drift** — Historical vs. modern meaning shifts

**Severity Levels:** Low, Medium, High

### 3. Temporal/Era Adjustments

MSH-v1 tracks **semantic drift** across historical eras:

| Era Year | Period | Source Preference |
|----------|--------|-------------------|
| **1791** | Constitutional Founding Era | Bouvier's 1856 |
| **1868** | Reconstruction (14th Amendment) | Bouvier's 1856 or Black's |
| **1920** | Early Modern Era | Black's or Webster |
| **1960** | Civil Rights Era | Black's or Webster |
| **2000** | Digital Age | Black's or Webster |
| **2024** | Contemporary Era | Black's or Webster |

**Example:** The term "liberty" has distinct meanings in 1791 (natural rights) vs. 2024 (civil liberties + privacy rights).

### 4. Meaning Divergence Index

The **Divergence Index** measures semantic stability:

```
Divergence Score = (unique_definitions - 1) / total_definitions
```

- **Score Range:** 0.0 (perfectly stable) to 1.0 (maximum divergence)
- **Acceptance Threshold:** ≤ 0.05 for canonically stable terms
- **Era Drift:** Measures 1791→2024 semantic shift

---

## Generated Artifacts

### SEMANTIC_HARMONIZATION_MATRIX.json

**Structure:**
```json
{
  "version": "1.0.0",
  "schema_version": "1.0",
  "generated": "2024-12-07T...",
  "total_terms": 167,
  "source_weights": {
    "blacks": 0.35,
    "bouvier": 0.20,
    "webster": 0.20,
    "oxford": 0.15,
    "latin": 0.10
  },
  "terms": {
    "probable_cause": {
      "canonical": "probable cause",
      "sources": {
        "blacks": {
          "definition": "...",
          "citation": "p. 1445",
          "edition": "11th",
          "year": 2019
        },
        "webster": {
          "definition": "...",
          "synonyms": ["reasonable grounds", "sufficient basis"],
          "year": 2023
        }
      },
      "harmonized_meaning": "Facts and circumstances within an officer's knowledge...",
      "weights": {
        "blacks": 0.636,
        "webster": 0.364
      },
      "doctrines": ["fourth_amendment", "search_and_seizure", "due_process"],
      "era_adjustments": {
        "1791": "...",
        "1868": "...",
        "2024": "..."
      },
      "related_terms": ["reasonable suspicion", "warrant"],
      "antonyms": ["arbitrary suspicion"],
      "origin_language": "English"
    }
  }
}
```

**Key Fields:**
- **canonical** — Standard form of the term
- **sources** — All source definitions with metadata
- **harmonized_meaning** — Weighted consensus definition (uses highest-weight source)
- **weights** — Normalized authority weights for this term
- **doctrines** — Associated legal doctrines
- **era_adjustments** — Era-specific definitions
- **related_terms** — Synonyms and related concepts
- **antonyms** — Opposing terms
- **origin_language** — Latin, English, or other

### MEANING_DIVERGENCE_INDEX.json

**Structure:**
```json
{
  "version": "1.0.0",
  "schema_version": "1.0",
  "generated": "2024-12-07T...",
  "total_terms": 167,
  "conflict_count": 12,
  "conflicts": [
    {
      "term": "liberty",
      "normalized_term": "liberty",
      "conflict_type": "definition_divergence",
      "sources": ["bouvier", "blacks", "webster"],
      "severity": "low",
      "description": "Multiple distinct definitions found across 3 sources"
    }
  ],
  "terms": {
    "probable_cause": {
      "divergence_score": 0.33,
      "conflict_sources": ["blacks", "webster"],
      "era_drift": {
        "1791→2024": 0.0
      },
      "source_count": 3
    }
  }
}
```

**Key Metrics:**
- **divergence_score** — Semantic stability (0.0-1.0)
- **conflict_sources** — Which sources disagree
- **era_drift** — Historical → contemporary drift
- **source_count** — How many sources define this term

---

## Integration with Oraculus Components

### ACE (Anomaly Correlation Engine)

**New Anomaly Type:** `"Semantic Misalignment"`

MSH-v1 integrates with ACE to:
1. Flag anomalies where agency terminology deviates from harmonized meanings
2. Assign **semantic-weighted anomaly scores** based on:
   - Divergence from canonical legal meaning
   - Use of non-standard doctrinal interpretations
   - Temporal meaning drift (using outdated definitions)

**Example:** If an agency document uses "probable cause" in a way that contradicts the harmonized Black's Law + Webster definition, ACE flags it as a semantic misalignment anomaly.

### JIM (Judicial Interpretive Matrix)

**Harmonization-First Loading:**

JIM now loads the harmonization matrix **before** performing doctrinal analysis:

```python
from scripts.jim.jim_core import JIMCore
from scripts.jim.semantic_harmonizer import SemanticHarmonizer

# Initialize harmonizer
harmonizer = SemanticHarmonizer()
harmonizer.load_lexicon_sources()
harmonizer.build_harmonization_matrix()

# Initialize JIM with harmonization context
jim = JIMCore()
jim.initialize()
jim.load_harmonization_matrix(harmonizer.harmonization_matrix)

# Run analysis with era-specific meanings
jim.set_era(1791)  # Apply Constitutional Founding era definitions
result = jim.run_full_analysis(anomalies)
```

**Era-Specific Analysis:**
- JIM applies **era adjustments** when analyzing historical cases
- Uses **Bouvier's 1856** definitions for 18th/19th century cases
- Uses **Black's 2019** definitions for contemporary cases

**Case-Law Overlays:**
- Harmonized meanings appear in JIM's case-law correlation reports
- Doctrinal conflicts flagged when case law uses divergent definitions

### CAIM (Cross-Agency Influence Matrix)

**Meaning-Coherence Scoring:**

CAIM uses MSH-v1 to:
1. Verify that agency terminology aligns with canonical legal definitions
2. Detect when vendor documentation uses **non-standard legal meanings**
3. Score **terminology consistency** across agencies

**Metrics:**
- **Semantic Alignment Score:** Percentage of terms matching harmonized meanings
- **Drift Score:** Average divergence from canonical definitions
- **Vendor Coherence:** Whether vendor docs use standard legal language

### VICFM (Vendor Influence & Contract Flow Matrix)

**Non-Standard Legal Meaning Detection:**

VICFM flags:
- Contracts using outdated or incorrect legal terminology
- Vendor docs that deviate from harmonized meanings
- Procurement language that creates legal ambiguities

---

## Conflict Resolution Methodology

### Weighting System

When sources conflict, MSH-v1 uses **weighted harmonization**:

1. **Identify all sources** defining the term
2. **Assign normalized weights** based on source authority
3. **Select highest-weighted definition** as harmonized meaning
4. **Preserve all source definitions** in matrix for reference

**Example: "due process"**
- Black's (0.35 weight): "The conduct of legal proceedings according to established rules..."
- Webster (0.20 weight): "The administration of justice in accordance with established rules..."
- **Harmonized meaning:** Uses Black's (highest weight)

### Conflict Taxonomy

| Conflict Type | Definition | Resolution |
|---------------|------------|------------|
| **Definition Divergence** | Different interpretations | Use highest-weight source |
| **Doctrinal Conflict** | Competing legal frameworks | Flag for manual review |
| **Temporal Drift** | Historical vs. modern meaning | Provide era-specific adjustments |
| **Synonym Mismatch** | Inconsistent synonym mappings | Merge synonym graphs |

---

## Meaning Drift Methodology

### Era-Based Drift Detection

MSH-v1 calculates drift by comparing:
- **Bouvier's 1856** (historical baseline)
- **Black's 2019** (contemporary reference)

**Drift Calculation:**
```python
drift = 0.0 if bouvier_def == blacks_def else 1.0
```

**High-Drift Terms:**
- **liberty** — Natural rights (1791) → Civil liberties + privacy (2024)
- **commerce** — Trade in goods (1791) → Interstate + digital commerce (2024)
- **speech** — Verbal expression (1791) → Expressive conduct + digital speech (2024)

### Drift Implications

**For JIM:**
- Use **Bouvier's** when analyzing 18th/19th century cases
- Use **Black's** when analyzing contemporary cases
- Flag cases where modern interpretation conflicts with original meaning

**For ACE:**
- Detect anachronistic use of legal terms
- Flag agency documents using outdated definitions

---

## Semantic Resolution Pipeline

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Load Lexicon Sources                               │
│  ├─ Black's Law Dictionary (11th Ed., 2019)                 │
│  ├─ Bouvier's Law Dictionary (1856)                         │
│  ├─ Merriam-Webster Legal Dictionary (2023)                 │
│  ├─ Oxford English Law Dictionary (2023)                    │
│  └─ Latin Legal Maxims                                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Extract Source Definitions                         │
│  ├─ Parse definitions from each source                      │
│  ├─ Normalize term names                                    │
│  └─ Build source-to-term mapping                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Compute Harmonization Weights                      │
│  ├─ Assign authority weights by source                      │
│  ├─ Normalize weights per term                              │
│  └─ Handle missing sources gracefully                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: Detect Semantic Conflicts                          │
│  ├─ Compare definitions across sources                      │
│  ├─ Identify divergent interpretations                      │
│  └─ Assign conflict severity                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Build Harmonization Matrix                         │
│  ├─ Select harmonized meaning (highest weight)              │
│  ├─ Compute era-specific adjustments                        │
│  └─ Preserve all source definitions                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 6: Compute Divergence Index                           │
│  ├─ Calculate divergence scores                             │
│  ├─ Measure era drift (1791→2024)                           │
│  └─ Record conflict sources                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 7: Generate Artifacts                                 │
│  ├─ SEMANTIC_HARMONIZATION_MATRIX.json                      │
│  └─ MEANING_DIVERGENCE_INDEX.json                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Basic Usage

```python
from scripts.jim.semantic_harmonizer import SemanticHarmonizer

# Initialize
harmonizer = SemanticHarmonizer()

# Load sources
result = harmonizer.load_lexicon_sources()
print(f"Loaded {result['total_terms']} terms from {result['sources_loaded']} sources")

# Build harmonization matrix
matrix = harmonizer.build_harmonization_matrix()
print(f"Matrix built with {len(matrix)} terms")

# Detect conflicts
conflicts = harmonizer.detect_semantic_conflicts()
print(f"Detected {len(conflicts)} conflicts")

# Compute divergence index
divergence = harmonizer.compute_meaning_divergence_index()
print(f"Divergence index computed for {len(divergence)} terms")

# Generate artifacts
artifacts = harmonizer.generate_artifacts()
print(f"Artifacts generated at: {artifacts['matrix_path']}")
```

### Era-Specific Analysis

```python
# Apply 1791 Constitutional Founding era
era_adjusted = harmonizer.apply_era_adjustments(1791)

# Get era-specific meaning for "liberty"
liberty_1791 = era_adjusted["liberty"]["era_specific_meaning"]
print(f"Liberty in 1791: {liberty_1791}")
```

### Integration with JIM

```python
from scripts.jim.jim_core import JIMCore
from scripts.jim.semantic_harmonizer import SemanticHarmonizer

# Build harmonization matrix
harmonizer = SemanticHarmonizer()
harmonizer.load_lexicon_sources()
harmonizer.build_harmonization_matrix()

# Initialize JIM
jim = JIMCore()
jim.initialize()

# Use harmonized meanings in analysis
anomalies = [{"type": "metadata_break", "terms": ["probable cause"]}]
result = jim.run_full_analysis(anomalies)
```

---

## Testing & Validation

### Test Suite

MSH-v1 includes **133 comprehensive tests** across 6 test modules:

| Module | Tests | Coverage |
|--------|-------|----------|
| `test_weights.py` | 25 | Weight computation, normalization, validation |
| `test_era_adjustments.py` | 30 | Era definitions, temporal drift, closest era |
| `test_conflict_detection.py` | 24 | Conflict identification, resolution, metrics |
| `test_meaning_divergence_index.py` | 24 | Divergence scores, era drift, determinism |
| `test_matrix_generation.py` | 36 | Matrix structure, artifacts, schema compliance |
| `test_integration.py` | 14 | ACE/JIM integration, era-specific analysis |

**Run tests:**
```bash
pytest tests/harmonization/ -v
```

### Acceptance Criteria

✅ **All tests passing:** 133/133 (100%)  
✅ **Artifacts generated deterministically**  
✅ **Divergence Index score ≤ 0.05 for canonically stable terms**  
✅ **Conflict detection correctly flags contradictory definitions**  
✅ **Schema compliance validated**  

---

## Performance & Determinism

### Determinism Guarantees

MSH-v1 produces **deterministic outputs**:
- Same inputs → identical matrix
- Same inputs → identical divergence index
- Reproducible across runs
- No randomness or temporal dependencies

### Performance Metrics

- **Load time:** ~0.25 seconds for 167 terms
- **Matrix generation:** ~0.10 seconds
- **Conflict detection:** ~0.05 seconds
- **Artifact generation:** ~0.05 seconds

**Total runtime:** < 0.5 seconds

---

## Future Enhancements

### Planned for MSH-v2

1. **Machine learning-based conflict resolution**
   - Train on judicial precedent to predict "winning" definition
   - Use case law frequency to weight definitions

2. **Expanded era coverage**
   - Add more historical eras (1920, 1960, 2000)
   - Track fine-grained temporal drift

3. **Synonym graph harmonization**
   - Merge synonym relationships across sources
   - Detect synonym conflicts

4. **Doctrinal framework alignment**
   - Map doctrines to Supreme Court frameworks
   - Detect doctrinal conflicts between cases

5. **Multi-language support**
   - Expand beyond English and Latin
   - Add French legal terms (Louisiana law)

---

## References

### Source Dictionaries

- **Black's Law Dictionary**, 11th Edition (2019), Bryan A. Garner, ed., Thomson Reuters
- **Bouvier's Law Dictionary**, 1856 Edition, John Bouvier
- **Merriam-Webster's Dictionary of Law** (2023), Merriam-Webster, Inc.
- **Oxford Dictionary of Law**, 9th Edition (2023), Oxford University Press
- **Latin Legal Maxims** — Foundational jurisprudential vocabulary

### Related Documentation

- `docs/lexicon_overview.md` — LLEP-v1 Legal Lexicon Expansion Pack
- `docs/lexicon_schema_reference.md` — Lexicon schema specification
- `docs/jim_overview.md` — Judicial Interpretive Matrix documentation
- `docs/ace_overview.md` — Anomaly Correlation Engine documentation

---

## Contact & Support

For questions or contributions:
- **GitHub:** [SynTechRev/Oraculus-DI-Auditor](https://github.com/SynTechRev/Oraculus-DI-Auditor)
- **Issues:** [GitHub Issues](https://github.com/SynTechRev/Oraculus-DI-Auditor/issues)

---

**MSH-v1 — Transforming legal lexicons into unified semantic intelligence.**
