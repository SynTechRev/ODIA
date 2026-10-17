"""
Tests for JIM Case Loader - Supreme Court case law loading and validation.
"""

import pytest

from scripts.jim.jim_case_loader import JIMCaseLoader


class TestJIMCaseLoaderInitialization:
    """Test case loader initialization."""

    def test_loader_initializes_with_default_path(self):
        """Test loader initializes with default cases directory."""
        loader = JIMCaseLoader()
        assert loader.cases_dir.name == "cases"
        assert "legal" in str(loader.cases_dir)

    def test_loader_initializes_with_custom_path(self, tmp_path):
        """Test loader initializes with custom path."""
        custom_dir = tmp_path / "custom_cases"
        custom_dir.mkdir()
        loader = JIMCaseLoader(custom_dir)
        assert loader.cases_dir == custom_dir

    def test_loader_starts_with_empty_indexes(self):
        """Test loader starts with empty internal indexes."""
        loader = JIMCaseLoader()
        assert loader.scotus_index == {}
        assert loader.cases_by_doctrine == {}
        assert loader.cases_by_year == {}
        assert loader.interpretive_canons == []


class TestSCOTUSIndexLoading:
    """Test loading SCOTUS case index."""

    def test_load_scotus_index_success(self):
        """Test successful loading of SCOTUS index."""
        loader = JIMCaseLoader()
        result = loader.load_scotus_index()

        assert "version" in result
        assert "cases" in result
        assert "metadata" in result
        assert len(result["cases"]) > 0

    def test_load_scotus_index_missing_file(self, tmp_path):
        """Test error handling when index file missing."""
        loader = JIMCaseLoader(tmp_path)

        with pytest.raises(FileNotFoundError):
            loader.load_scotus_index()

    def test_load_scotus_index_builds_internal_indexes(self):
        """Test internal indexes built after loading."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()

        assert len(loader.cases_by_doctrine) > 0
        assert len(loader.cases_by_year) > 0
        assert len(loader.interpretive_canons) > 0

    def test_load_scotus_index_indexes_by_doctrine(self):
        """Test cases indexed by doctrine."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()

        assert "due_process" in loader.cases_by_doctrine
        assert "fourth_amendment" in loader.cases_by_doctrine
        assert "administrative_law" in loader.cases_by_doctrine

    def test_load_scotus_index_indexes_by_year(self):
        """Test cases indexed by year."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()

        assert len(loader.cases_by_year) > 0
        # Check for some known years
        assert any(year >= 1950 for year in loader.cases_by_year.keys())


class TestCaseRetrieval:
    """Test case retrieval methods."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_get_cases_by_doctrine_due_process(self, loaded_loader):
        """Test retrieving due process cases."""
        cases = loaded_loader.get_cases_by_doctrine("due_process")
        assert len(cases) > 0
        for case in cases:
            assert case["doctrine"] == "due_process"

    def test_get_cases_by_doctrine_fourth_amendment(self, loaded_loader):
        """Test retrieving Fourth Amendment cases."""
        cases = loaded_loader.get_cases_by_doctrine("fourth_amendment")
        assert len(cases) > 0
        for case in cases:
            assert case["doctrine"] == "fourth_amendment"

    def test_get_cases_by_doctrine_nonexistent(self, loaded_loader):
        """Test retrieving cases for nonexistent doctrine."""
        cases = loaded_loader.get_cases_by_doctrine("nonexistent_doctrine")
        assert cases == []

    def test_get_cases_by_year_range(self, loaded_loader):
        """Test retrieving cases by year range."""
        cases = loaded_loader.get_cases_by_year_range(2000, 2020)
        assert len(cases) > 0
        for case in cases:
            assert 2000 <= case["year"] <= 2020

    def test_get_cases_by_year_range_empty(self, loaded_loader):
        """Test retrieving cases for empty year range."""
        cases = loaded_loader.get_cases_by_year_range(1500, 1600)
        assert cases == []

    def test_get_case_by_id_mathews(self, loaded_loader):
        """Test retrieving specific case by ID."""
        case = loaded_loader.get_case_by_id("mathews_v_eldridge_1976")
        assert case is not None
        assert case["name"] == "Mathews v. Eldridge"
        assert case["year"] == 1976

    def test_get_case_by_id_nonexistent(self, loaded_loader):
        """Test retrieving nonexistent case."""
        case = loaded_loader.get_case_by_id("nonexistent_case")
        assert case is None

    def test_search_cases_by_tag(self, loaded_loader):
        """Test searching cases by issue tag."""
        cases = loaded_loader.search_cases_by_tag("procedural_due_process")
        assert len(cases) > 0
        for case in cases:
            assert "procedural_due_process" in case["issue_tags"]

    def test_search_cases_by_tag_nonexistent(self, loaded_loader):
        """Test searching for nonexistent tag."""
        cases = loaded_loader.search_cases_by_tag("nonexistent_tag")
        assert cases == []


class TestInterpretiveCanons:
    """Test interpretive canon retrieval."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_get_interpretive_canon_major_questions(self, loaded_loader):
        """Test retrieving major questions doctrine canon."""
        canon = loaded_loader.get_interpretive_canon("major_questions_doctrine")
        assert canon is not None
        assert "major_questions_doctrine" in canon["canon_id"]

    def test_get_interpretive_canon_clear_statement(self, loaded_loader):
        """Test retrieving clear statement rule."""
        canon = loaded_loader.get_interpretive_canon("clear_statement_rule")
        assert canon is not None
        assert "clear" in canon["name"].lower()

    def test_get_interpretive_canon_nonexistent(self, loaded_loader):
        """Test retrieving nonexistent canon."""
        canon = loaded_loader.get_interpretive_canon("nonexistent_canon")
        assert canon is None


class TestMetadata:
    """Test metadata retrieval."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_get_all_doctrines(self, loaded_loader):
        """Test retrieving all doctrine names."""
        doctrines = loaded_loader.get_all_doctrines()
        assert len(doctrines) > 0
        assert "due_process" in doctrines
        assert "fourth_amendment" in doctrines

    def test_get_metadata(self, loaded_loader):
        """Test retrieving index metadata."""
        metadata = loaded_loader.get_metadata()
        assert "version" in metadata
        assert "total_cases_loaded" in metadata
        assert "doctrines" in metadata
        assert "year_range" in metadata
        assert metadata["total_cases_loaded"] > 0

    def test_get_metadata_year_range(self, loaded_loader):
        """Test year range in metadata."""
        metadata = loaded_loader.get_metadata()
        year_range = metadata["year_range"]
        assert year_range[0] < year_range[1]
        assert year_range[0] >= 1789  # Founding


class TestIndexValidation:
    """Test case index validation."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_validate_index_success(self, loaded_loader):
        """Test validation of valid index."""
        validation = loaded_loader.validate_index()
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        assert validation["cases_validated"] > 0

    def test_validate_index_checks_required_fields(self, loaded_loader):
        """Test validation checks required top-level fields."""
        # Temporarily remove required field
        original_version = loaded_loader.scotus_index.pop("version", None)

        validation = loaded_loader.validate_index()
        assert validation["valid"] is False
        assert any("version" in error for error in validation["errors"])

        # Restore
        if original_version:
            loaded_loader.scotus_index["version"] = original_version

    def test_validate_index_checks_case_fields(self, loaded_loader):
        """Test validation checks required case fields."""
        # Temporarily corrupt a case
        if loaded_loader.scotus_index.get("cases"):
            original_name = loaded_loader.scotus_index["cases"][0].pop("name", None)

            validation = loaded_loader.validate_index()
            assert validation["valid"] is False
            assert any("name" in error for error in validation["errors"])

            # Restore
            if original_name:
                loaded_loader.scotus_index["cases"][0]["name"] = original_name

    def test_validate_index_warns_invalid_weight(self, loaded_loader):
        """Test validation warns about invalid doctrinal weights."""
        # Temporarily set invalid weight
        if loaded_loader.scotus_index.get("cases"):
            original_weight = loaded_loader.scotus_index["cases"][0].get(
                "doctrinal_weight"
            )
            loaded_loader.scotus_index["cases"][0]["doctrinal_weight"] = 1.5

            validation = loaded_loader.validate_index()
            assert len(validation["warnings"]) > 0

            # Restore
            if original_weight is not None:
                loaded_loader.scotus_index["cases"][0][
                    "doctrinal_weight"
                ] = original_weight


class TestSpecificCases:
    """Test specific landmark cases are properly loaded."""

    @pytest.fixture
    def loaded_loader(self):
        """Provide loaded case loader."""
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_chevron_case_loaded(self, loaded_loader):
        """Test Chevron case is loaded."""
        case = loaded_loader.get_case_by_id("chevron_v_nrdc_1984")
        assert case is not None
        assert "Chevron" in case["name"]

    def test_loper_bright_case_loaded(self, loaded_loader):
        """Test Loper Bright (overruling Chevron) is loaded."""
        case = loaded_loader.get_case_by_id("loper_bright_2024")
        assert case is not None
        assert case["year"] == 2024

    def test_west_virginia_epa_loaded(self, loaded_loader):
        """Test West Virginia v. EPA (major questions) is loaded."""
        case = loaded_loader.get_case_by_id("west_virginia_v_epa_2022")
        assert case is not None
        assert "major_questions_doctrine" in case["issue_tags"]

    def test_carpenter_case_loaded(self, loaded_loader):
        """Test Carpenter v. US (digital privacy) is loaded."""
        case = loaded_loader.get_case_by_id("carpenter_v_us_2018")
        assert case is not None
        assert case["doctrine"] == "fourth_amendment"

    def test_katz_case_loaded(self, loaded_loader):
        """Test Katz v. US (privacy foundation) is loaded."""
        case = loaded_loader.get_case_by_id("katz_v_us_1967")
        assert case is not None
        assert "expectation_of_privacy" in case["issue_tags"]
