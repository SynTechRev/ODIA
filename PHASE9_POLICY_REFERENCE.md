# Phase 9: Policy Reference Guide

## Overview

This document provides a comprehensive reference for all governance policies implemented in Phase 9 of the Oraculus-DI-Auditor Pipeline Governor.

## Policy Version

**Current Version**: 1.0.0

Policies follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes to policy structure
- **MINOR**: New policies or non-breaking changes
- **PATCH**: Bug fixes or clarifications

## Policy Categories

Policies are organized into four categories:

1. **Document Policies** - Rules for individual documents
2. **Orchestrator Policies** - Rules for multi-document jobs
3. **Security Policies** - Security and threat-related rules
4. **Analysis Policies** - Rules for analysis execution

---

## 1. Document Policies

Policies that apply to individual documents during ingestion and analysis.

### Policy: min_document_length

**Description**: Minimum document length in characters

**Type**: Document Policy  
**Severity**: Error  
**Enabled**: Yes  
**Value**: 10 characters

**Rationale**: Documents shorter than 10 characters likely contain insufficient content for meaningful analysis and may indicate malformed input.

**Violation Example**:
```json
{
  "policy": "min_document_length",
  "description": "Minimum document length in characters",
  "severity": "error",
  "actual_value": 5,
  "expected_value": 10
}
```

**Remediation**: Ensure documents contain at least 10 characters of substantive content.

---

### Policy: max_document_length

**Description**: Maximum document length in characters

**Type**: Document Policy  
**Severity**: Error  
**Enabled**: Yes  
**Value**: 10,000,000 characters (10 MB)

**Rationale**: Extremely large documents may indicate data errors, could impact system performance, and exceed reasonable processing limits.

**Violation Example**:
```json
{
  "policy": "max_document_length",
  "description": "Maximum document length in characters",
  "severity": "error",
  "actual_value": 15000000,
  "expected_value": 10000000
}
```

**Remediation**: Split large documents into smaller segments or validate the document is not corrupted.

---

### Policy: require_metadata

**Description**: Documents must include metadata

**Type**: Document Policy  
**Severity**: Warning  
**Enabled**: Yes  
**Value**: True

**Rationale**: Metadata (title, jurisdiction, etc.) improves traceability, provenance tracking, and analysis quality.

**Violation Example**:
```json
{
  "policy": "require_metadata",
  "description": "Documents must include metadata",
  "severity": "warning"
}
```

**Remediation**: Provide metadata with at least one field (e.g., title, document_id, jurisdiction).

---

## 2. Orchestrator Policies

Policies that apply to multi-document orchestration jobs.

### Policy: min_documents_per_job

**Description**: Minimum documents in orchestration job

**Type**: Orchestrator Policy  
**Severity**: Error  
**Enabled**: Yes  
**Value**: 1 document

**Rationale**: Orchestration jobs must contain at least one document to be valid.

**Violation Example**:
```json
{
  "policy": "min_documents_per_job",
  "description": "Minimum documents in orchestration job",
  "severity": "error",
  "actual_value": 0,
  "expected_value": 1
}
```

**Remediation**: Ensure at least one document is provided in the orchestration request.

---

### Policy: max_documents_per_job

**Description**: Maximum documents in single orchestration job

**Type**: Orchestrator Policy  
**Severity**: Error  
**Enabled**: Yes  
**Value**: 100 documents

**Rationale**: Jobs with more than 100 documents may cause performance degradation and exceed resource limits. For larger batches, use multiple jobs.

**Violation Example**:
```json
{
  "policy": "max_documents_per_job",
  "description": "Maximum documents in single orchestration job",
  "severity": "error",
  "actual_value": 150,
  "expected_value": 100
}
```

**Remediation**: Split large document sets into multiple orchestration jobs of 100 or fewer documents.

---

### Policy: require_cross_document_analysis

**Description**: Enable cross-document pattern analysis

**Type**: Orchestrator Policy  
**Severity**: Warning  
**Enabled**: Yes  
**Value**: True

**Rationale**: Cross-document analysis is a key feature of the orchestrator. Disabling it reduces the value of multi-document jobs.

**Violation Example**:
```json
{
  "policy": "require_cross_document_analysis",
  "description": "Enable cross-document pattern analysis",
  "severity": "warning"
}
```

**Remediation**: Enable cross-document analysis in orchestration options, or use single-document analysis endpoint instead.

---

## 3. Security Policies

Policies related to security, threats, and provenance.

### Policy: max_threat_score

**Description**: Maximum allowed threat score

**Type**: Security Policy  
**Severity**: Critical  
**Enabled**: Yes  
**Value**: 0.5 (on scale of 0.0-1.0)

**Rationale**: Documents with threat scores above 0.5 indicate medium-to-high risk of containing malicious content (XSS, SQL injection, etc.) and should be blocked.

**Violation Example**:
```json
{
  "policy": "max_threat_score",
  "description": "Maximum allowed threat score",
  "severity": "critical",
  "actual_value": 0.9,
  "expected_value": 0.5
}
```

**Remediation**: Review and sanitize document content. Remove any script tags, SQL keywords, path traversal sequences, or other suspicious patterns.

**Threat Score Calculation**:
- `0.0` - No threats detected
- `0.1-0.3` - Low risk (monitoring recommended)
- `0.3-0.5` - Medium risk (caution advised)
- `0.5-0.7` - High risk (blocked by policy)
- `0.7-1.0` - Critical risk (definitely blocked)

---

### Policy: require_provenance

**Description**: Documents must have provenance metadata

**Type**: Security Policy  
**Severity**: Warning  
**Enabled**: Yes  
**Value**: True

**Rationale**: Provenance information (source path, hash, origin) enables document verification, integrity checking, and audit trails.

**Violation Example**:
```json
{
  "policy": "require_provenance",
  "description": "Documents must have provenance metadata",
  "severity": "warning"
}
```

**Remediation**: Include provenance fields in document metadata:
- `source_path` - Original file path
- `hash` - SHA-256 hash of content
- `verified_on` - Timestamp of verification

---

### Policy: block_suspicious_patterns

**Description**: Block documents with detected threat patterns

**Type**: Security Policy  
**Severity**: Critical  
**Enabled**: Yes  
**Value**: True

**Rationale**: Documents containing known attack patterns (XSS, SQL injection, etc.) pose security risks and should be blocked.

**Violation Example**:
```json
{
  "policy": "block_suspicious_patterns",
  "description": "Block documents with detected threat patterns",
  "severity": "critical"
}
```

**Remediation**: Remove malicious patterns from document content.

**Detected Patterns**:
- **XSS**: `<script>.*</script>`, `javascript:` URIs
- **SQL Injection**: `SELECT`, `UNION`, `DROP`, `INSERT` keywords
- **Path Traversal**: `../` sequences
- **Code Injection**: `<iframe>` tags, `eval()` calls

---

## 4. Analysis Policies

Policies governing analysis execution and agent behavior.

### Policy: max_severity_threshold

**Description**: Severity threshold for escalation

**Type**: Analysis Policy  
**Severity**: High  
**Enabled**: Yes  
**Value**: 0.9 (on scale of 0.0-1.0)

**Rationale**: Documents with severity scores exceeding 0.9 indicate critical issues requiring immediate attention or escalation.

**Application**: This is an informational threshold. Documents exceeding this value may trigger additional review or alerting.

---

### Policy: require_all_agents

**Description**: All analysis agents must be available

**Type**: Analysis Policy  
**Severity**: Error  
**Enabled**: Yes  
**Value**: True

**Rationale**: Complete analysis requires all specialized agents (fiscal, constitutional, surveillance). Missing agents result in incomplete audits.

**Violation Example**:
```json
{
  "policy": "require_all_agents",
  "description": "All analysis agents must be available",
  "severity": "error"
}
```

**Remediation**: Ensure all analysis agents are properly initialized and registered with the orchestrator.

**Required Agents**:
- Fiscal Analysis Agent
- Constitutional Analysis Agent
- Surveillance Analysis Agent
- Cross-Reference Agent (if applicable)

---

### Policy: min_confidence_score

**Description**: Minimum confidence score for findings

**Type**: Analysis Policy  
**Severity**: Warning  
**Enabled**: Yes  
**Value**: 0.5 (on scale of 0.0-1.0)

**Rationale**: Findings with confidence below 0.5 may be false positives or require additional validation.

**Application**: Findings below this threshold should be reviewed manually before taking action.

---

## Policy Evaluation

### Evaluation Process

Policies are evaluated in this order:

1. **Document Policies** - Applied to each individual document
2. **Security Policies** - Applied after input sanitation
3. **Orchestrator Policies** - Applied to the entire job
4. **Analysis Policies** - Applied during agent execution

### Evaluation Results

Each policy evaluation returns:

```json
{
  "status": "compliant" | "non_compliant",
  "violations": [
    {
      "policy": "policy_name",
      "description": "Policy description",
      "severity": "error" | "warning" | "critical",
      "actual_value": "...",
      "expected_value": "..."
    }
  ],
  "warnings": [...],
  "policies_evaluated": ["policy_name_1", "policy_name_2", ...]
}
```

### Severity Levels

- **Error**: Must be fixed for processing to continue
- **Warning**: Should be addressed but won't block processing
- **Critical**: Severe security/safety issue requiring immediate block

### Status Determination

- **Compliant**: No violations of error or critical severity
- **Non-Compliant**: One or more violations of error or critical severity

---

## Compliance Reporting

### Compliance Report Structure

```json
{
  "timestamp": "ISO 8601 timestamp",
  "policy_version": "1.0.0",
  "overall_compliance": "compliant" | "non_compliant",
  "total_evaluations": 10,
  "compliant_count": 8,
  "non_compliant_count": 2,
  "total_violations": 3,
  "total_warnings": 5,
  "violations_by_severity": {
    "error": 2,
    "warning": 1,
    "critical": 0
  },
  "recommendations": [
    "Review and address all policy violations before proceeding",
    "Consider addressing warnings to improve compliance"
  ]
}
```

---

## Policy Customization

### Disabling Policies

To disable a policy (not recommended for production):

```python
from oraculus_di_auditor.governor import PolicyEngine

engine = PolicyEngine()
engine.policies['document_policies']['require_metadata']['enabled'] = False
```

### Adjusting Thresholds

To adjust policy values:

```python
from oraculus_di_auditor.governor import PolicyEngine

engine = PolicyEngine()
# Increase max documents per job to 200
engine.policies['orchestrator_policies']['max_documents_per_job']['value'] = 200
```

**Warning**: Customizing policies may impact system stability, security, or compliance. Document all changes.

---

## Policy Versioning Strategy

### Version Increments

- **Patch (1.0.X)**: Bug fixes, documentation updates
- **Minor (1.X.0)**: New policies, threshold adjustments
- **Major (X.0.0)**: Breaking changes to policy structure

### Version Storage

Policy versions are stored in the `GovernancePolicy` database model:

```sql
SELECT policy_id, policy_version, policy_type, enabled
FROM governance_policies
WHERE enabled = 1;
```

### Migration

When upgrading policy versions:

1. **Backup**: Export current policies
2. **Review**: Check changes in new version
3. **Test**: Validate new policies in test environment
4. **Deploy**: Update production policies
5. **Monitor**: Track compliance changes

---

## Best Practices

### 1. Start Strict, Relax Gradually

Begin with strict policies (current defaults) and relax only after validating the impact.

### 2. Monitor Compliance Trends

Track compliance rates over time:
- High non-compliance = policies too strict or input quality issues
- 100% compliance = policies may be too lenient

### 3. Document Exceptions

If you disable or adjust policies, document:
- **Why**: Business justification
- **When**: Date and duration
- **Who**: Approver
- **Impact**: Expected effects

### 4. Version Control Policies

Store policy configurations in version control for audit trails.

### 5. Regular Review

Review policies quarterly:
- Are thresholds appropriate?
- Are new policies needed?
- Should deprecated policies be removed?

---

## FAQ

**Q: Can I add custom policies?**  
A: Yes, extend the `PolicyEngine` class and add policies to the appropriate category.

**Q: What happens if a document violates multiple policies?**  
A: All violations are reported. The highest severity determines the enforcement action.

**Q: Can policies be different per tenant?**  
A: Not currently. Multi-tenant policies are planned for Phase 10.

**Q: How are policies enforced in the API?**  
A: Call `/governor/enforce` before processing documents. It returns `passed` or `blocked`.

**Q: Can I override a policy violation?**  
A: Not automatically. Manual override would require disabling the policy temporarily.

**Q: What's the performance impact of policy enforcement?**  
A: Minimal (~10ms per document). Deep validation adds ~50ms but is optional.

---

## Summary

Phase 9 provides 15 comprehensive policies across 4 categories:

- **Document**: 3 policies (length, metadata)
- **Orchestrator**: 3 policies (job size, cross-document analysis)
- **Security**: 3 policies (threat score, provenance, suspicious patterns)
- **Analysis**: 3 policies (severity threshold, agent availability, confidence)

All policies are:
- ✅ **Versioned** (1.0.0)
- ✅ **Deterministic** (reproducible results)
- ✅ **Documented** (this reference)
- ✅ **Testable** (43 tests)
- ✅ **Customizable** (adjustable thresholds)

For implementation details, see [PHASE9_GOVERNOR_IMPLEMENTATION.md](PHASE9_GOVERNOR_IMPLEMENTATION.md).
