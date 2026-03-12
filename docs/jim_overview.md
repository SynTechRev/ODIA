# Judicial Interpretive Matrix (JIM) - Overview

**Version:** 1.0.0  
**Status:** Production  
**Created:** 2025-12-06

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Legal Framework](#legal-framework)
5. [Usage Guide](#usage-guide)
6. [Integration with Oraculus-DI-Auditor](#integration-with-oraculus-di-auditor)
7. [Output Artifacts](#output-artifacts)
8. [Testing](#testing)

---

## Introduction

The **Judicial Interpretive Matrix (JIM)** is a comprehensive legal analysis engine that maps constitutional doctrines, Supreme Court precedents, and administrative law principles to anomalies detected by the Oraculus-DI-Auditor system.

### Purpose

JIM provides automated legal risk assessment by:

1. **Correlating** audit anomalies to relevant constitutional doctrines
2. **Linking** findings to controlling Supreme Court precedents
3. **Scoring** legal risks across six dimensions
4. **Identifying** systemic constitutional concerns
5. **Generating** actionable legal reports with citations

### Key Features

- **44 landmark Supreme Court cases** (1789-2025) — *Updated in CLEP-v1*
- **10 constitutional doctrines** (Due Process, Fourth Amendment, Constitutional Torts, etc.) — *+3 in CLEP-v1*
- **9 interpretive frameworks** (Major Questions, Digital Privacy, Police Accountability, etc.)
- **8-dimensional risk scoring** framework — *+2 dimensions in CLEP-v1*
- **Automated report generation** (JSON, Markdown, Graph)
- **208 comprehensive tests** ensuring accuracy — *+67 in CLEP-v1*

---

## Case Law Expansion Pack v1 (CLEP-v1)

**Release Date:** December 6, 2025  
**Status:** Production

CLEP-v1 represents the first major expansion of JIM, adding **20 new cases** (+83%) with enhanced coverage of:

- **Digital Privacy** (Riley, Terry, cell-site location, GPS tracking)
- **Evidence Integrity** (Silverthorne, Nardone, Wong Sun - fruit of poisonous tree)
- **Police Accountability** (Graham v. Connor, Tennessee v. Garner - use of force)
- **Freedom of Movement** (Shapiro, Saenz - right to travel)
- **Modern Executive Authority** (Trump v. US 2024 - presidential immunity)

### New Doctrines
- **Constitutional Torts** - § 1983 liability, qualified immunity
- **Property Rights** - Economic liberty, contractual freedom
- **Free Movement** - Interstate travel, identity control

### New Risk Dimensions
- **Digital Privacy Risk** (8% weight) - Cell-site, GPS, electronic surveillance
- **Accountability Concern** (7% weight) - Use of force, qualified immunity

See `legal/cases/CLEP_SUMMARY.md` for complete details.

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORACULUS-DI-AUDITOR                          │
├─────────────────────────────────────────────────────────────────┤
│  ACE      │  VICFM   │  CAIM    │  PDF Forensics │  Legislative │
│ Anomalies │ Patterns │ Analysis │   Irregularities│   Timeline   │
└────────────┬────────────────────┬──────────────────┬─────────────┘
             │                    │                  │
             └────────────────────▼──────────────────┘
                               JIM Core
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
   ┌─────▼─────┐          ┌──────▼──────┐         ┌──────▼──────┐
   │   Case    │          │ Correlation │         │    Risk     │
   │  Loader   │          │   Engine    │         │   Scorer    │
   └───────────┘          └─────────────┘         └─────────────┘
         │                        │                        │
         │                        │                        │
   ┌─────▼─────────────────────────▼────────────────────────▼─────┐
   │              JIM OUTPUT ARTIFACTS                             │
   ├───────────────────────────────────────────────────────────────┤
   │  - JIM_REPORT.json                                            │
   │  - JIM_SUMMARY.md                                             │
   │  - CASE_LINKAGE_GRAPH.json                                    │
   │  - STATUTORY_ALIGNMENT_REPORT.md                              │
   └───────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Anomalies from ACE, VICFM, CAIM, PDF forensics, legislative timeline
2. **Processing**:
   - Case Loader: Loads Supreme Court case law database
   - Correlation Engine: Maps anomalies → doctrines → precedents
   - Risk Scorer: Calculates constitutional risk scores
3. **Output**: Comprehensive legal reports with citations and recommendations

---

## Core Components

### 1. JIM Core (`jim_core.py`)

**Purpose**: Main orchestration engine

**Responsibilities**:
- Initialize case law database
- Coordinate analysis pipeline
- Generate output reports
- Manage analysis state

**Key Methods**:
```python
jim = JIMCore()
jim.initialize()  # Load case law
result = jim.analyze_anomalies(anomalies)  # Analyze
jim.generate_reports(result)  # Output reports
```

### 2. Case Loader (`jim_case_loader.py`)

**Purpose**: Supreme Court case law management

**Features**:
- Loads SCOTUS_INDEX.json (24 cases)
- Indexes by doctrine, year, tags
- Validates case data integrity
- Provides efficient lookup

**Key Methods**:
```python
loader = JIMCaseLoader()
loader.load_scotus_index()
cases = loader.get_cases_by_doctrine("due_process")
case = loader.get_case_by_id("mathews_v_eldridge_1976")
```

### 3. Correlation Engine (`jim_correlation_engine.py`)

**Purpose**: Anomaly-to-precedent correlation

**Capabilities**:
- Maps 18+ anomaly types to doctrines
- Finds relevant Supreme Court cases
- Calculates case relevance scores
- Identifies interpretive canons
- Detects systemic patterns

**Risk Indicators Assessed**:
- Constitutional rights impact
- Separation of powers concerns
- Delegation issues
- Administrative procedure violations
- Evidentiary concerns

### 4. Risk Scorer (`jim_risk_scoring.py`)

**Purpose**: Constitutional risk assessment

**Six-Dimensional Scoring Framework**:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Due Process Conflict | 25% | Notice, hearing, procedural safeguards |
| Delegation Issues | 20% | Intelligible principle, statutory standards |
| Fourth Amendment Concerns | 20% | Privacy, surveillance, warrants |
| Administrative Overreach | 15% | Arbitrary/capricious, reasoned decision-making |
| Metadata Integrity | 12% | Forensic score, timestamp conflicts |
| Chain of Custody | 8% | Documentation gaps, handling verification |

**Severity Levels**:
- **Critical** (≥0.80): Immediate legal review required
- **High** (≥0.60): Significant constitutional risk
- **Medium** (≥0.40): Moderate concern
- **Low** (≥0.20): Minor issue
- **Minimal** (<0.20): Technical irregularity

---

## Legal Framework

### Constitutional Doctrines

1. **Due Process** (Fifth/Fourteenth Amendments)
   - Procedural: Notice, hearing, Mathews v. Eldridge balancing
   - Substantive: Fundamental rights protection

2. **Fourth Amendment** (Privacy & Searches)
   - Reasonable expectation of privacy (Katz)
   - Warrant requirement
   - Digital privacy (Carpenter, Jones)

3. **Non-Delegation Doctrine** (Article I)
   - Intelligible principle required
   - Statutory standards necessary
   - Major Questions Doctrine

4. **Separation of Powers** (Articles I, II, III)
   - Branch encroachment prohibited
   - Youngstown framework

5. **Administrative Law** (APA, Article II)
   - Reasoned decision-making
   - Arbitrary and capricious review
   - Notice and comment rulemaking
   - **Post-Loper Bright (2024)**: No Chevron deference; independent judicial review

6. **Equal Protection** (Fourteenth Amendment)
   - Rational basis review
   - Class-of-one protection
   - Arbitrary discrimination prohibited

7. **Unconstitutional Conditions**
   - Benefit conditioning on rights waiver prohibited

### Interpretive Canons

- **Major Questions Doctrine** (0.95 weight): Clear authorization for transformative actions
- **Clear Statement Rule** (0.90): Explicit intent for fundamental rights/federalism
- **Constitutional Avoidance** (0.88): Avoid constitutional questions
- **Rule of Lenity** (0.85): Construe penal statutes favorably
- **Non-Delegation Canon** (0.90): Find intelligible principle

### Landmark Cases Included

**Due Process**:
- Mathews v. Eldridge (1976) - Three-factor balancing test
- Goldberg v. Kelly (1970) - Property interest in benefits
- Hamdi v. Rumsfeld (2004) - Detention hearing rights

**Administrative Law**:
- Loper Bright Enterprises v. Raimondo (2024) - Chevron overruled ⭐
- West Virginia v. EPA (2022) - Major Questions Doctrine
- Motor Vehicle Mfrs. v. State Farm (1983) - Arbitrary/capricious

**Fourth Amendment**:
- Carpenter v. US (2018) - Digital privacy
- Katz v. US (1967) - Reasonable expectation
- Kyllo v. US (2001) - Technology-enhanced surveillance

**[See full case list in SCOTUS_INDEX.json]**

---

## Usage Guide

### Basic Usage

```python
from scripts.jim.jim_core import JIMCore

# Initialize JIM
jim = JIMCore()
init_result = jim.initialize()

if not init_result["success"]:
    print("Error:", init_result["error"])
    exit(1)

# Prepare anomalies from audit systems
anomalies = [
    {
        "id": "ace_001",
        "type": "metadata_break",
        "source": "ace",
        "affects_rights": True,
        "description": "Missing notice requirement in benefit termination"
    },
    {
        "id": "vicfm_042",
        "type": "sole_source_procurement",
        "source": "vicfm",
        "category": "procurement",
        "description": "Non-competitive contract award"
    }
]

# Run full analysis
result = jim.run_full_analysis(anomalies)

# Reports generated at analysis/jim/:
# - JIM_REPORT.json
# - JIM_SUMMARY.md
# - CASE_LINKAGE_GRAPH.json
```

### Step-by-Step Analysis

```python
# Initialize
jim = JIMCore()
jim.initialize()

# Analyze anomalies
analysis = jim.analyze_anomalies(anomalies)

# Inspect results
print(f"Total analyzed: {analysis['total_anomalies_analyzed']}")
print(f"High priority: {analysis['risk_summary']['high_priority_count']}")
print(f"Dominant doctrines: {analysis['correlation_summary']['dominant_doctrines']}")

# Generate reports
reports = jim.generate_reports(analysis)
print(f"Reports at: {reports['output_directory']}")
```

### Anomaly Format

```python
anomaly = {
    # Required fields
    "id": "unique_identifier",
    "type": "metadata_break",  # See anomaly_doctrine_map
    "source": "ace",  # ace, vicfm, caim, pdf_forensics
    
    # Optional flags (affect scoring)
    "affects_rights": True,
    "lacks_standards": True,
    "involves_surveillance": False,
    "lacks_reasoning": False,
    "forensic_score": 65,  # 0-100, lower = worse
    
    # Metadata
    "description": "Human-readable description",
    "category": "metadata_break",
    "timeline_irregularity": False,
}
```

---

## Integration with Oraculus-DI-Auditor

### ACE Integration

ACE (Anomaly Correlation Engine) detects:
- Metadata breaks → Due Process + Administrative Law
- Chronological drift → Administrative Law
- Cross-year irregularities → Administrative Law

### VICFM Integration

VICFM (Vendor Influence Contract Flow Map) detects:
- Sole source procurement → Due Process + Equal Protection
- Cost escalation → Administrative Law
- Vendor concentration → Administrative Law + Equal Protection

### CAIM Integration

CAIM (Cross-Agency Influence Map) detects:
- Agency coordination gaps → Separation of Powers + Administrative Law
- Cross-agency conflicts → Separation of Powers
- Delegation without authority → Non-Delegation + Separation of Powers

### PDF Forensics Integration

PDF forensics detects:
- Timestamp conflicts → Administrative Law (evidentiary)
- Producer mismatches → Administrative Law (authenticity)
- XMP integrity failures → Administrative Law (chain of custody)

---

## Output Artifacts

### 1. JIM_REPORT.json

Comprehensive JSON report with:
- Executive summary
- Risk distribution statistics
- Doctrinal analysis
- Case law citations
- Individual findings with scores
- Critical findings requiring review

### 2. JIM_SUMMARY.md

Executive markdown summary with:
- Risk assessment overview
- Distribution table
- Dominant doctrines
- Systemic patterns
- Top relevant cases with holdings
- Critical findings
- Recommendations

### 3. CASE_LINKAGE_GRAPH.json

Visualization-ready graph with:
- Nodes: Anomalies, doctrines, cases
- Edges: Implication links, precedent links
- Statistics: Node/edge counts by type

### 4. STATUTORY_ALIGNMENT_REPORT.md

Legislative alignment analysis with:
- Canon-to-anomaly mappings
- Statutory compliance assessment
- APA/Appropriations/Procurement alignment
- Federal Records Act compliance

---

## Testing

**Test Suite**: 141 comprehensive tests  
**Coverage**: All core components  
**Location**: `tests/jim/`

### Test Categories

1. **Case Loading** (32 tests)
   - Initialization
   - SCOTUS index loading
   - Case retrieval by doctrine/year/ID
   - Interpretive canon lookup
   - Validation

2. **Correlation Engine** (37 tests)
   - Doctrine identification
   - Case relevance calculation
   - Canon identification
   - Risk indicators
   - Constitutional basis mapping
   - Systemic patterns

3. **Risk Scoring** (42 tests)
   - Component scoring (due process, delegation, 4A, admin, metadata, custody)
   - Overall scoring
   - Severity determination
   - Risk factor compilation
   - Recommendations
   - Aggregate reporting

4. **JIM Core** (30 tests)
   - Initialization
   - Analysis pipeline
   - Report generation
   - Full integration

### Running Tests

```bash
# All JIM tests
pytest tests/jim/ -v

# Specific component
pytest tests/jim/test_case_loader.py -v
pytest tests/jim/test_correlation_engine.py -v
pytest tests/jim/test_risk_scoring.py -v
pytest tests/jim/test_jim_core.py -v

# With coverage
pytest tests/jim/ --cov=scripts.jim --cov-report=html
```

---

## Security & Privacy

- **No external API calls**: All processing local
- **No sensitive data storage**: Operates on audit metadata
- **Deterministic**: Same inputs → same outputs
- **Audit trail**: Complete provenance tracking
- **Human review required**: JIM provides analysis, not legal advice

---

## Limitations & Disclaimers

1. **Not Legal Advice**: JIM provides automated analysis; consult qualified counsel
2. **Case Law Scope**: 24 foundational cases; not exhaustive
3. **Temporal Scope**: Cases through 2024; future precedents not included
4. **Context Required**: Human interpretation essential for application
5. **Jurisdiction**: Federal constitutional and administrative law focus

---

## Future Enhancements

Potential extensions:
- State constitutional law integration
- International human rights frameworks
- Circuit court precedent tracking
- Real-time case law updates
- Natural language query interface
- Visual correlation graphs

---

## References

- Supreme Court case law: SCOTUS_INDEX.json
- Doctrinal framework: jim_doctrine_map.json
- Legislative canons: LEGISLATIVE_CANON_MAP.json
- API documentation: See module docstrings

---

**For questions or issues, consult:**
- docs/judicial_doctrines_reference.md
- docs/case_law_alignment.md
- docs/constitutional_risk_model.md
