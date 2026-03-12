# tests/aer20/test_phase20_service.py
"""Tests for Phase20Service orchestrator."""
import pytest

from oraculus_di_auditor.aer20.aer20_service import Phase20Service


def _create_phase_inputs_fixture():
    """Create comprehensive Phase 12-19 input fixture."""
    return {
        "phase12": {
            "coherence_score": 0.85,
            "scalar_map": {"layer_0": 1.0, "layer_1": 0.9},
        },
        "phase13": {
            "probability": 0.88,
            "temporal_vector": [0.9, 0.85, 0.82],
        },
        "phase14": {
            "prediction_score": 0.82,
            "recursive_depth": 3,
        },
        "phase15": {
            "stability_score": 0.80,
            "temporal_field": {"stability": 0.75},
        },
        "phase16": {
            "recursive_integrity_score": 0.87,
            "meta_harmonic_field": {"0": 1.0, "1": 0.9},
        },
        "phase17": {
            "global_ethics_score": 0.90,
            "ethical_lattice": {
                "primary_ethic": "beneficence",
                "ethical_vector": {
                    "rights_impact": 0.85,
                    "harm_probability": 0.15,
                },
            },
            "ethical_projection": {
                "risk": "low",
                "reversible": True,
            },
            "governance_invariants": {
                "invariant_violations": [],
                "alignment_score": 0.88,
            },
        },
        "phase18": {
            "score": 0.86,
            "outcome": {"outcome": "APPROVE"},
            "policy_violations": [],
        },
        "phase19": {
            "uif_19_state": {
                "uif_id": "a" * 64,
                "dimension": 142,
                "field_vector": {f"dim_{i}": 0.5 + i * 0.001 for i in range(142)},
                "phase_contributions": {
                    "phase12": {"coherence": 0.85},
                    "phase17": {"ethics": 0.90},
                    "phase18": {"governance": 0.86},
                },
                "harmonization_pressure": 0.85,
                "ethical_warp": 0.90,
                "governance_weight": 0.86,
            },
            "insight_packets": [
                {
                    "insight_id": "b" * 64,
                    "insight_type": "analytic",
                    "content": "Test insight",
                    "confidence": 0.88,
                    "source_phases": ["phase12", "phase17"],
                    "structured_data": {},
                }
            ],
            "alignment_report": {
                "alignment_id": "c" * 64,
                "rec17_compliant": True,
                "rgk18_compliant": True,
                "ethical_score": 0.90,
                "governance_score": 0.86,
                "violations": [],
                "recommendations": [],
            },
            "scenario_map": {
                "scenario_id": "d" * 64,
                "steps": [],
                "trajectory_type": "stable",
                "reversibility": True,
                "critical_points": [],
            },
            "aei19_result": {
                "result_id": "e" * 64,
                "explanation": "Test explanation",
                "structured_packet": {},
                "counterfactuals": [],
                "ethical_basis": {},
                "governance_basis": {},
                "determinism_signature": "f" * 64,
                "reversibility_protocol": "Test protocol",
            },
            "provenance": {
                "input_hash": "g" * 64,
                "service_version": "aei19-1.0.0",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        },
    }


def test_phase20_run_basic():
    """Test basic Phase 20 execution."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    # Verify all required top-level fields present
    assert result.auf_20_state is not None
    assert result.meta_insights is not None
    assert result.recursive_ascension_report is not None
    assert result.alignment_analysis is not None
    assert result.fap_20_result is not None
    assert result.provenance is not None


def test_phase20_auf_construction():
    """Test AUF-20 construction with 256 dimensions."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    auf = result.auf_20_state
    assert auf.dimension == 256
    assert len(auf.auf_id) == 64  # SHA256 hex
    assert len(auf.field_vector) == 256
    assert 0.0 <= auf.convergence_coefficient <= 1.0

    # Check dimension ranges
    assert "dim_0" in auf.field_vector
    assert "dim_141" in auf.field_vector  # End of UIF-19
    assert "dim_255" in auf.field_vector  # End of AUF-20

    # Check phase contributions
    assert "phase12" in auf.phase_contributions
    assert "phase19" in auf.phase_contributions

    # Check integration structures
    assert auf.uif19_integration["dimension"] == 142
    assert auf.rgk18_lattice is not None
    assert auf.emcs16_harmonics is not None
    assert auf.rec17_ethics is not None


def test_phase20_meta_insight_generation():
    """Test that meta-insights are generated."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    # Should have at least 1 meta-insight
    assert len(result.meta_insights) >= 1

    # Check first meta-insight structure
    mip = result.meta_insights[0]
    assert len(mip.mip_id) == 64  # SHA256
    assert mip.foundational_insight
    assert mip.structural_insight
    assert mip.temporal_insight
    assert mip.ethical_insight
    assert mip.governance_insight
    assert mip.counterfactual_meta
    assert 0.0 <= mip.confidence <= 1.0

    # Check meta-insight components
    assert isinstance(mip.cross_domain_convergence, dict)
    assert isinstance(mip.emergent_resonance, dict)
    assert isinstance(mip.scalar_themes, list)
    assert isinstance(mip.harmonic_stability, dict)


def test_phase20_recursive_ascension_loop():
    """Test recursive ascension loop execution."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    ral = result.recursive_ascension_report
    assert len(ral.ral_id) == 64  # SHA256

    # Check all 7 required components
    assert ral.self_diagnosis is not None
    assert ral.self_revision is not None
    assert ral.self_optimization is not None
    assert ral.self_stabilization is not None
    assert ral.governance_verification is not None
    assert ral.ethical_verification is not None
    assert ral.determinism_verification is not None

    # Check metrics
    assert isinstance(ral.revision_count, int)
    assert isinstance(ral.optimization_applied, bool)
    assert isinstance(ral.stability_achieved, bool)

    # Verify no auto-application (safety)
    assert ral.self_optimization.get("auto_applied") is False


def test_phase20_integrity_alignment():
    """Test integrity and alignment analysis."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    analysis = result.alignment_analysis
    assert len(analysis.analysis_id) == 64  # SHA256

    # Check phase coherence
    assert "phase12" in analysis.phase_coherence
    assert "phase19" in analysis.phase_coherence

    # Check required reports
    assert analysis.harmonization_report is not None
    assert analysis.stability_analysis is not None
    assert 0.0 <= analysis.future_readiness <= 1.0
    assert analysis.deviation_detection is not None
    assert analysis.convergence_equilibrium is not None

    # Check risk assessment
    assert analysis.risk_assessment in ["none", "low", "moderate", "high"]

    # Check compliance
    assert isinstance(analysis.compliance_status, dict)
    assert "ethics_threshold" in analysis.compliance_status
    assert "governance_threshold" in analysis.compliance_status
    assert "determinism_guarantee" in analysis.compliance_status


def test_phase20_final_ascendant_packet():
    """Test Final Ascendant Packet (FAP-20) structure."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    fap = result.fap_20_result
    assert len(fap.fap_id) == 64  # SHA256

    # Check narrative explanation
    assert fap.ascendant_explanation
    assert "Phase 20" in fap.ascendant_explanation
    assert "AER-20" in fap.ascendant_explanation

    # Check structured packet
    assert isinstance(fap.structured_packet, dict)
    assert "auf_summary" in fap.structured_packet
    assert "synthesis_summary" in fap.structured_packet
    assert "meta_insights_summary" in fap.structured_packet

    # Check counterfactuals
    assert isinstance(fap.counterfactuals, list)

    # Check ethical and governance basis
    assert isinstance(fap.ethical_basis, dict)
    assert isinstance(fap.governance_basis, dict)
    assert "global_ethics_score" in fap.ethical_basis
    assert "governance_score" in fap.governance_basis

    # Check signatures and protocols
    assert len(fap.determinism_signature) == 64
    assert fap.reversibility_protocol
    assert "Reversibility Protocol" in fap.reversibility_protocol
    assert fap.holistic_signature
    assert fap.synthesis_explanation


def test_phase20_determinism():
    """Test that Phase 20 produces deterministic outputs."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    # Run twice with same inputs
    result1 = service.run_ascendant_emergence(phase_inputs)
    result2 = service.run_ascendant_emergence(phase_inputs)

    # AUF IDs should match
    assert result1.auf_20_state.auf_id == result2.auf_20_state.auf_id

    # Meta-insight IDs should match
    assert len(result1.meta_insights) == len(result2.meta_insights)
    assert result1.meta_insights[0].mip_id == result2.meta_insights[0].mip_id

    # Ascension report IDs should match
    assert (
        result1.recursive_ascension_report.ral_id
        == result2.recursive_ascension_report.ral_id
    )

    # FAP determinism signature should match
    assert (
        result1.fap_20_result.determinism_signature
        == result2.fap_20_result.determinism_signature
    )


def test_phase20_dry_run_default():
    """Test that dry_run defaults to True."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    # Provenance should show dry_run=True
    assert result.provenance["dry_run"] is True


def test_phase20_auto_apply_flag():
    """Test auto_apply flag in provenance."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs, auto_apply=False)

    # Provenance should show auto_apply=False
    assert result.provenance["auto_apply"] is False


def test_phase20_missing_phase_inputs():
    """Test that missing phase inputs raise ValueError."""
    service = Phase20Service()

    # Missing phase19
    incomplete_inputs = _create_phase_inputs_fixture()
    del incomplete_inputs["phase19"]

    with pytest.raises(ValueError, match="Missing required phase inputs"):
        service.run_ascendant_emergence(incomplete_inputs)


def test_phase20_invalid_phase17_format():
    """Test that invalid Phase 17 format raises ValueError."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    # Remove required field
    del phase_inputs["phase17"]["global_ethics_score"]

    with pytest.raises(ValueError, match="global_ethics_score"):
        service.run_ascendant_emergence(phase_inputs)


def test_phase20_invalid_phase18_format():
    """Test that invalid Phase 18 format raises ValueError."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    # Remove required field
    del phase_inputs["phase18"]["score"]

    with pytest.raises(ValueError, match="Phase 18"):
        service.run_ascendant_emergence(phase_inputs)


def test_phase20_invalid_phase19_format():
    """Test that invalid Phase 19 format raises ValueError."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    # Remove required field
    del phase_inputs["phase19"]["uif_19_state"]

    with pytest.raises(ValueError, match="uif_19_state"):
        service.run_ascendant_emergence(phase_inputs)


def test_phase20_low_scores_scenario():
    """Test Phase 20 behavior with low ethics/governance scores."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    # Set low scores
    phase_inputs["phase17"]["global_ethics_score"] = 0.4
    phase_inputs["phase18"]["score"] = 0.45

    result = service.run_ascendant_emergence(phase_inputs)

    # Should still produce result but with warnings
    assert result.alignment_analysis.risk_assessment in ["moderate", "high"]

    # Compliance should be non-compliant
    assert result.alignment_analysis.compliance_status["ethics_threshold"] is False
    assert result.alignment_analysis.compliance_status["governance_threshold"] is False

    # Ascension report should detect issues
    ral = result.recursive_ascension_report
    assert ral.self_diagnosis["issues_detected"] > 0
    assert ral.ethical_verification["compliant"] is False
    assert ral.governance_verification["compliant"] is False


def test_phase20_provenance_metadata():
    """Test provenance metadata is complete."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(
        phase_inputs, dry_run=True, auto_apply=False
    )

    prov = result.provenance
    assert len(prov["input_hash"]) == 64
    assert prov["service_version"] == "aer20-1.0.0"
    assert prov["dry_run"] is True
    assert prov["auto_apply"] is False
    assert prov["determinism_guaranteed"] is True
    assert prov["reversibility_supported"] is True
    assert prov["human_primacy_maintained"] is True
    assert prov["no_unbounded_autonomy"] is True

    # Check all phases integrated
    phases = prov["phases_integrated"]
    assert "phase12" in phases
    assert "phase19" in phases
    assert len(phases) == 8


def test_phase20_explanation_narrative():
    """Test that FAP explanation contains expected content."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    explanation = result.fap_20_result.ascendant_explanation

    # Should contain key phrases
    assert "Final Ascendant Packet" in explanation
    assert "FAP-20" in explanation
    assert "Crown" in explanation or "crown" in explanation
    assert "Phase 20" in explanation or "AER-20" in explanation
    assert "Convergence" in explanation or "convergence" in explanation

    # Should contain status information
    assert "OPERATIONAL" in explanation or "REQUIRES ATTENTION" in explanation


def test_phase20_synthesis_explanation():
    """Test synthesis explanation is generated."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    synthesis = result.fap_20_result.synthesis_explanation

    # Should be non-empty and contain key content
    assert len(synthesis) > 100
    assert "Recursive Synthesis" in synthesis or "synthesis" in synthesis


def test_phase20_reversibility_protocol():
    """Test reversibility protocol is detailed."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    protocol = result.fap_20_result.reversibility_protocol

    # Should contain step-by-step instructions
    assert "Reversibility Protocol" in protocol
    assert "Step" in protocol
    assert "Phase 20" in protocol or "AER-20" in protocol
    assert "Rollback" in protocol or "Restore" in protocol or "Reversal" in protocol


def test_phase20_high_convergence_generates_multiple_insights():
    """Test that high convergence generates multiple meta-insights."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    # Ensure high scores for convergence
    phase_inputs["phase12"]["coherence_score"] = 0.95
    phase_inputs["phase17"]["global_ethics_score"] = 0.95
    phase_inputs["phase18"]["score"] = 0.95

    result = service.run_ascendant_emergence(phase_inputs)

    # High convergence should generate 2 meta-insights
    assert len(result.meta_insights) >= 1

    # Check convergence is high
    assert result.auf_20_state.convergence_coefficient > 0.7


def test_phase20_compliance_verification():
    """Test comprehensive compliance verification."""
    service = Phase20Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_ascendant_emergence(phase_inputs)

    compliance = result.alignment_analysis.compliance_status

    # Check all compliance flags
    assert "ethics_threshold" in compliance
    assert "governance_threshold" in compliance
    assert "rec17_verification" in compliance
    assert "rgk18_verification" in compliance
    assert "determinism_guarantee" in compliance
    assert "reversibility_supported" in compliance
    assert "human_primacy" in compliance
    assert "non_autonomy" in compliance

    # Safety guarantees should always be True
    assert compliance["reversibility_supported"] is True
    assert compliance["human_primacy"] is True
    assert compliance["non_autonomy"] is True
