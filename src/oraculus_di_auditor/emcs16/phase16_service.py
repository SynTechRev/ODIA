# src/oraculus_di_auditor/emcs16/phase16_service.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .harmonization import HarmonizationCore
from .meta_audit import MetaAudit
from .meta_supervisor import MetaSupervisor, _sha256_hex
from .self_modeling import RecursiveSelfModeling

SERVICE_VERSION = "emcs16-0.1.0"


class Phase16Service:
    """Orchestrates Phase 16 run cycle deterministically."""

    def __init__(self):
        self.supervisor = MetaSupervisor()
        self.self_modeler = RecursiveSelfModeling()
        self.harmonizer = HarmonizationCore()
        self.auditor = MetaAudit()

    def _compute_provenance(
        self, req: dict[str, Any], input_hash: str, seed: int
    ) -> dict[str, Any]:
        return {
            "input_hash": input_hash,
            "service_version": SERVICE_VERSION,
            "deterministic_seed": seed,
            "timestamp": datetime.now(UTC),
        }

    def run_cycle(self, raw_request: dict[str, Any]) -> dict[str, Any]:
        """Main entry; accepts raw dict for easy testing/fixtures (then validate)."""
        # Validate / compute input hash
        input_hash = _sha256_hex(raw_request)
        # Supervisor checks
        sup_report = self.supervisor.run_checks(raw_request)

        # Self-model & projection
        sm = self.self_modeler.build_and_project(
            raw_request.get("system_state", {}), input_hash
        )

        # Harmonize
        harmonics = self.harmonizer.fuse(
            raw_request.get("phase12_harmonics", {}),
            raw_request.get("phase13_probabilities", {}),
            raw_request.get("phase14_outputs", {}).get("cri_rankings", {}),
        )
        patterns = self.harmonizer.emergent_patterns(harmonics)

        # Audit
        audit = self.auditor.generate_report(sup_report, harmonics)
        actions = audit["actions"]

        # Compose result (conform to Phase16Result schema)
        result = {
            "meta_state_vector": sm["meta_state"],
            "recursive_integrity_score": sup_report.get("integrity_score", 0.0),
            "emergent_pattern_index": patterns,
            "prediction_drift_corrections": actions,
            "self_reflection_report": audit,
            "meta_harmonic_field": harmonics,
            "provenance": self._compute_provenance(
                raw_request, input_hash, sm.get("seed", 0)
            ),
            "timestamp": datetime.now(UTC),
        }
        # Note: we intentionally return raw dict (tests will validate schema)
        return result
