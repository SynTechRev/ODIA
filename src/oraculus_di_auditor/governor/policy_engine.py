"""Policy Engine for Phase 9 Governor.

Implements deterministic rule-based governance with version-controlled policies,
execution constraints, and compliance reporting.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Engine for enforcing governance policies and rules.

    Provides:
    - Deterministic rule evaluation
    - Version-controlled policies
    - Execution constraints
    - Required field validation
    - Severity threshold enforcement
    - Compliance reporting
    """

    def __init__(self):
        """Initialize policy engine."""
        self.policies = self._load_default_policies()
        self.policy_version = "1.0.0"

    def _load_default_policies(self) -> dict[str, Any]:
        """Load default governance policies.

        Returns:
            Dictionary of policies
        """
        return {
            "document_policies": {
                "min_document_length": {
                    "value": 10,
                    "description": "Minimum document length in characters",
                    "severity": "error",
                    "enabled": True,
                },
                "max_document_length": {
                    "value": 10_000_000,
                    "description": "Maximum document length in characters",
                    "severity": "error",
                    "enabled": True,
                },
                "require_metadata": {
                    "value": True,
                    "description": "Documents must include metadata",
                    "severity": "warning",
                    "enabled": True,
                },
            },
            "orchestrator_policies": {
                "max_documents_per_job": {
                    "value": 100,
                    "description": "Maximum documents in single orchestration job",
                    "severity": "error",
                    "enabled": True,
                },
                "min_documents_per_job": {
                    "value": 1,
                    "description": "Minimum documents in orchestration job",
                    "severity": "error",
                    "enabled": True,
                },
                "require_cross_document_analysis": {
                    "value": True,
                    "description": "Enable cross-document pattern analysis",
                    "severity": "warning",
                    "enabled": True,
                },
            },
            "security_policies": {
                "max_threat_score": {
                    "value": 0.5,
                    "description": "Maximum allowed threat score",
                    "severity": "critical",
                    "enabled": True,
                },
                "require_provenance": {
                    "value": True,
                    "description": "Documents must have provenance metadata",
                    "severity": "warning",
                    "enabled": True,
                },
                "block_suspicious_patterns": {
                    "value": True,
                    "description": "Block documents with detected threat patterns",
                    "severity": "critical",
                    "enabled": True,
                },
            },
            "analysis_policies": {
                "max_severity_threshold": {
                    "value": 0.9,
                    "description": "Severity threshold for escalation",
                    "severity": "high",
                    "enabled": True,
                },
                "require_all_agents": {
                    "value": True,
                    "description": "All analysis agents must be available",
                    "severity": "error",
                    "enabled": True,
                },
                "min_confidence_score": {
                    "value": 0.5,
                    "description": "Minimum confidence score for findings",
                    "severity": "warning",
                    "enabled": True,
                },
            },
        }

    def evaluate_document_policies(
        self, document_text: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate policies for a single document.

        Args:
            document_text: Document text
            metadata: Document metadata

        Returns:
            Policy evaluation result
        """
        result = {
            "status": "compliant",
            "violations": [],
            "warnings": [],
            "policies_evaluated": [],
        }

        policies = self.policies["document_policies"]

        # Check minimum length
        min_length_policy = policies["min_document_length"]
        if min_length_policy["enabled"]:
            result["policies_evaluated"].append("min_document_length")
            if len(document_text) < min_length_policy["value"]:
                violation = {
                    "policy": "min_document_length",
                    "description": min_length_policy["description"],
                    "severity": min_length_policy["severity"],
                    "actual_value": len(document_text),
                    "expected_value": min_length_policy["value"],
                }
                if min_length_policy["severity"] == "error":
                    result["violations"].append(violation)
                    result["status"] = "non_compliant"
                else:
                    result["warnings"].append(violation)

        # Check maximum length
        max_length_policy = policies["max_document_length"]
        if max_length_policy["enabled"]:
            result["policies_evaluated"].append("max_document_length")
            if len(document_text) > max_length_policy["value"]:
                violation = {
                    "policy": "max_document_length",
                    "description": max_length_policy["description"],
                    "severity": max_length_policy["severity"],
                    "actual_value": len(document_text),
                    "expected_value": max_length_policy["value"],
                }
                if max_length_policy["severity"] == "error":
                    result["violations"].append(violation)
                    result["status"] = "non_compliant"
                else:
                    result["warnings"].append(violation)
        # Check metadata requirement
        metadata_policy = policies["require_metadata"]
        if metadata_policy["enabled"]:
            result["policies_evaluated"].append("require_metadata")
            if not metadata or len(metadata) == 0:
                violation = {
                    "policy": "require_metadata",
                    "description": metadata_policy["description"],
                    "severity": metadata_policy["severity"],
                }
                if metadata_policy["severity"] == "error":
                    result["violations"].append(violation)
                    result["status"] = "non_compliant"
                else:
                    result["warnings"].append(violation)

        return result

    def evaluate_orchestrator_policies(self, document_count: int) -> dict[str, Any]:
        """Evaluate policies for orchestrator jobs.

        Args:
            document_count: Number of documents in job

        Returns:
            Policy evaluation result
        """
        result = {
            "status": "compliant",
            "violations": [],
            "warnings": [],
            "policies_evaluated": [],
        }

        policies = self.policies["orchestrator_policies"]

        # Check minimum documents
        min_docs_policy = policies["min_documents_per_job"]
        if min_docs_policy["enabled"]:
            result["policies_evaluated"].append("min_documents_per_job")
            if document_count < min_docs_policy["value"]:
                result["violations"].append(
                    {
                        "policy": "min_documents_per_job",
                        "description": min_docs_policy["description"],
                        "severity": min_docs_policy["severity"],
                        "actual_value": document_count,
                        "expected_value": min_docs_policy["value"],
                    }
                )
                result["status"] = "non_compliant"

        # Check maximum documents
        max_docs_policy = policies["max_documents_per_job"]
        if max_docs_policy["enabled"]:
            result["policies_evaluated"].append("max_documents_per_job")
            if document_count > max_docs_policy["value"]:
                result["violations"].append(
                    {
                        "policy": "max_documents_per_job",
                        "description": max_docs_policy["description"],
                        "severity": max_docs_policy["severity"],
                        "actual_value": document_count,
                        "expected_value": max_docs_policy["value"],
                    }
                )
                result["status"] = "non_compliant"

        return result

    def evaluate_security_policies(
        self, threat_score: float, has_provenance: bool
    ) -> dict[str, Any]:
        """Evaluate security policies.

        Args:
            threat_score: Calculated threat score
            has_provenance: Whether document has provenance

        Returns:
            Policy evaluation result
        """
        result = {
            "status": "compliant",
            "violations": [],
            "warnings": [],
            "policies_evaluated": [],
        }

        policies = self.policies["security_policies"]

        # Check threat score
        threat_policy = policies["max_threat_score"]
        if threat_policy["enabled"]:
            result["policies_evaluated"].append("max_threat_score")
            if threat_score > threat_policy["value"]:
                result["violations"].append(
                    {
                        "policy": "max_threat_score",
                        "description": threat_policy["description"],
                        "severity": threat_policy["severity"],
                        "actual_value": threat_score,
                        "expected_value": threat_policy["value"],
                    }
                )
                result["status"] = "non_compliant"

        # Check provenance
        provenance_policy = policies["require_provenance"]
        if provenance_policy["enabled"]:
            result["policies_evaluated"].append("require_provenance")
            if not has_provenance:
                violation = {
                    "policy": "require_provenance",
                    "description": provenance_policy["description"],
                    "severity": provenance_policy["severity"],
                }
                if provenance_policy["severity"] == "error":
                    result["violations"].append(violation)
                    result["status"] = "non_compliant"
                else:
                    result["warnings"].append(violation)

        return result

    def generate_compliance_report(
        self, evaluation_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate compliance report from evaluation results.

        Args:
            evaluation_results: List of policy evaluation results

        Returns:
            Compliance report
        """
        logger.debug("Generating compliance report")

        report = {
            "timestamp": self._get_timestamp(),
            "policy_version": self.policy_version,
            "overall_compliance": "compliant",
            "total_evaluations": len(evaluation_results),
            "compliant_count": 0,
            "non_compliant_count": 0,
            "total_violations": 0,
            "total_warnings": 0,
            "violations_by_severity": {},
            "recommendations": [],
        }

        # Aggregate results
        for eval_result in evaluation_results:
            if eval_result.get("status") == "compliant":
                report["compliant_count"] += 1
            else:
                report["non_compliant_count"] += 1

            # Count violations and warnings
            violations = eval_result.get("violations", [])
            warnings = eval_result.get("warnings", [])

            report["total_violations"] += len(violations)
            report["total_warnings"] += len(warnings)

            # Group by severity
            for violation in violations:
                severity = violation.get("severity", "unknown")
                report["violations_by_severity"][severity] = (
                    report["violations_by_severity"].get(severity, 0) + 1
                )

        # Determine overall compliance
        if report["non_compliant_count"] > 0:
            report["overall_compliance"] = "non_compliant"

        # Generate recommendations
        if report["total_violations"] > 0:
            report["recommendations"].append(
                "Review and address all policy violations before proceeding"
            )
        if report["total_warnings"] > 0:
            report["recommendations"].append(
                "Consider addressing warnings to improve compliance"
            )

        logger.debug(f"Compliance report: {report['overall_compliance']}")

        return report

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat()


__all__ = ["PolicyEngine"]
