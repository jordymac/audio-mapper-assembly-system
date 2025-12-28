#!/usr/bin/env python3
"""
Marker Repository - Data access layer for marker operations
Provides CRUD operations without GUI coupling
"""

import copy
from typing import List, Optional, Callable
from core.models import Marker


class MarkerRepository:
    """
    Repository pattern for marker data management.
    Handles all marker CRUD operations without GUI dependencies.
    """

    def __init__(self, markers: Optional[List[dict]] = None):
        """
        Initialize repository with optional marker list.

        Args:
            markers: Initial list of marker dictionaries (default: empty list)
        """
        self._markers = markers if markers is not None else []
        self._change_listeners: List[Callable[[], None]] = []

    def add_change_listener(self, listener: Callable[[], None]) -> None:
        """
        Register a callback to be notified when markers change.

        Args:
            listener: Function to call when markers are modified
        """
        self._change_listeners.append(listener)

    def _notify_change(self) -> None:
        """Notify all registered listeners that markers have changed."""
        for listener in self._change_listeners:
            listener()

    @property
    def markers(self) -> List[dict]:
        """Get reference to markers list (for backward compatibility)."""
        return self._markers

    def get_all_markers(self) -> List[dict]:
        """
        Get all markers in time order.

        Returns:
            List of marker dictionaries sorted by time_ms
        """
        return [copy.deepcopy(m) for m in self._markers]

    def get_marker(self, index: int) -> Optional[dict]:
        """
        Get marker at specific index.

        Args:
            index: Position in sorted marker list

        Returns:
            Marker dictionary or None if index out of range
        """
        if 0 <= index < len(self._markers):
            return copy.deepcopy(self._markers[index])
        return None

    def add_marker(self, marker: dict) -> None:
        """
        Add a new marker and maintain time-based sorting.

        Args:
            marker: Marker dictionary to add
        """
        self._markers.append(copy.deepcopy(marker))
        self._markers.sort(key=lambda m: m["time_ms"])
        self._notify_change()

    def remove_marker(self, marker: dict) -> None:
        """
        Remove a marker by value.

        Args:
            marker: Marker dictionary to remove
        """
        self._markers.remove(marker)
        self._notify_change()

    def remove_marker_at(self, index: int) -> Optional[dict]:
        """
        Remove marker at specific index.

        Args:
            index: Position in marker list

        Returns:
            Removed marker dictionary or None if index invalid
        """
        if 0 <= index < len(self._markers):
            removed = self._markers.pop(index)
            self._notify_change()
            return removed
        return None

    def update_marker(self, index: int, marker: dict) -> bool:
        """
        Replace marker at specific index.

        Args:
            index: Position in marker list
            marker: New marker data

        Returns:
            True if successful, False if index invalid
        """
        if 0 <= index < len(self._markers):
            self._markers[index] = copy.deepcopy(marker)
            self._notify_change()
            return True
        return False

    def insert_marker(self, index: int, marker: dict) -> None:
        """
        Insert marker at specific position.

        Args:
            index: Position to insert at
            marker: Marker dictionary to insert
        """
        self._markers.insert(index, copy.deepcopy(marker))
        self._notify_change()

    def sort_markers(self) -> None:
        """Sort markers by time_ms and notify listeners."""
        self._markers.sort(key=lambda m: m["time_ms"])
        self._notify_change()

    def clear_all(self) -> List[dict]:
        """
        Remove all markers.

        Returns:
            List of removed markers (for undo support)
        """
        old_markers = [copy.deepcopy(m) for m in self._markers]
        self._markers.clear()
        self._notify_change()
        return old_markers

    def count(self) -> int:
        """
        Get number of markers.

        Returns:
            Count of markers in repository
        """
        return len(self._markers)

    def find_by_time(self, time_ms: int, tolerance: int = 0) -> Optional[int]:
        """
        Find marker index by time with optional tolerance.

        Args:
            time_ms: Time to search for
            tolerance: Allowed time difference in milliseconds

        Returns:
            Index of matching marker or None if not found
        """
        for i, marker in enumerate(self._markers):
            if abs(marker["time_ms"] - time_ms) <= tolerance:
                return i
        return None
