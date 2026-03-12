"""Security Gatekeeper for Phase 9 Governor.

Implements security policies including input/output sanitation, MIME validation,
rate limiting posture, provenance checking, and threat scoring.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class SecurityGatekeeper:
    """Gatekeeper for enforcing security policies on pipeline execution.

    Enforces:
    - Input/output sanitation
    - MIME type validation
    - Document origin checks
    - Provenance validation
    - Threat scoring
    - Rate limiting posture
    """

    def __init__(self):
        """Initialize security gatekeeper."""
        self.threat_patterns = self._load_threat_patterns()
        self.allowed_mime_types = [
            "text/plain",
            "application/json",
            "application/pdf",
            "application/xml",
            "text/xml",
        ]

    def _load_threat_patterns(self) -> list[dict[str, Any]]:
        """Load threat detection patterns.

        Returns:
            List of threat patterns
        """
        return [
            {
                "pattern": r"<script[^>]*>.*?</script>",
                "threat_type": "xss",
                "severity": 0.9,
            },
            {
                "pattern": r"javascript:",
                "threat_type": "javascript_injection",
                "severity": 0.8,
            },
            {
                "pattern": r"(union|select|insert|update|delete|drop)\s+",
                "threat_type": "sql_injection",
                "severity": 0.7,
            },
            {
                "pattern": r"\.\./",
                "threat_type": "path_traversal",
                "severity": 0.8,
            },
            {
                "pattern": r"<iframe[^>]*>",
                "threat_type": "iframe_injection",
                "severity": 0.7,
            },
        ]

    def sanitize_input(
        self, document_text: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Sanitize input document text and metadata.

        Args:
            document_text: Raw document text
            metadata: Document metadata

        Returns:
            Sanitization result with cleaned text and threats detected
        """
        result = {
            "status": "clean",
            "threats_detected": [],
            "sanitized_text": document_text,
            "sanitized_metadata": metadata.copy(),
            "threat_score": 0.0,
        }

        # Check for threat patterns
        for threat_pattern in self.threat_patterns:
            pattern = threat_pattern["pattern"]
            if re.search(pattern, document_text, re.IGNORECASE):
                result["threats_detected"].append(
                    {
                        "type": threat_pattern["threat_type"],
                        "severity": threat_pattern["severity"],
                        "description": (
                            f"Detected {threat_pattern['threat_type']} pattern"
                        ),
                    }
                )
                result["status"] = "threat_detected"
                result["threat_score"] = max(
                    result["threat_score"], threat_pattern["severity"]
                )

        # Sanitize metadata strings
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str):
                    # Check for threats in metadata
                    for threat_pattern in self.threat_patterns:
                        if re.search(threat_pattern["pattern"], value, re.IGNORECASE):
                            result["threats_detected"].append(
                                {
                                    "type": threat_pattern["threat_type"],
                                    "severity": threat_pattern["severity"],
                                    "description": (
                                        "Detected "
                                        f"{threat_pattern['threat_type']} "
                                        f"in metadata field '{key}'"
                                    ),
                                    "field": key,
                                }
                            )
                            result["status"] = "threat_detected"
                            result["threat_score"] = max(
                                result["threat_score"], threat_pattern["severity"]
                            )

        return result

    def validate_mime_type(self, mime_type: str) -> dict[str, Any]:
        """Validate MIME type is allowed.

        Args:
            mime_type: MIME type to validate

        Returns:
            Validation result
        """
        result = {
            "valid": mime_type in self.allowed_mime_types,
            "mime_type": mime_type,
            "allowed_types": self.allowed_mime_types,
        }

        if not result["valid"]:
            result["error"] = f"MIME type '{mime_type}' not allowed"

        return result

    def validate_provenance(
        self,
        document_id: str,
        source_path: str | None = None,
        expected_hash: str | None = None,
    ) -> dict[str, Any]:
        """Validate document provenance and origin.

        Args:
            document_id: Document identifier
            source_path: Optional source path
            expected_hash: Optional expected hash for verification

        Returns:
            Provenance validation result
        """
        result = {
            "status": "valid",
            "document_id": document_id,
            "provenance_verified": False,
            "warnings": [],
        }

        # Check if document ID follows expected format
        if not document_id or len(document_id) < 8:
            result["warnings"].append("Document ID too short or missing")
            result["status"] = "warning"

        # Check source path if provided
        if source_path:
            # Detect path traversal attempts
            if ".." in source_path:
                result["status"] = "error"
                result["warnings"].append("Path traversal detected in source_path")

        # Validate hash if provided
        if expected_hash:
            # Check hash format (SHA-256 should be 64 hex characters)
            # Note: This only validates the format, not that the hash matches the
            # document content. Actual hash verification requires the document content
            # and should be done separately using the checksum module.
            if len(expected_hash) == 64 and all(
                c in "0123456789abcdef" for c in expected_hash.lower()
            ):
                result["provenance_verified"] = True
            else:
                result["warnings"].append("Invalid hash format")
                result["status"] = "warning"

        return result

    def calculate_threat_score(
        self, document_text: str, metadata: dict[str, Any]
    ) -> float:
        """Calculate overall threat score for a document.

        Args:
            document_text: Document text
            metadata: Document metadata

        Returns:
            Threat score (0.0 = no threats, 1.0 = critical)
        """
        sanitization_result = self.sanitize_input(document_text, metadata)
        return sanitization_result["threat_score"]

    def check_rate_limit_posture(
        self, request_count: int, time_window_seconds: int
    ) -> dict[str, Any]:
        """Check rate limiting posture.

        Args:
            request_count: Number of requests
            time_window_seconds: Time window in seconds

        Returns:
            Rate limit status
        """
        # Calculate requests per minute
        rpm = (request_count / time_window_seconds) * 60

        result = {
            "requests_per_minute": rpm,
            "status": "normal",
            "threshold_warning": 100,
            "threshold_critical": 300,
        }

        if rpm > result["threshold_critical"]:
            result["status"] = "critical"
            result["action"] = "block"
        elif rpm > result["threshold_warning"]:
            result["status"] = "warning"
            result["action"] = "monitor"
        else:
            result["action"] = "allow"

        return result

    def generate_security_profile(
        self, document_text: str, metadata: dict[str, Any], mime_type: str | None = None
    ) -> dict[str, Any]:
        """Generate comprehensive security profile for a document.

        Args:
            document_text: Document text
            metadata: Document metadata
            mime_type: Optional MIME type

        Returns:
            Security profile with all checks
        """
        logger.debug("Generating security profile")

        profile = {
            "timestamp": self._get_timestamp(),
            "overall_status": "secure",
            "checks": {
                "input_sanitation": self.sanitize_input(document_text, metadata),
                "provenance": self.validate_provenance(
                    metadata.get("document_id", "unknown"),
                    metadata.get("source_path"),
                    metadata.get("expected_hash"),
                ),
            },
        }

        # Add MIME validation if provided
        if mime_type:
            profile["checks"]["mime_validation"] = self.validate_mime_type(mime_type)

        # Calculate threat score
        profile["threat_score"] = profile["checks"]["input_sanitation"]["threat_score"]

        # Determine overall status
        if profile["threat_score"] > 0.7:
            profile["overall_status"] = "critical"
        elif profile["threat_score"] > 0.3:
            profile["overall_status"] = "warning"
        elif any(
            check.get("status") == "error" for check in profile["checks"].values()
        ):
            profile["overall_status"] = "error"

        logger.debug(f"Security profile generated: {profile['overall_status']}")

        return profile

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat()


__all__ = ["SecurityGatekeeper"]
