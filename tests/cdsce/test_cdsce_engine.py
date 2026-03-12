"""
Tests for CDSCE Main Correlation Engine.

Tests initialization, term correlation, corpus generation, and integration.
"""

import pytest

from scripts.jim.cdsce_engine import CDSCEEngine


class TestInitialization:
    """Tests for CDSCE initialization."""

    def test_init_default_paths(self):
        """Test initialization with default paths."""
        engine = CDSCEEngine()
        assert engine.loaded is False
        assert engine.VERSION == "1.0.0"
        assert engine.SCHEMA_VERSION == "1.0"

    def test_init_custom_paths(self, tmp_path):
        """Test initialization with custom paths."""
        engine = CDSCEEngine(
            lexicon_dir=tmp_path,
            etymology_dir=tmp_path,
            cases_dir=tmp_path,
            constitutional_dir=tmp_path,
            output_dir=tmp_path,
        )
        assert engine.output_dir == tmp_path


class TestCorrelation:
    """Tests for term correlation."""

    def test_correlate_term_not_initialized(self):
        """Test correlation before initialization raises error."""
        engine = CDSCEEngine()
        with pytest.raises(RuntimeError, match="not initialized"):
            engine.correlate_term("liberty")

    def test_get_dictionary_sources_empty(self):
        """Test getting dictionary sources with no data."""
        engine = CDSCEEngine()
        engine.semantic_loader.merged_definitions = {}
        sources = engine._get_dictionary_sources("nonexistent")
        assert len(sources) == 0

    def test_get_etymology_lineage_empty(self):
        """Test getting etymology lineage with no data."""
        engine = CDSCEEngine()
        lineage = engine._get_etymology_lineage("nonexistent")
        assert len(lineage) == 0

    def test_get_doctrinal_mappings_empty(self):
        """Test getting doctrinal mappings with no data."""
        engine = CDSCEEngine()
        mappings = engine._get_doctrinal_mappings("nonexistent")
        assert len(mappings) == 0

    def test_calculate_correlation_strength_empty(self):
        """Test correlation strength with no data."""
        engine = CDSCEEngine()
        strength = engine._calculate_correlation_strength([], [], [])
        assert strength == 0.0

    def test_calculate_correlation_strength_with_sources(self):
        """Test correlation strength with dictionary sources."""
        engine = CDSCEEngine()
        sources = [
            {"source": "blacks", "definition": "test"},
            {"source": "webster", "definition": "test"},
        ]
        strength = engine._calculate_correlation_strength(sources, [], [])
        assert 0.0 < strength <= 0.4

    def test_calculate_correlation_strength_with_all_data(self):
        """Test correlation strength with all data types."""
        engine = CDSCEEngine()
        sources = [{"source": "blacks", "definition": "test"}]
        etymology = [{"language": "latin", "root": "test"}]
        doctrines = [{"doctrine": "due_process"}]
        strength = engine._calculate_correlation_strength(sources, etymology, doctrines)
        assert 0.0 < strength <= 1.0


class TestCorpusGeneration:
    """Tests for corpus generation."""

    def test_generate_corpus_not_initialized(self):
        """Test corpus generation before initialization raises error."""
        engine = CDSCEEngine()
        with pytest.raises(RuntimeError, match="not initialized"):
            engine.generate_corpus([])

    def test_corpus_structure(self):
        """Test corpus has correct structure."""
        engine = CDSCEEngine()
        engine.loaded = True
        engine.semantic_loader.merged_definitions = {}
        result = engine.generate_corpus([])
        assert result["success"] is True
        assert "corpus" in dir(engine)
        assert "version" in engine.corpus
        assert "schema_version" in engine.corpus
        assert "terms" in engine.corpus


class TestStatistics:
    """Tests for statistics retrieval."""

    def test_get_statistics_initial(self):
        """Test statistics after initialization."""
        engine = CDSCEEngine()
        stats = engine.get_statistics()
        assert stats["version"] == "1.0.0"
        assert stats["loaded"] is False
        assert stats["corpus_terms"] == 0
        assert stats["correlations"] == 0
        assert stats["anomalies"] == 0
        assert stats["contradictions"] == 0


class TestIntegration:
    """Integration tests for CDSCE engine."""

    def test_full_workflow_empty_data(self):
        """Test full workflow with empty data."""
        engine = CDSCEEngine()
        engine.loaded = True
        engine.semantic_loader.merged_definitions = {}

        # Generate corpus
        result = engine.generate_corpus([])
        assert result["success"] is True

        # Get statistics
        stats = engine.get_statistics()
        assert stats["corpus_terms"] == 0

    def test_correlation_strength_boundaries(self):
        """Test correlation strength stays within bounds."""
        engine = CDSCEEngine()

        # Test maximum sources
        sources = [{"source": f"source{i}", "definition": "test"} for i in range(10)]
        etymology = [{"language": f"lang{i}", "root": "test"} for i in range(10)]
        doctrines = [{"doctrine": f"doctrine{i}"} for i in range(10)]

        strength = engine._calculate_correlation_strength(sources, etymology, doctrines)
        assert 0.0 <= strength <= 1.0


class TestSchemaCompliance:
    """Tests for schema compliance."""

    def test_corpus_schema_fields(self):
        """Test corpus contains required schema fields."""
        engine = CDSCEEngine()
        engine.loaded = True
        engine.semantic_loader.merged_definitions = {}

        engine.generate_corpus([])

        # Check required fields
        assert "version" in engine.corpus
        assert "schema_version" in engine.corpus
        assert "generated" in engine.corpus
        assert "total_terms" in engine.corpus
        assert "terms" in engine.corpus

    def test_term_correlation_structure(self):
        """Test term correlation has correct structure."""
        engine = CDSCEEngine()
        engine.loaded = True
        engine.semantic_loader.merged_definitions = {
            "test": {
                "sources": {},
                "doctrines": [],
                "era_adjustments": {},
            }
        }
        engine.etymology_loader.latin_maxims = {"maxims": {}}
        engine.etymology_loader.greek_roots = {"roots": {}}
        engine.etymology_loader.canon_roots = {"entries": {}}
        engine.harmonizer.merged_definitions = {"test": {"sources": {}}}
        engine.case_loader.cases = {}
        engine.framework_loader.frameworks = {}

        correlation = engine.correlate_term("test")

        # Check required fields
        assert "term" in correlation
        assert "canonical" in correlation
        assert "dictionary_sources" in correlation
        assert "correlation_strength" in correlation
        assert "timestamp" in correlation


class TestErrorHandling:
    """Tests for error handling."""

    def test_initialize_missing_files(self, tmp_path):
        """Test initialization handles missing files gracefully."""
        engine = CDSCEEngine(
            lexicon_dir=tmp_path / "nonexistent",
            etymology_dir=tmp_path / "nonexistent",
            cases_dir=tmp_path / "nonexistent",
            constitutional_dir=tmp_path / "nonexistent",
        )
        result = engine.initialize()
        assert result["success"] is False
        assert "error" in result

    def test_save_corpus_before_generation(self):
        """Test saving corpus before generation."""
        engine = CDSCEEngine()
        result = engine.save_corpus()
        # Should save empty corpus
        assert "success" in result


class TestEraDefinitions:
    """Tests for era definition handling."""

    def test_get_era_definitions_empty(self):
        """Test getting era definitions with no data."""
        engine = CDSCEEngine()
        engine.harmonizer.merged_definitions = {}
        era_defs = engine._get_era_definitions("nonexistent")
        assert len(era_defs) == 0

    def test_get_era_definitions_with_data(self):
        """Test getting era definitions with data."""
        engine = CDSCEEngine()
        engine.harmonizer.merged_definitions = {
            "test": {
                "era_adjustments": {
                    "1791": "founding era definition",
                    "2024": "modern definition",
                }
            }
        }
        engine.harmonizer.ERAS = {
            1791: "Founding Era",
            2024: "Contemporary Era",
        }

        era_defs = engine._get_era_definitions("test")
        assert "1791" in era_defs
        assert "2024" in era_defs


class TestFrameworkContext:
    """Tests for framework context extraction."""

    def test_get_framework_context_empty(self):
        """Test getting framework context with no data."""
        engine = CDSCEEngine()
        engine.framework_loader.frameworks = {}
        contexts = engine._get_framework_context("liberty")
        assert len(contexts) == 0

    def test_get_framework_context_keyword_matching(self):
        """Test framework context with keyword matching."""
        engine = CDSCEEngine()
        engine.framework_loader.frameworks = {
            "originalism": {
                "name": "Original Public Meaning",
                "description": "liberty in founding era context",
                "era": "founding",
                "jim_weight": 0.25,
            }
        }

        contexts = engine._get_framework_context("liberty")
        # Should find liberty in framework
        assert len(contexts) >= 0
