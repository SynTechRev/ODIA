# tests/rec17/test_governance_invariants.py
"""Tests for Governance Invariant Engine (GIE-17)."""
from oraculus_di_auditor.rec17.governance_invariants import GovernanceInvariantEngine


def test_invariants_basic():
    """Test basic invariant checking."""
    engine = GovernanceInvariantEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.6,
            "harm_probability": 0.3,
            "autonomy_effect": 0.7,
            "system_stability": 0.8,
            "governance_compliance": 0.75,
        },
    }

    legal_map = {
        "constitutional_flags": [],
        "human_rights_flags": [],
        "compliance_score": 0.8,
    }

    phase16_result = {}

    invariants = engine.check_invariants(ethical_lattice, legal_map, phase16_result)

    # Verify structure
    assert isinstance(invariants.invariant_violations, list)
    assert 0.0 <= invariants.alignment_score <= 1.0


def test_voluntary_consent_violation():
    """Test detection of voluntary consent violation."""
    engine = GovernanceInvariantEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.5,
            "harm_probability": 0.3,
            "autonomy_effect": 0.5,  # Below voluntary_consent threshold (0.7)
            "system_stability": 0.7,
            "governance_compliance": 0.6,
        },
    }

    legal_map = {"constitutional_flags": [], "compliance_score": 0.6}
    phase16_result = {}

    invariants = engine.check_invariants(ethical_lattice, legal_map, phase16_result)

    # Should detect voluntary_consent violation
    assert "voluntary_consent" in invariants.invariant_violations


def test_proportionality_violation():
    """Test detection of proportionality violation (high harm)."""
    engine = GovernanceInvariantEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.6,
            "harm_probability": 0.7,  # High harm > 0.5 threshold
            "autonomy_effect": 0.8,
            "system_stability": 0.7,
            "governance_compliance": 0.7,
        },
    }

    legal_map = {"constitutional_flags": [], "compliance_score": 0.7}
    phase16_result = {}

    invariants = engine.check_invariants(ethical_lattice, legal_map, phase16_result)

    # Should detect proportionality violation
    assert "proportionality" in invariants.invariant_violations


def test_no_violations_high_alignment():
    """Test case with no violations yields high alignment."""
    engine = GovernanceInvariantEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.8,
            "harm_probability": 0.2,
            "autonomy_effect": 0.9,
            "system_stability": 0.9,
            "governance_compliance": 0.9,
        },
    }

    legal_map = {"constitutional_flags": [], "compliance_score": 0.9}
    phase16_result = {}

    invariants = engine.check_invariants(ethical_lattice, legal_map, phase16_result)

    # Should have no violations
    assert len(invariants.invariant_violations) == 0
    # Should have high alignment
    assert invariants.alignment_score >= 0.8


def test_alignment_score_with_violations():
    """Test that violations reduce alignment score."""
    engine = GovernanceInvariantEngine()

    # Scenario with multiple violations
    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.3,  # Low - may trigger non_discrimination
            "harm_probability": 0.7,  # High - triggers proportionality
            "autonomy_effect": 0.3,  # Low - triggers voluntary_consent and non_coercion
            "system_stability": 0.5,
            "governance_compliance": 0.4,  # Low - triggers human_primacy, transparency
        },
    }

    legal_map = {"constitutional_flags": [], "compliance_score": 0.4}
    phase16_result = {}

    invariants = engine.check_invariants(ethical_lattice, legal_map, phase16_result)

    # Should have violations
    assert len(invariants.invariant_violations) > 0
    # Alignment should be reduced
    assert invariants.alignment_score < 0.6


def test_invariants_determinism():
    """Test determinism of invariant checking."""
    engine = GovernanceInvariantEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.6,
            "harm_probability": 0.4,
            "autonomy_effect": 0.7,
            "system_stability": 0.8,
            "governance_compliance": 0.75,
        },
    }

    legal_map = {"constitutional_flags": [], "compliance_score": 0.75}
    phase16_result = {}

    invariants1 = engine.check_invariants(ethical_lattice, legal_map, phase16_result)
    invariants2 = engine.check_invariants(ethical_lattice, legal_map, phase16_result)

    # Should be identical
    assert invariants1.invariant_violations == invariants2.invariant_violations
    assert invariants1.alignment_score == invariants2.alignment_score
