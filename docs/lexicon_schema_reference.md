# Legal Lexicon Schema Reference

## Overview

This document defines the JSON schemas for all legal lexicon dictionary files and the unified index. All files must conform to these schemas for successful loading by the JIM Semantic Loader.

## Common Schema Elements

### Term Normalization Rules

All terms are normalized according to the following rules:

1. **Lowercase**: All characters converted to lowercase
2. **Spaces to Underscores**: Spaces replaced with underscores
3. **Hyphens to Underscores**: Hyphens replaced with underscores  
4. **Remove Apostrophes**: Apostrophes removed
5. **Strip Whitespace**: Leading and trailing whitespace removed

**Examples**:
- `"Probable Cause"` → `"probable_cause"`
- `"Ex-Parte"` → `"ex_parte"`
- `"Black's Law"` → `"blacks_law"`

### Doctrine Mapping Standard

Doctrines follow a consistent naming convention:

- Lowercase with underscores: `fourth_amendment`, `due_process`
- Descriptive but concise: `search_and_seizure`, `exclusionary_rule`
- Aligned with JIM doctrine map: Must match or be compatible with doctrines in `jim_doctrine_map.json`

## Black's Law Dictionary Schema

**File**: `black_law_subset.json`

```json
{
  "dictionary": "blacks_law_dictionary",
  "edition": "11th",
  "year": 2019,
  "description": "Core subset of Black's Law Dictionary covering foundational constitutional and procedural terms",
  "terms": [
    {
      "term": "string (required)",
      "definition": "string (required, min 20 chars)",
      "citation": "string (required, format: 'p. XXX')",
      "category": "string (required, one of: constitutional_law, criminal_law, criminal_procedure, civil_procedure, evidence, tort_law, property_law, contracts, administrative_law, common_law, jurisprudence)",
      "origin_language": "string (required, one of: English, Latin, French, Greek)"
    }
  ]
}
```

### Required Fields

- **dictionary**: Must be `"blacks_law_dictionary"`
- **edition**: Edition number or identifier
- **year**: Publication year
- **description**: Brief description of content scope
- **terms**: Array of term objects

### Term Object Fields

- **term** (required): The legal term as it appears in the dictionary
- **definition** (required): Complete definition, minimum 20 characters
- **citation** (required): Page reference in format "p. XXX" or "pp. XXX-YYY"
- **category** (required): Legal category from predefined list
- **origin_language** (required): Language of term origin

### Validation Rules

1. No duplicate terms within dictionary
2. All citations must contain "p." or "pp."
3. Definitions must be non-empty and substantive
4. All required fields must be present

## Bouvier's Law Dictionary Schema

**File**: `bouvier_1856.json`

```json
{
  "dictionary": "bouviers_law_dictionary",
  "edition": "1856",
  "year": 1856,
  "description": "Key terms from Bouvier's Law Dictionary (1856 edition) - foundational American legal definitions",
  "terms": [
    {
      "term": "string (required)",
      "definition": "string (required, min 20 chars)",
      "citation": "string (required, format: 'Vol. X, p. XXX')",
      "category": "string (required)",
      "origin_language": "string (required)"
    }
  ]
}
```

### Bouvier-Specific Requirements

- **citation**: Must contain "Vol." and "p." for volume and page references
- Historical context preserved in definitions
- 1856 spelling and terminology maintained

## Webster Legal Dictionary Schema

**File**: `webster_legal_subset.json`

```json
{
  "dictionary": "webster_legal_dictionary",
  "edition": "Merriam-Webster Legal Dictionary",
  "year": 2023,
  "description": "Modern legal terms with accessible definitions, synonyms, and practical usage examples",
  "terms": [
    {
      "term": "string (required)",
      "definition": "string (required, min 20 chars)",
      "synonyms": ["string", "string", ...] (required, may be empty array),
      "antonyms": ["string", "string", ...] (required, may be empty array),
      "practical_usage": "string (required)",
      "origin_language": "string (required)"
    }
  ]
}
```

### Webster-Specific Fields

- **synonyms** (required): Array of synonym terms (may be empty)
- **antonyms** (required): Array of antonym terms (may be empty)
- **practical_usage** (required): Description of how term is used in practice

### Synonym/Antonym Requirements

- Each synonym/antonym must be a non-empty string
- Should be normalized according to term normalization rules
- Bidirectional relationships encouraged (if A is synonym of B, B should be synonym of A)

## Oxford Law Dictionary Schema

**File**: `oxford_law_synonyms.json`

```json
{
  "dictionary": "oxford_english_law_dictionary",
  "edition": "Oxford Dictionary of Law",
  "year": 2023,
  "description": "Synonym and equivalent term mappings for legal terminology (definitions not included - see source dictionaries)",
  "synonym_mappings": [
    {
      "term": "string (required)",
      "synonyms": ["string", "string", ...] (required, min 1 item)
    }
  ]
}
```

### Oxford-Specific Requirements

- **No definitions**: This dictionary contains only synonym mappings
- **synonyms**: Must contain at least one synonym
- Focus on cross-jurisdictional term equivalents

## Latin Legal Maxims Schema

**File**: `latin_foundational.json`

```json
{
  "dictionary": "latin_legal_maxims",
  "edition": "Foundational Latin Legal Vocabulary",
  "year": 2024,
  "description": "Essential Latin legal terms, maxims, and phrases with translations and jurisprudential usage",
  "terms": [
    {
      "latin": "string (required)",
      "translation": "string (required)",
      "jurisprudential_usage": "string (required, min 20 chars)",
      "doctrinal_mapping": ["string", "string", ...] (required, min 1 item),
      "origin_language": "Latin" (required, must be "Latin")
    }
  ]
}
```

### Latin-Specific Fields

- **latin** (required): The Latin term or maxim
- **translation** (required): English translation
- **jurisprudential_usage** (required): How the term is used in legal practice
- **doctrinal_mapping** (required): Array of associated doctrines (minimum 1)
- **origin_language** (required): Must be "Latin"

### Latin Formatting Standards

- Latin terms in lowercase (except proper nouns)
- Italicization not required in JSON (handled in rendering)
- Classical Latin spelling preferred

## Unified Legal Dictionary Index Schema

**File**: `LEGAL_DICTIONARY_INDEX.json`

```json
{
  "version": "1.0.0",
  "description": "Unified legal lexicon index consolidating all dictionary sources",
  "metadata": {
    "created": "YYYY-MM-DD",
    "total_terms": 0,
    "source_dictionaries": [
      {
        "name": "string",
        "edition": "string",
        "year": 0,
        "term_count": 0
      }
    ],
    "categories": ["string", "string", ...]
  },
  "index": [
    {
      "term": "string (required)",
      "normalized_term": "string (required)",
      "sources": [
        {
          "dictionary": "string (required)",
          "edition": "string (optional)",
          "citation": "string (optional)",
          "definition": "string (optional)",
          "synonyms": ["string", ...] (optional),
          "antonyms": ["string", ...] (optional),
          "translation": "string (optional)",
          "jurisprudential_usage": "string (optional)"
        }
      ],
      "doctrines": ["string", "string", ...] (required, may be empty),
      "origin_language": "string (required)",
      "related_terms": ["string", "string", ...] (required, may be empty),
      "antonyms": ["string", "string", ...] (required, may be empty)
    }
  ]
}
```

### Index Structure

The index consolidates information from all source dictionaries for each term.

#### Metadata Section

- **version**: Index schema version
- **created**: ISO 8601 date of index creation
- **total_terms**: Count of unique terms in index
- **source_dictionaries**: Array of source dictionary metadata
- **categories**: List of all legal categories used

#### Index Entry Structure

- **term** (required): Original term name
- **normalized_term** (required): Normalized version following term normalization rules
- **sources** (required): Array of source dictionary entries for this term
- **doctrines** (required): Array of associated doctrine identifiers
- **origin_language** (required): Primary language of term origin
- **related_terms** (required): Array of semantically related terms
- **antonyms** (required): Array of opposing terms

#### Source Object Structure

Each source provides information from one dictionary:

- **dictionary** (required): Source dictionary identifier
- **edition** (optional): Edition or year
- **citation** (optional): Page reference
- **definition** (optional): Definition from this source
- **synonyms** (optional): Synonyms from this source
- **antonyms** (optional): Antonyms from this source
- **translation** (optional): Translation (for Latin terms)
- **jurisprudential_usage** (optional): Usage description

### Index Validation Rules

1. **Unique normalized terms**: No duplicate `normalized_term` values
2. **At least one source**: Each term must have at least one source entry
3. **Valid doctrine references**: Doctrines should align with JIM doctrine map
4. **Bidirectional relationships**: Related terms and antonyms should be reciprocal where possible
5. **Consistent normalization**: All `normalized_term` values must follow normalization rules

## Generated Artifacts

### LEXICON_GRAPH.json

```json
{
  "version": "1.0.0",
  "generated": "ISO 8601 timestamp",
  "synonym_graph": {
    "normalized_term": ["synonym1", "synonym2", ...]
  },
  "antonym_graph": {
    "normalized_term": ["antonym1", "antonym2", ...]
  },
  "doctrine_map": {
    "doctrine_name": ["term1", "term2", ...]
  },
  "normalized_terms": {
    "normalized_term": "original_term"
  }
}
```

### LEXICON_STATS.json

```json
{
  "version": "1.0.0",
  "generated": "ISO 8601 timestamp",
  "total_terms": 0,
  "synonym_relationships": 0,
  "antonym_relationships": 0,
  "doctrines_mapped": 0,
  "source_dictionaries": 5,
  "blacks_terms": 0,
  "bouvier_terms": 0,
  "webster_terms": 0,
  "oxford_mappings": 0,
  "latin_terms": 0,
  "index_entries": 0
}
```

### LEXICON_SUMMARY.md

Markdown format document containing:
- Overview and statistics
- Source dictionary breakdown
- Doctrine coverage analysis
- Category distribution
- Integration guidelines

## Versioning

All schemas use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible schema changes
- **MINOR**: Backward-compatible additions
- **PATCH**: Backward-compatible fixes

Current version: **1.0.0**

## Extending the Schema

To add a new dictionary source:

1. Create new JSON file following naming convention: `{source}_subset.json`
2. Include required metadata fields: `dictionary`, `edition`, `year`, `description`
3. Define term array with source-specific required fields
4. Update `LEGAL_DICTIONARY_INDEX.json` to include terms
5. Update `jim_semantic_loader.py` to load new source
6. Add validation tests
7. Update documentation

## Best Practices

1. **Consistency**: Use consistent terminology across all dictionary sources
2. **Completeness**: Ensure all required fields are populated
3. **Accuracy**: Verify citations against source materials
4. **Clarity**: Write clear, complete definitions
5. **Cross-referencing**: Link related terms via synonym/antonym/related fields
6. **Documentation**: Include source attribution and edition information
7. **Validation**: Run schema validation before committing changes

## Validation Tools

The semantic loader provides validation through:

```python
from scripts.jim.jim_semantic_loader import JIMSemanticLoader

loader = JIMSemanticLoader()
loader.load_lexicon_sources()
validation = loader.validate_lexicon_schema()

if not validation['valid']:
    print(f"Validation errors: {validation['errors']}")
```

## References

- JSON Schema: https://json-schema.org/
- ISO 8601 Date Format: https://en.wikipedia.org/wiki/ISO_8601
- Semantic Versioning: https://semver.org/

## See Also

- `lexicon_overview.md` - Lexicon system overview
- `jim_overview.md` - JIM documentation
- Test suite in `tests/lexicon/` for schema validation examples
