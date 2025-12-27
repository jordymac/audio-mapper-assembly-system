#!/usr/bin/env python3
"""
Command Pattern - Undo/Redo System
Base command class and all command implementations for marker operations
"""


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
    def __init__(self, gui, marker):
        self.gui = gui
        self.marker = marker.copy()  # Store copy to avoid mutation

    def execute(self):
        self.gui.markers.append(self.marker)
        self.gui.markers.sort(key=lambda m: m["time_ms"])
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()

    def undo(self):
        self.gui.markers.remove(self.marker)
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()


class DeleteMarkerCommand(Command):
    """Command to delete a marker"""
    def __init__(self, gui, marker, index):
        self.gui = gui
        self.marker = marker.copy()
        self.index = index

    def execute(self):
        self.gui.markers.pop(self.index)
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()

    def undo(self):
        self.gui.markers.insert(self.index, self.marker)
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()


class MoveMarkerCommand(Command):
    """Command to move a marker to a new time"""
    def __init__(self, gui, marker, old_time_ms, new_time_ms):
        self.gui = gui
        self.marker = marker  # Reference to actual marker object
        self.old_time_ms = old_time_ms
        self.new_time_ms = new_time_ms

    def execute(self):
        self.marker["time_ms"] = self.new_time_ms
        self.gui.markers.sort(key=lambda m: m["time_ms"])
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()

    def undo(self):
        self.marker["time_ms"] = self.old_time_ms
        self.gui.markers.sort(key=lambda m: m["time_ms"])
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()


class EditMarkerCommand(Command):
    """Command to edit a marker's prompt data"""
    def __init__(self, gui, marker_index, old_marker, new_marker):
        self.gui = gui
        self.marker_index = marker_index
        self.old_marker = old_marker.copy()  # Store copy of old state
        self.new_marker = new_marker.copy()  # Store copy of new state

    def execute(self):
        self.gui.markers[self.marker_index] = self.new_marker
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()

    def undo(self):
        self.gui.markers[self.marker_index] = self.old_marker
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()


class GenerateAudioCommand(Command):
    """Command to generate/regenerate audio for a marker (creates new version)"""
    def __init__(self, gui, marker_index, old_marker_state):
        self.gui = gui
        self.marker_index = marker_index
        self.old_marker_state = old_marker_state.copy()  # Marker state before generation
        self.new_marker_state = None  # Will be set after generation completes

    def execute(self):
        """Execute is called when generation starts"""
        # Store the new state (after generation)
        if self.new_marker_state is None:
            self.new_marker_state = self.gui.markers[self.marker_index].copy()
        else:
            self.gui.markers[self.marker_index] = self.new_marker_state
            self.gui.update_marker_list()
            self.gui.redraw_marker_indicators()

    def undo(self):
        """Undo reverts to previous version/state"""
        self.gui.markers[self.marker_index] = self.old_marker_state
        self.gui.update_marker_list()
        self.gui.redraw_marker_indicators()
