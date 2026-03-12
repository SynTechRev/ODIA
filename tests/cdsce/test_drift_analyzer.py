"""
Tests for CDSCE Drift Analyzer.

Tests semantic drift detection, era-aware scoring, drift spikes,
meaning inversion, and interpretive instability.
"""

from scripts.jim.cdsce_drift_analyzer import CDSCEDriftAnalyzer


class TestDriftScoreCalculation:
    """Tests for drift score calculation."""

    def test_calculate_drift_score_no_definitions(self):
        """Test drift score with no definitions."""
        analyzer = CDSCEDriftAnalyzer()
        score = analyzer.calculate_drift_score("test", {})
        assert score == 0.0

    def test_calculate_drift_score_single_definition(self):
        """Test drift score with single definition."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {1791: "original meaning"}
        score = analyzer.calculate_drift_score("test", definitions)
        assert score == 0.0

    def test_calculate_drift_score_identical_definitions(self):
        """Test drift score with identical definitions."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "the right to be free from government interference",
            2024: "the right to be free from government interference",
        }
        score = analyzer.calculate_drift_score("liberty", definitions)
        assert score < 0.3  # Low drift for identical definitions

    def test_calculate_drift_score_different_definitions(self):
        """Test drift score with very different definitions."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "natural inherent freedom from restraint",
            2024: "positive rights granted by government statute",
        }
        score = analyzer.calculate_drift_score("liberty", definitions)
        assert score > 0.4  # Higher drift for different definitions

    def test_calculate_drift_score_multiple_eras(self):
        """Test drift score across multiple eras."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "freedom from tyranny",
            1868: "freedom with equality",
            1960: "civil rights protection",
            2024: "comprehensive personal autonomy",
        }
        score = analyzer.calculate_drift_score("liberty", definitions)
        assert 0.0 <= score <= 1.0

    def test_calculate_drift_score_latin_lineage(self):
        """Test drift score with Latin lineage weighting."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "original definition",
            2024: "completely different modern definition",
        }
        score = analyzer.calculate_drift_score("test", definitions, lineage="latin")
        assert score > 0.0  # Latin lineage increases weight

    def test_calculate_drift_score_colloquial_lineage(self):
        """Test drift score with colloquial lineage (lower weight)."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "original definition",
            2024: "completely different modern definition",
        }
        score = analyzer.calculate_drift_score(
            "test", definitions, lineage="colloquial"
        )
        assert 0.0 <= score <= 1.0


class TestPairwiseDriftCalculation:
    """Tests for pairwise drift calculation."""

    def test_pairwise_drift_identical_text(self):
        """Test pairwise drift with identical text."""
        analyzer = CDSCEDriftAnalyzer()
        text = "the right to be free from government interference"
        drift = analyzer._calculate_pairwise_drift(text, text)
        assert drift == 0.0

    def test_pairwise_drift_completely_different(self):
        """Test pairwise drift with completely different text."""
        analyzer = CDSCEDriftAnalyzer()
        text1 = "freedom liberty independence"
        text2 = "obligation duty requirement"
        drift = analyzer._calculate_pairwise_drift(text1, text2)
        assert drift > 0.8  # High drift for opposite meanings

    def test_pairwise_drift_empty_strings(self):
        """Test pairwise drift with empty strings."""
        analyzer = CDSCEDriftAnalyzer()
        drift = analyzer._calculate_pairwise_drift("", "some text")
        assert drift == 0.5

    def test_pairwise_drift_stopwords_only(self):
        """Test pairwise drift filters stopwords."""
        analyzer = CDSCEDriftAnalyzer()
        text1 = "the a an"
        text2 = "and or but"
        drift = analyzer._calculate_pairwise_drift(text1, text2)
        assert drift == 0.5  # Default when no meaningful words


class TestDriftSpikeDetection:
    """Tests for drift spike detection."""

    def test_detect_drift_spike_no_spike(self):
        """Test drift spike detection with no spike."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "freedom from government interference",
            2024: "freedom from governmental interference",
        }
        result = analyzer.detect_drift_spike("liberty", definitions)
        assert result["has_spike"] is False
        assert result["spike_count"] == 0

    def test_detect_drift_spike_with_spike(self):
        """Test drift spike detection with significant spike."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "natural inherent freedom",
            2024: "statutory government-granted privileges",
        }
        result = analyzer.detect_drift_spike("liberty", definitions, threshold=0.6)
        assert result["term"] == "liberty"
        assert "has_spike" in result
        assert "spike_count" in result

    def test_detect_drift_spike_custom_threshold(self):
        """Test drift spike with custom threshold."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "freedom from tyranny",
            2024: "government regulated liberty",
        }
        result = analyzer.detect_drift_spike("liberty", definitions, threshold=0.9)
        # With high threshold, less likely to detect spike
        assert "has_spike" in result

    def test_detect_drift_spike_multiple_spikes(self):
        """Test detection of multiple drift spikes."""
        analyzer = CDSCEDriftAnalyzer()
        definitions = {
            1791: "natural freedom",
            1868: "statutory equality rights",
            1960: "civil rights protections",
            2024: "comprehensive personal autonomy",
        }
        result = analyzer.detect_drift_spike("liberty", definitions, threshold=0.5)
        assert "spikes" in result
        assert isinstance(result["spikes"], list)


class TestMeaningInversion:
    """Tests for meaning inversion detection."""

    def test_analyze_meaning_inversion_true(self):
        """Test meaning inversion detection - true inversion."""
        analyzer = CDSCEDriftAnalyzer()
        original = "freedom from government control"
        modern = "not freedom but government regulation and control"
        result = analyzer.analyze_meaning_inversion("liberty", original, modern)
        assert result["is_inversion"] is True
        assert result["confidence"] >= 0.5

    def test_analyze_meaning_inversion_false(self):
        """Test meaning inversion detection - no inversion."""
        analyzer = CDSCEDriftAnalyzer()
        original = "freedom from government interference"
        modern = "freedom from governmental interference"
        result = analyzer.analyze_meaning_inversion("liberty", original, modern)
        assert result["is_inversion"] is False

    def test_analyze_meaning_inversion_with_indicators(self):
        """Test meaning inversion with explicit indicators."""
        analyzer = CDSCEDriftAnalyzer()
        original = "natural right"
        modern = "opposite of natural right now means statutory privilege"
        result = analyzer.analyze_meaning_inversion("liberty", original, modern)
        assert result["is_inversion"] is True
        assert len(result["inversion_indicators_found"]) > 0

    def test_analyze_meaning_inversion_custom_indicators(self):
        """Test meaning inversion with custom indicators."""
        analyzer = CDSCEDriftAnalyzer()
        original = "old meaning"
        modern = "reversed meaning totally different"
        indicators = ["reversed", "totally different"]
        result = analyzer.analyze_meaning_inversion(
            "test", original, modern, inversion_indicators=indicators
        )
        assert "is_inversion" in result
        assert "confidence" in result


class TestInterpretiveInstability:
    """Tests for interpretive instability detection."""

    def test_analyze_instability_insufficient_data(self):
        """Test instability with insufficient case data."""
        analyzer = CDSCEDriftAnalyzer()
        case_definitions = {"case1": "definition one"}
        result = analyzer.analyze_interpretive_instability("term", case_definitions)
        assert result["instability_score"] == 0.0
        assert result["is_unstable"] is False

    def test_analyze_instability_consistent_usage(self):
        """Test instability with consistent usage."""
        analyzer = CDSCEDriftAnalyzer()
        case_definitions = {
            "case1": "freedom from government interference",
            "case2": "freedom from governmental interference",
            "case3": "freedom from state interference",
        }
        result = analyzer.analyze_interpretive_instability("liberty", case_definitions)
        assert result["is_unstable"] is False
        assert result["instability_score"] < 0.5

    def test_analyze_instability_inconsistent_usage(self):
        """Test instability with inconsistent usage."""
        analyzer = CDSCEDriftAnalyzer()
        case_definitions = {
            "case1": "natural inherent freedom",
            "case2": "statutory government-granted privilege",
            "case3": "constitutional right to autonomy",
        }
        result = analyzer.analyze_interpretive_instability("liberty", case_definitions)
        assert result["term"] == "liberty"
        assert result["variation_count"] == 3

    def test_analyze_instability_many_cases(self):
        """Test instability with many cases."""
        analyzer = CDSCEDriftAnalyzer()
        case_definitions = {
            f"case{i}": f"definition variant {i % 3}" for i in range(10)
        }
        result = analyzer.analyze_interpretive_instability("term", case_definitions)
        assert result["variation_count"] == 10
        assert result["pairwise_comparisons"] > 0


class TestDriftReportGeneration:
    """Tests for drift report generation."""

    def test_generate_drift_report_basic(self):
        """Test basic drift report generation."""
        analyzer = CDSCEDriftAnalyzer()
        correlation_data = {
            "era_definitions": {
                "1791": {"definition": "original meaning"},
                "2024": {"definition": "modern meaning"},
            },
            "etymology_lineage": [{"language": "latin", "root": "test"}],
        }
        report = analyzer.generate_drift_report("liberty", correlation_data)
        assert report["term"] == "liberty"
        assert "overall_drift_score" in report
        assert "linguistic_lineage" in report
        assert "drift_category" in report

    def test_generate_drift_report_with_spikes(self):
        """Test drift report with spikes."""
        analyzer = CDSCEDriftAnalyzer()
        correlation_data = {
            "era_definitions": {
                "1791": {"definition": "natural freedom inherent rights"},
                "2024": {"definition": "statutory government-granted privileges"},
            },
            "etymology_lineage": [{"language": "latin"}],
        }
        report = analyzer.generate_drift_report("liberty", correlation_data)
        assert "has_drift_spike" in report
        assert "spike_count" in report
        assert "spikes" in report

    def test_generate_drift_report_categorization(self):
        """Test drift report categorizes drift correctly."""
        analyzer = CDSCEDriftAnalyzer()
        correlation_data = {
            "era_definitions": {
                "1791": {"definition": "test meaning"},
                "2024": {"definition": "test meaning"},
            },
            "etymology_lineage": [],
        }
        report = analyzer.generate_drift_report("test", correlation_data)
        assert report["drift_category"] in [
            "minimal",
            "low",
            "moderate",
            "high",
            "severe",
        ]


class TestEraWeighting:
    """Tests for era weighting calculations."""

    def test_era_weight_short_span(self):
        """Test era weight for short time span."""
        analyzer = CDSCEDriftAnalyzer()
        weight = analyzer._get_era_weight(2020, 2024)
        assert weight == 0.5  # <= 10 years

    def test_era_weight_medium_span(self):
        """Test era weight for medium time span."""
        analyzer = CDSCEDriftAnalyzer()
        weight = analyzer._get_era_weight(1980, 2024)
        assert weight == 0.7  # <= 50 years

    def test_era_weight_long_span(self):
        """Test era weight for long time span."""
        analyzer = CDSCEDriftAnalyzer()
        weight = analyzer._get_era_weight(1900, 2024)
        assert weight == 1.0  # > 100 years

    def test_era_weight_very_long_span(self):
        """Test era weight for very long time span."""
        analyzer = CDSCEDriftAnalyzer()
        weight = analyzer._get_era_weight(1791, 2024)
        assert weight == 1.0  # > 100 years


class TestDriftCategorization:
    """Tests for drift categorization."""

    def test_categorize_minimal_drift(self):
        """Test categorization of minimal drift."""
        analyzer = CDSCEDriftAnalyzer()
        category = analyzer._categorize_drift(0.1)
        assert category == "minimal"

    def test_categorize_low_drift(self):
        """Test categorization of low drift."""
        analyzer = CDSCEDriftAnalyzer()
        category = analyzer._categorize_drift(0.3)
        assert category == "low"

    def test_categorize_moderate_drift(self):
        """Test categorization of moderate drift."""
        analyzer = CDSCEDriftAnalyzer()
        category = analyzer._categorize_drift(0.5)
        assert category == "moderate"

    def test_categorize_high_drift(self):
        """Test categorization of high drift."""
        analyzer = CDSCEDriftAnalyzer()
        category = analyzer._categorize_drift(0.7)
        assert category == "high"

    def test_categorize_severe_drift(self):
        """Test categorization of severe drift."""
        analyzer = CDSCEDriftAnalyzer()
        category = analyzer._categorize_drift(0.9)
        assert category == "severe"


class TestStatistics:
    """Tests for statistics retrieval."""

    def test_get_statistics_initial(self):
        """Test statistics after initialization."""
        analyzer = CDSCEDriftAnalyzer()
        stats = analyzer.get_statistics()
        assert stats["version"] == "1.0.0"
        assert stats["terms_analyzed"] == 0
        assert stats["era_comparisons"] == 0
        assert stats["lineage_analyses"] == 0
