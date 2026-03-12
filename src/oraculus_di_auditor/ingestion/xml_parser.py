"""XML Parser for Legal Documents.

Converts legal XML documents (USC, CFR, etc.) into normalized plain text.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

from pathlib import Path


def parse_xml_to_text(file_path: str | Path) -> str:
    """Parse XML file and extract text content.

    Args:
        file_path: Path to the XML file

    Returns:
        Extracted text content as a string

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file cannot be parsed as XML
    """
    try:
        from lxml import etree  # type: ignore[reportMissingTypeStubs]
    except ImportError:
        # Fallback to built-in xml.etree.ElementTree if lxml is not available
        import xml.etree.ElementTree as etree  # noqa: N813

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"XML file not found: {file_path}")

    try:
        tree = etree.parse(str(file_path))
        return extract_text_from_xml(tree.getroot())
    except Exception as e:
        raise ValueError(f"Failed to parse XML file {file_path}: {e}") from e


def extract_text_from_xml(element) -> str:
    """Extract all text content from an XML element tree.

    Args:
        element: XML element (root or subtree)

    Returns:
        Concatenated text content with line breaks
    """
    texts = []

    # Get text from current element
    if element.text and element.text.strip():
        texts.append(element.text.strip())

    # Recursively get text from child elements
    for child in element:
        child_text = extract_text_from_xml(child)
        if child_text:
            texts.append(child_text)

        # Get tail text (text after the child element)
        if child.tail and child.tail.strip():
            texts.append(child.tail.strip())

    return "\n".join(texts)
