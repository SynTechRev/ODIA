"""
Tests for Legal Lexicon Loading - LLEP-v1.

Tests dictionary file loading and schema validation.
"""

import json
from pathlib import Path

from scripts.jim.jim_semantic_loader import JIMSemanticLoader


class TestLexiconFileLoading:
    """Test loading of individual dictionary files."""

    def test_blacks_law_loads(self):
        """Test Black's Law Dictionary loads successfully."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["success"] is True
        assert result["blacks_terms"] > 0
        assert loader.blacks_law is not None
        assert "dictionary" in loader.blacks_law
        assert loader.blacks_law["dictionary"] == "blacks_law_dictionary"

    def test_bouvier_1856_loads(self):
        """Test Bouvier's 1856 Dictionary loads successfully."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["success"] is True
        assert result["bouvier_terms"] > 0
        assert loader.bouvier is not None
        assert "dictionary" in loader.bouvier
        assert loader.bouvier["dictionary"] == "bouviers_law_dictionary"

    def test_webster_legal_loads(self):
        """Test Webster Legal Dictionary loads successfully."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["success"] is True
        assert result["webster_terms"] > 0
        assert loader.webster is not None
        assert "dictionary" in loader.webster
        assert loader.webster["dictionary"] == "webster_legal_dictionary"

    def test_oxford_law_loads(self):
        """Test Oxford Law Dictionary loads successfully."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["success"] is True
        assert result["oxford_mappings"] > 0
        assert loader.oxford is not None
        assert "dictionary" in loader.oxford
        assert loader.oxford["dictionary"] == "oxford_english_law_dictionary"

    def test_latin_foundational_loads(self):
        """Test Latin Legal Maxims loads successfully."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["success"] is True
        assert result["latin_terms"] > 0
        assert loader.latin is not None
        assert "dictionary" in loader.latin
        assert loader.latin["dictionary"] == "latin_legal_maxims"

    def test_legal_dictionary_index_loads(self):
        """Test unified Legal Dictionary Index loads successfully."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["success"] is True
        assert result["index_entries"] > 0
        assert loader.index is not None
        assert "version" in loader.index
        assert "index" in loader.index


class TestSchemaValidation:
    """Test schema validation for all dictionary sources."""

    def test_validate_all_schemas(self):
        """Test schema validation passes for all dictionaries."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        validation = loader.validate_lexicon_schema()
        assert validation["valid"] is True
        assert validation["error_count"] == 0

    def test_blacks_law_required_fields(self):
        """Test Black's Law terms have required fields."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.blacks_law.get("terms", []):
            assert "term" in term
            assert "definition" in term
            assert "citation" in term
            assert "category" in term
            assert "origin_language" in term

    def test_bouvier_required_fields(self):
        """Test Bouvier's terms have required fields."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.bouvier.get("terms", []):
            assert "term" in term
            assert "definition" in term
            assert "citation" in term
            assert "category" in term
            assert "origin_language" in term

    def test_webster_required_fields(self):
        """Test Webster Legal terms have required fields."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.webster.get("terms", []):
            assert "term" in term
            assert "definition" in term
            assert "synonyms" in term
            assert "antonyms" in term
            assert "practical_usage" in term
            assert "origin_language" in term

    def test_oxford_required_fields(self):
        """Test Oxford mappings have required fields."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for mapping in loader.oxford.get("synonym_mappings", []):
            assert "term" in mapping
            assert "synonyms" in mapping
            assert isinstance(mapping["synonyms"], list)

    def test_latin_required_fields(self):
        """Test Latin terms have required fields."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.latin.get("terms", []):
            assert "latin" in term
            assert "translation" in term
            assert "jurisprudential_usage" in term
            assert "doctrinal_mapping" in term
            assert "origin_language" in term

    def test_index_required_fields(self):
        """Test index entries have required fields."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for entry in loader.index.get("index", []):
            assert "term" in entry
            assert "normalized_term" in entry
            assert "sources" in entry
            assert "doctrines" in entry
            assert "origin_language" in entry
            assert "related_terms" in entry
            assert "antonyms" in entry


class TestDictionaryIntegrity:
    """Test dictionary data integrity."""

    def test_no_empty_definitions(self):
        """Test no dictionary has empty definitions."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Check Black's
        for term in loader.blacks_law.get("terms", []):
            assert term["definition"].strip() != ""

        # Check Bouvier's
        for term in loader.bouvier.get("terms", []):
            assert term["definition"].strip() != ""

        # Check Webster
        for term in loader.webster.get("terms", []):
            assert term["definition"].strip() != ""

    def test_no_duplicate_terms_in_blacks(self):
        """Test Black's Law has no duplicate terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        terms = [term["term"] for term in loader.blacks_law.get("terms", [])]
        assert len(terms) == len(set(terms))

    def test_no_duplicate_terms_in_bouvier(self):
        """Test Bouvier's has no duplicate terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        terms = [term["term"] for term in loader.bouvier.get("terms", [])]
        assert len(terms) == len(set(terms))

    def test_no_duplicate_terms_in_webster(self):
        """Test Webster has no duplicate terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        terms = [term["term"] for term in loader.webster.get("terms", [])]
        assert len(terms) == len(set(terms))

    def test_citations_present(self):
        """Test all citeable dictionaries have citations."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Check Black's
        for term in loader.blacks_law.get("terms", []):
            assert "citation" in term
            assert term["citation"].strip() != ""

        # Check Bouvier's
        for term in loader.bouvier.get("terms", []):
            assert "citation" in term
            assert term["citation"].strip() != ""

    def test_latin_translations_present(self):
        """Test all Latin terms have translations."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.latin.get("terms", []):
            assert "translation" in term
            assert term["translation"].strip() != ""

    def test_doctrinal_mappings_valid(self):
        """Test Latin terms have valid doctrinal mappings."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.latin.get("terms", []):
            assert "doctrinal_mapping" in term
            assert isinstance(term["doctrinal_mapping"], list)
            assert len(term["doctrinal_mapping"]) > 0


class TestTermCounts:
    """Test term count requirements."""

    def test_blacks_law_term_count(self):
        """Test Black's Law has 50+ terms."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["blacks_terms"] >= 50

    def test_bouvier_term_count(self):
        """Test Bouvier's has 35+ terms."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["bouvier_terms"] >= 35

    def test_webster_term_count(self):
        """Test Webster has 30+ terms."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["webster_terms"] >= 30

    def test_oxford_mapping_count(self):
        """Test Oxford has 50+ synonym mappings."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["oxford_mappings"] >= 50

    def test_latin_term_count(self):
        """Test Latin has 50+ terms."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["latin_terms"] >= 50

    def test_total_index_entries(self):
        """Test index has 20+ entries."""
        loader = JIMSemanticLoader()
        result = loader.load_lexicon_sources()
        assert result["index_entries"] >= 20


class TestJSONValidity:
    """Test JSON file validity."""

    def test_blacks_law_json_valid(self):
        """Test Black's Law JSON is valid."""
        repo_root = Path(__file__).parent.parent.parent
        path = repo_root / "legal" / "lexicon" / "black_law_subset.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_bouvier_json_valid(self):
        """Test Bouvier's JSON is valid."""
        repo_root = Path(__file__).parent.parent.parent
        path = repo_root / "legal" / "lexicon" / "bouvier_1856.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_webster_json_valid(self):
        """Test Webster JSON is valid."""
        repo_root = Path(__file__).parent.parent.parent
        path = repo_root / "legal" / "lexicon" / "webster_legal_subset.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_oxford_json_valid(self):
        """Test Oxford JSON is valid."""
        repo_root = Path(__file__).parent.parent.parent
        path = repo_root / "legal" / "lexicon" / "oxford_law_synonyms.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_latin_json_valid(self):
        """Test Latin JSON is valid."""
        repo_root = Path(__file__).parent.parent.parent
        path = repo_root / "legal" / "lexicon" / "latin_foundational.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_index_json_valid(self):
        """Test Index JSON is valid."""
        repo_root = Path(__file__).parent.parent.parent
        path = repo_root / "legal" / "lexicon" / "LEGAL_DICTIONARY_INDEX.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
