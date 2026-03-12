#!/usr/bin/env python3
"""
Path Resolver - Utilities for resolving deeply nested file paths.

This module provides utilities for discovering and resolving paths to files
that may be deeply nested in directory structures.

Author: GitHub Copilot Agent
Date: 2025-12-08
"""

import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))


def find_file_recursive(base_dir: Path, filename: str) -> Path | None:
    """
    Recursively search for a file by name.

    Args:
        base_dir: Base directory to search from
        filename: Name of file to find

    Returns:
        Path to file if found, None otherwise
    """
    if not base_dir.exists():
        return None

    for path in base_dir.rglob(filename):
        if path.is_file():
            return path

    return None


def resolve_artifact_path(artifact_name: str, search_dirs: list[Path]) -> Path | None:
    """
    Resolve path to an artifact file by searching multiple directories.

    Args:
        artifact_name: Name of artifact file
        search_dirs: List of directories to search

    Returns:
        Resolved path if found, None otherwise
    """
    for search_dir in search_dirs:
        found = find_file_recursive(search_dir, artifact_name)
        if found:
            return found

    return None


def normalize_path(path: Path, base_dir: Path) -> str:
    """
    Normalize a path relative to base directory.

    Args:
        path: Path to normalize
        base_dir: Base directory for relative paths

    Returns:
        Normalized path string
    """
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)


def validate_paths(paths: dict[str, Path]) -> dict[str, bool]:
    """
    Validate that a set of paths exist.

    Args:
        paths: Dictionary mapping names to paths

    Returns:
        Dictionary mapping names to existence status
    """
    return {name: path.exists() for name, path in paths.items()}


def main():
    """Main entry point for path resolver."""
    print("Path Resolver module initialized")
    print("Use find_file_recursive() to locate files in directory trees")


if __name__ == "__main__":
    main()
