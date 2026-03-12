# src/oraculus_di_auditor/rgk18/consensus_engine.py
"""Consensus engine for multi-source evidence aggregation."""
from __future__ import annotations

from .constants import DEFAULT_WEIGHTS
from .schemas import DecisionScore


class ConsensusEngine:
    """Aggregates evidence from multiple sources into a composite score."""

    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize consensus engine.

        Args:
            weights: Custom weights for evidence sources (uses defaults if None)
        """
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def aggregate(self, evidence: dict[str, float]) -> DecisionScore:
        """Aggregate evidence into a composite decision score.

        Args:
            evidence: Dictionary of evidence scores (0.0 - 1.0)
                Expected keys: scalar_harmonics, qdcl_probability,
                              temporal_stability, ethical_score,
                              self_healing_risk

        Returns:
            DecisionScore with composite score and components
        """
        # Normalize evidence values to 0.0 - 1.0 range
        normalized_evidence = {}
        for key, value in evidence.items():
            if value is None:
                # Missing evidence defaults to 0.5 (neutral)
                normalized_value = 0.5
            else:
                # Clamp to [0.0, 1.0]
                normalized_value = max(0.0, min(1.0, float(value)))
            normalized_evidence[key] = normalized_value

        # Calculate weighted sum
        composite_score = 0.0
        components = {}

        for source, weight in self.weights.items():
            source_score = normalized_evidence.get(source, 0.5)  # Default to neutral
            weighted_score = source_score * weight
            composite_score += weighted_score
            components[source] = source_score

        # Ensure score is in [0.0, 1.0]
        composite_score = max(0.0, min(1.0, composite_score))

        return DecisionScore(score=composite_score, components=components)

    def update_weights(self, new_weights: dict[str, float]) -> None:
        """Update evidence weights.

        Args:
            new_weights: New weights dictionary
        """
        self.weights = new_weights.copy()
        # Normalize to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
