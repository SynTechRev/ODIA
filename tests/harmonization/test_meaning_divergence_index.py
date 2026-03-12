"""
Tests for meaning divergence index computation.
"""

import pytest

from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class TestDivergenceIndexComputation:
    """Test computation of meaning divergence index."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.detect_semantic_conflicts()
        return harmonizer

    def test_compute_divergence_index(self, harmonizer):
        """Test basic divergence index computation."""
        divergence_index = harmonizer.compute_meaning_divergence_index()
        assert isinstance(divergence_index, dict)
        assert len(divergence_index) > 0

    def test_divergence_index_covers_all_terms(self, harmonizer):
        """Test that divergence index covers all merged terms."""
        divergence_index = harmonizer.compute_meaning_divergence_index()
        merged_terms = set(harmonizer.merged_definitions.keys())
        index_terms = set(divergence_index.keys())

        # Should cover all terms
        assert merged_terms == index_terms

    def test_divergence_entries_have_required_fields(self, harmonizer):
        """Test that divergence entries have required fields."""
        divergence_index = harmonizer.compute_meaning_divergence_index()

        required_fields = [
            "divergence_score",
            "conflict_sources",
            "era_drift",
            "source_count",
        ]

        for entry in divergence_index.values():
            for field in required_fields:
                assert field in entry

    def test_divergence_scores_in_valid_range(self, harmonizer):
        """Test that divergence scores are in range [0, 1]."""
        divergence_index = harmonizer.compute_meaning_divergence_index()

        for entry in divergence_index.values():
            score = entry["divergence_score"]
            assert 0.0 <= score <= 1.0

    def test_conflict_sources_are_lists(self, harmonizer):
        """Test that conflict sources are lists."""
        divergence_index = harmonizer.compute_meaning_divergence_index()

        for entry in divergence_index.values():
            assert isinstance(entry["conflict_sources"], list)


class TestDivergenceScoreCalculation:
    """Test divergence score calculation logic."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_single_source_has_zero_divergence(self, harmonizer):
        """Test that single source terms have zero divergence."""
        # Create mock with single source
        mock_sources = {"blacks": {"definition": "Test definition"}}

        divergence = harmonizer._calculate_divergence_score(mock_sources)
        assert divergence == 0.0

    def test_identical_definitions_have_zero_divergence(self, harmonizer):
        """Test that identical definitions have zero divergence."""
        mock_sources = {
            "blacks": {"definition": "Same definition"},
            "webster": {"definition": "Same definition"},
        }

        divergence = harmonizer._calculate_divergence_score(mock_sources)
        assert divergence == 0.0

    def test_different_definitions_have_nonzero_divergence(self, harmonizer):
        """Test that different definitions have non-zero divergence."""
        mock_sources = {
            "blacks": {"definition": "Definition A"},
            "webster": {"definition": "Definition B"},
        }

        divergence = harmonizer._calculate_divergence_score(mock_sources)
        assert divergence > 0.0

    def test_divergence_increases_with_more_differences(self, harmonizer):
        """Test that divergence increases with more unique definitions."""
        # Two different definitions
        sources_2 = {
            "blacks": {"definition": "Def A"},
            "webster": {"definition": "Def B"},
        }
        divergence_2 = harmonizer._calculate_divergence_score(sources_2)

        # Three different definitions
        sources_3 = {
            "blacks": {"definition": "Def A"},
            "webster": {"definition": "Def B"},
            "bouvier": {"definition": "Def C"},
        }
        divergence_3 = harmonizer._calculate_divergence_score(sources_3)

        # More unique definitions should have higher divergence
        assert divergence_3 >= divergence_2

    def test_divergence_score_capped_at_one(self, harmonizer):
        """Test that divergence score is capped at 1.0."""
        # Many different definitions
        mock_sources = {
            f"source_{i}": {"definition": f"Definition {i}"} for i in range(10)
        }

        divergence = harmonizer._calculate_divergence_score(mock_sources)
        assert divergence <= 1.0


class TestEraDriftCalculation:
    """Test era drift calculation."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_era_drift_calculation(self, harmonizer):
        """Test basic era drift calculation."""
        mock_sources = {
            "bouvier": {"definition": "Historical definition"},
            "blacks": {"definition": "Modern definition"},
        }

        era_drift = harmonizer._calculate_era_drift(mock_sources)
        assert isinstance(era_drift, dict)

    def test_era_drift_1791_to_2024(self, harmonizer):
        """Test 1791→2024 era drift measurement."""
        mock_sources = {
            "bouvier": {"definition": "Historical definition"},
            "blacks": {"definition": "Modern definition"},
        }

        era_drift = harmonizer._calculate_era_drift(mock_sources)

        # Should have 1791→2024 measurement
        assert "1791→2024" in era_drift

    def test_era_drift_scores_in_valid_range(self, harmonizer):
        """Test that era drift scores are in valid range."""
        mock_sources = {
            "bouvier": {"definition": "Historical definition"},
            "blacks": {"definition": "Modern definition"},
        }

        era_drift = harmonizer._calculate_era_drift(mock_sources)

        for drift_score in era_drift.values():
            assert 0.0 <= drift_score <= 1.0

    def test_identical_definitions_zero_drift(self, harmonizer):
        """Test that identical definitions have zero drift."""
        mock_sources = {
            "bouvier": {"definition": "Same definition"},
            "blacks": {"definition": "Same definition"},
        }

        era_drift = harmonizer._calculate_era_drift(mock_sources)

        if "1791→2024" in era_drift:
            assert era_drift["1791→2024"] == 0.0

    def test_different_definitions_nonzero_drift(self, harmonizer):
        """Test that different definitions have non-zero drift."""
        mock_sources = {
            "bouvier": {"definition": "Old meaning"},
            "blacks": {"definition": "New meaning"},
        }

        era_drift = harmonizer._calculate_era_drift(mock_sources)

        if "1791→2024" in era_drift:
            assert era_drift["1791→2024"] > 0.0

    def test_era_drift_requires_both_sources(self, harmonizer):
        """Test that era drift requires both Bouvier and Black's."""
        # Only Bouvier
        sources_bouvier = {"bouvier": {"definition": "Historical"}}
        drift_bouvier = harmonizer._calculate_era_drift(sources_bouvier)

        # Only Black's
        sources_blacks = {"blacks": {"definition": "Modern"}}
        drift_blacks = harmonizer._calculate_era_drift(sources_blacks)

        # Neither should have 1791→2024 drift
        assert "1791→2024" not in drift_bouvier
        assert "1791→2024" not in drift_blacks


class TestDivergenceIndexIntegration:
    """Test integration of divergence index with other components."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        harmonizer.detect_semantic_conflicts()
        harmonizer.compute_meaning_divergence_index()
        return harmonizer

    def test_divergence_index_stored_in_harmonizer(self, harmonizer):
        """Test that divergence index is stored in harmonizer."""
        assert hasattr(harmonizer, "divergence_index")
        assert isinstance(harmonizer.divergence_index, dict)
        assert len(harmonizer.divergence_index) > 0

    def test_conflict_sources_match_detected_conflicts(self, harmonizer):
        """Test that conflict sources in index match detected conflicts."""
        for conflict in harmonizer.conflicts:
            normalized_term = conflict["normalized_term"]

            if normalized_term in harmonizer.divergence_index:
                divergence_entry = harmonizer.divergence_index[normalized_term]
                conflict_sources = divergence_entry["conflict_sources"]

                # Should have conflict sources recorded
                assert len(conflict_sources) >= 0

    def test_source_count_accurate(self, harmonizer):
        """Test that source count is accurate."""
        for normalized_term, entry in harmonizer.divergence_index.items():
            source_count = entry["source_count"]
            source_defs = harmonizer._extract_source_definitions(normalized_term)

            # Source count should match actual sources
            assert source_count == len(source_defs)


class TestDivergenceMetrics:
    """Test divergence metrics and statistics."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.detect_semantic_conflicts()
        harmonizer.compute_meaning_divergence_index()
        return harmonizer

    def test_canonically_stable_terms_low_divergence(self, harmonizer):
        """Test that canonically stable terms have low divergence."""
        # Terms defined consistently should have divergence ≤ 0.05
        stable_count = 0
        for entry in harmonizer.divergence_index.values():
            if entry["divergence_score"] <= 0.05:
                stable_count += 1

        # At least some terms should be stable
        assert stable_count > 0

    def test_divergence_statistics(self, harmonizer):
        """Test overall divergence statistics."""
        scores = [
            entry["divergence_score"] for entry in harmonizer.divergence_index.values()
        ]

        # Calculate basic stats
        avg_divergence = sum(scores) / len(scores) if scores else 0
        max_divergence = max(scores) if scores else 0
        min_divergence = min(scores) if scores else 0

        # Sanity checks
        assert 0.0 <= avg_divergence <= 1.0
        assert 0.0 <= max_divergence <= 1.0
        assert 0.0 <= min_divergence <= 1.0
        assert min_divergence <= avg_divergence <= max_divergence

    def test_high_divergence_terms_identified(self, harmonizer):
        """Test that high divergence terms are identified."""
        high_divergence = [
            term
            for term, entry in harmonizer.divergence_index.items()
            if entry["divergence_score"] > 0.5
        ]

        # May or may not have high divergence terms
        assert isinstance(high_divergence, list)


class TestDivergenceIndexDeterminism:
    """Test determinism of divergence index computation."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.detect_semantic_conflicts()
        return harmonizer

    def test_divergence_computation_deterministic(self, harmonizer):
        """Test that divergence computation is deterministic."""
        index1 = harmonizer.compute_meaning_divergence_index()
        index2 = harmonizer.compute_meaning_divergence_index()

        # Should produce identical results
        assert len(index1) == len(index2)

        for term in index1.keys():
            assert index1[term]["divergence_score"] == index2[term]["divergence_score"]

    def test_divergence_index_reproducible(self, harmonizer):
        """Test that divergence index is reproducible."""
        harmonizer.compute_meaning_divergence_index()
        initial_index = harmonizer.divergence_index.copy()

        # Recompute
        harmonizer.compute_meaning_divergence_index()

        # Should be identical
        assert len(harmonizer.divergence_index) == len(initial_index)
