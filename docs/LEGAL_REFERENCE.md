# ODIA Legal Reference System

The legal reference system provides a searchable, RAG-integrated dataset of legal
definitions, case law holdings, and Latin maxims that ODIA's anomaly detectors and
language-model reasoning pipeline can draw from without accessing external services.

---

## Overview

The system has three layers:

| Layer | Source | Records |
|-------|--------|---------|
| Legal dictionaries | Bouvier (1856), Anderson (1889), Cornell Wex, Latin maxims | 255 terms across 4 sources |
| Case law | SCOTUS and federal court holdings | 64 cases, 14 doctrines, 35 extracted definitions |
| RAG index | Combined export of all layers | 433 chunks indexed by `RetrievalEngine` |

All data is resident in the repository under `legal/`. No external API calls are made
at runtime to populate these datasets.

---

## Data Sources

### Bouvier's Law Dictionary (1856 edition)
- **File**: `legal/lexicon/bouvier_1856.json`
- **Terms**: 100
- **License**: Public domain — published 1856, well beyond copyright term
- **Coverage**: Core common-law concepts (appropriation, probable cause, warrant,
  contract, hearsay, eminent domain, due process, equal protection, breach, surety)
- **Relevance fields**: `relevance_to_audit` present on all terms

### Anderson's Dictionary of Law (1889 edition)
- **File**: `legal/lexicon/anderson_1889.json`
- **Terms**: 52
- **License**: Public domain — published 1889, well beyond copyright term
- **Coverage**: Municipal and public-finance law (comptroller, county auditor,
  competitive bid, sole source contract, open meetings law, public records,
  fiscal officer, appropriations committee)

### Cornell Legal Information Institute — Wex (selected terms)
- **File**: `legal/lexicon/wex_cornell.json`
- **Terms**: 53
- **License**: Open reference; Cornell LII publishes Wex under an open-access policy
  for educational and research use
- **Coverage**: Modern administrative, surveillance, and civil-rights law (FOIA, FISA,
  Fourth Amendment doctrine, ALPR, biometric data, geofence warrant, Monell liability,
  non-delegation doctrine, qualified immunity, Single Audit Act, Carpenter doctrine,
  False Claims Act, qui tam)

### Latin Legal Maxims
- **File**: `legal/lexicon/latin_foundational.json`
- **Terms**: 50
- **License**: Classical Latin phrases — no copyright; definitions are original
  work product of this project (MIT license)
- **Coverage**: Core doctrinal maxims (ultra vires, res judicata, mandamus, in camera,
  habeas corpus, noscitur a sociis, expressio unius, ejusdem generis, pro tanto,
  quantum meruit)
- **Relevance fields**: `relevance_to_audit` maps each maxim to specific ODIA audit
  finding categories

### What Is NOT Included

The following sources were evaluated and excluded:

| Source | Reason |
|--------|--------|
| Black's Law Dictionary (current edition) | Copyrighted; Thomson Reuters — inclusion would require licensing |
| American Jurisprudence (Am Jur) | Copyrighted; Thomson Reuters — same issue |
| Westlaw / LexisNexis full-text | Commercial, licensed databases — not redistributable |
| Restatements (ALI) | ALI asserts copyright over Restatement text |
| PACER case text | Per-page fee; not freely redistributable |

Federal government works (17 U.S.C. § 105) are not subject to copyright. SCOTUS opinions,
federal statutes, and CFR text are in the public domain and are the basis for all case
law data in `legal/cases/`.

---

## Case Law Dataset

### Structure

Each case is stored as a JSON file in `legal/cases/` and indexed in
`legal/cases/SCOTUS_INDEX.json`.

```json
{
  "case_id": "carpenter_v_united_states_2018",
  "name": "Carpenter v. United States",
  "citation": "585 U.S. 296 (2018)",
  "year": 2018,
  "court": "SCOTUS",
  "doctrine": "fourth_amendment",
  "doctrinal_weight": 0.95,
  "summary": "...",
  "holding": "...",
  "key_quotes": [...],
  "legal_definitions": [
    {
      "term": "Carpenter doctrine",
      "definition": "...",
      "pinpoint_citation": "585 U.S. 296, 310"
    }
  ]
}
```

### Doctrines Covered (14)

| Doctrine | Description |
|----------|-------------|
| `fourth_amendment` | Search and seizure, warrant requirements, digital privacy |
| `fifth_amendment` | Self-incrimination, due process, takings clause |
| `first_amendment` | Speech, assembly, religion — relevant to surveillance review |
| `fourteenth_amendment` | Equal protection, substantive due process |
| `administrative_law` | Chevron/Loper Bright, APA, non-delegation |
| `civil_rights` | Section 1983, Monell, qualified immunity |
| `procurement_law` | Competitive bidding, sole source, False Claims Act |
| `government_transparency` | FOIA, FISA, open meetings |
| `surveillance_law` | ALPR, biometrics, geofence warrants, pen register |
| `fiscal_law` | Appropriations, Antideficiency Act, Single Audit |
| `federalism` | Spending clause, commandeering, preemption |
| `contract_law` | Government contracts, breach, performance bonds |
| `evidence` | Exclusionary rule, fruit of the poisonous tree, hearsay |
| `standing` | Article III standing, ripeness, mootness |

### Superseded Doctrine Tracking

Three case-derived definitions are automatically flagged as superseded:

| Term | Original Case | Superseded By |
|------|--------------|---------------|
| Chevron deference | Chevron USA v. NRDC (1984) | Loper Bright Enterprises v. Raimondo (2024) |
| Auer deference | Auer v. Robbins (1997) | Kisor v. Wilkie (2019) |
| intelligible principle | Panama Refining Co. v. Ryan (1935) | Mistretta v. United States (1989) |

The `DefinitionExtractor` marks these in the `superseded_by` field of the
`CaseDefinition` model and includes a supersession note in all RAG export chunks
for those terms.

---

## How to Expand the Dataset

### Adding a New Dictionary

1. Create `legal/lexicon/<name>.json` following the schema in
   `legal/lexicon/bouvier_1856.json`:

   ```json
   {
     "source": "<name>",
     "edition": "<year or edition>",
     "license": "<license text>",
     "terms": [
       {
         "term": "example term",
         "definition": "...",
         "category": "...",
         "relevance_to_audit": "..."
       }
     ]
   }
   ```

2. Add an entry to `legal/lexicon/LEGAL_DICTIONARY_INDEX.json` under
   `source_dictionaries`.

3. Add the new source key to `LegalReferenceService._DICT_SOURCES` in
   `src/oraculus_di_auditor/legal/reference_service.py`.

### Adding a New Case

1. Create `legal/cases/<case_id>.json` using the schema above. Required fields:
   `case_id`, `name`, `citation`, `year`, `court`, `doctrine`, `doctrinal_weight`,
   `summary`, `holding`.

2. Add an entry to `legal/cases/SCOTUS_INDEX.json`.

3. If the case defines a term that supersedes an existing definition, add an entry
   to `_SUPERSEDED_BY` in
   `src/oraculus_di_auditor/legal/definition_extractor.py`.

### Adding a New Doctrine

The doctrine field is a free string in each case file. To make a new doctrine
queryable via `LegalReferenceService.lookup_doctrine()`, add the doctrine key and
associated description to the `_DOCTRINE_DESCRIPTIONS` dict in `reference_service.py`.

---

## How Legal Reference Feeds into ODIA

### RAG Pipeline (Sprint 7)

```python
from oraculus_di_auditor.legal import LegalReferenceService
from oraculus_di_auditor.rag.retriever_engine import RetrievalEngine

svc = LegalReferenceService()
engine = RetrievalEngine()

# Export all legal chunks and index them
chunks = svc.export_all_for_rag()          # 433 chunks
engine.index_legal_references(chunks)      # indexed in the TF-IDF retriever

# Now semantic search includes legal context
results = engine.search("geofence warrant Fourth Amendment")
```

RAG chunks carry `source_type` values of `"legal_dictionary"`, `"case_law"`, or
`"case_law_definition"`, so queries can be filtered to legal sources only using
`engine.search(query, source_filter="legal_dictionary")`.

The `RAGService` in `rag/rag_service.py` will include legal chunks in context
building automatically once `index_legal_references()` has been called.

### Anomaly Detectors

The constitutional and surveillance detectors can call `LegalReferenceService`
to look up the current legal standard for a doctrine before flagging a finding:

```python
svc = LegalReferenceService()
result = svc.lookup_doctrine("fourth_amendment")
# result.current_standard gives the operative legal test
```

This prevents findings from citing outdated standards (e.g., the pre-Carpenter
third-party doctrine as applied to cell-site location data).

### Reporting Engine

The unified reporting engine (`reporting/`) can include legal citations in
generated markdown and JSON reports. When a finding references a constitutional
doctrine, the report template can inline the authoritative case citation from
`TermLookupResult.case_references`.

### Cross-Jurisdiction Comparison (Sprint 5)

`DoctrineLookupResult.relevance_to_audit` provides a plain-English explanation
of why a doctrine matters in an audit context. The multi-jurisdiction runner
includes this text in comparative reports when a doctrine-related anomaly appears
in two or more jurisdictions.

---

## API

### `LegalReferenceService`

```python
from oraculus_di_auditor.legal import LegalReferenceService

svc = LegalReferenceService()
# Initialize is called automatically on first use, but can be called explicitly:
counts = svc.initialize()
# {"bouvier_1856": 100, "anderson_1889": 52, "latin_foundational": 50,
#  "wex_cornell": 53, "case_law": 64}

# Term lookup (searches all dictionaries + case law)
result = svc.lookup_term("probable cause")
result.found          # True
result.definitions    # list[DefinitionEntry] — all matching definitions
result.case_references  # list[dict] — cases that define this term

# Doctrine lookup
doctrine = svc.lookup_doctrine("fourth_amendment")
doctrine.current_standard  # operative legal test (post-Carpenter)
doctrine.key_cases         # ordered list of landmark cases
doctrine.evolution         # chronological list of major shifts

# Free-text search
hits = svc.search("geofence warrant cell phone location")
# list[dict] with keys: term/doctrine, definition, source, score, metadata

# Export for RAG
chunks = svc.export_all_for_rag()
# list[dict] with keys: document_id, title, content, source_type, metadata

# Coverage statistics
stats = svc.get_statistics()
# {"cases": 64, "doctrines_covered": 14, "case_law_definitions": 35,
#  "dictionary_sources": 4, "total_dictionary_terms": 255, "total_rag_chunks": 433}
```

### `DefinitionExtractor`

```python
from oraculus_di_auditor.legal import CaseLawBuilder, DefinitionExtractor

builder = CaseLawBuilder("legal/cases")
extractor = DefinitionExtractor(builder)

# Get authoritative definition (SCOTUS preferred, most recent)
defn = extractor.get_authoritative_definition("curtilage")

# Build full dictionary of all case-law-derived definitions
dictionary = extractor.build_case_law_dictionary()
dictionary.term_count   # 35
dictionary.case_count   # 35
```

---

## Coverage Statistics (live — generated from `legal/` directory)

| Metric | Count |
|--------|-------|
| Cases indexed | 64 |
| Doctrines covered | 14 |
| Case-law-derived definitions | 35 |
| Dictionary sources | 4 |
| Bouvier 1856 terms | 100 |
| Anderson 1889 terms | 52 |
| Latin maxims | 50 |
| Cornell Wex terms | 53 |
| **Total dictionary terms** | **255** |
| **Total RAG chunks** | **433** |

These numbers reflect the state of the `legal/` directory as of Sprint 8.
Run `LegalReferenceService().get_statistics()` at any time to get current counts.
