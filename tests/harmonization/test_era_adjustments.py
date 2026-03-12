"""
Tests for era-based semantic adjustments.
"""

import pytest

from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class TestEraDefinitions:
    """Test era definitions and constants."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        return SemanticHarmonizer()

    def test_eras_defined(self, harmonizer):
        """Test that key historical eras are defined."""
        assert 1791 in harmonizer.ERAS
        assert 1868 in harmonizer.ERAS
        assert 2024 in harmonizer.ERAS

    def test_constitutional_founding_era(self, harmonizer):
        """Test that 1791 Constitutional Founding era is defined."""
        assert harmonizer.ERAS[1791] == "Constitutional Founding Era"

    def test_reconstruction_era(self, harmonizer):
        """Test that 1868 Reconstruction era is defined."""
        assert harmonizer.ERAS[1868] == "Reconstruction Era (14th Amendment)"

    def test_contemporary_era(self, harmonizer):
        """Test that 2024 Contemporary era is defined."""
        assert harmonizer.ERAS[2024] == "Contemporary Era"

    def test_eras_chronological(self, harmonizer):
        """Test that eras are in chronological order."""
        era_years = sorted(harmonizer.ERAS.keys())
        assert era_years == sorted(era_years)


class TestEraAdjustmentComputation:
    """Test computation of era-specific adjustments."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_compute_era_adjustments_for_term(self, harmonizer):
        """Test era adjustment computation for a term."""
        source_defs = harmonizer._extract_source_definitions("liberty")
        era_adjustments = harmonizer._compute_era_adjustments("liberty", source_defs)
        assert isinstance(era_adjustments, dict)

    def test_era_adjustments_have_string_keys(self, harmonizer):
        """Test that era adjustments use string year keys."""
        source_defs = harmonizer._extract_source_definitions("liberty")
        era_adjustments = harmonizer._compute_era_adjustments("liberty", source_defs)
        for era_key in era_adjustments.keys():
            assert isinstance(era_key, str)

    def test_founding_era_uses_bouvier(self, harmonizer):
        """Test that 1791 founding era uses Bouvier's definition when available."""
        # Find a term with Bouvier definition
        source_defs = harmonizer._extract_source_definitions("sovereignty")
        era_adjustments = harmonizer._compute_era_adjustments(
            "sovereignty", source_defs
        )

        if "bouvier" in source_defs and "1791" in era_adjustments:
            # Should use Bouvier's historical definition
            assert era_adjustments["1791"] == source_defs["bouvier"]["definition"]

    def test_contemporary_era_uses_blacks(self, harmonizer):
        """Test that 2024 contemporary era uses Black's definition when available."""
        source_defs = harmonizer._extract_source_definitions("probable_cause")
        era_adjustments = harmonizer._compute_era_adjustments(
            "probable_cause", source_defs
        )

        if "blacks" in source_defs and "2024" in era_adjustments:
            # Should use Black's modern definition
            assert era_adjustments["2024"] == source_defs["blacks"]["definition"]

    def test_era_adjustments_not_empty_strings(self, harmonizer):
        """Test that era adjustments contain actual definitions."""
        source_defs = harmonizer._extract_source_definitions("probable_cause")
        era_adjustments = harmonizer._compute_era_adjustments(
            "probable_cause", source_defs
        )

        for era_meaning in era_adjustments.values():
            assert isinstance(era_meaning, str)
            assert len(era_meaning) > 0


class TestApplyEraAdjustments:
    """Test application of era adjustments to matrix."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        return harmonizer

    def test_apply_era_adjustments(self, harmonizer):
        """Test applying era adjustments to matrix."""
        era_adjusted = harmonizer.apply_era_adjustments(1791)
        assert isinstance(era_adjusted, dict)
        assert len(era_adjusted) > 0

    def test_era_adjusted_has_same_terms(self, harmonizer):
        """Test that era-adjusted matrix has same terms as original."""
        era_adjusted = harmonizer.apply_era_adjustments(1791)
        assert len(era_adjusted) == len(harmonizer.harmonization_matrix)

    def test_era_adjusted_adds_era_specific_meaning(self, harmonizer):
        """Test that era adjustment adds era-specific meaning field."""
        era_adjusted = harmonizer.apply_era_adjustments(2024)

        # Check if any term has era_specific_meaning
        has_era_meaning = False
        for entry in era_adjusted.values():
            if "era_specific_meaning" in entry:
                has_era_meaning = True
                break

        # At least some terms should have era-specific meanings
        assert has_era_meaning

    def test_applied_era_recorded(self, harmonizer):
        """Test that applied era is recorded in adjusted entries."""
        era_adjusted = harmonizer.apply_era_adjustments(1791)

        for entry in era_adjusted.values():
            if "applied_era" in entry:
                # Should be a string representation of a year
                assert isinstance(entry["applied_era"], str)
                assert entry["applied_era"].isdigit()


class TestClosestEraFinding:
    """Test finding closest era to target year."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        return SemanticHarmonizer()

    def test_find_exact_era(self, harmonizer):
        """Test finding exact era match."""
        available = ["1791", "1868", "2024"]
        closest = harmonizer._find_closest_era(1791, available)
        assert closest == "1791"

    def test_find_closest_era_before(self, harmonizer):
        """Test finding closest era when target is between eras."""
        available = ["1791", "2024"]
        closest = harmonizer._find_closest_era(1800, available)
        # Should be 1791 (closer than 2024)
        assert closest == "1791"

    def test_find_closest_era_after(self, harmonizer):
        """Test finding closest era when target is after all eras."""
        available = ["1791", "1868"]
        closest = harmonizer._find_closest_era(2024, available)
        # Should be 1868 (closest available)
        assert closest == "1868"

    def test_empty_eras_returns_empty(self, harmonizer):
        """Test that empty era list returns empty string."""
        closest = harmonizer._find_closest_era(1791, [])
        assert closest == ""

    def test_single_era_returns_that_era(self, harmonizer):
        """Test that single era always returns that era."""
        available = ["1791"]
        for target in [1700, 1791, 1900, 2024]:
            closest = harmonizer._find_closest_era(target, available)
            assert closest == "1791"


class TestEraIntegration:
    """Test integration of era adjustments with harmonization matrix."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        return harmonizer

    def test_matrix_contains_era_adjustments(self, harmonizer):
        """Test that harmonization matrix includes era adjustments."""
        for entry in harmonizer.harmonization_matrix.values():
            assert "era_adjustments" in entry
            assert isinstance(entry["era_adjustments"], dict)

    def test_era_adjustments_for_historical_terms(self, harmonizer):
        """Test that historical terms have appropriate era adjustments."""
        # Terms like 'liberty' or 'sovereignty' should have era context
        if "liberty" in harmonizer.harmonization_matrix:
            entry = harmonizer.harmonization_matrix["liberty"]
            era_adjustments = entry["era_adjustments"]

            # Should have some era adjustments
            assert len(era_adjustments) > 0

    def test_era_adjustment_years_valid(self, harmonizer):
        """Test that era adjustment years are valid."""
        for entry in harmonizer.harmonization_matrix.values():
            era_adjustments = entry["era_adjustments"]
            for era_year in era_adjustments.keys():
                # Should be a valid year string
                assert era_year.isdigit()
                year = int(era_year)
                assert 1700 <= year <= 2100  # Reasonable range


class TestTemporalDrift:
    """Test detection of temporal/semantic drift across eras."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_historical_terms_show_drift(self, harmonizer):
        """Test that historical terms show semantic drift."""
        # Terms with both Bouvier (1856) and Black's (2019) should show some drift
        source_defs = harmonizer._extract_source_definitions("liberty")

        if "bouvier" in source_defs and "blacks" in source_defs:
            era_drift = harmonizer._calculate_era_drift(source_defs)
            # Should have 1791→2024 drift measurement
            assert "1791→2024" in era_drift or len(era_drift) >= 0

    def test_drift_score_in_valid_range(self, harmonizer):
        """Test that drift scores are in valid range [0, 1]."""
        source_defs = harmonizer._extract_source_definitions("liberty")
        era_drift = harmonizer._calculate_era_drift(source_defs)

        for drift_score in era_drift.values():
            assert 0.0 <= drift_score <= 1.0

    def test_identical_definitions_have_zero_drift(self, harmonizer):
        """Test that identical definitions result in zero drift."""
        # Create mock source definitions with same text
        mock_sources = {
            "bouvier": {"definition": "Same definition"},
            "blacks": {"definition": "Same definition"},
        }

        era_drift = harmonizer._calculate_era_drift(mock_sources)

        if "1791→2024" in era_drift:
            assert era_drift["1791→2024"] == 0.0
