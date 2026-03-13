# Phase 18: Recursive Governance Kernel (RGK-18) Overview

## Purpose

RGK-18 is a fully deterministic, audit-ready governance kernel that enforces, validates, and synthesizes governance rules across the entire Oraculus DI Auditor pipeline (Phases 1–17). It provides runtime constraint enforcement, policy rollbacks, and a certified governance decision ledger.

## Architecture

### Core Components

1. **Policy Interpreter** (`policy_interpreter.py`)
   - Normalizes GCN rules (Phase 10) and Governor policies (Phase 9) into canonical `Policy` objects
   - Validates syntactic and semantic correctness
   - Produces `PolicySet` with priority, scope, and mutability flags

2. **Consensus Engine** (`consensus_engine.py`)
   - Aggregates evidence from multiple sources:
     - Scalar harmonics (Phase 12)
     - QDCL probability signals (Phase 13)
     - Temporal stability metrics (Phase 15)
     - Ethical lattice + projection (Phase 17)
     - Self-healing risk (Phase 11)
   - Deterministic weighted aggregation → `DecisionScore` (0.0–1.0)
   - Configurable weighting matrix

3. **Governance Kernel** (`kernel.py`)
   - Evaluates candidate actions against policies
   - Produces decision outcomes:
     - `APPROVE`: Score ≥ 0.75
     - `CONDITIONAL_APPROVE`: 0.55 ≤ Score < 0.75
     - `REVIEW`: 0.35 ≤ Score < 0.55
     - `REJECT`: Score < 0.35 or high-severity violations
   - Generates mitigations for conditional approvals
   - Deterministic tie-breaking via canonical hash ordering

4. **Ledger** (`ledger.py`)
   - Append-only, cryptographically-signed entries
   - SHA256 chain signature for integrity verification
   - Support for read-by-proof (audit trail)
   - Optional DB adapter integration

5. **Rollback Manager** (`rollback_manager.py`)
   - Manages reversible decision applications
   - Stores reverse-patch for each applied decision
   - Validates invariants before rollback
   - Respects maximum rollback attempts (default: 3)

6. **Service API** (`service.py`)
   - `Phase18Service.evaluate()`: Evaluate candidate action
   - `Phase18Service.commit()`: Apply decision with governor approval
   - `Phase18Service.rollback()`: Reverse applied decision
   - `Phase18Service.verify_ledger()`: Verify chain integrity

## Configuration

Configuration constants are defined in `constants.py`:

```python
# Evidence weights (normalized to sum to 1.0)
DEFAULT_WEIGHTS = {
    "scalar_harmonics": 0.25,
    "qdcl_probability": 0.25,
    "temporal_stability": 0.20,
    "ethical_score": 0.20,
    "self_healing_risk": 0.10,
}

# Decision thresholds
APPROVE_THRESHOLD = 0.75
CONDITIONAL_THRESHOLD = 0.55
REVIEW_THRESHOLD = 0.35

# Ledger configuration
MAX_ROLLBACK_ATTEMPTS = 3
```

## Security & Safety Model

- **Dry-run by default**: `dry_run=True` ensures no side effects
- **Governor approval required**: `auto_apply=False` unless governor approval token present
- **Append-only ledger**: Immutable decision history
- **No external calls**: All operations are local and deterministic
- **Audit trail**: Complete provenance metadata (seed, timestamp, service_version, input_hash)

## Determinism

RGK-18 achieves determinism through:

1. **Canonical input normalization**: Sorts dictionaries, normalizes floats to 6 decimal places
2. **Seed derivation**: SHA256 hash of canonical input → deterministic seed
3. **Deterministic RNG**: Linear Congruential Generator for tie-breaking
4. **Fixed JSON serialization**: `json.dumps(sort_keys=True)` ensures consistent ordering

## Usage Example

```python
from oraculus_di_auditor.rgk18 import Phase18Service

# Initialize service
service = Phase18Service()

# Define candidate action
candidate_action = {
    "action_type": "apply_patch",
    "patch_id": "patch-123",
    "payload": {"changes": [...]}
}

# Provide phase inputs
phase_inputs = {
    "phase12": {"coherence_score": 0.85},
    "phase13": {"probability": 0.88},
    "phase15": {"stability_score": 0.82},
    "phase17": {"global_ethics_score": 0.87},
    "phase11": {"risk_score": 0.15}
}

# Optional: Define GCN rules
gcn_rules = [
    {
        "policy_id": "no-delete",
        "rule_type": "prohibition",
        "condition": {"prohibited_actions": ["delete"]},
        "severity": "high"
    }
]

# Evaluate (dry run by default)
result = service.evaluate(
    candidate_action=candidate_action,
    phase_inputs=phase_inputs,
    gcn_rules=gcn_rules,
    dry_run=True
)

print(f"Outcome: {result.outcome.outcome}")
print(f"Score: {result.score.score:.3f}")
print(f"Rationale: {result.outcome.rationale}")

# If approved, commit with governor approval
if result.outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE"]:
    commit_result = service.commit(
        decision_id=result.ledger_entry_id,
        governor_approval="signed-governor-token"
    )
    
    if commit_result["success"]:
        print("Decision committed successfully")
        
        # Later, if needed, rollback
        rollback_result = service.rollback(
            decision_id=result.ledger_entry_id,
            dry_run=False,
            governor_approval="signed-governor-token"
        )
```

## Integration Points

### With Governor (Phase 9)
- Governor must call `Phase18Service.commit()` with validated approval token
- Governor can query ledger for decision history and provenance

### With Orchestrator (Phase 8)
- Orchestrator should call `Phase18Service.evaluate()` before applying cross-document changes
- Orchestrator respects decision outcomes and applies mitigations for conditional approvals

### With Self-Healing (Phase 11)
- Self-healing consults RGK-18 for policy conflicts before auto-applying fixes
- Self-healing risk scores feed into consensus engine

### With GCN (Phase 10)
- GCN rules are loaded and normalized by policy interpreter
- Policy violations trigger appropriate decision outcomes

## Backwards Compatibility

- RGK-18 uses only existing outputs from Phases 10–17
- Missing phase outputs default to neutral (0.5) scores
- In-memory ledger used when DB adapter not provided
- All operations are backward compatible with existing phases

## Testing

RGK-18 includes 64 comprehensive tests:
- `test_policy_interpreter.py`: 7 tests
- `test_consensus_engine.py`: 10 tests
- `test_kernel_decision_flow.py`: 9 tests
- `test_ledger_and_provenance.py`: 10 tests
- `test_rollback_manager.py`: 13 tests
- `test_phase18_service_integration.py`: 15 tests

All tests are deterministic and verify:
- Policy checking and normalization
- Evidence aggregation and scoring
- Decision flow logic
- Ledger integrity and chain signatures
- Rollback functionality
- End-to-end service integration

## ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Phase 18: RGK-18 Service                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Governance Kernel (kernel.py)       │
        │  • Evaluates candidate actions           │
        │  • Maps scores to outcomes               │
        │  • Generates mitigations                 │
        └─────────────────────────────────────────┘
                 │                    │
         ┌───────┴────────┐    ┌──────┴────────┐
         ▼                ▼    ▼               ▼
   ┌──────────┐    ┌────────────┐    ┌──────────────┐
   │ Policy   │    │ Consensus  │    │   Ledger     │
   │ Interpreter│    │  Engine    │    │ (ledger.py)  │
   │ (policy_ │    │ (consensus_│    │ • Append-only│
   │ interpreter.py)│ engine.py) │    │ • Chain sigs │
   │ • GCN rules│    │ • Evidence │    │ • Provenance │
   │ • Priority │    │   aggregation│    │            │
   └──────────┘    └────────────┘    └──────────────┘
         │                │                   │
         ▼                ▼                   ▼
   ┌──────────────────────────────────────────────┐
   │           Phase Inputs (10-17)               │
   │  • Phase 10: GCN rules                       │
   │  • Phase 12: Scalar harmonics                │
   │  • Phase 13: QDCL probability                │
   │  • Phase 15: Temporal stability              │
   │  • Phase 17: Ethical score                   │
   │  • Phase 11: Self-healing risk               │
   └──────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Rollback Manager │
              │ (rollback_       │
              │  manager.py)     │
              │ • Applied track  │
              │ • Reverse patches│
              └──────────────────┘
```

## Performance Considerations

- **Policy caching**: Future optimization for large policy sets
- **Indexed scope checks**: For faster policy evaluation
- **DB adapter**: Optional for production persistence
- **In-memory operations**: Default mode for tests and dry-runs

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Wrong classification of borderline decisions | Conservative thresholds (APPROVE_THRESHOLD=0.75), manual review for CONDITIONAL_APPROVE |
| Ledger tampering | Chain signature, strong DB transaction enforcement |
| Performance hit with many policies | Policy caching, indexed scope checks (future) |
| Drift across Python versions | Canonical JSON dumps, fixed float rounding, pinned Python version in CI |

## Future Enhancements

- Policy template library
- Machine learning-based threshold adjustment
- Distributed ledger backend
- Real-time policy conflict detection
- Advanced mitigation generation using LLMs
