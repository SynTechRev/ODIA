"""Tests for Phase 9 Governor components.

Tests for ValidationEngine, SecurityGatekeeper, PolicyEngine, and GovernorService.
"""

from __future__ import annotations

import pytest


class TestValidationEngine:
    """Tests for ValidationEngine."""

    def test_validation_engine_initialization(self):
        """Test ValidationEngine can be initialized."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        assert engine is not None
        assert engine.validation_cache == {}

    def test_validate_schemas(self):
        """Test schema validation."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate_schemas()

        assert "status" in result
        assert result["status"] in ["success", "warning", "error"]
        assert "schemas_validated" in result
        assert "errors" in result
        assert "warnings" in result

    def test_validate_agents(self):
        """Test agent validation."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate_agents()

        assert "status" in result
        assert "agents_available" in result
        assert "agents_missing" in result
        assert isinstance(result["agents_available"], list)

    def test_validate_dependencies(self):
        """Test dependency validation."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate_dependencies()

        assert "status" in result
        assert "cycles_detected" in result
        assert "dependency_issues" in result

    def test_validate_database(self):
        """Test database validation."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate_database()

        assert "status" in result
        assert "models_available" in result
        assert "models_missing" in result

    def test_validate_orchestrator_readiness(self):
        """Test orchestrator readiness validation."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate_orchestrator_readiness()

        assert "status" in result
        assert "orchestrator_ready" in result
        assert "endpoints_available" in result

    def test_validate_model_versions(self):
        """Test model version validation."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate_model_versions()

        assert "status" in result
        assert "embedding_model" in result
        assert "version_drift" in result

    def test_validate_endpoints(self):
        """Test endpoint validation."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.validate_endpoints()

        assert "status" in result
        assert "endpoints_required" in result
        assert "endpoints_found" in result

    def test_run_full_validation(self):
        """Test full validation run."""
        from oraculus_di_auditor.governor import ValidationEngine

        engine = ValidationEngine()
        result = engine.run_full_validation()

        assert "timestamp" in result
        assert "overall_status" in result
        assert result["overall_status"] in ["success", "warning", "error"]
        assert "checks" in result
        assert "schemas" in result["checks"]
        assert "agents" in result["checks"]
        assert "dependencies" in result["checks"]
        assert "database" in result["checks"]
        assert "orchestrator" in result["checks"]
        assert "models" in result["checks"]
        assert "endpoints" in result["checks"]


class TestSecurityGatekeeper:
    """Tests for SecurityGatekeeper."""

    def test_security_gatekeeper_initialization(self):
        """Test SecurityGatekeeper can be initialized."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        assert gatekeeper is not None
        assert len(gatekeeper.threat_patterns) > 0
        assert len(gatekeeper.allowed_mime_types) > 0

    def test_sanitize_clean_input(self):
        """Test sanitization of clean input."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.sanitize_input(
            "This is a clean document.", {"title": "Test Doc"}
        )

        assert result["status"] == "clean"
        assert len(result["threats_detected"]) == 0
        assert result["threat_score"] == 0.0

    def test_sanitize_xss_threat(self):
        """Test detection of XSS threat."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.sanitize_input(
            "Document with <script>alert('xss')</script> threat", {}
        )

        assert result["status"] == "threat_detected"
        assert len(result["threats_detected"]) > 0
        assert result["threat_score"] > 0.0
        assert any(t["type"] == "xss" for t in result["threats_detected"])

    def test_sanitize_sql_injection(self):
        """Test detection of SQL injection."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.sanitize_input("SELECT * FROM users WHERE id=1", {})

        assert result["status"] == "threat_detected"
        assert len(result["threats_detected"]) > 0
        assert any(t["type"] == "sql_injection" for t in result["threats_detected"])

    def test_sanitize_path_traversal(self):
        """Test detection of path traversal."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.sanitize_input("../../etc/passwd", {})

        assert result["status"] == "threat_detected"
        assert len(result["threats_detected"]) > 0
        assert any(t["type"] == "path_traversal" for t in result["threats_detected"])

    def test_validate_mime_type_allowed(self):
        """Test validation of allowed MIME type."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.validate_mime_type("text/plain")

        assert result["valid"] is True
        assert "error" not in result

    def test_validate_mime_type_disallowed(self):
        """Test validation of disallowed MIME type."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.validate_mime_type("application/x-evil")

        assert result["valid"] is False
        assert "error" in result

    def test_validate_provenance_valid(self):
        """Test provenance validation with valid data."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.validate_provenance(
            "doc_12345678",
            source_path="/data/docs/test.txt",
            expected_hash="a" * 64,
        )

        assert result["status"] in ["valid", "warning"]
        assert result["provenance_verified"] is True

    def test_validate_provenance_path_traversal(self):
        """Test provenance validation detects path traversal."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.validate_provenance(
            "doc_12345678", source_path="../../../etc/passwd"
        )

        assert result["status"] == "error"
        assert len(result["warnings"]) > 0

    def test_calculate_threat_score(self):
        """Test threat score calculation."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()

        # Clean document
        score1 = gatekeeper.calculate_threat_score("Clean text", {})
        assert score1 == 0.0

        # Document with threat
        score2 = gatekeeper.calculate_threat_score("<script>alert('test')</script>", {})
        assert score2 > 0.0

    def test_check_rate_limit_posture_normal(self):
        """Test rate limit posture check - normal."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.check_rate_limit_posture(10, 60)

        assert result["status"] == "normal"
        assert result["action"] == "allow"

    def test_check_rate_limit_posture_warning(self):
        """Test rate limit posture check - warning."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.check_rate_limit_posture(150, 60)

        assert result["status"] == "warning"
        assert result["action"] == "monitor"

    def test_check_rate_limit_posture_critical(self):
        """Test rate limit posture check - critical."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.check_rate_limit_posture(400, 60)

        assert result["status"] == "critical"
        assert result["action"] == "block"

    def test_generate_security_profile(self):
        """Test security profile generation."""
        from oraculus_di_auditor.governor import SecurityGatekeeper

        gatekeeper = SecurityGatekeeper()
        profile = gatekeeper.generate_security_profile(
            "Clean document text",
            {"document_id": "doc_12345678", "title": "Test"},
            "text/plain",
        )

        assert "timestamp" in profile
        assert "overall_status" in profile
        assert "checks" in profile
        assert "input_sanitation" in profile["checks"]
        assert "provenance" in profile["checks"]
        assert "mime_validation" in profile["checks"]
        assert "threat_score" in profile


class TestPolicyEngine:
    """Tests for PolicyEngine."""

    def test_policy_engine_initialization(self):
        """Test PolicyEngine can be initialized."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        assert engine is not None
        assert engine.policy_version == "1.0.0"
        assert len(engine.policies) > 0

    def test_evaluate_document_policies_compliant(self):
        """Test document policy evaluation - compliant."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        result = engine.evaluate_document_policies(
            "This is a valid document with enough text.", {"title": "Test"}
        )

        assert result["status"] == "compliant"
        assert len(result["violations"]) == 0

    def test_evaluate_document_policies_too_short(self):
        """Test document policy evaluation - too short."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        result = engine.evaluate_document_policies("Short", {})

        assert result["status"] == "non_compliant"
        assert len(result["violations"]) > 0

    def test_evaluate_orchestrator_policies_compliant(self):
        """Test orchestrator policy evaluation - compliant."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        result = engine.evaluate_orchestrator_policies(5)

        assert result["status"] == "compliant"
        assert len(result["violations"]) == 0

    def test_evaluate_orchestrator_policies_too_many_docs(self):
        """Test orchestrator policy evaluation - too many documents."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        result = engine.evaluate_orchestrator_policies(150)

        assert result["status"] == "non_compliant"
        assert len(result["violations"]) > 0

    def test_evaluate_security_policies_compliant(self):
        """Test security policy evaluation - compliant."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        result = engine.evaluate_security_policies(
            threat_score=0.1, has_provenance=True
        )

        assert result["status"] == "compliant"
        assert len(result["violations"]) == 0

    def test_evaluate_security_policies_high_threat(self):
        """Test security policy evaluation - high threat score."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        result = engine.evaluate_security_policies(
            threat_score=0.9, has_provenance=True
        )

        assert result["status"] == "non_compliant"
        assert len(result["violations"]) > 0

    def test_generate_compliance_report(self):
        """Test compliance report generation."""
        from oraculus_di_auditor.governor import PolicyEngine

        engine = PolicyEngine()
        eval_results = [
            {"status": "compliant", "violations": [], "warnings": []},
            {
                "status": "non_compliant",
                "violations": [{"severity": "error"}],
                "warnings": [],
            },
        ]

        report = engine.generate_compliance_report(eval_results)

        assert "timestamp" in report
        assert "policy_version" in report
        assert report["total_evaluations"] == 2
        assert report["compliant_count"] == 1
        assert report["non_compliant_count"] == 1
        assert report["overall_compliance"] == "non_compliant"


class TestGovernorService:
    """Tests for GovernorService."""

    def test_governor_service_initialization(self):
        """Test GovernorService can be initialized."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        assert service is not None
        assert service.validation_engine is not None
        assert service.security_gatekeeper is not None
        assert service.policy_engine is not None

    def test_get_system_state(self):
        """Test getting system state."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        state = service.get_system_state()

        assert "timestamp" in state
        assert "overall_health" in state
        assert "governor_version" in state
        assert "validation_summary" in state
        assert "policy_version" in state
        assert "security_posture" in state
        assert "compliance_status" in state

    def test_validate_pipeline_quick(self):
        """Test quick pipeline validation."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        result = service.validate_pipeline(deep=False)

        assert "timestamp" in result
        assert "overall_status" in result
        assert "checks" in result

    def test_validate_pipeline_deep(self):
        """Test deep pipeline validation."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        result = service.validate_pipeline(deep=True)

        assert "timestamp" in result
        assert "overall_status" in result
        assert "checks" in result
        assert len(result["checks"]) >= 5  # Should have all checks

    def test_enforce_policies_clean_document(self):
        """Test policy enforcement on clean document."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        result = service.enforce_policies(
            "This is a valid document with sufficient text for testing.",
            {"document_id": "test_doc_001", "title": "Test Document"},
        )

        assert "timestamp" in result
        assert "enforcement_status" in result
        assert "checks_performed" in result
        assert "security_profile" in result

    def test_enforce_policies_malicious_document(self):
        """Test policy enforcement on malicious document."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        result = service.enforce_policies(
            "<script>alert('xss')</script>", {"title": "Malicious"}
        )

        assert result["enforcement_status"] == "blocked"
        assert len(result["violations"]) > 0

    def test_validate_orchestrator_job_valid(self):
        """Test orchestrator job validation - valid."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        result = service.validate_orchestrator_job(5)

        assert result["validation_status"] == "passed"
        assert len(result["violations"]) == 0

    def test_validate_orchestrator_job_invalid(self):
        """Test orchestrator job validation - invalid."""
        from oraculus_di_auditor.governor import GovernorService

        service = GovernorService()
        result = service.validate_orchestrator_job(150)

        assert result["validation_status"] == "blocked"
        assert len(result["violations"]) > 0


class TestGovernorDatabaseModels:
    """Tests for Phase 9 database models."""

    def test_governance_policy_model_exists(self):
        """Test GovernancePolicy model can be imported."""
        try:
            from oraculus_di_auditor.db.models import GovernancePolicy

            assert GovernancePolicy is not None
        except ImportError:
            pytest.skip("SQLAlchemy not installed")

    def test_validation_result_model_exists(self):
        """Test ValidationResult model can be imported."""
        try:
            from oraculus_di_auditor.db.models import ValidationResult

            assert ValidationResult is not None
        except ImportError:
            pytest.skip("SQLAlchemy not installed")

    def test_security_event_model_exists(self):
        """Test SecurityEvent model can be imported."""
        try:
            from oraculus_di_auditor.db.models import SecurityEvent

            assert SecurityEvent is not None
        except ImportError:
            pytest.skip("SQLAlchemy not installed")


class TestGovernorAPIEndpoints:
    """Tests for Phase 9 API endpoints."""

    def test_governor_state_endpoint_exists(self):
        """Test /governor/state endpoint is available."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)
            response = client.get("/api/v1/info")
            assert response.status_code == 200
            info = response.json()
            assert "/governor/state" in info["endpoints"]
        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_governor_state_endpoint(self):
        """Test /governor/state endpoint returns valid data."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)
            response = client.get("/governor/state")
            assert response.status_code == 200

            data = response.json()
            assert "timestamp" in data
            assert "overall_health" in data
            assert "governor_version" in data
        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_governor_validate_endpoint(self):
        """Test /governor/validate endpoint."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)
            response = client.post("/governor/validate", json={"deep": False})
            assert response.status_code == 200

            data = response.json()
            assert "timestamp" in data
            assert "overall_status" in data
            assert "checks" in data
        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_governor_enforce_endpoint(self):
        """Test /governor/enforce endpoint."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)
            request_data = {
                "document_text": "This is a test document with valid content.",
                "metadata": {"title": "Test Document"},
                "options": {},
            }
            response = client.post("/governor/enforce", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert "timestamp" in data
            assert "enforcement_status" in data
            assert "checks_performed" in data
        except ImportError:
            pytest.skip("FastAPI not installed")
