"""
Marker Version Manager

Handles version management and format migration for audio markers.
Extracted from AudioMapperGUI as part of Sprint 2 refactoring.

Key Responsibilities:
- Migrate old marker format (prompt string) to new format (prompt_data)
- Manage marker versions (create, rollback, retrieve)
- Ensure version data structure integrity
"""

from datetime import datetime
from typing import Dict, Any, Optional, List


class MarkerVersionManager:
    """
    Manages marker versioning and format migrations

    This class provides stateless operations for:
    - Format migration (old -> new marker structure)
    - Version management (add, rollback, retrieve)
    - Version format migration (ensure version structure exists)
    """

    @staticmethod
    def migrate_marker_to_new_format(marker: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert old marker format (prompt string) to new format (prompt_data)

        Args:
            marker: Marker dict in old or new format

        Returns:
            Marker dict in new format with prompt_data
        """
        # If already new format, return as-is
        if "prompt_data" in marker:
            return marker

        # Old format has "prompt" as string
        old_prompt = marker.get("prompt", "")
        marker_type = marker.get("type", "sfx")

        # Create new format based on type
        if marker_type == "sfx":
            prompt_data = {
                "description": old_prompt
            }
        elif marker_type == "voice":
            # Try to split old prompt into profile and text
            # Format assumption: "Profile: text" or just use as text
            if ":" in old_prompt:
                parts = old_prompt.split(":", 1)
                prompt_data = {
                    "voice_profile": parts[0].strip(),
                    "text": parts[1].strip()
                }
            else:
                prompt_data = {
                    "voice_profile": "",
                    "text": old_prompt
                }
        elif marker_type == "music":
            # Old prompt becomes positive global style
            prompt_data = {
                "positiveGlobalStyles": [old_prompt] if old_prompt else [],
                "negativeGlobalStyles": [],
                "sections": []
            }
        else:
            # Default: treat as description
            prompt_data = {
                "description": old_prompt
            }

        # Update marker with new format
        new_marker = marker.copy()
        del new_marker["prompt"]  # Remove old field
        new_marker["prompt_data"] = prompt_data
        new_marker["asset_id"] = marker.get("asset_id", None)
        new_marker["status"] = marker.get("status", "not yet generated")

        return new_marker

    @staticmethod
    def get_current_version_data(marker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the current version object from a marker

        Args:
            marker: Marker dict with versions

        Returns:
            Version object for the current active version, or None if no versions exist
        """
        if "versions" not in marker or not marker["versions"]:
            return None

        current_version = marker.get("current_version", 1)

        # Find version object matching current_version
        for version_obj in marker["versions"]:
            if version_obj["version"] == current_version:
                return version_obj

        # Fallback to latest version if current not found
        return marker["versions"][-1] if marker["versions"] else None

    @staticmethod
    def add_new_version(marker: Dict[str, Any], prompt_data: Dict[str, Any]) -> int:
        """
        Create a new version for a marker

        Args:
            marker: The marker dict to add version to
            prompt_data: The prompt_data to use for this version

        Returns:
            The new version number
        """
        # Initialize versions list if it doesn't exist
        if "versions" not in marker:
            marker["versions"] = []

        # Get next version number
        if marker["versions"]:
            next_version = max(v["version"] for v in marker["versions"]) + 1
        else:
            next_version = 1

        # Generate new asset filename with version
        type_prefix_map = {
            "music": "MUS",
            "sfx": "SFX",
            "voice": "VOX",
            "music_control": "CTRL"
        }

        prefix = type_prefix_map.get(marker["type"], "ASSET")
        marker_count = int(marker.get("asset_slot", "0").split("_")[-1])
        asset_file = f"{prefix}_{marker_count:05d}_v{next_version}.mp3"

        # Create version object
        version_obj = {
            "version": next_version,
            "asset_file": asset_file,
            "asset_id": None,  # Will be set when generated via API
            "created_at": datetime.now().isoformat(),
            "status": "not yet generated",
            "prompt_data_snapshot": prompt_data.copy()  # Deep copy of prompt_data
        }

        # Add to versions list
        marker["versions"].append(version_obj)

        # Update current_version
        marker["current_version"] = next_version

        # Update top-level fields for backward compatibility
        marker["asset_file"] = asset_file
        marker["prompt_data"] = prompt_data.copy()
        marker["status"] = "not yet generated"
        marker["asset_id"] = None

        return next_version

    @staticmethod
    def rollback_to_version(marker: Dict[str, Any], version_num: int) -> bool:
        """
        Roll back a marker to a specific version

        Args:
            marker: The marker dict
            version_num: The version number to roll back to

        Returns:
            True if successful, False if version not found
        """
        if "versions" not in marker or not marker["versions"]:
            return False

        # Find the version object
        target_version = None
        for version_obj in marker["versions"]:
            if version_obj["version"] == version_num:
                target_version = version_obj
                break

        if not target_version:
            return False

        # Update current_version
        marker["current_version"] = version_num

        # Update top-level fields from this version
        marker["asset_file"] = target_version["asset_file"]
        marker["asset_id"] = target_version["asset_id"]
        marker["status"] = target_version["status"]
        marker["prompt_data"] = target_version["prompt_data_snapshot"].copy()

        return True

    @staticmethod
    def migrate_marker_to_version_format(marker: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate a marker to the new version-based format

        Handles both old format (no versions) and ensures version structure exists

        Args:
            marker: Marker dict to migrate

        Returns:
            Marker dict with version structure
        """
        # If already has versions, just ensure it's valid
        if "versions" in marker and marker["versions"]:
            # Ensure current_version exists
            if "current_version" not in marker:
                marker["current_version"] = marker["versions"][-1]["version"]
            return marker

        # Create initial version from current marker state
        prompt_data = marker.get(
            "prompt_data",
            MarkerVersionManager.create_default_prompt_data(marker.get("type", "sfx"))
        )
        asset_file = marker.get("asset_file", "ASSET_00000.mp3")

        # Update asset_file to include _v1 if it doesn't have version suffix
        if "_v" not in asset_file:
            # Insert _v1 before .mp3 extension
            base_name = asset_file.rsplit(".", 1)[0]
            extension = asset_file.rsplit(".", 1)[1] if "." in asset_file else "mp3"
            asset_file = f"{base_name}_v1.{extension}"

        version_obj = {
            "version": 1,
            "asset_file": asset_file,
            "asset_id": marker.get("asset_id", None),
            "created_at": datetime.now().isoformat(),
            "status": marker.get("status", "not yet generated"),
            "prompt_data_snapshot": prompt_data.copy()
        }

        # Add version structure to marker
        marker["versions"] = [version_obj]
        marker["current_version"] = 1
        marker["asset_file"] = asset_file

        # Ensure all required fields exist
        if "prompt_data" not in marker:
            marker["prompt_data"] = prompt_data
        if "status" not in marker:
            marker["status"] = "not yet generated"
        if "asset_id" not in marker:
            marker["asset_id"] = None

        return marker

    @staticmethod
    def create_default_prompt_data(marker_type: str) -> Dict[str, Any]:
        """
        Create empty but valid prompt_data structure for a given marker type

        Args:
            marker_type: Type of marker ("sfx", "voice", "music", etc.)

        Returns:
            Empty but valid prompt_data dict for the marker type
        """
        if marker_type == "sfx":
            return {"description": ""}

        elif marker_type == "voice":
            return {
                "voice_profile": "",
                "text": ""
            }

        elif marker_type == "music":
            return {
                "positiveGlobalStyles": [],
                "negativeGlobalStyles": [],
                "sections": []
            }

        else:
            # Default fallback
            return {"description": ""}
