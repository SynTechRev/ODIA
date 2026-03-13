# Phase 17 — REC-17 Overview

## Goals
- Provide deterministic multi-framework ethical reasoning for decisions from Phases 12–16
- Evaluate moral, legal, constitutional, and sociotechnical implications
- Generate structured, audit-ready ethical assessments with provenance
- Maintain strict safety constraints (dry-run by default, no side effects)

## Components

### 1. Ethical Lattice Generator (ELG-17)
Deterministically creates a multi-axis ethical lattice from Phase 16 inputs.

**Ethical Axes:**
- Rights Impact (0–1)
- Harm Probability (0–1)
- Autonomy Effect (0–1)
- System Stability (0–1)
- Governance Compliance (0–1)

**Output:**
- `lattice_id`: SHA256 hash of sorted ethical vector
- `ethical_vector`: Dictionary mapping axes to scores
- `primary_ethic`: Dominant principle (beneficence, non-maleficence, justice, autonomy, stability)

### 2. Ethical Projection Engine (EPE-17)
Simulates ethical consequences over deterministic future states.

**Computation:**
- 3-step deterministic projection using pseudo-random evolution
- `delta_ethics`: Difference between projected and current ethics
- `risk`: Grade assessment (none, low, moderate, high)
- `reversible`: Boolean indicating whether changes are reversible

### 3. Legal & Constitutional Mapping (LCM-17)
Maps actions to legal and constitutional frameworks (symbolic analysis only).

**Frameworks:**
- US Constitution (1st, 4th, 5th, 14th Amendments)
- International human rights (UDHR Articles 1, 3, 12, 19)
- Common law principles

**Output:**
- `constitutional_flags`: List of potential constitutional concerns
- `human_rights_flags`: List of human rights considerations
- `compliance_score`: Overall legal compliance (0–1)

**Note:** This is symbolic analysis only, NOT legal advice.

### 4. Governance Invariant Engine (GIE-17)
Extracts and validates governance invariants.

**Invariants (by priority):**
1. Voluntary Consent (highest priority)
2. Human Primacy
3. Transparency
4. Non-Discrimination
5. Proportionality
6. Non-Coercion

**Output:**
- `invariant_violations`: List of violated invariants
- `alignment_score`: Overall governance alignment (0–1)

### 5. Phase17Service (Orchestrator)
Coordinates all components to produce complete ethical analysis.

**Inputs:**
- `phase16_result`: Phase16Result from EMCS
- `dry_run`: If True, suggest but don't apply (default: True)
- `auto_apply`: Allow auto-application (default: False)

**Outputs:**
- Complete `Phase17Result` with:
  - `ethical_lattice`
  - `ethical_projection`
  - `legal_map`
  - `governance_invariants`
  - `global_ethics_score`: Weighted ethical score (0–1)
  - `action_suggestions`: List of recommended actions
  - `provenance`: Hash, timestamp, version, configuration

## Safety Features
- `dry_run` defaults to True
- All outputs are deterministic and reproducible
- No network calls or external dependencies
- No real-world actions unless explicitly enabled with governance approval
- Comprehensive provenance tracking

## Determinism & Provenance
- All randomness derived from SHA256 hashes of inputs
- Each result includes full provenance with:
  - `input_hash`: SHA256 of Phase 16 result
  - `service_version`: rec17-0.1.0
  - `timestamp`: ISO 8601 UTC timestamp
  - `dry_run` and `auto_apply` flags

## Testing
Phase 17 includes 28 comprehensive tests covering:
- Ethical lattice generation and determinism
- Projection computation and risk assessment
- Legal mapping and compliance scoring
- Governance invariant checking
- Full service orchestration
- Determinism verification (same input → same output)

All tests pass (100% success rate).

## How to Run
See `scripts/phase17_example.py` for usage examples.

## Integration
Phase 17 consumes Phase 16 results and produces ethical analysis suitable for:
- Human review and decision-making
- Audit trail generation
- Compliance reporting
- Governance validation

## Compliance
- Pydantic v2 schemas
- Black + Ruff formatting
- Type-annotated
- Fully documented
- Security-reviewed (CodeQL)
