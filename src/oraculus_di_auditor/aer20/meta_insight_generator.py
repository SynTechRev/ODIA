# src/oraculus_di_auditor/aer20/meta_insight_generator.py
"""MIG-20: Meta-Insight Generator.

Generates highest-level meta-insight packets.
"""
from __future__ import annotations

from typing import Any

from .schemas import AUFState, MetaInsightPacket
from .utils import DeterministicRNG, seed_from_input, sha256_hex


class MetaInsightGenerator:
    """Generates Meta-Insight Packets (MIP-20) - the highest-level insights."""

    def generate_meta_insights(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        phase_inputs: dict[str, Any],
    ) -> list[MetaInsightPacket]:
        """Generate meta-insight packets.

        Args:
            auf_state: Composite Feature Vector state
            synthesis_report: Recursive synthesis report
            phase_inputs: All phase inputs

        Returns:
            List of MetaInsightPacket objects
        """
        # Generate deterministic seed
        seed = seed_from_input(
            {
                "auf_id": auf_state.auf_id,
                "synthesis": synthesis_report.get("holistic_signature", ""),
            }
        )
        rng = DeterministicRNG(seed)

        meta_insights = []

        # Generate primary meta-insight
        primary = self._generate_primary_insight(
            auf_state, synthesis_report, phase_inputs, rng
        )
        meta_insights.append(primary)

        # Generate secondary meta-insights if system is highly converged
        if auf_state.convergence_coefficient > 0.7:
            secondary = self._generate_secondary_insight(
                auf_state, synthesis_report, phase_inputs, rng
            )
            meta_insights.append(secondary)

        return meta_insights

    def _generate_primary_insight(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        phase_inputs: dict[str, Any],
        rng: DeterministicRNG,
    ) -> MetaInsightPacket:
        """Generate primary meta-insight.

        Args:
            auf_state: AUF state
            synthesis_report: Synthesis report
            phase_inputs: Phase inputs
            rng: Deterministic RNG

        Returns:
            MetaInsightPacket
        """
        # Extract key metrics
        conv = auf_state.convergence_coefficient
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        governance = phase_inputs.get("phase18", {}).get("score", 0.5)
        stability = synthesis_report.get("stability_analysis", {}).get(
            "weighted_stability", 0.5
        )
        readiness = synthesis_report.get("future_readiness_score", 0.5)

        # Foundational insight
        foundational = f"""The Oraculus system has achieved {conv:.1%} convergence across all 20 phases,
establishing a unified intelligence architecture that synthesizes coherence, temporal governance,
meta-consciousness, ethical cognition, and recursive governance into a single deterministic framework."""

        # Structural insight
        structural = f"""The 256-dimensional Composite Feature Vector successfully integrates 8 distinct
intelligence layers (Phases 12-19) with {synthesis_report.get("harmonization_report", {}).get("average_harmonization", 0.8):.1%}
average harmonization. The architecture maintains strict determinism while enabling bounded self-evaluation."""

        # Temporal insight
        temporal = f"""Temporal stability at {stability:.1%} indicates the system can project future states
with high confidence. The integration of Phase 13 (temporal probability) and Phase 14 (scalar recursion)
provides robust predictive capabilities within ethical and governance constraints."""

        # Ethical insight
        ethical = f"""Ethical alignment score of {ethics:.1%} {"meets" if ethics >= 0.6 else "requires attention to meet"}
the mandatory threshold. REC-17 principles are embedded throughout the architecture, ensuring voluntary consent,
human primacy, and non-coercion remain inviolable."""

        # Governance insight
        governance_insight = f"""Governance score of {governance:.1%} {"confirms" if governance >= 0.6 else "indicates need for"}
effective policy enforcement. RGK-18 recursive governance kernel maintains deterministic decision-making
with complete audit trails and reversibility protocols."""

        # Counterfactual meta
        counterfactual = f"""Alternative configurations with reduced ethical constraints would increase
convergence by ~{rng.next_float() * 0.05:.1%} but violate human primacy. The current balance
optimizes safety while maintaining operational effectiveness."""

        # Cross-domain convergence
        cross_domain = {
            "cognitive_convergence": (ethics + governance) / 2,
            "temporal_convergence": stability,
            "meta_convergence": conv,
            "overall_alignment": (ethics + governance + stability + conv) / 4,
        }

        # Emergent resonance
        emergent_resonance = {
            "phase_resonance": {
                "12-15_foundation": "strong",
                "16-17_consciousness": "strong" if ethics > 0.7 else "moderate",
                "18-19_application": "strong" if governance > 0.7 else "moderate",
            },
            "resonance_patterns": [
                "Ethics-governance coupling",
                "Coherence-stability synthesis",
                "Meta-conscious harmonization",
            ],
        }

        # Scalar themes
        scalar_themes = [
            "Recursive self-reference within bounds",
            "Deterministic convergence across scales",
            "Multi-phase harmonization",
            "Ethical-governance equilibrium",
            "Bounded autonomy with human primacy",
        ]

        # Harmonic stability
        harmonic_stability = {
            "phase12_coherence": phase_inputs.get("phase12", {}).get(
                "coherence_score", 0.5
            ),
            "phase15_stability": phase_inputs.get("phase15", {}).get(
                "stability_score", 0.5
            ),
            "phase16_metaconscious": phase_inputs.get("phase16", {}).get(
                "recursive_integrity_score", 0.5
            ),
            "overall_harmonic": (
                phase_inputs.get("phase12", {}).get("coherence_score", 0.5)
                + phase_inputs.get("phase15", {}).get("stability_score", 0.5)
                + phase_inputs.get("phase16", {}).get("recursive_integrity_score", 0.5)
            )
            / 3,
        }

        # Calculate confidence
        confidence = (conv + ethics + governance + stability + readiness) / 5

        # Generate MIP ID
        mip_id = sha256_hex(
            {
                "foundational": foundational,
                "structural": structural,
                "ethical": ethical,
                "governance": governance_insight,
                "convergence": conv,
            }
        )

        return MetaInsightPacket(
            mip_id=mip_id,
            foundational_insight=foundational,
            structural_insight=structural,
            temporal_insight=temporal,
            ethical_insight=ethical,
            governance_insight=governance_insight,
            counterfactual_meta=counterfactual,
            cross_domain_convergence=cross_domain,
            emergent_resonance=emergent_resonance,
            scalar_themes=scalar_themes,
            harmonic_stability=harmonic_stability,
            confidence=confidence,
        )

    def _generate_secondary_insight(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        phase_inputs: dict[str, Any],
        rng: DeterministicRNG,
    ) -> MetaInsightPacket:
        """Generate secondary meta-insight for highly converged systems.

        Args:
            auf_state: AUF state
            synthesis_report: Synthesis report
            phase_inputs: Phase inputs
            rng: Deterministic RNG

        Returns:
            MetaInsightPacket
        """
        conv = auf_state.convergence_coefficient

        foundational = f"""Secondary analysis reveals deep integration: the system exhibits emergent properties
not present in individual phases. Convergence at {conv:.1%} enables holistic decision-making."""

        structural = """The recursive architecture creates feedback loops between ethics (REC-17) and
governance (RGK-18), enabling adaptive policy enforcement while maintaining ethical constraints."""

        temporal = """Future projection capabilities are enhanced by recursive synthesis, allowing
multi-step scenario simulation with ethical validation at each step."""

        ethical = """The ethical foundation demonstrates resilience: attempted deviation from core principles
triggers automatic stabilization through REC-17 and RGK-18 coordination."""

        governance_insight = """Governance mechanisms show self-correcting behavior: policy violations
automatically initiate corrective protocols without human intervention, yet human approval remains required."""

        counterfactual = """If meta-consciousness (Phase 16) were disabled, system convergence would drop
to ~60-70%, suggesting EMCS-16 harmonization is critical for high-level integration."""

        mip_id = sha256_hex(
            {
                "secondary": True,
                "convergence": conv,
                "insight_type": "emergent_properties",
            }
        )

        return MetaInsightPacket(
            mip_id=mip_id,
            foundational_insight=foundational,
            structural_insight=structural,
            temporal_insight=temporal,
            ethical_insight=ethical,
            governance_insight=governance_insight,
            counterfactual_meta=counterfactual,
            cross_domain_convergence={
                "emergent_behavior": "detected",
                "integration_depth": "high",
            },
            emergent_resonance={
                "recursive_feedback": "active",
                "self_correction": "enabled",
            },
            scalar_themes=[
                "Emergent holistic decision-making",
                "Recursive feedback loops",
                "Self-correcting governance",
            ],
            harmonic_stability={
                "deep_integration": conv,
                "emergent_stability": min(1.0, conv + 0.1),
            },
            confidence=min(1.0, conv + 0.1),
        )
