"""Tests for Phase 10 GCN Service."""

from __future__ import annotations


class TestGCNService:
    """Tests for GCNService."""

    def test_gcn_service_initialization(self):
        """Test GCNService can be initialized."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        assert service is not None
        assert service.version == "1.0.0"
        assert service.enforcement_mode == "strict"

    def test_get_state(self):
        """Test GCN state retrieval."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        state = service.get_state()

        assert "timestamp" in state
        assert "gcn_version" in state
        assert "rules_loaded" in state
        assert "rules_active" in state
        assert "enforcement_mode" in state
        assert "health_status" in state
        assert state["gcn_version"] == "1.0.0"
        assert state["health_status"] in ["healthy", "degraded", "error"]

    def test_validate_system_quick(self):
        """Test quick GCN system validation."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        result = service.validate_system(deep=False)

        assert "timestamp" in result
        assert "overall_status" in result
        assert "checks" in result
        assert "errors" in result
        assert "warnings" in result
        assert result["overall_status"] in ["success", "warning", "error"]

    def test_validate_system_deep(self):
        """Test deep GCN system validation."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        result = service.validate_system(deep=True)

        assert "timestamp" in result
        assert "overall_status" in result
        assert "checks" in result
        assert "deep" in result["checks"]

    def test_validate_document_entity(self):
        """Test document entity validation."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        entity_data = {
            "document_text": "This is a test document with valid content.",
            "metadata": {"title": "Test Document"},
        }

        result = service.validate_entity(
            entity_type="document",
            entity_id="test-doc-1",
            entity_data=entity_data,
            scope="document",
        )

        assert "valid" in result
        assert "entity_id" in result
        assert "timestamp" in result
        assert "rules_evaluated" in result
        assert "violations" in result
        assert result["entity_id"] == "test-doc-1"

    def test_validate_document_too_short(self):
        """Test validation of document that is too short."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        entity_data = {
            "document_text": "Short",  # Less than minimum length
            "metadata": {},
        }

        result = service.validate_entity(
            entity_type="document",
            entity_id="short-doc",
            entity_data=entity_data,
            scope="document",
        )

        assert "valid" in result
        assert "violations" in result
        # Should have violation for being too short
        assert any("too short" in str(v).lower() for v in result["violations"])

    def test_validate_job_entity(self):
        """Test job entity validation."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        entity_data = {
            "agent_count": 5,
            "concurrent_tasks": 10,
        }

        result = service.validate_entity(
            entity_type="job",
            entity_id="test-job-1",
            entity_data=entity_data,
            scope="job",
        )

        assert "valid" in result
        assert "entity_id" in result
        assert result["entity_id"] == "test-job-1"

    def test_set_enforcement_mode(self):
        """Test setting enforcement mode."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()

        # Test valid mode
        result = service.set_enforcement_mode("permissive")
        assert result is True
        assert service.enforcement_mode == "permissive"

        # Test another valid mode
        result = service.set_enforcement_mode("audit")
        assert result is True
        assert service.enforcement_mode == "audit"

        # Test invalid mode
        result = service.set_enforcement_mode("invalid_mode")
        assert result is False

    def test_validate_with_different_strictness(self):
        """Test validation with strict and non-strict modes."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        entity_data = {
            "document_text": "Test document",
            "metadata": {},  # Missing title (warning-level violation)
        }

        # Strict mode - should fail on warnings
        result_strict = service.validate_entity(
            entity_type="document",
            entity_id="test-doc",
            entity_data=entity_data,
            scope="document",
            strict=True,
        )

        # Non-strict mode - should pass with warnings
        result_permissive = service.validate_entity(
            entity_type="document",
            entity_id="test-doc",
            entity_data=entity_data,
            scope="document",
            strict=False,
        )

        assert "valid" in result_strict
        assert "valid" in result_permissive
        # Strict should be more restrictive
        if result_strict["warnings"] > 0:
            assert not result_strict["valid"]

    def test_gcn_state_includes_rules_by_type(self):
        """Test that GCN state includes rules breakdown by type."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        state = service.get_state()

        assert "rules_by_type" in state
        assert isinstance(state["rules_by_type"], dict)

    def test_validate_checks_rules_and_policies(self):
        """Test that validation checks both rules and policies."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        result = service.validate_system(
            deep=False,
            check_rules=True,
            check_policies=True,
        )

        assert "checks" in result
        assert "rules" in result["checks"]
        assert "policies" in result["checks"]

    def test_last_validation_timestamp_updated(self):
        """Test that last_validation timestamp is updated after validation."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        assert service.last_validation is None

        service.validate_system()
        assert service.last_validation is not None

    def test_multiple_violations_detected(self):
        """Test detection of multiple constraint violations."""
        from oraculus_di_auditor.gcn import GCNService

        service = GCNService()
        entity_data = {
            "document_text": "x" * 11_000_000,  # Too long
            "metadata": {},  # Missing required metadata
        }

        result = service.validate_entity(
            entity_type="document",
            entity_id="bad-doc",
            entity_data=entity_data,
            scope="document",
        )

        assert "violations" in result
        assert len(result["violations"]) > 0


__all__ = ["TestGCNService"]
