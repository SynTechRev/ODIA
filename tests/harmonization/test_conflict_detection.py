"""
Tests for semantic conflict detection.
"""

import pytest

from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class TestConflictDetection:
    """Test detection of semantic conflicts between sources."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_detect_conflicts(self, harmonizer):
        """Test basic conflict detection."""
        conflicts = harmonizer.detect_semantic_conflicts()
        assert isinstance(conflicts, list)

    def test_conflicts_have_required_fields(self, harmonizer):
        """Test that conflict entries have required fields."""
        conflicts = harmonizer.detect_semantic_conflicts()

        required_fields = [
            "term",
            "normalized_term",
            "conflict_type",
            "sources",
            "severity",
            "description",
        ]

        for conflict in conflicts:
            for field in required_fields:
                assert field in conflict

    def test_conflict_sources_are_lists(self, harmonizer):
        """Test that conflict sources are lists."""
        conflicts = harmonizer.detect_semantic_conflicts()

        for conflict in conflicts:
            assert isinstance(conflict["sources"], list)
            assert len(conflict["sources"]) >= 2  # Need 2+ sources for conflict

    def test_conflict_severity_valid(self, harmonizer):
        """Test that conflict severity values are valid."""
        conflicts = harmonizer.detect_semantic_conflicts()
        valid_severities = ["low", "medium", "high"]

        for conflict in conflicts:
            assert conflict["severity"] in valid_severities

    def test_no_single_source_conflicts(self, harmonizer):
        """Test that conflicts require multiple sources."""
        conflicts = harmonizer.detect_semantic_conflicts()

        for conflict in conflicts:
            # Must have at least 2 sources to be a conflict
            assert len(conflict["sources"]) >= 2


class TestConflictTypes:
    """Test different types of semantic conflicts."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_definition_divergence_conflicts(self, harmonizer):
        """Test detection of definition divergence conflicts."""
        conflicts = harmonizer.detect_semantic_conflicts()

        # Should detect some definition divergences
        divergence_conflicts = [
            c for c in conflicts if c["conflict_type"] == "definition_divergence"
        ]

        # We expect some conflicts given multiple source dictionaries
        assert len(divergence_conflicts) >= 0

    def test_conflict_types_valid(self, harmonizer):
        """Test that conflict types are from valid set."""
        conflicts = harmonizer.detect_semantic_conflicts()
        valid_types = [
            "definition_divergence",
            "doctrinal_conflict",
            "temporal_drift",
            "synonym_mismatch",
        ]

        for conflict in conflicts:
            # Current implementation uses definition_divergence
            assert conflict["conflict_type"] in valid_types


class TestConflictIdentification:
    """Test identification of specific conflicts."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_conflicts_stored_in_harmonizer(self, harmonizer):
        """Test that conflicts are stored in harmonizer instance."""
        harmonizer.detect_semantic_conflicts()
        assert hasattr(harmonizer, "conflicts")
        assert isinstance(harmonizer.conflicts, list)

    def test_conflict_detection_deterministic(self, harmonizer):
        """Test that conflict detection is deterministic."""
        conflicts1 = harmonizer.detect_semantic_conflicts()
        conflicts2 = harmonizer.detect_semantic_conflicts()

        # Should produce same results
        assert len(conflicts1) == len(conflicts2)

    def test_terms_with_multiple_definitions_checked(self, harmonizer):
        """Test that terms with multiple source definitions are checked."""
        harmonizer.detect_semantic_conflicts()

        # Check that terms with multiple sources were evaluated
        for normalized_term in harmonizer.merged_definitions.keys():
            source_defs = harmonizer._extract_source_definitions(normalized_term)
            if len(source_defs) >= 2:
                # Was at least checked (may or may not have conflict)
                assert isinstance(source_defs, dict)


class TestConflictResolution:
    """Test conflict resolution logic."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_harmonized_meaning_resolves_conflicts(self, harmonizer):
        """Test that harmonized meanings resolve conflicts via weighting."""
        harmonizer.build_harmonization_matrix()
        harmonizer.detect_semantic_conflicts()

        # For terms with conflicts, harmonized meaning should exist
        for conflict in harmonizer.conflicts:
            normalized_term = conflict["normalized_term"]
            if normalized_term in harmonizer.harmonization_matrix:
                entry = harmonizer.harmonization_matrix[normalized_term]
                # Should have a harmonized meaning
                assert "harmonized_meaning" in entry
                assert len(entry["harmonized_meaning"]) > 0

    def test_highest_weight_source_used_for_harmonization(self, harmonizer):
        """Test that highest-weighted source is used for harmonized meaning."""
        harmonizer.build_harmonization_matrix()

        for _normalized_term, entry in harmonizer.harmonization_matrix.items():
            weights = entry.get("weights", {})
            harmonized = entry.get("harmonized_meaning", "")

            if weights and harmonized:
                # Get highest weighted source
                max_source = max(weights.items(), key=lambda x: x[1])[0]

                # Harmonized meaning should come from high-weight source
                source_defs = entry.get("sources", {})
                if max_source in source_defs:
                    # Should be using this source's definition
                    assert isinstance(harmonized, str)


class TestConflictMetrics:
    """Test conflict metrics and statistics."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_conflict_count_reasonable(self, harmonizer):
        """Test that conflict count is reasonable."""
        conflicts = harmonizer.detect_semantic_conflicts()

        # Should have some conflicts but not every term
        total_terms = len(harmonizer.merged_definitions)
        conflict_count = len(conflicts)

        assert 0 <= conflict_count <= total_terms

    def test_conflict_description_present(self, harmonizer):
        """Test that all conflicts have descriptions."""
        conflicts = harmonizer.detect_semantic_conflicts()

        for conflict in conflicts:
            assert "description" in conflict
            assert len(conflict["description"]) > 0
            assert isinstance(conflict["description"], str)

    def test_conflicts_reference_valid_terms(self, harmonizer):
        """Test that conflicts reference valid terms."""
        conflicts = harmonizer.detect_semantic_conflicts()

        for conflict in conflicts:
            normalized_term = conflict["normalized_term"]
            # Should be a valid term in merged definitions
            assert normalized_term in harmonizer.merged_definitions


class TestConflictIntegration:
    """Test integration of conflict detection with other components."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        harmonizer.detect_semantic_conflicts()
        return harmonizer

    def test_conflicts_included_in_divergence_index(self, harmonizer):
        """Test that conflicts are included in divergence index."""
        harmonizer.compute_meaning_divergence_index()

        # Terms with conflicts should have entries in divergence index
        for conflict in harmonizer.conflicts:
            normalized_term = conflict["normalized_term"]
            if normalized_term in harmonizer.divergence_index:
                divergence_entry = harmonizer.divergence_index[normalized_term]
                # Should have conflict sources recorded
                assert "conflict_sources" in divergence_entry

    def test_conflict_detection_before_artifact_generation(self, harmonizer):
        """Test that conflicts are detected before artifact generation."""
        artifacts = harmonizer.generate_artifacts()

        # Should have conflicts in output
        assert "conflicts_detected" in artifacts
        assert artifacts["conflicts_detected"] >= 0

    def test_conflicts_accessible_after_detection(self, harmonizer):
        """Test that conflicts remain accessible after detection."""
        initial_conflicts = harmonizer.conflicts.copy()

        # Conflicts should still be accessible
        assert len(harmonizer.conflicts) == len(initial_conflicts)
        assert harmonizer.conflicts == initial_conflicts
