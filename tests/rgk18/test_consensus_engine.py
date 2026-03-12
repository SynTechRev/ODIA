# tests/rgk18/test_consensus_engine.py
"""Tests for consensus engine."""

from oraculus_di_auditor.rgk18.consensus_engine import ConsensusEngine


def test_consensus_engine_default_weights():
    """Test consensus engine with default weights."""
    engine = ConsensusEngine()

    # Check weights are normalized
    assert abs(sum(engine.weights.values()) - 1.0) < 0.001


def test_consensus_engine_custom_weights():
    """Test consensus engine with custom weights."""
    custom_weights = {
        "scalar_harmonics": 0.5,
        "qdcl_probability": 0.3,
        "temporal_stability": 0.2,
    }
    engine = ConsensusEngine(weights=custom_weights)

    # Weights should be normalized to sum to 1.0
    assert abs(sum(engine.weights.values()) - 1.0) < 0.001


def test_aggregate_full_evidence():
    """Test aggregation with complete evidence."""
    engine = ConsensusEngine()

    evidence = {
        "scalar_harmonics": 0.8,
        "qdcl_probability": 0.9,
        "temporal_stability": 0.7,
        "ethical_score": 0.85,
        "self_healing_risk": 0.6,
    }

    score = engine.aggregate(evidence)

    assert 0.0 <= score.score <= 1.0
    assert len(score.components) == 5
    assert score.components["scalar_harmonics"] == 0.8
    # Score should be weighted average
    expected_score = 0.8 * 0.25 + 0.9 * 0.25 + 0.7 * 0.20 + 0.85 * 0.20 + 0.6 * 0.10
    assert abs(score.score - expected_score) < 0.001


def test_aggregate_partial_evidence():
    """Test aggregation with missing evidence (defaults to neutral)."""
    engine = ConsensusEngine()

    evidence = {
        "scalar_harmonics": 0.8,
        "qdcl_probability": None,  # Missing
        "temporal_stability": 0.7,
        # ethical_score and self_healing_risk completely missing
    }

    score = engine.aggregate(evidence)

    assert 0.0 <= score.score <= 1.0
    # Missing evidence should default to 0.5 (neutral)
    assert score.components["qdcl_probability"] == 0.5
    assert score.components["ethical_score"] == 0.5
    assert score.components["self_healing_risk"] == 0.5


def test_aggregate_bounds_checking():
    """Test that evidence values are clamped to [0.0, 1.0]."""
    engine = ConsensusEngine()

    evidence = {
        "scalar_harmonics": 1.5,  # Above 1.0
        "qdcl_probability": -0.5,  # Below 0.0
        "temporal_stability": 0.7,
        "ethical_score": 0.85,
        "self_healing_risk": 0.6,
    }

    score = engine.aggregate(evidence)

    # Should be clamped
    assert score.components["scalar_harmonics"] == 1.0
    assert score.components["qdcl_probability"] == 0.0
    assert 0.0 <= score.score <= 1.0


def test_deterministic_aggregation():
    """Test that aggregation is deterministic."""
    engine = ConsensusEngine()

    evidence = {
        "scalar_harmonics": 0.75,
        "qdcl_probability": 0.82,
        "temporal_stability": 0.68,
        "ethical_score": 0.91,
        "self_healing_risk": 0.55,
    }

    # Run aggregation multiple times
    scores = [engine.aggregate(evidence) for _ in range(3)]

    # All scores should be identical
    for s in scores[1:]:
        assert s.score == scores[0].score
        assert s.components == scores[0].components


def test_update_weights():
    """Test updating consensus engine weights."""
    engine = ConsensusEngine()

    initial_score = engine.aggregate(
        {
            "scalar_harmonics": 0.8,
            "qdcl_probability": 0.2,
            "temporal_stability": 0.5,
            "ethical_score": 0.5,
            "self_healing_risk": 0.5,
        }
    )

    # Update weights to favor scalar_harmonics
    engine.update_weights({"scalar_harmonics": 1.0, "qdcl_probability": 0.0})

    updated_score = engine.aggregate(
        {
            "scalar_harmonics": 0.8,
            "qdcl_probability": 0.2,
            "temporal_stability": 0.5,
            "ethical_score": 0.5,
            "self_healing_risk": 0.5,
        }
    )

    # Score should be different and closer to scalar_harmonics value
    assert updated_score.score != initial_score.score


def test_zero_evidence_all_neutral():
    """Test aggregation when all evidence is neutral."""
    engine = ConsensusEngine()

    evidence = {
        "scalar_harmonics": 0.5,
        "qdcl_probability": 0.5,
        "temporal_stability": 0.5,
        "ethical_score": 0.5,
        "self_healing_risk": 0.5,
    }

    score = engine.aggregate(evidence)

    # Should result in 0.5 (neutral) composite score
    assert abs(score.score - 0.5) < 0.001


def test_extreme_evidence_high():
    """Test aggregation with all high evidence."""
    engine = ConsensusEngine()

    evidence = {
        "scalar_harmonics": 1.0,
        "qdcl_probability": 1.0,
        "temporal_stability": 1.0,
        "ethical_score": 1.0,
        "self_healing_risk": 1.0,
    }

    score = engine.aggregate(evidence)

    # Should result in 1.0 composite score
    assert abs(score.score - 1.0) < 0.001


def test_extreme_evidence_low():
    """Test aggregation with all low evidence."""
    engine = ConsensusEngine()

    evidence = {
        "scalar_harmonics": 0.0,
        "qdcl_probability": 0.0,
        "temporal_stability": 0.0,
        "ethical_score": 0.0,
        "self_healing_risk": 0.0,
    }

    score = engine.aggregate(evidence)

    # Should result in 0.0 composite score
    assert abs(score.score - 0.0) < 0.001
