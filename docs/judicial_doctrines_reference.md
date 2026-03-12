# Judicial Doctrines Reference

This document provides detailed reference material for constitutional doctrines implemented in the Judicial Interpretive Matrix (JIM).

---

## Due Process

**Constitutional Basis**: Fifth Amendment (federal), Fourteenth Amendment (states)

### Procedural Due Process

**Core Principle**: Government must provide fair process before depriving person of life, liberty, or property.

**Mathews v. Eldridge Balancing Test** (424 U.S. 319, 1976):

Three factors:
1. **Private interest** affected by government action
2. **Risk of erroneous deprivation** and probable value of additional safeguards
3. **Government interest**, including fiscal/administrative burdens

**Application in JIM**:
- Triggers on benefit terminations, sanctions, enforcement actions
- Scored based on adequacy of notice and hearing
- Weight: 25% of overall risk score

**Key Cases**:
- Goldberg v. Kelly (1970): Pre-termination hearing for welfare
- Hamdi v. Rumsfeld (2004): Detention hearing rights

---

## Fourth Amendment Privacy

**Constitutional Basis**: Fourth Amendment

### Reasonable Expectation of Privacy

**Katz Test** (389 U.S. 347, 1967):
1. Subjective expectation of privacy
2. Objectively reasonable expectation society recognizes

**Modern Applications**:
- **Digital Privacy**: Cell-site location (Carpenter v. US, 2018)
- **Technology-Enhanced Surveillance**: Thermal imaging (Kyllo v. US, 2001)
- **GPS Tracking**: Physical intrusion (US v. Jones, 2012)

**Application in JIM**:
- Triggers on surveillance programs, data collection, warrantless activities
- Examines privacy expectation, warrant presence, special needs
- Weight: 20% of overall risk score

---

## Non-Delegation Doctrine

**Constitutional Basis**: Article I, Section 1 (vesting clause)

### Intelligible Principle Standard

**Core Principle**: Congress may delegate rulemaking if it provides "intelligible principle" to guide agency.

**Historical Context**:
- **1935 Violations**: Schechter Poultry, Panama Refining (NIRA struck down)
- **Modern Application**: Gundy v. US (2019) - principle upheld
- **Major Questions Corollary**: West Virginia v. EPA (2022)

**JIM Application**:
- Analyzes statutory standards and policy guidance
- Checks for unfettered discretion
- Applies major questions doctrine for transformative actions
- Weight: 20% of overall risk score

---

## Separation of Powers

**Constitutional Basis**: Articles I, II, III

### Youngstown Framework

**Justice Jackson's Concurrence** (Youngstown Sheet & Tube, 1952):

**Three Categories**:
1. **Maximum power**: President acts with express/implied congressional authorization
2. **Twilight zone**: Congress silent; President and Congress may have concurrent authority
3. **Minimum power**: President acts contrary to congressional will

**Application in JIM**:
- Examines cross-agency conflicts
- Identifies jurisdictional overlaps
- Assesses executive actions without clear statutory basis
- Weight: Integrated into delegation and administrative scores

---

## Administrative Law

**Constitutional Basis**: Article II, Administrative Procedure Act (5 U.S.C. § 551 et seq.)

### Arbitrary and Capricious Standard

**State Farm Factors** (Motor Vehicle Mfrs. v. State Farm, 1983):

Agency action arbitrary/capricious if:
- Failed to consider important aspect of problem
- Offered explanation counter to evidence
- Implausible explanation
- Departure from past practice without justification

### Post-Loper Bright Framework (2024)

**Loper Bright Enterprises v. Raimondo** (144 S. Ct. 2244, 2024):

**KEY CHANGE**: Chevron doctrine **overruled**.

**New Standard**:
- Courts exercise **independent judgment** on statutory questions
- **No deference** to agency statutory interpretations
- APA requires courts decide "all relevant questions of law"

**JIM Integration**:
- Updated doctrine map reflects Loper Bright
- Enhanced scrutiny for agency statutory interpretations
- Chevron marked historical, weight = 0.0
- Weight: 15% of overall risk score

### Major Questions Doctrine

**West Virginia v. EPA** (142 S. Ct. 2587, 2022):

**Principle**: Extraordinary grants of regulatory authority require clear congressional statement.

**Triggers**:
- Vast economic/political significance
- Novel assertion of authority
- Transformative regulatory action
- Agency claiming power beyond historical practice

**JIM Application**:
- Special scrutiny multiplier (1.3x)
- Links to non-delegation analysis
- Weight: Elevated priority in correlation

---

## Equal Protection

**Constitutional Basis**: Fourteenth Amendment

### Standards of Review

**Strict Scrutiny** (Fundamental rights, suspect classifications):
- Compelling government interest
- Narrowly tailored means

**Intermediate Scrutiny** (Gender, legitimacy):
- Important government interest
- Substantially related means

**Rational Basis** (All other classifications):
- Legitimate government interest
- Rationally related means

### Class-of-One

**Village of Willowbrook v. Olech** (528 U.S. 562, 2000):
- Protects against intentional, arbitrary discrimination
- No class membership required
- Irrational treatment violates equal protection

**JIM Application**:
- Procurement favoritism analysis
- Arbitrary enforcement detection
- Vendor concentration concerns

---

## Unconstitutional Conditions

**Principle**: Government cannot condition benefits on surrender of constitutional rights.

**Perry v. Sindermann** (408 U.S. 593, 1972):
- Employment conditions cannot infringe First Amendment
- Academic freedom protection

**Application in JIM**:
- Contract conditions analysis
- Regulatory compliance conditions
- Benefit eligibility requirements

---

## Interpretive Canon Integration

### How Doctrines Map to Canons

| Doctrine | Primary Canons | Weight |
|----------|---------------|--------|
| Due Process | Clear Statement Rule, Constitutional Avoidance | 0.90-0.92 |
| Fourth Amendment | Constitutional Avoidance | 0.88 |
| Non-Delegation | Major Questions Doctrine, Non-Delegation Canon | 0.90-0.95 |
| Administrative Law | Post-Chevron Independent Review | N/A |
| Equal Protection | Equal Protection Scrutiny | 0.88 |

---

## Evidentiary Standards

### Federal Rules of Evidence

**Rule 901**: Authentication requirement
- Chain of custody
- Document origin verification
- Digital evidence standards

**Best Evidence Rule** (Rules 1001-1008):
- Original document preferred
- Duplicate admissible if authentic
- Exception: Public records

**JIM Application**:
- PDF forensics integration
- Timestamp conflict analysis
- Metadata integrity scoring
- Weight: 12% (metadata) + 8% (custody) = 20% combined

---

## Risk Scoring Formula

```
Overall Score = (Due Process × 0.25) +
                (Delegation × 0.20) +
                (Fourth Amendment × 0.20) +
                (Administrative × 0.15) +
                (Metadata × 0.12) +
                (Custody × 0.08)
```

**Severity Mapping**:
- ≥0.80: Critical
- ≥0.60: High
- ≥0.40: Medium
- ≥0.20: Low
- <0.20: Minimal

---

## Case Law Update Protocol

**When new Supreme Court decisions issue**:

1. Assess doctrinal impact
2. Update SCOTUS_INDEX.json with:
   - Case citation
   - Holding
   - Doctrinal classification
   - Issue tags
   - Doctrinal weight
3. Update correlation engine mappings if needed
4. Regenerate test fixtures
5. Run full test suite

**Example: Loper Bright (2024)**:
- Added as case_id "loper_bright_2024"
- Marked Chevron as overruled (weight = 0.0)
- Updated administrative law doctrine
- Added to correlation engine
- All 141 tests passing

---

## References

- **Primary Sources**: SCOTUS opinions (justia.com, supremecourt.gov)
- **Secondary Sources**: Constitutional law treatises (Chemerinsky, Tribe)
- **Implementation**: jim_doctrine_map.json, SCOTUS_INDEX.json
- **Testing**: tests/jim/ (141 tests)

---

*This reference is current as of December 2024. Constitutional law evolves; consult current case law and qualified counsel.*

---

## CLEP-v1 New Doctrines

### Constitutional Torts & Qualified Immunity

**Constitutional Basis**: 42 U.S.C. § 1983, Bivens Actions, Fourth Amendment

**Core Principles**:
- Government officials liable for constitutional violations under color of law
- Qualified immunity protects unless clearly established law violated
- Objective reasonableness standard for official conduct
- Remedy for deprivation of federal rights

**Key Cases**:
- **Sanders v. English** (1992) – Qualified immunity standards
- **Graham v. Connor** (1989) – Excessive force objective reasonableness
- **Tennessee v. Garner** (1985) – Deadly force constitutional limits

**Application in JIM**:
- Triggers on use of force, official misconduct, unlawful detention
- Examines clearly established law at time of conduct
- Assesses objective reasonableness from officer perspective
- Weight: 7% in accountability concern dimension

---

### Property Rights & Economic Liberty

**Constitutional Basis**: Fifth Amendment Takings, Fourteenth Amendment Due Process, Contract Clause

**Core Principles**:
- Property includes tangible and intangible interests
- Government takings require just compensation
- Substantive due process protects against arbitrary deprivation
- Liberty interests include contractual freedom

**Key Cases**:
- **Flournoy v. First Nat. Bank** (1941) – Property rights, commercial relationships

**Application in JIM**:
- Triggers on vendor contract interference, regulatory restrictions
- Analyzes arbitrary interference with property or contracts
- Assesses takings without compensation
- Integrated into due process and administrative scoring

---

### Right to Travel & Freedom of Movement

**Constitutional Basis**: Fourteenth Amendment Privileges and Immunities, Equal Protection, Due Process

**Core Principles**:
- Right to interstate travel is fundamental
- Durational residency requirements require compelling interest
- New residents entitled to equal treatment
- Identity control measures must not burden fundamental rights

**Key Cases**:
- **Shapiro v. Thompson** (1969) – Durational residency unconstitutional
- **Saenz v. Roe** (1999) – Equal treatment of newcomers
- **Brown v. Texas** (1979) – Stop-and-identify reasonable suspicion

**Application in JIM**:
- Triggers on residency requirements, travel restrictions, identity tracking
- Examines burden on interstate migration
- Applies strict scrutiny to fundamental rights restrictions
- Weight: 0.84 doctrinal weight

---

## Updated Fourth Amendment Framework (CLEP-v1)

### Digital Privacy Protection

**New Principles** (from CLEP-v1):
- Cell phone searches require warrant (Riley v. California, 2014)
- Cell-site location data requires warrant (Carpenter v. US, 2018)
- GPS tracking is Fourth Amendment search (United States v. Jones, 2012)
- Digital information receives heightened protection

**Stop & Frisk Standards**:
- **Terry v. Ohio** (1968): Brief investigatory stop with reasonable suspicion
- **Brown v. Texas** (1979): Cannot demand identification without reasonable suspicion
- Reasonable suspicion requires specific articulable facts

**Probable Cause Standards**:
- **Illinois v. Gates** (1983): Totality of circumstances test
- **Johnson v. United States** (1948): Neutral magistrate must evaluate

**Evidence Integrity**:
- **Silverthorne Lumber** (1920): Fruit of poisonous tree doctrine
- **Nardone v. US** (1939): Derivative evidence inadmissible
- **Wong Sun v. US** (1963): Attenuation may break causal chain

---

## Risk Scoring Integration (CLEP-v1)

### Digital Privacy Risk Dimension (8% weight)

Applies when:
- Cell-site location or GPS tracking involved
- Digital device or database searches conducted
- Electronic communications intercepted
- Warrantless digital surveillance programs

**Key Cases**: Riley, Carpenter, Jones

---

### Accountability Concern Dimension (7% weight)

Applies when:
- Use of force incidents (excessive or deadly)
- Qualified immunity defenses raised
- Official misconduct alleged
- Police accountability issues present

**Key Cases**: Graham v. Connor, Tennessee v. Garner, Sanders v. English

---

*Updated: December 6, 2025 | CLEP-v1 Release*  
*44 cases across 10 doctrines | 208 comprehensive tests*
