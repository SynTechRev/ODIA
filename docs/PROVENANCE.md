# Data Provenance

## Overview

This document tracks the provenance of all data sources used in testing and development of the Oraculus DI Auditor.

## Test Data Sources

### Synthetic Test Data

**Purpose**: Unit and integration testing  
**Location**: `tests/fixtures/`  
**Content**: Synthetic legal documents for testing  
**License**: Public Domain (project-generated)  
**Status**: Committed to repository

### Sample Documents

No real legal documents are committed to this repository. All test data is synthetic.

## Production Data Guidelines

### Real Data Location

**IMPORTANT**: Real legal documents should be stored in gitignored directories:

- `data/sources/` - Raw source files
- `data/raw/` - Unprocessed data
- `data/private/` - Private analysis results

### Documenting Real Data Sources

When processing real data locally, document here (do NOT commit the actual files):

#### Example Entry Template

```markdown
### [Dataset Name]

**Source**: [URL or citation]
**Date Acquired**: YYYY-MM-DD
**License**: [License type]
**Coverage**: [What it contains]
**Processing Date**: YYYY-MM-DD
**Notes**: [Any relevant notes]
```

## Public Datasets

### U.S. Code (Future Phase 3)

**Source**: https://uscode.house.gov/  
**License**: U.S. Government Work (Public Domain)  
**Coverage**: All 54 titles of U.S. Code  
**Status**: Not yet ingested  
**Notes**: Will be processed in Phase 3

### Code of Federal Regulations (Future Phase 3)

**Source**: https://www.govinfo.gov/app/collection/cfr  
**License**: U.S. Government Work (Public Domain)  
**Coverage**: All 50 titles of CFR  
**Status**: Not yet ingested  
**Notes**: Will be processed in Phase 3

## Data Transformation Log

### Transformations Applied

Document any transformations applied to source data:

1. **Normalization**: Convert to canonical JSON schema
2. **Chunking**: Split text into 512-character chunks with 64-char overlap
3. **Hashing**: SHA-256 hash for integrity verification
4. **Anonymization**: If PII removed, document here

## Verification

### Hash Verification

For critical datasets, maintain SHA-256 hashes:

```
# Example (not real data)
# filename: hash_value
# sample_statute.json: a1b2c3d4e5f6...
```

### Audit Trail

Track when data was processed:

```
# Example
# 2025-11-12: Processed 10 synthetic test documents for unit tests
# 2025-11-12: Created sample fixtures for normalization tests
```

## Contact

For questions about data provenance: [contact to be added]

## Updates

This document should be updated whenever:
- New data sources are added
- Data is reprocessed
- Transformations change
- Verification hashes are generated

**Last Updated**: 2025-11-12  
**Version**: 1.0
