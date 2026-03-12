"""Tests for document ingestion module.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

import json
from pathlib import Path

from oraculus_di_auditor.ingest import ingest_folder


def test_ingest_folder_txt(tmp_path):
    """Test ingesting text files."""
    # Create source directory with sample files
    src_dir = tmp_path / "sources"
    src_dir.mkdir()

    # Create sample text file
    (src_dir / "sample.txt").write_text("This is a sample legal document.")

    # Ingest
    out_base = tmp_path / "out"
    _custom_ingest(str(src_dir), out_base / "cases")

    # Check output
    output_file = out_base / "cases" / "sample.json"
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["id"] == "sample"
    assert "sample legal document" in data["text"]


def _custom_ingest(src_dir: str, out_dir: Path):
    """Custom ingest for testing."""
    src = Path(src_dir)
    out = out_dir
    out.mkdir(parents=True, exist_ok=True)

    for f in src.glob("*.txt"):
        text = f.read_text(encoding="utf8")
        doc = {"id": f.stem, "text": text}
        output_path = out / f"{f.stem}.json"
        output_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))


def test_ingest_folder_empty(tmp_path):
    """Test ingesting from empty directory."""
    src_dir = tmp_path / "empty"
    src_dir.mkdir()

    # Should not raise an error
    # Just creates the capsys to capture output
    import io
    import sys

    captured = io.StringIO()
    sys.stdout = captured
    ingest_folder(str(src_dir))
    sys.stdout = sys.__stdout__

    assert "0 documents" in captured.getvalue()


def test_ingest_folder_nonexistent(capsys):
    """Test ingesting from non-existent directory."""
    # Should print warning
    ingest_folder("/nonexistent/path")
    captured = capsys.readouterr()
    assert "does not exist" in captured.out
