"""
Marker Utilities - Consistent marker handling across dict and object types

This module provides utilities to handle markers consistently regardless of
whether they are dicts or Marker objects. This eliminates scattered isinstance
checks throughout the codebase.
"""

from typing import Union, Dict, Any, List, Optional


def normalize_marker(marker: Union[dict, Any]) -> dict:
    """
    Convert marker to dict format for consistent handling.

    Args:
        marker: Either a dict or Marker object

    Returns:
        Dict representation of marker
    """
    if isinstance(marker, dict):
        return marker

    # Convert Marker object to dict
    return {
        'name': getattr(marker, 'name', ''),
        'type': getattr(marker, 'type', 'sfx'),
        'time_ms': getattr(marker, 'time_ms', 0),
        'duration_ms': getattr(marker, 'duration_ms', 0),
        'versions': getattr(marker, 'versions', []),
        'current_version': getattr(marker, 'current_version', 0),
        'asset_file': getattr(marker, 'asset_file', ''),
        'prompt_data': getattr(marker, 'prompt_data', {}),
        'assigned_track': getattr(marker, 'assigned_track', None),
        'assigned_channels': getattr(marker, 'assigned_channels', []),
    }


def normalize_markers(markers: List[Union[dict, Any]]) -> List[dict]:
    """
    Normalize a list of markers to dicts.

    Args:
        markers: List of dict or Marker objects

    Returns:
        List of dict markers
    """
    return [normalize_marker(m) for m in markers]


def get_marker_attr(marker: Union[dict, Any], key: str, default: Any = None) -> Any:
    """
    Get attribute from marker regardless of type.

    This is the primary utility for accessing marker properties without
    needing isinstance checks at every access point.

    Args:
        marker: Dict or Marker object
        key: Attribute name
        default: Default value if not found

    Returns:
        Attribute value or default
    """
    if isinstance(marker, dict):
        return marker.get(key, default)
    return getattr(marker, key, default)


def set_marker_attr(marker: Union[dict, Any], key: str, value: Any) -> None:
    """
    Set attribute on marker regardless of type.

    Args:
        marker: Dict or Marker object
        key: Attribute name
        value: Value to set
    """
    if isinstance(marker, dict):
        marker[key] = value
    else:
        setattr(marker, key, value)


def get_current_version_data(marker: Union[dict, Any]) -> Optional[dict]:
    """
    Get the current version data from a marker.

    Args:
        marker: Dict or Marker object

    Returns:
        Version dict for current version, or None if not found
    """
    versions = get_marker_attr(marker, 'versions', [])
    current_version = get_marker_attr(marker, 'current_version', 1)

    if not versions:
        return None

    return next((v for v in versions if v.get('version') == current_version), None)


def get_marker_audio_path(marker: Union[dict, Any]) -> Optional[str]:
    """
    Get the audio file path for a marker's current version.

    Args:
        marker: Dict or Marker object

    Returns:
        Asset file path or None
    """
    version_data = get_current_version_data(marker)
    if version_data:
        return version_data.get('asset_file')

    # Fallback to direct asset_file attribute
    return get_marker_attr(marker, 'asset_file')
