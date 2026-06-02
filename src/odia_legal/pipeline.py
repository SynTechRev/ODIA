"""odia_legal pipeline — public API for running all legal detectors.

Single authoritative list of detector modules and a public runner function.
Consumed by:
  - audit_engine.py (persists findings to DB on every document ingest)
  - vector3.py  (temporal re-evaluation)
  - legal_routes.py  (on-demand API calls)
  - build_rag_index.py  (live enrichment during index build)
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical detector registry — single source of truth
# ---------------------------------------------------------------------------

LEGAL_DETECTOR_MODULES: list[str] = [
    "odia_legal.detectors.l1_statutory_applicability",
    "odia_legal.detectors.l2_procedural_compliance",
    "odia_legal.detectors.l3_exemption_misapplication",
    "odia_legal.detectors.l4_ministerial_duty",
    "odia_legal.detectors.l5_federal_grant_compliance",
    "odia_legal.detectors.l6_constitutional_implication",
    "odia_legal.detectors.l7_regulatory_authority",
    "odia_legal.detectors.l9_recodification",
    "odia_legal.detectors.l10_balancing_test",
]


def run_legal_detectors(
    doc: dict[str, Any],
    layers: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Run all (or a filtered subset of) odia_legal detectors on *doc*.

    Args:
        doc:    Document dict with at least a ``text`` / ``content`` field.
        layers: Optional list of layer IDs to run. If None, all detectors run.
                Example: ['l3_exemption_misapplication', 'l6_constitutional_implication']

    Returns:
        Merged list of finding dicts in the standard ODIA anomaly shape:
        {id, issue, severity, layer, details}

    Any detector that fails to import or raises is silently skipped so that
    one broken detector can never abort the full pipeline.
    """
    findings: list[dict[str, Any]] = []
    for mod_path in LEGAL_DETECTOR_MODULES:
        layer_id = mod_path.split(".")[-1]
        if layers is not None and layer_id not in layers:
            continue
        try:
            mod = importlib.import_module(mod_path)
            findings.extend(mod.detect(doc))
        except Exception:  # noqa: BLE001
            logger.debug(
                "odia_legal: detector %s skipped (import/runtime error)", layer_id
            )
    return findings
