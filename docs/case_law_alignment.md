# Case Law Alignment Matrix

This document maps audit anomaly types to relevant Supreme Court precedents.

---

## ACE (Anomaly Correlation Engine) → Case Law

### Metadata Breaks

**Relevant Cases**:
- **Mathews v. Eldridge** (1976): Procedural adequacy, notice requirements
- **Motor Vehicle Mfrs. v. State Farm** (1983): Administrative record completeness

**Alignment Issues**:
- Inadequate notice violates due process
- Deficient record fails arbitrary/capricious review

### Chronological Drift

**Relevant Cases**:
- **State Farm**: Departure from practice requires explanation
- **Kent v. Dulles** (1958): Clear statement for rights restrictions

**Alignment Issues**:
- Temporal ambiguity creates enforcement uncertainty
- Retroactive application without clear authorization

---

## VICFM (Vendor Contracts) → Case Law

### Sole Source Procurement

**Relevant Cases**:
- **Village of Willowbrook v. Olech** (2000): Class-of-one equal protection
- **Perry v. Sindermann** (1972): Arbitrary government action

**Alignment Issues**:
- Non-competitive awards raise equal protection concerns
- Vendor favoritism without rational basis

---

## CAIM (Cross-Agency) → Case Law

### Delegation Without Authority

**Relevant Cases**:
- **West Virginia v. EPA** (2022): Major questions doctrine
- **Schechter Poultry** (1935): Intelligible principle requirement
- **Gundy v. US** (2019): Modern non-delegation

**Alignment Issues**:
- Exceeds statutory grant
- Lacks intelligible principle
- Major policy shift without clear authorization

### Agency Coordination Gaps

**Relevant Cases**:
- **Youngstown Sheet & Tube** (1952): Separation of powers framework
- **Mistretta v. US** (1989): Permissible delegation with standards

---

## PDF Forensics → Case Law

### Timestamp Conflicts

**Relevant Cases**:
- **FRE Rule 901**: Authentication standards
- **FRE Rule 1002**: Best evidence rule

**Alignment Issues**:
- Documentary authenticity questioned
- Admissibility concerns
- Chain of custody integrity

---

## Surveillance → Case Law

### Data Collection Programs

**Relevant Cases**:
- **Carpenter v. US** (2018): CSLI requires warrant
- **Katz v. US** (1967): Reasonable expectation of privacy
- **Kyllo v. US** (2001): Technology-enhanced surveillance
- **US v. Jones** (2012): GPS tracking

**Alignment Issues**:
- Warrantless collection violates Fourth Amendment
- Privacy expectation in digital data
- Special needs exception narrowly construed

---

## Case Selection Criteria

JIM includes cases meeting these criteria:

1. **Foundational** doctrine establishment
2. **Controlling** precedent status
3. **Recent** relevance (especially 2000+)
4. **High doctrinal weight** (≥0.75)
5. **Frequent citation** in lower courts

---

## Correlation Algorithm

```python
Relevance Score = (Doctrinal Weight × 0.5) +
                  (Tag Match Bonus × 0.1 per tag) +
                  (Recency Boost × 0.2 if year ≥ 2000)
```

**Top 5 cases** returned per anomaly, minimum relevance 0.3.

---

*See SCOTUS_INDEX.json for complete case database.*

---

## CLEP-v1 Expansion (December 2025)

### Digital Privacy & Surveillance

**New Cases:**
- **Riley v. California** (2014): Warrantless cell phone search
- **Terry v. Ohio** (1968): Stop & frisk, reasonable suspicion
- **Illinois v. Gates** (1983): Probable cause totality of circumstances
- **Johnson v. United States** (1948): Neutral magistrate requirement
- **Rakas v. Illinois** (1978): Standing, expectation of privacy
- **Brown v. Texas** (1979): Stop-and-identify reasonable suspicion
- **Florida v. Jardines** (2013): Curtilage protection, dog sniff

**Alignment Issues:**
- Cell phone searches require warrant (Riley)
- Stop-and-frisk requires articulable reasonable suspicion (Terry)
- Identification demands must be supported by reasonable suspicion (Brown)

---

### Evidence Integrity & Chain of Custody

**New Cases:**
- **Silverthorne Lumber v. United States** (1920): Fruit of poisonous tree
- **Nardone v. United States** (1939): Derivative evidence exclusion
- **Wong Sun v. United States** (1963): Attenuation doctrine

**Alignment Issues:**
- Evidence from illegal search inadmissible (Silverthorne)
- Derivative evidence tainted unless independent source (Nardone)
- Attenuation may break causal chain (Wong Sun)
- PDF forensics anomalies → fruit of poisonous tree analysis

---

### Use of Force & Police Accountability

**New Cases:**
- **Graham v. Connor** (1989): Excessive force objective reasonableness
- **Tennessee v. Garner** (1985): Deadly force standards
- **Sanders v. English** (1992): Qualified immunity standards

**Alignment Issues:**
- Use of force evaluated from officer perspective (Graham)
- Deadly force requires imminent threat of serious harm (Garner)
- Qualified immunity unless clearly established law violated (Sanders)

---

### Due Process Enhancements

**New Cases:**
- **Coffin v. United States** (1895): Presumption of innocence
- **James v. Kentucky** (1984): Jury instructions, right to silence
- **Moya v. United States** (1985): Confrontation, evidentiary standards

**Alignment Issues:**
- Burden of proof on prosecution (Coffin)
- Proper procedural safeguards required (James)
- Confrontation rights must be protected (Moya)

---

### Freedom of Movement

**New Cases:**
- **Shapiro v. Thompson** (1969): Right to interstate travel
- **Saenz v. Roe** (1999): Equal treatment of newcomers

**Alignment Issues:**
- Durational residency requirements unconstitutional (Shapiro)
- New residents entitled to same benefits (Saenz)
- Identity tracking systems may burden travel rights

---

### Modern Executive Authority

**New Cases:**
- **Trump v. United States** (2024): Presidential immunity framework
- **Flournoy v. First Nat. Bank** (1941): Property rights, contractual freedom

**Alignment Issues:**
- Official acts receive presumptive immunity (Trump)
- Property and liberty interests protected (Flournoy)
- Vendor contract interference may violate property rights

---

## Updated Correlation Algorithm (CLEP-v1)

```python
Relevance Score = (Doctrinal Weight × 0.5) +
                  (Tag Match Bonus × 0.1 per tag) +
                  (Recency Boost × 0.2 if year ≥ 2000) +
                  (Digital Privacy Boost × 0.15 if Riley/Carpenter)
```

**Top 5 cases** returned per anomaly, minimum relevance 0.3.

**New Tag Priorities:**
- digital_privacy, cell_site_location, gps_tracking
- fruit_of_poisonous_tree, chain_of_custody
- stop_and_frisk, reasonable_suspicion
- excessive_force, qualified_immunity
- right_to_travel, interstate_migration

---

*Updated: December 6, 2025 | CLEP-v1 Release*  
*See SCOTUS_INDEX.json for complete 44-case database.*
