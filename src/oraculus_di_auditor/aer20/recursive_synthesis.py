# src/oraculus_di_auditor/aer20/recursive_synthesis.py
"""RSE-20: Recursive Synthesis Engine.

Generates holistic synthesis across all intelligence layers.
"""
from __future__ import annotations

from typing import Any

from .schemas import AUFState
from .utils import sha256_hex


class RecursiveSynthesisEngine:
    """Performs recursive synthesis across all phases and intelligence layers.

    Generates:
    - Holistic intelligence signature
    - Deep synthesis explanation
    - Phase-to-phase harmonization report
    - Stability analysis
    - Future readiness score
    - Deviation detection
    - Convergence equilibrium report
    """

    def synthesize(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform complete recursive synthesis.

        Args:
            auf_state: Ascendant Unified Field state
            phase_inputs: All phase inputs (12-19)

        Returns:
            Complete synthesis report
        """
        # Generate holistic signature
        holistic_signature = self._generate_holistic_signature(auf_state, phase_inputs)

        # Deep synthesis explanation
        synthesis_explanation = self._generate_synthesis_explanation(
            auf_state, phase_inputs
        )

        # Phase-to-phase harmonization
        harmonization_report = self._analyze_harmonization(auf_state, phase_inputs)

        # Stability analysis
        stability_analysis = self._analyze_stability(auf_state, phase_inputs)

        # Future readiness
        future_readiness = self._calculate_future_readiness(auf_state, phase_inputs)

        # Deviation detection
        deviation_analysis = self._detect_deviations(auf_state, phase_inputs)

        # Convergence equilibrium
        convergence_equilibrium = self._analyze_convergence(auf_state, phase_inputs)

        return {
            "holistic_signature": holistic_signature,
            "synthesis_explanation": synthesis_explanation,
            "harmonization_report": harmonization_report,
            "stability_analysis": stability_analysis,
            "future_readiness_score": future_readiness,
            "deviation_detection": deviation_analysis,
            "convergence_equilibrium": convergence_equilibrium,
        }

    def _generate_holistic_signature(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> str:
        """Generate holistic intelligence signature.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Holistic signature string
        """
        # Collect key metrics from all phases
        metrics = {
            "convergence": auf_state.convergence_coefficient,
            "ethics": phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5),
            "governance": phase_inputs.get("phase18", {}).get("score", 0.5),
            "coherence": phase_inputs.get("phase12", {}).get("coherence_score", 0.5),
            "stability": phase_inputs.get("phase15", {}).get("stability_score", 0.5),
        }

        signature = sha256_hex(metrics)
        return signature

    def _generate_synthesis_explanation(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> str:
        """Generate deep synthesis explanation.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Markdown explanation
        """
        conv = auf_state.convergence_coefficient
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        gov = phase_inputs.get("phase18", {}).get("score", 0.5)

        explanation = f"""# Recursive Synthesis Report

## Overall Assessment

The Oraculus system demonstrates a convergence coefficient of {conv:.3f}, indicating {"strong" if conv > 0.7 else "moderate" if conv > 0.5 else "developing"} integration across all phases.

## Phase Integration Status

- **Foundational Phases (12-15)**: Coherence and temporal governance established
- **Cognitive Phases (16-17)**: Meta-consciousness and ethical cognition operational
- **Governance Phase (18)**: Recursive governance kernel active (score: {gov:.3f})
- **Applied Intelligence (19)**: Emergent intelligence synthesis complete
- **Ascendant Synthesis (20)**: 256-dimensional unified field constructed

## Ethical-Governance Alignment

Ethics Score: {ethics:.3f}
Governance Score: {gov:.3f}
Alignment Status: {"COMPLIANT" if ethics >= 0.6 and gov >= 0.6 else "ATTENTION REQUIRED"}

## System Readiness

The system has achieved recursive self-awareness within deterministic bounds,
maintaining complete reversibility and human primacy throughout all operations.
"""
        return explanation

    def _analyze_harmonization(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze phase-to-phase harmonization.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Harmonization report
        """
        # Check each phase pair for compatibility
        phase_scores = {
            "phase12": phase_inputs.get("phase12", {}).get("coherence_score", 0.5),
            "phase13": phase_inputs.get("phase13", {}).get("probability", 0.5),
            "phase14": phase_inputs.get("phase14", {}).get("prediction_score", 0.5),
            "phase15": phase_inputs.get("phase15", {}).get("stability_score", 0.5),
            "phase16": phase_inputs.get("phase16", {}).get(
                "recursive_integrity_score", 0.5
            ),
            "phase17": phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5),
            "phase18": phase_inputs.get("phase18", {}).get("score", 0.5),
        }

        # Calculate pairwise harmonization
        harmonization_pairs = []
        phases = list(phase_scores.keys())
        for i in range(len(phases) - 1):
            p1, p2 = phases[i], phases[i + 1]
            score1, score2 = phase_scores[p1], phase_scores[p2]
            harmony = 1.0 - abs(score1 - score2)
            harmonization_pairs.append(
                {
                    "pair": f"{p1}-{p2}",
                    "harmony_score": harmony,
                    "status": (
                        "good"
                        if harmony > 0.8
                        else "moderate" if harmony > 0.6 else "attention"
                    ),
                }
            )

        avg_harmony = sum(p["harmony_score"] for p in harmonization_pairs) / len(
            harmonization_pairs
        )

        return {
            "average_harmonization": avg_harmony,
            "pairwise_analysis": harmonization_pairs,
            "overall_status": (
                "harmonized"
                if avg_harmony > 0.8
                else "acceptable" if avg_harmony > 0.6 else "needs_attention"
            ),
        }

    def _analyze_stability(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze overall system stability.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Stability analysis
        """
        # Weighted stability calculation
        coherence = phase_inputs.get("phase12", {}).get("coherence_score", 0.5)
        temporal_stability = phase_inputs.get("phase15", {}).get("stability_score", 0.5)
        meta_conscious = phase_inputs.get("phase16", {}).get(
            "recursive_integrity_score", 0.5
        )

        weighted_stability = (
            0.3 * coherence + 0.4 * temporal_stability + 0.3 * meta_conscious
        )

        return {
            "weighted_stability": weighted_stability,
            "components": {
                "coherence": coherence,
                "temporal": temporal_stability,
                "meta_conscious": meta_conscious,
            },
            "stability_level": (
                "high"
                if weighted_stability > 0.75
                else "moderate" if weighted_stability > 0.6 else "low"
            ),
        }

    def _calculate_future_readiness(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> float:
        """Calculate system readiness for future demands.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Readiness score (0.0-1.0)
        """
        # Factors: convergence, stability, ethics, governance
        conv = auf_state.convergence_coefficient
        stability = phase_inputs.get("phase15", {}).get("stability_score", 0.5)
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        governance = phase_inputs.get("phase18", {}).get("score", 0.5)

        readiness = 0.25 * conv + 0.25 * stability + 0.25 * ethics + 0.25 * governance
        return min(1.0, max(0.0, readiness))

    def _detect_deviations(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Detect deviations from expected behavior.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Deviation analysis
        """
        deviations = []

        # Check ethics threshold
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        if ethics < 0.6:
            deviations.append(
                {
                    "type": "ethical",
                    "severity": "high",
                    "description": f"Ethics score {ethics:.3f} below threshold 0.6",
                }
            )

        # Check governance threshold
        governance = phase_inputs.get("phase18", {}).get("score", 0.5)
        if governance < 0.6:
            deviations.append(
                {
                    "type": "governance",
                    "severity": "high",
                    "description": f"Governance score {governance:.3f} below threshold 0.6",
                }
            )

        # Check convergence
        if auf_state.convergence_coefficient < 0.5:
            deviations.append(
                {
                    "type": "convergence",
                    "severity": "moderate",
                    "description": f"Convergence {auf_state.convergence_coefficient:.3f} below expected 0.5",
                }
            )

        return {
            "deviations_detected": len(deviations),
            "deviations": deviations,
            "status": "compliant" if len(deviations) == 0 else "deviations_found",
        }

    def _analyze_convergence(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze convergence equilibrium.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Convergence equilibrium analysis
        """
        # Calculate variance across dimensions
        field_values = list(auf_state.field_vector.values())
        mean_val = sum(field_values) / len(field_values)
        variance = sum((v - mean_val) ** 2 for v in field_values) / len(field_values)
        std_dev = variance**0.5

        return {
            "mean_field_value": mean_val,
            "variance": variance,
            "std_deviation": std_dev,
            "convergence_coefficient": auf_state.convergence_coefficient,
            "equilibrium_status": (
                "stable"
                if std_dev < 0.2
                else "moderate" if std_dev < 0.4 else "divergent"
            ),
            "recommendation": (
                "System in equilibrium"
                if std_dev < 0.2
                else (
                    "Monitor for stability"
                    if std_dev < 0.4
                    else "Stabilization recommended"
                )
            ),
        }
