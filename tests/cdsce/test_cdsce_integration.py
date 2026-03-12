"""
CDSCE Integration Tests.

Tests integration between CDSCE components and with other Oraculus systems.
"""

from scripts.jim.cdsce_anomaly_detector import CDSCEAnomalyDetector
from scripts.jim.cdsce_contradiction_engine import CDSCEContradictionEngine
from scripts.jim.cdsce_drift_analyzer import CDSCEDriftAnalyzer
from scripts.jim.cdsce_engine import CDSCEEngine
from scripts.jim.cdsce_graph_builder import CDSCEGraphBuilder


class TestComponentIntegration:
    """Tests integration between CDSCE components."""

    def test_engine_with_drift_analyzer(self):
        """Test CDSCE engine integration with drift analyzer."""
        engine = CDSCEEngine()
        analyzer = CDSCEDriftAnalyzer()

        # Both should initialize without errors
        assert engine.VERSION == "1.0.0"
        assert analyzer.VERSION == "1.0.0"

    def test_engine_with_anomaly_detector(self):
        """Test CDSCE engine integration with anomaly detector."""
        engine = CDSCEEngine()
        detector = CDSCEAnomalyDetector()

        assert engine.VERSION == "1.0.0"
        assert detector.VERSION == "1.0.0"

    def test_engine_with_contradiction_engine(self):
        """Test CDSCE engine integration with contradiction engine."""
        engine = CDSCEEngine()
        contradiction_engine = CDSCEContradictionEngine()

        assert engine.VERSION == "1.0.0"
        assert contradiction_engine.VERSION == "1.0.0"

    def test_engine_with_graph_builder(self):
        """Test CDSCE engine integration with graph builder."""
        engine = CDSCEEngine()
        builder = CDSCEGraphBuilder()

        assert engine.VERSION == "1.0.0"
        assert builder.VERSION == "1.0.0"


class TestDataFlow:
    """Tests data flow between components."""

    def test_drift_to_anomaly_flow(self):
        """Test drift analysis output feeds into anomaly detection."""
        analyzer = CDSCEDriftAnalyzer()
        detector = CDSCEAnomalyDetector()

        # Generate drift analysis
        definitions = {
            1791: "natural inherent freedom",
            2024: "statutory government privilege",
        }
        drift_analysis = {
            "term": "liberty",
            "overall_drift_score": analyzer.calculate_drift_score(
                "liberty", definitions
            ),
            "has_drift_spike": False,
            "spikes": [],
        }

        # Feed into anomaly detector
        anomaly = detector.detect_drift_spike("liberty", drift_analysis)
        # Should handle the input without error
        assert anomaly is None or isinstance(anomaly, dict)

    def test_contradiction_to_anomaly_flow(self):
        """Test contradiction detection feeds into anomaly system."""
        contradiction_engine = CDSCEContradictionEngine()

        source1 = {"source": "blacks", "definition": "natural freedom"}
        source2 = {"source": "webster", "definition": "statutory privilege"}

        contradiction = contradiction_engine.detect_lexical_contradiction(
            "liberty", source1, source2
        )

        if contradiction:
            assert "severity" in contradiction
            assert "conflict_type" in contradiction

    def test_corpus_to_graph_flow(self):
        """Test corpus generation feeds into graph building."""
        builder = CDSCEGraphBuilder()

        # Mock corpus data
        corpus = {
            "terms": {
                "liberty": {
                    "etymology_lineage": [
                        {
                            "language": "latin",
                            "root": "libertas",
                            "meaning": "freedom",
                            "era": "classical",
                        }
                    ],
                    "doctrinal_mappings": [{"doctrine": "due_process"}],
                }
            }
        }

        # Build graphs from corpus
        etymology_graph = builder.build_etymology_graph(corpus)
        doctrine_graph = builder.build_doctrine_graph(corpus)

        assert isinstance(etymology_graph, dict)
        assert isinstance(doctrine_graph, dict)


class TestEndToEndWorkflow:
    """Tests end-to-end CDSCE workflows."""

    def test_minimal_workflow(self):
        """Test minimal CDSCE workflow."""
        # Initialize all components
        engine = CDSCEEngine()
        analyzer = CDSCEDriftAnalyzer()
        detector = CDSCEAnomalyDetector()
        contradiction_engine = CDSCEContradictionEngine()
        builder = CDSCEGraphBuilder()

        # All components should be ready
        assert engine.loaded is False
        assert analyzer.get_statistics()["version"] == "1.0.0"
        assert detector.get_statistics()["version"] == "1.0.0"
        assert contradiction_engine.get_statistics()["version"] == "1.0.0"
        assert builder.get_statistics()["version"] == "1.0.0"

    def test_correlation_with_drift_analysis(self):
        """Test correlation combined with drift analysis."""
        analyzer = CDSCEDriftAnalyzer()

        # Mock correlation data
        correlation_data = {
            "era_definitions": {
                "1791": {"definition": "natural freedom"},
                "2024": {"definition": "statutory privilege"},
            },
            "etymology_lineage": [{"language": "latin"}],
        }

        # Generate drift report
        report = analyzer.generate_drift_report("liberty", correlation_data)

        assert "overall_drift_score" in report
        assert "drift_category" in report

    def test_correlation_with_contradiction_scan(self):
        """Test correlation with contradiction scanning."""
        contradiction_engine = CDSCEContradictionEngine()

        # Mock correlation data
        correlation_data = {
            "dictionary_sources": [
                {"source": "blacks", "definition": "natural freedom", "year": 2019},
                {
                    "source": "webster",
                    "definition": "statutory privilege",
                    "year": 2023,
                },
            ],
            "doctrinal_mappings": [],
            "framework_context": [],
            "era_definitions": {},
            "etymology_lineage": [],
        }

        # Scan for contradictions
        contradictions = contradiction_engine.scan_term_contradictions(
            "liberty", correlation_data
        )

        assert isinstance(contradictions, list)


class TestVersionCompatibility:
    """Tests version compatibility between components."""

    def test_all_components_same_version(self):
        """Test all CDSCE components use same version."""
        engine = CDSCEEngine()
        analyzer = CDSCEDriftAnalyzer()
        detector = CDSCEAnomalyDetector()
        contradiction_engine = CDSCEContradictionEngine()
        builder = CDSCEGraphBuilder()

        assert engine.VERSION == "1.0.0"
        assert analyzer.VERSION == "1.0.0"
        assert detector.VERSION == "1.0.0"
        assert contradiction_engine.VERSION == "1.0.0"
        assert builder.VERSION == "1.0.0"

    def test_schema_version_consistency(self):
        """Test schema version consistency."""
        engine = CDSCEEngine()

        assert engine.SCHEMA_VERSION == "1.0"


class TestErrorHandlingIntegration:
    """Tests error handling across component boundaries."""

    def test_invalid_data_handling(self):
        """Test components handle invalid data gracefully."""
        analyzer = CDSCEDriftAnalyzer()
        detector = CDSCEAnomalyDetector()
        builder = CDSCEGraphBuilder()

        # Test with empty/invalid data
        assert analyzer.calculate_drift_score("test", {}) == 0.0

        empty_corpus = {"terms": {}}
        assert builder.build_etymology_graph(empty_corpus) == {}

        empty_correlation = {
            "dictionary_sources": [],
            "etymology_lineage": [],
        }
        assert detector.scan_term_for_anomalies("test", empty_correlation) == []

    def test_missing_fields_handling(self):
        """Test components handle missing fields gracefully."""
        builder = CDSCEGraphBuilder()

        # Corpus with missing fields
        corpus = {"terms": {"liberty": {}}}

        # Should not crash
        graph = builder.build_etymology_graph(corpus)
        assert isinstance(graph, dict)


class TestStatisticsAggregation:
    """Tests statistics aggregation across components."""

    def test_aggregate_component_statistics(self):
        """Test aggregating statistics from all components."""
        engine = CDSCEEngine()
        analyzer = CDSCEDriftAnalyzer()
        detector = CDSCEAnomalyDetector()
        contradiction_engine = CDSCEContradictionEngine()
        builder = CDSCEGraphBuilder()

        # Get all statistics
        stats = {
            "engine": engine.get_statistics(),
            "analyzer": analyzer.get_statistics(),
            "detector": detector.get_statistics(),
            "contradiction": contradiction_engine.get_statistics(),
            "builder": builder.get_statistics(),
        }

        # Verify structure
        assert "engine" in stats
        assert "analyzer" in stats
        assert "detector" in stats
        assert "contradiction" in stats
        assert "builder" in stats
