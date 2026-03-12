"""Shared utility functions for analysis modules."""

from __future__ import annotations

from typing import Any


def extract_text_content(doc: dict[str, Any]) -> str:
    """Extract all text content from document for analysis.

    Args:
        doc: Normalized document dict

    Returns:
        Concatenated text content from all sections
    """
    text_parts = []

    # Extract from raw_text field
    if "raw_text" in doc and isinstance(doc["raw_text"], str):
        text_parts.append(doc["raw_text"])

    # Extract from sections
    sections = doc.get("sections", [])
    if isinstance(sections, list):
        for section in sections:
            if isinstance(section, dict) and "content" in section:
                text_parts.append(str(section["content"]))

    return " ".join(text_parts)
