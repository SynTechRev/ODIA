# O.D.I.A. AI — Fine-Tuning and Continual Learning

Extends the [O.D.I.A.](https://github.com/SynTechRev/ODIA) forensic audit platform with an AI-augmented document-extraction layer that learns from the audit record itself.

**License:** MIT
**Python:** 3.11+
**Status:** Alpha (0.1.0)

---

## What it is

The O.D.I.A. audit platform ingests municipal documents and runs twelve deterministic anomaly detectors across them. That produces a corpus of labeled findings — for the Tulare County 9-jurisdiction audit, ~1,379 alerts across 3,150+ documents. Each alert is an expert read of a source document, tagged with severity, finding category (F-1 through F-12), and primary-source citations.

**`odia_ai` converts that corpus into a training signal.** It builds a Layer 2 named-entity and relational extractor, fine-tunes a small LLM (Llama 3.1 8B / Qwen 2.5 7B / Mistral 7B) on audit labels, evaluates generalization across held-out jurisdictions, and continuously re-learns from user corrections.

Every component degrades gracefully — if the fine-tuned model is unavailable, extraction falls back to a RAG pipeline via the parent project's existing LLM providers (Ollama, OpenAI, Anthropic). If the RAG backend is unavailable, extraction falls back to a deterministic pattern-matching backend that always works.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      ODIA audit corpus                         │
│   (MAS markdown files, 9 jurisdictions, 1,379 alerts)          │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │  odia_ai.backref            │   Alert → document extraction
         │  extractor.py               │   (tested: 866 alerts from
         └──────────────┬──────────────┘    31 MAS files)
                        │
                        ▼
         ┌─────────────────────────────┐
         │  odia_ai.training           │   Dataset construction with
         │  dataset_builder.py         │   jurisdiction-transfer synthesis
         │                             │   and held-out splits
         └──────────────┬──────────────┘    (TCSO→val, Exeter→test)
                        │
                        ▼
         ┌─────────────────────────────┐
         │  odia_ai.training           │   LoRA fine-tune on single
         │  lora_runner.py             │   consumer GPU (4-bit NF4)
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  odia_ai.extraction         │   Runtime extraction:
         │  ExtractionService          │   - finetuned (preferred)
         │   ├─ FinetunedBackend       │   - rag_llm (parent's RAG)
         │   ├─ RAGExtractionBackend   │   - pattern (always available)
         │   └─ PatternBackend         │
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  odia_ai.evaluation         │   Set-based P/R/F1 per field,
         │  harness.py                 │   per jurisdiction, per finding
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  odia_ai.continual          │   SQLite-backed correction store
         │  feedback_store.py          │   + automatic re-training triggers
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  odia_ai.registry           │   Versioned models with SHA-256
         │  registry.py                │   provenance, staged deployment
         └─────────────────────────────┘
```

---

## Installation

### Core package (no ML dependencies)

```bash
pip install -e .
```

The pattern-matching extraction backend, dataset builder, correction store, registry, and evaluation harness all work with stdlib + numpy + the parent project's dependencies.

### With server integration

```bash
pip install -e ".[server]"
```

Adds FastAPI so the `/ai/*` routes can be registered onto the existing O.D.I.A. Desktop backend.

### With fine-tuning

```bash
pip install -e ".[training]"
```

Adds PyTorch, transformers, PEFT, bitsandbytes, accelerate, and trl. Only needed when actually fine-tuning. A single RTX 4090 (24GB) is sufficient for 7B-8B LoRA at r=16 with batch-size 1 × gradient-accumulation 16.

### Everything

```bash
pip install -e ".[all,dev]"
```

---

## Quick start

### 1. Build a training dataset from your MAS corpus

```bash
odia-ai build-dataset --mas-dir ./data/mas_corpus --output-dir ./data/splits
```

Produces:
```
./data/splits/
  _raw_alerts.jsonl     # All extracted alerts as ExtractedAlert records
  train.jsonl           # Training split (alpaca format)
  validation.jsonl      # Held-out: TCSO jurisdiction
  test.jsonl            # Held-out: Exeter jurisdiction
```

Tested on the Tulare County corpus: 31 MAS files → 866 alerts → 623 training examples with jurisdiction-transfer synthesis enabled.

### 2. Evaluate the baseline pattern backend

```bash
odia-ai evaluate --dataset ./data/splits/test.jsonl --backend pattern
```

Produces per-field precision/recall/F1 metrics as a baseline. The pattern backend is deterministic and always available; its scores set the floor any fine-tuned model must beat.

### 3. Fine-tune (requires GPU)

```bash
odia-ai init-config --path ./odia_ai_config.json
# edit ./odia_ai_config.json to point at your base model and paths
odia-ai --config ./odia_ai_config.json train
```

The training run registers the resulting model in the registry automatically.

### 4. Promote a model to production

```bash
odia-ai registry list
odia-ai registry promote --version-id odia-l2-v0.1.0+a1b2c3d4
```

### 5. Run extraction from the command line

```bash
odia-ai extract --file path/to/document.txt
# or pipe stdin:
cat document.txt | odia-ai extract
```

### 6. Check continual-learning status

```bash
odia-ai feedback stats
```

Shows how many corrections have accumulated, whether a re-training trigger has fired, and correction counts broken down by field and jurisdiction.

---

## Integration with the existing O.D.I.A. backend

The FastAPI routes in `odia_ai.server_routes` attach to the existing `oraculus_di_auditor.interface.api` backend with a single line. In `interface/api.py`:

```python
def create_app() -> FastAPI:
    app = FastAPI(title="ODIA")
    # ... existing routes ...

    # NEW: attach AI extraction, feedback, registry endpoints
    try:
        from odia_ai.server_routes import include_ai_routes
        include_ai_routes(app, config_path="./odia_ai_config.json")
    except ImportError:
        pass  # odia_ai not installed; backend runs without AI routes

    return app
```

The new routes appear under `/ai/*`:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ai/extract` | Layer 2 extraction on a document passage |
| POST | `/ai/corrections` | Submit a user correction to an extraction output |
| GET | `/ai/corrections/stats` | Corrections store summary |
| GET | `/ai/registry/versions` | List registered model versions |
| GET | `/ai/registry/versions/{id}` | Single model version metadata |
| GET | `/ai/status` | System status (backends, corrections, triggers) |
| GET | `/ai/health` | Health check |

The desktop app (Electron) can now offer a **"Correct this extraction"** UI that calls `POST /ai/corrections`, accumulating labeled corrections that feed back into the next re-training run.

---

## Training-dataset schema

Each training example is an alpaca-format JSON record:

```json
{
  "instruction": "Extract structured information from the following document passage. Return only JSON matching the ODIA schema.",
  "input": "[document passage]",
  "output": "{\"vendors\": [...], \"persons\": [...], \"dollar_amounts\": [...], \"statutes_cited\": [...], \"procurement_instruments\": [...], \"governance_bodies\": [...], \"anomaly_candidates\": [...]}",
  "system": "[ODIA analyst system prompt]"
}
```

**Output schema fields:**
- `vendors` — surveillance/tech vendor names present in text
- `persons` — `{name, role, agency}` objects for named officials
- `dollar_amounts` — `{amount_raw, vendor, context}` objects
- `statutes_cited` — statutory citations (SB 524, AB 481, Civil Code §1798.90.5x, etc.)
- `procurement_instruments` — `{type, number, date}` objects (resolutions, ordinances, agreements)
- `governance_bodies` — named oversight committees, task forces, advisory bodies (F-11 detector)
- `anomaly_candidates` — `{category, severity, reasoning}` where category is F-1 through F-12

---

## Held-out jurisdiction policy

Splits are **deliberate, not random**:

- **TCSO** → validation (constitutional-officer jurisdiction; structurally distinct from municipalities)
- **Exeter** → test (largest coverage in the current corpus; strongest generalization signal)
- **All other jurisdictions** → train

Random splits would leak neighboring context across splits (MAS versions cite prior findings; same resolution numbers appear in multiple alerts). Jurisdictional hold-out tests the actual deployment scenario: extending to Kings County, Kern County, Fresno County, and statewide.

---

## Continual learning

The `CorrectionStore` persists three types of user feedback:

- **Addition** — the model missed an extraction the user expected
- **Deletion** — the model produced a false positive
- **Modification** — the model produced a value that the user corrects

Corrections are keyed by SHA-256 of the input text and stamped with the model version that produced the original extraction. A re-training trigger fires when:

- 50+ reviewed corrections have accumulated since the last training run (configurable)
- 30+ days have elapsed with any pending corrections (configurable)
- Evaluation F1 regresses by 2% against the held-out test set (configurable)

When a trigger fires, corrections are converted back into training examples and merged with the base training dataset for the next fine-tuning run.

---

## Tests

34 stdlib-only tests validate the extractor, dataset builder, extraction backends, evaluation harness, correction store, trigger logic, registry promotion, and config round-trip. Run:

```bash
# pytest (requires pytest installed)
pytest odia_ai/tests

# or stdlib-only
python -m odia_ai.tests.run_stdlib_tests
```

All pass:

```
Ran 34 tests in 0.349s
OK
```

---

## Scope expansion

The same infrastructure applies directly to:

- **Kings County** (Hanford, Lemoore, Corcoran, Avenal) — known Flock deployment
- **Kern County** (Bakersfield, Delano, McFarland) — large Sheriff's Office + extensive Flock
- **Fresno County** (Fresno PD, Clovis, Selma, Reedley, Sanger, Kingsburg)

Adding a new jurisdiction requires only a new MAS corpus — `odia-ai build-dataset` re-generates the training splits and the next fine-tune generalizes from the existing 9-jurisdiction signal.

At scale, the CivicPlus / Legistar / Granicus scraper infrastructure (separate component) feeds new municipal agendas continuously into `odia-ai extract`; any anomaly candidates above a configurable severity threshold enter a review queue. Accepted candidates become new alerts; rejected candidates become labeled negative examples. The system gets stronger as it is used.

---

## Relationship to the parent project

The `odia_ai` package is a sibling of `oraculus_di_auditor`, not a replacement. The parent project's twelve deterministic detectors, RAG infrastructure, desktop application, and vendor database all remain primary. `odia_ai` adds:

1. A way to convert audit output into training data
2. A way to train a model on that data
3. A way to serve the model alongside the deterministic detectors
4. A way to capture corrections and improve the model over time

All four are optional. The parent project runs entirely without `odia_ai` installed.

---

## License

MIT. Same terms as the parent ODIA project.
