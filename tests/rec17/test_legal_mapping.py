# tests/rec17/test_legal_mapping.py
"""Tests for Legal & Constitutional Mapping (LCM-17)."""
from oraculus_di_auditor.rec17.legal_mapping import LegalConstitutionalMapper


def test_legal_mapping_basic():
    """Test basic legal mapping."""
    mapper = LegalConstitutionalMapper()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.6,
            "harm_probability": 0.4,
            "autonomy_effect": 0.7,
            "system_stability": 0.8,
            "governance_compliance": 0.75,
        },
    }

    ethical_projection = {"risk": "low"}

    phase16_result = {"provenance": {"input_hash": "test"}}

    legal_map = mapper.map_legal_concerns(
        ethical_lattice, ethical_projection, phase16_result
    )

    # Verify structure
    assert isinstance(legal_map.constitutional_flags, list)
    assert isinstance(legal_map.human_rights_flags, list)
    assert 0.0 <= legal_map.compliance_score <= 1.0


def test_constitutional_flags_low_rights():
    """Test constitutional flags when rights impact is low."""
    mapper = LegalConstitutionalMapper()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.2,  # Low rights impact
            "harm_probability": 0.3,
            "autonomy_effect": 0.2,  # Low autonomy
            "system_stability": 0.5,
            "governance_compliance": 0.5,
        },
    }

    ethical_projection = {"risk": "low"}
    phase16_result = {}

    legal_map = mapper.map_legal_concerns(
        ethical_lattice, ethical_projection, phase16_result
    )

    # Should flag constitutional concerns
    assert len(legal_map.constitutional_flags) > 0
    # Check for specific flags
    flag_str = "|".join(legal_map.constitutional_flags)
    assert "amendment" in flag_str


def test_human_rights_flags_high_harm():
    """Test human rights flags when harm probability is high."""
    mapper = LegalConstitutionalMapper()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.5,
            "harm_probability": 0.7,  # High harm
            "autonomy_effect": 0.5,
            "system_stability": 0.5,
            "governance_compliance": 0.5,
        },
    }

    ethical_projection = {"risk": "moderate"}
    phase16_result = {}

    legal_map = mapper.map_legal_concerns(
        ethical_lattice, ethical_projection, phase16_result
    )

    # Should flag human rights concerns
    assert len(legal_map.human_rights_flags) > 0
    # Should include security concerns
    flag_str = "|".join(legal_map.human_rights_flags)
    assert "udhr" in flag_str


def test_compliance_score_calculation():
    """Test compliance score is calculated correctly."""
    mapper = LegalConstitutionalMapper()

    # Good compliance scenario
    ethical_lattice_good = {
        "ethical_vector": {
            "rights_impact": 0.8,
            "harm_probability": 0.2,
            "autonomy_effect": 0.8,
            "system_stability": 0.9,
            "governance_compliance": 0.9,
        },
    }

    ethical_projection = {"risk": "none"}
    phase16_result = {}

    legal_map = mapper.map_legal_concerns(
        ethical_lattice_good, ethical_projection, phase16_result
    )

    # Should have high compliance
    assert legal_map.compliance_score >= 0.7


def test_legal_mapping_determinism():
    """Test determinism of legal mapping."""
    mapper = LegalConstitutionalMapper()

    ethical_lattice = {
        "ethical_vector": {
            "rights_impact": 0.6,
            "harm_probability": 0.3,
            "autonomy_effect": 0.7,
            "system_stability": 0.8,
            "governance_compliance": 0.75,
        },
    }

    ethical_projection = {"risk": "low"}
    phase16_result = {}

    legal_map1 = mapper.map_legal_concerns(
        ethical_lattice, ethical_projection, phase16_result
    )
    legal_map2 = mapper.map_legal_concerns(
        ethical_lattice, ethical_projection, phase16_result
    )

    # Should be identical
    assert legal_map1.constitutional_flags == legal_map2.constitutional_flags
    assert legal_map1.human_rights_flags == legal_map2.human_rights_flags
    assert legal_map1.compliance_score == legal_map2.compliance_score
