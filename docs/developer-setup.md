# Developer Setup Guide

## Quick Start

Get up and running with Oraculus-DI-Auditor in under 5 minutes.

```bash
# Clone the repository
git clone https://github.com/SynTechRev/Oraculus-DI-Auditor.git
cd Oraculus-DI-Auditor

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests to verify installation
pytest

# Run linter
ruff check src tests

# Install pre-commit hooks
pre-commit install
```

**Expected Output**:
- All 143 tests should pass
- Ruff should report "All checks passed!"
- Pre-commit hooks installed successfully

---

## System Requirements

### Required
- **Python**: 3.11 or higher
- **pip**: Latest version (update with `pip install --upgrade pip`)
- **Git**: For version control

### Recommended
- **pyenv** or **asdf**: For managing multiple Python versions
- **direnv**: For automatic virtual environment activation
- **VS Code** or **PyCharm**: With Python extensions

### Operating Systems
- **Linux**: Ubuntu 20.04+, Debian 11+, Arch, Fedora
- **macOS**: 11 (Big Sur) or newer
- **Windows**: 10/11 with WSL2 recommended

---

## Detailed Installation

### 1. Install Python 3.11+

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

#### macOS (via Homebrew)
```bash
brew install python@3.11
```

#### Windows
Download from [python.org](https://www.python.org/downloads/) or use:
```powershell
winget install Python.Python.3.11
```

### 2. Clone and Setup Repository

```bash
# SSH (recommended for contributors)
git clone git@github.com:SynTechRev/Oraculus-DI-Auditor.git

# HTTPS (for read-only access)
git clone https://github.com/SynTechRev/Oraculus-DI-Auditor.git

cd Oraculus-DI-Auditor
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Windows cmd.exe)
.venv\Scripts\activate.bat
```

**Verify Activation**:
```bash
which python  # Should show path inside .venv
python --version  # Should show 3.11+
```

### 4. Install Dependencies

#### Option 1: Editable Install (Recommended for Development)
```bash
pip install -e ".[dev]"
```

#### Option 2: Requirements Files
```bash
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

**What Gets Installed**:
- **Core**: `pypdf`, `jsonschema`, `scikit-learn`, `numpy`
- **Dev**: `pytest`, `pytest-cov`, `black`, `ruff`, `pre-commit`, `isort`

### 5. Verify Installation

```bash
# Run full test suite
pytest

# Run with coverage report
pytest --cov=src/oraculus --cov=src/oraculus_di_auditor --cov-report=term-missing

# Check code formatting
black --check src tests

# Run linter
ruff check src tests

# Check for complexity warnings
ruff check src --statistics
```

---

## Development Workflow

### 1. Pre-Commit Hooks

Install pre-commit hooks to automatically check code before committing:

```bash
pre-commit install
```

**What it does**:
- Runs `ruff` linter on changed files
- Formats code with `black`
- Checks for trailing whitespace, merge conflicts, etc.
- Validates JSON and YAML files

**Manual run**:
```bash
pre-commit run --all-files
```

### 2. Running Tests

#### All Tests
```bash
pytest
```

#### Specific Test File
```bash
pytest tests/test_audit_engine.py
```

#### Specific Test Function
```bash
pytest tests/test_audit_engine.py::test_analyze_document_smoke
```

#### With Verbose Output
```bash
pytest -v
```

#### With Coverage
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

#### Watch Mode (Re-run on File Changes)
```bash
pip install pytest-watch
ptw
```

### 3. Code Quality

#### Format Code
```bash
# Check formatting (don't modify)
black --check src tests

# Apply formatting
black src tests
```

#### Lint Code
```bash
# Check for issues
ruff check src tests

# Auto-fix issues
ruff check src tests --fix
```

#### Sort Imports
```bash
# Check imports
isort --check-only src tests

# Fix imports
isort src tests
```

### 4. Type Checking (Optional)

The project includes `pyrightconfig.json` for static type checking:

```bash
# Install pyright
pip install pyright

# Run type checker
pyright src
```

---

## Project Structure

```
Oraculus-DI-Auditor/
├── src/
│   ├── oraculus/                  # Advanced legislative system
│   │   ├── auditing/              # Provenance tracking
│   │   ├── ingestion/             # Legislative loaders
│   │   └── ...
│   └── oraculus_di_auditor/       # Foundational scaffold
│       ├── analysis/              # Audit detectors
│       │   ├── audit_engine.py
│       │   ├── fiscal.py
│       │   ├── constitutional.py
│       │   ├── surveillance.py
│       │   ├── cross_reference.py
│       │   └── scalar_core.py
│       ├── ingestion/             # XML parser, checksum tracker
│       ├── interface/             # API interfaces (future)
│       ├── cli.py                 # Command-line interface
│       ├── config.py              # Configuration
│       ├── ingest.py              # Document ingestion
│       ├── normalize.py           # Text normalization
│       ├── embeddings.py          # TF-IDF embeddings
│       ├── retriever.py           # Vector search
│       ├── analyzer.py            # Anomaly analyzer
│       └── reporter.py            # Report generation
├── tests/                         # Test suite (143 tests)
├── docs/                          # Documentation
├── config/                        # Configuration files
├── data/                          # Runtime data (gitignored)
├── schemas/                       # JSON schemas
├── scripts/                       # Utility scripts
└── pyproject.toml                 # Project metadata and config
```

---

## Common Development Tasks

### Adding a New Anomaly Detector

1. Create detector module:
```python
# src/oraculus_di_auditor/analysis/my_detector.py
from typing import Any

def detect_my_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect specific anomalies."""
    anomalies = []
    # Detection logic here
    return anomalies
```

2. Register in audit engine:
```python
# src/oraculus_di_auditor/analysis/audit_engine.py
from .my_detector import detect_my_anomalies

def analyze_document(doc: dict[str, Any]) -> dict[str, Any]:
    anomalies = []
    anomalies.extend(detect_fiscal_anomalies(doc))
    anomalies.extend(detect_my_anomalies(doc))  # Add here
    # ...
```

3. Write tests:
```python
# tests/test_my_detector.py
def test_detect_my_anomalies():
    doc = {"field": "value"}
    result = detect_my_anomalies(doc)
    assert isinstance(result, list)
```

4. Run tests and lint:
```bash
pytest tests/test_my_detector.py
ruff check src/oraculus_di_auditor/analysis/my_detector.py
```

### Running the CLI

```bash
# Ingest documents
python -m oraculus_di_auditor.cli ingest --source data/sources

# Or use scripts
python scripts/ingest_and_index.py --source data/sources --analyze
```

### Generating Documentation

```bash
# Generate API documentation (future)
pip install pdoc3
pdoc --html --output-dir docs/api src/oraculus_di_auditor
```

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'oraculus_di_auditor'`

**Solution**:
```bash
# Ensure installed in editable mode
pip install -e .

# Verify installation
pip list | grep oraculus
```

### Test Failures

**Problem**: Tests fail with missing fixtures

**Solution**:
```bash
# Ensure pytest discovers fixtures
# Check that tests/conftest.py exists
ls tests/conftest.py

# Run with verbose output
pytest -v
```

### Linter Errors

**Problem**: Ruff reports complexity warnings (C901)

**Solution**:
```bash
# These are informational (not blocking)
# Refactor complex functions iteratively
ruff check src --statistics
```

### Virtual Environment Issues

**Problem**: Wrong Python version or packages not found

**Solution**:
```bash
# Deactivate current environment
deactivate

# Remove old environment
rm -rf .venv

# Recreate with correct Python version
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## IDE Configuration

### VS Code

**Recommended Extensions**:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- Black Formatter (ms-python.black-formatter)

**Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### PyCharm

1. **Open Project**: File → Open → Select `Oraculus-DI-Auditor`
2. **Configure Interpreter**: Settings → Project → Python Interpreter → Add → Virtualenv Environment → Existing → `.venv/bin/python`
3. **Enable pytest**: Settings → Tools → Python Integrated Tools → Testing → Default test runner: pytest
4. **Enable Black**: Settings → Tools → Black → On code reformat
5. **Enable Ruff**: Settings → Tools → External Tools → Add Ruff

---

## CI/CD Integration

The project uses GitHub Actions for continuous integration:

**Workflow**: `.github/workflows/python-ci.yml`

**Checks**:
- Pytest (all 143 tests)
- Ruff linting
- Code formatting (Black)

**Local CI Simulation**:
```bash
# Run exactly what CI runs
pytest
ruff check src tests
black --check src tests
```

---

## Contributing Guidelines

### Branching Strategy

- `main`: Stable releases
- `develop`: Integration branch (not currently used)
- `feature/X`: New features
- `fix/X`: Bug fixes
- `copilot/X`: AI-assisted development branches

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add constitutional delegation detector
fix: resolve provenance hash validation
docs: update audit methodology guide
test: add integration tests for audit engine
chore: update dependencies
```

### Pull Request Process

1. Create feature branch
2. Make minimal, focused changes
3. Ensure all tests pass
4. Run linter and formatter
5. Update documentation
6. Submit PR with clear description
7. Address code review feedback

### Code Review Checklist

- [ ] All tests pass
- [ ] Linter reports no errors
- [ ] Code is formatted with Black
- [ ] Docstrings added for public functions
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] No secrets or sensitive data committed

---

## Additional Resources

### Documentation
- **Architecture**: `docs/ARCHITECTURE.md`
- **Audit Methodology**: `docs/audit-methodology.md`
- **Recursive Scalar Model**: `docs/recursive-scalar-model.md`
- **Phase Planning**: `docs/PHASE_PLAN.md`
- **Data Provenance**: `docs/DATA_PROVENANCE.md`

### External Links
- **GitHub Repository**: https://github.com/SynTechRev/Oraculus-DI-Auditor
- **Issue Tracker**: https://github.com/SynTechRev/Oraculus-DI-Auditor/issues
- **Ruff Documentation**: https://docs.astral.sh/ruff/
- **Pytest Documentation**: https://docs.pytest.org/

### Support

For questions or issues:
1. Check existing documentation
2. Search GitHub issues
3. Open a new issue with detailed description
4. Contact: syntechrev@gmail.com

---

## Next Steps

After completing setup:

1. **Explore the codebase**: Read `docs/ARCHITECTURE.md`
2. **Run the test suite**: `pytest -v`
3. **Try the CLI**: `python -m oraculus_di_auditor.cli --help`
4. **Read methodology**: `docs/audit-methodology.md`
5. **Contribute**: Pick an issue from the roadmap

Welcome to the Oraculus-DI-Auditor project! 🚀
