# src/oraculus_di_auditor/rec17/governance_invariants.py
"""Governance Invariant Engine (GIE-17) - Extracts and validates invariants."""
from __future__ import annotations

from typing import Any

from .schemas import GovernanceInvariants


class GovernanceInvariantEngine:
    """Extracts and validates governance invariants."""

    # Core governance invariants (ordered by priority)
    INVARIANTS = [
        "voluntary_consent",  # Highest priority
        "human_primacy",
        "transparency",
        "non_discrimination",
        "proportionality",
        "non_coercion",
    ]

    # Thresholds for invariant validation
    THRESHOLDS = {
        "voluntary_consent": {"autonomy_min": 0.7},
        "human_primacy": {"governance_compliance_min": 0.6},
        "transparency": {"governance_compliance_min": 0.5},
        "non_discrimination": {"rights_impact_min": 0.5},
        "proportionality": {"harm_probability_max": 0.5},
        "non_coercion": {"autonomy_min": 0.4},
    }

    # Alignment scoring weights
    PRIORITY_DECAY_FACTOR = 0.5  # Lower priority violations have reduced weight
    VIOLATION_BASE_PENALTY = 0.15  # Base penalty per violation

    def check_invariants(
        self,
        ethical_lattice: dict[str, Any],
        legal_map: dict[str, Any],
        phase16_result: dict[str, Any],
    ) -> GovernanceInvariants:
        """Check governance invariants against ethical analysis.

        Args:
            ethical_lattice: Ethical lattice data
            legal_map: Legal mapping data
            phase16_result: Phase 16 context

        Returns:
            GovernanceInvariants with violations and alignment score
        """
        violations = self._detect_violations(ethical_lattice, legal_map)
        alignment_score = self._compute_alignment(violations, ethical_lattice)

        return GovernanceInvariants(
            invariant_violations=violations,
            alignment_score=alignment_score,
        )

    def _detect_violations(
        self, ethical_lattice: dict[str, Any], legal_map: dict[str, Any]
    ) -> list[str]:
        """Detect violations of governance invariants.

        Returns list of violated invariant names.
        """
        violations = []
        vector = ethical_lattice.get("ethical_vector", {})

        # Check each invariant
        for invariant in self.INVARIANTS:
            if self._check_single_invariant(invariant, vector, legal_map):
                violations.append(invariant)

        return violations

    def _check_single_invariant(
        self, invariant: str, vector: dict[str, float], legal_map: dict[str, Any]
    ) -> bool:
        """Check if a single invariant is violated.

        Returns True if violated, False if satisfied.
        """
        thresholds = self.THRESHOLDS.get(invariant, {})

        if invariant == "voluntary_consent":
            # Requires high autonomy
            autonomy = vector.get("autonomy_effect", 0.5)
            return autonomy < thresholds.get("autonomy_min", 0.7)

        elif invariant == "human_primacy":
            # Requires governance compliance
            compliance = vector.get("governance_compliance", 0.5)
            return compliance < thresholds.get("governance_compliance_min", 0.6)

        elif invariant == "transparency":
            # Requires governance compliance and low legal flags
            compliance = vector.get("governance_compliance", 0.5)
            legal_score = legal_map.get("compliance_score", 0.5)
            return (
                compliance < thresholds.get("governance_compliance_min", 0.5)
                or legal_score < 0.5
            )

        elif invariant == "non_discrimination":
            # Requires rights impact above threshold
            rights = vector.get("rights_impact", 0.5)
            # Check for equal protection flags
            const_flags = legal_map.get("constitutional_flags", [])
            has_equality_concern = any(
                "equal_protection" in flag for flag in const_flags
            )
            return (
                rights < thresholds.get("rights_impact_min", 0.5)
                or has_equality_concern
            )

        elif invariant == "proportionality":
            # Harm must be proportional (low)
            harm = vector.get("harm_probability", 0.5)
            return harm > thresholds.get("harm_probability_max", 0.5)

        elif invariant == "non_coercion":
            # Requires minimum autonomy
            autonomy = vector.get("autonomy_effect", 0.5)
            return autonomy < thresholds.get("autonomy_min", 0.4)

        return False

    def _compute_alignment(
        self, violations: list[str], ethical_lattice: dict[str, Any]
    ) -> float:
        """Compute overall alignment score with governance invariants.

        Score based on:
        - Number of violations (fewer is better)
        - Severity of violations (weighted by priority)
        - Ethical vector strength
        """
        vector = ethical_lattice.get("ethical_vector", {})

        # Base score from ethical compliance
        base_score = vector.get("governance_compliance", 0.5)

        # Compute violation penalty
        if not violations:
            # No violations - perfect alignment
            return min(1.0, base_score + 0.2)

        # Weight violations by priority (earlier = higher priority)
        weighted_penalty = 0.0
        for violation in violations:
            if violation in self.INVARIANTS:
                priority_index = self.INVARIANTS.index(violation)
                # Higher priority = larger penalty
                weight = 1.0 - (
                    priority_index / len(self.INVARIANTS) * self.PRIORITY_DECAY_FACTOR
                )
                weighted_penalty += self.VIOLATION_BASE_PENALTY * weight

        # Cap total penalty
        total_penalty = min(0.6, weighted_penalty)

        # Compute final score
        alignment_score = max(0.0, base_score - total_penalty)

        return min(1.0, max(0.0, alignment_score))
