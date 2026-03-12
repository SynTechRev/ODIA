"""Tests for legal document schema validation.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import json
from pathlib import Path

import jsonschema  # type: ignore[reportMissingTypeStubs]
import pytest


@pytest.fixture
def legal_schema():
    """Load the legal document schema."""
    schema_path = Path(__file__).parent.parent / "schemas" / "legal_schema.json"
    with open(schema_path) as f:
        return json.load(f)


def test_schema_exists(legal_schema):
    """Test that the schema file exists and is valid JSON."""
    assert legal_schema is not None
    assert isinstance(legal_schema, dict)
    assert legal_schema["title"] == "LegalDocument"


def test_schema_required_fields(legal_schema):
    """Test that schema has correct required fields."""
    required = legal_schema["required"]
    assert "id" in required
    assert "title" in required
    assert "jurisdiction" in required
    assert "source" in required
    assert "ingest_timestamp" in required
    assert "text" in required


def test_valid_document(legal_schema):
    """Test that a valid document passes schema validation."""
    valid_doc = {
        "id": "usc-title-1-section-1",
        "title": "U.S. Code Title 1 Section 1",
        "jurisdiction": "federal",
        "source": "data/sources/usc_title_1.txt",
        "source_url": "https://uscode.house.gov/view.xhtml?req=title:1",
        "version_date": "2024-01-01",
        "ingest_timestamp": "2025-11-13T06:00:00Z",
        "checksum": "abc123def456",
        "citations": ["1 U.S.C. § 1"],
        "metadata": {
            "processor_version": "0.1.0",
            "transformations": ["normalize", "chunk"],
        },
        "text": "Words denoting number, gender, and so forth.",
    }

    # Should not raise an exception
    jsonschema.validate(instance=valid_doc, schema=legal_schema)


def test_missing_required_field(legal_schema):
    """Test that missing required field fails validation."""
    invalid_doc = {
        "id": "test-doc",
        "title": "Test Document",
        # Missing "jurisdiction" - required field
        "source": "test.txt",
        "ingest_timestamp": "2025-11-13T06:00:00Z",
        "text": "Sample text",
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_doc, schema=legal_schema)


def test_minimal_valid_document(legal_schema):
    """Test that a document with only required fields is valid."""
    minimal_doc = {
        "id": "minimal-doc",
        "title": "Minimal Document",
        "jurisdiction": "unknown",
        "source": "test.txt",
        "ingest_timestamp": "2025-11-13T06:00:00Z",
        "text": "Minimal text content",
    }

    # Should not raise an exception
    jsonschema.validate(instance=minimal_doc, schema=legal_schema)


def test_with_optional_fields(legal_schema):
    """Test that optional fields are accepted."""
    doc_with_optional = {
        "id": "doc-with-optional",
        "title": "Document with Optional Fields",
        "jurisdiction": "california",
        "source": "ca_code.txt",
        "ingest_timestamp": "2025-11-13T06:00:00Z",
        "text": "Text content",
        "source_url": "https://leginfo.legislature.ca.gov/",
        "version_date": "2024-06-15",
        "checksum": "sha256hash",
        "citations": ["Cal. Civ. Code § 1234"],
        "metadata": {"notes": "Important document"},
    }

    # Should not raise an exception
    jsonschema.validate(instance=doc_with_optional, schema=legal_schema)


def test_invalid_type(legal_schema):
    """Test that wrong type for a field fails validation."""
    invalid_type_doc = {
        "id": "invalid-type",
        "title": "Invalid Type Document",
        "jurisdiction": "federal",
        "source": "test.txt",
        "ingest_timestamp": "2025-11-13T06:00:00Z",
        "text": "Text content",
        "citations": "not-an-array",  # Should be array, not string
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_type_doc, schema=legal_schema)
