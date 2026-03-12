"""Tests for Phase 5 orchestration components."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.orchestrator import Phase5Orchestrator
from oraculus_di_auditor.orchestrator.agents import (
    AnalysisAgent,
    AnomalyAgent,
    DatabaseAgent,
    IngestionAgent,
    InterfaceAgent,
    SynthesisAgent,
)
from oraculus_di_auditor.orchestrator.task_graph import TaskGraph


class TestTaskGraph:
    """Tests for TaskGraph class."""

    def test_add_task(self):
        """Test adding a task to the graph."""
        graph = TaskGraph()
        graph.add_task(
            "task1", "IngestionAgent", "ingest", {"text": "sample"}, dependencies=[]
        )

        assert "task1" in graph.tasks
        assert graph.tasks["task1"].agent_name == "IngestionAgent"
        assert graph.tasks["task1"].status == "pending"

    def test_add_task_with_dependencies(self):
        """Test adding tasks with dependencies."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})
        graph.add_task("task2", "AnalysisAgent", "analyze", {}, dependencies=["task1"])

        assert "task2" in graph.tasks
        assert graph.tasks["task2"].dependencies == ["task1"]

    def test_add_duplicate_task_raises_error(self):
        """Test that adding duplicate task raises error."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})

        with pytest.raises(ValueError, match="already exists"):
            graph.add_task("task1", "IngestionAgent", "ingest", {})

    def test_add_task_with_missing_dependency_raises_error(self):
        """Test that referencing missing dependency raises error."""
        graph = TaskGraph()

        with pytest.raises(ValueError, match="not found"):
            graph.add_task(
                "task1", "AnalysisAgent", "analyze", {}, dependencies=["missing"]
            )

    def test_compute_execution_order_sequential(self):
        """Test execution order for sequential tasks."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})
        graph.add_task("task2", "AnalysisAgent", "analyze", {}, dependencies=["task1"])
        graph.add_task("task3", "SynthesisAgent", "synth", {}, dependencies=["task2"])

        order = graph.compute_execution_order()

        assert len(order) == 3
        assert order[0] == ["task1"]
        assert order[1] == ["task2"]
        assert order[2] == ["task3"]
        assert graph.get_execution_mode() == "sequential"

    def test_compute_execution_order_parallel(self):
        """Test execution order for parallel tasks."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})
        graph.add_task("task2", "IngestionAgent", "ingest", {})
        graph.add_task("task3", "IngestionAgent", "ingest", {})

        order = graph.compute_execution_order()

        assert len(order) == 1
        assert set(order[0]) == {"task1", "task2", "task3"}
        assert graph.get_execution_mode() == "parallel"

    def test_compute_execution_order_hybrid(self):
        """Test execution order for hybrid tasks."""
        graph = TaskGraph()
        # Level 0: parallel
        graph.add_task("ingest1", "IngestionAgent", "ingest", {})
        graph.add_task("ingest2", "IngestionAgent", "ingest", {})

        # Level 1: parallel, depends on level 0
        graph.add_task(
            "analyze1", "AnalysisAgent", "analyze", {}, dependencies=["ingest1"]
        )
        graph.add_task(
            "analyze2", "AnalysisAgent", "analyze", {}, dependencies=["ingest2"]
        )

        # Level 2: single, depends on level 1
        graph.add_task(
            "synth",
            "SynthesisAgent",
            "synth",
            {},
            dependencies=["analyze1", "analyze2"],
        )

        order = graph.compute_execution_order()

        assert len(order) == 3
        assert set(order[0]) == {"ingest1", "ingest2"}
        assert set(order[1]) == {"analyze1", "analyze2"}
        assert order[2] == ["synth"]
        assert graph.get_execution_mode() == "hybrid"

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})

        # Manually create circular dependency (bypassing validation)
        graph.add_task("task2", "AnalysisAgent", "analyze", {}, dependencies=["task1"])
        # Hack to create circular dep
        graph.tasks["task1"].dependencies = ["task2"]

        with pytest.raises(ValueError, match="Circular dependency"):
            graph.compute_execution_order()

    def test_get_ready_tasks(self):
        """Test getting tasks ready to execute."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})
        graph.add_task("task2", "AnalysisAgent", "analyze", {}, dependencies=["task1"])

        # Initially only task1 is ready
        ready = graph.get_ready_tasks()
        assert ready == ["task1"]

        # After task1 completes, task2 is ready
        graph.update_task_status("task1", "completed")
        ready = graph.get_ready_tasks()
        assert ready == ["task2"]

    def test_update_task_status(self):
        """Test updating task status."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})

        graph.update_task_status("task1", "running")
        assert graph.tasks["task1"].status == "running"

        graph.update_task_status("task1", "completed", result={"success": True})
        assert graph.tasks["task1"].status == "completed"
        assert graph.tasks["task1"].result == {"success": True}

    def test_task_graph_to_dict(self):
        """Test converting task graph to dictionary."""
        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})
        graph.compute_execution_order()

        result = graph.to_dict()

        assert "tasks" in result
        assert "execution_order" in result
        assert "execution_mode" in result
        assert result["total_tasks"] == 1


class TestAgents:
    """Tests for Phase 5 agents."""

    def test_ingestion_agent(self):
        """Test IngestionAgent execution."""
        agent = IngestionAgent()
        result = agent.execute(
            {"document_text": "Sample text", "metadata": {"title": "Test"}}
        )

        assert result["agent"] == "IngestionAgent"
        assert result["action"] == "ingest_document"
        assert "outputs" in result
        assert "document_id" in result["outputs"]
        assert result["confidence"] == 1.0

    def test_analysis_agent(self):
        """Test AnalysisAgent execution."""
        agent = AnalysisAgent()
        result = agent.execute(
            {
                "document_text": "There is appropriated $1,000,000",
                "metadata": {"title": "Budget Act"},
            }
        )

        assert result["agent"] == "AnalysisAgent"
        assert result["action"] == "run_analysis"
        assert "findings" in result["outputs"]
        assert "scores" in result["outputs"]
        assert "summary" in result["outputs"]

    def test_anomaly_agent(self):
        """Test AnomalyAgent execution."""
        agent = AnomalyAgent()
        findings = {
            "fiscal": [{"severity": "high", "id": "F001", "issue": "Test issue"}],
            "constitutional": [],
            "surveillance": [],
        }

        result = agent.execute({"findings": findings})

        assert result["agent"] == "AnomalyAgent"
        assert result["action"] == "detect_anomalies"
        assert "anomalies" in result["outputs"]
        assert result["outputs"]["total_count"] == 1
        assert len(result["outputs"]["high_priority"]) == 1

    def test_synthesis_agent_single_doc(self):
        """Test SynthesisAgent with single document."""
        agent = SynthesisAgent()
        analyses = [
            {
                "summary": "Test summary",
                "findings": {"fiscal": [{"severity": "low"}]},
            }
        ]

        result = agent.execute({"analyses": analyses, "mode": "single"})

        assert result["agent"] == "SynthesisAgent"
        assert result["action"] == "synthesize"
        assert "summary" in result["outputs"]
        assert "themes" in result["outputs"]
        assert result["outputs"]["cross_links"] == []

    def test_synthesis_agent_cross_document(self):
        """Test SynthesisAgent with multiple documents."""
        agent = SynthesisAgent()
        analyses = [
            {"summary": "Doc 1", "findings": {"fiscal": [{"severity": "low"}]}},
            {"summary": "Doc 2", "findings": {"fiscal": [{"severity": "medium"}]}},
        ]

        result = agent.execute({"analyses": analyses, "mode": "cross_document"})

        assert result["agent"] == "SynthesisAgent"
        assert result["action"] == "synthesize"
        assert "cross_links" in result["outputs"]
        assert len(result["outputs"]["cross_links"]) >= 0

    def test_database_agent(self):
        """Test DatabaseAgent execution."""
        agent = DatabaseAgent()
        result = agent.execute(
            {"operation": "store_document", "data": {"id": "doc1", "title": "Test"}}
        )

        assert result["agent"] == "DatabaseAgent"
        assert result["action"] == "persist"
        assert result["outputs"]["status"] == "success"
        assert "record_id" in result["outputs"]

    def test_interface_agent_json_format(self):
        """Test InterfaceAgent with JSON format."""
        agent = InterfaceAgent()
        result = agent.execute(
            {"format": "json", "data": {"key": "value", "number": 42}}
        )

        assert result["agent"] == "InterfaceAgent"
        assert result["action"] == "prepare_response"
        assert result["outputs"]["format"] == "json"
        assert result["outputs"]["formatted_data"]["key"] == "value"

    def test_interface_agent_csv_format(self):
        """Test InterfaceAgent with CSV format."""
        agent = InterfaceAgent()
        result = agent.execute(
            {"format": "csv", "data": {"key1": "value1", "key2": "value2"}}
        )

        assert result["agent"] == "InterfaceAgent"
        assert result["outputs"]["format"] == "csv"
        assert isinstance(result["outputs"]["formatted_data"], str)
        assert "key,value" in result["outputs"]["formatted_data"]


class TestPhase5Orchestrator:
    """Tests for Phase 5 Orchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes with all agents."""
        orchestrator = Phase5Orchestrator()

        assert len(orchestrator.agents) == 6
        assert "IngestionAgent" in orchestrator.agents
        assert "AnalysisAgent" in orchestrator.agents
        assert "AnomalyAgent" in orchestrator.agents
        assert "SynthesisAgent" in orchestrator.agents
        assert "DatabaseAgent" in orchestrator.agents
        assert "InterfaceAgent" in orchestrator.agents

    def test_classify_single_document_request(self):
        """Test request classification for single document."""
        orchestrator = Phase5Orchestrator()
        request = {"document_text": "Sample text", "metadata": {}}

        request_type = orchestrator._classify_request(request)

        assert request_type == "single_document_analysis"

    def test_classify_cross_document_request(self):
        """Test request classification for multiple documents."""
        orchestrator = Phase5Orchestrator()
        request = {
            "documents": [
                {"text": "Doc 1", "metadata": {}},
                {"text": "Doc 2", "metadata": {}},
            ]
        }

        request_type = orchestrator._classify_request(request)

        assert request_type == "cross_document_analysis"

    def test_classify_database_query_request(self):
        """Test request classification for database query."""
        orchestrator = Phase5Orchestrator()
        request = {"query": "SELECT * FROM documents"}

        request_type = orchestrator._classify_request(request)

        assert request_type == "database_query"

    def test_execute_single_document_request(self):
        """Test executing single document analysis."""
        orchestrator = Phase5Orchestrator()
        request = {
            "document_text": "There is appropriated $1,000,000",
            "metadata": {"title": "Budget Act"},
        }

        result = orchestrator.execute_request(request)

        assert result["request_type"] == "single_document_analysis"
        assert "execution_plan" in result
        assert "agent_results" in result
        assert "harmonized_output" in result
        assert len(result["agent_results"]) > 0

    def test_execute_request_plan_only_mode(self):
        """Test executing request in plan-only mode."""
        orchestrator = Phase5Orchestrator()
        request = {
            "document_text": "Sample text",
            "metadata": {"title": "Test"},
        }

        result = orchestrator.execute_request(request, mode="plan_only")

        assert result["mode"] == "plan_only"
        assert "execution_plan" in result
        assert "agent_results" not in result
        assert "harmonized_output" not in result

    def test_execute_cross_document_request(self):
        """Test executing cross-document analysis."""
        orchestrator = Phase5Orchestrator()
        request = {
            "documents": [
                {"text": "Doc 1 with fiscal content", "metadata": {"title": "Act 1"}},
                {"text": "Doc 2 with fiscal content", "metadata": {"title": "Act 2"}},
            ]
        }

        result = orchestrator.execute_request(request)

        assert result["request_type"] == "cross_document_analysis"
        assert len(result["agent_results"]) > 0
        assert "harmonized_output" in result

    def test_get_agent_info(self):
        """Test getting agent information."""
        orchestrator = Phase5Orchestrator()
        info = orchestrator.get_agent_info()

        assert "agents" in info
        assert "capabilities" in info
        assert len(info["agents"]) == 6
        assert "IngestionAgent" in info["agents"]

    def test_task_graph_generation_single_doc(self):
        """Test task graph generation for single document."""
        orchestrator = Phase5Orchestrator()
        request = {"document_text": "Sample", "metadata": {}}

        graph = orchestrator._generate_task_plan("single_document_analysis", request)

        assert len(graph.tasks) == 4  # ingest, analyze, anomaly, synthesis
        assert "ingest_01" in graph.tasks
        assert "analyze_01" in graph.tasks
        assert "anomaly_01" in graph.tasks
        assert "synthesis_01" in graph.tasks

    def test_task_graph_generation_cross_doc(self):
        """Test task graph generation for cross-document."""
        orchestrator = Phase5Orchestrator()
        request = {
            "documents": [
                {"text": "Doc 1", "metadata": {}},
                {"text": "Doc 2", "metadata": {}},
            ]
        }

        graph = orchestrator._generate_task_plan("cross_document_analysis", request)

        # Should have: 2 ingest + 2 analyze + 1 synthesis = 5 tasks
        assert len(graph.tasks) >= 5
        assert "ingest_00" in graph.tasks
        assert "ingest_01" in graph.tasks
        assert "synthesis_cross" in graph.tasks

    def test_harmonized_output_format(self):
        """Test harmonized output structure."""
        orchestrator = Phase5Orchestrator()
        request = {
            "document_text": "Sample legislation",
            "metadata": {"title": "Test Act"},
        }

        result = orchestrator.execute_request(request)
        harmonized = result["harmonized_output"]

        assert "metadata" in harmonized
        assert "findings" in harmonized
        assert "scores" in harmonized
        assert "confidence" in harmonized

    def test_provenance_tracking(self):
        """Test that provenance is tracked throughout execution."""
        orchestrator = Phase5Orchestrator()
        request = {"document_text": "Sample", "metadata": {}}

        result = orchestrator.execute_request(request)

        assert "provenance" in result
        assert result["provenance"]["orchestrator"] == "Phase5Orchestrator"
        assert "timestamp" in result["provenance"]

        # Check agent results have provenance
        for agent_result in result["agent_results"]:
            assert "provenance" in agent_result

    def test_confidence_scoring(self):
        """Test that confidence scores are computed."""
        orchestrator = Phase5Orchestrator()
        request = {"document_text": "Sample", "metadata": {}}

        result = orchestrator.execute_request(request)

        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

        # Check agent results have confidence
        for agent_result in result["agent_results"]:
            if "confidence" in agent_result:
                assert 0.0 <= agent_result["confidence"] <= 1.0


class TestResultFormatting:
    """Tests for result formatting functions."""

    def test_task_execution_plan_format(self):
        """Test task execution plan formatting."""
        from oraculus_di_auditor.orchestrator.results import format_task_execution_plan

        graph = TaskGraph()
        graph.add_task("task1", "IngestionAgent", "ingest", {})
        graph.compute_execution_order()

        plan = format_task_execution_plan(graph, {"text": "sample"})

        assert "task_graph" in plan
        assert "agents_involved" in plan
        assert "execution_mode" in plan
        assert "confidence" in plan

    def test_pipeline_output_format(self):
        """Test pipeline output formatting."""
        from oraculus_di_auditor.orchestrator.results import format_pipeline_output

        analysis_result = {
            "metadata": {"title": "Test"},
            "findings": {"fiscal": [], "constitutional": [], "surveillance": []},
            "severity_score": 0.2,
            "lattice_score": 0.95,
            "coherence_bonus": 0.1,
            "flags": ["test_flag"],
            "summary": "Test summary",
        }

        output = format_pipeline_output(analysis_result)

        assert "metadata" in output
        assert "findings" in output
        assert "scores" in output
        assert "provenance" in output
        assert "timestamp" in output
        assert output["findings"]["anomalies"] == []  # Should have anomalies category
