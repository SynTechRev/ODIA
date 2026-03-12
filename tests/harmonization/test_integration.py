"""
Integration tests for MSH-v1 with ACE and JIM.
"""

import pytest

from scripts.jim.jim_core import JIMCore
from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class TestACEIntegration:
    """Test integration with ACE (Anomaly Correlation Engine)."""

    def test_ace_has_semantic_misalignment_category(self):
        """Test that ACE includes semantic_misalignment anomaly type."""
        from scripts.ace_analyzer import ANOMALY_CATEGORIES

        assert "semantic_misalignment" in ANOMALY_CATEGORIES

    def test_semantic_misalignment_in_anomaly_list(self):
        """Test that semantic_misalignment can be used in anomaly detection."""
        from scripts.ace_analyzer import ANOMALY_CATEGORIES

        # Should be one of the valid categories
        assert "semantic_misalignment" in ANOMALY_CATEGORIES
        assert len(ANOMALY_CATEGORIES) >= 7  # Original 6 + new 1


class TestJIMIntegration:
    """Test integration with JIM (Judicial Interpretive Matrix)."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        return harmonizer

    @pytest.fixture
    def jim(self):
        """Create JIM instance."""
        jim = JIMCore()
        jim.initialize()
        return jim

    def test_jim_can_load_harmonization_matrix(self, jim, harmonizer):
        """Test that JIM can load harmonization matrix."""
        result = jim.load_harmonization_matrix(harmonizer.harmonization_matrix)

        assert result["success"] is True
        assert result["terms_loaded"] > 0

    def test_jim_stores_harmonization_matrix(self, jim, harmonizer):
        """Test that JIM stores harmonization matrix."""
        jim.load_harmonization_matrix(harmonizer.harmonization_matrix)

        assert len(jim.harmonization_matrix) > 0
        assert jim.harmonization_matrix == harmonizer.harmonization_matrix

    def test_jim_can_set_era(self, jim):
        """Test that JIM can set analysis era."""
        result = jim.set_era(1791)

        assert result["success"] is True
        assert result["era"] == 1791

    def test_jim_era_stored(self, jim):
        """Test that JIM stores current era."""
        jim.set_era(1791)
        assert jim.current_era == 1791

        jim.set_era(2024)
        assert jim.current_era == 2024

    def test_jim_era_with_harmonization(self, jim, harmonizer):
        """Test that JIM tracks harmonization status with era."""
        # Before loading harmonization
        result = jim.set_era(1791)
        assert result["harmonization_loaded"] is False

        # After loading harmonization
        jim.load_harmonization_matrix(harmonizer.harmonization_matrix)
        result = jim.set_era(2024)
        assert result["harmonization_loaded"] is True


class TestHarmonizationWorkflow:
    """Test complete harmonization workflow with ACE and JIM."""

    def test_complete_harmonization_workflow(self):
        """Test complete workflow: Harmonizer -> JIM -> Analysis."""
        # Step 1: Build harmonization matrix
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        harmonizer.detect_semantic_conflicts()
        harmonizer.compute_meaning_divergence_index()

        # Step 2: Initialize JIM
        jim = JIMCore()
        jim.initialize()

        # Step 3: Load harmonization into JIM
        load_result = jim.load_harmonization_matrix(harmonizer.harmonization_matrix)
        assert load_result["success"] is True

        # Step 4: Set era for analysis
        era_result = jim.set_era(1791)
        assert era_result["success"] is True

        # Step 5: Verify JIM has harmonization context
        assert len(jim.harmonization_matrix) > 0
        assert jim.current_era == 1791

    def test_harmonization_with_semantic_misalignment_anomaly(self):
        """Test that semantic misalignment anomalies can be processed."""
        from scripts.ace_analyzer import ANOMALY_CATEGORIES

        # Create semantic misalignment anomaly
        anomaly = {
            "id": "test_semantic_1",
            "type": "semantic_misalignment",
            "term": "probable_cause",
            "description": "Agency uses non-standard definition",
        }

        # Verify it's a valid anomaly type
        assert anomaly["type"] in ANOMALY_CATEGORIES


class TestCAIMIntegration:
    """Test CAIM integration comments."""

    def test_caim_has_msh_integration_comment(self):
        """Test that CAIM module has MSH-v1 integration documentation."""
        import scripts.cross_agency_influence as caim

        # Check module docstring mentions MSH-v1
        assert caim.__doc__ is not None
        assert "MSH-v1" in caim.__doc__


class TestVICFMIntegration:
    """Test VICFM integration comments."""

    def test_vicfm_has_msh_integration_comment(self):
        """Test that VICFM module has MSH-v1 integration documentation."""
        import scripts.vendor_map_extractor as vicfm

        # Check module docstring mentions MSH-v1
        assert vicfm.__doc__ is not None
        assert "MSH-v1" in vicfm.__doc__


class TestEraSpecificAnalysis:
    """Test era-specific legal analysis."""

    @pytest.fixture
    def harmonizer(self):
        """Create harmonizer instance."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        harmonizer.build_harmonization_matrix()
        return harmonizer

    def test_constitutional_era_analysis(self, harmonizer):
        """Test analysis with Constitutional Founding era (1791)."""
        jim = JIMCore()
        jim.initialize()
        jim.load_harmonization_matrix(harmonizer.harmonization_matrix)
        jim.set_era(1791)

        # Verify era is set
        assert jim.current_era == 1791

        # Apply era adjustments
        era_adjusted = harmonizer.apply_era_adjustments(1791)
        assert len(era_adjusted) > 0

    def test_contemporary_era_analysis(self, harmonizer):
        """Test analysis with contemporary era (2024)."""
        jim = JIMCore()
        jim.initialize()
        jim.load_harmonization_matrix(harmonizer.harmonization_matrix)
        jim.set_era(2024)

        # Verify era is set
        assert jim.current_era == 2024

        # Apply era adjustments
        era_adjusted = harmonizer.apply_era_adjustments(2024)
        assert len(era_adjusted) > 0

    def test_era_switching(self, harmonizer):
        """Test switching between different eras."""
        jim = JIMCore()
        jim.initialize()
        jim.load_harmonization_matrix(harmonizer.harmonization_matrix)

        # Switch to 1791
        jim.set_era(1791)
        assert jim.current_era == 1791

        # Switch to 1868
        jim.set_era(1868)
        assert jim.current_era == 1868

        # Switch to 2024
        jim.set_era(2024)
        assert jim.current_era == 2024
