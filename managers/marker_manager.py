#!/usr/bin/env python3
"""
Marker Manager - High-level marker operations and coordination

Coordinates marker creation, deletion, and modifications.
Integrates marker_repository, history_manager, and version_manager.
Extracted from AudioMapperGUI as part of Sprint 3.3 refactoring.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from core.marker_repository import MarkerRepository
from managers.history_manager import HistoryManager
from managers.version_manager import MarkerVersionManager
from core.commands import AddMarkerCommand, EditMarkerCommand, DeleteMarkerCommand, MoveMarkerCommand


class MarkerManager:
    """
    High-level marker management coordinator.

    Responsibilities:
    - Create markers with proper initialization (asset slots, versions)
    - Execute marker operations via command pattern (add, edit, delete, nudge)
    - Coordinate between repository, history, and version manager
    - Provide callbacks for UI coordination
    """

    def __init__(
        self,
        marker_repository: MarkerRepository,
        history_manager: HistoryManager,
        get_current_time: Callable[[], int],
        get_duration: Callable[[], int],
        is_video_loaded: Callable[[], bool]
    ):
        """
        Initialize the marker manager.

        Args:
            marker_repository: Repository for marker CRUD operations
            history_manager: History manager for undo/redo
            get_current_time: Callback to get current timeline position (ms)
            get_duration: Callback to get total timeline duration (ms)
            is_video_loaded: Callback to check if video/timeline is loaded
        """
        self.marker_repository = marker_repository
        self.history = history_manager
        self.get_current_time = get_current_time
        self.get_duration = get_duration
        self.is_video_loaded = is_video_loaded

        # Type prefix mapping for asset file generation
        self._type_prefix_map = {
            "music": "MUS",
            "sfx": "SFX",
            "voice": "VOX",
            "music_control": "CTRL"
        }

    def create_marker_of_type(self, marker_type: str) -> Optional[Dict[str, Any]]:
        """
        Create a new marker with proper initialization.

        Creates marker with:
        - Asset slot and base filename
        - Empty but valid prompt_data structure
        - NO versions yet (versions created on first generation)

        Args:
            marker_type: Type of marker ("sfx", "voice", "music", etc.)

        Returns:
            Marker dictionary or None if creation failed
        """
        if not self.is_video_loaded():
            return None

        # Generate asset slot and base filename (version will be added during generation)
        prefix = self._type_prefix_map.get(marker_type, "ASSET")
        markers = self.marker_repository.markers
        marker_count = len([m for m in markers if m["type"] == marker_type])
        asset_slot = f"{marker_type}_{marker_count}"
        asset_file = f"{prefix}_{marker_count:05d}.mp3"  # Base filename, no version yet

        # Create empty but valid prompt_data structure
        prompt_data = MarkerVersionManager.create_default_prompt_data(marker_type)

        current_time = self.get_current_time()

        marker = {
            "time_ms": current_time,
            "type": marker_type,
            "name": "",  # Custom marker name (to be filled in editor)
            "prompt_data": prompt_data,
            "asset_slot": asset_slot,
            "asset_file": asset_file,  # Base filename
            "asset_id": None,
            "status": "not yet generated",
            "current_version": 0,  # 0 indicates no versions yet
            "versions": []  # Empty - versions created when audio is generated
        }

        return marker

    def add_marker_by_type(self, marker_type: str) -> Optional[int]:
        """
        Create and add a new marker of the specified type.

        Args:
            marker_type: Type of marker to create

        Returns:
            Index of newly added marker, or None if creation failed
        """
        marker = self.create_marker_of_type(marker_type)
        if marker is None:
            return None

        # Execute via command pattern for undo/redo support
        command = AddMarkerCommand(self.marker_repository, marker)
        self.history.execute_command(command)

        # Return index of newly added marker (last one in the list)
        return len(self.marker_repository.markers) - 1

    def delete_marker_at_index(self, marker_index: int) -> bool:
        """
        Delete marker at specified index.

        Args:
            marker_index: Index of marker to delete

        Returns:
            True if successful, False otherwise
        """
        markers = self.marker_repository.markers

        if not 0 <= marker_index < len(markers):
            return False

        marker = markers[marker_index]

        # Execute via command pattern for undo/redo support
        command = DeleteMarkerCommand(self.marker_repository, marker, marker_index)
        self.history.execute_command(command)

        return True

    def clear_all_markers(self) -> int:
        """
        Clear all markers from the timeline.

        Returns:
            Number of markers that were cleared
        """
        count = self.marker_repository.count()
        if count > 0:
            self.marker_repository.clear_all()
        return count

    def nudge_marker(self, marker_index: int, delta_ms: int) -> bool:
        """
        Nudge marker by delta_ms milliseconds.

        Args:
            marker_index: Index of marker to nudge
            delta_ms: Amount to move marker (positive or negative)

        Returns:
            True if marker was moved, False otherwise
        """
        markers = self.marker_repository.markers

        if not 0 <= marker_index < len(markers):
            return False

        marker = markers[marker_index]
        old_time_ms = marker["time_ms"]
        duration = self.get_duration()
        new_time_ms = max(0, min(old_time_ms + delta_ms, duration))

        if new_time_ms != old_time_ms:
            # Create and execute move command
            command = MoveMarkerCommand(
                self.marker_repository,
                marker_index,
                old_time_ms,
                new_time_ms
            )
            self.history.execute_command(command)
            return True

        return False

    def nudge_marker_by_frame(self, marker_index: int, delta_frames: int, fps: float = 30.0) -> bool:
        """
        Nudge marker by specified number of frames.

        Args:
            marker_index: Index of marker to nudge
            delta_frames: Number of frames to move (positive or negative)
            fps: Frames per second (default: 30.0)

        Returns:
            True if marker was moved, False otherwise
        """
        frame_duration_ms = int(1000 / fps)
        delta_ms = delta_frames * frame_duration_ms
        return self.nudge_marker(marker_index, delta_ms)

    def update_marker(self, marker_index: int, updated_marker: Dict[str, Any]) -> bool:
        """
        Update marker at specified index via command pattern.

        Args:
            marker_index: Index of marker to update
            updated_marker: New marker data

        Returns:
            True if successful, False otherwise
        """
        markers = self.marker_repository.markers

        if not 0 <= marker_index < len(markers):
            return False

        old_marker = markers[marker_index].copy()

        # Execute edit via command pattern for undo/redo support
        command = EditMarkerCommand(
            self.marker_repository,
            marker_index,
            old_marker,
            updated_marker
        )
        self.history.execute_command(command)

        return True

    def get_marker_count(self) -> int:
        """Get total number of markers."""
        return self.marker_repository.count()

    def get_marker_at_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get marker at specified index."""
        return self.marker_repository.get_marker(index)

    def get_all_markers(self) -> List[Dict[str, Any]]:
        """Get all markers."""
        return self.marker_repository.get_all_markers()

    @staticmethod
    def get_prompt_preview(marker: Dict[str, Any]) -> str:
        """
        Get a short preview string of the prompt for display.

        Args:
            marker: Marker dictionary

        Returns:
            Preview string (max 40 chars)
        """
        # Handle old format
        if "prompt" in marker:
            prompt = marker["prompt"]
            return prompt[:40] + "..." if len(prompt) > 40 else prompt

        # Handle new format
        if "prompt_data" not in marker:
            return "(no prompt)"

        prompt_data = marker["prompt_data"]
        marker_type = marker.get("type", "sfx")

        if marker_type == "sfx":
            desc = prompt_data.get("description", "")
            return desc[:40] + "..." if len(desc) > 40 else desc

        elif marker_type == "voice":
            text = prompt_data.get("text", "")
            return text[:40] + "..." if len(text) > 40 else text

        elif marker_type == "music":
            styles = prompt_data.get("positiveGlobalStyles", [])
            if styles:
                preview = ", ".join(styles)
                return preview[:40] + "..." if len(preview) > 40 else preview
            return "(no styles)"

        return "(unknown)"
