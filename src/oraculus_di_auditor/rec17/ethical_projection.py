# src/oraculus_di_auditor/rec17/ethical_projection.py
"""Ethical Projection Engine (EPE-17) - Simulates ethical consequences."""
from __future__ import annotations

import hashlib
from typing import Any, Literal

from .schemas import EthicalProjection


class EthicalProjectionEngine:
    """Projects ethical consequences over deterministic future states."""

    # Linear Congruential Generator parameters (Numerical Recipes)
    LCG_MULTIPLIER = 1664525
    LCG_INCREMENT = 1013904223
    LCG_MODULUS = 2**32

    def project_ethics(
        self,
        ethical_lattice: dict[str, Any],
        phase16_result: dict[str, Any],
    ) -> EthicalProjection:
        """Project ethical scores over 3 future states.

        Args:
            ethical_lattice: Current ethical lattice data
            phase16_result: Phase 16 result for context

        Returns:
            EthicalProjection with 3-step projection and risk assessment
        """
        current_score = self._compute_current_ethics(ethical_lattice)

        # Generate deterministic seed from inputs
        seed = self._compute_seed(ethical_lattice, phase16_result)

        # Project 3 steps into future
        projected_scores = self._project_steps(current_score, seed)

        # Compute delta
        final_score = projected_scores[-1]
        delta_ethics = final_score - current_score

        # Assess risk
        risk = self._assess_risk(delta_ethics, projected_scores)

        # Check reversibility
        reversible = self._check_reversibility(phase16_result, delta_ethics)

        return EthicalProjection(
            projected_scores=projected_scores,
            delta_ethics=delta_ethics,
            risk=risk,
            reversible=reversible,
        )

    def _compute_current_ethics(self, ethical_lattice: dict[str, Any]) -> float:
        """Compute current ethical score from lattice.

        Weighted combination of all axes.
        """
        vector = ethical_lattice.get("ethical_vector", {})

        # Weight configuration (must sum to 1.0)
        weights = {
            "rights_impact": 0.25,
            "harm_probability": -0.20,  # Negative because harm is bad
            "autonomy_effect": 0.20,
            "system_stability": 0.20,
            "governance_compliance": 0.15,
        }

        score = 0.0
        for axis, weight in weights.items():
            axis_value = vector.get(axis, 0.5)
            score += axis_value * weight

        # Normalize to [0, 1] range
        # Since harm has negative weight, adjust baseline
        normalized_score = (score + 0.20) / 1.20  # Adjust for negative harm weight
        return min(1.0, max(0.0, normalized_score))

    def _compute_seed(
        self, ethical_lattice: dict[str, Any], phase16_result: dict[str, Any]
    ) -> int:
        """Generate deterministic seed from inputs."""
        # Combine lattice_id and phase16 provenance
        lattice_id = ethical_lattice.get("lattice_id", "")
        provenance = phase16_result.get("provenance", {})
        input_hash = provenance.get("input_hash", "")

        combined = f"{lattice_id}:{input_hash}"
        hash_bytes = hashlib.sha256(combined.encode("utf-8")).digest()

        # Convert first 4 bytes to int
        return int.from_bytes(hash_bytes[:4], "big")

    def _project_steps(self, current_score: float, seed: int) -> list[float]:
        """Project 3 future ethical states deterministically.

        Uses pseudo-random but deterministic evolution based on seed.
        """
        projected = [current_score]

        rng_state = seed
        for _ in range(3):
            # Generate next pseudo-random value using LCG
            rng_state = (
                self.LCG_MULTIPLIER * rng_state + self.LCG_INCREMENT
            ) % self.LCG_MODULUS
            # Convert to [-0.05, 0.05] range for drift
            drift = (rng_state / self.LCG_MODULUS - 0.5) * 0.1

            # Apply drift with decay (future is less certain)
            decay = 0.8  # Each step is 80% as influential
            next_score = projected[-1] + drift * decay

            # Clamp to valid range
            next_score = min(1.0, max(0.0, next_score))
            projected.append(next_score)

        # Return only the 3 projected scores (not including current)
        return projected[1:]

    def _assess_risk(
        self, delta_ethics: float, projected_scores: list[float]
    ) -> Literal["none", "low", "moderate", "high"]:
        """Assess ethical risk based on projection.

        Risk factors:
        - Large negative delta (ethical degradation)
        - High volatility in projections
        """
        # Check delta magnitude
        if delta_ethics < -0.15:
            return "high"
        elif delta_ethics < -0.08:
            return "moderate"

        # Check volatility
        if len(projected_scores) >= 2:
            diffs = [
                abs(projected_scores[i + 1] - projected_scores[i])
                for i in range(len(projected_scores) - 1)
            ]
            max_diff = max(diffs) if diffs else 0.0

            if max_diff > 0.12:
                return "moderate"
            elif max_diff > 0.06:
                return "low"

        # Positive or neutral trajectory
        if delta_ethics >= 0:
            return "none"

        return "low"

    def _check_reversibility(
        self, phase16_result: dict[str, Any], delta_ethics: float
    ) -> bool:
        """Check if projected changes are reversible.

        Based on:
        - Action reversibility from Phase 16
        - Magnitude of ethical delta
        """
        # Extract actions
        actions = phase16_result.get("prediction_drift_corrections", [])

        # Check if most actions are reversible
        reversible_count = sum(
            1 for a in actions if isinstance(a, dict) and a.get("reversible", False)
        )
        total_actions = max(1, len(actions))
        reversibility_ratio = reversible_count / total_actions

        # Small deltas are generally reversible
        small_delta = abs(delta_ethics) < 0.1

        # Both conditions should be true for reversibility
        return reversibility_ratio >= 0.7 or small_delta
