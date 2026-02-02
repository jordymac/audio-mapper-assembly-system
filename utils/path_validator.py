#!/usr/bin/env python3
"""
Path Validator - Security utilities for file path validation
Prevents path traversal attacks and restricts file access to allowed directories
"""

import os
from pathlib import Path
from typing import Tuple, Optional, List


class PathValidationError(Exception):
    """Raised when path validation fails"""
    pass


# Default allowed directories (relative to project root)
DEFAULT_ALLOWED_DIRS = [
    ".",  # Project root
    "output",
    "generated_audio",
    "temp",
    "template_maps",
]


def get_project_root() -> Path:
    """Get the project root directory (where audio_mapper.py is located)"""
    # Walk up from this file to find project root
    current = Path(__file__).resolve().parent.parent
    return current


def is_safe_path(filepath: str, allowed_dirs: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Check if a file path is safe (within allowed directories, no traversal).

    Args:
        filepath: The path to validate
        allowed_dirs: List of allowed directory paths (relative to project root).
                     If None, uses DEFAULT_ALLOWED_DIRS.

    Returns:
        Tuple of (is_safe, reason):
        - is_safe: True if path is safe, False otherwise
        - reason: Empty string if safe, explanation if not safe
    """
    if allowed_dirs is None:
        allowed_dirs = DEFAULT_ALLOWED_DIRS

    try:
        # Resolve the path to absolute, following symlinks
        abs_path = Path(filepath).resolve()
        project_root = get_project_root()

        # Check for path traversal patterns in the original string
        if ".." in filepath:
            return False, "Path contains traversal pattern '..'"

        # Check if path is within any allowed directory
        for allowed_dir in allowed_dirs:
            if allowed_dir == ".":
                allowed_path = project_root
            else:
                allowed_path = (project_root / allowed_dir).resolve()

            try:
                # Check if abs_path is relative to (inside) allowed_path
                abs_path.relative_to(allowed_path)
                return True, ""
            except ValueError:
                # Path is not inside this allowed directory
                continue

        # Path is not in any allowed directory
        return False, f"Path is outside allowed directories: {', '.join(allowed_dirs)}"

    except Exception as e:
        return False, f"Path validation error: {str(e)}"


def validate_path(filepath: str, allowed_dirs: Optional[List[str]] = None, must_exist: bool = False) -> str:
    """
    Validate a file path and return the resolved absolute path.

    Args:
        filepath: The path to validate
        allowed_dirs: List of allowed directory paths (relative to project root).
                     If None, uses DEFAULT_ALLOWED_DIRS.
        must_exist: If True, also check that the file exists

    Returns:
        The resolved absolute path if valid

    Raises:
        PathValidationError: If path is invalid or outside allowed directories
    """
    is_safe, reason = is_safe_path(filepath, allowed_dirs)

    if not is_safe:
        raise PathValidationError(f"Invalid file path: {reason}\nPath: {filepath}")

    abs_path = Path(filepath).resolve()

    if must_exist and not abs_path.exists():
        raise PathValidationError(f"File does not exist: {filepath}")

    return str(abs_path)


def validate_import_path(filepath: str) -> str:
    """
    Validate a path for JSON import operations.
    Allows reading from anywhere on the filesystem for user convenience,
    but warns about suspicious paths.

    Args:
        filepath: The path to validate

    Returns:
        The resolved absolute path

    Raises:
        PathValidationError: If path contains traversal patterns
    """
    # For imports, we're more permissive - user might import from Downloads, Desktop, etc.
    # But we still block explicit traversal patterns
    if ".." in filepath:
        raise PathValidationError(
            f"Invalid file path: Path contains traversal pattern '..'\n"
            f"Path: {filepath}\n\n"
            f"Please use an absolute path or a path without '..' components."
        )

    return str(Path(filepath).resolve())


def validate_export_path(filepath: str) -> str:
    """
    Validate a path for export operations.
    Restricts exports to project output directories for safety.

    Args:
        filepath: The path to validate

    Returns:
        The resolved absolute path

    Raises:
        PathValidationError: If path is outside allowed export directories
    """
    export_dirs = [".", "output", "template_maps", "generated_audio"]
    return validate_path(filepath, allowed_dirs=export_dirs, must_exist=False)
