"""Tests for Phase 11 Self-Healing Layer."""

from oraculus_di_auditor.self_healing import (
    CorrectionEngine,
    DetectionEngine,
    PreventionEngine,
    SelfHealingService,
)


class TestDetectionEngine:
    """Tests for DetectionEngine."""

    def test_detection_engine_initialization(self):
        """Test detection engine initializes correctly."""
        engine = DetectionEngine()
        assert engine is not None
        assert len(engine.detection_history) == 0

    def test_detect_broken_imports(self):
        """Test broken import detection."""
        engine = DetectionEngine()
        issues = engine.detect_broken_imports()
        assert isinstance(issues, list)
        # Should detect any actual broken imports in the codebase

    def test_detect_schema_divergence(self):
        """Test schema divergence detection."""
        engine = DetectionEngine()
        issues = engine.detect_schema_divergence()
        assert isinstance(issues, list)

    def test_detect_anti_patterns(self):
        """Test anti-pattern detection."""
        engine = DetectionEngine()
        issues = engine.detect_anti_patterns()
        assert isinstance(issues, list)

    def test_detect_performance_bottlenecks(self):
        """Test performance bottleneck detection."""
        engine = DetectionEngine()
        issues = engine.detect_performance_bottlenecks()
        assert isinstance(issues, list)

    def test_detect_unreachable_code(self):
        """Test unreachable code detection."""
        engine = DetectionEngine()
        issues = engine.detect_unreachable_code()
        assert isinstance(issues, list)

    def test_run_full_detection(self):
        """Test full detection scan."""
        engine = DetectionEngine()
        report = engine.run_full_detection()

        assert "timestamp" in report
        assert "scan_type" in report
        assert report["scan_type"] == "full"
        assert "checks" in report
        assert "summary" in report

        # Verify all checks are present
        assert "broken_imports" in report["checks"]
        assert "schema_divergence" in report["checks"]
        assert "anti_patterns" in report["checks"]
        assert "performance_bottlenecks" in report["checks"]
        assert "unreachable_code" in report["checks"]

        # Verify summary statistics
        assert "total_issues" in report["summary"]
        assert "critical_issues" in report["summary"]
        assert "high_issues" in report["summary"]
        assert "health_score" in report["summary"]
        assert 0.0 <= report["summary"]["health_score"] <= 1.0


class TestCorrectionEngine:
    """Tests for CorrectionEngine."""

    def test_correction_engine_initialization(self):
        """Test correction engine initializes correctly."""
        engine = CorrectionEngine()
        assert engine is not None
        assert engine.dry_run is True
        assert len(engine.correction_history) == 0

    def test_set_dry_run(self):
        """Test setting dry run mode."""
        engine = CorrectionEngine()
        engine.set_dry_run(False)
        assert engine.dry_run is False

        engine.set_dry_run(True)
        assert engine.dry_run is True

    def test_propose_import_fixes(self):
        """Test import fix proposals."""
        engine = CorrectionEngine()
        issues = [
            {
                "type": "broken_import",
                "file": "test.py",
                "module": "nonexistent_module",
                "line": 10,
                "error": "No module named 'nonexistent_module'",
                "severity": "high",
            }
        ]

        fixes = engine.propose_import_fixes(issues)
        assert isinstance(fixes, list)
        assert len(fixes) == 1
        assert fixes[0]["fix_type"] == "import_correction"

    def test_propose_schema_fixes(self):
        """Test schema fix proposals."""
        engine = CorrectionEngine()
        issues = [
            {
                "type": "missing_index",
                "model": "TestModel",
                "table": "test_table",
                "column": "test_column",
                "severity": "medium",
            }
        ]

        fixes = engine.propose_schema_fixes(issues)
        assert isinstance(fixes, list)
        assert len(fixes) == 1
        assert fixes[0]["fix_type"] == "add_index"

    def test_generate_patch_report(self):
        """Test patch report generation."""
        detection_engine = DetectionEngine()
        detection_report = detection_engine.run_full_detection()

        correction_engine = CorrectionEngine()
        patch_report = correction_engine.generate_patch_report(detection_report)

        assert "timestamp" in patch_report
        assert "detection_summary" in patch_report
        assert "fixes" in patch_report
        assert "prioritized_fixes" in patch_report
        assert "total_fixes_proposed" in patch_report

    def test_apply_fix_dry_run(self):
        """Test applying fix in dry run mode."""
        engine = CorrectionEngine()
        fix = {
            "fix_type": "test_fix",
            "description": "Test fix",
            "risk": "low",
            "confidence": 0.9,
        }

        result = engine.apply_fix(fix)
        assert result["status"] == "skipped"
        assert result["reason"] == "dry_run mode enabled"


class TestPreventionEngine:
    """Tests for PreventionEngine."""

    def test_prevention_engine_initialization(self):
        """Test prevention engine initializes correctly."""
        engine = PreventionEngine()
        assert engine is not None
        assert len(engine.guards) > 0  # Should have default guards
        assert len(engine.prevention_history) == 0

    def test_add_guard(self):
        """Test adding a guard."""
        engine = PreventionEngine()
        initial_count = len(engine.guards)

        engine.add_guard("test_guard", {"type": "test", "action": "warn"})
        assert len(engine.guards) == initial_count + 1
        assert "test_guard" in engine.guards

    def test_remove_guard(self):
        """Test removing a guard."""
        engine = PreventionEngine()
        engine.add_guard("test_guard", {"type": "test", "action": "warn"})

        result = engine.remove_guard("test_guard")
        assert result is True
        assert "test_guard" not in engine.guards

        # Try removing non-existent guard
        result = engine.remove_guard("nonexistent_guard")
        assert result is False

    def test_register_fallback(self):
        """Test registering a fallback function."""
        engine = PreventionEngine()

        def test_fallback():
            return "fallback"

        engine.register_fallback("test_operation", test_fallback)
        assert "test_operation" in engine.fallbacks

    def test_set_threshold(self):
        """Test setting a threshold."""
        engine = PreventionEngine()
        engine.set_threshold("test_metric", 0.75)
        assert engine.thresholds["test_metric"] == 0.75

    def test_check_guard(self):
        """Test checking a guard."""
        engine = PreventionEngine()
        result = engine.check_guard("import_validation", {})

        assert "guard_id" in result
        assert "passed" in result
        assert "action" in result
        assert isinstance(result["passed"], bool)

    def test_check_all_guards(self):
        """Test checking all guards."""
        engine = PreventionEngine()
        results = engine.check_all_guards({})

        assert "timestamp" in results
        assert "total_guards" in results
        assert "guards_passed" in results
        assert "guards_failed" in results
        assert "details" in results
        assert "overall_status" in results
        assert results["total_guards"] > 0

    def test_generate_prevention_plan(self):
        """Test prevention plan generation."""
        detection_engine = DetectionEngine()
        detection_report = detection_engine.run_full_detection()

        prevention_engine = PreventionEngine()
        plan = prevention_engine.generate_prevention_plan(detection_report)

        assert "timestamp" in plan
        assert "recommended_guards" in plan
        assert "recommended_fallbacks" in plan
        assert "recommended_thresholds" in plan


class TestSelfHealingService:
    """Tests for SelfHealingService."""

    def test_self_healing_service_initialization(self):
        """Test self-healing service initializes correctly."""
        service = SelfHealingService()
        assert service is not None
        assert service.detection_engine is not None
        assert service.correction_engine is not None
        assert service.prevention_engine is not None
        assert service.version == "1.0.0"
        assert len(service.healing_cycles) == 0

    def test_get_system_health(self):
        """Test getting system health."""
        service = SelfHealingService()
        health = service.get_system_health()

        assert "timestamp" in health
        assert "version" in health
        assert "overall_health_score" in health
        assert "status" in health
        assert "detection_health_score" in health
        assert "guard_health_score" in health
        assert 0.0 <= health["overall_health_score"] <= 1.0

        # Status should be one of the expected values
        assert health["status"] in ["healthy", "warning", "degraded", "critical"]

    def test_run_healing_cycle(self):
        """Test running a healing cycle."""
        service = SelfHealingService()
        report = service.run_healing_cycle(auto_apply=False)

        assert "cycle_id" in report
        assert report["cycle_id"] == 1
        assert "timestamp_start" in report
        assert "timestamp_end" in report
        assert "duration_seconds" in report
        assert "auto_apply_enabled" in report
        assert report["auto_apply_enabled"] is False
        assert "detection_summary" in report
        assert "total_fixes_proposed" in report
        assert "fixes_applied" in report
        assert report["fixes_applied"] == 0  # No fixes applied without auto_apply
        assert "prevention_plan" in report
        assert "cycle_outcome" in report

        # Service should have recorded the cycle
        assert len(service.healing_cycles) == 1

    def test_run_healing_cycle_with_auto_apply(self):
        """Test running a healing cycle with auto-apply."""
        service = SelfHealingService()
        report = service.run_healing_cycle(auto_apply=True)

        assert report["auto_apply_enabled"] is True
        # Fixes might be applied if there are low-risk, high-confidence fixes

    def test_get_healing_report(self):
        """Test getting comprehensive healing report."""
        service = SelfHealingService()
        report = service.get_healing_report()

        assert "timestamp" in report
        assert "service_version" in report
        assert "system_health" in report
        assert "detection" in report
        assert "correction" in report
        assert "prevention" in report
        assert "history" in report

    def test_validate_system_integrity(self):
        """Test system integrity validation."""
        service = SelfHealingService()
        validation = service.validate_system_integrity()

        assert "timestamp" in validation
        assert "integrity_score" in validation
        assert "status" in validation
        assert "components" in validation
        assert "recommendations" in validation

        assert 0.0 <= validation["integrity_score"] <= 1.0
        assert validation["status"] in [
            "excellent",
            "good",
            "acceptable",
            "poor",
            "failing",
        ]
