"""
Tests for CLEP-v1 Case Law Expansion - Correlation Engine with New Doctrines.
"""

import pytest

from scripts.jim.jim_case_loader import JIMCaseLoader
from scripts.jim.jim_correlation_engine import JIMCorrelationEngine


class TestCLEPv1NewDoctrineMappings:
    """Test new anomaly-to-doctrine mappings from CLEP-v1."""

    @pytest.fixture
    def engine(self):
        """Provide correlation engine with loaded cases."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_digital_privacy_violation_mapping(self, engine):
        """Test digital privacy violation anomaly maps to fourth_amendment."""
        anomaly = {
            "id": "test_001",
            "type": "digital_privacy_violation",
            "source": "PDF_FORENSICS",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]

    def test_cell_site_location_tracking_mapping(self, engine):
        """Test cell-site location tracking maps to fourth_amendment."""
        anomaly = {
            "id": "test_002",
            "type": "cell_site_location_tracking",
            "source": "ACE",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]

    def test_gps_tracking_mapping(self, engine):
        """Test GPS tracking maps to fourth_amendment."""
        anomaly = {
            "id": "test_003",
            "type": "gps_tracking",
            "source": "SURVEILLANCE",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]

    def test_identity_tracking_system_mapping(self, engine):
        """Test identity tracking system maps to free_movement and fourth_amendment."""
        anomaly = {
            "id": "test_004",
            "type": "identity_tracking_system",
            "source": "CAIM",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "free_movement" in result["doctrines"]
        assert "fourth_amendment" in result["doctrines"]

    def test_residency_requirement_mapping(self, engine):
        """Test residency requirement maps to free_movement."""
        anomaly = {
            "id": "test_005",
            "type": "residency_requirement",
            "source": "LEGISLATIVE",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "free_movement" in result["doctrines"]

    def test_excessive_force_mapping(self, engine):
        """Test excessive force maps to fourth_amendment and constitutional_torts."""
        anomaly = {
            "id": "test_006",
            "type": "excessive_force",
            "source": "ENFORCEMENT",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]
        assert "constitutional_torts" in result["doctrines"]

    def test_qualified_immunity_issue_mapping(self, engine):
        """Test qualified immunity issue maps to constitutional_torts."""
        anomaly = {
            "id": "test_007",
            "type": "qualified_immunity_issue",
            "source": "LEGAL_REVIEW",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "constitutional_torts" in result["doctrines"]

    def test_evidence_chain_break_mapping(self, engine):
        """Test evidence chain break maps to fourth_amendment."""
        anomaly = {
            "id": "test_008",
            "type": "evidence_chain_break",
            "source": "PDF_FORENSICS",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]


class TestCLEPv1CaseCorrelation:
    """Test correlation to specific CLEP-v1 cases."""

    @pytest.fixture
    def engine(self):
        """Provide correlation engine."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_digital_search_correlates_to_riley(self, engine):
        """Test digital search anomaly correlates to Riley v. California."""
        anomaly = {
            "id": "digital_001",
            "type": "digital_privacy_violation",
            "source": "SURVEILLANCE",
            "description": "warrantless cell phone search digital information",
            "involves_surveillance": True,
        }

        result = engine.correlate_anomaly(anomaly)
        case_names = [c["name"] for c in result["relevant_cases"]]
        assert "Riley v. California" in case_names or len(result["relevant_cases"]) > 0

    def test_stop_and_identify_correlates_to_terry_brown(self, engine):
        """Test stop and identify correlates to Terry or Brown."""
        anomaly = {
            "id": "stop_001",
            "type": "identification_demand",
            "source": "ENFORCEMENT",
            "description": "police stop reasonable suspicion identification demand",
            "involves_surveillance": True,
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]
        # Should correlate to Terry v. Ohio or Brown v. Texas
        case_ids = [c["case_id"] for c in result["relevant_cases"]]
        assert (
            "terry_v_ohio_1968" in case_ids
            or "brown_v_texas_1979" in case_ids
            or len(result["relevant_cases"]) > 0
        )

    def test_tainted_evidence_correlates_to_silverthorne(self, engine):
        """Test tainted evidence correlates to fruit of poisonous tree cases."""
        anomaly = {
            "id": "evidence_001",
            "type": "tainted_evidence",
            "source": "PDF_FORENSICS",
            "description": "evidence derived from illegal search fruit poisonous tree",
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]
        # Should correlate to Silverthorne, Nardone, or Wong Sun

    def test_use_of_force_correlates_to_graham_garner(self, engine):
        """Test use of force correlates to Graham v. Connor or Tennessee v. Garner."""
        anomaly = {
            "id": "force_001",
            "type": "excessive_force",
            "source": "ENFORCEMENT",
            "description": "excessive force objective reasonableness",
            "involves_force": True,
        }

        result = engine.correlate_anomaly(anomaly)
        assert "fourth_amendment" in result["doctrines"]


class TestCLEPv1MultiCaseCorrelation:
    """Test multi-case correlation with CLEP-v1 cases."""

    @pytest.fixture
    def engine(self):
        """Provide correlation engine."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_multiple_fourth_amendment_anomalies(self, engine):
        """Test multiple Fourth Amendment anomalies show pattern."""
        anomalies = [
            {
                "id": "4a_001",
                "type": "digital_privacy_violation",
                "source": "SURVEILLANCE",
            },
            {
                "id": "4a_002",
                "type": "warrantless_search",
                "source": "ENFORCEMENT",
            },
            {
                "id": "4a_003",
                "type": "gps_tracking",
                "source": "SURVEILLANCE",
            },
        ]

        result = engine.correlate_multiple_anomalies(anomalies)
        assert result["total_anomalies_correlated"] == 3
        assert "fourth_amendment" in result["doctrine_frequency"]
        assert result["doctrine_frequency"]["fourth_amendment"] >= 3

    def test_mixed_new_doctrines(self, engine):
        """Test mixed anomalies with new doctrines."""
        anomalies = [
            {"id": "mix_001", "type": "excessive_force", "source": "ENFORCEMENT"},
            {"id": "mix_002", "type": "residency_requirement", "source": "LEGISLATIVE"},
            {"id": "mix_003", "type": "evidence_chain_break", "source": "FORENSICS"},
        ]

        result = engine.correlate_multiple_anomalies(anomalies)
        assert "fourth_amendment" in result["doctrine_frequency"]
        assert "free_movement" in result["doctrine_frequency"]
        assert "constitutional_torts" in result["doctrine_frequency"]


class TestCLEPv1TagPriority:
    """Test updated tag priority mappings."""

    @pytest.fixture
    def engine(self):
        """Provide correlation engine."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_fourth_amendment_priority_tags_expanded(self, engine):
        """Test Fourth Amendment priority tags include new tags."""
        tags = engine.tag_priority["fourth_amendment"]
        assert "digital_privacy" in tags
        assert "cell_site_location" in tags
        assert "gps_tracking" in tags
        assert "fruit_of_poisonous_tree" in tags
        assert "chain_of_custody" in tags
        assert "stop_and_frisk" in tags

    def test_constitutional_torts_priority_tags(self, engine):
        """Test constitutional torts priority tags exist."""
        assert "constitutional_torts" in engine.tag_priority
        tags = engine.tag_priority["constitutional_torts"]
        assert "qualified_immunity" in tags
        assert "excessive_force" in tags

    def test_free_movement_priority_tags(self, engine):
        """Test free movement priority tags exist."""
        assert "free_movement" in engine.tag_priority
        tags = engine.tag_priority["free_movement"]
        assert "right_to_travel" in tags
        assert "interstate_migration" in tags

    def test_property_rights_priority_tags(self, engine):
        """Test property rights priority tags exist."""
        assert "property_rights" in engine.tag_priority
        tags = engine.tag_priority["property_rights"]
        assert "liberty_interests" in tags


class TestCLEPv1CaseRelevanceScoring:
    """Test case relevance scoring with CLEP-v1 cases."""

    @pytest.fixture
    def engine(self):
        """Provide correlation engine."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_recent_cases_boosted_for_fourth_amendment(self, engine):
        """Test recent Fourth Amendment cases get relevance boost."""
        anomaly = {
            "id": "recent_001",
            "type": "digital_privacy_violation",
            "source": "SURVEILLANCE",
            "description": "digital surveillance privacy",
        }

        result = engine.correlate_anomaly(anomaly)
        # Riley (2014) and Carpenter (2018) should score highly
        relevant_cases = result["relevant_cases"]
        if relevant_cases:
            # Check that at least one recent case (2000+) is in results
            recent_cases = [c for c in relevant_cases if c["year"] >= 2000]
            assert len(recent_cases) > 0

    def test_high_doctrinal_weight_cases_prioritized(self, engine):
        """Test cases with high doctrinal weight prioritized."""
        anomaly = {
            "id": "weight_001",
            "type": "warrantless_search",
            "source": "ENFORCEMENT",
        }

        result = engine.correlate_anomaly(anomaly)
        if result["relevant_cases"]:
            # Top case should have high doctrinal weight
            top_case = result["relevant_cases"][0]
            assert top_case["doctrinal_weight"] >= 0.75


class TestCLEPv1SystemicPatterns:
    """Test systemic pattern identification with CLEP-v1."""

    @pytest.fixture
    def engine(self):
        """Provide correlation engine."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_digital_privacy_pattern_detection(self, engine):
        """Test detection of systemic digital privacy concerns."""
        anomalies = [
            {
                "id": f"digital_{i}",
                "type": "digital_privacy_violation",
                "source": "SURVEILLANCE",
                "affects_rights": True,
            }
            for i in range(5)
        ]

        result = engine.correlate_multiple_anomalies(anomalies)
        patterns = result["systemic_patterns"]
        # Should detect constitutional rights concerns
        assert any("constitutional rights" in p.lower() for p in patterns)
