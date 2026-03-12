# tests/rec17/test_phase17_service.py
"""Tests for Phase17Service orchestrator."""

from oraculus_di_auditor.rec17.rec17_service import Phase17Service


def _load_phase16_fixture():
    """Load Phase 16 result fixture."""
    # Create mock Phase 16 result
    return {
        "recursive_integrity_score": 0.85,
        "meta_harmonic_field": {"0": 1.0, "1": 0.9, "2": 0.95},
        "emergent_pattern_index": {"pattern1": 0.8, "pattern2": 0.7},
        "prediction_drift_corrections": [
            {
                "id": "1",
                "description": "Test action",
                "reversible": True,
                "risk_level": "low",
            },
            {
                "id": "2",
                "description": "Another action",
                "reversible": True,
                "risk_level": "low",
            },
        ],
        "self_reflection_report": {"status": "ok"},
        "provenance": {
            "input_hash": "abc123def456",
            "service_version": "emcs16-0.1.0",
        },
    }


def test_phase17_run_basic():
    """Test basic Phase 17 execution."""
    service = Phase17Service()
    phase16_result = _load_phase16_fixture()

    result = service.run_ethical_analysis(phase16_result)

    # Verify all required fields present
    assert "ethical_lattice" in result
    assert "ethical_projection" in result
    assert "legal_map" in result
    assert "governance_invariants" in result
    assert "global_ethics_score" in result
    assert "action_suggestions" in result
    assert "provenance" in result
    assert "timestamp" in result


def test_phase17_all_components_populated():
    """Test that all components produce valid outputs."""
    service = Phase17Service()
    phase16_result = _load_phase16_fixture()

    result = service.run_ethical_analysis(phase16_result)

    # Ethical lattice
    lattice = result["ethical_lattice"]
    assert "ethical_vector" in lattice
    assert "primary_ethic" in lattice
    assert "lattice_id" in lattice
    assert len(lattice["lattice_id"]) == 64  # SHA256

    # Ethical projection
    projection = result["ethical_projection"]
    assert "projected_scores" in projection
    assert len(projection["projected_scores"]) == 3
    assert "delta_ethics" in projection
    assert projection["risk"] in ["none", "low", "moderate", "high"]
    assert isinstance(projection["reversible"], bool)

    # Legal map
    legal = result["legal_map"]
    assert "constitutional_flags" in legal
    assert "human_rights_flags" in legal
    assert 0.0 <= legal["compliance_score"] <= 1.0

    # Governance invariants
    governance = result["governance_invariants"]
    assert "invariant_violations" in governance
    assert 0.0 <= governance["alignment_score"] <= 1.0

    # Global score
    assert 0.0 <= result["global_ethics_score"] <= 1.0

    # Action suggestions
    assert isinstance(result["action_suggestions"], list)

    # Provenance
    prov = result["provenance"]
    assert "input_hash" in prov
    assert "service_version" in prov
    assert prov["service_version"].startswith("rec17")


def test_phase17_determinism():
    """Test that same input produces same output."""
    service = Phase17Service()
    phase16_result = _load_phase16_fixture()

    result1 = service.run_ethical_analysis(phase16_result)
    result2 = service.run_ethical_analysis(phase16_result)

    # Compare all fields except timestamp
    for key in result1.keys():
        if key != "timestamp":
            if key == "provenance":
                # Compare provenance without timestamp
                for prov_key in result1["provenance"].keys():
                    if prov_key != "timestamp":
                        assert (
                            result1["provenance"][prov_key]
                            == result2["provenance"][prov_key]
                        ), f"Mismatch in provenance.{prov_key}"
            else:
                assert result1[key] == result2[key], f"Mismatch in {key}"


def test_phase17_dry_run_default():
    """Test that dry_run defaults to True."""
    service = Phase17Service()
    phase16_result = _load_phase16_fixture()

    result = service.run_ethical_analysis(phase16_result)

    # Should have dry_run in provenance
    assert result["provenance"]["dry_run"] is True

    # Should have dry-run message in suggestions
    suggestions_str = "|".join(result["action_suggestions"])
    assert "dry-run" in suggestions_str.lower()


def test_phase17_auto_apply_flag():
    """Test auto_apply flag behavior."""
    service = Phase17Service()
    phase16_result = _load_phase16_fixture()

    # Test with auto_apply=False (default)
    result1 = service.run_ethical_analysis(phase16_result, auto_apply=False)
    assert result1["provenance"]["auto_apply"] is False

    # Test with auto_apply=True
    result2 = service.run_ethical_analysis(phase16_result, auto_apply=True)
    assert result2["provenance"]["auto_apply"] is True


def test_phase17_action_suggestions_populated():
    """Test that action suggestions are generated."""
    service = Phase17Service()
    phase16_result = _load_phase16_fixture()

    result = service.run_ethical_analysis(phase16_result)

    # Should have at least some suggestions
    assert len(result["action_suggestions"]) > 0


def test_phase17_global_ethics_score_calculation():
    """Test that global ethics score is properly calculated."""
    service = Phase17Service()

    # Test with good ethical indicators
    phase16_good = {
        "recursive_integrity_score": 0.95,
        "meta_harmonic_field": {"0": 1.0, "1": 0.98},
        "emergent_pattern_index": {},
        "prediction_drift_corrections": [{"reversible": True}],
        "provenance": {"input_hash": "good"},
    }

    result_good = service.run_ethical_analysis(phase16_good)
    score_good = result_good["global_ethics_score"]

    # Test with poor ethical indicators
    phase16_poor = {
        "recursive_integrity_score": 0.3,
        "meta_harmonic_field": {"0": 0.2},
        "emergent_pattern_index": {"p1": 1.0, "p2": 1.0, "p3": 1.0},
        "prediction_drift_corrections": [{"reversible": False}],
        "provenance": {"input_hash": "poor"},
    }

    result_poor = service.run_ethical_analysis(phase16_poor)
    score_poor = result_poor["global_ethics_score"]

    # Good indicators should yield higher score
    assert score_good > score_poor
