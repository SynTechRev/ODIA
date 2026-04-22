# ODIA AI Integration — Install Report

Generated: 2026-04-21
Host: Windows 10, Python 3.13.7, Git Bash
Repo: `C:\Users\yahua\Downloads\ODI x RAIA\Oraculus-DI-Auditor-clean`

---

## Installation Status

| Item | Value |
|---|---|
| Package location | `./odia_ai/` (repo root) |
| Integration patch | Applied to `src/oraculus_di_auditor/interface/api.py`, lines 131–145 (15 lines added inside `create_app()`) |
| Base dependencies | fastapi 0.135.1, pydantic 2.12.5, uvicorn 0.41.0, pyyaml 6.0.3, pytest 8.3.3 — all pre-existing |
| `oraculus_di_auditor` importable | Yes, via `PYTHONPATH=src` |
| ML training extras | **Not installed** — torch/transformers/peft/bitsandbytes/accelerate/trl deliberately skipped (gigabytes, needs GPU) |
| Python interpreter | 3.13.7, invoked as `python` (no `python3` alias on this host) |
| `PYTHONPATH` separator | `;` (Windows) — all invocation recipes in this report use that |

---

## Verification Results

### Phase 1 — Discovery

- Repo root confirmed (has `src/oraculus_di_auditor/`, `desktop/`, `frontend/`, `.git/`).
- Package extracted at `O.D.I.A._AI-0.1.0/odia_ai_build/odia_ai/` — **two levels below repo root**, not one as the build prompt assumed. Phase 2 flattened.
- `create_app()` at `src/oraculus_di_auditor/interface/api.py:81-131` — `logger` (line 28) and `os` (line 21) already imported at module scope, so the patch reuses them.
- Pre-flight odia_ai stdlib tests: **34/34 pass** in 12.0 s.

### Phase 2 — Package placement

Moves performed (all on untracked files extracted from the zip):

```
O.D.I.A._AI-0.1.0/odia_ai_build/odia_ai/                  -> ./odia_ai/
O.D.I.A._AI-0.1.0/odia_ai_build/odia_ai_config.example.yaml -> ./odia_ai_config.example.yaml
O.D.I.A._AI-0.1.0/odia_ai_build/INTEGRATION_PATCH.md       -> ./INTEGRATION_PATCH.md
O.D.I.A._AI-0.1.0/odia_ai_build/pyproject.toml             -> ./odia_ai/pyproject.toml
O.D.I.A._AI-0.1.0/odia_ai_build/LICENSE                    -> ./odia_ai/LICENSE
```

The package's `pyproject.toml` and `LICENSE` are kept **inside** `odia_ai/` so the repo's top-level `pyproject.toml` and `LICENSE` are untouched.

Cleaned up:
- Stray empty directory `odia_ai/{training,extraction,evaluation,backref,configs,scripts,cli,server_routes,continual,registry}` — a shell brace-expansion artifact from the original build script (braces got quoted so `mkdir -p` created one literal directory instead of ten siblings).
- Empty parents `O.D.I.A._AI-0.1.0/odia_ai_build/` and `O.D.I.A._AI-0.1.0/` — fully removed.

### Phase 3 — Dependency resolution

Nothing installed. Every optional group (`server`, `rag`, `yaml`) was satisfied by the repo's existing environment. Imports verified:

```
from odia_ai import backref, training, extraction, evaluation,
                   continual, registry, configs   # OK
from odia_ai.server_routes import include_ai_routes # OK
from odia_ai.cli.main import main                    # OK
```

### Phase 4 — Integration patch

Diff:

```diff
--- a/src/oraculus_di_auditor/interface/api.py
+++ b/src/oraculus_di_auditor/interface/api.py
@@ -128,6 +128,21 @@ def create_app() -> Any:
     _register_routes(app)
     _register_feature_routes(app)

+    # ODIA AI subsystem integration (odia_ai package) - guarded import.
+    # Exposes /ai/extract, /ai/status, /ai/health, /ai/corrections,
+    # /ai/corrections/stats, /ai/registry/versions. Silent no-op if odia_ai
+    # is not installed so the core backend still starts.
+    try:
+        from odia_ai.server_routes import include_ai_routes
+
+        ai_config_path = os.environ.get("ODIA_AI_CONFIG")
+        include_ai_routes(app, config_path=ai_config_path)
+        logger.info("odia_ai routes registered under /ai/*")
+    except ImportError:
+        logger.info("odia_ai not installed; /ai/* routes unavailable")
+    except Exception as exc:  # noqa: BLE001 - never crash app startup
+        logger.warning("odia_ai route registration failed: %s", exc)
+
     return app
```

Routes present after `create_app()`:

```
/ai/corrections
/ai/corrections/stats
/ai/extract
/ai/health
/ai/registry/versions
/ai/registry/versions/{version_id}
/ai/status
```

All 7 expected routes registered.

### Phase 5 — Live API verification

Backend ran via `uvicorn oraculus_di_auditor.interface.api:create_app --factory --host 127.0.0.1 --port 18743` (port 18741 was already occupied on this host; 18742 used before a restart; 18743 was the successful run).

**1. Health**
```json
{"status":"ok","subsystem":"odia_ai"}
```

**2. Status**
```json
{
    "backends_available": ["pattern"],
    "corrections_total": 0,
    "corrections_pending": 0,
    "should_retrain": false,
    "retrain_reason": "0 reviewed/unapplied corrections; threshold 50",
    "production_model_version": null,
    "config": {
        "llm_provider": "ollama",
        "llm_model": "llama3.1:8b",
        "finetuned_model_path": null,
        "correction_store": "./data/corrections.db",
        "registry_root": "./models/registry"
    }
}
```

**3. Extract** — input text: `"City Council adopted Resolution 2024-32 authorizing a $298,000 Flock Safety sole-source procurement on consent calendar Item 7.1. SB 524 not referenced. CJIS Security Addendum absent. This is a CRITICAL F-2 finding."`
```json
{
    "extraction": {
        "vendors": ["Flock Safety", "Flock"],
        "persons": [],
        "dollar_amounts": [{"amount_raw": "$298,000", "vendor": "Flock Safety", "context": ""}],
        "statutes_cited": ["SB 524", "CJIS"],
        "procurement_instruments": [{"type": "resolution_or_agreement", "number": "2024-32", "date": null}],
        "governance_bodies": [],
        "anomaly_candidates": [{"category": "F-2", "severity": "CRITICAL", "reasoning": "Pattern-matched from document text"}],
        "_backend": "pattern"
    },
    "backend_used": "pattern"
}
```
All required fields present (vendors, SB 524 + CJIS, Resolution 2024-32, $298,000, F-2/CRITICAL anomaly, backend "pattern"). **Pass.**

**4. Correction POST**
```json
{"correction_id": "644d8f55-6878-4b29-a11e-20420e6b8d2a", "stored": true}
```

**5. Correction stats** (after the POST)
```json
{"total": 1, "reviewed": 0, "pending": 0, "by_field": {"vendors": 1}, "by_jurisdiction": {"Test": 1}}
```

**6. Server cleanly terminated.**

**Bug found and fixed during Phase 5** (see "Fixes applied" below): the `/ai/extract` endpoint was initially rejecting every request because FastAPI was classifying the Pydantic body model as a query parameter. Root cause: `from __future__ import annotations` combined with Pydantic models defined inside a closure.

### Phase 6 — CLI pipeline

- `odia-ai --help` — all 7 subcommands listed: `init-config`, `build-dataset`, `train`, `evaluate`, `extract`, `registry`, `feedback`.
- `init-config` — writes `odia_ai_config.json`, valid JSON, 5 top-level keys (`dataset`, `training`, `evaluation`, `continual`, `deployment`).
- `build-dataset --mas-dir ./_fake_mas_corpus` — correctly reports `Scanning 1 MAS files`, extracts 2 alerts, populates `vendors_mentioned`, `statutes_mentioned`, `resolutions_mentioned`, `dollar_amounts` on both. All 2 alerts placed in `train` split (expected for a 2-alert corpus — jurisdiction holdout logic keeps Tulare in train).
- `extract --backend pattern --text ...` — returns the expected JSON shape with `_backend: "pattern"`.
- `registry list` — `(registry is empty)`.
- `feedback stats` — reports `Total corrections: 1` (the correction posted in Phase 5), `by_field: vendors=1`, `by_jurisdiction: Test=1`. **API and CLI share the same `./data/corrections.db` store when both run from the repo root** — no path divergence issue.

**Bug found and fixed during Phase 6** (see "Fixes applied" below): `mas_dir.glob("*.md") + mas_dir.glob("*.MD")` double-scanned every file on Windows.

### Phase 7 — Full test suite

| Runner | Result | Time |
|---|---|---|
| `python -m odia_ai.tests.run_stdlib_tests` | **34 / 34 pass** | 9.4 s |
| `python -m pytest odia_ai/tests -v` | **37 / 37 pass** | 10.9 s |

(pytest collects 37 items because the same tests are exposed both as flat `test_*` functions and grouped TestCase methods; both runners pass cleanly.)

### Phase 8 — Real MAS corpus

No real MAS files present in the repo (`find` for `*MAS*.md`, `VPD*`, `PPD*`, `TUL*`, `LIND*`, `FAR*`, `WDL*`, `DIN*`, `EXE*`, `TCSO*`, `Tulare*`, `Exeter*`, `Dinuba*`, `Visalia*`, `Farmersville*`, `Lindsay*`, `Woodlake*`, `Porterville*` — only my fake `_fake_mas_corpus/Test_MAS_V1_0.md`). Phase skipped per the build-prompt's own directive.

---

## Fixes Applied to the `odia_ai` Package

Two genuine bugs were found in the shipped package. Both were single-line fixes; both have been applied in-place. Neither touched the `oraculus_di_auditor` code.

### Fix 1 — `odia_ai/server_routes/routes.py`: removed `from __future__ import annotations`

The file defined Pydantic request models (`ExtractRequest`, `CorrectionRequest`, `StatusResponse`) **inside** the `_build_router()` function (closure locals). With `from __future__ import annotations`, every type annotation becomes a string (PEP 563). When FastAPI calls `get_type_hints()` on each endpoint to classify parameters as body vs query, it evaluates the annotation string against the function's **module globals** — which do not contain `ExtractRequest` (it's a closure cell, not a module attribute). FastAPI falls back to treating `req` as a query parameter, and every POST is rejected with `"loc": ["query", "req"]`.

Removing the future import lets Python evaluate annotations eagerly at function-body execution, when the Pydantic classes are already in scope. All union syntax in the file (`str | None`, `list[str]`) works natively on Python 3.10+, which is below the 3.11 project minimum.

Diff:
```diff
-from __future__ import annotations
-
 import hashlib
```

**Alternative fix** if the project wants to keep future-style annotations everywhere: move the three Pydantic classes to module scope. Current in-place fix is minimal; the alternative is a larger structural change.

### Fix 2 — `odia_ai/cli/main.py`: dedupe MAS file glob on case-insensitive filesystems

Line 77 used to read:
```python
mas_files = sorted(mas_dir.glob("*.md")) + sorted(mas_dir.glob("*.MD"))
```

On Windows (and case-insensitive macOS HFS+/APFS volumes), `Path.glob()` is case-insensitive, so both patterns match every `.md` file and `extract_corpus()` processes each file twice. On Linux (case-sensitive ext4) the two patterns are disjoint and the code is correct.

Fix: set-union dedupe. Works identically on all platforms.

```python
# set-union dedupes hits on case-insensitive filesystems (Windows/macOS),
# where *.md and *.MD match the same files.
mas_files = sorted({*mas_dir.glob("*.md"), *mas_dir.glob("*.MD")})
```

---

## Open Issues (non-fatal)

1. **`python -m odia_ai.cli.main` emits a `RuntimeWarning`.** The CLI's `__init__.py` imports `main` at package-import time, which makes `python -m` see the module already loaded and warn about ordering. Harmless but noisy — users who pipe the CLI output may see stderr noise. Fix would be to drop the `from .main import ...` in `odia_ai/cli/__init__.py`.
2. **CLI help output uses an em-dash (`—`) which renders as `�` on Windows cp1252 stdout.** Functional output (JSON, etc.) is clean. Fix would be to either `sys.stdout.reconfigure(encoding="utf-8")` at CLI entry or use an ASCII hyphen in the description.
3. **Port 18741 was occupied on this host** during Phase 5. The build prompt names that port explicitly — everything worked on 18743. Not a package issue; just a note for anyone reusing the verification recipe verbatim.

---

## What You Should Do Next

**1. Place your real MAS corpus.**

The CLI expects a flat directory of `.md` files named after each MAS version (e.g. `Exeter_MAS_V16_0.md`, `VPD_V8_0.md`, `Tulare_County_MAS_V1_0.md`). Recommended path:

```
data/mas_corpus/
  VPD_V8_0.md
  Tulare_County_MAS_V1_0.md
  Exeter_MAS_V16_0.md
  ...
```

Then build the dataset:

```bash
PYTHONPATH=".;src" python -m odia_ai.cli.main build-dataset \
    --mas-dir data/mas_corpus \
    --output-dir data/odia_ai_datasets \
    --format alpaca
```

Expected: roughly 600–900 training examples across 7–9 jurisdictions, with jurisdiction holdouts producing `train.jsonl` / `validation.jsonl` / `test.jsonl`.

**2. Daily backend start.**

No new command needed. The existing `uvicorn` invocation now serves `/ai/*` automatically:

```bash
PYTHONPATH=".;src" python -m uvicorn \
    oraculus_di_auditor.interface.api:create_app --factory
```

Check `/ai/health` to confirm the integration is live. If you ever deploy to a minimal host without `odia_ai` installed, the try/except block makes the backend silently skip `/ai/*` and keep the core detectors running — no startup crash.

**3. Install the training extras (only when you have GPU hardware).**

These are multi-gigabyte. Do **not** install on a laptop you use for frontend work.

```bash
pip install torch transformers peft datasets accelerate bitsandbytes trl
```

Realistically: rent an A100 for 2–4 hours (≈ $5–15 on RunPod / Lambda / vast.ai), run `odia-ai train` there, copy the resulting adapter back, promote via `odia-ai registry promote <version_id>`.

**4. Configure an LLM provider (optional — enables the RAG backend).**

Edit `odia_ai_config.example.yaml` → rename to `odia_ai_config.yaml`, set `deployment.default_llm_provider` to `ollama` / `anthropic` / `openai`, and point the backend at it:

```bash
export ODIA_AI_CONFIG="$(pwd)/odia_ai_config.yaml"
```

With `ollama` you need `ollama serve` running locally and the model pulled (e.g. `ollama pull llama3.1:8b`). With `anthropic`/`openai` set `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`.

**5. First real end-to-end loop.**

```
1. build-dataset          -> data/odia_ai_datasets/{train,val,test}.jsonl
2. evaluate --backend pattern   -> baseline metrics before any training
3. (from the frontend / desktop app) submit corrections via POST /ai/corrections
4. Wait until corrections_pending >= 50 (see /ai/status.retrain_reason)
5. train                  -> new LoRA adapter under models/registry/<uuid>/
6. evaluate --backend finetuned --model <path>  -> compare to baseline
7. registry promote <version_id>                -> new production model
```

Every correction is a labeled example. Every retrain cycle tightens the model against the specific failures your reviewers found.

**6. Desktop app bundling (when you rebuild the PyInstaller binary).**

Add the hiddenimports listed in `INTEGRATION_PATCH.md` to `desktop/odia-backend.spec`. The training submodule can be omitted (its imports are lazy); including only extraction + feedback keeps the binary small.

---

## File Inventory

### Added
```
odia_ai/                              (new package, ~30 files, 4,555 Python lines)
odia_ai_config.example.yaml           (at repo root)
INTEGRATION_PATCH.md                  (at repo root)
ODIA_AI_INSTALL_REPORT.md             (this file)
```

### Modified
```
src/oraculus_di_auditor/interface/api.py     (+15 lines inside create_app())
```

### Package-internal fixes (inside the new odia_ai/ tree)
```
odia_ai/server_routes/routes.py       (removed `from __future__ import annotations`)
odia_ai/cli/main.py                   (set-union dedupe for Windows case-insensitive glob)
```

### Removed
```
O.D.I.A._AI-0.1.0/odia_ai_build/{training,extraction,evaluation,backref,configs,scripts,cli,server_routes,continual,registry}/
O.D.I.A._AI-0.1.0/odia_ai_build/
O.D.I.A._AI-0.1.0/
```

### Scratch artifacts you can delete (left in place for audit)
```
_fake_mas_corpus/                     (test corpus — single .md file)
_fake_ds/                             (dataset builder output from the fake corpus)
_extract_payload.json                 (Phase 5 test payload)
_correction_payload.json              (Phase 5 test payload)
odia_ai_config.json                   (generated by init-config; safe to keep, delete, or commit)
data/corrections.db                   (contains the 1 test correction from Phase 5)
```

Nothing committed to git. All changes live in the working tree for you to review and stage as you see fit.
