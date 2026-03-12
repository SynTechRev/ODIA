"""Global Constraint Network (GCN) module for Phase 10.

Central authority for defining and enforcing computation boundaries,
structural constraints, policies, document rulesets, and pipeline
safety invariants across all agents and operations.
"""

from .constraint_validator import ConstraintValidator
from .gcn_service import GCNService
from .policy_registry import PolicyRegistry
from .schemas import (
    ConstraintValidationRequest,
    ConstraintValidationResponse,
    ConstraintViolation,
    GCNRuleSchema,
    GCNStateResponse,
    GCNValidateRequest,
    GCNValidateResponse,
)

__all__ = [
    "GCNService",
    "ConstraintValidator",
    "PolicyRegistry",
    "GCNRuleSchema",
    "ConstraintValidationRequest",
    "ConstraintValidationResponse",
    "ConstraintViolation",
    "GCNStateResponse",
    "GCNValidateRequest",
    "GCNValidateResponse",
]
