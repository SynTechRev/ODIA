# src/oraculus_di_auditor/rgk18/constants.py
"""Configuration constants for Phase 18: Recursive Governance Kernel."""

# Default weights for evidence aggregation
DEFAULT_WEIGHTS = {
    "scalar_harmonics": 0.25,
    "qdcl_probability": 0.25,
    "temporal_stability": 0.20,
    "ethical_score": 0.20,
    "self_healing_risk": 0.10,
}

# Decision thresholds
APPROVE_THRESHOLD = 0.75  # Score >= 0.75 → APPROVE
CONDITIONAL_THRESHOLD = 0.55  # 0.55 <= Score < 0.75 → CONDITIONAL_APPROVE
REVIEW_THRESHOLD = 0.35  # 0.35 <= Score < 0.55 → REVIEW
# Score < 0.35 → REJECT

# Ledger configuration
LEDGER_SIGNATURE_KEY = "rgk18-ledger-v1"  # Used for chain signature derivation
MAX_ROLLBACK_ATTEMPTS = 3

# Service version
SERVICE_VERSION = "rgk18-0.1.0"
