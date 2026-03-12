"""Tests for XML parser module.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import xml.etree.ElementTree as ET  # noqa: N817

import pytest

from oraculus_di_auditor.ingestion.xml_parser import (
    extract_text_from_xml,
    parse_xml_to_text,
)


def test_parse_simple_xml(tmp_path):
    """Test parsing simple XML file."""
    xml_content = """<?xml version="1.0"?>
<document>
    <title>Test Document</title>
    <content>This is test content.</content>
</document>
"""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)

    text = parse_xml_to_text(xml_file)

    assert "Test Document" in text
    assert "This is test content." in text


def test_parse_nested_xml(tmp_path):
    """Test parsing nested XML structure."""
    xml_content = """<?xml version="1.0"?>
<statute>
    <title>Title 42</title>
    <section>
        <number>1983</number>
        <text>Every person who, under color of any statute...</text>
        <subsection>
            <letter>a</letter>
            <text>Subsection text</text>
        </subsection>
    </section>
</statute>
"""
    xml_file = tmp_path / "statute.xml"
    xml_file.write_text(xml_content)

    text = parse_xml_to_text(xml_file)

    assert "Title 42" in text
    assert "1983" in text
    assert "Every person who" in text
    assert "Subsection text" in text


def test_parse_xml_with_attributes(tmp_path):
    """Test parsing XML with attributes (text extraction ignores attributes)."""
    xml_content = """<?xml version="1.0"?>
<law jurisdiction="federal" year="2020">
    <section id="42-1983">Text content</section>
</law>
"""
    xml_file = tmp_path / "law.xml"
    xml_file.write_text(xml_content)

    text = parse_xml_to_text(xml_file)

    # Attributes are not extracted, only text content
    assert "Text content" in text
    assert "federal" not in text
    assert "42-1983" not in text


def test_parse_xml_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        parse_xml_to_text("/nonexistent/file.xml")


def test_parse_invalid_xml(tmp_path):
    """Test error handling for invalid XML."""
    invalid_xml = tmp_path / "invalid.xml"
    invalid_xml.write_text("<unclosed>tag")

    with pytest.raises(ValueError, match="Failed to parse XML"):
        parse_xml_to_text(invalid_xml)


def test_extract_text_from_element():
    """Test extracting text from XML element."""
    root = ET.fromstring(
        """
<root>
    <a>Text A</a>
    <b>Text B</b>
    <c>
        <d>Nested D</d>
    </c>
</root>
"""
    )

    text = extract_text_from_xml(root)

    assert "Text A" in text
    assert "Text B" in text
    assert "Nested D" in text


def test_extract_text_preserves_order():
    """Test that text extraction preserves document order."""
    root = ET.fromstring(
        """
<doc>
    <p>First paragraph</p>
    <p>Second paragraph</p>
    <p>Third paragraph</p>
</doc>
"""
    )

    text = extract_text_from_xml(root)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    assert lines[0] == "First paragraph"
    assert lines[1] == "Second paragraph"
    assert lines[2] == "Third paragraph"


def test_extract_text_handles_empty_elements():
    """Test extraction with empty elements."""
    root = ET.fromstring(
        """
<doc>
    <p>Text before</p>
    <empty></empty>
    <p>Text after</p>
</doc>
"""
    )

    text = extract_text_from_xml(root)

    assert "Text before" in text
    assert "Text after" in text


def test_extract_text_handles_whitespace():
    """Test that whitespace is handled correctly."""
    root = ET.fromstring(
        """
<doc>
    <p>  Text with spaces  </p>
    <p>
        Multiline
        text
    </p>
</doc>
"""
    )

    text = extract_text_from_xml(root)

    # Whitespace should be stripped
    assert "Text with spaces" in text
    # Multiline text should be preserved
    assert "Multiline" in text
    assert "text" in text


def test_parse_real_world_usc_structure(tmp_path):
    """Test parsing USC-like XML structure."""
    usc_xml = """<?xml version="1.0"?>
<usc>
    <title number="42">
        <heading>THE PUBLIC HEALTH AND WELFARE</heading>
        <chapter number="21">
            <heading>CIVIL RIGHTS</heading>
            <section number="1983">
                <heading>Civil action for deprivation of rights</heading>
                <text>
                    Every person who, under color of any statute, ordinance,
                    regulation, custom, or usage, of any State or Territory
                    or the District of Columbia, subjects, or causes to be
                    subjected, any citizen of the United States or other
                    person within the jurisdiction thereof to the deprivation
                    of any rights, privileges, or immunities secured by the
                    Constitution and laws, shall be liable to the party
                    injured in an action at law, suit in equity, or other
                    proper proceeding for redress...
                </text>
            </section>
        </chapter>
    </title>
</usc>
"""
    xml_file = tmp_path / "title42.xml"
    xml_file.write_text(usc_xml)

    text = parse_xml_to_text(xml_file)

    assert "THE PUBLIC HEALTH AND WELFARE" in text
    assert "CIVIL RIGHTS" in text
    assert "Civil action for deprivation of rights" in text
    assert "Every person who" in text
    assert "Constitution and laws" in text
