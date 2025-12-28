#!/usr/bin/env python3
"""
Keyboard Shortcut Manager - Centralized keyboard event handling
Decoupled from GUI implementation using callback pattern
"""

from typing import Callable, Optional
from tkinter import messagebox


class KeyboardShortcutManager:
    """
    Manages all keyboard shortcuts for the audio mapper application.
    Uses callback pattern to decouple from GUI implementation.
    """

    def __init__(self, root, callbacks: dict):
        """
        Initialize keyboard shortcut manager.

        Args:
            root: Tkinter root window
            callbacks: Dictionary of callback functions for shortcut actions
                Required callbacks:
                - 'toggle_playback': Callable[[], None]
                - 'add_marker': Callable[[], None]
                - 'delete_marker': Callable[[], None]
                - 'nudge_selected_marker': Callable[[int], None]
                - 'nudge_selected_marker_by_frame': Callable[[int], None]
                - 'step_time': Callable[[int], None]
                - 'step_frame': Callable[[int], None]
                - 'undo': Callable[[], None]
                - 'redo': Callable[[], None]
                - 'play_marker_audio': Callable[[int], None]
                - 'generate_marker_audio': Callable[[int], None]
                - 'load_video': Callable[[], None]
                - 'get_selected_marker_index': Callable[[], Optional[int]]
                - 'redraw_marker_indicators': Callable[[], None]
                - 'get_marker_row_widgets': Callable[[], list]
        """
        self.root = root
        self.callbacks = callbacks
        self.shortcuts_enabled = True

        # Bind all shortcuts
        self._bind_shortcuts()

    def _bind_shortcuts(self):
        """Bind all keyboard shortcuts to the root window"""
        # Playback control
        self.root.bind("<space>", lambda e: self.shortcuts_enabled and self.callbacks['toggle_playback']())

        # Marker creation
        self.root.bind("m", lambda e: self.shortcuts_enabled and self.callbacks['add_marker']())
        self.root.bind("M", lambda e: self.shortcuts_enabled and self.callbacks['add_marker']())

        # Marker deletion
        self.root.bind("<Delete>", lambda e: self.shortcuts_enabled and self.callbacks['delete_marker']())
        self.root.bind("<BackSpace>", lambda e: self.shortcuts_enabled and self.callbacks['delete_marker']())

        # Arrow keys - context sensitive (nudge marker if selected, otherwise scrub timeline)
        self.root.bind("<Left>", lambda e: self.shortcuts_enabled and self._handle_left_arrow())
        self.root.bind("<Right>", lambda e: self.shortcuts_enabled and self._handle_right_arrow())

        # Shift+Arrow - frame-precise (nudge marker by frame if selected, otherwise step timeline by frame)
        self.root.bind("<Shift-Left>", lambda e: self.shortcuts_enabled and self._handle_shift_left_arrow())
        self.root.bind("<Shift-Right>", lambda e: self.shortcuts_enabled and self._handle_shift_right_arrow())

        # Alt/Cmd+Arrow - millisecond-precise (nudge marker by 1ms)
        self.root.bind("<Alt-Left>", lambda e: self.shortcuts_enabled and self.callbacks['nudge_selected_marker'](-1))
        self.root.bind("<Alt-Right>", lambda e: self.shortcuts_enabled and self.callbacks['nudge_selected_marker'](1))
        self.root.bind("<Command-Left>", lambda e: self.shortcuts_enabled and self.callbacks['nudge_selected_marker'](-1))
        self.root.bind("<Command-Right>", lambda e: self.shortcuts_enabled and self.callbacks['nudge_selected_marker'](1))

        # Undo/Redo (works on both macOS and other platforms)
        # On macOS: Cmd+Z / Cmd+Shift+Z
        # On other platforms: Ctrl+Z / Ctrl+Shift+Z
        self.root.bind("<Command-z>", lambda e: self.callbacks['undo']())  # macOS
        self.root.bind("<Control-z>", lambda e: self.callbacks['undo']())  # Windows/Linux
        self.root.bind("<Command-Shift-Z>", lambda e: self.callbacks['redo']())  # macOS
        self.root.bind("<Control-Shift-Z>", lambda e: self.callbacks['redo']())  # Windows/Linux
        self.root.bind("<Command-y>", lambda e: self.callbacks['redo']())  # macOS alternative
        self.root.bind("<Control-y>", lambda e: self.callbacks['redo']())  # Windows alternative

        # Marker operations (require a selected marker)
        self.root.bind("p", lambda e: self.shortcuts_enabled and self._play_selected_marker_shortcut())
        self.root.bind("P", lambda e: self.shortcuts_enabled and self._play_selected_marker_shortcut())
        self.root.bind("g", lambda e: self.shortcuts_enabled and self._generate_selected_marker_shortcut())
        self.root.bind("G", lambda e: self.shortcuts_enabled and self._generate_selected_marker_shortcut())
        self.root.bind("r", lambda e: self.shortcuts_enabled and self._regenerate_selected_marker_shortcut())
        self.root.bind("R", lambda e: self.shortcuts_enabled and self._regenerate_selected_marker_shortcut())

        # Deselect marker
        self.root.bind("<Escape>", lambda e: self._deselect_marker())

        # File operations
        self.root.bind("<Command-o>", lambda e: self.callbacks['load_video']())  # macOS
        self.root.bind("<Control-o>", lambda e: self.callbacks['load_video']())  # Windows/Linux

    def disable(self):
        """Disable keyboard shortcuts when typing in text boxes"""
        self.shortcuts_enabled = False

    def enable(self):
        """Re-enable keyboard shortcuts"""
        self.shortcuts_enabled = True

    def _handle_left_arrow(self):
        """Context-sensitive left arrow: nudge marker or scrub timeline"""
        selected_index = self.callbacks['get_selected_marker_index']()
        if selected_index is not None:
            self.callbacks['nudge_selected_marker'](-50)
        else:
            self.callbacks['step_time'](-50)

    def _handle_right_arrow(self):
        """Context-sensitive right arrow: nudge marker or scrub timeline"""
        selected_index = self.callbacks['get_selected_marker_index']()
        if selected_index is not None:
            self.callbacks['nudge_selected_marker'](50)
        else:
            self.callbacks['step_time'](50)

    def _handle_shift_left_arrow(self):
        """Context-sensitive Shift+Left: nudge marker by frame or step timeline by frame"""
        selected_index = self.callbacks['get_selected_marker_index']()
        if selected_index is not None:
            self.callbacks['nudge_selected_marker_by_frame'](-1)
        else:
            self.callbacks['step_frame'](-1)

    def _handle_shift_right_arrow(self):
        """Context-sensitive Shift+Right: nudge marker by frame or step timeline by frame"""
        selected_index = self.callbacks['get_selected_marker_index']()
        if selected_index is not None:
            self.callbacks['nudge_selected_marker_by_frame'](1)
        else:
            self.callbacks['step_frame'](1)

    def _play_selected_marker_shortcut(self):
        """Play selected marker's audio (keyboard shortcut: P)"""
        selected_index = self.callbacks['get_selected_marker_index']()
        if selected_index is not None:
            self.callbacks['play_marker_audio'](selected_index)
        else:
            # No marker selected - show brief info
            messagebox.showinfo(
                "No Marker Selected",
                "Select a marker first (click on it in the list or timeline)\n\n"
                "Keyboard shortcut: P → Play selected marker"
            )

    def _generate_selected_marker_shortcut(self):
        """Generate audio for selected marker (keyboard shortcut: G)"""
        selected_index = self.callbacks['get_selected_marker_index']()
        if selected_index is not None:
            self.callbacks['generate_marker_audio'](selected_index)
        else:
            # No marker selected - show brief info
            messagebox.showinfo(
                "No Marker Selected",
                "Select a marker first (click on it in the list or timeline)\n\n"
                "Keyboard shortcut: G → Generate selected marker"
            )

    def _regenerate_selected_marker_shortcut(self):
        """Regenerate audio for selected marker (keyboard shortcut: R)"""
        selected_index = self.callbacks['get_selected_marker_index']()
        if selected_index is not None:
            # Regenerate is the same as generate - it creates a new version
            self.callbacks['generate_marker_audio'](selected_index)
        else:
            # No marker selected - show brief info
            messagebox.showinfo(
                "No Marker Selected",
                "Select a marker first (click on it in the list or timeline)\n\n"
                "Keyboard shortcut: R → Regenerate selected marker"
            )

    def _deselect_marker(self):
        """Deselect the currently selected marker"""
        selected_index = self.callbacks['get_selected_marker_index']()
        marker_row_widgets = self.callbacks['get_marker_row_widgets']()

        if selected_index is not None and selected_index < len(marker_row_widgets):
            marker_row_widgets[selected_index].set_selected(False)

        # Clear selection in GUI (via callback)
        # Note: We need a callback to set selected_marker_index = None
        if 'set_selected_marker_index' in self.callbacks:
            self.callbacks['set_selected_marker_index'](None)

        self.callbacks['redraw_marker_indicators']()
