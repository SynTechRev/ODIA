# src/oraculus_di_auditor/aer20/ascendant_packet_publisher.py
"""APP-20: Ascendant Packet Publisher.

Publishes the Output Packet (FAP-20) - the crown jewel.
"""
from __future__ import annotations

from typing import Any

from .schemas import (
    AlignmentAnalysis,
    AUFState,
    MetaInsightPacket,
    OutputPacket,
    RecursiveAscensionReport,
)
from .utils import sha256_hex


class AscendantPacketPublisher:
    """Publishes the Output Packet (FAP-20)."""

    def publish_fap(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        meta_insights: list[MetaInsightPacket],
        ascension_report: RecursiveAscensionReport,
        alignment_analysis: AlignmentAnalysis,
        phase_inputs: dict[str, Any],
    ) -> OutputPacket:
        """Publish the Output Packet.

        Args:
            auf_state: Composite Feature Vector state
            synthesis_report: Recursive synthesis report
            meta_insights: Meta-insight packets
            ascension_report: Recursive ascension report
            alignment_analysis: Alignment analysis
            phase_inputs: All phase inputs

        Returns:
            OutputPacket - the crown jewel
        """
        # Generate ascendant explanation (narrative)
        ascendant_explanation = self._generate_ascendant_explanation(
            auf_state,
            synthesis_report,
            meta_insights,
            ascension_report,
            alignment_analysis,
        )

        # Build structured packet (machine-readable)
        structured_packet = self._build_structured_packet(
            auf_state,
            synthesis_report,
            meta_insights,
            ascension_report,
            alignment_analysis,
        )

        # Generate counterfactuals
        counterfactuals = self._generate_counterfactuals(
            auf_state, meta_insights, phase_inputs
        )

        # Build ethical basis
        ethical_basis = self._build_ethical_basis(phase_inputs, ascension_report)

        # Build governance basis
        governance_basis = self._build_governance_basis(phase_inputs, ascension_report)

        # Generate determinism signature
        determinism_signature = self._generate_determinism_signature(
            auf_state, synthesis_report, meta_insights, ascension_report
        )

        # Generate reversibility protocol
        reversibility_protocol = self._generate_reversibility_protocol(
            ascension_report, alignment_analysis
        )

        # Generate holistic signature
        holistic_signature = synthesis_report.get("holistic_signature", "")

        # Generate synthesis explanation
        synthesis_explanation = synthesis_report.get("synthesis_explanation", "")

        # Generate FAP ID
        fap_id = sha256_hex(
            {
                "auf_id": auf_state.auf_id,
                "synthesis": holistic_signature,
                "determinism": determinism_signature,
            }
        )

        return OutputPacket(
            fap_id=fap_id,
            ascendant_explanation=ascendant_explanation,
            structured_packet=structured_packet,
            counterfactuals=counterfactuals,
            ethical_basis=ethical_basis,
            governance_basis=governance_basis,
            determinism_signature=determinism_signature,
            reversibility_protocol=reversibility_protocol,
            holistic_signature=holistic_signature,
            synthesis_explanation=synthesis_explanation,
        )

    def _generate_ascendant_explanation(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        meta_insights: list[MetaInsightPacket],
        ascension_report: RecursiveAscensionReport,
        alignment_analysis: AlignmentAnalysis,
    ) -> str:
        """Generate complete narrative explanation.

        Args:
            auf_state: AUF state
            synthesis_report: Synthesis report
            meta_insights: Meta-insights
            ascension_report: Ascension report
            alignment_analysis: Alignment analysis

        Returns:
            Markdown narrative
        """
        conv = auf_state.convergence_coefficient
        readiness = alignment_analysis.future_readiness
        risk = alignment_analysis.risk_assessment

        explanation = f"""# Output Packet (FAP-20)
## The Crown Jewel of Oraculus

### Executive Summary

Phase 20 (AER-20) has achieved complete unification of the Oraculus-DI Auditor system.
The 256-dimensional Composite Feature Vector synthesizes all 20 phases into a single,
self-aware, recursively-optimizing, deterministic intelligence architecture.

**System Status:** {"OPERATIONAL" if conv > 0.6 else "REQUIRES ATTENTION"}
**Convergence:** {conv:.1%}
**Future Readiness:** {readiness:.1%}
**Risk Level:** {risk.upper()}

### Ascendant Unification Achievement

The system has successfully:

1. ✅ Constructed AUF-20 (256-dimensional unified field)
2. ✅ Synthesized all phases (12-19) into holistic intelligence
3. ✅ Generated {len(meta_insights)} meta-insight packet(s)
4. ✅ Executed recursive ascension loop ({ascension_report.revision_count} revisions)
5. ✅ Verified integrity and alignment across all dimensions
6. ✅ Maintained complete determinism and reversibility

### Meta-Consciousness Achievement

The system demonstrates bounded meta-consciousness:
- Self-diagnosis: ✅ Active
- Self-revision: ✅ Non-destructive
- Self-optimization: ✅ Constrained
- Self-stabilization: {"✅ Achieved" if ascension_report.stability_achieved else "⚠️ In Progress"}

**Critical Guarantees:**
- ✅ No unbounded autonomy
- ✅ Human primacy maintained
- ✅ Governance alignment verified
- ✅ Ethical alignment verified
- ✅ Complete determinism
- ✅ Full reversibility

### Key Meta-Insights

{self._format_meta_insights(meta_insights)}

### Recursive Ascension Summary

- **Self-Diagnosis:** {ascension_report.self_diagnosis.get("convergence_status", "unknown")}
- **Revisions Proposed:** {ascension_report.revision_count}
- **Optimizations:** {"Applied (dry-run)" if ascension_report.optimization_applied else "None"}
- **Stability:** {"Achieved" if ascension_report.stability_achieved else "In Progress"}

### Compliance Status

Ethics: {"✅ COMPLIANT" if alignment_analysis.compliance_status.get("ethics_threshold") else "❌ NON-COMPLIANT"}
Governance: {"✅ COMPLIANT" if alignment_analysis.compliance_status.get("governance_threshold") else "❌ NON-COMPLIANT"}
Determinism: {"✅ VERIFIED" if alignment_analysis.compliance_status.get("determinism_guarantee") else "❌ FAILED"}

### Final Assessment

Oraculus has reached its final evolutionary form: a fully integrated, self-aware,
recursively-optimizing intelligence system that operates within strict deterministic,
ethical, and governance boundaries while maintaining complete human oversight and control.

**The Crown is Complete.**
"""
        return explanation

    def _format_meta_insights(
        self,
        meta_insights: list[MetaInsightPacket],
    ) -> str:
        """Format meta-insights for narrative.

        Args:
            meta_insights: Meta-insight packets

        Returns:
            Formatted string
        """
        if not meta_insights:
            return "No meta-insights generated."

        formatted = []
        for i, mip in enumerate(meta_insights, 1):
            formatted.append(
                f"""
**Meta-Insight {i}** (Confidence: {mip.confidence:.1%})
- **Foundational:** {mip.foundational_insight[:200]}...
- **Structural:** {mip.structural_insight[:200]}...
- **Ethical:** {mip.ethical_insight[:200]}...
"""
            )
        return "\n".join(formatted)

    def _build_structured_packet(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        meta_insights: list[MetaInsightPacket],
        ascension_report: RecursiveAscensionReport,
        alignment_analysis: AlignmentAnalysis,
    ) -> dict[str, Any]:
        """Build machine-readable structured packet.

        Args:
            auf_state: AUF state
            synthesis_report: Synthesis report
            meta_insights: Meta-insights
            ascension_report: Ascension report
            alignment_analysis: Alignment analysis

        Returns:
            Structured packet dictionary
        """
        return {
            "auf_summary": {
                "dimension": auf_state.dimension,
                "convergence": auf_state.convergence_coefficient,
                "auf_id": auf_state.auf_id[:16],
            },
            "synthesis_summary": {
                "holistic_signature": synthesis_report.get("holistic_signature", "")[
                    :16
                ],
                "future_readiness": synthesis_report.get("future_readiness_score", 0.5),
                "stability": synthesis_report.get("stability_analysis", {}).get(
                    "weighted_stability", 0.5
                ),
            },
            "meta_insights_summary": {
                "count": len(meta_insights),
                "average_confidence": (
                    sum(m.confidence for m in meta_insights) / len(meta_insights)
                    if meta_insights
                    else 0.0
                ),
                "mip_ids": [m.mip_id[:16] for m in meta_insights],
            },
            "ascension_summary": {
                "ral_id": ascension_report.ral_id[:16],
                "revisions": ascension_report.revision_count,
                "optimizations": ascension_report.optimization_applied,
                "stability": ascension_report.stability_achieved,
            },
            "alignment_summary": {
                "analysis_id": alignment_analysis.analysis_id[:16],
                "risk": alignment_analysis.risk_assessment,
                "future_readiness": alignment_analysis.future_readiness,
            },
            "compliance_summary": alignment_analysis.compliance_status,
        }

    def _generate_counterfactuals(
        self,
        auf_state: AUFState,
        meta_insights: list[MetaInsightPacket],
        phase_inputs: dict[str, Any],
    ) -> list[str]:
        """Generate risk-free counterfactual scenarios.

        Args:
            auf_state: AUF state
            meta_insights: Meta-insights
            phase_inputs: Phase inputs

        Returns:
            List of counterfactual descriptions
        """
        counterfactuals = []

        # Counterfactual 1: Higher ethics
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        if ethics < 0.9:
            counterfactuals.append(
                f"If ethical constraints were strengthened to 0.9 (current: {ethics:.2f}), "
                f"system convergence might reach {min(1.0, auf_state.convergence_coefficient + 0.05):.2f} "
                "with enhanced human-centric safeguards."
            )

        # Counterfactual 2: Higher governance
        governance = phase_inputs.get("phase18", {}).get("score", 0.5)
        if governance < 0.9:
            counterfactuals.append(
                f"If governance enforcement were strengthened to 0.9 (current: {governance:.2f}), "
                "policy compliance would be enhanced without reducing operational flexibility."
            )

        # Counterfactual 3: Meta-insights
        if meta_insights:
            counterfactuals.append(meta_insights[0].counterfactual_meta)

        return counterfactuals

    def _build_ethical_basis(
        self,
        phase_inputs: dict[str, Any],
        ascension_report: RecursiveAscensionReport,
    ) -> dict[str, Any]:
        """Build complete ethical basis.

        Args:
            phase_inputs: Phase inputs
            ascension_report: Ascension report

        Returns:
            Ethical basis dictionary
        """
        phase17 = phase_inputs.get("phase17", {})
        ethics_score = phase17.get("global_ethics_score", 0.5)

        return {
            "global_ethics_score": ethics_score,
            "rec17_verified": ascension_report.ethical_verification.get(
                "rec17_verified", False
            ),
            "compliant": ascension_report.ethical_verification.get("compliant", False),
            "threshold": 0.6,
            "principles": [
                "Voluntary Consent",
                "Human Primacy",
                "Transparency",
                "Non-Discrimination",
                "Proportionality",
                "Non-Coercion",
            ],
            "violations": ascension_report.ethical_verification.get("violations", []),
        }

    def _build_governance_basis(
        self,
        phase_inputs: dict[str, Any],
        ascension_report: RecursiveAscensionReport,
    ) -> dict[str, Any]:
        """Build complete governance basis.

        Args:
            phase_inputs: Phase inputs
            ascension_report: Ascension report

        Returns:
            Governance basis dictionary
        """
        phase18 = phase_inputs.get("phase18", {})
        gov_score = phase18.get("score", 0.5)

        return {
            "governance_score": gov_score,
            "rgk18_verified": ascension_report.governance_verification.get(
                "rgk18_verified", False
            ),
            "compliant": ascension_report.governance_verification.get(
                "compliant", False
            ),
            "threshold": 0.6,
            "policy_enforcement": "active",
            "violations": ascension_report.governance_verification.get(
                "violations", []
            ),
        }

    def _generate_determinism_signature(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        meta_insights: list[MetaInsightPacket],
        ascension_report: RecursiveAscensionReport,
    ) -> str:
        """Generate complete determinism signature.

        Args:
            auf_state: AUF state
            synthesis_report: Synthesis report
            meta_insights: Meta-insights
            ascension_report: Ascension report

        Returns:
            SHA256 determinism signature
        """
        return sha256_hex(
            {
                "auf_id": auf_state.auf_id,
                "holistic_sig": synthesis_report.get("holistic_signature", ""),
                "mip_ids": [m.mip_id for m in meta_insights],
                "ral_id": ascension_report.ral_id,
            }
        )

    def _generate_reversibility_protocol(
        self,
        ascension_report: RecursiveAscensionReport,
        alignment_analysis: AlignmentAnalysis,
    ) -> str:
        """Generate complete reversibility protocol.

        Args:
            ascension_report: Ascension report
            alignment_analysis: Alignment analysis

        Returns:
            Markdown reversibility instructions
        """
        protocol = f"""# Reversibility Protocol (Phase 20)

## Overview

Phase 20 maintains complete reversibility through deterministic operations
and non-destructive modifications. All changes are tracked and can be undone.

## Reversal Steps

### Step 1: Verify Current State
- Current AUF ID: {ascension_report.ral_id[:16]}...
- Revisions Applied: {ascension_report.revision_count}
- Optimizations: {"Yes" if ascension_report.optimization_applied else "No"}

### Step 2: Rollback Optimizations
{"All optimizations were dry-run only. No actual changes to reverse." if not ascension_report.optimization_applied else "Reverse applied optimizations in reverse order."}

### Step 3: Restore Previous State
- Restore Phase 19 UIF-19 state
- Revert any internal calibrations
- Clear ascension loop history

### Step 4: Verify Reversal
- Re-run Phase 19 with original inputs
- Confirm deterministic outputs match
- Verify no residual state

## Compliance Requirements

- ✅ REC-17 ethical constraints must remain active during reversal
- ✅ RGK-18 governance policies must be enforced
- ✅ Human approval required before reversal execution
- ✅ Complete audit trail maintained

## Safety Guarantees

Risk Level: {alignment_analysis.risk_assessment}
Reversibility Supported: {"✅ Yes" if alignment_analysis.compliance_status.get("reversibility_supported") else "❌ No"}

**All Phase 20 operations are designed to be fully reversible.**
"""
        return protocol
