# tests/aei19/test_phase19_service.py
"""Tests for Phase19Service orchestrator."""
import pytest

from oraculus_di_auditor.aei19.aei19_service import Phase19Service


def _create_phase_inputs_fixture():
    """Create comprehensive Phase 12-18 input fixture."""
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
    }


def test_phase19_run_basic():
    """Test basic Phase 19 execution."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    # Verify all required top-level fields present
    assert result.uif_19_state is not None
    assert result.insight_packets is not None
    assert result.alignment_report is not None
    assert result.scenario_map is not None
    assert result.aei19_result is not None
    assert result.provenance is not None


def test_phase19_uif_construction():
    """Test UIF-19 construction with 142 dimensions."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    uif = result.uif_19_state
    assert uif.dimension == 142
    assert len(uif.uif_id) == 64  # SHA256 hex
    assert len(uif.field_vector) == 142
    assert 0.0 <= uif.harmonization_pressure <= 1.0
    assert 0.0 <= uif.ethical_warp <= 1.0
    assert 0.0 <= uif.governance_weight <= 1.0

    # Check dimension ranges
    assert "dim_0" in uif.field_vector
    assert "dim_140" in uif.field_vector
    assert "dim_141" in uif.field_vector

    # Check phase contributions
    assert "phase12" in uif.phase_contributions
    assert "phase17" in uif.phase_contributions
    assert "phase18" in uif.phase_contributions


def test_phase19_insight_generation():
    """Test that insights are generated across all types."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    insights = result.insight_packets
    assert len(insights) > 0

    # Check insight types
    insight_types = {i.insight_type for i in insights}
    # Should have at least some of these types
    assert len(insight_types) > 0

    # Check insight structure
    for insight in insights:
        assert len(insight.insight_id) == 64  # SHA256
        assert insight.insight_type in [
            "analytic",
            "contextual",
            "emergent",
            "counterfactual",
        ]
        assert len(insight.content) > 0
        assert 0.0 <= insight.confidence <= 1.0
        assert len(insight.source_phases) > 0


def test_phase19_alignment_checking():
    """Test ethical and governance alignment checking."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    alignment = result.alignment_report
    assert len(alignment.alignment_id) == 64  # SHA256
    assert isinstance(alignment.rec17_compliant, bool)
    assert isinstance(alignment.rgk18_compliant, bool)
    assert 0.0 <= alignment.ethical_score <= 1.0
    assert 0.0 <= alignment.governance_score <= 1.0
    assert isinstance(alignment.violations, list)
    assert isinstance(alignment.recommendations, list)

    # With good inputs, should be compliant
    assert alignment.rec17_compliant is True
    assert alignment.rgk18_compliant is True
    assert alignment.ethical_score >= 0.6
    assert alignment.governance_score >= 0.6


def test_phase19_scenario_simulation():
    """Test deterministic scenario simulation."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    scenario = result.scenario_map
    assert len(scenario.scenario_id) == 64  # SHA256
    assert len(scenario.steps) == 3  # Always 3 steps
    assert scenario.trajectory_type in ["stable", "improving", "degrading"]
    assert isinstance(scenario.reversibility, bool)

    # Check each step
    for i, step in enumerate(scenario.steps, 1):
        assert step.step_number == i
        assert len(step.state_vector) > 0
        assert step.risk_level in ["none", "low", "moderate", "high"]

        # Check state vector has expected keys
        assert "coherence" in step.state_vector
        assert "ethical" in step.state_vector
        assert "governance" in step.state_vector


def test_phase19_aei_result_structure():
    """Test final AEI-19 result structure."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    aei = result.aei19_result
    assert len(aei.result_id) == 64  # SHA256
    assert len(aei.explanation) > 0
    assert isinstance(aei.structured_packet, dict)
    assert isinstance(aei.counterfactuals, list)
    assert isinstance(aei.ethical_basis, dict)
    assert isinstance(aei.governance_basis, dict)
    assert len(aei.determinism_signature) == 64  # SHA256
    assert len(aei.reversibility_protocol) > 0

    # Check structured packet structure
    packet = aei.structured_packet
    assert "uif_summary" in packet
    assert "insights" in packet
    assert "compliance" in packet
    assert "scenario" in packet

    # Check ethical basis
    assert "global_ethics_score" in aei.ethical_basis
    assert "rec17_compliant" in aei.ethical_basis

    # Check governance basis
    assert "governance_score" in aei.governance_basis
    assert "rgk18_compliant" in aei.governance_basis


def test_phase19_determinism():
    """Test that Phase 19 produces deterministic outputs."""
    phase_inputs = _create_phase_inputs_fixture()

    # Run twice with same inputs
    service1 = Phase19Service()
    result1 = service1.run_applied_intelligence(phase_inputs)

    service2 = Phase19Service()
    result2 = service2.run_applied_intelligence(phase_inputs)

    # Compare key deterministic outputs
    assert result1.uif_19_state.uif_id == result2.uif_19_state.uif_id
    assert len(result1.insight_packets) == len(result2.insight_packets)
    assert (
        result1.alignment_report.alignment_id == result2.alignment_report.alignment_id
    )
    assert result1.scenario_map.scenario_id == result2.scenario_map.scenario_id
    assert (
        result1.aei19_result.determinism_signature
        == result2.aei19_result.determinism_signature
    )

    # Field vectors should be identical
    for key in result1.uif_19_state.field_vector:
        assert (
            result1.uif_19_state.field_vector[key]
            == result2.uif_19_state.field_vector[key]
        )


def test_phase19_dry_run_default():
    """Test that dry_run is True by default."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    assert result.provenance["dry_run"] is True
    assert result.provenance["auto_apply"] is False


def test_phase19_auto_apply_flag():
    """Test auto_apply flag in provenance."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(
        phase_inputs, dry_run=False, auto_apply=True
    )

    assert result.provenance["dry_run"] is False
    assert result.provenance["auto_apply"] is True


def test_phase19_missing_phase_inputs():
    """Test that missing phase inputs raise ValueError."""
    service = Phase19Service()

    # Missing phase17
    incomplete_inputs = _create_phase_inputs_fixture()
    del incomplete_inputs["phase17"]

    with pytest.raises(ValueError, match="Missing required phase inputs"):
        service.run_applied_intelligence(incomplete_inputs)


def test_phase19_invalid_phase17_format():
    """Test that invalid Phase 17 format raises ValueError."""
    service = Phase19Service()

    inputs = _create_phase_inputs_fixture()
    # Remove required field
    del inputs["phase17"]["global_ethics_score"]

    with pytest.raises(ValueError, match="global_ethics_score"):
        service.run_applied_intelligence(inputs)


def test_phase19_invalid_phase18_format():
    """Test that invalid Phase 18 format raises ValueError."""
    service = Phase19Service()

    inputs = _create_phase_inputs_fixture()
    # Remove required field
    del inputs["phase18"]["score"]

    with pytest.raises(ValueError, match="score"):
        service.run_applied_intelligence(inputs)


def test_phase19_low_scores_scenario():
    """Test Phase 19 with low compliance scores."""
    service = Phase19Service()

    # Create inputs with low scores
    inputs = _create_phase_inputs_fixture()
    inputs["phase17"]["global_ethics_score"] = 0.45
    inputs["phase18"]["score"] = 0.40

    result = service.run_applied_intelligence(inputs)

    # Should still complete but flag issues
    alignment = result.alignment_report
    assert alignment.rec17_compliant is False
    assert alignment.rgk18_compliant is False
    assert len(alignment.violations) > 0 or len(alignment.recommendations) > 0


def test_phase19_ethical_violations():
    """Test Phase 19 with ethical violations."""
    service = Phase19Service()

    inputs = _create_phase_inputs_fixture()
    inputs["phase17"]["governance_invariants"]["invariant_violations"] = [
        "voluntary_consent",
        "human_primacy",
    ]

    result = service.run_applied_intelligence(inputs)

    alignment = result.alignment_report
    assert alignment.rec17_compliant is False
    assert len(alignment.violations) > 0
    assert any("voluntary_consent" in v for v in alignment.violations)


def test_phase19_policy_violations():
    """Test Phase 19 with governance policy violations."""
    service = Phase19Service()

    inputs = _create_phase_inputs_fixture()
    # Use dict format for policy violation (supports both dict and object)
    mock_violation = {
        "severity": "high",
        "policy_id": "test-policy-001",
    }
    inputs["phase18"]["policy_violations"] = [mock_violation]

    result = service.run_applied_intelligence(inputs)

    alignment = result.alignment_report
    assert alignment.rgk18_compliant is False
    assert len(alignment.violations) > 0


def test_phase19_provenance_metadata():
    """Test that provenance metadata is complete."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    prov = result.provenance
    assert len(prov["input_hash"]) == 64  # SHA256
    assert prov["service_version"] == "aei19-1.0.0"
    assert "timestamp" in prov
    assert prov["determinism_guaranteed"] is True
    assert prov["reversibility_supported"] is True
    assert len(prov["phases_integrated"]) == 7


def test_phase19_explanation_narrative():
    """Test that explanation narrative is comprehensive."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    explanation = result.aei19_result.explanation
    # Check for key sections
    assert "Applied Emergent Intelligence" in explanation
    assert "System State" in explanation
    assert "Key Insights" in explanation
    assert "Compliance Status" in explanation
    assert "Forward Projection" in explanation
    assert "Recommendations" in explanation


def test_phase19_counterfactuals_generated():
    """Test that counterfactual scenarios are generated."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    counterfactuals = result.aei19_result.counterfactuals
    assert isinstance(counterfactuals, list)
    # Should have at least some counterfactuals with high scores
    assert len(counterfactuals) > 0


def test_phase19_reversibility_protocol():
    """Test reversibility protocol generation."""
    service = Phase19Service()
    phase_inputs = _create_phase_inputs_fixture()

    result = service.run_applied_intelligence(phase_inputs)

    protocol = result.aei19_result.reversibility_protocol
    assert "Reversibility Protocol" in protocol
    assert "Status:" in protocol
    assert "Compliance Requirements" in protocol
