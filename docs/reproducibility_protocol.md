# Reproducibility Protocol

This document describes the reproducibility guarantees and verification protocols for the Oraculus-DI-Auditor system.

## Determinism Guarantees

The Oraculus-DI-Auditor is designed for **complete deterministic execution**:

### Core Principles

1. **Same Input → Same Output**
   - Given identical corpus data, the analysis produces byte-identical results
   - No random number generation without deterministic seeding
   - No external API dependencies during analysis

2. **Cryptographic Seeding**
   - Random operations use SHA-256 hashes of input data as seeds
   - Seeds are derived from canonical input representations
   - Internal Linear Congruential Generator (LCG) ensures reproducibility

3. **Canonical Data Representation**
   - JSON outputs use consistent key ordering
   - Floating-point numbers use 6-decimal precision
   - Timestamps use UTC with Z suffix

### Implementation Details

```python
# Canonical input serialization
def canonicalize_input(data: dict) -> str:
    """Create canonical string representation for hashing."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

# Seed derivation
def seed_from_input(data: dict) -> int:
    """Derive deterministic seed from input data."""
    canonical = canonicalize_input(data)
    hash_bytes = hashlib.sha256(canonical.encode()).digest()
    return int.from_bytes(hash_bytes[:8], 'big')
```

## Verification Protocol

### Step 1: Environment Verification

Verify the execution environment matches requirements:

```bash
# Check Python version
python3 --version
# Expected: Python 3.11.x or higher

# Check dependencies
pip list | grep -E "(pypdf|jsonschema|scikit-learn|numpy)"
```

### Step 2: Repository Verification

Verify repository integrity:

```bash
# Clone fresh copy
git clone https://github.com/SynTechRev/Oraculus-DI-Auditor.git
cd Oraculus-DI-Auditor

# Verify commit hash (if provided)
git log -1 --format="%H"
```

### Step 3: Input Verification

Verify corpus data integrity:

```bash
# Check corpus manifest
cat transparency_release/corpus_manifest.json | jq '.total_corpora'
# Expected: 36

# Verify corpus structure
ls oraculus/corpus/ | wc -l
# Expected: 36+ (includes index files)
```

### Step 4: Execution

Run the reproducibility script:

```bash
cd transparency_release/scripts
chmod +x reproduce_audit.sh
./reproduce_audit.sh --full
```

### Step 5: Hash Verification

Verify output hashes match published values:

```bash
cd transparency_release
sha256sum -c HASH_MANIFEST_FULL_SHA256.txt
# Expected: All files show "OK"
```

## Reproducibility Certification

### Self-Test

Run the self-test to verify determinism:

```bash
# First run
./reproduce_audit.sh --full
cp HASH_MANIFEST_FULL_SHA256.txt /tmp/run1.txt

# Second run
./reproduce_audit.sh --full

# Compare
diff HASH_MANIFEST_FULL_SHA256.txt /tmp/run1.txt
# Expected: No differences (empty output)
```

### Cross-Platform Verification

The system has been verified on:

| Platform | Python | Status |
|----------|--------|--------|
| Ubuntu 20.04 LTS | 3.11 | ✅ Verified |
| Ubuntu 22.04 LTS | 3.11 | ✅ Verified |
| macOS 12+ | 3.11 | ✅ Verified |
| Windows 10+ (WSL2) | 3.11 | ✅ Verified |

### Known Limitations

1. **Floating-Point Precision**
   - Minor platform-specific variations possible in floating-point calculations
   - Mitigated by 6-decimal rounding in outputs

2. **File System Ordering**
   - Different file systems may return files in different order
   - Mitigated by explicit sorting in all operations

3. **Timestamp Precision**
   - Timestamps are execution-time dependent
   - Not included in determinism verification (excluded from hash)

## Audit Trail

### Execution Logging

Each execution generates an audit trail:

```json
{
  "execution_id": "sha256_of_start_time_and_params",
  "start_time": "2025-12-06T04:30:00.000000Z",
  "end_time": "2025-12-06T04:35:00.000000Z",
  "parameters": {
    "corpus_root": "oraculus/corpus",
    "year_range": "2014-2025"
  },
  "output_hash": "sha256_of_all_outputs",
  "status": "success"
}
```

### Provenance Tracking

Every output file includes provenance metadata:

```json
{
  "generated_at": "2025-12-06T04:30:00.000000Z",
  "generator_version": "1.0",
  "input_hash": "sha256_of_input_data",
  "output_hash": "sha256_of_this_file"
}
```

## Failure Modes

### Hash Mismatch

If hash verification fails:

1. **Check Python version** – Must be 3.11+
2. **Check dependencies** – Run `pip install -r requirements.txt`
3. **Check line endings** – Ensure Unix-style (LF, not CRLF)
4. **Check locale** – Set `LC_ALL=C` for consistent sorting

### Execution Errors

If execution fails:

1. **Check PYTHONPATH** – Must include `src/` and repository root
2. **Check corpus data** – Ensure corpus directories exist
3. **Check permissions** – Ensure write access to output directories

## Security Considerations

### Input Validation

All inputs are validated before processing:
- File paths are sanitized
- JSON inputs are schema-validated
- No code execution from untrusted inputs

### Output Sanitization

All outputs are sanitized before publication:
- No internal paths exposed
- No credentials or secrets
- No user-identifiable information

### Hash Algorithm

SHA-256 is used for all cryptographic hashing:
- 256-bit output
- Collision-resistant
- Widely supported and audited

## External Verification Services

For third-party verification, the following services can be used:

1. **Git Commit Signature**
   - Verify commit signatures on GitHub
   - Reference: Repository settings → Branch protection

2. **Hash Publication**
   - Hash manifests can be published to blockchain or timestamping services
   - Reference: RFC 3161 Timestamping

3. **Independent Audit**
   - Third-party auditors can run reproducibility script
   - Reference: HOW_TO_REPRODUCE_THE_AUDIT.md

---

*This document is part of the Oraculus-DI-Auditor documentation suite.*
