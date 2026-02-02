"""
Validation Utilities - Input validation with proper error handling

This module provides validation functions that raise exceptions or return
error indicators instead of silently returning default values.
"""

from typing import Optional, Tuple


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


def validate_duration_ms(duration_ms: int, source: str = "unknown") -> int:
    """
    Validate duration value.

    Args:
        duration_ms: Duration to validate
        source: Description of source for error messages

    Returns:
        Validated duration (unchanged if valid)

    Raises:
        ValidationError: If duration is negative
    """
    if duration_ms < 0:
        raise ValidationError(f"Invalid duration {duration_ms}ms from {source}")
    return duration_ms


def validate_fps(fps: float, source: str = "unknown") -> float:
    """
    Validate frames per second value.

    Args:
        fps: FPS value to validate
        source: Description of source for error messages

    Returns:
        Validated fps (unchanged if valid)

    Raises:
        ValidationError: If fps is <= 0
    """
    if fps <= 0:
        raise ValidationError(f"Invalid frame rate {fps} fps from {source}")
    return fps


def safe_duration_from_mediainfo(
    info: dict,
    source_path: str
) -> Tuple[Optional[int], Optional[str]]:
    """
    Safely extract duration from mediainfo dict.

    Returns a tuple of (duration_ms, error_message) instead of silently
    returning 0 on failure.

    Args:
        info: Dict from mediainfo()
        source_path: Path to source file for error messages

    Returns:
        Tuple of (duration_ms or None, error_message or None)
        - (duration_ms, None) on success
        - (None, error_message) on failure
    """
    try:
        duration_str = info.get('duration')
        if duration_str is None:
            return (None, f"No duration metadata in {source_path}")

        duration_ms = int(float(duration_str) * 1000)
        return (duration_ms, None)

    except (ValueError, TypeError) as e:
        return (None, f"Failed to parse duration from {source_path}: {e}")
