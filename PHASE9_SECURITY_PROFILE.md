# Phase 9: Security Profile Reference

## Overview

This document describes the security features, threat detection capabilities, and security posture management implemented in Phase 9 of the Oraculus-DI-Auditor Pipeline Governor.

## Security Architecture

### Defense in Depth

Phase 9 implements multiple layers of security:

1. **Input Validation** - Validate document format and structure
2. **Threat Detection** - Identify malicious patterns
3. **Input Sanitation** - Remove or flag dangerous content
4. **MIME Validation** - Enforce allowed file types
5. **Provenance Verification** - Validate document origin
6. **Threat Scoring** - Quantify overall risk level
7. **Rate Limiting** - Detect and prevent abuse
8. **Policy Enforcement** - Apply security policies

### Security Gatekeeper

The `SecurityGatekeeper` class is the central component for security enforcement.

**Responsibilities:**
- Pattern-based threat detection
- Input sanitation
- MIME type validation
- Provenance checking
- Threat score calculation
- Rate limit monitoring
- Security profile generation

---

## Threat Detection

### Detected Threat Types

#### 1. Cross-Site Scripting (XSS)

**Pattern**: `<script[^>]*>.*?</script>`  
**Threat Type**: `xss`  
**Severity**: 0.9 (Critical)

**Description**: Detects embedded JavaScript code that could be executed in a browser context.

**Examples**:
```html
<script>alert('XSS')</script>
<script src="evil.js"></script>
<SCRIPT>malicious()</SCRIPT>
```

**Remediation**: Remove all `<script>` tags and associated code.

---

#### 2. JavaScript Injection

**Pattern**: `javascript:`  
**Threat Type**: `javascript_injection`  
**Severity**: 0.8 (High)

**Description**: Detects JavaScript protocol URIs that could execute code when clicked.

**Examples**:
```html
<a href="javascript:alert('XSS')">Click</a>
javascript:void(0)
JAVASCRIPT:malicious()
```

**Remediation**: Replace with safe URI schemes (http, https, mailto, etc.).

---

#### 3. SQL Injection

**Pattern**: `(union|select|insert|update|delete|drop)\s+`  
**Threat Type**: `sql_injection`  
**Severity**: 0.7 (High)

**Description**: Detects SQL keywords that could indicate SQL injection attempts.

**Examples**:
```sql
SELECT * FROM users WHERE id=1
UNION SELECT password FROM users
DROP TABLE documents;
```

**Remediation**: If legitimate SQL code is needed in documentation, use code blocks or escaping. Otherwise, remove SQL keywords.

---

#### 4. Path Traversal

**Pattern**: `\.\./`  
**Threat Type**: `path_traversal`  
**Severity**: 0.8 (High)

**Description**: Detects directory traversal sequences that could access unauthorized files.

**Examples**:
```
../../etc/passwd
../../../secret/file.txt
..\..\Windows\System32
```

**Remediation**: Remove path traversal sequences. Use absolute paths or validate paths against whitelist.

---

#### 5. iframe Injection

**Pattern**: `<iframe[^>]*>`  
**Threat Type**: `iframe_injection`  
**Severity**: 0.7 (High)

**Description**: Detects iframe tags that could embed malicious content or phishing pages.

**Examples**:
```html
<iframe src="http://evil.com"></iframe>
<IFRAME SRC="javascript:alert('XSS')"></IFRAME>
```

**Remediation**: Remove iframe tags or validate source URLs against whitelist.

---

## Threat Scoring

### Score Calculation

Threat scores range from 0.0 (no threats) to 1.0 (critical threats).

**Calculation Method**:
1. Scan document text and metadata for all threat patterns
2. For each detected threat, record the pattern's severity
3. Overall threat score = maximum severity of all detected threats

**Example**:
```
Document contains:
  - XSS pattern (severity 0.9)
  - SQL injection pattern (severity 0.7)

Overall threat score = max(0.9, 0.7) = 0.9
```

### Risk Levels

| Score Range | Risk Level | Action | Description |
|-------------|------------|--------|-------------|
| 0.0 | None | Allow | No threats detected |
| 0.1-0.3 | Low | Monitor | Minor patterns detected, low risk |
| 0.3-0.5 | Medium | Warn | Moderate risk, review recommended |
| 0.5-0.7 | High | Block | High risk, block by default policy |
| 0.7-1.0 | Critical | Block | Critical risk, immediate block |

### Threat Score API

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()
threat_score = gatekeeper.calculate_threat_score(
    document_text="<script>alert('test')</script>",
    metadata={"title": "Test"}
)
print(f"Threat Score: {threat_score}")  # Output: 0.9
```

---

## Input Sanitation

### Sanitation Process

The `sanitize_input()` method performs comprehensive threat detection:

1. **Document Text Scan** - Check document content for threat patterns
2. **Metadata Scan** - Check all metadata string values
3. **Threat Aggregation** - Collect all detected threats
4. **Score Calculation** - Determine overall threat score
5. **Status Determination** - Return "clean" or "threat_detected"

### Sanitation Result Structure

```json
{
  "status": "clean" | "threat_detected",
  "threats_detected": [
    {
      "type": "xss",
      "severity": 0.9,
      "description": "Detected xss pattern"
    },
    {
      "type": "sql_injection",
      "severity": 0.7,
      "description": "Detected sql_injection in metadata field 'description'",
      "field": "description"
    }
  ],
  "sanitized_text": "original document text",
  "sanitized_metadata": { /* original metadata */ },
  "threat_score": 0.9
}
```

### Example Usage

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()

# Clean document
result = gatekeeper.sanitize_input(
    "This is a clean document.",
    {"title": "Test"}
)
assert result['status'] == 'clean'
assert result['threat_score'] == 0.0

# Malicious document
result = gatekeeper.sanitize_input(
    "<script>alert('xss')</script>",
    {"title": "Test"}
)
assert result['status'] == 'threat_detected'
assert result['threat_score'] > 0.7
```

---

## MIME Type Validation

### Allowed MIME Types

The following MIME types are permitted:

- `text/plain` - Plain text documents
- `application/json` - JSON documents
- `application/pdf` - PDF documents
- `application/xml` - XML documents
- `text/xml` - XML documents (alternate)

### Validation Process

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()

# Valid MIME type
result = gatekeeper.validate_mime_type("text/plain")
assert result['valid'] is True

# Invalid MIME type
result = gatekeeper.validate_mime_type("application/x-executable")
assert result['valid'] is False
assert 'error' in result
```

### Adding Custom MIME Types

To extend allowed types:

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()
gatekeeper.allowed_mime_types.append("application/vnd.custom")
```

---

## Provenance Validation

### What is Provenance?

Provenance tracks document origin, source, and integrity:

- **Document ID**: Unique identifier
- **Source Path**: Original file location
- **Hash**: SHA-256 checksum for integrity
- **Timestamp**: When document was verified

### Validation Checks

1. **Document ID Length** - Must be at least 8 characters
2. **Path Traversal Detection** - No `../` in source path
3. **Hash Format** - 64 hex characters for SHA-256

### Validation Result

```json
{
  "status": "valid" | "warning" | "error",
  "document_id": "doc_12345678",
  "provenance_verified": true,
  "warnings": [
    "Document ID too short or missing",
    "Path traversal detected in source_path",
    "Invalid hash format"
  ]
}
```

### Example Usage

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()

# Valid provenance
result = gatekeeper.validate_provenance(
    document_id="doc_12345678",
    source_path="/data/legal/uscode/title18.xml",
    expected_hash="a" * 64  # Valid SHA-256
)
assert result['status'] == 'valid'
assert result['provenance_verified'] is True

# Path traversal attack
result = gatekeeper.validate_provenance(
    document_id="doc_12345678",
    source_path="../../../etc/passwd"
)
assert result['status'] == 'error'
```

---

## Rate Limiting

### Rate Limit Thresholds

Request rates are monitored per minute:

| Threshold | Status | Action | Description |
|-----------|--------|--------|-------------|
| < 100 RPM | Normal | Allow | Normal traffic |
| 100-300 RPM | Warning | Monitor | Elevated traffic, monitor closely |
| > 300 RPM | Critical | Block | Potential abuse, block requests |

### Rate Limit Check

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()

# Normal traffic (10 requests in 60 seconds = 10 RPM)
result = gatekeeper.check_rate_limit_posture(10, 60)
assert result['status'] == 'normal'
assert result['action'] == 'allow'

# Warning level (150 requests in 60 seconds = 150 RPM)
result = gatekeeper.check_rate_limit_posture(150, 60)
assert result['status'] == 'warning'
assert result['action'] == 'monitor'

# Critical level (400 requests in 60 seconds = 400 RPM)
result = gatekeeper.check_rate_limit_posture(400, 60)
assert result['status'] == 'critical'
assert result['action'] == 'block'
```

---

## Security Profile

### What is a Security Profile?

A comprehensive security assessment of a document including:

- Input sanitation results
- Provenance validation
- MIME type validation (if provided)
- Overall threat score
- Security status

### Profile Generation

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()

profile = gatekeeper.generate_security_profile(
    document_text="Clean document text",
    metadata={
        "document_id": "doc_12345678",
        "title": "Test Document"
    },
    mime_type="text/plain"
)
```

### Profile Structure

```json
{
  "timestamp": "2025-11-19T18:55:32Z",
  "overall_status": "secure" | "warning" | "critical" | "error",
  "checks": {
    "input_sanitation": {
      "status": "clean",
      "threats_detected": [],
      "threat_score": 0.0
    },
    "provenance": {
      "status": "valid",
      "provenance_verified": false,
      "warnings": []
    },
    "mime_validation": {
      "valid": true,
      "mime_type": "text/plain"
    }
  },
  "threat_score": 0.0
}
```

### Status Determination

- **secure**: No threats, threat_score < 0.3
- **warning**: Minor issues, threat_score 0.3-0.7
- **critical**: High threat_score > 0.7
- **error**: Critical check failures

---

## Security Events

### Event Tracking

Security events are stored in the `SecurityEvent` database model:

**Event Types**:
- `threat_detected` - Malicious pattern found
- `policy_violation` - Security policy violated
- `sanitation` - Input sanitized

**Severity Levels**:
- `low` - Informational
- `medium` - Requires monitoring
- `high` - Requires attention
- `critical` - Requires immediate action

### Event Structure

```sql
CREATE TABLE security_events (
    id INTEGER PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    severity VARCHAR(20) NOT NULL,
    threat_score FLOAT DEFAULT 0.0,
    document_id VARCHAR(255),
    event_details_json TEXT
);
```

---

## Security Best Practices

### 1. Always Validate Input

Use the Security Gatekeeper for all external input:

```python
from oraculus_di_auditor.governor import SecurityGatekeeper

gatekeeper = SecurityGatekeeper()

# Before processing any document
result = gatekeeper.sanitize_input(document_text, metadata)
if result['status'] == 'threat_detected':
    log_security_event(result)
    raise SecurityException("Malicious content detected")
```

### 2. Monitor Threat Scores

Track threat score trends over time:

```python
# Log threat scores for analysis
scores = []
for document in documents:
    score = gatekeeper.calculate_threat_score(document.text, document.metadata)
    scores.append(score)

avg_score = sum(scores) / len(scores)
if avg_score > 0.3:
    alert("Elevated threat level detected")
```

### 3. Validate Provenance

Always include provenance for auditable documents:

```python
metadata = {
    "document_id": "doc_12345678",
    "source_path": "/data/legal/document.pdf",
    "hash": hashlib.sha256(content).hexdigest(),
    "verified_on": datetime.now(UTC).isoformat()
}
```

### 4. Use Security Profiles

Generate profiles for compliance reporting:

```python
profile = gatekeeper.generate_security_profile(
    document_text, metadata, mime_type
)

# Store for audit trail
store_security_profile(profile)
```

### 5. Implement Rate Limiting

Monitor and enforce rate limits at the application level:

```python
from collections import defaultdict
from datetime import datetime, timedelta

request_counts = defaultdict(int)

def check_rate_limit(client_id):
    now = datetime.now()
    window_start = now - timedelta(minutes=1)
    
    # Count requests in last minute
    count = request_counts[client_id]
    
    result = gatekeeper.check_rate_limit_posture(count, 60)
    if result['action'] == 'block':
        raise RateLimitException("Rate limit exceeded")
```

---

## Security Limitations

### Current Limitations

1. **Pattern-Based Detection**: Uses regex patterns, not ML-based detection
2. **No Deep Content Analysis**: Surface-level scanning only
3. **Static Threat Database**: Patterns must be manually updated
4. **No Encryption**: Data at rest not encrypted
5. **Single-Tenant**: No multi-tenant isolation
6. **Local Only**: No distributed security coordination

### Mitigation Strategies

1. **Regular Pattern Updates**: Review and update threat patterns quarterly
2. **Manual Review**: High-risk documents should be manually reviewed
3. **Defense in Depth**: Combine with application-level security
4. **Logging**: Comprehensive security event logging
5. **Monitoring**: Active threat score monitoring

---

## Future Enhancements

Planned for Phase 10 and beyond:

1. **ML-Based Threat Detection** - Train models on known threats
2. **Deep Content Analysis** - Semantic threat detection
3. **Encryption** - Encrypt sensitive data at rest and in transit
4. **Multi-Tenant Isolation** - Per-tenant security policies
5. **Distributed Security** - Federated threat intelligence
6. **Automated Response** - Auto-quarantine high-threat documents
7. **Threat Intelligence Integration** - External threat feeds
8. **Behavioral Analysis** - Detect anomalous usage patterns

---

## Security Incident Response

### When a Threat is Detected

1. **Log Event**: Record in `SecurityEvent` table
2. **Calculate Threat Score**: Determine severity
3. **Enforce Policy**: Apply `max_threat_score` policy
4. **Alert**: Notify security team if critical
5. **Quarantine**: Isolate document if score > 0.7
6. **Investigate**: Manual review for false positives
7. **Report**: Generate incident report

### Incident Report Template

```json
{
  "incident_id": "INC-2025-001",
  "timestamp": "2025-11-19T18:55:32Z",
  "threat_score": 0.9,
  "document_id": "doc_suspicious_001",
  "threats_detected": [
    {
      "type": "xss",
      "severity": 0.9,
      "description": "Detected xss pattern"
    }
  ],
  "action_taken": "Document quarantined",
  "status": "under_investigation"
}
```

---

## Summary

Phase 9 Security Profile provides:

✅ **5 Threat Types** - XSS, SQL injection, path traversal, JavaScript injection, iframe injection  
✅ **Threat Scoring** - 0.0-1.0 scale with risk levels  
✅ **Input Sanitation** - Comprehensive pattern detection  
✅ **MIME Validation** - Whitelist-based file type enforcement  
✅ **Provenance Validation** - Origin and integrity checking  
✅ **Rate Limiting** - Request rate monitoring and enforcement  
✅ **Security Profiles** - Comprehensive security assessment  
✅ **Event Tracking** - Database logging of security events  

**Security Posture: Active and Monitoring**

For implementation details, see [PHASE9_GOVERNOR_IMPLEMENTATION.md](PHASE9_GOVERNOR_IMPLEMENTATION.md).
