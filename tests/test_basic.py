"""Test module for Oraculus DI Auditor."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_import():
    """Test that the package can be imported."""
    import oraculus

    assert oraculus.__version__ == "0.1.0"


def test_package_structure():
    """Test that basic package structure exists."""
    from pathlib import Path

    project_root = Path(__file__).parent.parent

    # Check required directories exist
    assert (project_root / "src" / "oraculus").exists()
    assert (project_root / "tests").exists()
    assert (project_root / "docs").exists()
    assert (project_root / "schemas").exists()
    assert (project_root / "config").exists()
    assert (project_root / "data").exists()
    assert (project_root / ".github" / "workflows").exists()
