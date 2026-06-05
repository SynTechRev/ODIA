# ODIA API Verifier

Repeatable verification protocol for the ODIA FastAPI backend and legal
pipeline. Run this before any push that touches `src/odia_legal/`,
`src/oraculus_di_auditor/interface/routes/legal_routes.py`,
`src/oraculus_di_auditor/analysis/audit_engine.py`, or
`scripts/bulk_ingest.py`.

---

## Launch

Open two terminals from the repo root:

**Terminal 1 — API**
```powershell
cd "C:\Users\yahua\Downloads\ODI x RAIA\Oraculus-DI-Auditor-clean"
uvicorn oraculus_di_auditor.interface.api:app --reload --port 8000
```

**Terminal 2 — Frontend**
```powershell
cd "C:\Users\yahua\Downloads\ODI x RAIA\Oraculus-DI-Auditor-clean\frontend"
npm run dev
```

**Readiness checks** (wait up to 30s each):
```
GET http://localhost:8000/api/v1/legal/status
  → {"status":"ok","detectors_available":9}

GET http://localhost:3000/legal
  → HTTP 200
```

If `detectors_available` is less than 9, check that L-4, L-7, and L-10
are listed under `detectors` before proceeding — those were the last
three wired in (v3.8.0 / commit 559f4f2).

---

## Canonical smoke test — L-10 golden path

This is the primary evidence capture. Run it on every verification.

```
POST http://localhost:8000/api/v1/legal/analyze
Content-Type: application/json

{
  "text": "The agency deployed ALPR license plate reader systems pursuant to AB 481. License plate reader data is collected on vehicles passing through the city. The department stores ALPR data for one year. Records requested under Government Code section 7922.000 are withheld because it is not in the public interest to disclose them. The ALPR system provides persistent location surveillance of all vehicles.",
  "document_id": "smoke_test_l10"
}
```

**Required in response:**
- `counts.total >= 2`
- `findings` must contain an entry with `id` matching `legal:l10:balancing_test:alpr_carpenter_not_analyzed` at severity `medium`
- `findings` must contain an entry with `id` matching `legal:l10:balancing_test:cpra_conclusory_balancing` at severity `high`

**Expected full result (as of v3.8.0):** 12 findings — 4 high, 3 medium, 5 low — across L-1, L-2, L-3, L-6, L-10.

---

## Memorandum mode

```
POST http://localhost:8000/api/v1/legal/memorandum
Content-Type: application/json

{
  "text": "",
  "findings": [
    {
      "id": "legal:l10:balancing_test:alpr_carpenter_not_analyzed",
      "issue": "Comprehensive location surveillance (ALPR/CSLI) present without Carpenter mosaic-theory analysis",
      "severity": "medium",
      "layer": "l10_balancing_test",
      "details": {
        "framework": "Carpenter v. United States (2018) 585 U.S. 296",
        "detail": "Carpenter requires analysis of whether long-term surveillance aggregates into a comprehensive chronicle of daily movements requiring a warrant"
      }
    },
    {
      "id": "legal:l10:balancing_test:cpra_conclusory_balancing",
      "issue": "CPRA catch-all exemption invoked with only conclusory public-interest statement",
      "severity": "high",
      "layer": "l10_balancing_test",
      "details": {
        "framework": "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325",
        "statute": "Gov. Code 7922.000"
      }
    }
  ],
  "doc_meta": {
    "title": "TPD 2025 AB 481 Annual Report",
    "agency": "Tulare Police Department",
    "date": "2025-01-01"
  },
  "format": "text"
}
```

**Required in response:**
- `finding_count == 2`
- `output` contains `TABLE OF AUTHORITIES`
- `output` contains `Times Mirror`
- `toa_citations` is non-empty

---

## Explainer mode — community audience

```
POST http://localhost:8000/api/v1/legal/explain
Content-Type: application/json

{
  "findings": [same two findings as memorandum test above],
  "doc_meta": {"title": "TPD 2025 AB 481 Annual Report", "agency": "Tulare Police Department"},
  "audience": "community",
  "format": "text"
}
```

**Required in response:**
- `audience == "community"`
- `finding_count == 2`
- `output` contains `SERIOUS CONCERN` or `WORTH INVESTIGATING`

---

## Probes (run at least two per session)

| Probe | Input | Expected |
|---|---|---|
| Empty text | `POST /analyze` with `"text": ""` | `counts.total == 0` |
| Whitespace only | `POST /analyze` with `"text": "   \n\t  "` | `counts.total == 0` |
| Layer filter | `POST /analyze` with `"layers": ["l10_balancing_test"]` and ALPR+CPRA text | only `l10_balancing_test` in returned `layer` fields |
| Invalid audience | `POST /explain` with `"audience": "badvalue"` | HTTP 422 |
| Missing required field | `POST /analyze` with body `{}` | HTTP 422 |

---

## Corpus / RAG check (run after any bulk_ingest or build_rag_index run)

```
GET http://localhost:8000/api/v1/legal/status
```

Cross-reference against known index state:

| Index | Baseline (post-Tulare ingest, 2026-06-05) |
|---|---|
| corpus | 6,368 |
| ace | 22,039 |
| jim | 467 |
| Legal findings in ace | 2,326 |

If corpus count drops below 6,368 or ace below 22,039, the RAG index
needs a rebuild (`python scripts/build_rag_index.py`).

---

## Known issues / environment notes

- Memorandum em-dashes render as `â` in Windows PowerShell console —
  this is a UTF-8 terminal display artifact, not a bug. Raw JSON body
  and browser rendering are correct.
- `ocr_engine.py` is a stub. The 212 image-embedded Tulare minutes PDFs
  (2024+ meeting minutes) are skipped during ingestion with
  `skipped_empty`. Tesseract OCR integration is a medium-term item.
- L-8 (Case-Law Currency / CourtListener) is not yet implemented.
  `explainer.py` has its label registered but the detector file does
  not exist and it is absent from `pipeline.py`. Expected gap.
