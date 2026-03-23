# Contributing to ODIA

Thank you for your interest in contributing. This guide covers how to set up
your environment, the conventions we follow, and how to submit changes.

---

## Getting Started

```bash
git clone https://github.com/SynTechRev/ODIA.git
cd ODIA
pip install -e ".[dev]"
```

Verify everything works:

```bash
pytest
black --check src tests
ruff check src tests
```

---

## Development Workflow

1. **Fork** the repository and create a feature branch from `master`
2. Make your changes
3. Run the full test suite — all 827 tests must pass
4. Format and lint your code
5. Open a pull request with a clear description of what changed and why

```bash
# Before opening a PR
pytest
black src tests
ruff check src tests
```

---

## Code Conventions

| Tool | Config |
|------|--------|
| Formatter | `black`, line-length 88 |
| Linter | `ruff` (E, F, W, I, N, UP, C90, B) |
| Tests | `pytest`, mirrors `src/` structure |
| Python | 3.11+ |

**Anomaly detectors** must return a structured dict:
```python
{
    "type": str,        # e.g. "fiscal_anomaly"
    "severity": str,    # "low" | "medium" | "high" | "critical"
    "description": str,
    "evidence": str
}
```

**Naming** — use plain engineering terminology. Avoid abstract or
metaphorical names for new modules and functions.

**Config** — settings go in `config/` (YAML for runtime settings,
JSON for corpus manifests). No hardcoded jurisdiction names, URLs,
agency names, or dollar amounts.

**Secrets** — use environment variables (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`). Never commit credentials.

**Data** — do not commit files to `oraculus/corpus/` or generated
outputs to `analysis/`. These are runtime artifacts.

**Provenance** — all document processing must preserve SHA-256 hashes
and timestamps through the pipeline.

---

## Adding a New Anomaly Detector

1. Create your detector in `src/oraculus_di_auditor/analysis/`
2. Return the standard dict format above
3. Register it in `src/oraculus_di_auditor/analysis/audit_engine.py`
4. Add tests under `tests/` mirroring the module path

---

## Adding a New API Route

1. Add a route module under `src/oraculus_di_auditor/interface/routes/`
2. Register it in `src/oraculus_di_auditor/interface/api.py`
3. Use Pydantic v2 models for request/response validation
4. Add integration tests under `tests/test_api_integration.py`

---

## Reporting Issues

Use the GitHub issue tracker. For audit findings or security concerns,
use the [audit finding template](.github/ISSUE_TEMPLATE/audit_finding.md).

For security vulnerabilities, contact the maintainers directly before
opening a public issue.

---

## Legal Note

By contributing, you agree that your contributions will be licensed under
the project's [MIT License](LICENSE). Do not submit code containing
jurisdiction-specific data, PII, or material subject to confidentiality
obligations.

---

## PyPI Publication

### Build and publish (maintainers only)

```bash
# Install build tools
pip install build twine

# Run full test suite first
pytest

# Build wheel and sdist
python -m build

# Check the distribution
twine check dist/*

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Verify installability from TestPyPI
pip install --index-url https://test.pypi.org/simple/ odia

# Upload to production PyPI
twine upload dist/*
```

### CLI smoke test after installation

```bash
odia --help
odia demo
odia audit --source data/demo/ --output reports/smoke/
```

### Version bumping

Update `version` in `pyproject.toml` and create a git tag:

```bash
git tag v2.1.0
git push origin v2.1.0
```
