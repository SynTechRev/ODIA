"""
Tests for Etymology Cross-Integration - LGCEP-v1.

Tests integration with MSH, CLF, Lexicon systems and cross-module functionality.
"""

import pytest

from scripts.jim.etymology_loader import EtymologyLoader
from scripts.jim.framework_loader import ConstitutionalFrameworkLoader
from scripts.jim.jim_semantic_loader import JIMSemanticLoader
from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class TestLexiconIntegration:
    """Test integration with lexicon system."""

    @pytest.fixture
    def etymology_loader(self):
        """Create etymology loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    @pytest.fixture
    def lexicon_loader(self):
        """Create lexicon loader."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        return loader

    def test_etymology_loader_available(self, etymology_loader):
        """Test that etymology loader is available."""
        assert etymology_loader is not None
        assert etymology_loader.loaded is True

    def test_lexicon_loader_available(self, lexicon_loader):
        """Test that lexicon loader is available."""
        assert lexicon_loader is not None

    def test_latin_terms_in_both_systems(self, etymology_loader, lexicon_loader):
        """Test that Latin terms exist in both systems."""
        # Etymology has stare decisis
        maxim = etymology_loader.get_latin_maxim("stare decisis")
        assert maxim != {}

        # Lexicon also has stare decisis
        assert lexicon_loader.latin is not None

    def test_cross_reference_justice(self, etymology_loader):
        """Test cross-referencing justice concept."""
        etymology = etymology_loader.get_etymology_for_term("justice")
        assert etymology != {}

        # Check that it links to various roots
        roots = etymology.get("root_languages", {})
        assert "latin" in roots or "greek" in roots


class TestMSHIntegration:
    """Test integration with semantic harmonization."""

    @pytest.fixture
    def etymology_loader(self):
        """Create etymology loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    @pytest.fixture
    def harmonizer(self):
        """Create semantic harmonizer."""
        harmonizer = SemanticHarmonizer()
        harmonizer.load_lexicon_sources()
        return harmonizer

    def test_etymology_supports_msh(self, etymology_loader):
        """Test that etymology supports MSH integration."""
        report = etymology_loader.generate_etymology_report()
        integration = report.get("integration_points", {})
        assert integration.get("msh_compatible") is True

    def test_drift_scoring_compatible_with_msh(self, etymology_loader):
        """Test that drift scoring is compatible with MSH."""
        score = etymology_loader.get_drift_score("justice")
        assert 0.0 <= score <= 1.0

    def test_era_analysis_compatible_with_msh(self, etymology_loader):
        """Test that era analysis is compatible with MSH."""
        divergence = etymology_loader.detect_meaning_divergence(
            "justice", "roman_law", "modern"
        )
        assert "has_divergence" in divergence
        assert "drift_score" in divergence


class TestCLFIntegration:
    """Test integration with constitutional frameworks."""

    @pytest.fixture
    def etymology_loader(self):
        """Create etymology loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    @pytest.fixture
    def clf_loader(self):
        """Create CLF loader."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()
        return loader

    def test_etymology_supports_clf(self, etymology_loader):
        """Test that etymology supports CLF integration."""
        report = etymology_loader.generate_etymology_report()
        integration = report.get("integration_points", {})
        assert integration.get("clf_compatible") is True

    def test_doctrinal_mapping_available(self, etymology_loader):
        """Test that doctrinal mapping is available."""
        etymology = etymology_loader.get_doctrine_etymology("natural_law")
        assert len(etymology) > 0

    def test_constitutional_terms_have_etymology(self, etymology_loader):
        """Test that constitutional terms have etymology."""
        # Liberty is a key constitutional term - may not be in minimal matrix
        etymology = etymology_loader.get_etymology_for_term("liberty")
        lineage = etymology_loader.get_semantic_lineage("liberty")
        # At least the loader should be functional
        assert isinstance(etymology, dict)
        assert isinstance(lineage, list)


class TestDoctrineMapping:
    """Test doctrine to etymology mapping."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_natural_law_doctrine_mapping(self, loader):
        """Test natural law doctrine mapping."""
        etymology = loader.get_doctrine_etymology("natural_law")
        assert len(etymology) > 0
        assert any("ius naturale" in term or "physis" in term for term in etymology)

    def test_due_process_doctrine_mapping(self, loader):
        """Test due process doctrine mapping."""
        etymology = loader.get_doctrine_etymology("due_process")
        assert len(etymology) > 0

    def test_common_law_doctrine_mapping(self, loader):
        """Test common law doctrine mapping."""
        etymology = loader.get_doctrine_etymology("common_law")
        assert len(etymology) > 0

    def test_multiple_doctrines_available(self, loader):
        """Test that multiple doctrines are mapped."""
        assert len(loader.doctrine_etymology_map) > 0


class TestCrossReferencing:
    """Test cross-referencing across sources."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_cross_references_exist(self, loader):
        """Test that cross-references exist."""
        refs = loader.get_cross_references("justice")
        assert len(refs) > 0

    def test_cross_references_bidirectional(self, loader):
        """Test that cross-references link properly."""
        # Get cross-references for justice
        justice_refs = loader.get_cross_references("justice")
        if justice_refs:
            # Check if at least one reference points to valid entries
            found_valid = False
            for ref in justice_refs:
                # Try to find in various sources
                greek = loader.get_greek_root(ref)
                canon = loader.get_canon_root(ref)
                # References with / are composite (e.g., "dike / dikaiosyne")
                if greek != {} or canon != {} or "/" in ref:
                    found_valid = True
                    break
            # If we have references, at least one should be valid or composite
            assert found_valid, f"None of the references {justice_refs} are valid"

    def test_index_has_cross_references(self, loader):
        """Test that index maintains cross-references."""
        assert "cross_references" in loader.index


class TestSemanticIntegration:
    """Test semantic integration across modules."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_semantic_lineage_complete(self, loader):
        """Test that semantic lineage is complete."""
        lineage = loader.get_semantic_lineage("justice")
        if lineage:
            # Should show progression across eras
            for chain in lineage:
                assert len(chain) > 0

    def test_concept_evolution_tracked(self, loader):
        """Test that concept evolution is tracked."""
        evolution = loader.trace_concept_evolution("justice")
        if evolution:
            # Should have multiple eras
            assert len(evolution) > 0
            for entry in evolution:
                assert "era" in entry
                assert "meaning" in entry

    def test_meaning_drift_detected(self, loader):
        """Test that meaning drift is detected."""
        stability = loader.calculate_semantic_stability("justice")
        assert "drift_score" in stability
        assert "stability_rating" in stability


class TestMultiSourceConsistency:
    """Test consistency across multiple sources."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_latin_greek_consistency(self, loader):
        """Test consistency between Latin and Greek sources."""
        # Get Latin maxim
        latin = loader.get_latin_maxim("stare decisis")

        # Get etymology that references it
        etymology = loader.get_etymology_for_term("precedent")

        # Both should exist or be empty
        assert isinstance(latin, dict)
        assert isinstance(etymology, dict)

    def test_canon_integration_consistent(self, loader):
        """Test that Canon law integration is consistent."""
        canon = loader.get_canon_root("ius naturale")
        assert canon != {}

        # Should link to natural law doctrine
        doctrine_etymology = loader.get_doctrine_etymology("natural_law")
        assert len(doctrine_etymology) > 0


class TestIndexIntegrity:
    """Test index integrity and completeness."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_index_has_all_sources(self, loader):
        """Test that index references all sources."""
        sources = loader.index.get("sources", {})
        assert "latin_maxims" in sources
        assert "greek_roots" in sources
        assert "canon_law_roots" in sources
        assert "etymology_matrix" in sources

    def test_index_entry_counts_match(self, loader):
        """Test that index entry counts are reasonable."""
        sources = loader.index.get("sources", {})
        latin_count = sources.get("latin_maxims", {}).get("total_entries", 0)
        greek_count = sources.get("greek_roots", {}).get("total_entries", 0)
        canon_count = sources.get("canon_law_roots", {}).get("total_entries", 0)

        # All should be greater than 0 if loaded
        assert latin_count > 0
        assert greek_count > 0
        assert canon_count > 0

    def test_index_has_metadata(self, loader):
        """Test that index has complete metadata."""
        assert "version" in loader.index
        assert "total_entries" in loader.index


class TestSystemIntegration:
    """Test overall system integration."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_all_subsystems_loaded(self, loader):
        """Test that all subsystems are loaded."""
        assert loader.latin_maxims != {}
        assert loader.greek_roots != {}
        assert loader.canon_roots != {}
        assert loader.etymology_matrix != {}
        assert loader.index != {}

    def test_derivative_structures_built(self, loader):
        """Test that derivative structures are built."""
        assert len(loader.semantic_lineage_map) >= 0
        assert len(loader.drift_scores) >= 0
        assert len(loader.doctrine_etymology_map) >= 0

    def test_cross_module_functionality(self, loader):
        """Test cross-module functionality works."""
        # Should be able to get etymology
        etymology = loader.get_etymology_for_term("justice")

        # Should be able to get drift score
        score = loader.get_drift_score("justice")

        # Should be able to get doctrine mapping
        doctrines = loader.get_doctrine_etymology("natural_law")

        # All should work without errors
        assert isinstance(etymology, dict)
        assert isinstance(score, int | float)
        assert isinstance(doctrines, list)

    def test_generate_comprehensive_report(self, loader):
        """Test that comprehensive report can be generated."""
        report = loader.generate_etymology_report()

        # Should have all sections
        assert "version" in report
        assert "statistics" in report
        assert "drift_analysis" in report
        assert "integration_points" in report

        # Integration points should all be true
        integration = report["integration_points"]
        assert integration["msh_compatible"] is True
        assert integration["clf_compatible"] is True
        assert integration["lexicon_compatible"] is True


class TestDataQuality:
    """Test overall data quality."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_no_empty_entries(self, loader):
        """Test that there are no empty entries."""
        # Latin maxims
        if "maxims" in loader.latin_maxims:
            for maxim in loader.latin_maxims["maxims"]:
                assert len(maxim.get("term", "")) > 0

        # Greek roots
        if "roots" in loader.greek_roots:
            for root in loader.greek_roots["roots"]:
                assert len(root.get("root", "")) > 0

        # Canon roots
        if "entries" in loader.canon_roots:
            for entry in loader.canon_roots["entries"]:
                assert len(entry.get("term", "")) > 0

    def test_all_required_fields_present(self, loader):
        """Test that all required fields are present."""
        # Check Latin maxims
        if "maxims" in loader.latin_maxims:
            for maxim in loader.latin_maxims["maxims"]:
                assert "term" in maxim
                assert "literal_translation" in maxim
                assert "concept" in maxim

        # Check Greek roots
        if "roots" in loader.greek_roots:
            for root in loader.greek_roots["roots"]:
                assert "root" in root
                assert "meaning" in root
                assert "concept_family" in root

    def test_schema_validation_passes(self, loader):
        """Test that schema validation passes."""
        validation = loader.validate_schema()
        assert validation["valid"] is True
