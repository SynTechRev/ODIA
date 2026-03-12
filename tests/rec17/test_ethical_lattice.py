# tests/rec17/test_ethical_lattice.py
"""Tests for Ethical Lattice Generator (ELG-17)."""
from oraculus_di_auditor.rec17.ethical_lattice import EthicalLatticeGenerator


def test_lattice_generation_basic():
    """Test basic lattice generation."""
    generator = EthicalLatticeGenerator()

    # Create a mock Phase 16 result
    phase16_result = {
        "recursive_integrity_score": 0.85,
        "meta_harmonic_field": {"0": 1.0, "1": 0.9},
        "emergent_pattern_index": {"pattern1": 0.8},
        "prediction_drift_corrections": [
            {"id": "1", "reversible": True},
            {"id": "2", "reversible": True},
        ],
    }

    lattice = generator.generate_lattice(phase16_result)

    # Verify structure
    assert lattice.ethical_vector is not None
    assert lattice.primary_ethic in generator.ETHICAL_PRINCIPLES
    assert len(lattice.lattice_id) == 64  # SHA256 hex length


def test_ethical_vector_ranges():
    """Test that all ethical vector values are in [0, 1]."""
    generator = EthicalLatticeGenerator()

    phase16_result = {
        "recursive_integrity_score": 0.5,
        "meta_harmonic_field": {"0": 0.8},
        "emergent_pattern_index": {},
        "prediction_drift_corrections": [],
    }

    lattice = generator.generate_lattice(phase16_result)

    # Check all axes are in valid range
    for axis, value in lattice.ethical_vector.items():
        assert 0.0 <= value <= 1.0, f"Axis {axis} out of range: {value}"


def test_primary_ethic_determination():
    """Test primary ethic selection logic."""
    generator = EthicalLatticeGenerator()

    # Test non-maleficence (low harm)
    phase16_result = {
        "recursive_integrity_score": 0.9,  # High integrity = low harm
        "meta_harmonic_field": {"0": 0.8},
        "emergent_pattern_index": {},
        "prediction_drift_corrections": [],
    }
    lattice = generator.generate_lattice(phase16_result)
    assert lattice.primary_ethic in generator.ETHICAL_PRINCIPLES


def test_lattice_determinism():
    """Test that same input produces same lattice."""
    generator = EthicalLatticeGenerator()

    phase16_result = {
        "recursive_integrity_score": 0.7,
        "meta_harmonic_field": {"0": 0.9, "1": 0.8},
        "emergent_pattern_index": {"p1": 0.5},
        "prediction_drift_corrections": [{"id": "1", "reversible": True}],
    }

    lattice1 = generator.generate_lattice(phase16_result)
    lattice2 = generator.generate_lattice(phase16_result)

    # Should be identical
    assert lattice1.lattice_id == lattice2.lattice_id
    assert lattice1.ethical_vector == lattice2.ethical_vector
    assert lattice1.primary_ethic == lattice2.primary_ethic


def test_lattice_id_uniqueness():
    """Test that different inputs produce different lattice IDs."""
    generator = EthicalLatticeGenerator()

    phase16_result1 = {"recursive_integrity_score": 0.5}
    phase16_result2 = {"recursive_integrity_score": 0.8}

    lattice1 = generator.generate_lattice(phase16_result1)
    lattice2 = generator.generate_lattice(phase16_result2)

    # Different inputs should produce different IDs
    assert lattice1.lattice_id != lattice2.lattice_id
