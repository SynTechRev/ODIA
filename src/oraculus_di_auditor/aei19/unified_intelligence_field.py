# src/oraculus_di_auditor/aei19/unified_intelligence_field.py
"""UIF-19: Unified Intelligence Field Constructor.

Combines outputs from Phases 12-18 into a single deterministic 142-dimensional
intelligence tensor with ethical warp and governance weighting.
"""
from __future__ import annotations

from typing import Any

from .schemas import UIFState
from .utils import DeterministicRNG, seed_from_input, sha256_hex


class UnifiedIntelligenceFieldConstructor:
    """Constructs the Unified Intelligence Field from multi-phase inputs."""

    def __init__(self):
        """Initialize UIF-19 constructor."""
        self.dimension = 142

    def construct_uif(self, phase_inputs: dict[str, Any]) -> UIFState:
        """Construct UIF-19 state from Phase 12-18 outputs.

        The 142-dimensional vector is organized as:
        - Dimensions 0-19: Phase 12 (Scalar Convergence & Coherence)
        - Dimensions 20-39: Phase 13 (Temporal Quantized Probability)
        - Dimensions 40-59: Phase 14 (Scalar Recursive Predictive Modelling)
        - Dimensions 60-79: Phase 15 (Temporal Governance - OTGE-15)
        - Dimensions 80-99: Phase 16 (Meta-Conscious Systems - EMCS-16)
        - Dimensions 100-119: Phase 17 (Recursive Ethical Cognition - REC-17)
        - Dimensions 120-139: Phase 18 (Recursive Governance Kernel - RGK-18)
        - Dimensions 140-141: Cross-phase harmonization metrics

        Args:
            phase_inputs: Dictionary containing outputs from Phases 12-18

        Returns:
            UIFState with 142-dimensional intelligence tensor
        """
        # Generate deterministic seed from inputs
        seed = seed_from_input(phase_inputs)
        rng = DeterministicRNG(seed)

        # Initialize field vector
        field_vector = {}

        # Extract phase contributions
        phase_contributions = {}

        # Phase 12: Scalar Convergence (dimensions 0-19)
        phase12 = phase_inputs.get("phase12", {})
        coherence_score = phase12.get("coherence_score", 0.5)
        for i in range(20):
            # Distribute coherence with deterministic variation
            variation = rng.next_float() * 0.2 - 0.1  # ±0.1
            field_vector[f"dim_{i}"] = max(0.0, min(1.0, coherence_score + variation))
        phase_contributions["phase12"] = {
            "coherence_score": coherence_score,
            "dimension_range": "0-19",
        }

        # Phase 13: Temporal Quantized Probability (dimensions 20-39)
        phase13 = phase_inputs.get("phase13", {})
        probability = phase13.get("probability", 0.5)
        for i in range(20, 40):
            variation = rng.next_float() * 0.2 - 0.1
            field_vector[f"dim_{i}"] = max(0.0, min(1.0, probability + variation))
        phase_contributions["phase13"] = {
            "probability": probability,
            "dimension_range": "20-39",
        }

        # Phase 14: Scalar Recursive Predictive (dimensions 40-59)
        phase14 = phase_inputs.get("phase14", {})
        prediction_score = phase14.get("prediction_score", 0.5)
        for i in range(40, 60):
            variation = rng.next_float() * 0.2 - 0.1
            field_vector[f"dim_{i}"] = max(0.0, min(1.0, prediction_score + variation))
        phase_contributions["phase14"] = {
            "prediction_score": prediction_score,
            "dimension_range": "40-59",
        }

        # Phase 15: Temporal Governance (dimensions 60-79)
        phase15 = phase_inputs.get("phase15", {})
        stability_score = phase15.get("stability_score", 0.5)
        for i in range(60, 80):
            variation = rng.next_float() * 0.2 - 0.1
            field_vector[f"dim_{i}"] = max(0.0, min(1.0, stability_score + variation))
        phase_contributions["phase15"] = {
            "stability_score": stability_score,
            "dimension_range": "60-79",
        }

        # Phase 16: Meta-Conscious Systems (dimensions 80-99)
        phase16 = phase_inputs.get("phase16", {})
        recursive_integrity = phase16.get("recursive_integrity_score", 0.5)
        for i in range(80, 100):
            variation = rng.next_float() * 0.2 - 0.1
            field_vector[f"dim_{i}"] = max(
                0.0, min(1.0, recursive_integrity + variation)
            )
        phase_contributions["phase16"] = {
            "recursive_integrity_score": recursive_integrity,
            "dimension_range": "80-99",
        }

        # Phase 17: Recursive Ethical Cognition (dimensions 100-119)
        phase17 = phase_inputs.get("phase17", {})
        global_ethics = phase17.get("global_ethics_score", 0.5)
        for i in range(100, 120):
            variation = rng.next_float() * 0.2 - 0.1
            field_vector[f"dim_{i}"] = max(0.0, min(1.0, global_ethics + variation))
        phase_contributions["phase17"] = {
            "global_ethics_score": global_ethics,
            "dimension_range": "100-119",
        }

        # Phase 18: Recursive Governance Kernel (dimensions 120-139)
        phase18 = phase_inputs.get("phase18", {})
        governance_score = phase18.get("score", 0.5)
        for i in range(120, 140):
            variation = rng.next_float() * 0.2 - 0.1
            field_vector[f"dim_{i}"] = max(0.0, min(1.0, governance_score + variation))
        phase_contributions["phase18"] = {
            "governance_score": governance_score,
            "dimension_range": "120-139",
        }

        # Cross-phase harmonization (dimensions 140-141)
        # Dim 140: Overall system coherence
        all_scores = [
            coherence_score,
            probability,
            prediction_score,
            stability_score,
            recursive_integrity,
            global_ethics,
            governance_score,
        ]
        field_vector["dim_140"] = sum(all_scores) / len(all_scores)

        # Dim 141: Variance measure (system alignment)
        mean_score = field_vector["dim_140"]
        variance = sum((s - mean_score) ** 2 for s in all_scores) / len(all_scores)
        field_vector["dim_141"] = max(0.0, 1.0 - variance)  # Higher = more aligned

        # Calculate influence factors
        harmonization_pressure = recursive_integrity  # From EMCS-16
        ethical_warp = global_ethics  # From REC-17
        governance_weight = governance_score  # From RGK-18

        # Generate UIF ID
        uif_id = sha256_hex(
            {
                "field_vector": field_vector,
                "phase_contributions": phase_contributions,
                "seed": seed,
            }
        )

        return UIFState(
            uif_id=uif_id,
            dimension=self.dimension,
            field_vector=field_vector,
            phase_contributions=phase_contributions,
            harmonization_pressure=harmonization_pressure,
            ethical_warp=ethical_warp,
            governance_weight=governance_weight,
        )
