#!/usr/bin/env python3
"""
File Handler - JSON Import/Export for Template Maps
Handles reading and writing marker data to/from JSON files
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class FileHandler:
    """
    Handles import/export of marker templates to/from JSON files

    Provides:
    - Import markers from JSON with validation
    - Export markers to JSON with proper formatting
    - Template metadata handling
    - Error handling and validation
    """

    @staticmethod
    def import_from_json(filepath: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Import template data from JSON file

        Args:
            filepath: Path to JSON file

        Returns:
            Tuple of (success, data, error_message)
            - success: True if import succeeded
            - data: Dictionary with template data if successful, None otherwise
            - error_message: Error description if failed, None otherwise
        """
        try:
            # Load JSON file
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Validate required fields
            if "markers" not in data:
                return False, None, "Invalid JSON: 'markers' field missing"

            # Validate duration
            duration_ms = data.get("duration_ms", 0)
            if duration_ms < 0:
                # Set to 0 but allow import to continue
                data["duration_ms"] = 0

            # Validate marker times
            markers = data["markers"]
            for i, marker in enumerate(markers):
                if marker.get("time_ms", 0) < 0:
                    print(f"WARNING: Marker {i} has negative time ({marker.get('time_ms')}ms), setting to 0")
                    marker["time_ms"] = 0

            return True, data, None

        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON file: {str(e)}"
        except FileNotFoundError:
            return False, None, f"File not found: {filepath}"
        except Exception as e:
            return False, None, f"Failed to import: {str(e)}"

    @staticmethod
    def export_to_json(
        filepath: str,
        markers: List[Dict[str, Any]],
        template_id: str = "TEMPLATE",
        template_name: str = "Untitled",
        duration_ms: int = 0
    ) -> Tuple[bool, Optional[str]]:
        """
        Export markers to JSON file

        Args:
            filepath: Path to save JSON file
            markers: List of marker dictionaries
            template_id: Template identifier (default: "TEMPLATE")
            template_name: Template name (default: "Untitled")
            duration_ms: Total duration in milliseconds (default: 0)

        Returns:
            Tuple of (success, error_message)
            - success: True if export succeeded
            - error_message: Error description if failed, None otherwise
        """
        try:
            # Build JSON structure
            template = {
                "template_id": template_id or "TEMPLATE",
                "template_name": template_name or "Untitled",
                "duration_ms": duration_ms,
                "markers": markers
            }

            # Ensure parent directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(filepath, 'w') as f:
                json.dump(template, f, indent=2)

            print(f"✓ Exported {len(markers)} markers to {filepath}")
            return True, None

        except Exception as e:
            return False, f"Failed to export: {str(e)}"

    @staticmethod
    def migrate_marker_to_new_format(marker: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert old marker format (prompt string) to new format (prompt_data)

        Args:
            marker: Marker dictionary (potentially in old format)

        Returns:
            Marker dictionary in new format
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
            # Default fallback
            prompt_data = {"description": old_prompt}

        # Create new marker without "prompt" field
        new_marker = marker.copy()
        if "prompt" in new_marker:
            del new_marker["prompt"]
        new_marker["prompt_data"] = prompt_data

        return new_marker

    @staticmethod
    def migrate_marker_to_version_format(marker: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate marker to include version tracking format

        Args:
            marker: Marker dictionary

        Returns:
            Marker dictionary with version tracking
        """
        from datetime import datetime

        # If already has versions, return as-is
        if "versions" in marker:
            return marker

        # Ensure prompt_data exists (call migrate_marker_to_new_format first if needed)
        if "prompt_data" not in marker:
            marker = FileHandler.migrate_marker_to_new_format(marker)

        prompt_data = marker.get("prompt_data", FileHandler._create_default_prompt_data(marker.get("type", "sfx")))
        asset_file = marker.get("asset_file", "ASSET_00000.mp3")

        # Update asset_file to include _v1 if it doesn't have version suffix
        if "_v" not in asset_file:
            # Insert _v1 before .mp3 extension
            base_name = asset_file.rsplit(".", 1)[0]
            extension = asset_file.rsplit(".", 1)[1] if "." in asset_file else "mp3"
            asset_file = f"{base_name}_v1.{extension}"

        # Create initial version object
        version_obj = {
            "version": 1,
            "asset_file": asset_file,
            "asset_id": marker.get("asset_id", None),
            "created_at": datetime.now().isoformat(),
            "status": marker.get("status", "not yet generated"),
            "prompt_data_snapshot": prompt_data.copy()
        }

        # Update marker with version format
        new_marker = marker.copy()
        new_marker["asset_file"] = asset_file
        new_marker["current_version"] = 1
        new_marker["versions"] = [version_obj]

        return new_marker

    @staticmethod
    def _create_default_prompt_data(marker_type: str) -> Dict[str, Any]:
        """Create empty but valid prompt_data structure for a given marker type"""
        if marker_type == "sfx":
            return {"description": ""}
        elif marker_type == "voice":
            return {"voice_profile": "", "text": ""}
        elif marker_type == "music":
            return {"positiveGlobalStyles": [], "negativeGlobalStyles": [], "sections": []}
        else:
            return {"description": ""}

    @staticmethod
    def validate_template_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate template data structure

        Args:
            data: Template data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if "markers" not in data:
            return False, "Missing required field: 'markers'"

        if not isinstance(data["markers"], list):
            return False, "'markers' must be a list"

        # Validate each marker
        for i, marker in enumerate(data["markers"]):
            if not isinstance(marker, dict):
                return False, f"Marker {i} is not a dictionary"

            # Check required marker fields
            if "time_ms" not in marker:
                return False, f"Marker {i} missing 'time_ms'"
            if "type" not in marker:
                return False, f"Marker {i} missing 'type'"

            # Validate marker type
            valid_types = ["sfx", "voice", "music", "music_control"]
            if marker["type"] not in valid_types:
                return False, f"Marker {i} has invalid type: {marker['type']}"

        return True, None
