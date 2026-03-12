"""
Tests for CDSCE Anomaly Detector.

Tests detection of various semiotic anomaly types.
"""

from scripts.jim.cdsce_anomaly_detector import CDSCEAnomalyDetector


class TestContradictionDetection:
    """Tests for contradiction anomaly detection."""

    def test_detect_contradiction_none(self):
        """Test no contradiction with similar sources."""
        detector = CDSCEAnomalyDetector()
        source1 = {"source": "blacks", "definition": "freedom from government"}
        source2 = {"source": "webster", "definition": "freedom from governmental"}
        result = detector.detect_contradiction("liberty", source1, source2)
        assert result is None

    def test_detect_contradiction_detected(self):
        """Test contradiction detected."""
        detector = CDSCEAnomalyDetector()
        source1 = {"source": "blacks", "definition": "natural inherent freedom"}
        source2 = {"source": "webster", "definition": "statutory government privilege"}
        result = detector.detect_contradiction("liberty", source1, source2)
        assert result is not None
        assert result["type"] == "contradiction"
        assert result["severity"] > 0.5


class TestDriftSpikeDetection:
    """Tests for drift spike anomaly detection."""

    def test_detect_drift_spike_none(self):
        """Test no drift spike."""
        detector = CDSCEAnomalyDetector()
        drift_analysis = {"has_drift_spike": False, "spikes": []}
        result = detector.detect_drift_spike("test", drift_analysis)
        assert result is None

    def test_detect_drift_spike_detected(self):
        """Test drift spike detected."""
        detector = CDSCEAnomalyDetector()
        drift_analysis = {
            "has_drift_spike": True,
            "spikes": [
                {
                    "from_era": 1791,
                    "to_era": 2024,
                    "drift_score": 0.8,
                }
            ],
        }
        result = detector.detect_drift_spike("liberty", drift_analysis)
        assert result is not None
        assert result["type"] == "semantic_drift_spike"


class TestDoctrineInversion:
    """Tests for doctrine inversion anomaly detection."""

    def test_detect_doctrine_inversion_none(self):
        """Test no doctrine inversion."""
        detector = CDSCEAnomalyDetector()
        inversion_analysis = {"is_inversion": False}
        result = detector.detect_doctrine_inversion(
            "test", "doctrine", "original", "modern", inversion_analysis
        )
        assert result is None

    def test_detect_doctrine_inversion_detected(self):
        """Test doctrine inversion detected."""
        detector = CDSCEAnomalyDetector()
        inversion_analysis = {
            "is_inversion": True,
            "drift_score": 0.9,
            "confidence": 0.85,
            "inversion_indicators_found": ["not", "opposite"],
        }
        result = detector.detect_doctrine_inversion(
            "liberty", "due_process", "original", "modern", inversion_analysis
        )
        assert result is not None
        assert result["type"] == "doctrine_meaning_inversion"
        assert result["severity"] == 0.9


class TestInterpretiveInstability:
    """Tests for interpretive instability anomaly detection."""

    def test_detect_interpretive_instability_none(self):
        """Test no interpretive instability."""
        detector = CDSCEAnomalyDetector()
        instability_analysis = {"is_unstable": False, "instability_score": 0.3}
        result = detector.detect_interpretive_instability("test", instability_analysis)
        assert result is None

    def test_detect_interpretive_instability_detected(self):
        """Test interpretive instability detected."""
        detector = CDSCEAnomalyDetector()
        instability_analysis = {
            "is_unstable": True,
            "instability_score": 0.7,
            "variation_count": 5,
            "pairwise_comparisons": 10,
        }
        result = detector.detect_interpretive_instability(
            "liberty", instability_analysis
        )
        assert result is not None
        assert result["type"] == "interpretive_instability"


class TestCrossDictionaryConflict:
    """Tests for cross-dictionary conflict anomaly detection."""

    def test_detect_cross_dictionary_conflict_none_single_source(self):
        """Test no conflict with single etymology source."""
        detector = CDSCEAnomalyDetector()
        etymology_sources = [
            {"language": "latin", "root": "libertas", "meaning": "freedom"}
        ]
        result = detector.detect_cross_dictionary_conflict("liberty", etymology_sources)
        assert result is None

    def test_detect_cross_dictionary_conflict_similar_meanings(self):
        """Test no conflict when meanings are similar."""
        detector = CDSCEAnomalyDetector()
        etymology_sources = [
            {
                "language": "latin",
                "root": "libertas",
                "meaning": "freedom liberty independence",
            },
            {
                "language": "greek",
                "root": "eleutheria",
                "meaning": "freedom liberty independence",
            },
        ]
        result = detector.detect_cross_dictionary_conflict("liberty", etymology_sources)
        assert result is None  # Similar meanings = no conflict

    def test_detect_cross_dictionary_conflict_detected(self):
        """Test conflict detected with different meanings."""
        detector = CDSCEAnomalyDetector()
        etymology_sources = [
            {
                "language": "latin",
                "root": "libertas",
                "meaning": "freedom from constraint",
            },
            {"language": "greek", "root": "test", "meaning": "obligation and duty"},
        ]
        result = detector.detect_cross_dictionary_conflict("term", etymology_sources)
        assert result is not None
        assert result["type"] == "cross_dictionary_conflict"


class TestEtymologyDivergence:
    """Tests for etymology divergence anomaly detection."""

    def test_detect_etymology_divergence_none(self):
        """Test no divergence with similar meanings."""
        detector = CDSCEAnomalyDetector()
        result = detector.detect_etymology_divergence(
            "liberty",
            "libertas",
            "freedom from constraint",
            "freedom from governmental constraint",
        )
        assert result is None

    def test_detect_etymology_divergence_detected(self):
        """Test divergence detected."""
        detector = CDSCEAnomalyDetector()
        result = detector.detect_etymology_divergence(
            "liberty",
            "libertas",
            "natural inherent freedom",
            "statutory government-granted privilege",
        )
        assert result is not None
        assert result["type"] == "etymology_divergence"
        assert result["severity"] > 0.6


class TestScanTermForAnomalies:
    """Tests for comprehensive term anomaly scanning."""

    def test_scan_term_for_anomalies_none(self):
        """Test scanning with no anomalies."""
        detector = CDSCEAnomalyDetector()
        correlation_data = {
            "dictionary_sources": [],
            "etymology_lineage": [],
        }
        result = detector.scan_term_for_anomalies("test", correlation_data)
        assert len(result) == 0

    def test_scan_term_for_anomalies_with_contradictions(self):
        """Test scanning detects contradictions."""
        detector = CDSCEAnomalyDetector()
        correlation_data = {
            "dictionary_sources": [
                {"source": "blacks", "definition": "natural freedom"},
                {"source": "webster", "definition": "statutory privilege"},
            ],
            "etymology_lineage": [],
        }
        result = detector.scan_term_for_anomalies("liberty", correlation_data)
        assert len(result) > 0


class TestAnomalyIndex:
    """Tests for anomaly index building."""

    def test_build_anomaly_index_empty(self):
        """Test building index with no anomalies."""
        detector = CDSCEAnomalyDetector()
        anomalies = []
        index = detector.build_anomaly_index(anomalies)
        assert index["total_anomalies"] == 0

    def test_build_anomaly_index_with_data(self):
        """Test building index with anomalies."""
        detector = CDSCEAnomalyDetector()
        anomalies = [
            {
                "term": "liberty",
                "type": "contradiction",
                "severity": 0.8,
            },
            {
                "term": "liberty",
                "type": "semantic_drift_spike",
                "severity": 0.7,
            },
        ]
        index = detector.build_anomaly_index(anomalies)
        assert index["total_anomalies"] == 2
        assert "liberty" in index["by_term"]
        assert len(index["by_type"]) > 0


class TestStatistics:
    """Tests for statistics retrieval."""

    def test_get_statistics_initial(self):
        """Test statistics after initialization."""
        detector = CDSCEAnomalyDetector()
        stats = detector.get_statistics()
        assert stats["version"] == "1.0.0"
        assert stats["total_anomalies"] == 0
