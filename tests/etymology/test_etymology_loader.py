"""
Tests for Etymology Loader - LGCEP-v1.

Tests loading, validation, and access methods for etymological data.
"""

import pytest

from scripts.jim.etymology_loader import EtymologyLoader


class TestEtymologyLoaderInitialization:
    """Test etymology loader initialization."""

    def test_loader_initializes(self):
        """Test that loader initializes successfully."""
        loader = EtymologyLoader()
        assert loader is not None
        assert loader.VERSION == "1.0.0"
        assert loader.loaded is False

    def test_loader_has_version(self):
        """Test that loader has version info."""
        loader = EtymologyLoader()
        assert hasattr(loader, "VERSION")
        assert hasattr(loader, "SCHEMA_VERSION")


class TestSourceLoading:
    """Test loading of etymology sources."""

    @pytest.fixture
    def loader(self):
        """Create loader instance."""
        return EtymologyLoader()

    def test_load_all_sources(self, loader):
        """Test loading all etymology sources."""
        result = loader.load_all_sources()
        assert result["success"] is True
        assert loader.loaded is True

    def test_latin_maxims_loaded(self, loader):
        """Test that Latin maxims are loaded."""
        result = loader.load_all_sources()
        assert result["latin_maxims"] > 0
        assert loader.latin_maxims is not None

    def test_greek_roots_loaded(self, loader):
        """Test that Greek roots are loaded."""
        result = loader.load_all_sources()
        assert result["greek_roots"] > 0
        assert loader.greek_roots is not None

    def test_canon_roots_loaded(self, loader):
        """Test that Canon law roots are loaded."""
        result = loader.load_all_sources()
        assert result["canon_roots"] > 0
        assert loader.canon_roots is not None

    def test_etymology_matrix_loaded(self, loader):
        """Test that etymology matrix is loaded."""
        result = loader.load_all_sources()
        assert result["matrix_entries"] >= 0
        assert loader.etymology_matrix is not None

    def test_index_loaded(self, loader):
        """Test that index is loaded."""
        loader.load_all_sources()
        assert loader.index is not None
        assert "sources" in loader.index

    def test_total_entries_count(self, loader):
        """Test that total entries are counted correctly."""
        result = loader.load_all_sources()
        assert result["total_entries"] > 0


class TestLatinMaxims:
    """Test Latin maxims access."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_latin_maxim_stare_decisis(self, loader):
        """Test retrieval of stare decisis maxim."""
        maxim = loader.get_latin_maxim("stare decisis")
        assert maxim != {}
        assert "literal_translation" in maxim
        assert "concept" in maxim

    def test_get_latin_maxim_res_judicata(self, loader):
        """Test retrieval of res judicata maxim."""
        maxim = loader.get_latin_maxim("res judicata")
        assert maxim != {}
        assert maxim.get("concept") == "claim preclusion"

    def test_get_latin_maxim_not_found(self, loader):
        """Test retrieval of non-existent maxim."""
        maxim = loader.get_latin_maxim("nonexistent_maxim")
        assert maxim == {}

    def test_latin_maxims_have_doctrines(self, loader):
        """Test that Latin maxims have doctrine mappings."""
        maxim = loader.get_latin_maxim("audi alteram partem")
        assert maxim != {}
        assert "doctrines" in maxim
        assert len(maxim["doctrines"]) > 0

    def test_latin_maxims_have_citations(self, loader):
        """Test that Latin maxims have citations."""
        maxim = loader.get_latin_maxim("habeas corpus")
        assert maxim != {}
        assert "citations" in maxim


class TestGreekRoots:
    """Test Greek roots access."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_greek_root_dike(self, loader):
        """Test retrieval of dike root."""
        root = loader.get_greek_root("dike")
        assert root != {}
        assert "meaning" in root
        assert "concept_family" in root

    def test_get_greek_root_nomos(self, loader):
        """Test retrieval of nomos root."""
        root = loader.get_greek_root("nomos")
        assert root != {}
        assert root.get("meaning") == "law; custom; convention"

    def test_get_greek_root_not_found(self, loader):
        """Test retrieval of non-existent root."""
        root = loader.get_greek_root("nonexistent_root")
        assert root == {}

    def test_greek_roots_have_philosophers(self, loader):
        """Test that Greek roots reference philosophers."""
        root = loader.get_greek_root("logos")
        assert root != {}
        assert "philosophers" in root
        assert len(root["philosophers"]) > 0

    def test_greek_roots_have_semantic_chain(self, loader):
        """Test that Greek roots have semantic chains."""
        root = loader.get_greek_root("eleutheria")
        assert root != {}
        assert "semantic_chain" in root


class TestCanonLawRoots:
    """Test Canon law roots access."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_canon_root_ius_gentium(self, loader):
        """Test retrieval of ius gentium."""
        root = loader.get_canon_root("ius gentium")
        assert root != {}
        assert "category" in root
        assert "influence_on" in root

    def test_get_canon_root_ius_naturale(self, loader):
        """Test retrieval of ius naturale."""
        root = loader.get_canon_root("ius naturale")
        assert root != {}
        assert root.get("category") == "natural law"

    def test_get_canon_root_not_found(self, loader):
        """Test retrieval of non-existent root."""
        root = loader.get_canon_root("nonexistent_root")
        assert root == {}

    def test_canon_roots_have_sources(self, loader):
        """Test that Canon roots have canonical sources."""
        root = loader.get_canon_root("dignitas humana")
        assert root != {}
        assert "canonical_source" in root

    def test_canon_roots_have_semantic_notes(self, loader):
        """Test that Canon roots have semantic notes."""
        root = loader.get_canon_root("conscientia")
        assert root != {}
        assert "semantic_notes" in root


class TestEtymologyMatrix:
    """Test etymology matrix access."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_etymology_for_justice(self, loader):
        """Test retrieval of justice etymology."""
        etymology = loader.get_etymology_for_term("justice")
        assert etymology != {}
        assert "root_languages" in etymology
        assert "semantic_lineage" in etymology

    def test_get_etymology_for_law(self, loader):
        """Test retrieval of law etymology."""
        etymology = loader.get_etymology_for_term("law")
        assert etymology != {}
        assert etymology.get("root_languages", {}).get("greek") == "nomos"

    def test_etymology_has_drift_score(self, loader):
        """Test that etymology entries have drift scores."""
        etymology = loader.get_etymology_for_term("justice")
        assert etymology != {}
        assert "drift_score" in etymology
        assert 0.0 <= etymology["drift_score"] <= 1.0

    def test_etymology_has_era_meanings(self, loader):
        """Test that etymology entries have era meanings."""
        etymology = loader.get_etymology_for_term("justice")
        assert etymology != {}
        assert "era_meanings" in etymology
        era_meanings = etymology["era_meanings"]
        assert "classical_greek" in era_meanings or "roman_law" in era_meanings

    def test_etymology_has_doctrines(self, loader):
        """Test that etymology entries map to doctrines."""
        etymology = loader.get_etymology_for_term("justice")
        assert etymology != {}
        assert "legal_doctrines" in etymology


class TestSemanticLineage:
    """Test semantic lineage tracing."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_semantic_lineage_justice(self, loader):
        """Test semantic lineage for justice."""
        lineage = loader.get_semantic_lineage("justice")
        assert len(lineage) > 0
        assert any("dike" in line.lower() for line in lineage)

    def test_get_semantic_lineage_law(self, loader):
        """Test semantic lineage for law."""
        lineage = loader.get_semantic_lineage("law")
        assert len(lineage) > 0
        assert any("nomos" in line.lower() for line in lineage)

    def test_semantic_lineage_not_found(self, loader):
        """Test semantic lineage for unknown term."""
        lineage = loader.get_semantic_lineage("nonexistent_term")
        assert lineage == []


class TestDriftScoring:
    """Test semantic drift scoring."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_drift_score_justice(self, loader):
        """Test drift score for justice."""
        score = loader.get_drift_score("justice")
        assert 0.0 <= score <= 1.0

    def test_get_drift_score_law(self, loader):
        """Test drift score for law."""
        score = loader.get_drift_score("law")
        assert 0.0 <= score <= 1.0

    def test_drift_score_not_found(self, loader):
        """Test drift score for unknown term."""
        score = loader.get_drift_score("nonexistent_term")
        assert score == 0.0

    def test_calculate_semantic_stability(self, loader):
        """Test semantic stability calculation."""
        stability = loader.calculate_semantic_stability("justice")
        assert "drift_score" in stability
        assert "stability_rating" in stability
        assert stability["stability_rating"] in [
            "stable",
            "moderate_drift",
            "significant_drift",
            "unknown",
        ]

    def test_semantic_stability_includes_era_meanings(self, loader):
        """Test that semantic stability includes era meanings."""
        stability = loader.calculate_semantic_stability("justice")
        assert "era_meanings" in stability


class TestMeaningDivergence:
    """Test meaning divergence detection."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_detect_meaning_divergence_justice(self, loader):
        """Test divergence detection for justice."""
        divergence = loader.detect_meaning_divergence("justice", "roman_law", "modern")
        assert "has_divergence" in divergence
        assert "source_meaning" in divergence
        assert "target_meaning" in divergence

    def test_detect_meaning_divergence_law(self, loader):
        """Test divergence detection for law."""
        divergence = loader.detect_meaning_divergence(
            "law", "classical_greek", "modern"
        )
        assert "drift_score" in divergence


class TestConceptEvolution:
    """Test concept evolution tracing."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_trace_concept_evolution_justice(self, loader):
        """Test evolution tracing for justice."""
        evolution = loader.trace_concept_evolution("justice")
        assert len(evolution) > 0
        for entry in evolution:
            assert "era" in entry
            assert "meaning" in entry

    def test_trace_concept_evolution_law(self, loader):
        """Test evolution tracing for law."""
        evolution = loader.trace_concept_evolution("law")
        assert len(evolution) > 0


class TestDoctrineEtymology:
    """Test doctrine etymology mapping."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_doctrine_etymology_natural_law(self, loader):
        """Test etymology for natural law doctrine."""
        etymology = loader.get_doctrine_etymology("natural_law")
        assert len(etymology) > 0
        assert any("ius naturale" in term for term in etymology)

    def test_get_doctrine_etymology_due_process(self, loader):
        """Test etymology for due process doctrine."""
        etymology = loader.get_doctrine_etymology("due_process")
        assert len(etymology) > 0

    def test_doctrine_etymology_not_found(self, loader):
        """Test etymology for unknown doctrine."""
        etymology = loader.get_doctrine_etymology("nonexistent_doctrine")
        assert etymology == []


class TestCrossReferences:
    """Test cross-reference functionality."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_get_cross_references_justice(self, loader):
        """Test cross-references for justice."""
        refs = loader.get_cross_references("justice")
        assert len(refs) > 0
        assert "dike" in refs or "iustitia" in refs

    def test_get_cross_references_law(self, loader):
        """Test cross-references for law."""
        refs = loader.get_cross_references("law")
        assert len(refs) > 0


class TestSchemaValidation:
    """Test schema validation."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_validate_schema_success(self, loader):
        """Test that schema validation passes."""
        result = loader.validate_schema()
        assert result["valid"] is True
        assert len(result.get("errors", [])) == 0

    def test_validate_schema_before_load(self):
        """Test schema validation before loading."""
        loader = EtymologyLoader()
        result = loader.validate_schema()
        assert result["valid"] is False


class TestReportGeneration:
    """Test report generation."""

    @pytest.fixture
    def loader(self):
        """Create and load loader."""
        loader = EtymologyLoader()
        loader.load_all_sources()
        return loader

    def test_generate_etymology_report(self, loader):
        """Test etymology report generation."""
        report = loader.generate_etymology_report()
        assert "version" in report
        assert "statistics" in report
        assert "drift_analysis" in report

    def test_report_includes_statistics(self, loader):
        """Test that report includes statistics."""
        report = loader.generate_etymology_report()
        stats = report["statistics"]
        assert "latin_maxims" in stats
        assert "greek_roots" in stats
        assert "canon_roots" in stats

    def test_report_includes_drift_analysis(self, loader):
        """Test that report includes drift analysis."""
        report = loader.generate_etymology_report()
        drift = report["drift_analysis"]
        assert "stable_terms" in drift
        assert "moderate_drift" in drift
        assert "significant_drift" in drift

    def test_report_includes_integration_points(self, loader):
        """Test that report includes integration points."""
        report = loader.generate_etymology_report()
        integration = report["integration_points"]
        assert integration["msh_compatible"] is True
        assert integration["clf_compatible"] is True
        assert integration["lexicon_compatible"] is True
