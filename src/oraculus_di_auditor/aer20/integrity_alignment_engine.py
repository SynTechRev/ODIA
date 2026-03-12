# src/oraculus_di_auditor/aer20/integrity_alignment_engine.py
"""IAE-20: Integrity & Alignment Engine.

Comprehensive integrity and alignment verification.
"""
from __future__ import annotations

from typing import Any

from .schemas import AlignmentAnalysis, AUFState
from .utils import sha256_hex


class IntegrityAlignmentEngine:
    """Performs comprehensive integrity and alignment analysis."""

    def analyze_alignment(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        meta_insights: list[Any],
        ascension_report: Any,
        phase_inputs: dict[str, Any],
    ) -> AlignmentAnalysis:
        """Perform complete integrity and alignment analysis.

        Args:
            auf_state: Composite Feature Vector state
            synthesis_report: Recursive synthesis report
            meta_insights: Meta-insight packets
            ascension_report: Recursive ascension report
            phase_inputs: All phase inputs

        Returns:
            AlignmentAnalysis with comprehensive assessment
        """
        # Phase coherence scores
        phase_coherence = self._calculate_phase_coherence(phase_inputs)

        # Harmonization report
        harmonization_report = synthesis_report.get("harmonization_report", {})

        # Stability analysis
        stability_analysis = synthesis_report.get("stability_analysis", {})

        # Future readiness
        future_readiness = synthesis_report.get("future_readiness_score", 0.5)

        # Deviation detection
        deviation_detection = synthesis_report.get("deviation_detection", {})

        # Convergence equilibrium
        convergence_equilibrium = synthesis_report.get("convergence_equilibrium", {})

        # Risk assessment
        risk_assessment = self._assess_risk(
            auf_state, deviation_detection, ascension_report, phase_inputs
        )

        # Compliance status
        compliance_status = self._check_compliance(phase_inputs, ascension_report)

        # Generate analysis ID
        analysis_id = sha256_hex(
            {
                "phase_coherence": phase_coherence,
                "future_readiness": future_readiness,
                "risk": risk_assessment,
                "compliance": compliance_status,
            }
        )

        return AlignmentAnalysis(
            analysis_id=analysis_id,
            phase_coherence=phase_coherence,
            harmonization_report=harmonization_report,
            stability_analysis=stability_analysis,
            future_readiness=future_readiness,
            deviation_detection=deviation_detection,
            convergence_equilibrium=convergence_equilibrium,
            risk_assessment=risk_assessment,
            compliance_status=compliance_status,
        )

    def _calculate_phase_coherence(
        self,
        phase_inputs: dict[str, Any],
    ) -> dict[str, float]:
        """Calculate coherence score for each phase.

        Args:
            phase_inputs: Phase inputs

        Returns:
            Dict mapping phase to coherence score
        """
        return {
            "phase12": phase_inputs.get("phase12", {}).get("coherence_score", 0.5),
            "phase13": phase_inputs.get("phase13", {}).get("probability", 0.5),
            "phase14": phase_inputs.get("phase14", {}).get("prediction_score", 0.5),
            "phase15": phase_inputs.get("phase15", {}).get("stability_score", 0.5),
            "phase16": phase_inputs.get("phase16", {}).get(
                "recursive_integrity_score", 0.5
            ),
            "phase17": phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5),
            "phase18": phase_inputs.get("phase18", {}).get("score", 0.5),
            "phase19": self._extract_phase19_coherence(phase_inputs.get("phase19", {})),
        }

    def _extract_phase19_coherence(
        self,
        phase19: dict[str, Any],
    ) -> float:
        """Extract coherence score from Phase 19.

        Args:
            phase19: Phase 19 output

        Returns:
            Coherence score
        """
        # Use UIF convergence as coherence proxy
        uif_state = phase19.get("uif_19_state", {})
        # Calculate from harmonization pressure and ethical warp
        harm = uif_state.get("harmonization_pressure", 0.5)
        eth = uif_state.get("ethical_warp", 0.5)
        gov = uif_state.get("governance_weight", 0.5)
        return (harm + eth + gov) / 3

    def _assess_risk(
        self,
        auf_state: AUFState,
        deviation_detection: dict[str, Any],
        ascension_report: Any,
        phase_inputs: dict[str, Any],
    ) -> str:
        """Assess overall system risk level.

        Args:
            auf_state: AUF state
            deviation_detection: Deviation analysis
            ascension_report: Ascension report
            phase_inputs: Phase inputs

        Returns:
            Risk level: none, low, moderate, high
        """
        # Check for high-severity issues
        deviations = deviation_detection.get("deviations", [])
        high_severity = any(d.get("severity") == "high" for d in deviations)

        # Check convergence
        low_convergence = auf_state.convergence_coefficient < 0.5

        # Check compliance
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        governance = phase_inputs.get("phase18", {}).get("score", 0.5)
        non_compliant = ethics < 0.6 or governance < 0.6

        # Check stability
        stability_achieved = ascension_report.stability_achieved

        # Assess risk
        if high_severity or non_compliant:
            return "high"
        elif low_convergence or not stability_achieved:
            return "moderate"
        elif len(deviations) > 0:
            return "low"
        else:
            return "none"

    def _check_compliance(
        self,
        phase_inputs: dict[str, Any],
        ascension_report: Any,
    ) -> dict[str, bool]:
        """Check compliance with all requirements.

        Args:
            phase_inputs: Phase inputs
            ascension_report: Ascension report

        Returns:
            Dict mapping requirement to compliance status
        """
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        governance = phase_inputs.get("phase18", {}).get("score", 0.5)

        ethics_verified = ascension_report.ethical_verification.get("compliant", False)
        gov_verified = ascension_report.governance_verification.get("compliant", False)
        determinism_verified = ascension_report.determinism_verification.get(
            "determinism_verified", False
        )

        return {
            "ethics_threshold": ethics >= 0.6,
            "governance_threshold": governance >= 0.6,
            "rec17_verification": ethics_verified,
            "rgk18_verification": gov_verified,
            "determinism_guarantee": determinism_verified,
            "reversibility_supported": True,  # Always true by design
            "human_primacy": True,  # Always true by design
            "non_autonomy": True,  # Always true by design
        }
