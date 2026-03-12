# src/oraculus_di_auditor/rgk18/rollback_manager.py
"""Rollback manager for reversible governance decisions."""
from __future__ import annotations

from typing import Any

from .constants import MAX_ROLLBACK_ATTEMPTS
from .ledger import Ledger


class RollbackManager:
    """Manages reversible decision application and rollback."""

    def __init__(self, ledger: Ledger):
        """Initialize rollback manager.

        Args:
            ledger: Ledger instance for tracking decisions
        """
        self.ledger = ledger
        self.applied_decisions: dict[str, dict[str, Any]] = {}
        self.rollback_attempts: dict[str, int] = {}

    def mark_applied(
        self, decision_id: str, reverse_patch: dict[str, Any] | None = None
    ) -> None:
        """Mark a decision as applied with optional reverse patch.

        Args:
            decision_id: Decision/ledger entry ID
            reverse_patch: Optional reverse patch for rollback
        """
        self.applied_decisions[decision_id] = {
            "reverse_patch": reverse_patch,
            "applied": True,
        }
        self.rollback_attempts[decision_id] = 0

    def is_applied(self, decision_id: str) -> bool:
        """Check if a decision has been applied.

        Args:
            decision_id: Decision/ledger entry ID

        Returns:
            True if applied, False otherwise
        """
        if decision_id not in self.applied_decisions:
            return False
        return self.applied_decisions[decision_id].get("applied", False)

    def rollback(
        self,
        decision_id: str,
        dry_run: bool = True,
        governor_approval: str | None = None,
    ) -> dict[str, Any]:
        """Rollback an applied decision.

        Args:
            decision_id: Decision/ledger entry ID to rollback
            dry_run: If True, simulate rollback without applying
            governor_approval: Required approval token for actual rollback

        Returns:
            Rollback result dictionary
        """
        # Check if decision was applied
        if not self.is_applied(decision_id):
            return {
                "success": False,
                "error": "Decision was not applied",
                "decision_id": decision_id,
            }

        # Check rollback attempts
        attempts = self.rollback_attempts.get(decision_id, 0)
        if attempts >= MAX_ROLLBACK_ATTEMPTS:
            return {
                "success": False,
                "error": (
                    f"Maximum rollback attempts ({MAX_ROLLBACK_ATTEMPTS}) exceeded"
                ),
                "decision_id": decision_id,
            }

        # Get decision data
        decision_data = self.applied_decisions[decision_id]
        reverse_patch = decision_data.get("reverse_patch")

        if not reverse_patch:
            return {
                "success": False,
                "error": "No reverse patch available for rollback",
                "decision_id": decision_id,
            }

        # Dry run: just validate
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "decision_id": decision_id,
                "message": "Rollback validated (dry run)",
                "reverse_patch": reverse_patch,
            }

        # Actual rollback requires governor approval
        if not governor_approval:
            return {
                "success": False,
                "error": "Governor approval required for rollback",
                "decision_id": decision_id,
            }

        # Apply reverse patch (placeholder - actual implementation would apply changes)
        self._apply_reverse_patch(reverse_patch)

        # Increment attempts
        self.rollback_attempts[decision_id] += 1

        # Mark as rolled back
        self.applied_decisions[decision_id]["applied"] = False
        self.applied_decisions[decision_id]["rolled_back"] = True

        return {
            "success": True,
            "dry_run": False,
            "decision_id": decision_id,
            "message": "Rollback applied successfully",
            "attempts": self.rollback_attempts[decision_id],
        }

    def _apply_reverse_patch(self, reverse_patch: dict[str, Any]) -> None:
        """Apply a reverse patch to restore state.

        Args:
            reverse_patch: Reverse patch to apply
        """
        # Placeholder for actual reverse patch application
        # In production, this would:
        # 1. Validate invariants
        # 2. Apply the reverse operations
        # 3. Verify state consistency
        pass

    def get_applied_decisions(self) -> list[str]:
        """Get list of applied decision IDs.

        Returns:
            List of decision IDs that have been applied
        """
        return [
            decision_id
            for decision_id, data in self.applied_decisions.items()
            if data.get("applied", False)
        ]

    def get_rollback_status(self, decision_id: str) -> dict[str, Any]:
        """Get rollback status for a decision.

        Args:
            decision_id: Decision/ledger entry ID

        Returns:
            Status dictionary
        """
        if decision_id not in self.applied_decisions:
            return {"exists": False}

        data = self.applied_decisions[decision_id]
        return {
            "exists": True,
            "applied": data.get("applied", False),
            "rolled_back": data.get("rolled_back", False),
            "attempts": self.rollback_attempts.get(decision_id, 0),
            "has_reverse_patch": data.get("reverse_patch") is not None,
        }
