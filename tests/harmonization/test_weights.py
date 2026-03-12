"""
Tests for semantic harmonization weight computation.
"""

import pytest

from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class TestWeightComputation:
    """Test harmonization weight computation."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_source_weights_defined(self, harmonizer):
        """Test that source weights are properly defined."""
        assert "blacks" in harmonizer.SOURCE_WEIGHTS
        assert "bouvier" in harmonizer.SOURCE_WEIGHTS
        assert "webster" in harmonizer.SOURCE_WEIGHTS
        assert "oxford" in harmonizer.SOURCE_WEIGHTS
        assert "latin" in harmonizer.SOURCE_WEIGHTS

    def test_source_weights_sum_to_one(self, harmonizer):
        """Test that all source weights sum to 1.0."""
        total = sum(harmonizer.SOURCE_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01  # Allow small floating point error

    def test_blacks_has_highest_weight(self, harmonizer):
        """Test that Black's Law has highest authority weight."""
        blacks_weight = harmonizer.SOURCE_WEIGHTS["blacks"]
        for source, weight in harmonizer.SOURCE_WEIGHTS.items():
            if source != "blacks":
                assert blacks_weight > weight

    def test_compute_weights_for_term(self, harmonizer):
        """Test weight computation for a specific term."""
        # Test with 'probable_cause' which has multiple sources
        weights = harmonizer.compute_harmonization_weights("probable_cause")
        assert isinstance(weights, dict)
        assert len(weights) > 0

    def test_computed_weights_normalized(self, harmonizer):
        """Test that computed weights are normalized to sum to 1.0."""
        weights = harmonizer.compute_harmonization_weights("probable_cause")
        if weights:
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.01

    def test_weights_only_for_available_sources(self, harmonizer):
        """Test that weights are only assigned to sources that define the term."""
        weights = harmonizer.compute_harmonization_weights("probable_cause")
        # All weights should correspond to valid sources
        for source in weights.keys():
            assert source in harmonizer.SOURCE_WEIGHTS

    def test_missing_term_returns_empty_weights(self, harmonizer):
        """Test that missing term returns empty weight dict."""
        weights = harmonizer.compute_harmonization_weights("nonexistent_term_xyz")
        assert weights == {}

    def test_weight_proportions_preserved(self, harmonizer):
        """Test that relative weight proportions are preserved after normalization."""
        weights = harmonizer.compute_harmonization_weights("probable_cause")
        if "blacks" in weights and "webster" in weights:
            # Blacks should still have higher weight than Webster after normalization
            assert weights["blacks"] > weights["webster"]


class TestSourceMapping:
    """Test source name mapping."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        return SemanticHarmonizer()

    def test_map_blacks_law(self, harmonizer):
        """Test mapping of Black's Law Dictionary variants."""
        assert harmonizer._map_source_to_key("blacks_law") == "blacks"
        assert harmonizer._map_source_to_key("black_law_dictionary") == "blacks"
        assert harmonizer._map_source_to_key("BLACK'S LAW") == "blacks"

    def test_map_bouvier(self, harmonizer):
        """Test mapping of Bouvier's Dictionary variants."""
        assert harmonizer._map_source_to_key("bouvier_1856") == "bouvier"
        assert harmonizer._map_source_to_key("bouviers_law_dictionary") == "bouvier"
        assert harmonizer._map_source_to_key("BOUVIER") == "bouvier"

    def test_map_webster(self, harmonizer):
        """Test mapping of Webster Legal Dictionary variants."""
        assert harmonizer._map_source_to_key("webster_legal") == "webster"
        assert harmonizer._map_source_to_key("merriam_webster_legal") == "webster"
        assert harmonizer._map_source_to_key("WEBSTER") == "webster"

    def test_map_oxford(self, harmonizer):
        """Test mapping of Oxford Law Dictionary variants."""
        assert harmonizer._map_source_to_key("oxford_law") == "oxford"
        assert (
            harmonizer._map_source_to_key("oxford_english_law_dictionary") == "oxford"
        )
        assert harmonizer._map_source_to_key("OXFORD") == "oxford"

    def test_map_latin(self, harmonizer):
        """Test mapping of Latin Legal Maxims variants."""
        assert harmonizer._map_source_to_key("latin_legal") == "latin"
        assert harmonizer._map_source_to_key("latin_foundational") == "latin"
        assert harmonizer._map_source_to_key("LATIN") == "latin"

    def test_map_unknown_source(self, harmonizer):
        """Test mapping of unknown source names."""
        assert harmonizer._map_source_to_key("unknown_source") == "unknown"
        assert harmonizer._map_source_to_key("random_dictionary") == "unknown"


class TestWeightConsistency:
    """Test consistency of weight assignments."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_same_sources_same_weights(self, harmonizer):
        """Test that terms with same sources get same weight distribution."""
        # Build matrix to have all weights computed
        harmonizer.build_harmonization_matrix()

        # Get two terms with similar source coverage
        term1_weights = harmonizer.compute_harmonization_weights("probable_cause")
        term2_weights = harmonizer.compute_harmonization_weights("due_process")

        # If both have blacks, weights should follow same proportions
        if "blacks" in term1_weights and "blacks" in term2_weights:
            # Both should have blacks as highest weight
            assert term1_weights["blacks"] == max(term1_weights.values())
            assert term2_weights["blacks"] == max(term2_weights.values())

    def test_deterministic_weight_computation(self, harmonizer):
        """Test that weight computation is deterministic."""
        weights1 = harmonizer.compute_harmonization_weights("probable_cause")
        weights2 = harmonizer.compute_harmonization_weights("probable_cause")
        assert weights1 == weights2

    def test_all_terms_have_weights(self, harmonizer):
        """Test that all merged terms can have weights computed."""
        for normalized_term in harmonizer.merged_definitions.keys():
            weights = harmonizer.compute_harmonization_weights(normalized_term)
            # Should return dict (may be empty if no sources, but should not error)
            assert isinstance(weights, dict)


class TestWeightValidation:
    """Test validation of weight values."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_weights_in_valid_range(self, harmonizer):
        """Test that all weights are in range [0, 1]."""
        for _source, weight in harmonizer.SOURCE_WEIGHTS.items():
            assert 0.0 <= weight <= 1.0

    def test_computed_weights_in_valid_range(self, harmonizer):
        """Test that computed weights are in valid range."""
        weights = harmonizer.compute_harmonization_weights("probable_cause")
        for weight in weights.values():
            assert 0.0 <= weight <= 1.0

    def test_no_negative_weights(self, harmonizer):
        """Test that no negative weights are produced."""
        for normalized_term in harmonizer.merged_definitions.keys():
            weights = harmonizer.compute_harmonization_weights(normalized_term)
            for weight in weights.values():
                assert weight >= 0.0

    def test_no_weights_exceed_one(self, harmonizer):
        """Test that no individual weight exceeds 1.0."""
        for normalized_term in harmonizer.merged_definitions.keys():
            weights = harmonizer.compute_harmonization_weights(normalized_term)
            for weight in weights.values():
                assert weight <= 1.0
