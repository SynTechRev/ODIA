"""
Tests for harmonization matrix generation and artifact creation.
"""

import json
from pathlib import Path

import pytest

from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class TestMatrixGeneration:
    """Test harmonization matrix generation."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_build_harmonization_matrix(self, harmonizer):
        """Test basic matrix building."""
        matrix = harmonizer.build_harmonization_matrix()
        assert isinstance(matrix, dict)
        assert len(matrix) > 0

    def test_matrix_covers_all_terms(self, harmonizer):
        """Test that matrix covers all merged terms."""
        matrix = harmonizer.build_harmonization_matrix()
        merged_terms = set(harmonizer.merged_definitions.keys())
        matrix_terms = set(matrix.keys())

        assert merged_terms == matrix_terms

    def test_matrix_entries_have_required_fields(self, harmonizer):
        """Test that matrix entries have all required fields."""
        matrix = harmonizer.build_harmonization_matrix()

        required_fields = [
            "canonical",
            "sources",
            "harmonized_meaning",
            "weights",
            "doctrines",
            "era_adjustments",
            "related_terms",
            "antonyms",
            "origin_language",
        ]

        for entry in matrix.values():
            for field in required_fields:
                assert field in entry

    def test_canonical_forms_present(self, harmonizer):
        """Test that canonical term forms are present."""
        matrix = harmonizer.build_harmonization_matrix()

        for entry in matrix.values():
            canonical = entry["canonical"]
            assert isinstance(canonical, str)
            assert len(canonical) > 0

    def test_harmonized_meanings_present(self, harmonizer):
        """Test that harmonized meanings are present."""
        matrix = harmonizer.build_harmonization_matrix()

        for entry in matrix.values():
            harmonized = entry["harmonized_meaning"]
            assert isinstance(harmonized, str)


class TestMatrixStructure:
    """Test structure of harmonization matrix."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        return harmonizer

    def test_sources_are_dicts(self, harmonizer):
        """Test that sources are dictionaries."""
        for entry in harmonizer.harmonization_matrix.values():
            sources = entry["sources"]
            assert isinstance(sources, dict)

    def test_weights_are_dicts(self, harmonizer):
        """Test that weights are dictionaries."""
        for entry in harmonizer.harmonization_matrix.values():
            weights = entry["weights"]
            assert isinstance(weights, dict)

    def test_doctrines_are_lists(self, harmonizer):
        """Test that doctrines are lists."""
        for entry in harmonizer.harmonization_matrix.values():
            doctrines = entry["doctrines"]
            assert isinstance(doctrines, list)

    def test_era_adjustments_are_dicts(self, harmonizer):
        """Test that era adjustments are dictionaries."""
        for entry in harmonizer.harmonization_matrix.values():
            era_adjustments = entry["era_adjustments"]
            assert isinstance(era_adjustments, dict)

    def test_related_terms_are_lists(self, harmonizer):
        """Test that related terms are lists."""
        for entry in harmonizer.harmonization_matrix.values():
            related = entry["related_terms"]
            assert isinstance(related, list)

    def test_antonyms_are_lists(self, harmonizer):
        """Test that antonyms are lists."""
        for entry in harmonizer.harmonization_matrix.values():
            antonyms = entry["antonyms"]
            assert isinstance(antonyms, list)


class TestSourceDefinitionExtraction:
    """Test extraction of source definitions."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_extract_source_definitions(self, harmonizer):
        """Test extracting source definitions for a term."""
        source_defs = harmonizer._extract_source_definitions("probable_cause")
        assert isinstance(source_defs, dict)

    def test_blacks_extraction(self, harmonizer):
        """Test extraction from Black's Law Dictionary."""
        source_defs = harmonizer._extract_source_definitions("probable_cause")

        if "blacks" in source_defs:
            blacks_def = source_defs["blacks"]
            assert "definition" in blacks_def
            assert "citation" in blacks_def
            assert "edition" in blacks_def
            assert "year" in blacks_def
            assert blacks_def["year"] == 2019

    def test_bouvier_extraction(self, harmonizer):
        """Test extraction from Bouvier's Dictionary."""
        source_defs = harmonizer._extract_source_definitions("sovereignty")

        if "bouvier" in source_defs:
            bouvier_def = source_defs["bouvier"]
            assert "definition" in bouvier_def
            assert "citation" in bouvier_def
            assert "edition" in bouvier_def
            assert "year" in bouvier_def
            assert bouvier_def["year"] == 1856

    def test_webster_extraction(self, harmonizer):
        """Test extraction from Webster Legal Dictionary."""
        source_defs = harmonizer._extract_source_definitions("probable_cause")

        if "webster" in source_defs:
            webster_def = source_defs["webster"]
            assert "definition" in webster_def
            assert "year" in webster_def
            assert webster_def["year"] == 2023

    def test_latin_extraction(self, harmonizer):
        """Test extraction from Latin Legal Maxims."""
        source_defs = harmonizer._extract_source_definitions("habeas_corpus")

        if "latin" in source_defs:
            latin_def = source_defs["latin"]
            assert "latin" in latin_def
            assert "translation" in latin_def
            assert "jurisprudential_usage" in latin_def


class TestHarmonizedMeaningConstruction:
    """Test construction of harmonized meanings."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_build_harmonized_meaning(self, harmonizer):
        """Test building harmonized meaning from sources."""
        source_defs = {
            "blacks": {"definition": "Primary definition"},
            "webster": {"definition": "Secondary definition"},
        }
        weights = {"blacks": 0.7, "webster": 0.3}

        meaning = harmonizer._build_harmonized_meaning(source_defs, weights)
        assert isinstance(meaning, str)
        assert len(meaning) > 0

    def test_highest_weight_source_used(self, harmonizer):
        """Test that highest-weighted source definition is used."""
        source_defs = {
            "blacks": {"definition": "Primary definition"},
            "webster": {"definition": "Secondary definition"},
        }
        weights = {"blacks": 0.7, "webster": 0.3}

        meaning = harmonizer._build_harmonized_meaning(source_defs, weights)

        # Should use Black's (highest weight)
        assert meaning == "Primary definition"

    def test_empty_sources_returns_empty(self, harmonizer):
        """Test that empty sources returns empty string."""
        meaning = harmonizer._build_harmonized_meaning({}, {})
        assert meaning == ""

    def test_latin_jurisprudential_usage(self, harmonizer):
        """Test that Latin terms use jurisprudential_usage."""
        source_defs = {"latin": {"jurisprudential_usage": "Latin meaning"}}
        weights = {"latin": 1.0}

        meaning = harmonizer._build_harmonized_meaning(source_defs, weights)
        assert meaning == "Latin meaning"


class TestArtifactGeneration:
    """Test generation of JSON artifacts."""

    @pytest.fixture
    def harmonizer(self, tmp_path):
        """Create harmonizer instance with temporary output."""
        harmonizer = SemanticHarmonizer(output_dir=tmp_path)
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_generate_artifacts(self, harmonizer):
        """Test generating all artifacts."""
        result = harmonizer.generate_artifacts()

        assert result["success"] is True
        assert "matrix_path" in result
        assert "divergence_path" in result
        assert "total_terms" in result
        assert "conflicts_detected" in result

    def test_matrix_artifact_created(self, harmonizer):
        """Test that matrix JSON file is created."""
        result = harmonizer.generate_artifacts()
        matrix_path = Path(result["matrix_path"])

        assert matrix_path.exists()
        assert matrix_path.is_file()

    def test_divergence_artifact_created(self, harmonizer):
        """Test that divergence JSON file is created."""
        result = harmonizer.generate_artifacts()
        divergence_path = Path(result["divergence_path"])

        assert divergence_path.exists()
        assert divergence_path.is_file()

    def test_matrix_json_valid(self, harmonizer):
        """Test that matrix JSON is valid."""
        result = harmonizer.generate_artifacts()
        matrix_path = Path(result["matrix_path"])

        with open(matrix_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "version" in data
        assert "schema_version" in data
        assert "generated" in data
        assert "total_terms" in data
        assert "source_weights" in data
        assert "terms" in data

    def test_divergence_json_valid(self, harmonizer):
        """Test that divergence JSON is valid."""
        result = harmonizer.generate_artifacts()
        divergence_path = Path(result["divergence_path"])

        with open(divergence_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "version" in data
        assert "schema_version" in data
        assert "generated" in data
        assert "total_terms" in data
        assert "conflict_count" in data
        assert "conflicts" in data
        assert "terms" in data


class TestArtifactSchema:
    """Test schema compliance of generated artifacts."""

    @pytest.fixture
    def harmonizer(self, tmp_path):
        """Create harmonizer instance with temporary output."""
        harmonizer = SemanticHarmonizer(output_dir=tmp_path)
        harmonizer.load_lexicon_sources()
        harmonizer.generate_artifacts()
        return harmonizer

    def test_matrix_version_present(self, harmonizer, tmp_path):
        """Test that matrix has version information."""
        matrix_path = tmp_path / "SEMANTIC_HARMONIZATION_MATRIX.json"
        with open(matrix_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["version"] == "1.0.0"
        assert data["schema_version"] == "1.0"

    def test_divergence_version_present(self, harmonizer, tmp_path):
        """Test that divergence index has version information."""
        divergence_path = tmp_path / "MEANING_DIVERGENCE_INDEX.json"
        with open(divergence_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["version"] == "1.0.0"
        assert data["schema_version"] == "1.0"

    def test_matrix_term_structure(self, harmonizer, tmp_path):
        """Test structure of terms in matrix."""
        matrix_path = tmp_path / "SEMANTIC_HARMONIZATION_MATRIX.json"
        with open(matrix_path, encoding="utf-8") as f:
            data = json.load(f)

        # Check first term structure
        first_term = next(iter(data["terms"].values()))
        required_fields = [
            "canonical",
            "sources",
            "harmonized_meaning",
            "weights",
            "doctrines",
            "era_adjustments",
        ]

        for field in required_fields:
            assert field in first_term

    def test_divergence_term_structure(self, harmonizer, tmp_path):
        """Test structure of terms in divergence index."""
        divergence_path = tmp_path / "MEANING_DIVERGENCE_INDEX.json"
        with open(divergence_path, encoding="utf-8") as f:
            data = json.load(f)

        # Check first term structure
        first_term = next(iter(data["terms"].values()))
        required_fields = [
            "divergence_score",
            "conflict_sources",
            "era_drift",
            "source_count",
        ]

        for field in required_fields:
            assert field in first_term


class TestMatrixDeterminism:
    """Test determinism of matrix generation."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_matrix_generation_deterministic(self, harmonizer):
        """Test that matrix generation is deterministic."""
        matrix1 = harmonizer.build_harmonization_matrix()
        matrix2 = harmonizer.build_harmonization_matrix()

        # Should produce identical results
        assert len(matrix1) == len(matrix2)
        assert set(matrix1.keys()) == set(matrix2.keys())

    def test_artifact_generation_deterministic(self, harmonizer, tmp_path):
        """Test that artifact generation is deterministic."""
        # Generate first time
        harmonizer.output_dir = tmp_path / "run1"
        harmonizer.output_dir.mkdir(parents=True, exist_ok=True)
        result1 = harmonizer.generate_artifacts()

        # Generate second time
        harmonizer.output_dir = tmp_path / "run2"
        harmonizer.output_dir.mkdir(parents=True, exist_ok=True)
        result2 = harmonizer.generate_artifacts()

        # Should have same term counts
        assert result1["total_terms"] == result2["total_terms"]
        assert result1["conflicts_detected"] == result2["conflicts_detected"]
