INTEGRATION PATCH — Adding odia_ai routes to the existing FastAPI backend
==========================================================================

The odia_ai subsystem is designed to attach to the existing
oraculus_di_auditor.interface.api create_app() factory with a single
import and one function call.

Target file:  src/oraculus_di_auditor/interface/api.py
Description:  Wire in the /ai/* routes from the odia_ai package,
              guarded so that the backend still starts if odia_ai
              is not installed.

--------------------------------------------------------------------------
PATCH (apply inside create_app())
--------------------------------------------------------------------------

Inside the create_app() factory, AFTER all existing routes have been
registered and BEFORE return app, add the following block:

    # ------------------------------------------------------------------
    # ODIA AI subsystem integration (odia_ai package)
    # ------------------------------------------------------------------
    # The odia_ai package provides:
    #   POST /ai/extract              — Layer 2 NER + relational extraction
    #   POST /ai/corrections          — Submit user correction to extraction
    #   GET  /ai/corrections/stats    — Correction-store summary
    #   GET  /ai/registry/versions    — List registered model versions
    #   GET  /ai/registry/versions/{id}
    #   GET  /ai/status               — System status + retrain-trigger state
    #   GET  /ai/health
    #
    # If odia_ai is not installed (e.g. minimal deployment without the
    # fine-tuning subsystem), the import fails silently and the backend
    # continues to run with its core detectors and RAG endpoints only.
    try:
        from odia_ai.server_routes import include_ai_routes

        # Config path is optional; when None, defaults are used.
        # Override via environment variable ODIA_AI_CONFIG if desired.
        import os
        ai_config_path = os.environ.get("ODIA_AI_CONFIG")
        include_ai_routes(app, config_path=ai_config_path)
        logger.info("odia_ai routes registered under /ai/*")
    except ImportError:
        logger.info("odia_ai not installed; /ai/* routes unavailable")
    except Exception as e:
        logger.warning("odia_ai route registration failed: %s", e)


--------------------------------------------------------------------------
MINIMAL PATCH (if you prefer 3 lines)
--------------------------------------------------------------------------

If you want the smallest possible diff, this 3-line form works:

    from odia_ai.server_routes import include_ai_routes
    include_ai_routes(app)


--------------------------------------------------------------------------
VERIFICATION
--------------------------------------------------------------------------

After patching, start the backend:

    uvicorn oraculus_di_auditor.interface.api:create_app --factory --reload

Then hit the new endpoints:

    curl http://localhost:8000/ai/health
    curl http://localhost:8000/ai/status
    curl -X POST http://localhost:8000/ai/extract \
         -H 'Content-Type: application/json' \
         -d '{"text":"Resolution 2024-15 authorized $49,700 Flock Safety sole-source."}'


--------------------------------------------------------------------------
DESKTOP APP CONSIDERATIONS
--------------------------------------------------------------------------

The existing Electron desktop app bundles the backend via PyInstaller
(desktop/odia-backend.spec). To include odia_ai in the bundled binary,
add to the PyInstaller spec's hiddenimports list:

    hiddenimports = [
        # ... existing imports ...
        'odia_ai',
        'odia_ai.backref',
        'odia_ai.backref.extractor',
        'odia_ai.extraction',
        'odia_ai.extraction.extractor',
        'odia_ai.continual',
        'odia_ai.continual.feedback_store',
        'odia_ai.registry',
        'odia_ai.registry.registry',
        'odia_ai.server_routes',
        'odia_ai.server_routes.routes',
        'odia_ai.configs',
        'odia_ai.configs.config',
    ]

The training submodule (odia_ai.training.lora_runner) deliberately
imports torch/transformers/peft LAZILY inside functions, so bundling
the training stack into the desktop binary is OPTIONAL. Desktop users
who only need extraction and feedback (no fine-tuning) can omit it
and the binary stays small.


--------------------------------------------------------------------------
FRONTEND WIRING (optional)
--------------------------------------------------------------------------

The Next.js frontend in frontend/ can now call the new routes. A
recommended minimal UI addition: a "Correct Extraction" button on
each extraction result that opens a dialog to submit a correction
via POST /ai/corrections.

Example TypeScript client usage:

    async function submitCorrection(correction: {
      input_text: string;
      field_name: string;
      correction_type: "addition" | "deletion" | "modification";
      original_value: string;
      corrected_value: string;
      model_version_id: string;
      jurisdiction?: string;
      reviewer_id?: string;
      reviewer_note?: string;
    }) {
      const res = await fetch("/ai/corrections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(correction),
      });
      return res.json();
    }

