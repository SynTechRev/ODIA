"""Governor Service for Phase 9.

Main service coordinating validation, security, and policy enforcement.
"""

from __future__ import annotations

import logging
from typing import Any

from .policy_engine import PolicyEngine
from .security_gatekeeper import SecurityGatekeeper
from .validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class GovernorService:
    """Central service for pipeline governance and compliance.

    Coordinates:
    - Pipeline validation
    - Security enforcement
    - Policy compliance
    - System health monitoring
    """

    def __init__(self):
        """Initialize governor service."""
        self.validation_engine = ValidationEngine()
        self.security_gatekeeper = SecurityGatekeeper()
        self.policy_engine = PolicyEngine()
        logger.info("Governor service initialized")

    def get_system_state(self) -> dict[str, Any]:
        """Get current system health and readiness state.

        Returns:
            System state summary
        """
        logger.info("Getting system state")

        # Run quick validation checks
        validation_result = self.validation_engine.run_full_validation()

        # Generate state summary
        state = {
            "timestamp": self._get_timestamp(),
            "overall_health": validation_result["overall_status"],
            "governor_version": "1.0.0",
            "validation_summary": {
                "schemas_valid": validation_result["checks"]["schemas"]["status"]
                == "success",
                "agents_available": len(
                    validation_result["checks"]["agents"]["agents_available"]
                ),
                "database_ready": validation_result["checks"]["database"]["status"]
                == "success",
                "orchestrator_ready": validation_result["checks"]["orchestrator"].get(
                    "orchestrator_ready", False
                ),
            },
            "policy_version": self.policy_engine.policy_version,
            "security_posture": "active",
            "compliance_status": "monitoring",
        }

        logger.info(f"System state: {state['overall_health']}")
        return state

    def validate_pipeline(self, deep: bool = False) -> dict[str, Any]:
        """Validate pipeline components and readiness.

        Args:
            deep: Whether to run deep validation (slower but more thorough)

        Returns:
            Validation report
        """
        logger.info(f"Running pipeline validation (deep={deep})")

        if deep:
            # Run full validation
            validation_result = self.validation_engine.run_full_validation()
        else:
            # Run quick checks only
            validation_result = {
                "timestamp": self._get_timestamp(),
                "overall_status": "success",
                "checks": {
                    "agents": self.validation_engine.validate_agents(),
                    "orchestrator": (
                        self.validation_engine.validate_orchestrator_readiness()
                    ),
                },
            }

        logger.info(f"Pipeline validation: {validation_result['overall_status']}")
        return validation_result

    def enforce_policies(
        self,
        document_text: str,
        metadata: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Enforce governance policies on a document.

        Args:
            document_text: Document text
            metadata: Document metadata
            options: Optional enforcement options

        Returns:
            Enforcement result with policy compliance and security profile
        """
        logger.info("Enforcing governance policies")

        if options is None:
            options = {}

        result = {
            "timestamp": self._get_timestamp(),
            "enforcement_status": "passed",
            "checks_performed": [],
            "violations": [],
            "warnings": [],
        }

        # 1. Security check
        logger.debug("Running security checks")
        security_profile = self.security_gatekeeper.generate_security_profile(
            document_text, metadata
        )
        result["checks_performed"].append("security_profile")
        result["security_profile"] = security_profile

        # Check if threats detected
        if security_profile["overall_status"] in ["critical", "error"]:
            result["enforcement_status"] = "blocked"
            result["violations"].append(
                {
                    "type": "security",
                    "severity": "critical",
                    "description": "Security threats detected in document",
                }
            )

        # 2. Document policy evaluation
        logger.debug("Evaluating document policies")
        doc_policy_result = self.policy_engine.evaluate_document_policies(
            document_text, metadata
        )
        result["checks_performed"].append("document_policies")
        result["document_policies"] = doc_policy_result

        # Add violations from policy evaluation
        if doc_policy_result["status"] == "non_compliant":
            result["enforcement_status"] = "blocked"
            result["violations"].extend(doc_policy_result["violations"])

        result["warnings"].extend(doc_policy_result.get("warnings", []))

        # 3. Security policy evaluation
        logger.debug("Evaluating security policies")
        # Check for provenance: require document_id and at least one of
        # source_path or expected_hash
        has_provenance = (
            "document_id" in metadata
            and metadata["document_id"] is not None
            and (
                ("source_path" in metadata and metadata["source_path"] is not None)
                or (
                    "expected_hash" in metadata
                    and metadata["expected_hash"] is not None
                )
            )
        )
        security_policy_result = self.policy_engine.evaluate_security_policies(
            threat_score=security_profile["threat_score"],
            has_provenance=has_provenance,
        )
        result["checks_performed"].append("security_policies")
        result["security_policies"] = security_policy_result

        if security_policy_result["status"] == "non_compliant":
            result["enforcement_status"] = "blocked"
            result["violations"].extend(security_policy_result["violations"])

        result["warnings"].extend(security_policy_result.get("warnings", []))

        # Generate final decision
        if result["enforcement_status"] == "blocked":
            logger.warning(
                "Policy enforcement blocked document: "
                f"{len(result['violations'])} violations"
            )
        else:
            logger.info("Policy enforcement passed")

        return result

    def validate_orchestrator_job(self, document_count: int) -> dict[str, Any]:
        """Validate an orchestrator job request.

        Args:
            document_count: Number of documents in job

        Returns:
            Validation result for orchestrator job
        """
        logger.info(f"Validating orchestrator job with {document_count} documents")
        result = {
            "timestamp": self._get_timestamp(),
            "validation_status": "passed",
            "checks_performed": [],
            "violations": [],
            "warnings": [],
        }

        # Evaluate orchestrator policies
        orch_policy_result = self.policy_engine.evaluate_orchestrator_policies(
            document_count
        )
        result["checks_performed"].append("orchestrator_policies")
        result["orchestrator_policies"] = orch_policy_result

        if orch_policy_result["status"] == "non_compliant":
            result["validation_status"] = "blocked"
            result["violations"].extend(orch_policy_result["violations"])

        result["warnings"].extend(orch_policy_result.get("warnings", []))

        logger.info(f"Orchestrator job validation: {result['validation_status']}")
        return result

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat()


__all__ = ["GovernorService"]
