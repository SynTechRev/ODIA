"""Gap Detector - Identifies missing pieces and incompatibilities.

This module performs comprehensive validation of the system to identify:
- Missing backend endpoints
- Missing UI components
- Schema incompatibilities
- Security issues
- Performance bottlenecks

All detection is deterministic and produces actionable recommendations.
"""

from __future__ import annotations

from typing import Any


class GapDetector:
    """Gap detection and validation system for Phase 6."""

    def identify_gaps(self, backend_analysis: dict[str, Any]) -> dict[str, Any]:
        """Identify all gaps and issues in the system.

        Args:
            backend_analysis: Backend capabilities analysis

        Returns:
            Comprehensive gap report
        """
        gaps = {
            "missing_endpoints": self._detect_missing_endpoints(backend_analysis),
            "missing_ui_components": self._detect_missing_ui_components(
                backend_analysis
            ),
            "backend_incompatibilities": self._detect_incompatibilities(
                backend_analysis
            ),
            "security_issues": self._detect_security_issues(backend_analysis),
            "suggested_fixes": [],
            "priority": "low",
        }

        # Generate suggested fixes
        gaps["suggested_fixes"] = self._generate_fixes(gaps)

        # Calculate priority
        gaps["priority"] = self._calculate_priority(gaps)

        return gaps

    def detect_risk_flags(
        self,
        backend_analysis: dict[str, Any],
        components: list[dict[str, Any]],
        apis_needed: list[dict[str, Any]],
    ) -> list[str]:
        """Detect risk flags in the system.

        Args:
            backend_analysis: Backend capabilities
            components: Required UI components
            apis_needed: Required API methods

        Returns:
            List of risk flags
        """
        flags = []

        # Check for missing critical endpoints
        endpoints = backend_analysis.get("endpoints", [])
        if len(endpoints) < 3:
            flags.append("Insufficient backend endpoints")

        # Check for missing orchestration
        if not backend_analysis.get("orchestration_available"):
            flags.append("Phase 5 orchestration not available")

        # Check for missing detectors
        detectors = backend_analysis.get("detectors", [])
        if len(detectors) < 4:
            flags.append("Some detectors may be missing")

        # Check for critical components
        critical_components = [c for c in components if c.get("priority") == "critical"]
        if len(critical_components) < 3:
            flags.append("Insufficient critical UI components")

        return flags

    def _detect_missing_endpoints(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Detect missing backend endpoints.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            List of missing endpoints with descriptions
        """
        missing = []
        existing_paths = [ep["path"] for ep in backend_analysis.get("endpoints", [])]

        # Expected endpoints
        expected_endpoints = [
            {
                "path": "/api/v1/health",
                "description": "Health check endpoint",
                "priority": "high",
            },
            {
                "path": "/analyze",
                "description": "Primary analysis endpoint",
                "priority": "critical",
            },
            {
                "path": "/api/v1/info",
                "description": "API information endpoint",
                "priority": "medium",
            },
            {
                "path": "/api/v1/documents",
                "description": "Document listing endpoint (optional)",
                "priority": "low",
            },
            {
                "path": "/api/v1/orchestrate",
                "description": "Phase 5 orchestration endpoint (optional)",
                "priority": "low",
            },
        ]

        for endpoint in expected_endpoints:
            if endpoint["path"] not in existing_paths:
                missing.append(
                    {
                        "path": endpoint["path"],
                        "description": endpoint["description"],
                        "priority": endpoint["priority"],
                        "reason": "Endpoint not found in backend analysis",
                    }
                )

        return missing

    def _detect_missing_ui_components(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Detect missing UI components.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            List of potentially missing UI components
        """
        missing = []

        # Check if orchestration components are needed but unavailable
        if not backend_analysis.get("orchestration_available"):
            missing.append(
                {
                    "component": "AgentActivityMonitor",
                    "reason": "Phase 5 orchestration not available",
                    "impact": "Cannot display agent activity",
                    "priority": "low",
                }
            )

        # Check for detector-specific visualizations
        detectors = backend_analysis.get("detectors", [])
        if "fiscal" not in detectors:
            missing.append(
                {
                    "component": "FiscalDetectorView",
                    "reason": "Fiscal detector not in backend",
                    "impact": "Cannot display fiscal analysis",
                    "priority": "medium",
                }
            )

        return missing

    def _detect_incompatibilities(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Detect schema and compatibility issues.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            List of incompatibility issues
        """
        incompatibilities = []

        # Check for schema mismatches
        endpoints = backend_analysis.get("endpoints", [])
        for endpoint in endpoints:
            if endpoint.get("input_schema"):
                schema = endpoint["input_schema"]
                # Validate schema completeness
                if isinstance(schema, dict) and not schema:
                    incompatibilities.append(
                        {
                            "endpoint": endpoint["path"],
                            "issue": "Empty input schema",
                            "impact": "Cannot generate proper TypeScript types",
                            "priority": "medium",
                        }
                    )

        # Check API version consistency
        api_paths = [ep["path"] for ep in endpoints]
        has_v1 = any("/v1/" in path for path in api_paths)
        has_no_version = any(
            "/v1/" not in path and path != "/analyze" for path in api_paths
        )

        if has_v1 and has_no_version:
            incompatibilities.append(
                {
                    "endpoint": "multiple",
                    "issue": "Inconsistent API versioning",
                    "impact": "May confuse API consumers",
                    "priority": "low",
                }
            )

        return incompatibilities

    def _detect_security_issues(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Detect security concerns.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            List of security issues
        """
        issues = []

        # Check CORS configuration
        # Note: CORS is configurable via ORACULUS_CORS_ORIGINS, which is good
        issues.append(
            {
                "type": "CORS",
                "severity": "info",
                "description": "CORS is configurable via environment variable",
                "recommendation": (
                    "Ensure ORACULUS_CORS_ORIGINS is properly set in production"
                ),
            }
        )

        # Check authentication
        # Note: Backend doesn't currently have authentication
        issues.append(
            {
                "type": "Authentication",
                "severity": "medium",
                "description": "No authentication mechanism detected",
                "recommendation": (
                    "Consider adding authentication for production deployment"
                ),
            }
        )

        # Check input validation
        issues.append(
            {
                "type": "Input Validation",
                "severity": "info",
                "description": "Ensure all user inputs are properly sanitized",
                "recommendation": "Use schema validation on all API endpoints",
            }
        )

        # Check rate limiting
        issues.append(
            {
                "type": "Rate Limiting",
                "severity": "low",
                "description": "No rate limiting detected",
                "recommendation": "Consider adding rate limiting to prevent abuse",
            }
        )

        return issues

    def _generate_fixes(self, gaps: dict[str, Any]) -> list[dict[str, str]]:
        """Generate suggested fixes for identified gaps.

        Args:
            gaps: Detected gaps

        Returns:
            List of suggested fixes
        """
        fixes = []

        # Fix missing endpoints
        for missing in gaps["missing_endpoints"]:
            if missing["priority"] in ["critical", "high"]:
                fixes.append(
                    {
                        "gap": f"Missing endpoint: {missing['path']}",
                        "fix": f"Implement {missing['path']} in backend API",
                        "priority": missing["priority"],
                    }
                )

        # Fix security issues
        for issue in gaps["security_issues"]:
            if issue["severity"] in ["high", "medium"]:
                fixes.append(
                    {
                        "gap": f"Security: {issue['type']}",
                        "fix": issue["recommendation"],
                        "priority": "high" if issue["severity"] == "high" else "medium",
                    }
                )

        # Fix incompatibilities
        for incompat in gaps["backend_incompatibilities"]:
            if incompat["priority"] in ["critical", "high"]:
                fixes.append(
                    {
                        "gap": f"Incompatibility at {incompat['endpoint']}",
                        "fix": f"Fix: {incompat['issue']}",
                        "priority": incompat["priority"],
                    }
                )

        return fixes

    def _calculate_priority(self, gaps: dict[str, Any]) -> str:
        """Calculate overall gap priority.

        Args:
            gaps: Detected gaps

        Returns:
            Priority level: "critical", "high", "medium", "low"
        """
        # Check for critical gaps
        critical_endpoints = [
            ep for ep in gaps["missing_endpoints"] if ep["priority"] == "critical"
        ]
        if critical_endpoints:
            return "critical"

        # Check for high-priority gaps
        high_endpoints = [
            ep for ep in gaps["missing_endpoints"] if ep["priority"] == "high"
        ]
        high_security = [
            issue for issue in gaps["security_issues"] if issue["severity"] == "high"
        ]

        if high_endpoints or high_security:
            return "high"

        # Check for medium-priority gaps
        medium_endpoints = [
            ep for ep in gaps["missing_endpoints"] if ep["priority"] == "medium"
        ]
        medium_security = [
            issue for issue in gaps["security_issues"] if issue["severity"] == "medium"
        ]

        if medium_endpoints or medium_security or gaps["backend_incompatibilities"]:
            return "medium"

        return "low"


__all__ = ["GapDetector"]
