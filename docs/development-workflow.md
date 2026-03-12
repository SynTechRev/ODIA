# Development Workflow & Permanent Quality Enforcement

This document defines the permanent workflow standards to prevent recurring issues (e.g. PR not updating, placeholder validation logic, inconsistent enforcement at phase conclusions) and to perfect Phase 10 completion quality.

## 1. Branching & Pull Requests
- Create a dedicated branch for every feature or fix: `feature/<short-name>` or `fix/<short-name>`.
- Never push Phase changes directly to `main`. Open a PR; once merged the PR is immutable. New work requires a new branch + PR.
- Use clear PR titles: `Phase 10: <Component> Improvement` or `Fix: <Issue Summary>`.
- Include description with: scope, rationale, tests added, migration notes (if any).

## 2. Definition of Done (DoD)
A change is DONE only if ALL apply:
1. All tests pass (`pytest -q`).
2. Lint (`ruff check .`) and format (`black --check .`) clean.
3. No placeholders: search for `TODO`, `FIXME`, `Placeholder disables` yields zero in `src/`.
4. New logic covered by targeted tests (positive + negative paths).
5. Documentation updated if public API or workflow changed.
6. CI green (pre-commit workflow + any additional checks).

## 3. Constraint & Policy Integrity
- All constraint enforcement must use real logic; no unconditional passes.
- Add tests for each new constraint expression; failing scenario must exist.
- When adding a rule to `PolicyRegistry`, also add a corresponding test in `tests/` referencing its `rule_id`.

## 4. Preventing Placeholder Regressions
Add a CI grep step (or pre-commit hook) to fail if patterns match:
- `return True  # Placeholder`
- `# WARNING: This placeholder`
- `Simplified rule checking logic`
Optional enhancement: a script `scripts/scan_placeholders.py` returning non‑zero exit code if placeholders exist.

## 5. Quality Gates Automation
Pipeline order:
1. `pre-commit run --all-files` (formats + lints).
2. Placeholder scan.
3. Unit tests.
4. (Optional) Coverage threshold enforcement.

## 6. Test Strategy
- Unit tests for each agent type (Sentinel, Constraint, Routing, Synthesis).
- Rule tests: For every rule, at least one violation test (failing entity) and one success test.
- Mesh integration tests: multi-agent job execution path.
- Regression tests: when a bug is fixed, add a test reproducing it pre-fix.

## 7. Release & Tagging
- Tag stable milestones: `v0.2.0-phase10` after major phase completion + quality verification.
- Changelog entry must summarize: new rules, agents, tests count, enforcement improvements.

## 8. Workflow Commands (Reference)
```bash
# Create branch
git checkout -b fix/constraint-validation

# Run quality gates locally
ruff check .
black --check .
pytest -q

# Run full pre-commit suite
pre-commit run --all-files

# Placeholder scan (example)
grep -R "Placeholder disables" -n src/ && exit 1 || echo "No placeholders"
```

## 9. Incident Resolution Playbook
If recurring issue appears (e.g. PR not updating or missing enforcement):
1. Confirm PR merged status.
2. If merged, create new branch; never force-push merged PR.
3. Add missing tests reproducing defect.
4. Implement fix with minimal scope.
5. Run full gates; open new PR; link old PR number in description.

## 10. Continuous Improvement
- Quarterly audit: scan for low test coverage areas and add tests.
- Track mean time to resolve (MTTR) for constraint failures; optimize rule clarity.
- Review rule set priority collisions; adjust to keep ordering deterministic.

---
Adhering to this workflow permanently eliminates the class of recurring placeholder and PR update issues while reinforcing Phase 10 architectural integrity.
