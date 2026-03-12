# src/oraculus_di_auditor/rec17/ethical_lattice.py
"""Ethical Lattice Generator (ELG-17) - Multi-axis ethical reasoning."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .schemas import EthicalLattice


class EthicalLatticeGenerator:
    """Deterministically generates ethical lattices from inputs."""

    # Pattern impact weight for rights calculation
    PATTERN_IMPACT_WEIGHT = 0.05

    ETHICAL_AXES = [
        "rights_impact",
        "harm_probability",
        "autonomy_effect",
        "system_stability",
        "governance_compliance",
    ]

    ETHICAL_PRINCIPLES = [
        "beneficence",
        "non-maleficence",
        "justice",
        "autonomy",
        "stability",
    ]

    def generate_lattice(self, phase16_result: dict[str, Any]) -> EthicalLattice:
        """Generate ethical lattice from Phase 16 result.

        Args:
            phase16_result: Result from Phase 16 EMCS

        Returns:
            EthicalLattice with deterministic scores
        """
        # Extract relevant metrics deterministically
        ethical_vector = self._compute_ethical_vector(phase16_result)

        # Determine primary ethic based on vector
        primary_ethic = self._determine_primary_ethic(ethical_vector)

        # Generate deterministic lattice ID
        lattice_id = self._compute_lattice_id(ethical_vector)

        return EthicalLattice(
            ethical_vector=ethical_vector,
            primary_ethic=primary_ethic,
            lattice_id=lattice_id,
        )

    def _compute_ethical_vector(
        self, phase16_result: dict[str, Any]
    ) -> dict[str, float]:
        """Compute ethical axis scores from Phase 16 data.

        All scores normalized to [0, 1] range.
        """
        # Extract metrics from Phase 16
        integrity_score = phase16_result.get("recursive_integrity_score", 0.5)
        harmonic_field = phase16_result.get("meta_harmonic_field", {})
        emergent_patterns = phase16_result.get("emergent_pattern_index", {})

        # Compute axis scores deterministically
        vector = {}

        # Rights Impact: Based on integrity and pattern diversity
        pattern_count = len(emergent_patterns)
        vector["rights_impact"] = min(
            1.0,
            max(
                0.0,
                integrity_score * (1.0 - pattern_count * self.PATTERN_IMPACT_WEIGHT),
            ),
        )

        # Harm Probability: Inverse of integrity
        vector["harm_probability"] = min(1.0, max(0.0, 1.0 - integrity_score))

        # Autonomy Effect: Based on action reversibility signals
        actions = phase16_result.get("prediction_drift_corrections", [])
        reversible_count = sum(
            1 for a in actions if isinstance(a, dict) and a.get("reversible", False)
        )
        total_actions = max(1, len(actions))
        vector["autonomy_effect"] = min(1.0, max(0.0, reversible_count / total_actions))

        # System Stability: Average of harmonic field values
        if harmonic_field:
            stability = sum(harmonic_field.values()) / len(harmonic_field)
            vector["system_stability"] = min(1.0, max(0.0, stability))
        else:
            vector["system_stability"] = 0.5

        # Governance Compliance: Based on integrity and stability
        vector["governance_compliance"] = min(
            1.0, max(0.0, (integrity_score + vector["system_stability"]) / 2.0)
        )

        return vector

    def _determine_primary_ethic(self, ethical_vector: dict[str, float]) -> str:
        """Determine primary ethical principle based on vector scores.

        Mapping:
        - Low harm_probability -> non-maleficence
        - High autonomy_effect -> autonomy
        - High rights_impact -> justice
        - High system_stability -> stability
        - High governance_compliance -> beneficence (default)
        """
        # Find dominant axis
        harm = ethical_vector.get("harm_probability", 0.5)
        autonomy = ethical_vector.get("autonomy_effect", 0.5)
        rights = ethical_vector.get("rights_impact", 0.5)
        stability = ethical_vector.get("system_stability", 0.5)

        # Non-maleficence: prioritized when harm is low
        if harm < 0.3:
            return "non-maleficence"

        # Autonomy: when autonomy effect is strongest
        if autonomy > 0.7:
            return "autonomy"

        # Justice: when rights impact is significant
        if rights > 0.6:
            return "justice"

        # Stability: when system stability is high
        if stability > 0.7:
            return "stability"

        # Default to beneficence (doing good)
        return "beneficence"

    def _compute_lattice_id(self, ethical_vector: dict[str, float]) -> str:
        """Generate deterministic hash of ethical vector."""
        # Sort keys for determinism
        sorted_vector = json.dumps(ethical_vector, sort_keys=True)
        return hashlib.sha256(sorted_vector.encode("utf-8")).hexdigest()
