"""
Tests for CDSCE Contradiction Engine.

Tests detection of lexical, doctrinal, interpretive, temporal,
constitutional framework, and etymological contradictions.
"""

from scripts.jim.cdsce_contradiction_engine import CDSCEContradictionEngine


class TestLexicalContradiction:
    """Tests for lexical contradiction detection."""

    def test_detect_lexical_contradiction_none(self):
        """Test no contradiction with similar definitions."""
        engine = CDSCEContradictionEngine()
        source1 = {
            "source": "blacks",
            "definition": "freedom from government interference",
            "year": 2019,
        }
        source2 = {
            "source": "webster",
            "definition": "freedom from governmental interference",
            "year": 2023,
        }
        result = engine.detect_lexical_contradiction("liberty", source1, source2)
        assert result is None

    def test_detect_lexical_contradiction_detected(self):
        """Test contradiction detected with different definitions."""
        engine = CDSCEContradictionEngine()
        source1 = {
            "source": "blacks",
            "definition": "natural inherent freedom from restraint",
            "year": 2019,
        }
        source2 = {
            "source": "webster",
            "definition": "statutory privilege granted by government",
            "year": 2023,
        }
        result = engine.detect_lexical_contradiction("liberty", source1, source2)
        assert result is not None
        assert result["conflict_type"] == "lexical"
        assert result["severity"] > 0.5

    def test_detect_lexical_contradiction_with_marker(self):
        """Test contradiction with explicit marker."""
        engine = CDSCEContradictionEngine()
        source1 = {"source": "blacks", "definition": "natural right", "year": 2019}
        source2 = {
            "source": "webster",
            "definition": "not a natural right but a statutory privilege",
            "year": 2023,
        }
        result = engine.detect_lexical_contradiction("test", source1, source2)
        assert result is not None
        assert result["details"]["has_contradiction_marker"] is True

    def test_detect_lexical_contradiction_empty_definitions(self):
        """Test with empty definitions."""
        engine = CDSCEContradictionEngine()
        source1 = {"source": "blacks", "definition": "", "year": 2019}
        source2 = {"source": "webster", "definition": "test", "year": 2023}
        result = engine.detect_lexical_contradiction("test", source1, source2)
        assert result is None

    def test_lexical_contradiction_severity_calculation(self):
        """Test severity calculation for lexical contradiction."""
        engine = CDSCEContradictionEngine()
        source1 = {
            "source": "blacks",
            "definition": "freedom liberty independence",
            "year": 2019,
        }
        source2 = {
            "source": "webster",
            "definition": "obligation duty requirement",
            "year": 2023,
        }
        result = engine.detect_lexical_contradiction("test", source1, source2)
        assert result is not None
        assert 0.7 <= result["severity"] <= 1.0


class TestDoctrinalContradiction:
    """Tests for doctrinal contradiction detection."""

    def test_detect_doctrinal_contradiction_none(self):
        """Test no contradiction with compatible doctrines."""
        engine = CDSCEContradictionEngine()
        doctrine1 = {"doctrine": "due_process", "related_cases": []}
        doctrine2 = {"doctrine": "equal_protection", "related_cases": []}
        result = engine.detect_doctrinal_contradiction("liberty", doctrine1, doctrine2)
        assert result is None

    def test_detect_doctrinal_contradiction_strict_vs_rational(self):
        """Test contradiction: strict scrutiny vs rational basis."""
        engine = CDSCEContradictionEngine()
        doctrine1 = {"doctrine": "strict_scrutiny", "related_cases": []}
        doctrine2 = {"doctrine": "rational_basis", "related_cases": []}
        result = engine.detect_doctrinal_contradiction("liberty", doctrine1, doctrine2)
        assert result is not None
        assert result["conflict_type"] == "doctrinal"
        assert result["severity"] == 0.85

    def test_detect_doctrinal_contradiction_originalism_vs_living(self):
        """Test contradiction: originalism vs living constitution."""
        engine = CDSCEContradictionEngine()
        doctrine1 = {"doctrine": "originalism", "related_cases": []}
        doctrine2 = {"doctrine": "living_constitution", "related_cases": []}
        result = engine.detect_doctrinal_contradiction("term", doctrine1, doctrine2)
        assert result is not None
        assert "originalism" in result["sources_involved"]
        assert "living_constitution" in result["sources_involved"]

    def test_detect_doctrinal_contradiction_textualism_vs_purposivism(self):
        """Test contradiction: textualism vs purposivism."""
        engine = CDSCEContradictionEngine()
        doctrine1 = {"doctrine": "textualism", "related_cases": []}
        doctrine2 = {"doctrine": "purposivism", "related_cases": []}
        result = engine.detect_doctrinal_contradiction("term", doctrine1, doctrine2)
        assert result is not None
        assert result["conflict_type"] == "doctrinal"

    def test_doctrinal_contradiction_empty_doctrine(self):
        """Test with empty doctrine names."""
        engine = CDSCEContradictionEngine()
        doctrine1 = {"doctrine": "", "related_cases": []}
        doctrine2 = {"doctrine": "test", "related_cases": []}
        result = engine.detect_doctrinal_contradiction("term", doctrine1, doctrine2)
        assert result is None


class TestInterpretiveContradiction:
    """Tests for interpretive (constitutional framework) contradiction detection."""

    def test_detect_interpretive_contradiction_none(self):
        """Test no contradiction with compatible frameworks."""
        engine = CDSCEContradictionEngine()
        framework1 = {"framework": "due_process", "era": "modern", "weight": 0.5}
        framework2 = {"framework": "equal_protection", "era": "modern", "weight": 0.5}
        result = engine.detect_interpretive_contradiction(
            "liberty", framework1, framework2
        )
        assert result is None

    def test_detect_interpretive_contradiction_originalism_vs_living(self):
        """Test contradiction: originalism vs living constitutionalism."""
        engine = CDSCEContradictionEngine()
        framework1 = {"framework": "originalism", "era": "founding", "weight": 0.8}
        framework2 = {
            "framework": "living_constitutionalism",
            "era": "modern",
            "weight": 0.7,
        }
        result = engine.detect_interpretive_contradiction(
            "liberty", framework1, framework2
        )
        assert result is not None
        assert result["conflict_type"] == "interpretive"
        assert result["severity"] == 0.8

    def test_detect_interpretive_contradiction_textualism_vs_purposivism(self):
        """Test contradiction: textualism vs purposivism."""
        engine = CDSCEContradictionEngine()
        framework1 = {"framework": "textualism", "era": "modern", "weight": 0.7}
        framework2 = {"framework": "purposivism", "era": "modern", "weight": 0.6}
        result = engine.detect_interpretive_contradiction(
            "term", framework1, framework2
        )
        assert result is not None

    def test_detect_interpretive_contradiction_framers_vs_contemporary(self):
        """Test contradiction: framers intent vs contemporary interpretation."""
        engine = CDSCEContradictionEngine()
        framework1 = {"framework": "framers_intent", "era": "founding", "weight": 0.9}
        framework2 = {
            "framework": "contemporary_interpretation",
            "era": "modern",
            "weight": 0.6,
        }
        result = engine.detect_interpretive_contradiction(
            "term", framework1, framework2
        )
        assert result is not None

    def test_interpretive_contradiction_empty_framework(self):
        """Test with empty framework names."""
        engine = CDSCEContradictionEngine()
        framework1 = {"framework": "", "era": "modern", "weight": 0.5}
        framework2 = {"framework": "test", "era": "modern", "weight": 0.5}
        result = engine.detect_interpretive_contradiction(
            "term", framework1, framework2
        )
        assert result is None


class TestTemporalContradiction:
    """Tests for temporal contradiction detection."""

    def test_detect_temporal_contradiction_none(self):
        """Test no contradiction with similar meanings over time."""
        engine = CDSCEContradictionEngine()
        result = engine.detect_temporal_contradiction(
            "liberty",
            1791,
            "freedom from government interference",
            2024,
            "freedom from governmental interference",
        )
        assert result is None

    def test_detect_temporal_contradiction_detected(self):
        """Test contradiction with significantly different meanings."""
        engine = CDSCEContradictionEngine()
        result = engine.detect_temporal_contradiction(
            "liberty",
            1791,
            "natural inherent freedom from restraint",
            2024,
            "statutory privilege granted by government",
        )
        assert result is not None
        assert result["conflict_type"] == "temporal"
        assert result["severity"] > 0.7

    def test_temporal_contradiction_empty_definitions(self):
        """Test with empty definitions."""
        engine = CDSCEContradictionEngine()
        result = engine.detect_temporal_contradiction("term", 1791, "", 2024, "test")
        assert result is None

    def test_temporal_contradiction_time_span(self):
        """Test temporal contradiction includes time span."""
        engine = CDSCEContradictionEngine()
        result = engine.detect_temporal_contradiction(
            "liberty",
            1791,
            "natural freedom rights",
            2024,
            "government statutory privileges",
        )
        if result:
            assert result["details"]["time_span_years"] == 233

    def test_temporal_contradiction_severity_scaling(self):
        """Test severity scales with semantic difference."""
        engine = CDSCEContradictionEngine()
        result = engine.detect_temporal_contradiction(
            "test",
            1791,
            "completely different meaning one",
            2024,
            "totally unrelated meaning two",
        )
        if result:
            assert result["severity"] > 0.75


class TestConstitutionalFrameworkContradiction:
    """Tests for constitutional framework contradiction detection."""

    def test_detect_framework_contradiction_none(self):
        """Test no contradiction with compatible frameworks."""
        engine = CDSCEContradictionEngine()
        frameworks = [
            {"framework": "due_process", "era": "modern", "weight": 0.5},
            {"framework": "equal_protection", "era": "modern", "weight": 0.5},
        ]
        result = engine.detect_constitutional_framework_contradiction(
            "liberty", frameworks
        )
        assert len(result) == 0

    def test_detect_framework_contradiction_single(self):
        """Test with single framework (no contradiction possible)."""
        engine = CDSCEContradictionEngine()
        frameworks = [{"framework": "originalism", "era": "founding", "weight": 0.8}]
        result = engine.detect_constitutional_framework_contradiction(
            "liberty", frameworks
        )
        assert len(result) == 0

    def test_detect_framework_contradiction_detected(self):
        """Test contradiction detected across multiple frameworks."""
        engine = CDSCEContradictionEngine()
        frameworks = [
            {"framework": "originalism", "era": "founding", "weight": 0.8},
            {
                "framework": "living_constitutionalism",
                "era": "modern",
                "weight": 0.7,
            },
            {"framework": "textualism", "era": "modern", "weight": 0.6},
            {"framework": "purposivism", "era": "modern", "weight": 0.5},
        ]
        result = engine.detect_constitutional_framework_contradiction(
            "liberty", frameworks
        )
        # Should detect originalism vs living_constitutionalism
        # and textualism vs purposivism
        assert len(result) >= 2


class TestEtymologicalContradiction:
    """Tests for etymological contradiction detection."""

    def test_detect_etymological_contradiction_none(self):
        """Test no contradiction with same language."""
        engine = CDSCEContradictionEngine()
        etymology1 = {
            "language": "latin",
            "root": "libertas",
            "meaning": "freedom",
            "era": "classical",
        }
        etymology2 = {
            "language": "latin",
            "root": "liber",
            "meaning": "free",
            "era": "classical",
        }
        result = engine.detect_etymological_contradiction(
            "liberty", etymology1, etymology2
        )
        assert result is None  # Same language, no conflict

    def test_detect_etymological_contradiction_detected(self):
        """Test contradiction with different languages and meanings."""
        engine = CDSCEContradictionEngine()
        etymology1 = {
            "language": "latin",
            "root": "libertas",
            "meaning": "freedom from constraint",
            "era": "classical",
        }
        etymology2 = {
            "language": "greek",
            "root": "doulos",
            "meaning": "servitude and obligation",
            "era": "classical",
        }
        result = engine.detect_etymological_contradiction(
            "term", etymology1, etymology2
        )
        assert result is not None
        assert result["conflict_type"] == "etymological"
        assert "latin" in result["sources_involved"]
        assert "greek" in result["sources_involved"]

    def test_etymological_contradiction_empty_meanings(self):
        """Test with empty meanings."""
        engine = CDSCEContradictionEngine()
        etymology1 = {
            "language": "latin",
            "root": "test",
            "meaning": "",
            "era": "classical",
        }
        etymology2 = {
            "language": "greek",
            "root": "test",
            "meaning": "test",
            "era": "classical",
        }
        result = engine.detect_etymological_contradiction(
            "term", etymology1, etymology2
        )
        assert result is None

    def test_etymological_contradiction_similar_meanings_different_languages(self):
        """Test no contradiction when different languages have similar meanings."""
        engine = CDSCEContradictionEngine()
        etymology1 = {
            "language": "latin",
            "root": "libertas",
            "meaning": "freedom liberty independence",
            "era": "classical",
        }
        etymology2 = {
            "language": "greek",
            "root": "eleutheria",
            "meaning": "freedom liberty independence",
            "era": "classical",
        }
        result = engine.detect_etymological_contradiction(
            "liberty", etymology1, etymology2
        )
        # Similar meanings = no contradiction
        assert result is None


class TestScanTermContradictions:
    """Tests for comprehensive term contradiction scanning."""

    def test_scan_term_contradictions_none(self):
        """Test scanning with no contradictions."""
        engine = CDSCEContradictionEngine()
        correlation_data = {
            "dictionary_sources": [
                {"source": "blacks", "definition": "test meaning", "year": 2019}
            ],
            "doctrinal_mappings": [],
            "framework_context": [],
            "era_definitions": {},
            "etymology_lineage": [],
        }
        result = engine.scan_term_contradictions("test", correlation_data)
        assert len(result) == 0

    def test_scan_term_contradictions_lexical(self):
        """Test scanning detects lexical contradictions."""
        engine = CDSCEContradictionEngine()
        correlation_data = {
            "dictionary_sources": [
                {
                    "source": "blacks",
                    "definition": "natural freedom rights",
                    "year": 2019,
                },
                {
                    "source": "webster",
                    "definition": "statutory government privileges",
                    "year": 2023,
                },
            ],
            "doctrinal_mappings": [],
            "framework_context": [],
            "era_definitions": {},
            "etymology_lineage": [],
        }
        result = engine.scan_term_contradictions("liberty", correlation_data)
        lexical_contradictions = [c for c in result if c["conflict_type"] == "lexical"]
        assert len(lexical_contradictions) > 0

    def test_scan_term_contradictions_temporal(self):
        """Test scanning detects temporal contradictions."""
        engine = CDSCEContradictionEngine()
        correlation_data = {
            "dictionary_sources": [],
            "doctrinal_mappings": [],
            "framework_context": [],
            "era_definitions": {
                "1791": {"definition": "natural inherent freedom"},
                "2024": {"definition": "statutory government privilege"},
            },
            "etymology_lineage": [],
        }
        result = engine.scan_term_contradictions("liberty", correlation_data)
        temporal_contradictions = [
            c for c in result if c["conflict_type"] == "temporal"
        ]
        assert len(temporal_contradictions) > 0

    def test_scan_term_contradictions_multiple_types(self):
        """Test scanning detects multiple contradiction types."""
        engine = CDSCEContradictionEngine()
        correlation_data = {
            "dictionary_sources": [
                {
                    "source": "blacks",
                    "definition": "natural freedom",
                    "year": 2019,
                },
                {
                    "source": "webster",
                    "definition": "statutory privilege",
                    "year": 2023,
                },
            ],
            "doctrinal_mappings": [
                {"doctrine": "originalism"},
                {"doctrine": "living_constitution"},
            ],
            "framework_context": [],
            "era_definitions": {
                "1791": {"definition": "natural rights"},
                "2024": {"definition": "government grants"},
            },
            "etymology_lineage": [],
        }
        result = engine.scan_term_contradictions("liberty", correlation_data)
        contradiction_types = set(c["conflict_type"] for c in result)
        assert len(contradiction_types) >= 2


class TestContradictionReport:
    """Tests for contradiction report generation."""

    def test_generate_contradiction_report_empty(self):
        """Test report generation with no contradictions."""
        engine = CDSCEContradictionEngine()
        contradictions = []
        report = engine.generate_contradiction_report(contradictions)
        assert report["total_contradictions"] == 0
        assert report["statistics"]["average_severity"] == 0

    def test_generate_contradiction_report_with_data(self):
        """Test report generation with contradictions."""
        engine = CDSCEContradictionEngine()
        contradictions = [
            {
                "term": "liberty",
                "conflict_type": "lexical",
                "severity": 0.8,
                "sources_involved": ["blacks", "webster"],
            },
            {
                "term": "liberty",
                "conflict_type": "temporal",
                "severity": 0.9,
                "sources_involved": ["era_1791", "era_2024"],
            },
        ]
        report = engine.generate_contradiction_report(contradictions)
        assert report["total_contradictions"] == 2
        assert report["by_type"]["lexical"] == 1
        assert report["by_type"]["temporal"] == 1
        assert report["statistics"]["average_severity"] > 0

    def test_generate_contradiction_report_severity_grouping(self):
        """Test report groups contradictions by severity."""
        engine = CDSCEContradictionEngine()
        contradictions = [
            {"conflict_type": "lexical", "severity": 0.9},
            {"conflict_type": "temporal", "severity": 0.6},
            {"conflict_type": "doctrinal", "severity": 0.3},
        ]
        report = engine.generate_contradiction_report(contradictions)
        assert report["by_severity"]["high"] == 1
        assert report["by_severity"]["medium"] == 1
        assert report["by_severity"]["low"] == 1


class TestStatistics:
    """Tests for statistics retrieval."""

    def test_get_statistics_initial(self):
        """Test statistics after initialization."""
        engine = CDSCEContradictionEngine()
        stats = engine.get_statistics()
        assert stats["version"] == "1.0.0"
        assert stats["total_contradictions"] == 0
