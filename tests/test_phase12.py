"""Tests for Phase 12: Scalar-Convergent Architecture Integration."""

from __future__ import annotations

import json
from pathlib import Path

from oraculus_di_auditor.scalar_convergence import (
    CoherenceAuditor,
    IntegrationEngine,
    Phase12Service,
    ScalarRecursiveMap,
)
from oraculus_di_auditor.scalar_convergence.coherence_auditor import (
    CoherenceIssue,
)
from oraculus_di_auditor.scalar_convergence.integration_engine import (
    IntegrationTask,
)
from oraculus_di_auditor.scalar_convergence.scalar_recursive_map import (
    ScalarLayer,
)


class TestScalarLayer:
    """Tests for ScalarLayer class."""

    def test_scalar_layer_initialization(self):
        """Test ScalarLayer initialization."""
        layer = ScalarLayer(
            layer_id=1,
            name="Test Layer",
            description="Test description",
            inputs=["input1"],
            outputs=["output1"],
            recursion_rules=["rule1"],
            cross_layer_deps=[2],
            failure_states=["fail1"],
            correction_paths=["fix1"],
        )

        assert layer.layer_id == 1
        assert layer.name == "Test Layer"
        assert layer.description == "Test description"
        assert layer.inputs == ["input1"]
        assert layer.outputs == ["output1"]
        assert layer.recursion_rules == ["rule1"]
        assert layer.cross_layer_deps == [2]
        assert layer.failure_states == ["fail1"]
        assert layer.correction_paths == ["fix1"]
        assert layer.health_score == 1.0

    def test_scalar_layer_to_dict(self):
        """Test ScalarLayer to_dict conversion."""
        layer = ScalarLayer(
            layer_id=1,
            name="Test Layer",
            description="Test description",
            inputs=["input1"],
            outputs=["output1"],
            recursion_rules=["rule1"],
            cross_layer_deps=[2],
            failure_states=["fail1"],
            correction_paths=["fix1"],
        )

        layer_dict = layer.to_dict()

        assert layer_dict["layer_id"] == 1
        assert layer_dict["name"] == "Test Layer"
        assert "last_validated" in layer_dict


class TestScalarRecursiveMap:
    """Tests for ScalarRecursiveMap class."""

    def test_srm_initialization(self):
        """Test ScalarRecursiveMap initialization."""
        srm = ScalarRecursiveMap()

        assert srm.version == "1.0.0"
        assert len(srm.layers) == 7
        assert all(i in srm.layers for i in range(1, 8))

    def test_srm_get_layer(self):
        """Test getting individual layers."""
        srm = ScalarRecursiveMap()

        layer1 = srm.get_layer(1)
        assert layer1 is not None
        assert layer1.layer_id == 1
        assert layer1.name == "Primitive Signal Layer"

        layer7 = srm.get_layer(7)
        assert layer7 is not None
        assert layer7.layer_id == 7
        assert layer7.name == "Autonomic Convergence Layer"

        invalid_layer = srm.get_layer(99)
        assert invalid_layer is None

    def test_srm_get_all_layers(self):
        """Test getting all layers."""
        srm = ScalarRecursiveMap()

        all_layers = srm.get_all_layers()

        assert len(all_layers) == 7
        assert all_layers[0].layer_id == 1
        assert all_layers[6].layer_id == 7

    def test_srm_layer_specifications(self):
        """Test that all layers have complete specifications."""
        srm = ScalarRecursiveMap()

        for layer_id in range(1, 8):
            layer = srm.get_layer(layer_id)
            assert layer is not None
            assert len(layer.inputs) > 0
            assert len(layer.outputs) > 0
            assert len(layer.recursion_rules) > 0
            assert len(layer.cross_layer_deps) > 0
            assert len(layer.failure_states) > 0
            assert len(layer.correction_paths) > 0

    def test_srm_validate_dependencies(self):
        """Test dependency validation."""
        srm = ScalarRecursiveMap()

        validation = srm.validate_layer_dependencies()

        assert validation["is_valid"] is True
        assert validation["total_layers"] == 7
        assert validation["valid_connections"] > 0
        assert validation["invalid_connections"] == 0

    def test_srm_dependency_graph(self):
        """Test dependency graph generation."""
        srm = ScalarRecursiveMap()

        graph = srm.get_dependency_graph()

        assert len(graph["nodes"]) == 7
        assert len(graph["edges"]) > 0
        assert "metadata" in graph

    def test_srm_component_mapping(self):
        """Test component to layer mapping."""
        srm = ScalarRecursiveMap()

        # Test various components
        assert 1 in srm.map_component_to_layer("oraculus_di_auditor.ingestion")
        assert 2 in srm.map_component_to_layer("oraculus_di_auditor.db.models")
        assert 3 in srm.map_component_to_layer("oraculus_di_auditor.embeddings")
        assert 4 in srm.map_component_to_layer(
            "oraculus_di_auditor.evolution.change_tracker"
        )
        assert 5 in srm.map_component_to_layer(
            "oraculus_di_auditor.evolution.evolution_engine"
        )
        assert 6 in srm.map_component_to_layer(
            "oraculus_di_auditor.self_healing.detection_engine"
        )
        assert 7 in srm.map_component_to_layer(
            "oraculus_di_auditor.self_healing.self_healing_service"
        )

    def test_srm_multi_layer_components(self):
        """Test components that span multiple layers."""
        srm = ScalarRecursiveMap()

        # Governor should span multiple layers
        governor_layers = srm.map_component_to_layer("oraculus_di_auditor.governor")
        assert len(governor_layers) > 1

    def test_srm_to_dict(self):
        """Test SRM to_dict conversion."""
        srm = ScalarRecursiveMap()

        srm_dict = srm.to_dict()

        assert srm_dict["version"] == "1.0.0"
        assert "created_at" in srm_dict
        assert len(srm_dict["layers"]) == 7
        assert "dependency_graph" in srm_dict
        assert "validation" in srm_dict


class TestCoherenceIssue:
    """Tests for CoherenceIssue class."""

    def test_coherence_issue_initialization(self):
        """Test CoherenceIssue initialization."""
        issue = CoherenceIssue(
            issue_type="test_type",
            severity="high",
            location="test.py",
            description="Test issue",
            impact="Test impact",
            recommendation="Test fix",
        )

        assert issue.issue_type == "test_type"
        assert issue.severity == "high"
        assert issue.location == "test.py"

    def test_coherence_issue_to_dict(self):
        """Test CoherenceIssue to_dict conversion."""
        issue = CoherenceIssue(
            issue_type="test_type",
            severity="high",
            location="test.py",
            description="Test issue",
            impact="Test impact",
            recommendation="Test fix",
        )

        issue_dict = issue.to_dict()

        assert issue_dict["issue_type"] == "test_type"
        assert issue_dict["severity"] == "high"
        assert "detected_at" in issue_dict


class TestCoherenceAuditor:
    """Tests for CoherenceAuditor class."""

    def test_coherence_auditor_initialization(self):
        """Test CoherenceAuditor initialization."""
        auditor = CoherenceAuditor()

        assert auditor.version == "1.0.0"
        assert auditor.root_path is not None
        assert len(auditor.issues) == 0

    def test_coherence_auditor_full_audit(self):
        """Test full coherence audit."""
        auditor = CoherenceAuditor()

        report = auditor.run_full_audit()

        assert "timestamp" in report
        assert "summary" in report
        assert "issues" in report
        assert report["summary"]["total_issues"] > 0
        assert 0.0 <= report["summary"]["coherence_score"] <= 1.0

    def test_coherence_auditor_issue_categories(self):
        """Test that audit covers all issue categories."""
        auditor = CoherenceAuditor()
        auditor.run_full_audit()

        issue_types = {issue.issue_type for issue in auditor.issues}

        # Should have multiple issue types
        assert len(issue_types) > 0

    def test_coherence_auditor_severity_levels(self):
        """Test that issues have valid severity levels."""
        auditor = CoherenceAuditor()
        auditor.run_full_audit()

        valid_severities = {"critical", "high", "medium", "low"}

        for issue in auditor.issues:
            assert issue.severity in valid_severities

    def test_coherence_auditor_prioritization(self):
        """Test issue prioritization."""
        auditor = CoherenceAuditor()
        report = auditor.run_full_audit()

        prioritized = report["prioritized_issues"]

        # Should have prioritized issues
        assert len(prioritized) > 0
        # Should be limited to top 10
        assert len(prioritized) <= 10

    def test_coherence_auditor_recommendations(self):
        """Test recommendation generation."""
        auditor = CoherenceAuditor()
        report = auditor.run_full_audit()

        recommendations = report["recommendations"]

        # Should have recommendations
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)

    def test_coherence_auditor_get_by_severity(self):
        """Test filtering issues by severity."""
        auditor = CoherenceAuditor()
        auditor.run_full_audit()

        medium_issues = auditor.get_issues_by_severity("medium")

        assert all(issue.severity == "medium" for issue in medium_issues)

    def test_coherence_auditor_get_by_type(self):
        """Test filtering issues by type."""
        auditor = CoherenceAuditor()
        auditor.run_full_audit()

        # Get all unique types
        all_types = {issue.issue_type for issue in auditor.issues}

        if all_types:
            issue_type = list(all_types)[0]
            filtered = auditor.get_issues_by_type(issue_type)
            assert all(issue.issue_type == issue_type for issue in filtered)


class TestIntegrationTask:
    """Tests for IntegrationTask class."""

    def test_integration_task_initialization(self):
        """Test IntegrationTask initialization."""
        task = IntegrationTask(
            task_id="TEST-001",
            title="Test Task",
            description="Test description",
            category="test",
            priority="high",
            dependencies=[],
            estimated_effort="2 hours",
            impact="Test impact",
        )

        assert task.task_id == "TEST-001"
        assert task.title == "Test Task"
        assert task.status == "pending"

    def test_integration_task_to_dict(self):
        """Test IntegrationTask to_dict conversion."""
        task = IntegrationTask(
            task_id="TEST-001",
            title="Test Task",
            description="Test description",
            category="test",
            priority="high",
            dependencies=[],
            estimated_effort="2 hours",
            impact="Test impact",
        )

        task_dict = task.to_dict()

        assert task_dict["task_id"] == "TEST-001"
        assert task_dict["status"] == "pending"
        assert "created_at" in task_dict


class TestIntegrationEngine:
    """Tests for IntegrationEngine class."""

    def test_integration_engine_initialization(self):
        """Test IntegrationEngine initialization."""
        engine = IntegrationEngine()

        assert engine.version == "1.0.0"
        assert len(engine.tasks) == 0

    def test_integration_engine_plan_generation(self):
        """Test integration plan generation."""
        engine = IntegrationEngine()
        srm = ScalarRecursiveMap()
        auditor = CoherenceAuditor()

        srm_report = srm.to_dict()
        coherence_report = auditor.run_full_audit()

        plan = engine.generate_integration_plan(srm_report, coherence_report)

        assert "summary" in plan
        assert plan["summary"]["total_tasks"] > 0
        assert "tasks_by_category" in plan
        assert "dependency_graph" in plan
        assert "execution_phases" in plan

    def test_integration_engine_task_categories(self):
        """Test that tasks cover multiple categories."""
        engine = IntegrationEngine()
        srm = ScalarRecursiveMap()
        auditor = CoherenceAuditor()

        srm_report = srm.to_dict()
        coherence_report = auditor.run_full_audit()

        plan = engine.generate_integration_plan(srm_report, coherence_report)

        categories = plan["tasks_by_category"].keys()

        # Should have multiple categories
        expected_categories = {
            "code_adjustment",
            "schema",
            "test",
            "ci",
            "documentation",
        }
        assert len(categories & expected_categories) > 0

    def test_integration_engine_dependencies(self):
        """Test task dependency handling."""
        engine = IntegrationEngine()
        srm = ScalarRecursiveMap()
        auditor = CoherenceAuditor()

        srm_report = srm.to_dict()
        coherence_report = auditor.run_full_audit()

        plan = engine.generate_integration_plan(srm_report, coherence_report)

        # Check dependency graph
        graph = plan["dependency_graph"]
        assert "nodes" in graph
        assert "edges" in graph

    def test_integration_engine_execution_phases(self):
        """Test execution phase determination."""
        engine = IntegrationEngine()
        srm = ScalarRecursiveMap()
        auditor = CoherenceAuditor()

        srm_report = srm.to_dict()
        coherence_report = auditor.run_full_audit()

        plan = engine.generate_integration_plan(srm_report, coherence_report)

        phases = plan["execution_phases"]

        # Should have multiple phases
        assert len(phases) > 0
        # Each phase should have tasks
        assert all("tasks" in phase for phase in phases)

    def test_integration_engine_critical_path(self):
        """Test critical path identification."""
        engine = IntegrationEngine()
        srm = ScalarRecursiveMap()
        auditor = CoherenceAuditor()

        srm_report = srm.to_dict()
        coherence_report = auditor.run_full_audit()

        plan = engine.generate_integration_plan(srm_report, coherence_report)

        critical_path = plan["critical_path"]

        # Should have items on critical path
        assert len(critical_path) > 0


class TestPhase12Service:
    """Tests for Phase12Service class."""

    def test_phase12_service_initialization(self):
        """Test Phase12Service initialization."""
        service = Phase12Service()

        assert service.version == "1.0.0"
        assert service.srm is not None
        assert service.coherence_auditor is not None
        assert service.integration_engine is not None

    def test_phase12_service_execute_analysis(self):
        """Test Phase 12 analysis execution."""
        service = Phase12Service()

        report = service.execute_phase12_analysis()

        assert report["phase"] == "Phase 12: Scalar-Convergent Architecture Integration"
        assert report["status"] == "complete"
        assert report["mode"] == "DRY-RUN"
        assert "summary" in report
        assert "outputs" in report

    def test_phase12_service_outputs(self):
        """Test that all required outputs are generated."""
        service = Phase12Service()

        report = service.execute_phase12_analysis()
        outputs = report["outputs"]

        assert "scalar_recursive_map" in outputs
        assert "coherence_audit" in outputs
        assert "integration_plan" in outputs
        assert "system_analysis" in outputs
        assert "failure_predictions" in outputs

    def test_phase12_service_summary(self):
        """Test summary generation."""
        service = Phase12Service()

        report = service.execute_phase12_analysis()
        summary = report["summary"]

        assert summary["scalar_layers"] == 7
        assert summary["coherence_issues"] >= 0
        assert 0.0 <= summary["coherence_score"] <= 1.0
        assert summary["integration_tasks"] > 0

    def test_phase12_service_system_analysis(self):
        """Test system architecture analysis."""
        service = Phase12Service()

        report = service.execute_phase12_analysis()
        system_analysis = report["outputs"]["system_analysis"]

        assert "total_components" in system_analysis
        assert "layer_distribution" in system_analysis
        assert "architecture_health" in system_analysis

    def test_phase12_service_failure_predictions(self):
        """Test failure mode predictions."""
        service = Phase12Service()

        report = service.execute_phase12_analysis()
        predictions = report["outputs"]["failure_predictions"]

        assert "total_predictions" in predictions
        assert "predictions" in predictions
        assert len(predictions["predictions"]) > 0

    def test_phase12_service_next_steps(self):
        """Test next steps generation."""
        service = Phase12Service()

        report = service.execute_phase12_analysis()

        assert "next_steps" in report
        assert len(report["next_steps"]) > 0
        assert any("Phase 13" in step for step in report["next_steps"])

    def test_phase12_service_get_status(self):
        """Test status retrieval."""
        service = Phase12Service()

        status = service.get_status()

        assert "version" in status
        assert "execution_count" in status
        assert "components" in status

    def test_phase12_service_execution_history(self):
        """Test execution history tracking."""
        service = Phase12Service()

        # Execute multiple times
        service.execute_phase12_analysis()
        service.execute_phase12_analysis()

        status = service.get_status()

        assert status["execution_count"] == 2
        assert status["last_execution"] is not None

    def test_phase12_service_save_reports(self, tmp_path):
        """Test report saving."""
        service = Phase12Service()

        files = service.save_reports(str(tmp_path))

        assert "main_report" in files
        assert "scalar_map" in files
        assert "coherence_audit" in files
        assert "integration_plan" in files

        # Verify files exist
        for file_path in files.values():
            assert Path(file_path).exists()

        # Verify JSON is valid
        for file_path in files.values():
            with open(file_path) as f:
                data = json.load(f)
                assert data is not None


class TestPhase12Integration:
    """Integration tests for Phase 12 components."""

    def test_full_phase12_workflow(self):
        """Test complete Phase 12 workflow."""
        # Initialize service
        service = Phase12Service()

        # Execute analysis
        report = service.execute_phase12_analysis()

        # Verify all components worked together
        assert report["status"] == "complete"
        assert report["summary"]["scalar_layers"] == 7
        assert report["summary"]["coherence_issues"] >= 0
        assert report["summary"]["integration_tasks"] > 0

        # Verify coherence score is reasonable
        coherence_score = report["summary"]["coherence_score"]
        assert 0.0 <= coherence_score <= 1.0

    def test_srm_and_coherence_alignment(self):
        """Test that SRM and coherence auditor work together."""
        srm = ScalarRecursiveMap()
        auditor = CoherenceAuditor()

        # Get reports
        srm_report = srm.to_dict()
        coherence_report = auditor.run_full_audit()

        # Verify both completed successfully
        assert len(srm_report["layers"]) == 7
        assert coherence_report["summary"]["total_issues"] >= 0

    def test_integration_plan_coherence(self):
        """Test that integration plan addresses coherence issues."""
        service = Phase12Service()
        report = service.execute_phase12_analysis()

        integration_tasks = report["outputs"]["integration_plan"]["summary"][
            "total_tasks"
        ]

        # Integration plan should have tasks to address issues
        assert integration_tasks > 0

    def test_phase12_determinism(self):
        """Test that Phase 12 produces consistent results."""
        service = Phase12Service()

        # Run twice
        report1 = service.execute_phase12_analysis()
        report2 = service.execute_phase12_analysis()

        # Key metrics should be consistent
        assert (
            report1["summary"]["scalar_layers"] == report2["summary"]["scalar_layers"]
        )
        assert (
            report1["summary"]["coherence_issues"]
            == report2["summary"]["coherence_issues"]
        )
        assert (
            report1["summary"]["integration_tasks"]
            == report2["summary"]["integration_tasks"]
        )
