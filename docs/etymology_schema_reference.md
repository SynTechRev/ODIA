# Etymology Schema Reference — LGCEP-v1

**Version:** 1.0.0  
**Schema Version:** 1.0  
**Date:** December 2024

This document provides complete schema specifications for all etymology data files in LGCEP-v1.

---

## Schema Hierarchy

```
LGCEP-v1 Schemas
├── Latin Maxims Schema
├── Greek Roots Schema
├── Canon Law Roots Schema
├── Etymology Matrix Schema
└── Etymology Index Schema
```

---

## 1. Latin Maxims Schema

**File:** `legal/etymology/latin_maxims.json`

### Root Schema

```json
{
  "source": "latin_legal_maxims",
  "version": "1.0.0",
  "description": "string",
  "total_maxims": integer,
  "schema_version": "1.0",
  "generated_date": "YYYY-MM-DD",
  "maxims": [Maxim...]
}
```

### Maxim Object Schema

```json
{
  "term": "string (required)",
  "literal_translation": "string (required)",
  "concept": "string (required)",
  "doctrines": ["string", ...] (required),
  "era": "string (required)",
  "used_in": ["string", ...] (required),
  "citations": ["string", ...] (optional)
}
```

### Field Specifications

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `term` | string | Yes | Latin maxim or term | "stare decisis" |
| `literal_translation` | string | Yes | English translation | "to stand by things decided" |
| `concept` | string | Yes | Legal concept | "judicial precedent" |
| `doctrines` | array[string] | Yes | Legal doctrines | ["precedent", "common_law"] |
| `era` | string | Yes | Historical era | "Roman Law", "Medieval English Common Law" |
| `used_in` | array[string] | Yes | Areas of use | ["Common law", "Constitutional interpretation"] |
| `citations` | array[string] | No | References | ["Planned Parenthood v Casey (1992)"] |

### Validation Rules

1. **term**: Must be non-empty, Latin text
2. **literal_translation**: Must be non-empty English
3. **concept**: Must be non-empty, describes core legal concept
4. **doctrines**: Array must contain at least one doctrine
5. **era**: Must reference valid historical period
6. **used_in**: Array must contain at least one area

### Era Values

Valid era values:
- "Roman Law"
- "Medieval English Common Law"
- "Medieval Canon Law"

---

## 2. Greek Roots Schema

**File:** `legal/etymology/greek_roots.json`

### Root Schema

```json
{
  "source": "greek_philosophical_roots",
  "version": "1.0.0",
  "description": "string",
  "total_roots": integer,
  "schema_version": "1.0",
  "generated_date": "YYYY-MM-DD",
  "roots": [Root...]
}
```

### Root Object Schema

```json
{
  "root": "string (required)",
  "greek_term": "string (required)",
  "meaning": "string (required)",
  "concept_family": ["string", ...] (required),
  "influenced": ["string", ...] (required),
  "philosophers": ["string", ...] (required),
  "semantic_chain": ["string", ...] (required),
  "era": "string (required)",
  "modern_derivatives": ["string", ...] (optional)
}
```

### Field Specifications

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `root` | string | Yes | Transliterated Greek root | "dike" |
| `greek_term` | string | Yes | Greek text | "δίκη" |
| `meaning` | string | Yes | English meaning | "justice; rightful order" |
| `concept_family` | array[string] | Yes | Related concepts | ["justice", "equity", "right"] |
| `influenced` | array[string] | Yes | Doctrines influenced | ["natural_law", "common_law_equity"] |
| `philosophers` | array[string] | Yes | Associated philosophers | ["Plato", "Aristotle"] |
| `semantic_chain` | array[string] | Yes | Evolution chain | ["dike → iustitia → justice"] |
| `era` | string | Yes | Greek period | "Classical Greek" |
| `modern_derivatives` | array[string] | No | Modern words | ["judicial", "vindicate"] |

### Validation Rules

1. **root**: Must be non-empty, transliterated Greek
2. **greek_term**: Must contain Greek Unicode characters
3. **meaning**: Must be non-empty English
4. **concept_family**: Array must contain at least one concept
5. **influenced**: Array must contain at least one doctrine/area
6. **philosophers**: Array must contain at least one philosopher
7. **semantic_chain**: Array must show progression (contains →)
8. **era**: Must reference valid Greek period

### Era Values

Valid era values:
- "Archaic Greek"
- "Classical Greek"
- "Hellenistic"
- "Pre-Socratic to Classical"

---

## 3. Canon Law Roots Schema

**File:** `legal/etymology/canon_law_roots.json`

### Root Schema

```json
{
  "source": "canon_law_roots",
  "version": "1.0.0",
  "description": "string",
  "total_entries": integer,
  "schema_version": "1.0",
  "generated_date": "YYYY-MM-DD",
  "entries": [Entry...]
}
```

### Entry Object Schema

```json
{
  "term": "string (required)",
  "category": "string (required)",
  "canonical_source": "string (required)",
  "influence_on": ["string", ...] (required)",
  "semantic_notes": "string (required)"
}
```

### Field Specifications

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `term` | string | Yes | Canon law term | "ius gentium" |
| `category` | string | Yes | Canonical category | "universal law" |
| `canonical_source` | string | Yes | Source text | "Corpus Juris Canonici" |
| `influence_on` | array[string] | Yes | Influenced doctrines | ["founding-era_natural_law"] |
| `semantic_notes` | string | Yes | Explanatory notes | "Bridge between Roman natural law..." |

### Validation Rules

1. **term**: Must be non-empty, typically Latin
2. **category**: Must be non-empty, describes canonical category
3. **canonical_source**: Must reference valid canonical text
4. **influence_on**: Array must contain at least one influenced area
5. **semantic_notes**: Must be non-empty, provide context

### Category Values

Common categories:
- "universal law"
- "natural law"
- "divine law"
- "positive law"
- "conscience"
- "free will"
- "human dignity"
- "authority"
- "jurisdiction"
- "equity principle"

---

## 4. Etymology Matrix Schema

**File:** `legal/etymology/ETYMOLOGY_MATRIX.json`

### Root Schema

```json
{
  "matrix": "etymology_harmonization_matrix",
  "version": "1.0.0",
  "schema_version": "1.0",
  "description": "string",
  "generated_date": "YYYY-MM-DD",
  "total_entries": integer,
  "drift_score_methodology": "string",
  "entries": [Entry...]
}
```

### Entry Object Schema

```json
{
  "term": "string (required)",
  "root_languages": {
    "latin": "string (optional)",
    "greek": "string (optional)",
    "canon": "string (optional)",
    "english_modern": "string (required)"
  },
  "semantic_lineage": ["string", ...] (required),
  "drift_score": float (required, 0.0-1.0),
  "era_meanings": {
    "classical_greek": "string (optional)",
    "roman_law": "string (optional)",
    "medieval_canon": "string (optional)",
    "enlightenment": "string (optional)",
    "modern": "string (required)"
  },
  "legal_doctrines": ["string", ...] (required),
  "citations": ["string", ...] (optional)
}
```

### Field Specifications

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `term` | string | Yes | Modern English term | "justice" |
| `root_languages` | object | Yes | Root language mappings | See below |
| `semantic_lineage` | array[string] | Yes | Evolution chains | ["dike → iustitia → justice"] |
| `drift_score` | float | Yes | Semantic change (0.0-1.0) | 0.42 |
| `era_meanings` | object | Yes | Era-specific meanings | See below |
| `legal_doctrines` | array[string] | Yes | Related doctrines | ["equity", "natural_law"] |
| `citations` | array[string] | No | References | ["Plato Republic"] |

### Root Languages Sub-Schema

```json
{
  "latin": "string (optional)",
  "greek": "string (optional)",
  "canon": "string (optional)",
  "english_modern": "string (required)"
}
```

At least one of `latin`, `greek`, or `canon` must be present.

### Era Meanings Sub-Schema

```json
{
  "classical_greek": "string (optional)",
  "roman_law": "string (optional)",
  "medieval_canon": "string (optional)",
  "enlightenment": "string (optional)",
  "modern": "string (required)"
}
```

At least `modern` must be present. Additional eras provide historical context.

### Validation Rules

1. **term**: Must be non-empty, lowercase normalized
2. **root_languages**: Must have at least one non-English root
3. **semantic_lineage**: Must show progression (contains →)
4. **drift_score**: Must be float in range [0.0, 1.0]
5. **era_meanings**: Must have at least `modern` meaning
6. **legal_doctrines**: Array must contain at least one doctrine

### Drift Score Interpretation

| Range | Rating | Interpretation |
|-------|--------|----------------|
| 0.0-0.3 | Stable | Minimal semantic change from classical to modern |
| 0.3-0.5 | Moderate | Some evolution in meaning and usage |
| 0.5-1.0 | Significant | Substantial change in meaning and scope |

---

## 5. Etymology Index Schema

**File:** `legal/etymology/ETYMOLOGY_INDEX.json`

### Root Schema

```json
{
  "index": "etymology_index",
  "version": "1.0.0",
  "schema_version": "1.0",
  "description": "string",
  "generated_date": "YYYY-MM-DD",
  "sources": {
    "latin_maxims": {
      "file": "string",
      "total_entries": integer,
      "description": "string"
    },
    "greek_roots": {...},
    "canon_law_roots": {...},
    "etymology_matrix": {...}
  },
  "total_entries": integer,
  "cross_references": {
    "term": ["root1", "root2", ...]
  },
  "doctrine_mappings": {
    "doctrine": ["root1", "root2", ...]
  }
}
```

### Source Entry Schema

```json
{
  "file": "string (required)",
  "total_entries": integer (required),
  "description": "string (required)"
}
```

### Cross-References Schema

```json
{
  "english_term": ["root1", "root2", "root3", ...]
}
```

Maps English terms to their etymological roots across all sources.

### Doctrine Mappings Schema

```json
{
  "doctrine_name": ["root1", "root2", "root3", ...]
}
```

Maps legal doctrines to their etymological foundations.

### Validation Rules

1. **sources**: Must include all four source types
2. **total_entries**: Must sum entries from all sources
3. **cross_references**: Must reference valid terms/roots
4. **doctrine_mappings**: Must reference valid doctrines/roots

---

## Common Field Types

### String Types

| Type | Description | Example |
|------|-------------|---------|
| `term` | Legal term | "justice", "stare decisis" |
| `root` | Greek/Latin root | "dike", "lex" |
| `concept` | Legal concept | "precedent", "due process" |
| `doctrine` | Legal doctrine | "natural_law", "due_process" |
| `era` | Historical period | "Classical Greek", "Roman Law" |
| `citation` | Reference | "Plato Republic", "Marbury v Madison" |

### Array Types

All arrays must:
- Be valid JSON arrays
- Contain at least one element (unless optional)
- Contain only strings
- Not contain duplicates

### Object Types

All objects must:
- Be valid JSON objects
- Have required fields present
- Have no extraneous fields (unless extensible)

---

## Validation Checklist

### File-Level Validation

- [ ] Valid JSON syntax
- [ ] Correct file encoding (UTF-8)
- [ ] Required root fields present
- [ ] Version fields match specification
- [ ] Date fields in ISO 8601 format (YYYY-MM-DD)

### Entry-Level Validation

- [ ] All required fields present
- [ ] Field types match specification
- [ ] String fields non-empty
- [ ] Arrays contain valid elements
- [ ] Numeric fields in valid ranges

### Semantic Validation

- [ ] Cross-references resolve
- [ ] Doctrines map correctly
- [ ] Era values consistent
- [ ] Semantic chains show progression
- [ ] Drift scores reasonable

### Integration Validation

- [ ] Terms in matrix exist in sources
- [ ] Index references valid files
- [ ] Cross-references bidirectional
- [ ] Doctrine mappings complete

---

## Extension Points

The schema supports extension through:

1. **Additional fields**: Schemas are not closed; additional fields allowed
2. **New eras**: Era meanings can include additional historical periods
3. **New doctrines**: Doctrine arrays extensible
4. **New citations**: Citation arrays unlimited
5. **New categories**: Canon categories extensible

---

## Migration and Versioning

### Version Numbering

- **Major version**: Breaking schema changes
- **Minor version**: Backward-compatible additions
- **Patch version**: Bug fixes, clarifications

### Backward Compatibility

LGCEP-v1 maintains backward compatibility:
- Required fields never removed
- Field types never changed
- Enum values never removed

### Forward Compatibility

Consumers should:
- Ignore unknown fields
- Handle missing optional fields
- Accept extended enums
- Validate required fields only

---

## Schema Validation Tools

### Python Validation

```python
from scripts.jim.etymology_loader import EtymologyLoader

loader = EtymologyLoader()
loader.load_all_sources()

# Validate all schemas
validation = loader.validate_schema()
print(validation)  # {"valid": True, "errors": []}
```

### Manual Validation

1. Check JSON syntax with `jq` or `python -m json.tool`
2. Verify required fields present
3. Check field types match specification
4. Validate ranges for numeric fields
5. Confirm cross-references resolve

---

## Best Practices

### Data Entry

1. **Consistent formatting**: Use consistent capitalization and spacing
2. **Complete citations**: Include full citations when available
3. **Accurate translations**: Verify Latin/Greek translations
4. **Meaningful drift scores**: Base on substantive semantic analysis
5. **Era-specific meanings**: Provide context for each era

### Schema Evolution

1. **Maintain compatibility**: Don't break existing consumers
2. **Document changes**: Update schema reference for all changes
3. **Version appropriately**: Follow semantic versioning
4. **Test thoroughly**: Validate all data after schema changes
5. **Communicate changes**: Notify integrators of updates

---

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| Invalid JSON | Syntax error | Validate with JSON parser |
| Missing field | Required field absent | Add required field |
| Type mismatch | Wrong field type | Convert to correct type |
| Invalid range | Numeric value out of range | Adjust to valid range |
| Broken reference | Cross-reference invalid | Fix reference or add target |

### Validation Error Format

```json
{
  "valid": false,
  "errors": [
    {
      "file": "latin_maxims.json",
      "entry": "stare decisis",
      "field": "doctrines",
      "error": "Required field missing"
    }
  ]
}
```

---

## Support

For schema questions or validation issues:
- **Documentation**: See `etymology_overview.md`
- **Examples**: Review existing data files
- **Validation**: Run `etymology_loader.validate_schema()`
- **Integration**: Check integration test suite

---

**LGCEP-v1 Schema Reference** provides complete specifications for all etymology data structures, enabling consistent data entry, robust validation, and seamless integration with JIM semantic systems.
