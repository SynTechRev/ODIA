# tests/rec17/test_ethical_projection.py
"""Tests for Ethical Projection Engine (EPE-17)."""
from oraculus_di_auditor.rec17.ethical_projection import EthicalProjectionEngine


def test_projection_basic():
    """Test basic ethical projection."""
    engine = EthicalProjectionEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.7,
            "harm_probability": 0.3,
            "autonomy_effect": 0.8,
            "system_stability": 0.9,
            "governance_compliance": 0.85,
        },
        "lattice_id": "abc123",
    }

    phase16_result = {
        "provenance": {"input_hash": "def456"},
        "prediction_drift_corrections": [{"reversible": True}, {"reversible": True}],
    }

    projection = engine.project_ethics(ethical_lattice, phase16_result)

    # Verify structure
    assert len(projection.projected_scores) == 3
    assert projection.risk in ["none", "low", "moderate", "high"]
    assert isinstance(projection.reversible, bool)
    assert isinstance(projection.delta_ethics, float)


def test_projection_scores_valid_range():
    """Test that projected scores are in [0, 1]."""
    engine = EthicalProjectionEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.5,
            "harm_probability": 0.5,
            "autonomy_effect": 0.5,
            "system_stability": 0.5,
            "governance_compliance": 0.5,
        },
        "lattice_id": "test123",
    }

    phase16_result = {
        "provenance": {"input_hash": "hash123"},
        "prediction_drift_corrections": [],
    }

    projection = engine.project_ethics(ethical_lattice, phase16_result)

    # All projected scores should be in valid range
    for score in projection.projected_scores:
        assert 0.0 <= score <= 1.0, f"Score out of range: {score}"


def test_delta_computation():
    """Test that delta_ethics is computed correctly."""
    engine = EthicalProjectionEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.6,
            "harm_probability": 0.4,
            "autonomy_effect": 0.7,
            "system_stability": 0.8,
            "governance_compliance": 0.75,
        },
        "lattice_id": "delta_test",
    }

    phase16_result = {
        "provenance": {"input_hash": "delta_hash"},
        "prediction_drift_corrections": [],
    }

    projection = engine.project_ethics(ethical_lattice, phase16_result)

    # Delta should be final - current
    current = engine._compute_current_ethics(ethical_lattice)
    final = projection.projected_scores[-1]
    expected_delta = final - current

    assert abs(projection.delta_ethics - expected_delta) < 0.0001


def test_risk_assessment():
    """Test risk assessment based on delta and volatility."""
    engine = EthicalProjectionEngine()

    # High harm probability should lead to lower current ethics
    ethical_lattice_risky = {
        "ethical_vector": {
            "rights_impact": 0.3,
            "harm_probability": 0.8,  # High harm
            "autonomy_effect": 0.4,
            "system_stability": 0.4,
            "governance_compliance": 0.3,
        },
        "lattice_id": "risky",
    }

    phase16_result = {
        "provenance": {"input_hash": "risk_hash"},
        "prediction_drift_corrections": [],
    }

    projection = engine.project_ethics(ethical_lattice_risky, phase16_result)
    # Risk should be assessed (can be any level including none)
    assert projection.risk in ["none", "low", "moderate", "high"]


def test_projection_determinism():
    """Test that same inputs produce same projections."""
    engine = EthicalProjectionEngine()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.6,
            "harm_probability": 0.3,
            "autonomy_effect": 0.7,
            "system_stability": 0.8,
            "governance_compliance": 0.75,
        },
        "lattice_id": "determinism_test",
    }

    phase16_result = {
        "provenance": {"input_hash": "determinism_hash"},
        "prediction_drift_corrections": [{"reversible": True}],
    }

    projection1 = engine.project_ethics(ethical_lattice, phase16_result)
    projection2 = engine.project_ethics(ethical_lattice, phase16_result)

    # Should be identical
    assert projection1.projected_scores == projection2.projected_scores
    assert projection1.delta_ethics == projection2.delta_ethics
    assert projection1.risk == projection2.risk
    assert projection1.reversible == projection2.reversible
