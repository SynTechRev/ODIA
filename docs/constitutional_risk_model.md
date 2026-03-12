# Constitutional Risk Model

This document details the JIM risk scoring methodology and severity classification.

**Updated:** December 6, 2025 (CLEP-v1)

---

## Overview

JIM employs an **eight-dimensional risk scoring model** to assess constitutional and administrative law compliance. Each dimension receives a component score (0.0-1.0), which is weighted and aggregated into an overall risk score.

**Version History:**
- **Baseline (v1.0):** 6 dimensions, weights totaling 100%
- **CLEP-v1 (v1.1):** 8 dimensions (+digital privacy, +accountability), rebalanced weights

---

## Risk Dimensions

### 1. Due Process Conflict (Weight: 20%)

**Scoring Factors**:

| Factor | Score Contribution | Trigger |
|--------|-------------------|---------|
| Due process doctrine linked | +0.4 | Doctrine identified |
| Procedural irregularity | +0.3 | metadata_break, missing_notice, insufficient_hearing |
| Property/liberty interest affected | +0.2 | affects_rights flag |
| Timeline violation | +0.1 | timeline_irregularity flag |

**Maximum Component Score**: 1.0 (capped)

**Rationale**: Due process is foundational; violations carry high weight.  
**CLEP-v1 Change**: Weight reduced from 25% to 20% to accommodate new dimensions.

---

### 2. Delegation Issues (Weight: 15%)

**Scoring Factors**:

| Factor | Score Contribution | Trigger |
|--------|-------------------|---------|
| Non-delegation doctrine linked | +0.4 | Doctrine identified |
| Lacks statutory standards | +0.3 | lacks_standards flag |
| Unlimited discretion | +0.2 | unlimited_discretion flag |
| Major questions applicable | +0.1 | major_questions_applicable |

**Rationale**: Core separation of powers; significant constitutional concern.  
**CLEP-v1 Change**: Weight reduced from 20% to 15% to accommodate new dimensions.

---

### 3. Fourth Amendment Concerns (Weight: 20%)

**Scoring Factors**:

| Factor | Score Contribution | Trigger |
|--------|-------------------|---------|
| Fourth Amendment doctrine linked | +0.4 | Doctrine identified |
| Surveillance involvement | +0.3 | involves_surveillance flag |
| Warrantless activity | +0.2 | lacks_warrant flag |
| Privacy expectation | +0.1 | privacy_expectation flag |

**Rationale**: Privacy fundamental right; digital age heightens concern.  
**CLEP-v1 Change**: Weight unchanged at 20%; expanded with digital privacy dimension.

---

### 4. Administrative Overreach (Weight: 12%)

**Scoring Factors**:

| Factor | Score Contribution | Trigger |
|--------|-------------------|---------|
| Administrative law doctrine linked | +0.3 | Doctrine identified |
| Lacks reasoning | +0.3 | lacks_reasoning flag |
| Ignored relevant factors | +0.2 | ignored_factors flag |
| Departure without explanation | +0.2 | departure_without_explanation |

**Rationale**: Post-Loper Bright, agency actions face heightened scrutiny.  
**CLEP-v1 Change**: Weight reduced from 15% to 12% to accommodate new dimensions.

---

### 5. Metadata Integrity (Weight: 10%)

**Scoring Factors**:

| Forensic Score | Component Score | Impact |
|---------------|----------------|--------|
| < 50 | +0.5 | Critical forensic failure |
| 50-69 | +0.3 | Significant anomalies |
| 70-84 | +0.1 | Minor irregularities |
| ≥ 85 | 0.0 | Acceptable |

**Additional Factors**:
- Timestamp conflict: +0.3
- Producer mismatch: +0.2

**Rationale**: Documentary integrity affects evidentiary admissibility.  
**CLEP-v1 Change**: Weight reduced from 12% to 10% to accommodate new dimensions.

---

### 6. Chain of Custody (Weight: 8%)

**Scoring Factors**:

| Factor | Score Contribution | Trigger |
|--------|-------------------|---------|
| Missing custody record | +0.4 | missing_custody_record flag |
| Custody gap | +0.3 | custody_gap flag |
| Unverified handler | +0.2 | unverified_handler flag |
| Incomplete trail | +0.1 | incomplete_trail flag |

**Rationale**: Essential for evidentiary reliability and legal proceedings.  
**CLEP-v1 Change**: Weight unchanged at 8%.

---

### 7. Digital Privacy Risk (Weight: 8%) — *NEW IN CLEP-v1*

**Scoring Factors**:

| Factor | Score Contribution | Trigger |
|--------|-------------------|---------|
| Fourth Amendment + digital privacy case | +0.4 | Carpenter/Riley/Jones cited |
| Location tracking (cell-site/GPS) | +0.3 | involves_location_tracking flag |
| Digital device/database search | +0.2 | digital_search or database_query flag |
| Electronic communications | +0.1 | electronic_communications flag |

**Maximum Component Score**: 1.0 (capped)

**Rationale**: Riley v. California (2014) and Carpenter v. US (2018) establish heightened protection for digital information. Modern surveillance technologies pose unique constitutional concerns.

**Key Cases**: Riley v. California, Carpenter v. US, United States v. Jones

---

### 8. Accountability Concern (Weight: 7%) — *NEW IN CLEP-v1*

**Scoring Factors**:

| Factor | Score Contribution | Trigger |
|--------|-------------------|---------|
| Constitutional torts doctrine | +0.3 | Doctrine identified |
| Use of force | +0.3 | involves_force flag |
| Deadly force | +0.2 (additional) | deadly_force flag |
| Qualified immunity issue | +0.2 | qualified_immunity_applicable flag |
| Official misconduct | +0.2 | official_misconduct flag |

**Maximum Component Score**: 1.0 (capped)

**Rationale**: Graham v. Connor (1989) establishes objective reasonableness standard for use of force. Tennessee v. Garner (1985) limits deadly force. Qualified immunity doctrine requires clear analysis of established law.

**Key Cases**: Graham v. Connor, Tennessee v. Garner, Sanders v. English

---

## Overall Score Calculation

### CLEP-v1 Formula (Updated)

```
Overall Score = Σ (Component Score × Weight)

             = (Due Process × 0.20) +
               (Delegation × 0.15) +
               (Fourth Amendment × 0.20) +
               (Administrative × 0.12) +
               (Metadata × 0.10) +
               (Custody × 0.08) +
               (Digital Privacy × 0.08) +        ← NEW
               (Accountability × 0.07)           ← NEW

Total Weight = 1.00 (100%)
```

**Range**: 0.0 (no risk) to 1.0 (maximum risk)

### Baseline Formula (Deprecated)

```
Overall Score = (Due Process × 0.25) +
                (Delegation × 0.20) +
                (Fourth Amendment × 0.20) +
                (Administrative × 0.15) +
                (Metadata × 0.12) +
                (Custody × 0.08)
```

*Note: Baseline formula retired as of CLEP-v1. Use updated 8-dimension formula.*

---

## Severity Classification

| Score Range | Severity | Legal Significance | Response Required |
|-------------|----------|-------------------|------------------|
| ≥ 0.80 | **Critical** | Probable constitutional violation | Immediate legal review |
| 0.60-0.79 | **High** | Significant legal risk | Priority review within 48 hours |
| 0.40-0.59 | **Medium** | Moderate concern | Review within 1 week |
| 0.20-0.39 | **Low** | Technical irregularity | Monitor, document |
| < 0.20 | **Minimal** | De minimis issue | Routine follow-up |

---

## Risk Factor Identification

**Threshold**: Component score > 0.3 triggers risk factor flag.

**Example Risk Factors**:
- "Due process violation: Inadequate notice or hearing procedures"
- "Non-delegation concern: Insufficient statutory standards"
- "Fourth Amendment issue: Privacy expectation implicated"
- "Administrative law: Action may be arbitrary and capricious"
- "Evidence integrity: Metadata anomalies detected"
- "Chain of custody: Gaps or missing documentation"

---

## Recommendation Generation

### Critical/High Severity

**Mandatory Recommendations**:
1. Immediate legal review required
2. Document all findings with citations

### Doctrine-Specific Recommendations

| Component Score | Threshold | Recommendation |
|----------------|-----------|----------------|
| Due Process | > 0.5 | Review under Mathews v. Eldridge |
| Delegation | > 0.5 | Verify statutory authorization and intelligible principle |
| Fourth Amendment | > 0.5 | Analyze under Katz/Carpenter privacy framework |
| Administrative | > 0.5 | Assess reasoned decision-making under State Farm |
| Metadata | > 0.5 | Conduct forensic authentication |
| Custody | > 0.5 | Reconstruct custody chain |

---

## Aggregate Risk Reporting

**Multi-Anomaly Analysis**:

```python
{
  "total_anomalies": N,
  "risk_distribution": {
    "critical": count,
    "high": count,
    "medium": count,
    "low": count,
    "minimal": count
  },
  "average_score": μ,
  "high_priority_count": critical + high,
  "requires_immediate_review": bool,
  "critical_findings": [...]
}
```

---

## Validation & Calibration

**Test Suite**: 141 tests validate scoring accuracy

**Calibration Principles**:
1. **Conservative**: Err toward higher scores for rights violations
2. **Proportional**: Weight reflects constitutional significance
3. **Additive**: Multiple factors compound risk
4. **Capped**: Component scores max at 1.0
5. **Evidence-based**: Derived from legal standards

---

## Limitations

1. **Automated analysis**: Human legal judgment required
2. **Threshold-based**: Bright-line rules may miss context
3. **Federal focus**: State constitutional law not included
4. **Snapshot**: Based on law as of December 2024

---

## Future Enhancements

Potential improvements:
- **Machine learning** refinement from case outcomes
- **Dynamic weighting** based on jurisdiction
- **Context-aware** scoring using NLP
- **Temporal tracking** of risk score evolution

---

*This model is for automated screening. All high-risk findings require review by qualified legal counsel.*
