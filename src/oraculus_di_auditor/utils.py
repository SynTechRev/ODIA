"""Utility functions for Oraculus DI Auditor.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

import hashlib
from typing import Any


def compute_hash(content: Any) -> str:
    """Compute SHA-256 hash of content.

    Args:
        content: Content to hash (will be converted to string)

    Returns:
        Hexadecimal hash string
    """
    if isinstance(content, bytes):
        data = content
    else:
        data = str(content).encode("utf-8")

    return hashlib.sha256(data).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing unsafe characters.

    Args:
        filename: Input filename

    Returns:
        Sanitized filename
    """
    import re

    # Replace unsafe characters with underscores
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(". ")
    return safe_name or "unnamed"
