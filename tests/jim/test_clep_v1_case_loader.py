"""
Tests for CLEP-v1 Case Law Expansion - Case Loader Schema Validation.
"""

import pytest

from scripts.jim.jim_case_loader import JIMCaseLoader


class TestCLEPv1CaseLoading:
    """Test loading and validation of CLEP-v1 expanded case database."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader with CLEP-v1 cases."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_total_case_count_increased(self, loaded_loader):
        """Test that case count increased from baseline 24 to at least 44."""
        assert len(loaded_loader.scotus_index["cases"]) >= 44

    def test_new_doctrines_added(self, loaded_loader):
        """Test that new doctrines are present in index."""
        doctrines = loaded_loader.scotus_index["metadata"]["doctrinal_categories"]
        assert "constitutional_torts" in doctrines
        assert "property_rights" in doctrines
        assert "free_movement" in doctrines

    def test_temporal_range_extended(self, loaded_loader):
        """Test temporal range covers 1803-2024 (updated by CLEP-v2)."""
        assert loaded_loader.scotus_index["metadata"]["temporal_range"] == "1803-2024"


class TestCLEPv1NewCases:
    """Test specific new cases from CLEP-v1."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_coffin_v_united_states_loaded(self, loaded_loader):
        """Test Coffin v. United States (1895) loaded correctly."""
        case = loaded_loader.get_case_by_id("coffin_v_united_states_1895")
        assert case is not None
        assert case["name"] == "Coffin v. United States"
        assert case["year"] == 1895
        assert case["doctrine"] == "due_process"
        assert "presumption_of_innocence" in case["issue_tags"]

    def test_silverthorne_lumber_loaded(self, loaded_loader):
        """Test Silverthorne Lumber (1920) fruit of poisonous tree case."""
        case = loaded_loader.get_case_by_id("silverthorne_lumber_v_united_states_1920")
        assert case is not None
        assert case["doctrine"] == "fourth_amendment"
        assert "fruit_of_poisonous_tree" in case["issue_tags"]
        assert case["doctrinal_weight"] >= 0.85

    def test_terry_v_ohio_loaded(self, loaded_loader):
        """Test Terry v. Ohio (1968) stop and frisk case."""
        case = loaded_loader.get_case_by_id("terry_v_ohio_1968")
        assert case is not None
        assert "stop_and_frisk" in case["issue_tags"]
        assert "reasonable_suspicion" in case["issue_tags"]
        assert case["doctrinal_weight"] >= 0.90

    def test_riley_v_california_digital_privacy(self, loaded_loader):
        """Test Riley v. California (2014) digital privacy case."""
        case = loaded_loader.get_case_by_id("riley_v_california_2014")
        assert case is not None
        assert "digital_privacy" in case["issue_tags"]
        assert "cell_phone_search" in case["issue_tags"]
        assert case["year"] == 2014

    def test_trump_v_united_states_2024(self, loaded_loader):
        """Test Trump v. United States (2024) presidential immunity case."""
        case = loaded_loader.get_case_by_id("trump_v_united_states_2024")
        assert case is not None
        assert case["doctrine"] == "separation_of_powers"
        assert "presidential_immunity" in case["issue_tags"]
        assert case["year"] == 2024

    def test_graham_v_connor_use_of_force(self, loaded_loader):
        """Test Graham v. Connor (1989) excessive force case."""
        case = loaded_loader.get_case_by_id("graham_v_connor_1989")
        assert case is not None
        assert "excessive_force" in case["issue_tags"]
        assert "police_accountability" in case["issue_tags"]

    def test_shapiro_v_thompson_travel(self, loaded_loader):
        """Test Shapiro v. Thompson (1969) right to travel case."""
        case = loaded_loader.get_case_by_id("shapiro_v_thompson_1969")
        assert case is not None
        assert case["doctrine"] == "free_movement"
        assert "right_to_travel" in case["issue_tags"]


class TestCLEPv1SchemaValidation:
    """Test schema validation for CLEP-v1 cases."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_all_cases_have_required_fields(self, loaded_loader):
        """Test all cases have required fields from schema."""
        required_fields = [
            "case_id",
            "name",
            "citation",
            "year",
            "doctrine",
            "summary",
            "holding",
            "issue_tags",
            "doctrinal_weight",
            "constitutional_basis",
            "relevance_to_audit",
        ]

        for case in loaded_loader.scotus_index["cases"]:
            for field in required_fields:
                assert field in case, f"Case {case.get('case_id')} missing {field}"

    def test_new_cases_have_extended_metadata(self, loaded_loader):
        """Test new cases include extended metadata fields."""
        new_case_ids = [
            "coffin_v_united_states_1895",
            "riley_v_california_2014",
            "trump_v_united_states_2024",
        ]

        for case_id in new_case_ids:
            case = loaded_loader.get_case_by_id(case_id)
            assert case is not None
            assert "procedural_posture" in case
            assert "relevance_score" in case
            assert case["relevance_score"] >= 0.0
            assert case["relevance_score"] <= 1.0

    def test_doctrinal_weights_valid_range(self, loaded_loader):
        """Test all doctrinal weights are between 0 and 1."""
        for case in loaded_loader.scotus_index["cases"]:
            weight = case.get("doctrinal_weight", 0)
            assert (
                0.0 <= weight <= 1.0
            ), f"Case {case['case_id']} has invalid weight {weight}"

    def test_years_chronologically_valid(self, loaded_loader):
        """Test all case years are valid historical dates."""
        for case in loaded_loader.scotus_index["cases"]:
            year = case.get("year")
            assert (
                1789 <= year <= 2025
            ), f"Case {case['case_id']} has invalid year {year}"


class TestCLEPv1DoctrineIndexing:
    """Test doctrine indexing with new CLEP-v1 doctrines."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_constitutional_torts_cases_indexed(self, loaded_loader):
        """Test constitutional torts cases properly indexed."""
        cases = loaded_loader.get_cases_by_doctrine("constitutional_torts")
        assert len(cases) >= 1
        # Sanders v. English should be in this category
        case_names = [c["name"] for c in cases]
        assert "Sanders v. English" in case_names

    def test_property_rights_cases_indexed(self, loaded_loader):
        """Test property rights cases properly indexed."""
        cases = loaded_loader.get_cases_by_doctrine("property_rights")
        assert len(cases) >= 1

    def test_free_movement_cases_indexed(self, loaded_loader):
        """Test free movement cases properly indexed."""
        cases = loaded_loader.get_cases_by_doctrine("free_movement")
        assert len(cases) >= 2
        # Should include Shapiro and Saenz
        case_names = [c["name"] for c in cases]
        assert "Shapiro v. Thompson" in case_names
        assert "Saenz v. Roe" in case_names

    def test_fourth_amendment_expansion(self, loaded_loader):
        """Test Fourth Amendment cases expanded significantly."""
        cases = loaded_loader.get_cases_by_doctrine("fourth_amendment")
        # Should have at least 10 cases now (was ~5 before)
        assert len(cases) >= 10

        # Check for key new cases
        case_names = [c["name"] for c in cases]
        assert "Terry v. Ohio" in case_names
        assert "Riley v. California" in case_names
        assert "Silverthorne Lumber Co. v. United States" in case_names


class TestCLEPv1SearchByTag:
    """Test searching cases by new issue tags."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_search_digital_privacy_tag(self, loaded_loader):
        """Test searching for digital privacy cases."""
        cases = loaded_loader.search_cases_by_tag("digital_privacy")
        assert len(cases) >= 1
        case_names = [c["name"] for c in cases]
        assert "Riley v. California" in case_names

    def test_search_fruit_of_poisonous_tree(self, loaded_loader):
        """Test searching for fruit of poisonous tree cases."""
        cases = loaded_loader.search_cases_by_tag("fruit_of_poisonous_tree")
        assert len(cases) >= 2
        # Should include Silverthorne and Nardone

    def test_search_qualified_immunity(self, loaded_loader):
        """Test searching for qualified immunity cases."""
        cases = loaded_loader.search_cases_by_tag("qualified_immunity")
        assert len(cases) >= 1

    def test_search_right_to_travel(self, loaded_loader):
        """Test searching for right to travel cases."""
        cases = loaded_loader.search_cases_by_tag("right_to_travel")
        assert len(cases) >= 2

    def test_search_presumption_of_innocence(self, loaded_loader):
        """Test searching for presumption of innocence cases."""
        cases = loaded_loader.search_cases_by_tag("presumption_of_innocence")
        assert len(cases) >= 1
        case_names = [c["name"] for c in cases]
        assert "Coffin v. United States" in case_names
