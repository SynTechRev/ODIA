"""Tests for Phase 11 Evolution Engine."""

from oraculus_di_auditor.evolution import ChangeTracker, EvolutionEngine


class TestChangeTracker:
    """Tests for ChangeTracker."""

    def test_change_tracker_initialization(self):
        """Test change tracker initializes correctly."""
        tracker = ChangeTracker()
        assert tracker is not None
        assert len(tracker.changes) == 0
        assert len(tracker.change_map) == 0

    def test_record_change(self):
        """Test recording a change."""
        tracker = ChangeTracker()

        change_id = tracker.record_change(
            change_type="refactor",
            description="Test refactoring",
            affected_files=["test.py"],
            before_state={"code": "old"},
            after_state={"code": "new"},
            reversible=True,
        )

        assert change_id is not None
        assert change_id in tracker.change_map
        assert len(tracker.changes) == 1

        change = tracker.get_change(change_id)
        assert change["change_type"] == "refactor"
        assert change["description"] == "Test refactoring"
        assert change["reversible"] is True
        assert change["applied"] is False

    def test_mark_applied(self):
        """Test marking a change as applied."""
        tracker = ChangeTracker()
        change_id = tracker.record_change(
            change_type="test",
            description="Test change",
            affected_files=[],
            before_state={},
            after_state={},
        )

        tracker.mark_applied(change_id, success=True, details={"info": "test"})

        change = tracker.get_change(change_id)
        assert change["applied"] is True
        assert change["application_success"] is True
        assert "applied_at" in change

    def test_reverse_change(self):
        """Test reversing a change."""
        tracker = ChangeTracker()
        change_id = tracker.record_change(
            change_type="test",
            description="Test change",
            affected_files=[],
            before_state={"value": "original"},
            after_state={"value": "modified"},
            reversible=True,
        )

        # Mark as applied first
        tracker.mark_applied(change_id, success=True)

        # Now reverse it
        result = tracker.reverse_change(change_id)
        assert result["status"] == "success"
        assert "restore_state" in result

        change = tracker.get_change(change_id)
        assert change["reversed"] is True
        assert "reversed_at" in change

    def test_reverse_non_reversible_change(self):
        """Test attempting to reverse a non-reversible change."""
        tracker = ChangeTracker()
        change_id = tracker.record_change(
            change_type="test",
            description="Test change",
            affected_files=[],
            before_state={},
            after_state={},
            reversible=False,
        )

        tracker.mark_applied(change_id, success=True)

        result = tracker.reverse_change(change_id)
        assert result["status"] == "error"
        assert "not reversible" in result["message"]

    def test_get_changes_by_type(self):
        """Test getting changes by type."""
        tracker = ChangeTracker()

        tracker.record_change("refactor", "Refactor 1", [], {}, {})
        tracker.record_change("optimization", "Optimize 1", [], {}, {})
        tracker.record_change("refactor", "Refactor 2", [], {}, {})

        refactor_changes = tracker.get_changes_by_type("refactor")
        assert len(refactor_changes) == 2

        optimize_changes = tracker.get_changes_by_type("optimization")
        assert len(optimize_changes) == 1

    def test_get_changes_by_file(self):
        """Test getting changes by file."""
        tracker = ChangeTracker()

        tracker.record_change("refactor", "Change 1", ["file1.py"], {}, {})
        tracker.record_change("refactor", "Change 2", ["file2.py"], {}, {})
        tracker.record_change("refactor", "Change 3", ["file1.py", "file2.py"], {}, {})

        file1_changes = tracker.get_changes_by_file("file1.py")
        assert len(file1_changes) == 2

    def test_get_change_history(self):
        """Test getting change history."""
        tracker = ChangeTracker()

        for i in range(5):
            tracker.record_change("test", f"Change {i}", [], {}, {})

        history = tracker.get_change_history()
        assert len(history) == 5

        limited_history = tracker.get_change_history(limit=3)
        assert len(limited_history) == 3

    def test_get_statistics(self):
        """Test getting change statistics."""
        tracker = ChangeTracker()

        # Create some changes
        change1 = tracker.record_change("refactor", "C1", [], {}, {})
        change2 = tracker.record_change("optimization", "C2", [], {}, {})
        change3 = tracker.record_change("refactor", "C3", [], {}, {})
        assert change3  # ensure variable used

        # Mark some as applied
        tracker.mark_applied(change1, success=True)
        tracker.mark_applied(change2, success=False)

        stats = tracker.get_statistics()
        assert stats["total_changes"] == 3
        assert stats["applied_changes"] == 2
        assert stats["successful_changes"] == 1
        assert "changes_by_type" in stats
        assert stats["changes_by_type"]["refactor"] == 2


class TestEvolutionEngine:
    """Tests for EvolutionEngine."""

    def test_evolution_engine_initialization(self):
        """Test evolution engine initializes correctly."""
        engine = EvolutionEngine()
        assert engine is not None
        assert engine.change_tracker is not None
        assert engine.version == "1.0.0"
        assert len(engine.evolution_cycles) == 0

    def test_monitor_system(self):
        """Test system monitoring."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()

        assert "timestamp" in monitoring_data
        assert "metrics" in monitoring_data
        assert "code_quality" in monitoring_data["metrics"]
        assert "test_coverage" in monitoring_data["metrics"]
        assert "dependency_health" in monitoring_data["metrics"]
        assert "architecture_coherence" in monitoring_data["metrics"]
        assert "performance_baseline" in monitoring_data["metrics"]

    def test_analyze_improvements(self):
        """Test improvement analysis."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()
        analysis = engine.analyze_improvements(monitoring_data)

        assert "timestamp" in analysis
        assert "monitoring_timestamp" in analysis
        assert "total_opportunities" in analysis
        assert "opportunities" in analysis
        assert "prioritized_opportunities" in analysis
        assert isinstance(analysis["opportunities"], list)

    def test_design_refactoring(self):
        """Test refactoring design."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()
        analysis = engine.analyze_improvements(monitoring_data)
        refactoring = engine.design_refactoring(analysis)

        assert "timestamp" in refactoring
        assert "analysis_timestamp" in refactoring
        assert "total_plans" in refactoring
        assert "plans" in refactoring
        assert isinstance(refactoring["plans"], list)

    def test_reinforce_system(self):
        """Test system reinforcement."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()
        analysis = engine.analyze_improvements(monitoring_data)
        refactoring = engine.design_refactoring(analysis)
        reinforcement = engine.reinforce_system(refactoring)

        assert "timestamp" in reinforcement
        assert "design_timestamp" in reinforcement
        assert "total_reinforcements" in reinforcement
        assert "reinforcements" in reinforcement
        assert isinstance(reinforcement["reinforcements"], list)

    def test_validate_improvements(self):
        """Test improvement validation."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()
        analysis = engine.analyze_improvements(monitoring_data)
        refactoring = engine.design_refactoring(analysis)
        reinforcement = engine.reinforce_system(refactoring)
        validation = engine.validate_improvements(reinforcement)

        assert "timestamp" in validation
        assert "reinforcement_timestamp" in validation
        assert "total_validations" in validation
        assert "passed_validations" in validation
        assert "failed_validations" in validation
        assert "validations" in validation

    def test_record_changes(self):
        """Test change recording."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()
        analysis = engine.analyze_improvements(monitoring_data)
        refactoring = engine.design_refactoring(analysis)
        reinforcement = engine.reinforce_system(refactoring)
        validation = engine.validate_improvements(reinforcement)
        recording = engine.record_changes(validation, refactoring)

        assert "timestamp" in recording
        assert "validation_timestamp" in recording
        assert "recorded_changes" in recording
        assert "total_recorded" in recording
        assert isinstance(recording["recorded_changes"], list)

    def test_deploy_improvements(self):
        """Test improvement deployment."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()
        analysis = engine.analyze_improvements(monitoring_data)
        refactoring = engine.design_refactoring(analysis)
        reinforcement = engine.reinforce_system(refactoring)
        validation = engine.validate_improvements(reinforcement)
        recording = engine.record_changes(validation, refactoring)
        deployment = engine.deploy_improvements(recording, auto_deploy=False)

        assert "timestamp" in deployment
        assert "recording_timestamp" in deployment
        assert "auto_deploy_enabled" in deployment
        assert deployment["auto_deploy_enabled"] is False
        assert "changes_available" in deployment
        assert "changes_deployed" in deployment
        assert "deployment_status" in deployment
        assert deployment["changes_deployed"] == 0  # No auto-deploy

    def test_deploy_improvements_with_auto_deploy(self):
        """Test improvement deployment with auto-deploy."""
        engine = EvolutionEngine()
        monitoring_data = engine.monitor_system()
        analysis = engine.analyze_improvements(monitoring_data)
        refactoring = engine.design_refactoring(analysis)
        reinforcement = engine.reinforce_system(refactoring)
        validation = engine.validate_improvements(reinforcement)
        recording = engine.record_changes(validation, refactoring)
        deployment = engine.deploy_improvements(recording, auto_deploy=True)

        assert deployment["auto_deploy_enabled"] is True
        # Changes should be deployed if any were recorded

    def test_run_evolution_cycle(self):
        """Test running complete evolution cycle."""
        engine = EvolutionEngine()
        cycle_report = engine.run_evolution_cycle(auto_deploy=False)

        assert "cycle_id" in cycle_report
        assert cycle_report["cycle_id"] == 1
        assert "timestamp_start" in cycle_report
        assert "timestamp_end" in cycle_report
        assert "duration_seconds" in cycle_report
        assert "auto_deploy" in cycle_report
        assert "summary" in cycle_report
        assert "outcome" in cycle_report

        # Verify summary has all expected keys
        summary = cycle_report["summary"]
        assert "opportunities_found" in summary
        assert "plans_created" in summary
        assert "reinforcements_planned" in summary
        assert "validations_passed" in summary
        assert "changes_recorded" in summary
        assert "changes_deployed" in summary

        # Engine should have recorded the cycle
        assert len(engine.evolution_cycles) == 1

    def test_get_evolution_state(self):
        """Test getting evolution state."""
        engine = EvolutionEngine()

        # Run a cycle first
        engine.run_evolution_cycle(auto_deploy=False)

        state = engine.get_evolution_state()

        assert "timestamp" in state
        assert "version" in state
        assert "total_cycles" in state
        assert state["total_cycles"] == 1
        assert "total_changes_tracked" in state
        assert "successful_changes" in state
        assert "success_rate" in state
        assert "recent_cycles" in state
        assert len(state["recent_cycles"]) == 1

    def test_multiple_evolution_cycles(self):
        """Test running multiple evolution cycles."""
        engine = EvolutionEngine()

        # Run 3 cycles
        for i in range(3):
            cycle_report = engine.run_evolution_cycle(auto_deploy=False)
            assert cycle_report["cycle_id"] == i + 1

        assert len(engine.evolution_cycles) == 3

        state = engine.get_evolution_state()
        assert state["total_cycles"] == 3
