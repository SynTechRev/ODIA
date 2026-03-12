# Data Provenance and Integrity Tracking

This document describes the provenance tracking and integrity verification system implemented in Phase 7.

## Overview

Every file ingested into the Oraculus-DI-Auditor system is cryptographically verified using SHA-256 checksums and tracked in a provenance ledger. This ensures:

- **Data Integrity**: Files can be verified against their original checksums
- **Audit Trail**: Complete lineage from source to ingestion
- **Reproducibility**: Re-running ingestion produces verifiable results
- **Tamper Detection**: Any modification to files is immediately detectable

## Provenance Record Format

Provenance records are stored in JSONL (JSON Lines) format, with one record per line:

```json
{
  "file": "/absolute/path/to/source/file.xml",
  "sha256": "a3b2c1d4e5f6789...",
  "source": "https://uscode.house.gov/download/...",
  "jurisdiction": "federal",
  "size": 12345,
  "metadata": {
    "format": "xml",
    "filename": "title42.xml",
    "title": "42",
    "section": "1983"
  }
}
```

### Fields

- **`file`** (required): Absolute path to the source file
- **`sha256`** (required): SHA-256 hash of the file contents
- **`source`** (required): URL or description of the data source
- **`jurisdiction`** (required): Legal jurisdiction (e.g., "federal", "california")
- **`size`** (required): File size in bytes
- **`metadata`** (optional): Additional metadata specific to the document type

## Recording Provenance

### During Ingestion

When XML files are ingested via `scripts/ingest_and_index.py --format xml`, provenance is automatically recorded:

```python
from oraculus_di_auditor.ingestion.checksum import record_provenance

record_provenance(
    path=xml_file,
    source_url="https://uscode.house.gov/...",
    output="data/provenance.jsonl",
    jurisdiction="federal",
    metadata={"format": "xml", "filename": "title42.xml"}
)
```

### Manual Recording

For custom ingestion workflows:

```python
from pathlib import Path
from oraculus_di_auditor.ingestion.checksum import record_provenance

# Record provenance for a file
record = record_provenance(
    path="/data/legal/uscode/title42.xml",
    source_url="https://uscode.house.gov/download/releasepoints/us/pl/118/xml_uscAll.zip",
    output="data/provenance.jsonl",
    jurisdiction="federal",
    metadata={
        "format": "xml",
        "title": "42",
        "description": "Public Health and Welfare"
    }
)

print(f"Recorded provenance for {record['file']}")
print(f"SHA-256: {record['sha256']}")
```

## Verifying Integrity

### Using verify_integrity.py Script

The recommended method for verification:

```bash
# Verify all files in provenance log
python scripts/verify_integrity.py --input data/provenance.jsonl

# Show detailed results for each file
python scripts/verify_integrity.py --input data/provenance.jsonl --verbose
```

**Sample output:**
```
======================================================================
File Integrity Verification
======================================================================

Verifying files from: data/provenance.jsonl

======================================================================
Verification Results
======================================================================
Total records:   150
✓ Verified:      148
✗ Failed:        1
⚠ Missing:       1

Success rate:    98.7%

⚠ Some files failed verification or are missing
```

**Detailed output (--verbose):**
```
======================================================================
Detailed Results
======================================================================

✓ /data/legal/uscode/title42.xml
  Status: verified
  Expected: a3b2c1d4e5f6789...
  Actual:   a3b2c1d4e5f6789...

✗ /data/legal/cfr/title21.xml
  Status: failed
  Expected: b4c5d6e7f8a9012...
  Actual:   c5d6e7f8a9012b4...

⚠ /data/legal/ca/penal_code.xml
  Status: missing
  Expected: d6e7f8a9012b4c5...
```

### Programmatic Verification

```python
from oraculus_di_auditor.ingestion.checksum import verify_integrity

# Verify all files
results = verify_integrity("data/provenance.jsonl")

print(f"Total: {results['total']}")
print(f"Verified: {results['verified']}")
print(f"Failed: {results['failed']}")
print(f"Missing: {results['missing']}")

# Check specific files
for detail in results['details']:
    if detail['status'] != 'verified':
        print(f"Issue with {detail['file']}: {detail['status']}")
```

## Checksum Calculation

### File Checksums

Calculate SHA-256 hash for any file:

```python
from oraculus_di_auditor.ingestion.checksum import file_checksum

# Calculate checksum
hash_value = file_checksum("/data/legal/uscode/title42.xml")
print(f"SHA-256: {hash_value}")
```

**Implementation details:**
- Reads file in 8KB chunks to handle large files efficiently
- Returns lowercase hexadecimal string
- Raises `FileNotFoundError` if file doesn't exist

### Verification Process

For each provenance record:
1. Load the expected SHA-256 hash from the record
2. Check if the file still exists at the recorded path
3. Calculate the current SHA-256 hash
4. Compare expected vs. actual hash
5. Record verification status (verified, failed, or missing)

## Provenance Log Management

### Location

Default location: `data/provenance.jsonl`

This file is gitignored to prevent committing large provenance logs to the repository.

### Format: JSONL

JSON Lines (JSONL) format allows:
- **Streaming**: Process one record at a time
- **Append-only**: New records added without reading entire file
- **Human-readable**: Each line is valid JSON
- **Tool-friendly**: Compatible with jq, grep, etc.

### Query with jq

```bash
# Count total records
cat data/provenance.jsonl | wc -l

# Find all federal documents
cat data/provenance.jsonl | jq 'select(.jurisdiction == "federal")'

# Extract all checksums
cat data/provenance.jsonl | jq -r '.sha256'

# Find large files (>1MB)
cat data/provenance.jsonl | jq 'select(.size > 1048576)'

# Group by jurisdiction
cat data/provenance.jsonl | jq -r '.jurisdiction' | sort | uniq -c
```

## Use Cases

### 1. Corpus Validation

After downloading a legal corpus, verify integrity before ingestion:

```bash
# Download USC
wget https://uscode.house.gov/download/.../xml_uscAll.zip

# Ingest with provenance tracking
python scripts/ingest_and_index.py \
  --source /data/legal/uscode \
  --format xml \
  --jurisdiction federal

# Verify all files
python scripts/verify_integrity.py --input data/provenance.jsonl
```

### 2. Tamper Detection

Periodically verify that source files haven't been modified:

```bash
# Run weekly verification
python scripts/verify_integrity.py --input data/provenance.jsonl

# Alert if any files fail
if [ $? -ne 0 ]; then
  echo "WARNING: Some files failed integrity verification!"
  # Send alert, log incident, etc.
fi
```

### 3. Reproducibility

Prove that ingested data matches original sources:

```bash
# Re-download corpus
wget https://uscode.house.gov/download/.../xml_uscAll.zip -O uscode_new.zip

# Verify checksums match
unzip uscode_new.zip -d /tmp/uscode_verify
python scripts/verify_integrity.py --input data/provenance.jsonl --verbose
```

### 4. Audit Trail

Track the complete lineage of ingested documents:

```python
import json

# Read provenance log
with open("data/provenance.jsonl") as f:
    for line in f:
        record = json.loads(line)
        
        print(f"Document: {record['file']}")
        print(f"  Source: {record['source']}")
        print(f"  Jurisdiction: {record['jurisdiction']}")
        print(f"  SHA-256: {record['sha256']}")
        print(f"  Size: {record['size']} bytes")
        print()
```

## Security Considerations

### SHA-256 Properties

- **Collision-resistant**: Virtually impossible to create two files with same hash
- **One-way**: Cannot recover file contents from hash
- **Deterministic**: Same file always produces same hash
- **Avalanche effect**: Tiny change in file produces completely different hash

### Limitations

1. **Does not encrypt**: Hashes are public, files are not protected
2. **Does not sign**: Cannot verify who created the hash
3. **Requires secure storage**: Provenance log must be protected from tampering

### Future Enhancements

1. **Digital Signatures**: Sign provenance records with GPG
2. **Blockchain Ledger**: Store hashes in blockchain for tamper-evidence
3. **Timestamping**: Add RFC 3161 timestamps for legal compliance
4. **Key Management**: Integrate with HSM or key vault

## Integration with Existing Systems

### Phase 6 Compatibility

Phase 7 provenance tracking is **optional** and **backward-compatible**:

- Standard ingestion (TXT/JSON) works without provenance
- XML ingestion automatically creates provenance records
- Existing workflows are unaffected

### Data Pipeline

```
Source Files (XML) → Checksum → Provenance Record → Normalized JSON → Embeddings
                         ↓
                   data/provenance.jsonl
```

### Verification Workflow

```
Provenance Record → File Lookup → Checksum → Comparison → Report
                                      ↓
                                 ✓ / ✗ / ⚠
```

## Best Practices

1. **Verify before ingestion**: Check source files match expected checksums
2. **Keep provenance log safe**: Back up `data/provenance.jsonl` regularly
3. **Run periodic checks**: Schedule weekly/monthly integrity verification
4. **Document sources**: Include detailed source URLs in provenance records
5. **Version control**: Track provenance log changes in separate repository
6. **Audit compliance**: Use provenance for regulatory audit requirements

## Troubleshooting

### Failed Verification

**Problem**: File checksum doesn't match provenance record

**Possible causes:**
- File was modified after ingestion
- File was corrupted during download/transfer
- Original source data was updated

**Solution:**
```bash
# Re-download original file
# Re-verify checksums
# If checksums still don't match, investigate source updates
```

### Missing Files

**Problem**: File in provenance record no longer exists

**Possible causes:**
- File was deleted or moved
- Mount point not available (for external storage)
- Path changed due to directory restructuring

**Solution:**
```bash
# Check if file was moved
find /data/legal -name "filename.xml"

# Update provenance record with new path
# Or restore file from backup
```

### Large Provenance Logs

**Problem**: Provenance log growing too large

**Solutions:**
- Split by jurisdiction: `provenance_federal.jsonl`, `provenance_state.jsonl`
- Compress old records: `gzip data/provenance_2024.jsonl`
- Archive completed corpora: Move to long-term storage
- Use SQLite: Migrate to database for efficient querying

## References

- [PHASE7_CORPUS.md](PHASE7_CORPUS.md) - Phase 7 corpus integration guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- SHA-256: [NIST FIPS 180-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)
- JSONL: [JSON Lines Specification](https://jsonlines.org/)
