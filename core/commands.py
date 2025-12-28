#!/usr/bin/env python3
"""
Command Pattern - Undo/Redo System
Base command class and all command implementations for marker operations

REFACTORED: Commands now use MarkerRepository for data operations
and no longer directly reference GUI components.
"""

import copy
from core.marker_repository import MarkerRepository


class Command:
    """Base class for undoable commands"""
    def execute(self):
        """Perform the command action"""
        raise NotImplementedError

    def undo(self):
        """Reverse the command action"""
        raise NotImplementedError


class AddMarkerCommand(Command):
    """Command to add a marker"""
    def __init__(self, repository: MarkerRepository, marker: dict):
        """
        Initialize command.

        Args:
            repository: MarkerRepository for data operations
            marker: Marker dictionary to add
        """
        self.repository = repository
        self.marker = copy.deepcopy(marker)  # Deep copy to avoid nested mutation

    def execute(self):
        """Add marker to repository (triggers UI update via listener)"""
        self.repository.add_marker(self.marker)

    def undo(self):
        """Remove marker from repository (triggers UI update via listener)"""
        self.repository.remove_marker(self.marker)


class DeleteMarkerCommand(Command):
    """Command to delete a marker"""
    def __init__(self, repository: MarkerRepository, marker: dict, index: int):
        """
        Initialize command.

        Args:
            repository: MarkerRepository for data operations
            marker: Marker dictionary to delete
            index: Position of marker in list
        """
        self.repository = repository
        self.marker = copy.deepcopy(marker)  # Deep copy to preserve state
        self.index = index

    def execute(self):
        """Remove marker at index (triggers UI update via listener)"""
        self.repository.remove_marker_at(self.index)

    def undo(self):
        """Re-insert marker at original position (triggers UI update via listener)"""
        self.repository.insert_marker(self.index, self.marker)


class MoveMarkerCommand(Command):
    """Command to move a marker to a new time"""
    def __init__(self, repository: MarkerRepository, marker_index: int,
                 old_time_ms: int, new_time_ms: int):
        """
        Initialize command.

        Args:
            repository: MarkerRepository for data operations
            marker_index: Position of marker to move
            old_time_ms: Original time position
            new_time_ms: New time position
        """
        self.repository = repository
        self.marker_index = marker_index
        self.old_time_ms = old_time_ms
        self.new_time_ms = new_time_ms

    def execute(self):
        """Move marker to new time and re-sort (triggers UI update via listener)"""
        marker = self.repository.get_marker(self.marker_index)
        if marker:
            marker["time_ms"] = self.new_time_ms
            self.repository.update_marker(self.marker_index, marker)
            self.repository.sort_markers()

    def undo(self):
        """Restore marker to original time and re-sort (triggers UI update via listener)"""
        # After sorting, marker may have moved to different index
        # Find it by looking for marker with new_time_ms
        marker_index = self.repository.find_by_time(self.new_time_ms)
        if marker_index is not None:
            marker = self.repository.get_marker(marker_index)
            if marker:
                marker["time_ms"] = self.old_time_ms
                self.repository.update_marker(marker_index, marker)
                self.repository.sort_markers()


class EditMarkerCommand(Command):
    """Command to edit a marker's prompt data"""
    def __init__(self, repository: MarkerRepository, marker_index: int,
                 old_marker: dict, new_marker: dict):
        """
        Initialize command.

        Args:
            repository: MarkerRepository for data operations
            marker_index: Position of marker to edit
            old_marker: Original marker state
            new_marker: New marker state
        """
        self.repository = repository
        self.marker_index = marker_index
        self.old_marker = copy.deepcopy(old_marker)  # Deep copy to preserve nested state
        self.new_marker = copy.deepcopy(new_marker)  # Deep copy to preserve nested state

    def execute(self):
        """Replace marker with new state (triggers UI update via listener)"""
        self.repository.update_marker(self.marker_index, self.new_marker)

    def undo(self):
        """Restore marker to old state (triggers UI update via listener)"""
        self.repository.update_marker(self.marker_index, self.old_marker)


class GenerateAudioCommand(Command):
    """Command to generate/regenerate audio for a marker (creates new version)"""
    def __init__(self, repository: MarkerRepository, marker_index: int,
                 old_marker_state: dict):
        """
        Initialize command.

        Args:
            repository: MarkerRepository for data operations
            marker_index: Position of marker being generated
            old_marker_state: Marker state before generation
        """
        self.repository = repository
        self.marker_index = marker_index
        self.old_marker_state = copy.deepcopy(old_marker_state)  # Deep copy state
        self.new_marker_state = None  # Will be set after generation completes

    def execute(self):
        """
        Execute is called when generation starts.
        Triggers UI update via listener.
        """
        # Store the new state (after generation)
        if self.new_marker_state is None:
            marker = self.repository.get_marker(self.marker_index)
            if marker:
                self.new_marker_state = copy.deepcopy(marker)
        else:
            self.repository.update_marker(self.marker_index, self.new_marker_state)

    def undo(self):
        """
        Undo reverts to previous version/state.
        Triggers UI update via listener.
        """
        self.repository.update_marker(self.marker_index, self.old_marker_state)
