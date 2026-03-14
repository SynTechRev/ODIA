# Multi-Jurisdiction Analysis Guide

ODIA supports comparative analysis across multiple jurisdictions in a single pipeline run.
This guide explains how to set up jurisdiction configurations, organize source documents,
run the analysis, and interpret the output reports.

---

## Directory Structure

```
config/
└── multi_jurisdiction/
    ├── <jurisdiction_id>/
    │   ├── jurisdiction.json      # Required
    │   ├── agencies.json          # Optional: agency name aliases
    │   └── corpus_manifest.json   # Optional: corpus ID → meeting date map
    └── ...

data/
└── multi_jurisdiction/
    ├── <jurisdiction_id>/
    │   ├── document1.txt
    │   ├── document2.pdf
    │   └── ...
    └── ...

reports/
└── multi_jurisdiction/
    ├── multi_audit_<timestamp>.json
    └── multi_audit_<timestamp>.md
```

Jurisdiction IDs are directory names under `config/multi_jurisdiction/`. They must
match the corresponding directory names under `data/multi_jurisdiction/`.

---

## Jurisdiction Configuration

### jurisdiction.json (required)

```json
{
  "name": "City of Example",
  "state": "CA",
  "country": "US",
  "meeting_type": "City Council Regular Meeting",
  "legistar_base_url": "https://example.legistar.com"
}
```

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Human-readable jurisdiction name (appears in reports) |
| `state` | No | Two-letter state/province code |
| `country` | No | ISO country code |
| `meeting_type` | No | Meeting type label for display |
| `legistar_base_url` | No | Legistar API base URL (for future corpus ingestion) |

### agencies.json (optional)

Maps canonical agency names to text aliases used during extraction:

```json
{
  "City Council": ["city council", "council", "council meeting"],
  "Finance Department": ["finance", "finance department"]
}
```

### corpus_manifest.json (optional)

Maps corpus document IDs to meeting dates:

```json
{
  "DOC-001": "2024-01-15",
  "DOC-002": "2024-02-20"
}
```

Copy the provided example files from `config/multi_jurisdiction/example_city_a/`
as a starting point.

---

## Supported Document Types

The pipeline ingests the following file types from each jurisdiction's source directory:

| Extension | Handling |
|---|---|
| `.txt` | Read as UTF-8 text |
| `.json` | Parsed; if the file contains a `raw_text` key, that value is used as document text |
| `.xml` | Read as UTF-8 text |
| `.pdf` | Extracted via `pdfplumber`, `pypdf`, or `PyPDF2` (first available) |

Files with other extensions are silently skipped.

---

## Running the CLI

### Basic usage

```bash
python scripts/run_multi_audit.py \
    --config-dir config/multi_jurisdiction \
    --source-dir data/multi_jurisdiction \
    --output reports/multi_jurisdiction \
    --verbose
```

### Analyze specific jurisdictions

```bash
python scripts/run_multi_audit.py \
    --config-dir config/multi_jurisdiction \
    --source-dir data/multi_jurisdiction \
    --output reports/multi_jurisdiction \
    --jurisdictions city_a,city_b
```

### CLI flags

| Flag | Required | Default | Description |
|---|---|---|---|
| `--config-dir` | Yes | — | Directory containing per-jurisdiction config subdirectories |
| `--source-dir` | Yes | — | Directory containing per-jurisdiction document subdirectories |
| `--output` | Yes | — | Output directory for reports |
| `--verbose` | No | off | Print detailed progress to stdout |
| `--jurisdictions` | No | all | Comma-separated jurisdiction IDs to include |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Error (config directory not found, no valid jurisdictions, etc.) |

---

## REST API

Multi-jurisdiction analysis is also available via the FastAPI server:

### POST /multi/analyze

Run comparative analysis on documents provided inline:

```bash
curl -X POST http://localhost:8000/multi/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "jurisdictions": {
      "city_a": [
        {"document_text": "Policy document text.", "metadata": {"title": "Policy Doc"}}
      ],
      "city_b": [
        {"document_text": "Contract document text.", "metadata": {}}
      ]
    }
  }'
```

### GET /multi/jurisdictions

Return the loaded jurisdiction registry summary:

```bash
curl http://localhost:8000/multi/jurisdictions
```

The server loads jurisdiction configs from `config/multi_jurisdiction/` at startup.
Unknown jurisdiction IDs submitted via the API receive a bare default configuration
and are still analyzed.

---

## Report Structure

### JSON Report

The JSON report (`multi_audit_<timestamp>.json`) contains:

```json
{
  "report_type": "multi_jurisdiction_comparison",
  "generated_at": "2024-03-15T12:00:00+00:00",
  "jurisdictions": {
    "<id>": {
      "name": "...",
      "document_count": 3,
      "anomaly_count": 7,
      "top_severity": "high"
    }
  },
  "comparison_matrix": {
    "<detector>": {
      "<jurisdiction_id>": <anomaly_count>
    }
  },
  "cross_jurisdiction_patterns": [...],
  "risk_ranking": [
    {"jurisdiction_id": "...", "risk_score": 18, "rank": 1}
  ],
  "recommendations": ["..."]
}
```

### Markdown Report

The Markdown report (`multi_audit_<timestamp>.md`) contains five sections:

1. **Executive Summary** — totals across all jurisdictions
2. **Jurisdiction Comparison Table** — anomaly counts by jurisdiction and severity
3. **Cross-Jurisdiction Patterns** — detected patterns with affected jurisdictions and confidence scores
4. **Risk Ranking** — jurisdictions ranked by composite risk score
5. **Recommendations** — actionable guidance based on findings

---

## Cross-Jurisdiction Pattern Detection

The pattern detector identifies three pattern types:

### Vendor Playbook Replication

Fires when two or more jurisdictions share the same anomaly `id` (e.g., `fiscal:amount-without-appropriation`).
This indicates a vendor may be deploying the same contract structure across multiple clients,
replicating the same fiscal or governance gaps.

**Confidence** = (jurisdictions sharing the pattern) / (total jurisdictions analyzed)

### Procurement Parallels

Fires when two or more jurisdictions share procurement-related keyword matches
(e.g., "sole-source", "emergency procurement", "letter of intent"). This suggests
parallel procurement strategies that may warrant coordinated scrutiny.

### Regional Governance Gaps

Fires when two or more jurisdictions share governance-related anomalies
(e.g., missing data retention policies, missing public disclosure). This suggests
a systemic regional gap rather than an isolated finding.

---

## Risk Scoring

Each jurisdiction receives a composite risk score:

| Severity | Weight |
|---|---|
| Critical | 5 |
| High | 3 |
| Medium | 1 |
| Low | 0 |
| Cross-jurisdiction pattern involvement | +2 per pattern |

Jurisdictions are ranked highest-to-lowest by this score in the report.

---

## Sample Dataset

A synthetic sample dataset is included in `data/multi_jurisdiction/` covering three
California jurisdictions (City of Riverside, City of Lakewood, County of Tulare).
The dataset embeds overlapping vendor, procurement, fiscal, and governance anomaly
patterns for demonstration purposes.

See `data/multi_jurisdiction/README.md` for details on the embedded patterns.

Run the sample:

```bash
python scripts/run_multi_audit.py \
    --config-dir config/multi_jurisdiction \
    --source-dir data/multi_jurisdiction \
    --output reports/multi_jurisdiction \
    --verbose
```
