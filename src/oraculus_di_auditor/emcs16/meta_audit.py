# src/oraculus_di_auditor/emcs16/meta_audit.py
from __future__ import annotations

from typing import Any

from .schemas import ActionSuggestion


class MetaAudit:
    """Produce human-readable audit report and recommended actions."""

    def __init__(self):
        pass

    def generate_actions(
        self, supervisor_report: dict[str, Any]
    ) -> list[ActionSuggestion]:
        actions: list[ActionSuggestion] = []
        for rec in supervisor_report.get("recommended_actions", []):
            actions.append(
                ActionSuggestion(
                    id=rec.get("id", "rec:unknown"),
                    description=rec.get("description", ""),
                    confidence=rec.get("confidence", 0.5),
                    estimated_effort_hours=rec.get("estimated_effort_hours", 1.0),
                    risk_level=rec.get("risk_level", "medium"),
                    reversible=rec.get("reversible", True),
                )
            )
        return actions

    def generate_report(
        self, supervisor_report: dict[str, Any], harmonics: dict[str, float]
    ) -> dict[str, Any]:
        # lightweight textual summary + structured items
        issues = supervisor_report.get("issues", [])
        actions = self.generate_actions(supervisor_report)
        integrity = supervisor_report.get("integrity_score", 0.0)
        report = {
            "summary": f"Found {len(issues)} issues. Integrity: {integrity:.3f}",
            "issues": issues,
            "actions": [a.model_dump() for a in actions],
            "meta_field_snapshot": harmonics,
        }
        return report
