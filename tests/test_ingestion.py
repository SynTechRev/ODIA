"""Comprehensive tests for legislative ingestion."""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.document_loader import load_legislation, normalize_document


def test_load_legislation_json(tmp_path):
    """Test loading a JSON legislative document."""
    # Create a test JSON file
    test_data = {
        "title": "Test Bill",
        "content": "Test content",
        "authority": "Test Legislature",
    }
    json_file = tmp_path / "test_bill.json"
    json_file.write_text(json.dumps(test_data))

    # Load the file
    result = load_legislation(str(json_file))

    # Verify the result
    assert "title" in result
    assert result["title"] == "Test Bill"
    assert "provenance" in result
    assert "hash" in result["provenance"]
    assert "verified_on" in result["provenance"]


def test_load_legislation_text(tmp_path):
    """Test loading a text legislative document."""
    # Create a test text file
    test_content = "This is a test legislative document."
    text_file = tmp_path / "test_bill.txt"
    text_file.write_text(test_content)

    # Load the file
    result = load_legislation(str(text_file))

    # Verify the result
    assert "raw_text" in result
    assert result["raw_text"] == test_content
    assert "provenance" in result
    assert len(result["provenance"]["hash"]) == 64  # SHA-256 hex length


def test_load_legislation_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    try:
        load_legislation("/nonexistent/path/file.json")
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError as e:
        assert "No file found at" in str(e)


def test_load_legislation_unsupported_format(tmp_path):
    """Test that ValueError is raised for unsupported formats."""
    # Create a test file with unsupported extension
    test_file = tmp_path / "test.xyz"
    test_file.write_text("test content")

    try:
        load_legislation(str(test_file))
        raise AssertionError("Expected ValueError")
    except ValueError as e:
        assert "Unsupported file format" in str(e)


def test_load_legislation_pdf(tmp_path):
    """Test loading a PDF legislative document."""
    # Skip if pypdf is not available
    try:
        from pypdf import PdfWriter
    except ImportError:
        import pytest

        pytest.skip("pypdf not available")
        return

    # Create a simple PDF
    pdf_file = tmp_path / "test_bill.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)

    with open(pdf_file, "wb") as f:
        writer.write(f)

    # Load the file
    result = load_legislation(str(pdf_file))

    # Verify the result
    assert "raw_text" in result or "metadata" in result
    assert "provenance" in result


def test_normalize_document_with_title():
    """Test normalizing a document with title."""
    data = {
        "title": "Test Act 2023",
        "document_type": "act",
        "authority": "Federal Government",
        "jurisdiction": "United States",
    }

    normalized = normalize_document(data)

    assert "document_id" in normalized
    assert normalized["title"] == "Test Act 2023"
    assert normalized["document_type"] == "act"
    assert normalized["authority"] == "Federal Government"
    assert normalized["jurisdiction"] == "United States"
    assert "provenance" in normalized


def test_normalize_document_with_raw_text():
    """Test normalizing a document with raw text."""
    data = {
        "title": "Simple Bill",
        "raw_text": "Section 1: This is the content.",
    }

    normalized = normalize_document(data)

    assert "sections" in normalized
    assert len(normalized["sections"]) == 1
    assert normalized["sections"][0]["section_id"] == "raw"
    assert normalized["sections"][0]["content"] == "Section 1: This is the content."


def test_normalize_document_with_sections():
    """Test normalizing a document with structured sections."""
    data = {
        "title": "Structured Act",
        "sections": [
            {"section_id": "1", "title": "Definitions", "content": "Terms defined..."},
            {"section_id": "2", "title": "Provisions", "content": "Rules apply..."},
        ],
    }

    normalized = normalize_document(data)

    assert "sections" in normalized
    assert len(normalized["sections"]) == 2
    assert normalized["sections"][0]["section_id"] == "1"
    assert normalized["sections"][1]["title"] == "Provisions"


def test_normalize_document_with_references():
    """Test normalizing a document with cross-references."""
    data = {
        "title": "Amendment Act",
        "references": [
            {
                "document_id": "act-2020-001",
                "reference_type": "amends",
                "section": "Section 3",
            }
        ],
    }

    normalized = normalize_document(data)

    assert "references" in normalized
    assert len(normalized["references"]) == 1
    assert normalized["references"][0]["document_id"] == "act-2020-001"
    assert normalized["references"][0]["reference_type"] == "amends"


def test_normalize_document_custom_id():
    """Test normalizing with a custom document ID."""
    data = {"title": "Custom ID Document"}

    normalized = normalize_document(data, document_id="custom-doc-123")

    assert normalized["document_id"] == "custom-doc-123"


def test_normalize_document_deterministic_id():
    """Test that document ID generation is deterministic."""
    data = {"title": "Deterministic Test", "content": "Same content"}

    normalized1 = normalize_document(data)
    normalized2 = normalize_document(data)

    assert normalized1["document_id"] == normalized2["document_id"]


def test_load_and_normalize_pipeline(tmp_path):
    """Test complete pipeline: load then normalize."""
    # Create test document
    test_data = {
        "title": "Pipeline Test Act",
        "document_type": "act",
        "authority": "Test Authority",
        "sections": [{"section_id": "1", "content": "Test content"}],
    }
    json_file = tmp_path / "pipeline_test.json"
    json_file.write_text(json.dumps(test_data))

    # Load document
    loaded = load_legislation(str(json_file))

    # Normalize document
    normalized = normalize_document(loaded, document_id="pipeline-test-001")

    # Verify pipeline
    assert normalized["document_id"] == "pipeline-test-001"
    assert normalized["title"] == "Pipeline Test Act"
    assert "provenance" in normalized
    assert "hash" in normalized["provenance"]
    assert normalized["sections"][0]["section_id"] == "1"
