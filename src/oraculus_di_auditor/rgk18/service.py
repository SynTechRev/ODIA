# src/oraculus_di_auditor/rgk18/service.py
"""Phase 18 service: RGK-18 orchestrator and external API surface."""
from __future__ import annotations

import uuid
from typing import Any

from .consensus_engine import ConsensusEngine
from .kernel import GovernanceKernel
from .ledger import Ledger
from .policy_interpreter import PolicyInterpreter, PolicySet
from .rollback_manager import RollbackManager
from .schemas import Phase18Result


class Phase18Service:
    """Orchestrates Phase 18: Recursive Governance Kernel operations."""

    def __init__(
        self,
        db_adapter: Any | None = None,
        custom_weights: dict[str, float] | None = None,
    ):
        """Initialize Phase 18 service.

        Args:
            db_adapter: Optional database adapter for ledger persistence
            custom_weights: Optional custom weights for consensus engine
        """
        self.policy_interpreter = PolicyInterpreter()
        self.consensus_engine = ConsensusEngine(weights=custom_weights)
        self.kernel = GovernanceKernel(
            policy_interpreter=self.policy_interpreter,
            consensus_engine=self.consensus_engine,
        )
        self.ledger = Ledger(db_adapter=db_adapter)
        self.rollback_manager = RollbackManager(ledger=self.ledger)

    def evaluate(
        self,
        candidate_action: dict[str, Any],
        phase_inputs: dict[str, Any],
        gcn_rules: list[dict[str, Any]] | None = None,
        dry_run: bool = True,
        auto_apply: bool = False,
        governor_approval: str | None = None,
    ) -> Phase18Result:
        """Evaluate a candidate action through the governance kernel.

        Args:
            candidate_action: Action to evaluate
            phase_inputs: Inputs from previous phases (10-17)
            gcn_rules: Optional GCN rules to check against
            dry_run: If True, suggest but do not apply changes (default: True)
            auto_apply: Allow auto-application of recommendations (default: False)
            governor_approval: Required approval token for auto_apply

        Returns:
            Phase18Result with complete evaluation
        """
        # Load GCN rules if provided
        policy_set: PolicySet | None = None
        if gcn_rules:
            policy_set = self.policy_interpreter.load_gcn_rules(gcn_rules)

        # Evaluate through kernel
        outcome, score, policy_violations, provenance = self.kernel.evaluate(
            candidate_action=candidate_action,
            phase_inputs=phase_inputs,
            policy_set=policy_set,
        )

        # Generate ledger entry ID
        entry_id = str(uuid.uuid4())

        # Create ledger entry
        self.ledger.append(
            {
                "entry_id": entry_id,
                "input_hash": provenance["input_hash"],
                "decision": outcome,
                "score": score,
                "policies_checked": policy_violations,
                "provenance": {
                    **provenance,
                    "dry_run": dry_run,
                    "auto_apply": auto_apply,
                    "governor_approval_provided": governor_approval is not None,
                },
            }
        )

        # Build result
        result = Phase18Result(
            outcome=outcome,
            score=score,
            policy_violations=[v for v in policy_violations if v.violated],
            ledger_entry_id=entry_id,
            provenance=provenance,
        )

        # Handle auto-apply if conditions met
        if (
            auto_apply
            and not dry_run
            and governor_approval
            and outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE"]
        ):
            # Mark as applied (with placeholder reverse patch)
            self.rollback_manager.mark_applied(
                entry_id, reverse_patch={"action": "reverse_placeholder"}
            )

        return result

    def commit(
        self, decision_id: str, governor_approval: str | None = None
    ) -> dict[str, Any]:
        """Commit a decision (apply it if authorized).

        Args:
            decision_id: Ledger entry ID of the decision to commit
            governor_approval: Required approval token

        Returns:
            Commit result dictionary
        """
        if not governor_approval:
            return {
                "success": False,
                "error": "Governor approval required for commit",
                "decision_id": decision_id,
            }

        # Get ledger entry
        entry = self.ledger.get_entry(decision_id)
        if not entry:
            return {
                "success": False,
                "error": "Decision not found in ledger",
                "decision_id": decision_id,
            }

        # Check if already applied
        if self.rollback_manager.is_applied(decision_id):
            return {
                "success": False,
                "error": "Decision already applied",
                "decision_id": decision_id,
            }

        # Check outcome
        if entry.decision.outcome not in ["APPROVE", "CONDITIONAL_APPROVE"]:
            return {
                "success": False,
                "error": (
                    f"Cannot commit decision with outcome: {entry.decision.outcome}"
                ),
                "decision_id": decision_id,
            }

        # Mark as applied
        self.rollback_manager.mark_applied(
            decision_id, reverse_patch={"action": "reverse_commit"}
        )

        return {
            "success": True,
            "decision_id": decision_id,
            "message": "Decision committed successfully",
        }

    def rollback(
        self,
        decision_id: str,
        dry_run: bool = True,
        governor_approval: str | None = None,
    ) -> dict[str, Any]:
        """Rollback an applied decision.

        Args:
            decision_id: Ledger entry ID of the decision to rollback
            dry_run: If True, simulate rollback without applying (default: True)
            governor_approval: Required approval token for actual rollback

        Returns:
            Rollback result dictionary
        """
        return self.rollback_manager.rollback(
            decision_id=decision_id,
            dry_run=dry_run,
            governor_approval=governor_approval,
        )

    def get_ledger_entry(self, entry_id: str) -> dict[str, Any] | None:
        """Get a ledger entry by ID.

        Args:
            entry_id: Entry identifier

        Returns:
            Ledger entry as dictionary, or None if not found
        """
        entry = self.ledger.get_entry(entry_id)
        if entry:
            return entry.model_dump()
        return None

    def verify_ledger(self) -> bool:
        """Verify integrity of the ledger chain.

        Returns:
            True if ledger is valid, False otherwise
        """
        return self.ledger.verify_chain()

    def get_all_ledger_entries(self) -> list[dict[str, Any]]:
        """Get all ledger entries.

        Returns:
            List of ledger entries as dictionaries
        """
        return [entry.model_dump() for entry in self.ledger.get_all_entries()]
