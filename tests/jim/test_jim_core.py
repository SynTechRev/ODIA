"""
Tests for JIM Core - Main orchestration engine.
"""

import json

import pytest

from scripts.jim.jim_core import JIMCore


class TestJIMCoreInitialization:
    """Test JIM core initialization."""

    def test_core_initializes_default(self):
        """Test core initializes with defaults."""
        jim = JIMCore()
        assert jim.case_loader is not None
        assert jim.risk_scorer is not None
        assert jim.case_index_loaded is False

    def test_core_initializes_custom_paths(self, tmp_path):
        """Test core initializes with custom paths."""
        cases_dir = tmp_path / "cases"
        output_dir = tmp_path / "output"
        cases_dir.mkdir()
        output_dir.mkdir()

        jim = JIMCore(cases_dir, output_dir)
        assert jim.output_dir == output_dir

    def test_core_creates_output_directory(self, tmp_path):
        """Test core creates output directory if not exists."""
        output_dir = tmp_path / "new_output"
        _jim = JIMCore(output_dir=output_dir)
        assert output_dir.exists()


class TestJIMInitialization:
    """Test JIM engine initialization."""

    def test_initialize_success(self):
        """Test successful initialization."""
        jim = JIMCore()
        result = jim.initialize()

        assert result["success"] is True
        assert "version" in result
        assert "cases_loaded" in result
        assert result["cases_loaded"] > 0

    def test_initialize_loads_cases(self):
        """Test initialization loads cases."""
        jim = JIMCore()
        jim.initialize()

        assert jim.case_index_loaded is True
        assert jim.correlation_engine is not None

    def test_initialize_validates_cases(self):
        """Test initialization validates cases."""
        jim = JIMCore()
        result = jim.initialize()

        assert "validation" in result
        assert result["validation"]["valid"] is True


class TestAnalyzeAnomalies:
    """Test anomaly analysis."""

    @pytest.fixture
    def initialized_jim(self):
        """Provide initialized JIM."""
        jim = JIMCore()
        jim.initialize()
        return jim

    def test_analyze_requires_initialization(self):
        """Test analyze requires initialization."""
        jim = JIMCore()

        with pytest.raises(RuntimeError):
            jim.analyze_anomalies([])

    def test_analyze_empty_list(self, initialized_jim):
        """Test analyzing empty anomaly list."""
        result = initialized_jim.analyze_anomalies([])

        assert result["total_anomalies_analyzed"] == 0

    def test_analyze_single_anomaly(self, initialized_jim):
        """Test analyzing single anomaly."""
        anomalies = [
            {
                "id": "test_001",
                "type": "metadata_break",
                "source": "ace",
            }
        ]

        result = initialized_jim.analyze_anomalies(anomalies)

        assert result["total_anomalies_analyzed"] == 1
        assert "correlation_summary" in result
        assert "risk_summary" in result

    def test_analyze_multiple_anomalies(self, initialized_jim):
        """Test analyzing multiple anomalies."""
        anomalies = [
            {"id": "a1", "type": "metadata_break"},
            {"id": "a2", "type": "surveillance_program"},
            {"id": "a3", "type": "sole_source_procurement"},
        ]

        result = initialized_jim.analyze_anomalies(anomalies)

        assert result["total_anomalies_analyzed"] == 3
        assert len(result["individual_assessments"]) == 3

    def test_analyze_includes_timestamp(self, initialized_jim):
        """Test analysis includes timestamp."""
        result = initialized_jim.analyze_anomalies(
            [{"id": "a1", "type": "metadata_break"}]
        )

        assert "analysis_timestamp" in result
        # Check for ISO format with timezone
        assert "T" in result["analysis_timestamp"]
        assert ":" in result["analysis_timestamp"]

    def test_analyze_correlation_summary(self, initialized_jim):
        """Test correlation summary structure."""
        anomalies = [{"id": "a1", "type": "metadata_break"}]
        result = initialized_jim.analyze_anomalies(anomalies)

        summary = result["correlation_summary"]
        assert "doctrine_frequency" in summary
        assert "dominant_doctrines" in summary
        assert "systemic_patterns" in summary

    def test_analyze_risk_summary(self, initialized_jim):
        """Test risk summary structure."""
        anomalies = [{"id": "a1", "type": "metadata_break"}]
        result = initialized_jim.analyze_anomalies(anomalies)

        summary = result["risk_summary"]
        assert "risk_distribution" in summary
        assert "high_priority_count" in summary
        assert "average_score" in summary


class TestGenerateReports:
    """Test report generation."""

    @pytest.fixture
    def analysis_result(self):
        """Provide sample analysis result."""
        return {
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "total_anomalies_analyzed": 2,
            "correlation_summary": {
                "doctrine_frequency": {"due_process": 1},
                "dominant_doctrines": [("due_process", 1)],
                "dominant_cases": [("mathews_v_eldridge_1976", 1)],
                "systemic_patterns": [],
            },
            "risk_summary": {
                "total_anomalies": 2,
                "risk_distribution": {"high": 1, "low": 1},
                "high_priority_count": 1,
                "requires_immediate_review": True,
                "average_score": 0.5,
                "critical_findings": [],
            },
            "individual_assessments": [
                {
                    "anomaly_id": "a1",
                    "overall_score": 0.6,
                    "severity": "high",
                    "correlation": {
                        "doctrines": ["due_process"],
                        "relevant_cases": [],
                    },
                }
            ],
        }

    def test_generate_reports_creates_files(self, tmp_path, analysis_result):
        """Test report generation creates files."""
        jim = JIMCore(output_dir=tmp_path)
        jim.initialize()

        result = jim.generate_reports(analysis_result)

        assert result["success"] is True
        assert "JIM_REPORT.json" in result["generated_files"]
        assert "JIM_SUMMARY.md" in result["generated_files"]
        assert "CASE_LINKAGE_GRAPH.json" in result["generated_files"]

    def test_generate_reports_creates_json(self, tmp_path, analysis_result):
        """Test JSON report created."""
        jim = JIMCore(output_dir=tmp_path)
        jim.initialize()
        jim.generate_reports(analysis_result)

        json_path = tmp_path / "JIM_REPORT.json"
        assert json_path.exists()

        with open(json_path) as f:
            data = json.load(f)
            assert "version" in data
            assert "executive_summary" in data

    def test_generate_reports_creates_markdown(self, tmp_path, analysis_result):
        """Test markdown summary created."""
        jim = JIMCore(output_dir=tmp_path)
        jim.initialize()
        jim.generate_reports(analysis_result)

        md_path = tmp_path / "JIM_SUMMARY.md"
        assert md_path.exists()

        content = md_path.read_text()
        assert "Judicial Interpretive Matrix" in content
        assert "Risk Assessment" in content

    def test_generate_reports_creates_linkage_graph(self, tmp_path, analysis_result):
        """Test linkage graph created."""
        jim = JIMCore(output_dir=tmp_path)
        jim.initialize()
        jim.generate_reports(analysis_result)

        graph_path = tmp_path / "CASE_LINKAGE_GRAPH.json"
        assert graph_path.exists()

        with open(graph_path) as f:
            data = json.load(f)
            assert "graph" in data
            assert "nodes" in data["graph"]
            assert "edges" in data["graph"]


class TestJIMReport:
    """Test JIM report structure."""

    @pytest.fixture
    def initialized_jim(self):
        jim = JIMCore()
        jim.initialize()
        return jim

    def test_jim_report_structure(self, initialized_jim):
        """Test JIM report has correct structure."""
        analysis_result = {
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "total_anomalies_analyzed": 1,
            "correlation_summary": {
                "doctrine_frequency": {},
                "dominant_doctrines": [],
                "dominant_cases": [],
                "systemic_patterns": [],
            },
            "risk_summary": {
                "risk_distribution": {},
                "high_priority_count": 0,
                "requires_immediate_review": False,
                "average_score": 0.0,
                "critical_findings": [],
            },
            "individual_assessments": [],
        }

        report = initialized_jim._create_jim_report(analysis_result)

        assert "version" in report
        assert "generated_at" in report
        assert "metadata" in report
        assert "executive_summary" in report
        assert "doctrinal_analysis" in report
        assert "case_law_citations" in report


class TestSummaryMarkdown:
    """Test summary markdown generation."""

    @pytest.fixture
    def initialized_jim(self):
        jim = JIMCore()
        jim.initialize()
        return jim

    def test_summary_has_header(self, initialized_jim):
        """Test summary has proper header."""
        analysis_result = {
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "total_anomalies_analyzed": 1,
            "correlation_summary": {
                "dominant_doctrines": [],
                "systemic_patterns": [],
                "dominant_cases": [],
            },
            "risk_summary": {
                "risk_distribution": {},
                "average_score": 0.0,
                "high_priority_count": 0,
                "requires_immediate_review": False,
                "critical_findings": [],
            },
        }

        md = initialized_jim._create_summary_markdown(analysis_result)

        assert "# Judicial Interpretive Matrix" in md
        assert "Executive Summary" in md

    def test_summary_has_risk_table(self, initialized_jim):
        """Test summary has risk distribution table."""
        analysis_result = {
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "total_anomalies_analyzed": 1,
            "correlation_summary": {
                "dominant_doctrines": [],
                "systemic_patterns": [],
                "dominant_cases": [],
            },
            "risk_summary": {
                "risk_distribution": {"critical": 1, "high": 2},
                "average_score": 0.6,
                "high_priority_count": 3,
                "requires_immediate_review": True,
                "critical_findings": [],
            },
        }

        md = initialized_jim._create_summary_markdown(analysis_result)

        assert "Risk Distribution" in md
        assert "Critical" in md or "critical" in md


class TestLinkageGraph:
    """Test case linkage graph generation."""

    @pytest.fixture
    def initialized_jim(self):
        jim = JIMCore()
        jim.initialize()
        return jim

    def test_linkage_graph_structure(self, initialized_jim):
        """Test linkage graph has correct structure."""
        analysis_result = {
            "individual_assessments": [
                {
                    "anomaly_id": "a1",
                    "severity": "high",
                    "overall_score": 0.7,
                    "correlation": {
                        "doctrines": ["due_process"],
                        "relevant_cases": [
                            {
                                "case_id": "mathews_v_eldridge_1976",
                                "name": "Mathews v. Eldridge",
                                "citation": "424 U.S. 319 (1976)",
                                "year": 1976,
                                "doctrine": "due_process",
                                "relevance_score": 0.8,
                            }
                        ],
                    },
                }
            ]
        }

        graph = initialized_jim._create_linkage_graph(analysis_result)

        assert "graph" in graph
        assert "nodes" in graph["graph"]
        assert "edges" in graph["graph"]
        assert "statistics" in graph

    def test_linkage_graph_has_nodes(self, initialized_jim):
        """Test linkage graph creates nodes."""
        analysis_result = {
            "individual_assessments": [
                {
                    "anomaly_id": "a1",
                    "severity": "high",
                    "overall_score": 0.7,
                    "correlation": {
                        "doctrines": ["due_process"],
                        "relevant_cases": [],
                    },
                }
            ]
        }

        graph = initialized_jim._create_linkage_graph(analysis_result)

        nodes = graph["graph"]["nodes"]
        assert len(nodes) >= 2  # At least anomaly and doctrine


class TestFullAnalysis:
    """Test full analysis pipeline."""

    def test_run_full_analysis_initializes(self, tmp_path):
        """Test full analysis initializes if needed."""
        jim = JIMCore(output_dir=tmp_path)
        anomalies = [{"id": "a1", "type": "metadata_break"}]

        result = jim.run_full_analysis(anomalies)

        assert result["success"] is True

    def test_run_full_analysis_complete(self, tmp_path):
        """Test full analysis runs complete pipeline."""
        jim = JIMCore(output_dir=tmp_path)
        anomalies = [
            {"id": "a1", "type": "metadata_break"},
            {"id": "a2", "type": "surveillance_program"},
        ]

        result = jim.run_full_analysis(anomalies)

        assert result["success"] is True
        assert "analysis" in result
        assert "reports" in result

    def test_run_full_analysis_creates_files(self, tmp_path):
        """Test full analysis creates all output files."""
        jim = JIMCore(output_dir=tmp_path)
        anomalies = [{"id": "a1", "type": "metadata_break"}]

        jim.run_full_analysis(anomalies)

        assert (tmp_path / "JIM_REPORT.json").exists()
        assert (tmp_path / "JIM_SUMMARY.md").exists()
        assert (tmp_path / "CASE_LINKAGE_GRAPH.json").exists()
