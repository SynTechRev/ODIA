# src/oraculus_di_auditor/rgk18/__init__.py
"""Phase 18: Recursive Governance Kernel (RGK-18).

This module implements a deterministic governance kernel that enforces,
validates, and synthesizes governance rules across the entire pipeline.
"""
from .consensus_engine import ConsensusEngine
from .kernel import GovernanceKernel
from .ledger import Ledger
from .policy_interpreter import Policy, PolicyInterpreter, PolicySet
from .rollback_manager import RollbackManager
from .schemas import (
    DecisionOutcome,
    DecisionScore,
    LedgerEntry,
    Phase18Result,
    PolicyCheckResult,
)
from .service import Phase18Service

__all__ = [
    "Phase18Service",
    "GovernanceKernel",
    "PolicyInterpreter",
    "Policy",
    "PolicySet",
    "ConsensusEngine",
    "Ledger",
    "RollbackManager",
    "Phase18Result",
    "DecisionOutcome",
    "DecisionScore",
    "PolicyCheckResult",
    "LedgerEntry",
]
