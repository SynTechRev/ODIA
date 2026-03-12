# Compliance Checklist: Four Fault Lines

This checklist implements the four fault-line framework for auditing documents in the Oraculus DI Auditor system. Use this checklist to systematically review documents for compliance and identify potential issues.

---

## Overview

The four fault lines represent critical areas of legal, ethical, and policy compliance:

1. **DOJ Certification** - Department of Justice certification and law enforcement compliance
2. **IRB Consent (28 C.F.R. Part 46)** - Institutional Review Board and human subjects protections
3. **Infrastructure Policy** - Facility, procurement, and contractor compliance
4. **Federal Grant Incentives** - Grant funding mechanisms and conflict of interest

---

## 1. DOJ Certification

### Checklist Items

- [ ] **DOJ Certification Present**: Document includes explicit DOJ certification or reference
- [ ] **Law Enforcement Authority**: Proper law enforcement authority and jurisdiction established
- [ ] **Criminal Investigation Standards**: Compliance with criminal investigation procedures
- [ ] **Evidence Chain of Custody**: Proper evidence handling and chain-of-custody procedures documented
- [ ] **Legal Process Compliance**: Warrants, subpoenas, or court orders properly obtained
- [ ] **Information Sharing Protocols**: Appropriate information sharing agreements in place
- [ ] **Privacy Act Compliance**: Compliance with Privacy Act requirements for law enforcement records
- [ ] **FOIA Exemptions**: Proper application of Freedom of Information Act exemptions

### Red Flags

- Missing DOJ certification where required
- Unauthorized law enforcement activities
- Improper evidence handling
- Information sharing without legal basis
- Privacy Act violations

### Immediate Actions

1. Verify DOJ certification requirements for all law enforcement documents
2. Flag documents with missing certifications for legal review
3. Ensure proper chain-of-custody documentation for all evidence
4. Review information sharing agreements for legal compliance

---

## 2. IRB Consent (28 C.F.R. Part 46)

### Checklist Items

- [ ] **IRB Approval Present**: Research has valid Institutional Review Board approval
- [ ] **Informed Consent Documented**: Proper informed consent obtained from subjects
- [ ] **Consent Form Adequate**: Consent forms meet regulatory requirements
- [ ] **Subject Protections**: Adequate protections for human research subjects
- [ ] **Vulnerable Population Protections**: Special protections for children, prisoners, pregnant women
- [ ] **Risk Assessment**: Proper assessment and minimization of risks to subjects
- [ ] **Confidentiality Measures**: Adequate measures to protect subject confidentiality
- [ ] **Continuing Review**: Evidence of ongoing IRB continuing review
- [ ] **Adverse Event Reporting**: Procedures for reporting adverse events to IRB
- [ ] **HIPAA Compliance**: Health Insurance Portability and Accountability Act compliance where applicable

### Red Flags

- Research conducted without IRB approval
- Missing or inadequate informed consent
- Lack of protections for vulnerable populations
- Confidentiality breaches
- Failure to report adverse events

### Immediate Actions

1. Verify IRB approval status for all research documents
2. Review informed consent procedures and documentation
3. Identify documents involving vulnerable populations requiring special protections
4. Flag any research activities without proper IRB oversight
5. Consult with IRB and legal counsel on compliance issues

---

## 3. Infrastructure Policy

### Checklist Items

- [ ] **Facility Compliance**: Facilities meet applicable safety and regulatory standards
- [ ] **Procurement Compliance**: Procurement follows federal acquisition regulations (FAR)
- [ ] **Contractor Oversight**: Proper contractor selection and oversight procedures
- [ ] **Conflict of Interest Checks**: Conflicts of interest identified and managed
- [ ] **Security Requirements**: Facility and information security requirements met
- [ ] **Environmental Compliance**: Environmental regulations and permits in place
- [ ] **Accessibility Standards**: ADA and accessibility requirements met
- [ ] **Quality Assurance**: Quality control and assurance programs operational
- [ ] **Record Keeping**: Proper infrastructure documentation and record keeping
- [ ] **Audit Trail**: Complete audit trail for infrastructure decisions

### Red Flags

- Facility non-compliance or safety violations
- Procurement irregularities or FAR violations
- Inadequate contractor oversight
- Unmanaged conflicts of interest
- Security deficiencies
- Environmental violations

### Immediate Actions

1. Review all facility compliance documentation
2. Audit procurement processes for FAR compliance
3. Verify contractor oversight and performance monitoring
4. Identify and document conflicts of interest
5. Ensure security requirements are met
6. Flag infrastructure policy violations for immediate remediation

---

## 4. Federal Grant Incentives

### Checklist Items

- [ ] **Grant Authorization**: Proper authorization for federal grant funding
- [ ] **Grant Compliance**: Compliance with all grant terms and conditions
- [ ] **Budget Alignment**: Expenditures align with approved grant budget
- [ ] **Matching Funds**: Required matching funds or cost-sharing documented
- [ ] **Performance Metrics**: Grant performance metrics and milestones tracked
- [ ] **Financial Reporting**: Timely and accurate financial reporting to grantor
- [ ] **Audit Requirements**: Grant audit requirements satisfied
- [ ] **Conflict of Interest Policy**: Grant-specific conflict of interest policies in place
- [ ] **Indirect Cost Compliance**: Indirect costs properly calculated and approved
- [ ] **Close-out Procedures**: Grant close-out procedures followed

### Red Flags

- Unauthorized use of grant funds
- Failure to meet grant conditions
- Budget violations or cost overruns
- Missing matching funds
- Incomplete financial reporting
- Conflicts of interest involving grant funding
- Improper indirect cost rates

### Immediate Actions

1. Verify grant authorization and terms for all federally funded activities
2. Review financial reports for accuracy and compliance
3. Ensure matching funds and cost-sharing requirements are met
4. Identify conflicts of interest related to grant funding
5. Flag grant compliance issues for financial review
6. Coordinate with grants management office on remediation

---

## Cross-Cutting Concerns

### Data Protection and Privacy

- [ ] **PII Handling**: Personally identifiable information properly protected
- [ ] **Data Security**: Appropriate data security measures in place
- [ ] **Access Controls**: Proper access controls and authorization
- [ ] **Encryption**: Sensitive data encrypted in transit and at rest
- [ ] **Data Retention**: Data retention policies followed
- [ ] **Breach Response**: Data breach response plan in place

### Legal Review

- [ ] **Legal Counsel Review**: Documents reviewed by qualified legal counsel where required
- [ ] **Litigation Holds**: Documents subject to litigation hold properly preserved
- [ ] **Privilege Review**: Attorney-client privilege properly asserted
- [ ] **Regulatory Compliance**: Compliance with all applicable regulations verified

---

## Document-Specific Checklist

For each document under audit, complete this checklist:

### Document Information

- **Document ID**: _______________
- **Document Title**: _______________
- **Date Reviewed**: _______________
- **Reviewer**: _______________

### Fault Line Assessment

| Fault Line | Applicable | Compliant | Issues Identified | Severity |
|------------|-----------|-----------|-------------------|----------|
| DOJ Certification | ☐ Yes ☐ No | ☐ Yes ☐ No | | ☐ Low ☐ Med ☐ High ☐ Critical |
| IRB Consent | ☐ Yes ☐ No | ☐ Yes ☐ No | | ☐ Low ☐ Med ☐ High ☐ Critical |
| Infrastructure | ☐ Yes ☐ No | ☐ Yes ☐ No | | ☐ Low ☐ Med ☐ High ☐ Critical |
| Grant Incentives | ☐ Yes ☐ No | ☐ Yes ☐ No | | ☐ Low ☐ Med ☐ High ☐ Critical |

### Findings Summary

**Total Issues**: _______________  
**Critical Issues**: _______________  
**High Severity Issues**: _______________  
**Requires Legal Review**: ☐ Yes ☐ No  
**Requires Immediate Action**: ☐ Yes ☐ No

### Recommended Actions

1. _______________
2. _______________
3. _______________

### Notes

_______________
_______________
_______________

---

## Automation Support

The Oraculus DI Auditor provides automated support for this checklist:

- **Manifest Flags**: Use `scripts/triage.py` to add flags with categories matching fault lines
- **Report Generation**: Use `scripts/render_report.py` to generate compliance reports
- **Query Evaluation**: Use `scripts/eval_harness.py` with IRB and compliance queries

### Example: Adding a Compliance Flag

```bash
python scripts/triage.py --doc-id DOC123 \
  --flag "Missing IRB approval documentation" \
  --severity critical \
  --category irb_consent \
  --author "Compliance Officer"
```

---

## References

- 28 C.F.R. Part 46 - Protection of Human Subjects
- Department of Justice Certification Requirements
- Federal Acquisition Regulation (FAR)
- OMB Uniform Guidance (2 C.F.R. Part 200)
- Privacy Act of 1974
- HIPAA Privacy Rule
- Freedom of Information Act (FOIA)

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintained by**: Oraculus DI Auditor Project
