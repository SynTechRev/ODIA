# Etymology Pack Overview — LGCEP-v1

**Version:** 1.0.0  
**Schema Version:** 1.0  
**Date:** December 2024

## Executive Summary

The Latin, Greek, and Canonical Etymology Pack (LGCEP-v1) extends JIM's interpretive power by adding multi-era, multi-lingual etymological roots for legal, philosophical, and constitutional terminology. This provides JIM with the ability to trace semantic evolution across 2000+ years of legal tradition, from Classical Greek through Roman Law, Medieval Canon Law, Enlightenment philosophy, and modern jurisprudence.

LGCEP-v1 integrates with:
- **MSH (PR #49)**: Semantic harmonization and meaning-collision detection
- **CLF (PR #50)**: Constitutional linguistic frameworks and interpretation weights  
- **Lexicon (PR #48)**: Multi-source legal dictionary system

---

## Core Capabilities

### 1. Multi-Source Etymology

LGCEP-v1 provides etymological data from three primary traditions:

**Latin Legal Maxims (100 entries)**
- Foundational Latin legal principles and maxims
- Translations and jurisprudential usage
- Doctrinal mappings and citations
- Era attribution (Roman Law, Medieval Common Law)

**Greek Philosophical Roots (130 entries)**
- Classical Greek legal and philosophical roots
- Concept families and semantic relationships
- Philosopher attributions (Plato, Aristotle, Stoics)
- Semantic chains showing evolution

**Canon Law Roots (75 entries)**
- Medieval Canon law principles
- Ecclesiastical sources (Corpus Juris Canonici, Summa Theologica)
- Influence on secular legal doctrines
- Bridge between Roman and modern law

### 2. Harmonized Etymology Matrix

The **ETYMOLOGY_MATRIX.json** harmonizes all sources into unified entries showing:
- Root languages (Latin, Greek, Canon, English)
- Semantic lineage chains across eras
- Drift scores (0.0-1.0) measuring semantic change
- Era-specific meanings (Classical Greek → Modern)
- Legal doctrine mappings
- Scholarly citations

**Example Entry:**
```json
{
  "term": "justice",
  "root_languages": {
    "latin": "iustitia",
    "greek": "dike / dikaiosyne",
    "canon": "ius",
    "english_modern": "justice"
  },
  "semantic_lineage": [
    "dike (δίκη) → dikaiosyne (δικαιοσύνη) → iustitia → justice"
  ],
  "drift_score": 0.42,
  "era_meanings": {
    "classical_greek": "Right order, natural justice, lawsuit",
    "roman_law": "Virtue of giving each their due, legal justice",
    "medieval_canon": "Divine justice tempered with mercy",
    "enlightenment": "Natural rights, social contract justice",
    "modern": "Equal application of law, procedural fairness"
  },
  "legal_doctrines": ["equity", "natural_law", "due_process"]
}
```

### 3. Semantic Drift Analysis

**Drift Score Methodology:**
- **0.0-0.3**: Stable meaning (minimal semantic change)
- **0.3-0.5**: Moderate drift (some evolution in meaning)
- **0.5-1.0**: Significant drift (substantial change in meaning)

**Drift Analysis Capabilities:**
- Calculate semantic stability for any term
- Detect meaning divergence between eras
- Trace concept evolution across historical periods
- Identify terms with stable vs. evolved meanings

### 4. Semantic Lineage Tracing

LGCEP-v1 traces semantic chains showing evolution:

```
dike (δίκη) → dikaiosyne (δικαιοσύνη) → iustitia → justice
nomos (νόμος) → lex → law
eleutheria (ἐλευθερία) → libertas → liberty
```

**Lineage Features:**
- Greek → Latin → English progressions
- Era-specific meaning shifts
- Philosophical influences
- Doctrinal connections

---

## Integration with Existing Systems

### MSH Integration (Semantic Harmonization)

LGCEP-v1 complements MSH by providing:
- **Etymology-based meaning validation**: Verify modern definitions against historical roots
- **Era-specific semantic analysis**: MSH's era adjustments (1791/1868/2024) augmented with full lineage
- **Drift scoring**: Quantify semantic change alongside MSH's divergence scoring
- **Cross-era conflict resolution**: Use etymology to resolve modern meaning conflicts

**Integration Points:**
```python
from scripts.jim.etymology_loader import EtymologyLoader
from scripts.jim.semantic_harmonizer import SemanticHarmonizer

etymology = EtymologyLoader()
etymology.load_all_sources()

harmonizer = SemanticHarmonizer()
harmonizer.load_lexicon_sources()

# Detect drift across MSH eras
drift = etymology.detect_meaning_divergence("justice", "roman_law", "modern")
# Compare with MSH divergence scoring
divergence = harmonizer.calculate_divergence("justice")
```

### CLF Integration (Constitutional Frameworks)

LGCEP-v1 enhances CLF interpretation:
- **Founding-era linguistics**: Trace constitutional terms to 18th-century meanings
- **Original public meaning**: Connect terms to their etymological roots
- **Framers' intent**: Understand words through their historical lineage
- **Reconstruction-era context**: Analyze 14th Amendment terminology

**Doctrine Mapping:**
```python
# Get etymological roots for natural law doctrine
roots = etymology.get_doctrine_etymology("natural_law")
# Returns: ["ius naturale", "physis", "logos", "lex aeterna"]

# Trace evolution of "liberty" for constitutional interpretation
evolution = etymology.trace_concept_evolution("liberty")
# Returns era-by-era meanings from Greek to modern
```

### Lexicon Integration (LLEP-v1)

LGCEP-v1 extends the lexicon system:
- **Latin maxims complement**: Adds etymological depth to existing Latin foundational terms
- **Greek philosophical context**: Provides philosophical roots for legal concepts
- **Canon law bridges**: Connects Roman law to medieval/modern legal traditions
- **Cross-reference network**: Links lexicon entries to etymological origins

**Cross-References:**
```python
# Get cross-references for "justice"
refs = etymology.get_cross_references("justice")
# Returns: ["dike", "dikaiosyne", "iustitia", "ius"]

# Look up Latin maxim
maxim = etymology.get_latin_maxim("stare decisis")
# Get Greek root
root = etymology.get_greek_root("nomos")
# Get Canon root
canon = etymology.get_canon_root("ius naturale")
```

---

## Use Cases

### 1. Constitutional Interpretation

**Scenario:** Interpreting "liberty" in 14th Amendment Due Process Clause

```python
# Trace "liberty" from Greek origins
etymology = loader.get_etymology_for_term("liberty")
evolution = loader.trace_concept_evolution("liberty")

# Compare 1868 meaning with modern meaning
divergence = loader.detect_meaning_divergence("liberty", "enlightenment", "modern")
```

**Result:** Understand if modern "liberty" (including privacy rights) aligns with 1868 "liberty" (primarily physical freedom).

### 2. Natural Law Analysis

**Scenario:** Analyzing natural law foundations in constitutional rights

```python
# Get etymological roots of natural law doctrine
roots = loader.get_doctrine_etymology("natural_law")
# Returns: ["ius naturale", "physis", "logos", "lex aeterna"]

# Trace from Greek physis to modern natural law
physis = loader.get_greek_root("physis")
canon = loader.get_canon_root("ius naturale")
```

**Result:** Trace natural law from Greek φύσις (nature) through Roman/Canon ius naturale to modern constitutional interpretation.

### 3. Judicial Precedent Authority

**Scenario:** Understanding stare decisis doctrine

```python
# Get Latin maxim
maxim = loader.get_latin_maxim("stare decisis")
# Check semantic stability
stability = loader.calculate_semantic_stability("precedent")
# Get semantic lineage
lineage = loader.get_semantic_lineage("precedent")
```

**Result:** Understand stare decisis as "to stand by things decided" with stable meaning (low drift score) from Roman law to modern.

### 4. Due Process Historical Meaning

**Scenario:** Tracing "due process" to its historical roots

```python
# Get maxim underlying due process
maxim = loader.get_latin_maxim("audi alteram partem")
# "hear the other side" - foundational due process principle

# Get doctrine etymology
roots = loader.get_doctrine_etymology("due_process")
```

**Result:** Connect modern procedural due process to Roman natural justice principles.

---

## Etymology Loader API

### Loading Sources

```python
from scripts.jim.etymology_loader import EtymologyLoader

loader = EtymologyLoader()
result = loader.load_all_sources()
# result["success"] == True
# result["total_entries"] == 305
```

### Accessing Latin Maxims

```python
maxim = loader.get_latin_maxim("res judicata")
# Returns: {
#   "term": "res judicata",
#   "literal_translation": "a matter judged",
#   "concept": "claim preclusion",
#   "doctrines": ["civil_procedure", "finality"],
#   "era": "Roman Law",
#   "used_in": ["Civil procedure", "Constitutional law"],
#   "citations": [...]
# }
```

### Accessing Greek Roots

```python
root = loader.get_greek_root("dike")
# Returns: {
#   "root": "dike",
#   "greek_term": "δίκη",
#   "meaning": "justice; rightful order; lawsuit",
#   "concept_family": ["justice", "equity", "right", "order"],
#   "influenced": ["natural_law", "common_law_equity"],
#   "philosophers": ["Hesiod", "Plato", "Aristotle"],
#   "semantic_chain": ["dike → iustitia → justice"]
# }
```

### Accessing Canon Law Roots

```python
canon = loader.get_canon_root("ius gentium")
# Returns: {
#   "term": "ius gentium",
#   "category": "universal law",
#   "canonical_source": "Corpus Juris Canonici",
#   "influence_on": ["founding-era_natural_law", "international_law"],
#   "semantic_notes": "Bridge between Roman natural law and Christian moral law"
# }
```

### Semantic Analysis Methods

```python
# Get complete etymology
etymology = loader.get_etymology_for_term("justice")

# Get semantic lineage
lineage = loader.get_semantic_lineage("justice")

# Get drift score
score = loader.get_drift_score("justice")  # Returns 0.42

# Calculate semantic stability
stability = loader.calculate_semantic_stability("justice")
# Returns: {
#   "drift_score": 0.42,
#   "stability_rating": "moderate_drift",
#   "era_meanings": {...},
#   "semantic_lineage": [...]
# }

# Detect meaning divergence
divergence = loader.detect_meaning_divergence("justice", "roman_law", "modern")
# Returns: {
#   "has_divergence": True,
#   "source_meaning": "Virtue of giving each their due",
#   "target_meaning": "Equal application of law, procedural fairness",
#   "drift_score": 0.42
# }

# Trace concept evolution
evolution = loader.trace_concept_evolution("justice")
# Returns: [
#   {"era": "classical_greek", "meaning": "Right order, natural justice"},
#   {"era": "roman_law", "meaning": "Virtue of giving each their due"},
#   {"era": "medieval_canon", "meaning": "Divine justice tempered with mercy"},
#   {"era": "enlightenment", "meaning": "Natural rights, social contract"},
#   {"era": "modern", "meaning": "Equal application of law, procedural fairness"}
# ]
```

### Doctrine Mapping

```python
# Get etymological roots for a doctrine
roots = loader.get_doctrine_etymology("natural_law")
# Returns: ["ius naturale", "physis", "logos", "lex aeterna"]

roots = loader.get_doctrine_etymology("due_process")
# Returns: ["audi alteram partem", "nemo judex in causa sua"]
```

### Cross-References

```python
# Get cross-references for a term
refs = loader.get_cross_references("justice")
# Returns: ["dike", "dikaiosyne", "iustitia", "ius"]
```

### Validation and Reporting

```python
# Validate schema
validation = loader.validate_schema()
# Returns: {"valid": True, "errors": []}

# Generate comprehensive report
report = loader.generate_etymology_report()
# Returns: {
#   "version": "1.0.0",
#   "statistics": {
#     "latin_maxims": 100,
#     "greek_roots": 130,
#     "canon_roots": 75,
#     "matrix_entries": 50,
#     "total_entries": 305
#   },
#   "drift_analysis": {
#     "stable_terms": 15,
#     "moderate_drift": 20,
#     "significant_drift": 15
#   },
#   "integration_points": {
#     "msh_compatible": True,
#     "clf_compatible": True,
#     "lexicon_compatible": True
#   }
# }
```

---

## Drift Score Analysis

### Drift Score Distribution

Based on LGCEP-v1 analysis:

**Stable Terms (0.0-0.3):**
- Precedent (stare decisis)
- Consent (consensus)
- Contract (contractus)

**Moderate Drift (0.3-0.5):**
- Justice (dike → iustitia → justice)
- Law (nomos → lex → law)
- Equity (epieikeia → aequitas → equity)

**Significant Drift (0.5-1.0):**
- Liberty (eleutheria → libertas → liberty + privacy)
- Rights (dike → ius → rights + civil/human rights)
- Sovereignty (kratos → imperium → popular sovereignty)

### Factors Contributing to Drift

1. **Expansion of Scope**: Modern terms often broader than classical
2. **Philosophical Shifts**: Natural law → positivism → rights-based
3. **Political Evolution**: Monarchy → republicanism → democracy
4. **Social Change**: Gender, race, civil rights expansions
5. **Technological Context**: Digital age privacy, speech, commerce

---

## Files and Structure

```
legal/etymology/
├── latin_maxims.json          # 100 Latin legal maxims
├── greek_roots.json           # 130 Greek philosophical roots
├── canon_law_roots.json       # 75 Canon law roots
├── ETYMOLOGY_MATRIX.json      # 50 harmonized entries
└── ETYMOLOGY_INDEX.json       # Master index (305 total entries)

scripts/jim/
└── etymology_loader.py        # Etymology loader class

tests/etymology/
├── test_etymology_loader.py   # 52 loader tests
├── test_etymology_matrix.py   # 32 matrix tests
└── test_cross_integration.py  # 32 integration tests
```

---

## Future Enhancements

### Planned Additions

1. **Expanded Matrix**: Increase from 50 to 200+ harmonized entries
2. **Modern Derivatives**: Track modern legal terms derived from classical roots
3. **Comparative Law**: Add French (Code Napoleon), German (BGB) etymologies
4. **Temporal Visualization**: Graph semantic drift over time
5. **AI Semantic Analysis**: ML-powered drift detection and meaning prediction

### Integration Opportunities

1. **Case Law Analysis**: Link SCOTUS opinions to etymological foundations
2. **Statutory Interpretation**: Use etymology for canons of construction
3. **Originalism Support**: Provide founding-era meaning analysis
4. **International Law**: Extend to ius gentium and law of nations
5. **Comparative Constitutionalism**: Multi-national constitutional etymology

---

## References

### Classical Sources
- Plato, *Republic* (380 BCE)
- Aristotle, *Nicomachean Ethics* (350 BCE)
- Aristotle, *Politics* (350 BCE)
- Cicero, *De Legibus* (52 BCE)
- Justinian, *Institutes* (533 CE)

### Medieval Sources
- Gratian, *Decretum* (1140)
- Aquinas, *Summa Theologica* (1265-1274)
- Bracton, *De Legibus* (1250)

### Modern Sources
- Blackstone, *Commentaries* (1765-1769)
- Legal maxims treatises
- Black's Law Dictionary (11th ed.)
- Oxford Classical Dictionary

---

## Support and Documentation

For schema reference and detailed field specifications, see:
- **etymology_schema_reference.md**: Complete schema documentation
- **lexicon_overview.md**: Lexicon system integration
- **semantic_harmonization_overview.md**: MSH integration
- **constitutional_linguistic_frameworks.md**: CLF integration

---

**LGCEP-v1** provides JIM with unprecedented etymological depth, enabling sophisticated semantic analysis across 2000+ years of legal tradition. By tracing terms from their Greek and Latin origins through medieval Canon law to modern jurisprudence, JIM can validate interpretations, detect semantic drift, and ground constitutional analysis in historical linguistic foundations.
