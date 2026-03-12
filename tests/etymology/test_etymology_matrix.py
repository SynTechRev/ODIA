"""
Tests for Etymology Matrix - LGCEP-v1.

Tests harmonized etymology matrix structure, drift scores, and era meanings.
"""

import pytest

from scripts.jim.etymology_loader import EtymologyLoader


class TestMatrixStructure:
    """Test etymology matrix structure."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_matrix_has_entries(self, loader):
        """Test that matrix has entries."""
        assert "entries" in loader.etymology_matrix
        assert len(loader.etymology_matrix["entries"]) > 0

    def test_matrix_has_version(self, loader):
        """Test that matrix has version info."""
        assert "version" in loader.etymology_matrix
        assert "schema_version" in loader.etymology_matrix

    def test_matrix_has_description(self, loader):
        """Test that matrix has description."""
        assert "description" in loader.etymology_matrix


class TestMatrixEntries:
    """Test individual matrix entries."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_entry_has_required_fields(self, loader):
        """Test that entries have required fields."""
        if loader.etymology_matrix["entries"]:
            entry = loader.etymology_matrix["entries"][0]
            assert "term" in entry
            assert "root_languages" in entry
            assert "semantic_lineage" in entry
            assert "drift_score" in entry

    def test_entry_has_era_meanings(self, loader):
        """Test that entries have era meanings."""
        if loader.etymology_matrix["entries"]:
            entry = loader.etymology_matrix["entries"][0]
            assert "era_meanings" in entry
            assert isinstance(entry["era_meanings"], dict)

    def test_entry_has_doctrines(self, loader):
        """Test that entries have legal doctrines."""
        if loader.etymology_matrix["entries"]:
            entry = loader.etymology_matrix["entries"][0]
            assert "legal_doctrines" in entry
            assert isinstance(entry["legal_doctrines"], list)


class TestRootLanguages:
    """Test root language mappings."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_root_languages_structure(self, loader):
        """Test root languages structure."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            roots = etymology.get("root_languages", {})
            assert "latin" in roots or "greek" in roots

    def test_latin_roots_present(self, loader):
        """Test that Latin roots are present."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            roots = etymology.get("root_languages", {})
            assert "latin" in roots

    def test_greek_roots_present(self, loader):
        """Test that Greek roots are present."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            roots = etymology.get("root_languages", {})
            assert "greek" in roots


class TestDriftScores:
    """Test drift score calculations."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_drift_scores_in_range(self, loader):
        """Test that all drift scores are in valid range."""
        for entry in loader.etymology_matrix.get("entries", []):
            score = entry.get("drift_score", 0.0)
            assert 0.0 <= score <= 1.0

    def test_drift_score_types(self, loader):
        """Test that drift scores are numeric."""
        for entry in loader.etymology_matrix.get("entries", []):
            score = entry.get("drift_score", 0.0)
            assert isinstance(score, int | float)

    def test_drift_scores_reasonable(self, loader):
        """Test that drift scores are reasonable."""
        scores = [
            entry.get("drift_score", 0.0)
            for entry in loader.etymology_matrix.get("entries", [])
        ]
        if scores:
            assert min(scores) >= 0.0
            assert max(scores) <= 1.0


class TestEraMeanings:
    """Test era meanings."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_era_meanings_present(self, loader):
        """Test that era meanings are present."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            assert "era_meanings" in etymology
            assert len(etymology["era_meanings"]) > 0

    def test_era_meanings_keys(self, loader):
        """Test that era meanings have expected keys."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            era_meanings = etymology.get("era_meanings", {})
            valid_eras = [
                "classical_greek",
                "roman_law",
                "medieval_canon",
                "enlightenment",
                "modern",
            ]
            for era in era_meanings.keys():
                assert era in valid_eras

    def test_era_meanings_values_are_strings(self, loader):
        """Test that era meanings are strings."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            era_meanings = etymology.get("era_meanings", {})
            for meaning in era_meanings.values():
                assert isinstance(meaning, str)
                assert len(meaning) > 0


class TestSemanticLineage:
    """Test semantic lineage chains."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_semantic_lineage_present(self, loader):
        """Test that semantic lineage is present."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            assert "semantic_lineage" in etymology
            assert len(etymology["semantic_lineage"]) > 0

    def test_semantic_lineage_is_list(self, loader):
        """Test that semantic lineage is a list."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            lineage = etymology.get("semantic_lineage", [])
            assert isinstance(lineage, list)

    def test_semantic_lineage_chains(self, loader):
        """Test that lineage chains show evolution."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            lineage = etymology.get("semantic_lineage", [])
            if lineage:
                # Check for arrow notation indicating progression
                assert any("→" in chain for chain in lineage)


class TestLegalDoctrines:
    """Test legal doctrine mappings."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_legal_doctrines_present(self, loader):
        """Test that legal doctrines are present."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            assert "legal_doctrines" in etymology
            assert len(etymology["legal_doctrines"]) > 0

    def test_legal_doctrines_is_list(self, loader):
        """Test that legal doctrines is a list."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            doctrines = etymology.get("legal_doctrines", [])
            assert isinstance(doctrines, list)

    def test_legal_doctrines_valid(self, loader):
        """Test that legal doctrines are valid strings."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            doctrines = etymology.get("legal_doctrines", [])
            for doctrine in doctrines:
                assert isinstance(doctrine, str)
                assert len(doctrine) > 0


class TestCitations:
    """Test citation references."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_citations_present(self, loader):
        """Test that citations are present."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            assert "citations" in etymology

    def test_citations_is_list(self, loader):
        """Test that citations is a list."""
        etymology = loader.get_etymology_for_term("justice")
        if etymology:
            citations = etymology.get("citations", [])
            assert isinstance(citations, list)


class TestDriftAnalysis:
    """Test drift analysis capabilities."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_drift_analysis_categorization(self, loader):
        """Test that drift analysis categorizes terms."""
        report = loader.generate_etymology_report()
        drift = report["drift_analysis"]
        assert "stable_terms" in drift
        assert "moderate_drift" in drift
        assert "significant_drift" in drift

    def test_drift_categories_sum_to_total(self, loader):
        """Test that drift categories account for all terms."""
        report = loader.generate_etymology_report()
        drift = report["drift_analysis"]
        total_categorized = (
            drift["stable_terms"] + drift["moderate_drift"] + drift["significant_drift"]
        )
        assert total_categorized == len(loader.drift_scores)


class TestMatrixCompleteness:
    """Test matrix completeness."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_all_entries_have_terms(self, loader):
        """Test that all entries have terms."""
        for entry in loader.etymology_matrix.get("entries", []):
            assert "term" in entry
            assert len(entry["term"]) > 0

    def test_all_entries_have_drift_scores(self, loader):
        """Test that all entries have drift scores."""
        for entry in loader.etymology_matrix.get("entries", []):
            assert "drift_score" in entry

    def test_all_entries_have_semantic_lineage(self, loader):
        """Test that all entries have semantic lineage."""
        for entry in loader.etymology_matrix.get("entries", []):
            assert "semantic_lineage" in entry


class TestMatrixIntegrity:
    """Test matrix data integrity."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_no_duplicate_terms(self, loader):
        """Test that there are no duplicate terms."""
        terms = [
            entry.get("term", "")
            for entry in loader.etymology_matrix.get("entries", [])
            if entry.get("term")
        ]
        # Only test if we have terms
        if terms:
            assert len(terms) == len(set(terms))

    def test_all_terms_lowercase_normalized(self, loader):
        """Test that term lookups work with case insensitivity."""
        etymology_upper = loader.get_etymology_for_term("JUSTICE")
        etymology_lower = loader.get_etymology_for_term("justice")
        if etymology_upper and etymology_lower:
            assert etymology_upper == etymology_lower


class TestMatrixConsistency:
    """Test matrix internal consistency."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_root_languages_consistent(self, loader):
        """Test that root language mappings are consistent."""
        for entry in loader.etymology_matrix.get("entries", []):
            roots = entry.get("root_languages", {})
            for lang, root in roots.items():
                assert isinstance(lang, str)
                assert isinstance(root, str)

    def test_era_meanings_consistent(self, loader):
        """Test that era meanings are consistent."""
        for entry in loader.etymology_matrix.get("entries", []):
            era_meanings = entry.get("era_meanings", {})
            for era, meaning in era_meanings.items():
                assert isinstance(era, str)
                assert isinstance(meaning, str)
                assert len(meaning) > 0
