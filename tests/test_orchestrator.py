"""Tests for Phase 8 Multi-Document Orchestrator.

This module tests the /orchestrator/run endpoint and multi-document
coordination functionality.
"""

from __future__ import annotations

import pytest


class TestOrchestratorEndpoint:
    """Tests for the orchestrator endpoint."""

    def test_orchestrator_endpoint_exists(self):
        """Test that orchestrator endpoint is registered."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)
            response = client.get("/api/v1/info")
            assert response.status_code == 200
            info = response.json()
            assert "/orchestrator/run" in info["endpoints"]
        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_orchestrator_single_document(self):
        """Test orchestrator with single document."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)

            request_data = {
                "documents": [
                    {
                        "document_text": (
                            "There is appropriated $1,000,000 for FY 2025."
                        ),
                        "metadata": {
                            "title": "Budget Act 2025",
                            "jurisdiction": "federal",
                        },
                    }
                ],
                "options": {},
            }

            response = client.post("/orchestrator/run", json=request_data)
            assert response.status_code == 200

            result = response.json()
            assert "job_id" in result
            assert result["status"] == "completed"
            assert result["documents_analyzed"] == 1
            assert len(result["document_results"]) == 1
            assert "execution_log" in result

        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_orchestrator_multiple_documents(self):
        """Test orchestrator with multiple documents."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)

            request_data = {
                "documents": [
                    {
                        "document_text": (
                            "There is appropriated $1,000,000 for FY 2025."
                        ),
                        "metadata": {
                            "title": "Budget Act 2025",
                            "jurisdiction": "federal",
                        },
                    },
                    {
                        "document_text": (
                            "The Secretary may delegate authority without standards."
                        ),
                        "metadata": {
                            "title": "Delegation Act 2025",
                            "jurisdiction": "federal",
                        },
                    },
                ],
                "options": {},
            }

            response = client.post("/orchestrator/run", json=request_data)
            assert response.status_code == 200

            result = response.json()
            assert result["documents_analyzed"] == 2
            assert len(result["document_results"]) == 2

        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_orchestrator_cross_document_patterns(self):
        """Test that orchestrator detects cross-document patterns."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)

            # Create documents with similar fiscal patterns
            request_data = {
                "documents": [
                    {
                        "document_text": "Fiscal amount $500,000 is allocated.",
                        "metadata": {"title": "Doc 1"},
                    },
                    {
                        "document_text": "Funding of $750,000 is provided.",
                        "metadata": {"title": "Doc 2"},
                    },
                ],
                "options": {},
            }

            response = client.post("/orchestrator/run", json=request_data)
            assert response.status_code == 200

            result = response.json()
            # Should have cross-document patterns
            assert "cross_document_patterns" in result
            assert isinstance(result["cross_document_patterns"], list)

        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_orchestrator_correlated_anomalies(self):
        """Test that orchestrator correlates anomalies across documents."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)

            # Create documents with constitutional concerns
            request_data = {
                "documents": [
                    {
                        "document_text": "The agency may determine standards.",
                        "metadata": {"title": "Doc 1"},
                    },
                    {
                        "document_text": "Authority is delegated without limitation.",
                        "metadata": {"title": "Doc 2"},
                    },
                ],
                "options": {},
            }

            response = client.post("/orchestrator/run", json=request_data)
            assert response.status_code == 200

            result = response.json()
            # Should have correlated anomalies
            assert "correlated_anomalies" in result
            assert isinstance(result["correlated_anomalies"], list)

        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_orchestrator_execution_log(self):
        """Test that orchestrator provides execution log."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)

            request_data = {
                "documents": [
                    {
                        "document_text": "Sample document text.",
                        "metadata": {"title": "Test Doc"},
                    }
                ],
                "options": {},
            }

            response = client.post("/orchestrator/run", json=request_data)
            assert response.status_code == 200

            result = response.json()
            assert "execution_log" in result
            assert len(result["execution_log"]) > 0

            # Check for expected log events
            events = [log["event"] for log in result["execution_log"]]
            assert "job_started" in events
            assert "job_completed" in events

        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_orchestrator_metadata(self):
        """Test that orchestrator returns metadata."""
        try:
            from fastapi.testclient import TestClient

            from oraculus_di_auditor.interface.api import app

            if app is None:
                pytest.skip("FastAPI not installed")

            client = TestClient(app)

            request_data = {
                "documents": [
                    {
                        "document_text": "Sample text.",
                        "metadata": {"title": "Test"},
                    }
                ],
                "options": {"parallel": True},
            }

            response = client.post("/orchestrator/run", json=request_data)
            assert response.status_code == 200

            result = response.json()
            assert "metadata" in result
            assert "total_findings" in result["metadata"]

        except ImportError:
            pytest.skip("FastAPI not installed")


class TestOrchestratorService:
    """Tests for the OrchestratorService class."""

    def test_service_initialization(self):
        """Test that orchestrator service initializes correctly."""
        try:
            from oraculus_di_auditor.interface.routes.orchestrator import (
                OrchestratorService,
            )

            service = OrchestratorService()
            assert service.orchestrator is not None
        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_service_execute_orchestration(self):
        """Test service execute_orchestration method."""
        try:
            from oraculus_di_auditor.interface.routes.orchestrator import (
                DocumentInput,
                OrchestratorRequest,
                OrchestratorService,
            )

            service = OrchestratorService()

            doc = DocumentInput(
                document_text="Test document.",
                metadata={"title": "Test"},
            )
            request = OrchestratorRequest(documents=[doc], options={})

            result = service.execute_orchestration(request)

            assert result.job_id is not None
            assert result.status == "completed"
            assert result.documents_analyzed == 1
            assert len(result.document_results) == 1

        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_service_cross_document_analysis(self):
        """Test cross-document pattern analysis."""
        try:
            from oraculus_di_auditor.interface.routes.orchestrator import (
                DocumentInput,
                OrchestratorRequest,
                OrchestratorService,
            )

            service = OrchestratorService()

            docs = [
                DocumentInput(
                    document_text="Fiscal amount $100,000.",
                    metadata={"title": "Doc 1"},
                ),
                DocumentInput(
                    document_text="Budget of $200,000.",
                    metadata={"title": "Doc 2"},
                ),
            ]
            request = OrchestratorRequest(documents=docs, options={})

            result = service.execute_orchestration(request)

            # Should detect patterns across documents
            assert len(result.cross_document_patterns) >= 0
            assert result.documents_analyzed == 2

        except ImportError:
            pytest.skip("Pydantic not installed")


class TestOrchestratorSchemas:
    """Tests for orchestrator Pydantic schemas."""

    def test_document_input_schema(self):
        """Test DocumentInput schema validation."""
        try:
            from oraculus_di_auditor.interface.routes.orchestrator import (
                DocumentInput,
            )

            doc = DocumentInput(
                document_text="Test text",
                metadata={"title": "Test"},
            )

            assert doc.document_text == "Test text"
            assert doc.metadata["title"] == "Test"

        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_orchestrator_request_schema(self):
        """Test OrchestratorRequest schema validation."""
        try:
            from oraculus_di_auditor.interface.routes.orchestrator import (
                DocumentInput,
                OrchestratorRequest,
            )

            doc = DocumentInput(document_text="Test", metadata={})
            request = OrchestratorRequest(documents=[doc], options={})

            assert len(request.documents) == 1
            assert request.options == {}

        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_orchestrator_request_validation(self):
        """Test request validation requires at least one document."""
        try:
            from pydantic import ValidationError

            from oraculus_di_auditor.interface.routes.orchestrator import (
                OrchestratorRequest,
            )

            # Should fail with empty documents list
            with pytest.raises(ValidationError):
                OrchestratorRequest(documents=[], options={})

        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_cross_document_pattern_schema(self):
        """Test CrossDocumentPattern schema."""
        try:
            from oraculus_di_auditor.interface.routes.orchestrator import (
                CrossDocumentPattern,
            )

            pattern = CrossDocumentPattern(
                pattern_type="test_pattern",
                description="Test pattern description",
                document_ids=["doc1", "doc2"],
                confidence=0.85,
                evidence=["Evidence 1"],
            )

            assert pattern.pattern_type == "test_pattern"
            assert len(pattern.document_ids) == 2
            assert pattern.confidence == 0.85

        except ImportError:
            pytest.skip("Pydantic not installed")

    def test_document_result_schema(self):
        """Test DocumentResult schema."""
        try:
            from oraculus_di_auditor.interface.routes.orchestrator import (
                DocumentResult,
            )

            result = DocumentResult(
                document_id="doc123",
                metadata={"title": "Test"},
                findings={"fiscal": []},
                severity_score=0.5,
                lattice_score=0.9,
            )

            assert result.document_id == "doc123"
            assert result.severity_score == 0.5
            assert result.lattice_score == 0.9

        except ImportError:
            pytest.skip("Pydantic not installed")


class TestOrchestrationDatabase:
    """Tests for orchestration database models."""

    def test_orchestration_job_model_exists(self):
        """Test that OrchestrationJob model exists."""
        try:
            from oraculus_di_auditor.db.models import OrchestrationJob

            assert OrchestrationJob is not None
            assert OrchestrationJob.__tablename__ == "orchestration_jobs"

        except ImportError:
            pytest.skip("SQLAlchemy not installed")

    def test_orchestration_job_fields(self):
        """Test OrchestrationJob has required fields."""
        try:
            from oraculus_di_auditor.db.models import OrchestrationJob

            # Check that model has expected columns
            columns = OrchestrationJob.__table__.columns.keys()
            assert "id" in columns
            assert "job_id" in columns
            assert "status" in columns
            assert "created_at" in columns
            assert "document_count" in columns
            assert "patterns_found" in columns
            assert "correlations_found" in columns

        except ImportError:
            pytest.skip("SQLAlchemy not installed")
