"""Change Tracker for Evolution Engine.

Tracks all evolution changes with full audit trail and reversibility support.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ChangeTracker:
    """Tracks evolution changes with audit trail and reversibility.

    All changes are recorded and can be reversed if needed.
    Provides full provenance and traceability.
    """

    def __init__(self, tracking_dir: str | None = None):
        """Initialize change tracker.

        Args:
            tracking_dir: Directory to store change logs
        """
        if tracking_dir is None:
            self.tracking_dir = Path("data/evolution_changes")
        else:
            self.tracking_dir = Path(tracking_dir)

        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        self.changes: list[dict[str, Any]] = []
        self.change_map: dict[str, dict[str, Any]] = {}

        logger.info(f"ChangeTracker initialized at {self.tracking_dir}")

    def record_change(
        self,
        change_type: str,
        description: str,
        affected_files: list[str],
        before_state: dict[str, Any],
        after_state: dict[str, Any],
        reversible: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Record a change to the system.

        Args:
            change_type: Type of change (refactor, optimization, upgrade, etc.)
            description: Human-readable description
            affected_files: List of files affected
            before_state: State before change
            after_state: State after change
            reversible: Whether change can be reversed
            metadata: Additional metadata

        Returns:
            Change ID
        """
        change_id = self._generate_change_id(change_type, description)

        change_record = {
            "change_id": change_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "change_type": change_type,
            "description": description,
            "affected_files": affected_files,
            "before_state": before_state,
            "after_state": after_state,
            "reversible": reversible,
            "metadata": metadata or {},
            "status": "recorded",
            "applied": False,
            "reversed": False,
        }

        self.changes.append(change_record)
        self.change_map[change_id] = change_record

        # Persist to disk
        self._persist_change(change_record)

        logger.info(f"Change recorded: {change_id} - {description}")
        return change_id

    def mark_applied(
        self, change_id: str, success: bool, details: dict[str, Any] | None = None
    ):
        """Mark a change as applied.

        Args:
            change_id: Change identifier
            success: Whether application was successful
            details: Additional details about application
        """
        if change_id not in self.change_map:
            logger.warning(f"Change not found: {change_id}")
            return

        change = self.change_map[change_id]
        change["applied"] = True
        change["applied_at"] = datetime.now(UTC).isoformat()
        change["application_success"] = success
        change["application_details"] = details or {}

        logger.info(f"Change marked as applied: {change_id} (success={success})")

    def reverse_change(self, change_id: str) -> dict[str, Any]:
        """Reverse a previously applied change.

        Args:
            change_id: Change identifier

        Returns:
            Reversal result
        """
        if change_id not in self.change_map:
            return {"status": "error", "message": "Change not found"}

        change = self.change_map[change_id]

        if not change["reversible"]:
            return {"status": "error", "message": "Change is not reversible"}

        if not change["applied"]:
            return {"status": "error", "message": "Change was not applied"}

        if change["reversed"]:
            return {"status": "error", "message": "Change already reversed"}

        # Mark as reversed
        change["reversed"] = True
        change["reversed_at"] = datetime.now(UTC).isoformat()

        logger.info(f"Change reversed: {change_id}")

        return {
            "status": "success",
            "change_id": change_id,
            "reversed_at": change["reversed_at"],
            "restore_state": change["before_state"],
        }

    def get_change(self, change_id: str) -> dict[str, Any] | None:
        """Get change record by ID.

        Args:
            change_id: Change identifier

        Returns:
            Change record or None
        """
        return self.change_map.get(change_id)

    def get_changes_by_type(self, change_type: str) -> list[dict[str, Any]]:
        """Get all changes of a specific type.

        Args:
            change_type: Type of change to filter by

        Returns:
            List of matching changes
        """
        return [c for c in self.changes if c["change_type"] == change_type]

    def get_changes_by_file(self, file_path: str) -> list[dict[str, Any]]:
        """Get all changes affecting a specific file.

        Args:
            file_path: Path to file

        Returns:
            List of changes affecting the file
        """
        return [c for c in self.changes if file_path in c["affected_files"]]

    def get_change_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get change history.

        Args:
            limit: Maximum number of changes to return

        Returns:
            List of changes (most recent first)
        """
        sorted_changes = sorted(
            self.changes, key=lambda c: c["timestamp"], reverse=True
        )

        if limit:
            return sorted_changes[:limit]
        return sorted_changes

    def get_statistics(self) -> dict[str, Any]:
        """Get change statistics.

        Returns:
            Statistics about tracked changes
        """
        total_changes = len(self.changes)
        applied_changes = len([c for c in self.changes if c["applied"]])
        reversed_changes = len([c for c in self.changes if c["reversed"]])
        successful_changes = len(
            [
                c
                for c in self.changes
                if c.get("applied") and c.get("application_success")
            ]
        )

        changes_by_type: dict[str, int] = {}
        for change in self.changes:
            change_type = change["change_type"]
            changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1

        return {
            "total_changes": total_changes,
            "applied_changes": applied_changes,
            "reversed_changes": reversed_changes,
            "successful_changes": successful_changes,
            "success_rate": (
                successful_changes / applied_changes if applied_changes > 0 else 0.0
            ),
            "changes_by_type": changes_by_type,
        }

    def export_audit_trail(self, output_file: str | None = None) -> str:
        """Export full audit trail to JSON file.

        Args:
            output_file: Output file path (optional)

        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            output_file = str(self.tracking_dir / f"audit_trail_{timestamp}.json")

        audit_trail = {
            "exported_at": datetime.now(UTC).isoformat(),
            "total_changes": len(self.changes),
            "statistics": self.get_statistics(),
            "changes": self.changes,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(audit_trail, f, indent=2)

        logger.info(f"Audit trail exported to {output_file}")
        return output_file

    def _generate_change_id(self, change_type: str, description: str) -> str:
        """Generate unique change ID.

        Args:
            change_type: Type of change
            description: Change description

        Returns:
            Change ID
        """
        timestamp = datetime.now(UTC).isoformat()
        content = f"{change_type}:{description}:{timestamp}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"change_{hash_digest}"

    def _persist_change(self, change_record: dict[str, Any]):
        """Persist change record to disk.

        Args:
            change_record: Change to persist
        """
        change_id = change_record["change_id"]
        change_file = self.tracking_dir / f"{change_id}.json"

        with open(change_file, "w", encoding="utf-8") as f:
            json.dump(change_record, f, indent=2)
