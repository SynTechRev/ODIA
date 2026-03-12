"""Test module for legislative loader."""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_load_legislation_json(tmp_path):
    """Test loading a JSON legislative document."""
    from oraculus.ingestion.legislative_loader import load_legislation

    # Create a test JSON file
    test_data = {"title": "Test Bill", "content": "Test content"}
    json_file = tmp_path / "test_bill.json"
    json_file.write_text(json.dumps(test_data))

    # Load the file
    result = load_legislation(str(json_file))

    # Verify the result
    assert result["title"] == "Test Bill"
    assert result["content"] == "Test content"
    # Verify provenance was added
    assert "provenance" in result
    assert "hash" in result["provenance"]
    assert "verified_on" in result["provenance"]


def test_load_legislation_text(tmp_path):
    """Test loading a text legislative document."""
    from oraculus.ingestion.legislative_loader import load_legislation

    # Create a test text file
    test_content = "This is a test legislative document."
    text_file = tmp_path / "test_bill.txt"
    text_file.write_text(test_content)

    # Load the file
    result = load_legislation(str(text_file))

    # Verify the result
    assert "raw_text" in result
    assert result["raw_text"] == test_content


def test_load_legislation_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    from oraculus.ingestion.legislative_loader import load_legislation

    try:
        load_legislation("/nonexistent/path/file.json")
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError as e:
        assert "No file found at" in str(e)
