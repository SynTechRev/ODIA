# CCOPS Compliance Framework

## What Is CCOPS?

The **Community Control Over Police Surveillance (CCOPS)** model bill is published
by the ACLU. It provides a legislative template that cities and counties can adopt
to ensure elected officials and the public have meaningful oversight of surveillance
technology before it is purchased and while it is operated.

CCOPS defines 11 mandatory elements that any surveillance-technology ordinance must
contain. When a jurisdiction adopts a CCOPS-compliant ordinance, every new surveillance
technology acquisition must clear all 11 hurdles before a single dollar is spent.

Reference: <https://www.aclu.org/legal-document/community-control-over-police-surveillance-ccops-model-bill>

---

## CCOPS and ODIA

ODIA maps each CCOPS mandate to one or more of its existing anomaly detectors.
When you run `run_compliance_check.py` (or call `POST /compliance/assess`), ODIA:

1. Ingests your document set and runs all detectors.
2. Matches each detector's findings to the CCOPS mandate(s) it verifies.
3. Sets a per-mandate status (`compliant`, `non_compliant`, `partial`, or `unknown`).
4. Computes an overall compliance score and risk level.
5. Generates specific recommendations for every mandate that is not fully compliant.

No LLM is required. The compliance check is deterministic and runs entirely offline.

---

## The 11 CCOPS Mandates

| ID   | Title                        | Severity | Verifying Detectors                               |
|------|------------------------------|----------|---------------------------------------------------|
| M-01 | City Council Approval        | critical | `procurement_timeline`                            |
| M-02 | Surveillance Impact Report   | critical | `governance_gap`                                  |
| M-03 | Public Hearing Required      | critical | `procurement_timeline`, `administrative_integrity`|
| M-04 | Use Policy Required          | high     | `governance_gap`                                  |
| M-05 | Data Retention Limits        | high     | `governance_gap`                                  |
| M-06 | Data Sharing Restrictions    | high     | `surveillance`, `governance_gap`                  |
| M-07 | Annual Audit Report          | high     | `administrative_integrity`                        |
| M-08 | Community Oversight Body     | medium   | `governance_gap`                                  |
| M-09 | Vendor Contract Transparency | high     | `signature_chain`, `governance_gap`               |
| M-10 | Funding Source Disclosure    | medium   | `fiscal`                                          |
| M-11 | Penalty for Non-Compliance   | medium   | `administrative_integrity`                        |

### Mandate Descriptions

**M-01 — City Council Approval Required** *(critical)*
The elected body must approve acquisition of surveillance technology before
purchase or deployment. Required evidence: council resolution, vote record,
authorization date.

**M-02 — Surveillance Impact Report** *(critical)*
The agency must prepare and publish a Surveillance Impact Report (SIR) describing
the technology, its purpose, data collection scope, civil liberties impact, and
fiscal cost. Required evidence: surveillance impact report, public filing.

**M-03 — Public Hearing Required** *(critical)*
A public hearing must be held before acquisition where community members can
provide input. Required evidence: public hearing notice, hearing minutes, public
comment record.

**M-04 — Use Policy Required** *(high)*
A written use policy governing how the technology may and may not be used must be
adopted. Required evidence: use policy, department policy, operating procedures.

**M-05 — Data Retention Limits** *(high)*
The policy must specify how long data is retained and the procedures for deletion.
Required evidence: retention policy, deletion schedule.

**M-06 — Data Sharing Restrictions** *(high)*
The policy must restrict sharing of surveillance data with other agencies and define
authorization requirements. Required evidence: data sharing agreement, MOU, access
controls.

**M-07 — Annual Audit Report** *(high)*
The agency must publish an annual report on surveillance technology use including
statistics, complaints, and policy compliance. Required evidence: annual report,
audit report, compliance report.

**M-08 — Community Oversight Body** *(medium)*
An independent oversight body or committee must be established to monitor
surveillance technology use. Required evidence: oversight committee, advisory board,
civilian review.

**M-09 — Vendor Contract Transparency** *(high)*
Contracts with surveillance technology vendors must be publicly available and include
terms governing data access. Required evidence: executed contract, public contract,
vendor agreement.

**M-10 — Funding Source Disclosure** *(medium)*
All funding sources must be publicly disclosed, including grants, donations, and
third-party funding. Required evidence: funding disclosure, grant documentation,
budget authorization.

**M-11 — Penalty for Non-Compliance** *(medium)*
The ordinance must include enforcement mechanisms for non-compliance, including
technology moratorium or removal. Required evidence: enforcement clause, penalty
provision, compliance mechanism.

---

## Running a Compliance Check

### CLI

```bash
python scripts/run_compliance_check.py \
  --config-dir config/ \
  --source data/sources/ \
  --output reports/compliance/ \
  --atlas-data data/reference/atlas_sample.json \
  --has-ccops-ordinance
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `--config-dir` | `config/` | Jurisdiction config directory |
| `--source` | `data/sources/` | Document directory to ingest |
| `--output` | `reports/compliance/` | Output directory for reports |
| `--atlas-data` | *(none)* | Path to Atlas of Surveillance JSON file |
| `--has-ccops-ordinance` | *(false)* | Flag: ordinance is already adopted |
| `--jurisdiction` | *(from config)* | Override jurisdiction name |
| `--state` | *(none)* | Two-letter state code for Atlas lookup |
| `--verbose` | *(false)* | Enable debug logging |

**Output files:**

- `reports/compliance/<jurisdiction>_compliance.json` — Full `ComplianceScorecard` JSON
- `reports/compliance/<jurisdiction>_compliance.md` — Human-readable Markdown report

**Exit code:** 0 if no mandates are non-compliant; 1 otherwise (useful in CI pipelines).

### API

**Assess compliance:**

```http
POST /compliance/assess
Content-Type: application/json

{
  "jurisdiction": "example_city",
  "documents": [
    {
      "id": "proc-minutes-2023",
      "layer": "procurement_timeline",
      "issue": "No council vote found before technology purchase",
      "severity": "high",
      "details": {}
    }
  ],
  "has_ccops_ordinance": false,
  "state": "CA"
}
```

The `documents` field accepts two formats:
- **Flat anomaly dict** — any dict with a `layer` key (direct ODIA finding)
- **Analysis-result dict** — a dict with a `findings` key whose value is a
  `{layer: [anomaly, ...]}` mapping (output of `run_full_analysis()`)

**List all mandates:**

```http
GET /compliance/mandates
```

Returns all 11 mandates with descriptions, required evidence, and mapped detectors.

**Get a single mandate:**

```http
GET /compliance/mandates/M-01
```

Returns 404 if the mandate ID is not found.

---

## Interpreting the ComplianceScorecard

```json
{
  "jurisdiction": "example_city",
  "assessment_date": "2026-03-15",
  "has_ccops_ordinance": false,
  "total_mandates": 11,
  "compliant_count": 6,
  "non_compliant_count": 3,
  "partial_count": 1,
  "unknown_count": 1,
  "compliance_percentage": 54.55,
  "overall_risk": "critical",
  "mandate_statuses": [...],
  "technology_inventory": [...],
  "recommendations": [...]
}
```

### Status Values

| Status | Meaning |
|--------|---------|
| `compliant` | The relevant detector(s) ran and found no violations. |
| `non_compliant` | One or more relevant detectors found violations. |
| `partial` | Some relevant detectors ran clean; others did not run. |
| `unknown` | No relevant detectors ran — the mandate could not be evaluated. |

### Risk Levels

| Risk | Condition |
|------|-----------|
| `critical` | Any mandate with `severity: critical` is `non_compliant`. |
| `high` | More than 3 mandates are `non_compliant` or `partial`. |
| `moderate` | 1–3 mandates are `non_compliant` or `partial`. |
| `low` | No mandates are `non_compliant` or `partial`. |

### Compliance Percentage

```
compliance_percentage = (compliant_count / total_mandates) * 100
```

`partial` and `unknown` mandates do not count toward compliance.

---

## Sample CLI Output

```
============================================================
CCOPS Compliance Check: example_city
============================================================
Date         : 2026-03-15
Has Ordinance: No
Overall Risk : CRITICAL
Score        : 4/11 (36.4%)

Mandate  Status     Sev       Title
------------------------------------------------------------
M-01     [FAIL]     critical  City Council Approval Required
M-02     [FAIL]     critical  Surveillance Impact Report
M-03     [FAIL]     critical  Public Hearing Required
M-04     [----]     high      Use Policy Required
M-05     [----]     high      Data Retention Limits
M-06     [----]     high      Data Sharing Restrictions
M-07     [PASS]     high      Annual Audit Report
M-08     [----]     medium    Community Oversight Body
M-09     [PASS]     high      Vendor Contract Transparency
M-10     [PASS]     medium    Funding Source Disclosure
M-11     [PASS]     medium    Penalty for Non-Compliance

Recommendations:
  * [M-01] City Council Approval Required: Resolve 1 violation(s)...
  * [M-02] Surveillance Impact Report: Resolve 1 violation(s)...
  * [M-03] Public Hearing Required: Resolve 1 violation(s)...
```

---

## Atlas of Surveillance Integration

When `--atlas-data` is provided (or the `AtlasAdapter` is loaded), the scorecard
includes a `technology_inventory` list showing all surveillance technologies the
Atlas has on record for the jurisdiction. This lets investigators cross-reference
what equipment the agency is known to operate against what the CCOPS compliance
check covers.

Sample data is available at `data/reference/atlas_sample.json` (30 synthetic records
across 10 California agencies). For real data, download from the EFF Atlas of
Surveillance project at <https://atlasofsurveillance.org>.

---

## Programmatic Use

```python
from oraculus_di_auditor.adapters.ccops_adapter import CCOPSAdapter
from oraculus_di_auditor.adapters.atlas_adapter import AtlasAdapter
from oraculus_di_auditor.adapters.compliance_engine import ComplianceAssessmentEngine

ccops = CCOPSAdapter()
atlas = AtlasAdapter(local_dataset_path="data/reference/atlas_sample.json")
engine = ComplianceAssessmentEngine(ccops=ccops, atlas=atlas)

# Pass ODIA findings directly
findings = [
    {"id": "proc:no-vote", "layer": "procurement_timeline",
     "issue": "No council vote found", "severity": "high", "details": {}}
]
scorecard = engine.assess(
    jurisdiction="example_city",
    analysis_results=findings,
    state="CA",
    has_ccops_ordinance=False,
)

print(f"Risk: {scorecard.overall_risk}")
print(f"Score: {scorecard.compliance_percentage:.1f}%")
print(engine.generate_scorecard_markdown(scorecard))
```
