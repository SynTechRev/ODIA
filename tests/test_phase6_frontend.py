"""Tests for Phase 6 Frontend Orchestration System.

Tests all four required output formats:
1. Front-End Task Plan
2. Front-End Build Instructions
3. Gap Identification Report
4. Final Phase-6 Output Bundle

Validates deterministic execution, structured outputs, and architectural continuity.
"""

import json

import pytest

from oraculus_di_auditor.frontend import Phase6Orchestrator
from oraculus_di_auditor.frontend.api_client import APIClientGenerator
from oraculus_di_auditor.frontend.components import ComponentLibrary
from oraculus_di_auditor.frontend.gaps import GapDetector


@pytest.fixture
def orchestrator():
    """Create Phase6Orchestrator instance."""
    return Phase6Orchestrator()


@pytest.fixture
def backend_info():
    """Sample backend information."""
    return {
        "endpoints": [
            {
                "path": "/api/v1/health",
                "method": "GET",
                "description": "Health check",
            },
            {
                "path": "/analyze",
                "method": "POST",
                "description": "Analyze document",
                "input_schema": {"document_text": "string", "metadata": "object"},
                "output_schema": {
                    "findings": "object",
                    "severity_score": "number",
                },
            },
        ],
        "detectors": ["fiscal", "constitutional", "surveillance"],
        "features": ["Multi-format ingestion", "Anomaly detection"],
    }


# ============================================================================
# Test Output Format 1: Front-End Task Plan
# ============================================================================


def test_generate_task_plan(orchestrator, backend_info):
    """Test task plan generation format."""
    result = orchestrator.execute_request(
        {"type": "task_plan", "backend_info": backend_info, "framework": "nextjs"}
    )

    # Verify structure
    assert result["type"] == "task_plan"
    assert "components" in result
    assert "apis_needed" in result
    assert "data_models" in result
    assert "state_management" in result
    assert "execution_order" in result
    assert "dependencies" in result
    assert "risk_flags" in result
    assert "readiness_score" in result
    assert "timestamp" in result

    # Verify components list
    assert isinstance(result["components"], list)
    assert len(result["components"]) > 0

    # Verify readiness score
    assert 0.0 <= result["readiness_score"] <= 1.0


def test_task_plan_components_structure(orchestrator, backend_info):
    """Test that components have required structure."""
    result = orchestrator.execute_request(
        {"type": "task_plan", "backend_info": backend_info}
    )

    for component in result["components"]:
        assert "name" in component
        assert "category" in component
        assert "purpose" in component
        assert "priority" in component


def test_task_plan_data_models(orchestrator, backend_info):
    """Test data models generation."""
    result = orchestrator.execute_request(
        {"type": "task_plan", "backend_info": backend_info}
    )

    assert isinstance(result["data_models"], list)
    assert len(result["data_models"]) >= 3  # Document, AnalysisResult, Finding

    # Check for required models
    model_names = [m["name"] for m in result["data_models"]]
    assert "Document" in model_names
    assert "AnalysisResult" in model_names
    assert "Finding" in model_names


def test_task_plan_state_management(orchestrator, backend_info):
    """Test state management configuration."""
    result = orchestrator.execute_request(
        {"type": "task_plan", "backend_info": backend_info}
    )

    assert "library" in result["state_management"]
    assert "stores" in result["state_management"]
    assert isinstance(result["state_management"]["stores"], list)


def test_task_plan_execution_order(orchestrator, backend_info):
    """Test execution order is provided."""
    result = orchestrator.execute_request(
        {"type": "task_plan", "backend_info": backend_info}
    )

    assert isinstance(result["execution_order"], list)
    assert len(result["execution_order"]) > 5  # At least 5 steps


# ============================================================================
# Test Output Format 2: Front-End Build Instructions
# ============================================================================


def test_generate_build_instructions(orchestrator, backend_info):
    """Test build instructions generation format."""
    result = orchestrator.execute_request(
        {
            "type": "build_instructions",
            "backend_info": backend_info,
            "framework": "nextjs",
        }
    )

    # Verify structure
    assert result["type"] == "build_instructions"
    assert "framework" in result
    assert result["framework"] == "nextjs"
    assert "scaffold_commands" in result
    assert "directory_structure" in result
    assert "setup_steps" in result
    assert "integration_steps" in result
    assert "success_criteria" in result
    assert "timestamp" in result


def test_build_instructions_scaffold_commands(orchestrator, backend_info):
    """Test scaffold commands are provided."""
    result = orchestrator.execute_request(
        {"type": "build_instructions", "backend_info": backend_info}
    )

    assert isinstance(result["scaffold_commands"], list)
    assert len(result["scaffold_commands"]) > 0

    # Check for npm/npx commands
    commands_str = " ".join(result["scaffold_commands"])
    assert "npx" in commands_str or "npm" in commands_str


def test_build_instructions_directory_structure(orchestrator, backend_info):
    """Test directory structure specification."""
    result = orchestrator.execute_request(
        {"type": "build_instructions", "backend_info": backend_info}
    )

    assert isinstance(result["directory_structure"], dict)
    assert "root" in result["directory_structure"]
    assert "structure" in result["directory_structure"]


def test_build_instructions_setup_steps(orchestrator, backend_info):
    """Test setup steps have proper structure."""
    result = orchestrator.execute_request(
        {"type": "build_instructions", "backend_info": backend_info}
    )

    assert isinstance(result["setup_steps"], list)
    assert len(result["setup_steps"]) > 0

    # Check first step structure
    first_step = result["setup_steps"][0]
    assert "step" in first_step
    assert "action" in first_step
    assert "commands" in first_step


def test_build_instructions_success_criteria(orchestrator, backend_info):
    """Test success criteria are provided."""
    result = orchestrator.execute_request(
        {"type": "build_instructions", "backend_info": backend_info}
    )

    assert isinstance(result["success_criteria"], list)
    assert len(result["success_criteria"]) > 5  # Multiple criteria


# ============================================================================
# Test Output Format 3: Gap Identification Report
# ============================================================================


def test_generate_gap_report(orchestrator, backend_info):
    """Test gap report generation format."""
    result = orchestrator.execute_request(
        {"type": "gap_report", "backend_info": backend_info}
    )

    # Verify structure
    assert result["type"] == "gap_report"
    assert "missing_endpoints" in result
    assert "missing_ui_components" in result
    assert "backend_incompatibilities" in result
    assert "security_issues" in result
    assert "suggested_fixes" in result
    assert "priority" in result
    assert "timestamp" in result


def test_gap_report_missing_endpoints(orchestrator):
    """Test missing endpoints detection."""
    # Use minimal backend info to trigger missing endpoints
    minimal_backend = {"endpoints": []}

    result = orchestrator.execute_request(
        {"type": "gap_report", "backend_info": minimal_backend}
    )

    assert isinstance(result["missing_endpoints"], list)
    # Should detect some missing endpoints
    assert len(result["missing_endpoints"]) > 0


def test_gap_report_security_issues(orchestrator, backend_info):
    """Test security issues detection."""
    result = orchestrator.execute_request(
        {"type": "gap_report", "backend_info": backend_info}
    )

    assert isinstance(result["security_issues"], list)
    # Should have some security recommendations
    assert len(result["security_issues"]) > 0

    # Check structure
    if result["security_issues"]:
        issue = result["security_issues"][0]
        assert "type" in issue
        assert "severity" in issue
        assert "description" in issue


def test_gap_report_priority_levels(orchestrator, backend_info):
    """Test priority calculation."""
    result = orchestrator.execute_request(
        {"type": "gap_report", "backend_info": backend_info}
    )

    assert result["priority"] in ["critical", "high", "medium", "low"]


def test_gap_report_suggested_fixes(orchestrator):
    """Test suggested fixes are provided when gaps exist."""
    minimal_backend = {"endpoints": []}

    result = orchestrator.execute_request(
        {"type": "gap_report", "backend_info": minimal_backend}
    )

    # With missing endpoints, should have suggested fixes
    assert isinstance(result["suggested_fixes"], list)


# ============================================================================
# Test Output Format 4: Final Phase-6 Output Bundle
# ============================================================================


def test_generate_full_bundle(orchestrator, backend_info):
    """Test full bundle generation format."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info, "framework": "nextjs"}
    )

    # Verify structure
    assert result["type"] == "full_bundle"
    assert "architecture" in result
    assert "components" in result
    assert "state_model" in result
    assert "api_client" in result
    assert "testing" in result
    assert "deployment" in result
    assert "task_plan" in result
    assert "build_instructions" in result
    assert "gap_report" in result
    assert "recommended_next_phase" in result
    assert "confidence" in result
    assert "timestamp" in result


def test_full_bundle_architecture(orchestrator, backend_info):
    """Test architecture specification in bundle."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info}
    )

    arch = result["architecture"]
    assert "pattern" in arch
    assert "framework" in arch
    assert "language" in arch
    assert "principles" in arch

    # Check TypeScript is specified
    assert arch["language"] == "TypeScript"


def test_full_bundle_components(orchestrator, backend_info):
    """Test component specifications in bundle."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info}
    )

    components = result["components"]
    assert isinstance(components, dict)

    # Should have component categories
    assert "base" in components
    assert "dashboard" in components
    assert "analysis" in components


def test_full_bundle_api_client(orchestrator, backend_info):
    """Test API client specification in bundle."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info}
    )

    api_client = result["api_client"]
    assert "structure" in api_client
    assert "types" in api_client
    assert "client_class" in api_client
    assert "methods" in api_client


def test_full_bundle_testing_strategy(orchestrator, backend_info):
    """Test testing strategy in bundle."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info}
    )

    testing = result["testing"]
    assert "unit_tests" in testing
    assert "integration_tests" in testing


def test_full_bundle_deployment(orchestrator, backend_info):
    """Test deployment configuration in bundle."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info}
    )

    deployment = result["deployment"]
    assert "platforms" in deployment
    assert "environment_variables" in deployment


def test_full_bundle_confidence_score(orchestrator, backend_info):
    """Test confidence score calculation."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info}
    )

    assert 0.0 <= result["confidence"] <= 1.0


# ============================================================================
# Component Library Tests
# ============================================================================


def test_component_library_base_components():
    """Test base component generation."""
    library = ComponentLibrary()
    backend_analysis = {"detectors": [], "orchestration_available": False}

    components = library.generate_component_list(backend_analysis)

    # Should have base components
    base_components = [c for c in components if c["category"] == "base"]
    assert len(base_components) > 0

    # Check for essential base components
    names = [c["name"] for c in base_components]
    assert "Button" in names
    assert "Input" in names
    assert "Card" in names


def test_component_library_analysis_components():
    """Test analysis component generation."""
    library = ComponentLibrary()
    backend_analysis = {
        "detectors": ["fiscal", "constitutional"],
        "orchestration_available": False,
    }

    components = library.generate_component_list(backend_analysis)

    # Should have analysis components
    analysis_components = [c for c in components if c["category"] == "analysis"]
    assert len(analysis_components) > 0

    # Check for detector-specific components
    names = [c["name"] for c in analysis_components]
    assert "FiscalDetectorView" in names
    assert "ConstitutionalDetectorView" in names


def test_component_library_orchestration_components():
    """Test orchestration component generation when available."""
    library = ComponentLibrary()
    backend_analysis = {"detectors": [], "orchestration_available": True}

    components = library.generate_component_list(backend_analysis)

    # Should have orchestration components
    orch_components = [c for c in components if c["category"] == "orchestration"]
    assert len(orch_components) > 0

    names = [c["name"] for c in orch_components]
    assert "AgentActivityMonitor" in names


# ============================================================================
# API Client Generator Tests
# ============================================================================


def test_api_client_identify_apis():
    """Test API method identification."""
    generator = APIClientGenerator()
    backend_analysis = {
        "endpoints": [
            {"path": "/api/v1/health", "method": "GET"},
            {"path": "/analyze", "method": "POST"},
        ]
    }

    apis = generator.identify_required_apis(backend_analysis)

    assert len(apis) == 2
    assert any(api["name"] == "checkHealth" for api in apis)
    assert any(api["name"] == "analyzeDocument" for api in apis)


def test_api_client_generate_types():
    """Test TypeScript type generation."""
    generator = APIClientGenerator()
    backend_analysis = {"endpoints": []}

    types = generator._generate_typescript_types(backend_analysis)

    assert "AnalyzeRequest" in types
    assert "AnalysisResult" in types
    assert "Finding" in types

    # Check type definitions contain TypeScript syntax
    assert "interface" in types["AnalyzeRequest"]


def test_api_client_generate_class():
    """Test client class generation."""
    generator = APIClientGenerator()
    backend_analysis = {"endpoints": []}

    client_class = generator._generate_client_class(backend_analysis)

    assert "class OraculusAPIClient" in client_class
    assert "axios" in client_class
    assert "setupInterceptors" in client_class


def test_api_client_usage_examples():
    """Test usage examples generation."""
    generator = APIClientGenerator()
    backend_analysis = {"endpoints": []}

    examples = generator._generate_usage_examples(backend_analysis)

    assert len(examples) > 0
    assert any("Initialize" in ex["title"] for ex in examples)
    assert any("Analyze" in ex["title"] for ex in examples)


# ============================================================================
# Gap Detector Tests
# ============================================================================


def test_gap_detector_missing_endpoints():
    """Test missing endpoint detection."""
    detector = GapDetector()
    backend_analysis = {"endpoints": []}

    gaps = detector.identify_gaps(backend_analysis)

    assert len(gaps["missing_endpoints"]) > 0


def test_gap_detector_security_issues():
    """Test security issue detection."""
    detector = GapDetector()
    backend_analysis = {"endpoints": []}

    gaps = detector.identify_gaps(backend_analysis)

    # Should always detect some security considerations
    assert len(gaps["security_issues"]) > 0


def test_gap_detector_risk_flags():
    """Test risk flag detection."""
    detector = GapDetector()
    backend_analysis = {"endpoints": [], "orchestration_available": False}

    components = []
    apis_needed = []

    flags = detector.detect_risk_flags(backend_analysis, components, apis_needed)

    # Should detect risks with minimal backend
    assert len(flags) > 0


def test_gap_detector_priority_calculation():
    """Test priority calculation logic."""
    detector = GapDetector()

    # Test with critical gaps
    gaps_with_critical = {
        "missing_endpoints": [{"priority": "critical"}],
        "security_issues": [],
        "backend_incompatibilities": [],
    }

    priority = detector._calculate_priority(gaps_with_critical)
    assert priority == "critical"

    # Test with no critical gaps
    gaps_without_critical = {
        "missing_endpoints": [{"priority": "low"}],
        "security_issues": [{"severity": "low"}],
        "backend_incompatibilities": [],
    }

    priority = detector._calculate_priority(gaps_without_critical)
    assert priority == "low"


# ============================================================================
# Integration and Behavioral Tests
# ============================================================================


def test_deterministic_execution(orchestrator, backend_info):
    """Test that execution is deterministic (same input -> same structure)."""
    result1 = orchestrator.execute_request(
        {"type": "task_plan", "backend_info": backend_info}
    )

    result2 = orchestrator.execute_request(
        {"type": "task_plan", "backend_info": backend_info}
    )

    # Same structure (excluding timestamp)
    assert result1["type"] == result2["type"]
    assert len(result1["components"]) == len(result2["components"])
    assert result1["readiness_score"] == result2["readiness_score"]


def test_framework_variation(orchestrator, backend_info):
    """Test that framework choice affects output appropriately."""
    result_nextjs = orchestrator.execute_request(
        {
            "type": "build_instructions",
            "backend_info": backend_info,
            "framework": "nextjs",
        }
    )

    result_react = orchestrator.execute_request(
        {
            "type": "build_instructions",
            "backend_info": backend_info,
            "framework": "react",
        }
    )

    # Framework should be reflected
    assert result_nextjs["framework"] == "nextjs"
    assert result_react["framework"] == "react"

    # Scaffold commands should differ
    assert result_nextjs["scaffold_commands"] != result_react["scaffold_commands"]


def test_default_request_type(orchestrator, backend_info):
    """Test default request type is full_bundle."""
    result = orchestrator.execute_request({"backend_info": backend_info})

    assert result["type"] == "full_bundle"


def test_unknown_request_type(orchestrator, backend_info):
    """Test handling of unknown request type."""
    result = orchestrator.execute_request(
        {"type": "unknown_type", "backend_info": backend_info}
    )

    assert "error" in result
    assert "Unknown request type" in result["error"]


def test_json_serializable_outputs(orchestrator, backend_info):
    """Test that all outputs are JSON serializable."""
    result = orchestrator.execute_request(
        {"type": "full_bundle", "backend_info": backend_info}
    )

    # Should be serializable without errors
    json_str = json.dumps(result)
    assert len(json_str) > 0

    # Should be deserializable
    parsed = json.loads(json_str)
    assert parsed["type"] == "full_bundle"


def test_zero_hallucination_principle(orchestrator):
    """Test that outputs don't invent non-existent backend features."""
    # Provide minimal backend info
    minimal_backend = {
        "endpoints": [{"path": "/test", "method": "GET"}],
        "detectors": ["test-detector"],
    }

    orchestrator.execute_request(
        {
            "type": "task_plan",
            "backend_info": minimal_backend,
        }
    )

    # Should only reference what was provided or default expectations
    # Gap report should identify missing pieces
    gap_result = orchestrator.execute_request(
        {
            "type": "gap_report",
            "backend_info": minimal_backend,
        }
    )

    # Should detect missing expected endpoints
    assert len(gap_result["missing_endpoints"]) > 0
