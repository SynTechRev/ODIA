# Multi-Jurisdiction Sample Dataset

This directory contains a synthetic sample dataset for demonstrating and testing the
ODIA multi-jurisdiction comparative analysis pipeline.

## Structure

```
data/multi_jurisdiction/
├── example_city_a/          # City of Riverside, CA (synthetic)
│   ├── surveillance_contract.txt
│   ├── budget_amendment.txt
│   └── policy_gap_report.txt
├── example_city_b/          # City of Lakewood, CA (synthetic)
│   ├── surveillance_contract.txt
│   ├── budget_amendment.txt
│   └── policy_gap_report.txt
└── example_city_c/          # County of Tulare, CA (synthetic)
    ├── surveillance_contract.txt
    ├── budget_amendment.txt
    └── policy_gap_report.txt
```

## About the Sample Data

All documents are **entirely synthetic** and generated for demonstration purposes only.
They do not represent actual procurement actions, budget decisions, or governance assessments
by any real jurisdiction. Any resemblance to actual documents is coincidental.

### Overlapping Patterns Embedded

The dataset is designed to exercise the cross-jurisdiction pattern detection capabilities
of ODIA. The following patterns are embedded across all three jurisdictions:

| Pattern | Description |
|---|---|
| **Vendor playbook replication** | All three jurisdictions contract with the same vendor ("SecureTech Solutions") using sole-source justifications |
| **Procurement parallel** | All three use similar sole-source language and pre-authorization letter-of-intent patterns |
| **Fiscal anomaly** | Budget amendments reference expenditures without confirmed appropriation numbers |
| **Governance gap** | Surveillance capabilities are deployed without data retention, access control, or public disclosure policies in place |
| **Timeline irregularity** | Contracts are partially executed or planning begins before formal board/council authorization |

## Running the Analysis

```bash
python scripts/run_multi_audit.py \
    --config-dir config/multi_jurisdiction \
    --source-dir data/multi_jurisdiction \
    --output reports/multi_jurisdiction \
    --verbose
```

To analyze only specific jurisdictions:

```bash
python scripts/run_multi_audit.py \
    --config-dir config/multi_jurisdiction \
    --source-dir data/multi_jurisdiction \
    --output reports/multi_jurisdiction \
    --jurisdictions example_city_a,example_city_b
```

## Expected Output

The pipeline generates two report files in the output directory:

- `multi_audit_<timestamp>.json` — Machine-readable comparative report with anomaly counts,
  comparison matrix, cross-jurisdiction patterns, risk ranking, and recommendations
- `multi_audit_<timestamp>.md` — Human-readable Markdown report with the same content

The cross-jurisdiction pattern detector should identify at least one vendor playbook
replication pattern (all three jurisdictions sharing the same vendor anomaly profile)
and at least one procurement parallel (shared sole-source justification language).

## Adding Your Own Data

1. Create a jurisdiction config in `config/multi_jurisdiction/<your_id>/jurisdiction.json`
2. Place source documents in `data/multi_jurisdiction/<your_id>/`
3. Run the CLI as shown above

See `docs/MULTI_JURISDICTION.md` for full setup and configuration guidance.
