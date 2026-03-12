# src/oraculus_di_auditor/aei19/aei19_service.py
"""Phase19Service - Applied Emergent Intelligence orchestrator."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .alignment_engine import EthicalGovernanceAlignmentEngine
from .insight_synthesis import InsightSynthesisEngine
from .intelligence_publisher import AppliedIntelligencePublisher
from .scenario_simulator import DeterministicScenarioSimulator
from .schemas import Phase19Result
from .unified_intelligence_field import UnifiedIntelligenceFieldConstructor
from .utils import sha256_hex

SERVICE_VERSION = "aei19-1.0.0"


class Phase19Service:
    """Orchestrates Phase 19: Applied Emergent Intelligence (AEI-19)."""

    def __init__(self):
        """Initialize Phase 19 service components."""
        self.uif_constructor = UnifiedIntelligenceFieldConstructor()
        self.insight_engine = InsightSynthesisEngine()
        self.alignment_engine = EthicalGovernanceAlignmentEngine()
        self.scenario_simulator = DeterministicScenarioSimulator()
        self.intelligence_publisher = AppliedIntelligencePublisher()

    def run_applied_intelligence(
        self,
        phase_inputs: dict[str, Any],
        dry_run: bool = True,
        auto_apply: bool = False,
    ) -> Phase19Result:
        """Run complete Applied Emergent Intelligence analysis.

        This is the main entry point for Phase 19, which synthesizes all
        previous phases (12-18) into actionable, contextual intelligence.

        Args:
            phase_inputs: Dictionary containing outputs from Phases 12-18
                Expected keys:
                - phase12: Coherence Harmonics output
                - phase13: Temporal Quantized Probability output
                - phase14: Scalar Recursive Predictive Modelling output
                - phase15: Self-Healing Diagnostics output (OTGE-15)
                - phase16: Emergent Meta-Conscious Systems output (EMCS-16)
                - phase17: Recursive Ethical Cognition output (REC-17)
                - phase18: Recursive Governance Kernel output (RGK-18)
            dry_run: If True, suggest but do not apply changes (default: True)
            auto_apply: Allow auto-application of recommendations (default: False)

        Returns:
            Phase19Result with complete applied intelligence analysis

        Raises:
            ValueError: If required phase inputs are missing or invalid
        """
        # Validate inputs
        self._validate_inputs(phase_inputs)

        # Step 1: Construct Unified Intelligence Field (UIF-19)
        uif_state = self.uif_constructor.construct_uif(phase_inputs)

        # Step 2: Run Insight Synthesis (ISE-19)
        insights = self.insight_engine.synthesize_insights(uif_state, phase_inputs)

        # Step 3: Check Ethical-Governance Alignment (EGA-19)
        alignment_report = self.alignment_engine.check_alignment(phase_inputs)

        # Step 4: Simulate Deterministic Scenario (DSS-19)
        scenario_map = self.scenario_simulator.simulate_scenario(
            uif_state, phase_inputs
        )

        # Step 5: Publish Applied Intelligence (AIP-19)
        aei19_result = self.intelligence_publisher.publish_intelligence(
            uif_state,
            insights,
            alignment_report,
            scenario_map,
            phase_inputs,
        )

        # Build provenance
        provenance = self._build_provenance(phase_inputs, dry_run, auto_apply)

        # Compose final result
        result = Phase19Result(
            uif_19_state=uif_state,
            insight_packets=insights,
            alignment_report=alignment_report,
            scenario_map=scenario_map,
            aei19_result=aei19_result,
            provenance=provenance,
        )

        return result

    def _validate_inputs(self, phase_inputs: dict[str, Any]) -> None:
        """Validate that all required phase inputs are present.

        Args:
            phase_inputs: Phase inputs to validate

        Raises:
            ValueError: If required inputs are missing
        """
        required_phases = [
            "phase12",
            "phase13",
            "phase14",
            "phase15",
            "phase16",
            "phase17",
            "phase18",
        ]

        missing = [p for p in required_phases if p not in phase_inputs]

        if missing:
            raise ValueError(
                f"Missing required phase inputs: {', '.join(missing)}. "
                "Phase 19 requires outputs from Phases 12-18."
            )

        # Validate Phase 17 has required fields
        phase17 = phase_inputs.get("phase17", {})
        if "global_ethics_score" not in phase17:
            raise ValueError("Phase 17 output must include 'global_ethics_score'")

        # Validate Phase 18 has required fields
        phase18 = phase_inputs.get("phase18", {})
        if "score" not in phase18:
            raise ValueError("Phase 18 output must include 'score'")

    def _build_provenance(
        self,
        phase_inputs: dict[str, Any],
        dry_run: bool,
        auto_apply: bool,
    ) -> dict[str, Any]:
        """Build provenance metadata for auditing.

        Args:
            phase_inputs: Original phase inputs
            dry_run: Dry run flag
            auto_apply: Auto-apply flag

        Returns:
            Provenance dictionary
        """
        input_hash = sha256_hex(phase_inputs)

        return {
            "input_hash": input_hash,
            "service_version": SERVICE_VERSION,
            "timestamp": datetime.now(UTC),
            "dry_run": dry_run,
            "auto_apply": auto_apply,
            "phases_integrated": [
                "phase12",
                "phase13",
                "phase14",
                "phase15",
                "phase16",
                "phase17",
                "phase18",
            ],
            "determinism_guaranteed": True,
            "reversibility_supported": True,
        }
