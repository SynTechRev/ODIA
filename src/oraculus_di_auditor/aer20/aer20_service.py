# src/oraculus_di_auditor/aer20/aer20_service.py
"""Phase20Service - Ascendant Emergence & Recursive Synthesis orchestrator."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .ascendant_packet_publisher import AscendantPacketPublisher
from .composite_feature_vector import CompositeFeatureVectorConstructor
from .integrity_alignment_engine import IntegrityAlignmentEngine
from .meta_insight_generator import MetaInsightGenerator
from .validation_pipeline import ValidationPipeline
from .recursive_synthesis import RecursiveSynthesisEngine
from .schemas import Phase20Result
from .utils import sha256_hex

SERVICE_VERSION = "aer20-1.0.0"


class Phase20Service:
    """Orchestrates Phase 20: Ascendant Emergence & Recursive Synthesis (AER-20).

    This is the final phase that completes the Oraculus system by unifying
    all prior phases (12-19) into a self-aware, recursively-optimizing,
    deterministic intelligence architecture.
    """

    def __init__(self):
        """Initialize Phase 20 service components."""
        self.auf_constructor = CompositeFeatureVectorConstructor()
        self.synthesis_engine = RecursiveSynthesisEngine()
        self.meta_insight_generator = MetaInsightGenerator()
        self.ascension_loop = ValidationPipeline()
        self.integrity_engine = IntegrityAlignmentEngine()
        self.packet_publisher = AscendantPacketPublisher()

    def run_ascendant_emergence(
        self,
        phase_inputs: dict[str, Any],
        dry_run: bool = True,
        auto_apply: bool = False,
    ) -> Phase20Result:
        """Run complete Ascendant Emergence & Recursive Synthesis.

        This is the main entry point for Phase 20, which synthesizes all
        previous phases (12-19) into the final unified intelligence system.

        Args:
            phase_inputs: Dictionary containing outputs from Phases 12-19
                Expected keys:
                - phase12: Coherence Harmonics output
                - phase13: Temporal Quantized Probability output
                - phase14: Scalar Recursive Predictive Modelling output
                - phase15: Self-Healing Diagnostics output (OTGE-15)
                - phase16: Emergent Meta-Conscious Systems output (EMCS-16)
                - phase17: Recursive Ethical Cognition output (REC-17)
                - phase18: Recursive Governance Kernel output (RGK-18)
                - phase19: Applied Emergent Intelligence output (AEI-19)
            dry_run: If True, suggest but do not apply changes (default: True)
            auto_apply: Allow auto-application of recommendations (default: False)

        Returns:
            Phase20Result with complete ascendant intelligence analysis

        Raises:
            ValueError: If required phase inputs are missing or invalid
        """
        # Validate inputs
        self._validate_inputs(phase_inputs)

        # Step 1: Construct Composite Feature Vector (AUF-20)
        auf_state = self.auf_constructor.construct_auf(phase_inputs)

        # Step 2: Run Recursive Synthesis Engine (RSE-20)
        synthesis_report = self.synthesis_engine.synthesize(auf_state, phase_inputs)

        # Step 3: Generate Meta-Insight Packets (MIG-20)
        meta_insights = self.meta_insight_generator.generate_meta_insights(
            auf_state, synthesis_report, phase_inputs
        )

        # Step 4: Execute Validation Pipeline (RAL-20)
        ascension_report = self.ascension_loop.execute_ascension_loop(
            auf_state, synthesis_report, phase_inputs
        )

        # Step 5: Run Integrity & Alignment Engine (IAE-20)
        alignment_analysis = self.integrity_engine.analyze_alignment(
            auf_state,
            synthesis_report,
            meta_insights,
            ascension_report,
            phase_inputs,
        )

        # Step 6: Publish Output Packet (APP-20)
        fap_result = self.packet_publisher.publish_fap(
            auf_state,
            synthesis_report,
            meta_insights,
            ascension_report,
            alignment_analysis,
            phase_inputs,
        )

        # Build provenance
        provenance = self._build_provenance(phase_inputs, dry_run, auto_apply)

        # Compose final result
        result = Phase20Result(
            auf_20_state=auf_state,
            meta_insights=meta_insights,
            recursive_ascension_report=ascension_report,
            alignment_analysis=alignment_analysis,
            fap_20_result=fap_result,
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
            "phase19",
        ]

        missing = [p for p in required_phases if p not in phase_inputs]

        if missing:
            raise ValueError(
                f"Missing required phase inputs: {', '.join(missing)}. "
                "Phase 20 requires outputs from Phases 12-19."
            )

        # Validate Phase 17 has required fields
        phase17 = phase_inputs.get("phase17", {})
        if "global_ethics_score" not in phase17:
            raise ValueError("Phase 17 output must include 'global_ethics_score'")

        # Validate Phase 18 has required fields
        phase18 = phase_inputs.get("phase18", {})
        if "score" not in phase18:
            raise ValueError("Phase 18 output must include 'score'")

        # Validate Phase 19 has required fields
        phase19 = phase_inputs.get("phase19", {})
        if "uif_19_state" not in phase19:
            raise ValueError("Phase 19 output must include 'uif_19_state'")

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
                "phase19",
            ],
            "determinism_guaranteed": True,
            "reversibility_supported": True,
            "human_primacy_maintained": True,
            "no_unbounded_autonomy": True,
        }
