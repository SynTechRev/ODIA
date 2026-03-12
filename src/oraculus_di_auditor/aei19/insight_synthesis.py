# src/oraculus_di_auditor/aei19/insight_synthesis.py
"""ISE-19: Insight Synthesis Engine.

Produces analytic, contextual, emergent, and counterfactual insights based on
deterministic pattern extraction from the Unified Intelligence Field.
"""
from __future__ import annotations

from typing import Any

from .schemas import InsightPacket, UIFState
from .utils import sha256_hex


class InsightSynthesisEngine:
    """Generates applied insights from UIF-19 state."""

    def __init__(self):
        """Initialize ISE-19 engine."""
        pass

    def synthesize_insights(
        self,
        uif_state: UIFState,
        phase_inputs: dict[str, Any],
    ) -> list[InsightPacket]:
        """Generate comprehensive insights from UIF state.

        Args:
            uif_state: Unified Intelligence Field state
            phase_inputs: Original phase inputs for context

        Returns:
            List of InsightPacket objects
        """
        insights = []

        # Generate analytic insights
        insights.extend(self._generate_analytic_insights(uif_state, phase_inputs))

        # Generate contextual insights
        insights.extend(self._generate_contextual_insights(uif_state, phase_inputs))

        # Generate emergent insights
        insights.extend(self._generate_emergent_insights(uif_state, phase_inputs))

        # Generate counterfactual insights
        insights.extend(self._generate_counterfactual_insights(uif_state, phase_inputs))

        return insights

    def _generate_analytic_insights(
        self,
        uif_state: UIFState,
        phase_inputs: dict[str, Any],
    ) -> list[InsightPacket]:
        """Generate deductive and inductive analytic insights."""
        insights = []

        # Analyze system coherence
        coherence = uif_state.field_vector.get("dim_140", 0.5)
        alignment = uif_state.field_vector.get("dim_141", 0.5)

        if coherence > 0.75 and alignment > 0.75:
            insight_id = sha256_hex(
                {"type": "analytic_coherence_high", "coherence": coherence}
            )
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="analytic",
                    content=(
                        f"System demonstrates high coherence ({coherence:.3f}) "
                        f"and alignment ({alignment:.3f}). All phases are "
                        "operating in harmony with strong cross-phase consistency."
                    ),
                    confidence=min(coherence, alignment),
                    source_phases=[
                        "phase12",
                        "phase13",
                        "phase14",
                        "phase15",
                        "phase16",
                        "phase17",
                        "phase18",
                    ],
                    structured_data={
                        "coherence_score": coherence,
                        "alignment_score": alignment,
                        "assessment": "optimal",
                    },
                )
            )
        elif coherence < 0.5 or alignment < 0.5:
            insight_id = sha256_hex(
                {"type": "analytic_coherence_low", "coherence": coherence}
            )
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="analytic",
                    content=(
                        f"System coherence ({coherence:.3f}) or alignment "
                        f"({alignment:.3f}) is below optimal threshold. "
                        "Review phase integration and resolve conflicts."
                    ),
                    confidence=0.8,
                    source_phases=["phase12", "phase13", "phase14", "phase15"],
                    structured_data={
                        "coherence_score": coherence,
                        "alignment_score": alignment,
                        "assessment": "requires_attention",
                    },
                )
            )

        # Analyze ethical-governance balance
        ethical_score = uif_state.ethical_warp
        governance_score = uif_state.governance_weight

        if abs(ethical_score - governance_score) < 0.15:
            insight_id = sha256_hex(
                {"type": "analytic_balance", "ethics": ethical_score}
            )
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="analytic",
                    content=(
                        f"Ethical alignment ({ethical_score:.3f}) and governance "
                        f"compliance ({governance_score:.3f}) are well-balanced. "
                        "System maintains strong normative consistency."
                    ),
                    confidence=0.85,
                    source_phases=["phase17", "phase18"],
                    structured_data={
                        "ethical_score": ethical_score,
                        "governance_score": governance_score,
                        "balance": "optimal",
                    },
                )
            )

        return insights

    def _generate_contextual_insights(
        self,
        uif_state: UIFState,
        phase_inputs: dict[str, Any],
    ) -> list[InsightPacket]:
        """Generate situational and context-aware insights."""
        insights = []

        # Analyze temporal context
        phase15 = phase_inputs.get("phase15", {})
        stability = phase15.get("stability_score", 0.5)

        if stability > 0.7:
            insight_id = sha256_hex(
                {"type": "contextual_stability", "value": stability}
            )
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="contextual",
                    content=(
                        f"Temporal stability is strong ({stability:.3f}). "
                        "Current context supports confident forward planning "
                        "with low temporal drift risk."
                    ),
                    confidence=stability,
                    source_phases=["phase15"],
                    structured_data={
                        "stability_score": stability,
                        "context": "stable_temporal_environment",
                    },
                )
            )

        # Analyze meta-conscious state
        phase16 = phase_inputs.get("phase16", {})
        recursive_integrity = phase16.get("recursive_integrity_score", 0.5)

        if recursive_integrity > 0.75:
            insight_id = sha256_hex(
                {"type": "contextual_meta", "value": recursive_integrity}
            )
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="contextual",
                    content=(
                        f"Meta-conscious integrity high ({recursive_integrity:.3f}). "
                        "System shows strong self-awareness and adaptive capacity."
                    ),
                    confidence=recursive_integrity,
                    source_phases=["phase16"],
                    structured_data={
                        "recursive_integrity": recursive_integrity,
                        "context": "high_meta_awareness",
                    },
                )
            )

        return insights

    def _generate_emergent_insights(
        self,
        uif_state: UIFState,
        phase_inputs: dict[str, Any],
    ) -> list[InsightPacket]:
        """Generate emergent cross-domain insights."""
        insights = []

        # Look for emergent patterns across phases
        coherence = uif_state.field_vector.get("dim_140", 0.5)
        ethical = uif_state.ethical_warp
        governance = uif_state.governance_weight

        # Emergent: System readiness for complex decisions
        readiness = coherence * 0.4 + ethical * 0.3 + governance * 0.3

        if readiness > 0.75:
            insight_id = sha256_hex({"type": "emergent_readiness", "value": readiness})
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="emergent",
                    content=(
                        f"Emergent decision readiness ({readiness:.3f}); "
                        "coherence + ethics + governance converge, enabling "
                        "high-complexity autonomous reasoning."
                    ),
                    confidence=readiness,
                    source_phases=["phase12", "phase17", "phase18"],
                    structured_data={
                        "readiness_score": readiness,
                        "pattern": "emergent_capability",
                    },
                )
            )

        # Emergent: Cross-phase synergy
        alignment = uif_state.field_vector.get("dim_141", 0.5)
        if alignment > 0.8:
            insight_id = sha256_hex({"type": "emergent_synergy", "value": alignment})
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="emergent",
                    content=(
                        f"Strong cross-phase synergy detected ({alignment:.3f}). "
                        "Phases are exhibiting emergent harmonization beyond "
                        "individual component capabilities."
                    ),
                    confidence=alignment,
                    source_phases=[
                        "phase12",
                        "phase13",
                        "phase14",
                        "phase15",
                        "phase16",
                        "phase17",
                        "phase18",
                    ],
                    structured_data={
                        "synergy_score": alignment,
                        "pattern": "phase_harmonization",
                    },
                )
            )

        return insights

    def _generate_counterfactual_insights(
        self,
        uif_state: UIFState,
        phase_inputs: dict[str, Any],
    ) -> list[InsightPacket]:
        """Generate counterfactual scenario insights."""
        insights = []

        # Counterfactual: What if ethical score was lower?
        ethical = uif_state.ethical_warp
        if ethical > 0.7:
            counterfactual_ethical = ethical - 0.2
            insight_id = sha256_hex(
                {"type": "counterfactual_ethics", "original": ethical}
            )
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="counterfactual",
                    content=(
                        "Counterfactual: ethical score "
                        f"{counterfactual_ethical:.3f} vs {ethical:.3f} "
                        "triggers extra review."
                    ),
                    confidence=0.75,
                    source_phases=["phase17"],
                    structured_data={
                        "actual_ethical": ethical,
                        "counterfactual_ethical": counterfactual_ethical,
                        "impact": "reduced_autonomy",
                    },
                )
            )

        # Counterfactual: What if governance constraints were relaxed?
        governance = uif_state.governance_weight
        if governance > 0.7:
            counterfactual_gov = governance - 0.2
            insight_id = sha256_hex(
                {"type": "counterfactual_governance", "original": governance}
            )
            insights.append(
                InsightPacket(
                    insight_id=insight_id,
                    insight_type="counterfactual",
                    content=(
                        f"Counterfactual: governance {counterfactual_gov:.3f} vs "
                        f"{governance:.3f} could allow flagged actions, raising risk."
                    ),
                    confidence=0.75,
                    source_phases=["phase18"],
                    structured_data={
                        "actual_governance": governance,
                        "counterfactual_governance": counterfactual_gov,
                        "impact": "increased_risk",
                    },
                )
            )

        return insights
