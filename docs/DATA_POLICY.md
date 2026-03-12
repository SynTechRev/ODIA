# Data Policy - Oraculus DI Auditor

## Overview

The Oraculus DI Auditor processes sensitive legal documents including statutes, cases, and contracts. This document outlines our data handling, privacy, and security policies.

## Data Classification

### Public Data
- Published statutes (U.S. Code, CFR)
- Public court decisions
- Published regulations

**Policy**: May be committed to version control in normalized form

### Proprietary Data
- Unpublished legal documents
- Client contracts
- Internal legal analyses
- Personally identifiable information (PII)

**Policy**: MUST NOT be committed to version control

## Repository Data Handling

### Gitignored Directories

The following directories are gitignored and should contain sensitive/large data:

- `data/sources/` - Raw source files (may contain proprietary documents)
- `data/raw/` - Unprocessed data
- Any directory containing client-specific information

### Tracked Directories

These directories are tracked but should only contain:

- `data/cases/` - Normalized JSON (anonymized if needed)
- `data/statutes/` - Public statute data
- `tests/fixtures/` - Small sample data for testing (non-sensitive only)

## Data Processing Guidelines

### 1. Local Processing Only

**REQUIREMENT**: All document processing MUST occur locally

- No external API calls for document analysis
- No cloud storage of source documents
- No transmission of proprietary content

### 2. Source File Management

**For Proprietary Sources**:
1. Store in `data/sources/` (automatically gitignored)
2. Process using local CLI tools
3. Review normalized output before any sharing
4. Delete source files after processing if required

**For Public Sources**:
1. Document the source URL/reference
2. Add citation metadata
3. May be committed after normalization

### 3. Anonymization

Before sharing any processed data:

1. **Remove PII**: Names, addresses, identifiers
2. **Redact Sensitive Info**: Financial details, confidential clauses
3. **Use Document IDs**: Replace real names with anonymized IDs
4. **Review Output**: Manual review before commit

## Collaboration Guidelines

### Sharing Processed Data

When sharing with collaborators:

1. **Use Secure Channels**: Encrypted file transfer, secure cloud
2. **Document Provenance**: Track data lineage
3. **Access Control**: Limit access to need-to-know basis
4. **Retention Policy**: Delete after analysis complete

### Adding New Data Sources

1. Classify the data (public vs. proprietary)
2. Document in `docs/PROVENANCE.md`
3. Ensure appropriate `.gitignore` rules
4. Add processing notes to repository README

## Compliance

### Legal Requirements

- **Copyright**: Respect copyright for all documents
- **Licensing**: Honor source licenses (e.g., Creative Commons)
- **Confidentiality**: Maintain attorney-client privilege where applicable

### Audit Trail

Maintain records of:
- Source document origins
- Processing timestamps
- Data transformations applied
- Access logs (for sensitive data)

## Security Measures

### File System Security

- Restrict permissions on `data/sources/` directory
- Use encrypted file systems for sensitive data
- Regular security audits of data storage

### Code Security

- No hardcoded credentials
- No embedded API keys
- Use environment variables for configuration
- Security scanning of dependencies

## Data Retention

### Development Data

- Test fixtures: Retain indefinitely (non-sensitive only)
- Temporary processing: Delete after 30 days
- Logs: Retain for 90 days

### Production Data

- Source files: Per client agreement
- Normalized data: Per project requirements
- Reports: Archive for compliance period

## Incident Response

### Data Breach Protocol

1. **Immediate**: Revoke access, secure systems
2. **Assessment**: Determine scope of exposure
3. **Notification**: Inform affected parties per legal requirements
4. **Remediation**: Patch vulnerabilities, update policies

### Contact

For security concerns: [security contact to be added]

## Policy Updates

This policy will be reviewed quarterly and updated as needed.

**Last Updated**: 2025-11-12  
**Version**: 1.0  
**Owner**: Project Maintainer
