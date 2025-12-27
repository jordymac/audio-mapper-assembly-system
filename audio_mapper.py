#!/usr/bin/env python3
"""
Audio Mapper - Visual Timecode Mapping GUI
Tkinter-based application for mapping audio markers to video timecodes
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
from pathlib import Path
import threading
from datetime import datetime

try:
    import cv2
except ImportError:
    print("ERROR: opencv-python not found. Install with: pip install opencv-python")
    exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("ERROR: Pillow not found. Install with: pip install Pillow")
    exit(1)

try:
    import numpy as np
    from moviepy.video.io.VideoFileClip import VideoFileClip
except ImportError:
    print("ERROR: moviepy or numpy not found. Install with: pip install moviepy numpy")
    exit(1)


# ============================================================================
# COLOR SCHEME SYSTEM - Dark Mode Support
# ============================================================================

class ColorScheme:
    """Global color scheme that adapts to system dark mode"""

    def __init__(self):
        self.is_dark_mode = self._detect_dark_mode()
        self._init_colors()

    def _detect_dark_mode(self):
        """Detect if macOS is in dark mode"""
        try:
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and 'Dark' in result.stdout
        except:
            return False

    def _init_colors(self):
        """Initialize color palettes for light and dark modes"""
        if self.is_dark_mode:
            # Dark Mode Colors
            self.bg_primary = "#1E1E1E"           # Main background
            self.bg_secondary = "#2C2C2C"         # Secondary background
            self.bg_tertiary = "#3C3C3C"          # Tertiary background
            self.bg_input = "#2C2C2C"             # Input field background
            self.bg_hover = "#404040"             # Hover state

            self.fg_primary = "#E0E0E0"           # Main text
            self.fg_secondary = "#B0B0B0"         # Secondary text
            self.fg_tertiary = "#808080"          # Tertiary text
            self.fg_input = "#E0E0E0"             # Input text

            self.border = "#404040"               # Borders
            self.divider = "#2C2C2C"              # Dividers

            # Accent colors (markers)
            self.sfx_bg = "#D32F2F"               # SFX red (darker)
            self.sfx_fg = "white"
            self.music_bg = "#1976D2"             # Music blue (darker)
            self.music_fg = "white"
            self.voice_bg = "#388E3C"             # Voice green (darker)
            self.voice_fg = "white"

            # Button colors
            self.btn_primary_bg = "#1976D2"       # Primary button (blue)
            self.btn_primary_fg = "white"
            self.btn_success_bg = "#388E3C"       # Success button (green)
            self.btn_success_fg = "white"
            self.btn_danger_bg = "#D32F2F"        # Danger button (red)
            self.btn_danger_fg = "white"
            self.btn_warning_bg = "#F57C00"       # Warning button (orange)
            self.btn_warning_fg = "white"
            self.btn_special_bg = "#7B1FA2"       # Special button (purple)
            self.btn_special_fg = "white"

            # Info/highlight backgrounds
            self.info_bg = "#0D47A1"              # Info background (dark blue)
            self.success_bg = "#1B5E20"           # Success background (dark green)
            self.warning_bg = "#E65100"           # Warning background (dark orange)
            self.selection_bg = "#1565C0"         # Selection highlight

        else:
            # Light Mode Colors
            self.bg_primary = "#FFFFFF"           # Main background
            self.bg_secondary = "#F5F5F5"         # Secondary background
            self.bg_tertiary = "#E0E0E0"          # Tertiary background
            self.bg_input = "#F5F5F5"             # Input field background
            self.bg_hover = "#E8E8E8"             # Hover state

            self.fg_primary = "#000000"           # Main text
            self.fg_secondary = "#424242"         # Secondary text
            self.fg_tertiary = "#666666"          # Tertiary text
            self.fg_input = "#000000"             # Input text

            self.border = "#CCCCCC"               # Borders
            self.divider = "#E0E0E0"              # Dividers

            # Accent colors (markers)
            self.sfx_bg = "#F44336"               # SFX red
            self.sfx_fg = "black"
            self.music_bg = "#2196F3"             # Music blue
            self.music_fg = "black"
            self.voice_bg = "#4CAF50"             # Voice green
            self.voice_fg = "black"

            # Button colors
            self.btn_primary_bg = "#2196F3"       # Primary button (blue)
            self.btn_primary_fg = "white"
            self.btn_success_bg = "#4CAF50"       # Success button (green)
            self.btn_success_fg = "white"
            self.btn_danger_bg = "#f44336"        # Danger button (red)
            self.btn_danger_fg = "white"
            self.btn_warning_bg = "#FF9800"       # Warning button (orange)
            self.btn_warning_fg = "white"
            self.btn_special_bg = "#9C27B0"       # Special button (purple)
            self.btn_special_fg = "white"

            # Info/highlight backgrounds
            self.info_bg = "#E3F2FD"              # Info background (light blue)
            self.success_bg = "#E8F5E9"           # Success background (light green)
            self.warning_bg = "#FFFFE0"           # Warning background (light yellow)
            self.selection_bg = "#BBDEFB"         # Selection highlight

# Global color scheme instance
COLORS = ColorScheme()


# ============================================================================
# UNDO/REDO SYSTEM - Command Pattern
# ============================================================================

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


class HistoryManager:
    """Manages undo/redo history"""
    def __init__(self, max_history=50):
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history

    def execute_command(self, command):
        """Execute command and add to history"""
        command.execute()
        self.undo_stack.append(command)

        # Clear redo stack when new command is executed
        self.redo_stack.clear()

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def undo(self):
        """Undo the last command"""
        if not self.undo_stack:
            return False

        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True

    def redo(self):
        """Redo the last undone command"""
        if not self.redo_stack:
            return False

        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return True

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0


# ============================================================================
# BATCH PROGRESS WINDOW - Modal dialog for batch generation operations
# ============================================================================

class BatchProgressWindow:
    """Modal window showing progress for batch audio generation"""

    def __init__(self, parent, operation_name, total_markers):
        self.parent = parent
        self.operation_name = operation_name
        self.total_markers = total_markers
        self.current_index = 0
        self.success_count = 0
        self.failed_count = 0
        self.cancelled = False

        # Create modal window
        self.window = tk.Toplevel(parent.root)
        self.window.title(f"Batch Generation - {operation_name}")
        self.window.geometry("500x250")
        self.window.resizable(False, False)
        self.window.transient(parent.root)
        self.window.grab_set()

        # Center on parent
        self.window.update_idletasks()
        x = parent.root.winfo_x() + (parent.root.winfo_width() // 2) - (500 // 2)
        y = parent.root.winfo_y() + (parent.root.winfo_height() // 2) - (250 // 2)
        self.window.geometry(f"+{x}+{y}")

        # Title
        tk.Label(
            self.window,
            text=operation_name,
            font=("Arial", 14, "bold")
        ).pack(pady=20)

        # Current marker label
        self.marker_label = tk.Label(
            self.window,
            text="Starting...",
            font=("Arial", 10)
        )
        self.marker_label.pack(pady=10)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.window,
            variable=self.progress_var,
            maximum=total_markers,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=10)

        # Progress text
        self.progress_text = tk.Label(
            self.window,
            text=f"0 / {total_markers}",
            font=("Arial", 10)
        )
        self.progress_text.pack(pady=5)

        # Cancel button
        self.cancel_btn = tk.Button(
            self.window,
            text="Cancel",
            command=self.on_cancel,
            bg="#F44336",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        self.cancel_btn.pack(pady=15)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def update_progress(self, marker_index, marker_name, marker_type):
        """Update progress bar and current marker display"""
        self.current_index = marker_index + 1
        self.progress_var.set(self.current_index)
        self.progress_text.config(text=f"{self.current_index} / {self.total_markers}")
        self.marker_label.config(
            text=f"Generating: {marker_type.upper()} - {marker_name}"
        )
        self.window.update()

    def mark_success(self):
        """Increment success counter"""
        self.success_count += 1

    def mark_failed(self):
        """Increment failed counter"""
        self.failed_count += 1

    def on_cancel(self):
        """Handle cancel button click"""
        if messagebox.askyesno(
            "Cancel Batch Operation",
            "Are you sure you want to cancel?\n\n"
            "Markers already generated will be kept.",
            parent=self.window
        ):
            self.cancelled = True
            self.window.destroy()

    def close(self):
        """Close the progress window"""
        try:
            self.window.destroy()
        except:
            pass

    def show_summary(self):
        """Show summary dialog after batch operation completes"""
        skipped_count = self.total_markers - (self.success_count + self.failed_count)

        summary_msg = f"Batch operation complete!\n\n"
        summary_msg += f"✓ Generated: {self.success_count}\n"
        summary_msg += f"⚠️ Failed: {self.failed_count}\n"
        summary_msg += f"○ Skipped: {skipped_count}\n"

        if self.cancelled:
            summary_msg += "\n(Operation was cancelled)"

        messagebox.showinfo(
            "Batch Operation Complete",
            summary_msg,
            parent=self.parent.root
        )


# ============================================================================
# MUSIC SECTION EDITOR WINDOW - Nested modal for editing music sections
# ============================================================================

class ToolTip:
    """Simple tooltip class for hovering over widgets"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        """Show tooltip on mouse enter"""
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#FFFFE0",
            foreground="black",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            padx=5,
            pady=3
        )
        label.pack()

    def on_leave(self, event=None):
        """Hide tooltip on mouse leave"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class MusicSectionEditorWindow:
    """Modal pop-up window for editing a music section"""

    def __init__(self, parent, section, section_index, on_save_callback):
        """
        Initialize the section editor window

        Args:
            parent: Parent tk window (the PromptEditorWindow)
            section: The section dict to edit
            section_index: Index of section in sections list
            on_save_callback: Function to call when Save is clicked
        """
        self.parent = parent
        self.section = section.copy()  # Work on a copy
        self.section_index = section_index
        self.on_save_callback = on_save_callback

        # Create modal window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Edit Section: {section.get('sectionName', 'Unnamed')}")
        self.window.geometry("550x600")

        # Make modal on top of parent
        self.window.transient(parent)
        self.window.grab_set()

        # Center on parent
        self.center_on_parent()

        # Handle window close (treat as cancel)
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Build UI
        self.create_ui()

    def center_on_parent(self):
        """Center this window on the parent window"""
        self.window.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get this window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Calculate centered position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        self.window.geometry(f"+{x}+{y}")

    def create_ui(self):
        """Build the section editor UI"""
        content_frame = tk.Frame(self.window, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Section Name
        tk.Label(
            content_frame,
            text="Section Name:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.section_name_entry = tk.Entry(
            content_frame,
            font=("Arial", 10),
            width=50,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.section_name_entry.pack(fill=tk.X, pady=(0, 15))
        section_name = self.section.get("sectionName", "")
        if section_name:
            self.section_name_entry.insert(0, section_name)

        # Set focus to show cursor
        self.section_name_entry.focus_set()

        # Duration (ms)
        tk.Label(
            content_frame,
            text="Duration (ms):",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.duration_entry = tk.Entry(
            content_frame,
            font=("Arial", 10),
            width=50,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.duration_entry.pack(fill=tk.X, pady=(0, 5))
        self.duration_entry.insert(0, str(self.section.get("durationMs", 1000)))

        tk.Label(
            content_frame,
            text="Duration in milliseconds (e.g., 3000 = 3 seconds)",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Positive Local Styles
        tk.Label(
            content_frame,
            text="Positive Local Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.positive_styles = tk.Text(
            content_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.positive_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing positive styles
        positive = self.section.get("positiveLocalStyles", [])
        if positive:
            self.positive_styles.insert("1.0", ", ".join(positive))

        tk.Label(
            content_frame,
            text="Comma-separated (e.g., 'rising synth arpeggio, energetic')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Negative Local Styles
        tk.Label(
            content_frame,
            text="Negative Local Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.negative_styles = tk.Text(
            content_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.negative_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing negative styles
        negative = self.section.get("negativeLocalStyles", [])
        if negative:
            self.negative_styles.insert("1.0", ", ".join(negative))

        tk.Label(
            content_frame,
            text="Comma-separated styles to avoid (e.g., 'soft pads, ambient')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Buttons
        button_frame = tk.Frame(self.window, padx=20, pady=15)
        button_frame.pack(fill=tk.X)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=12,
            font=("Arial", 10)
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            button_frame,
            text="Save",
            command=self.on_save,
            bg=COLORS.btn_primary_bg,
            fg=COLORS.btn_primary_fg,
            width=12,
            font=("Arial", 10, "bold")
        ).pack(side=tk.RIGHT, padx=5)

    def on_cancel(self):
        """Cancel button - close without saving"""
        try:
            self.window.destroy()
        except Exception as e:
            print(f"Warning: Error closing section editor window: {e}")

    def on_save(self):
        """Save button - validate and save changes"""
        try:
            # Get section name
            section_name = self.section_name_entry.get().strip()
            if not section_name:
                messagebox.showwarning(
                    "Validation Error",
                    "Section name cannot be empty",
                    parent=self.window
                )
                return

            # Get and validate duration
            try:
                duration = int(self.duration_entry.get().strip())
                if duration <= 0:
                    raise ValueError("Duration must be positive")
            except ValueError:
                messagebox.showwarning(
                    "Validation Error",
                    "Duration must be a positive number in milliseconds",
                    parent=self.window
                )
                return

            # Get styles
            positive_text = self.positive_styles.get("1.0", "end-1c").strip()
            positive_list = [s.strip() for s in positive_text.split(",") if s.strip()] if positive_text else []

            negative_text = self.negative_styles.get("1.0", "end-1c").strip()
            negative_list = [s.strip() for s in negative_text.split(",") if s.strip()] if negative_text else []

            # Update section
            self.section["sectionName"] = section_name
            self.section["durationMs"] = duration
            self.section["positiveLocalStyles"] = positive_list
            self.section["negativeLocalStyles"] = negative_list

            # Call callback and close
            try:
                self.on_save_callback(self.section, self.section_index)
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save section:\n{str(e)}",
                    parent=self.window
                )
                return

            try:
                self.window.destroy()
            except Exception as e:
                print(f"Warning: Error closing section editor window: {e}")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred:\n{str(e)}",
                parent=self.window
            )
            print(f"Error in section editor on_save: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# PROMPT EDITOR WINDOW - Pop-up modal for editing marker prompts
# ============================================================================

class PromptEditorWindow:
    """Modal pop-up window for editing marker prompt data"""

    def __init__(self, parent, marker, marker_index, on_save_callback, on_cancel_callback=None, gui_ref=None):
        """
        Initialize the prompt editor window

        Args:
            parent: Parent tk window
            marker: The marker dict to edit
            marker_index: Index of marker in markers list
            on_save_callback: Function to call when Save is clicked (receives updated marker)
            on_cancel_callback: Optional function to call when Cancel is clicked or window closed
            gui_ref: Reference to main GUI (for audio player and version methods)
        """
        self.parent = parent
        self.marker = marker.copy()  # Work on a copy
        self.marker_index = marker_index
        self.on_save_callback = on_save_callback
        self.on_cancel_callback = on_cancel_callback
        self.gui_ref = gui_ref  # Reference to main GUI
        self.result = None  # Will be set to marker if saved, None if cancelled

        # Create modal window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Edit Marker: {self.format_time(marker['time_ms'])}")
        self.window.geometry("500x600")

        # Make modal
        self.window.transient(parent)
        self.window.grab_set()

        # Center on parent
        self.center_on_parent()

        # Handle window close (treat as cancel)
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # Build UI
        self.create_ui()

    def format_time(self, ms):
        """Format milliseconds as M:SS.mmm"""
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int(ms % 1000)
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

    def center_on_parent(self):
        """Center this window on the parent window"""
        self.window.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get this window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Calculate centered position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        self.window.geometry(f"+{x}+{y}")

    def create_version_history_section(self):
        """Create version history UI section at top of editor"""
        version_frame = tk.Frame(self.window, padx=20, pady=10, bg=COLORS.bg_secondary)
        version_frame.pack(fill=tk.X)

        # Title
        tk.Label(
            version_frame,
            text="Version History",
            font=("Arial", 10, "bold"),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(anchor=tk.W)

        # Version dropdown and buttons row
        controls_frame = tk.Frame(version_frame, bg=COLORS.bg_secondary)
        controls_frame.pack(fill=tk.X, pady=(5, 0))

        # Version dropdown
        tk.Label(
            controls_frame,
            text="Version:",
            font=("Arial", 9),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Get all versions
        versions = self.marker.get('versions', [])
        current_version = self.marker.get('current_version', 1)

        # Build version list for dropdown (newest first)
        version_options = []
        for v in sorted(versions, key=lambda x: x['version'], reverse=True):
            version_num = v['version']
            is_current = " (current)" if version_num == current_version else ""
            version_options.append(f"v{version_num}{is_current}")

        self.version_var = tk.StringVar(value=f"v{current_version} (current)")
        self.version_dropdown = ttk.Combobox(
            controls_frame,
            textvariable=self.version_var,
            values=version_options,
            state="readonly",
            width=15
        )
        self.version_dropdown.pack(side=tk.LEFT, padx=5)
        self.version_dropdown.bind("<<ComboboxSelected>>", self.on_version_selected)

        # Rollback button
        self.rollback_btn = tk.Button(
            controls_frame,
            text="Rollback",
            command=self.on_rollback_version,
            font=("Arial", 9),
            bg=COLORS.btn_warning_bg,
            fg=COLORS.btn_warning_fg,
            width=10
        )
        self.rollback_btn.pack(side=tk.LEFT, padx=5)

        # Play button
        self.play_version_btn = tk.Button(
            controls_frame,
            text="▶ Play",
            command=self.on_play_version,
            font=("Arial", 9),
            bg=COLORS.btn_success_bg,
            fg=COLORS.btn_success_fg,
            width=10
        )
        self.play_version_btn.pack(side=tk.LEFT, padx=5)

        # Version metadata display
        self.metadata_frame = tk.Frame(version_frame, bg=COLORS.bg_secondary)
        self.metadata_frame.pack(fill=tk.X, pady=(5, 0))

        self.metadata_label = tk.Label(
            self.metadata_frame,
            text="",
            font=("Arial", 8),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_tertiary,
            justify=tk.LEFT
        )
        self.metadata_label.pack(anchor=tk.W)

        # Update metadata for current version
        self.update_version_metadata()

    def get_selected_version_number(self):
        """Extract version number from dropdown selection"""
        selected = self.version_var.get()
        # Format: "v2 (current)" or "v1"
        version_str = selected.split()[0]  # Get "v2"
        return int(version_str[1:])  # Remove 'v' and convert to int

    def update_version_metadata(self):
        """Update the metadata display for selected version"""
        selected_version_num = self.get_selected_version_number()
        versions = self.marker.get('versions', [])

        # Find the selected version data
        version_data = None
        for v in versions:
            if v['version'] == selected_version_num:
                version_data = v
                break

        if not version_data:
            self.metadata_label.config(text="No metadata available")
            return

        # Build metadata string
        created_at = version_data.get('created_at', 'Unknown')
        status = version_data.get('status', 'unknown')
        asset_id = version_data.get('asset_id', 'N/A')
        asset_file = version_data.get('asset_file', 'N/A')

        # Format created_at if it's a datetime string
        if 'T' in created_at:
            # ISO format: 2025-12-27T10:30:00
            date_part = created_at.split('T')[0]
            time_part = created_at.split('T')[1].split('.')[0] if '.' in created_at else created_at.split('T')[1]
            created_at = f"{date_part} {time_part}"

        metadata_text = (
            f"Created: {created_at}  |  "
            f"Status: {status}  |  "
            f"Asset: {asset_file}"
        )

        self.metadata_label.config(text=metadata_text)

    def on_version_selected(self, event=None):
        """Handle version dropdown change"""
        self.update_version_metadata()

    def on_rollback_version(self):
        """Rollback to selected version"""
        selected_version_num = self.get_selected_version_number()
        current_version = self.marker.get('current_version', 1)

        if selected_version_num == current_version:
            messagebox.showinfo(
                "Already Current",
                f"Version {selected_version_num} is already the current version."
            )
            return

        # Confirm rollback
        confirm = messagebox.askyesno(
            "Confirm Rollback",
            f"Roll back to version {selected_version_num}?\n\n"
            f"This will make v{selected_version_num} the active version.\n"
            f"The prompt data will be restored from this version."
        )

        if not confirm:
            return

        # Perform rollback using GUI method if available
        if self.gui_ref and hasattr(self.gui_ref, 'rollback_to_version'):
            success = self.gui_ref.rollback_to_version(self.marker, selected_version_num)
            if success:
                # Reload prompt data from selected version
                versions = self.marker.get('versions', [])
                for v in versions:
                    if v['version'] == selected_version_num:
                        prompt_data_snapshot = v.get('prompt_data_snapshot', {})
                        self.marker['prompt_data'] = prompt_data_snapshot
                        self.marker['current_version'] = selected_version_num
                        break

                # Update dropdown to show new current
                self.version_var.set(f"v{selected_version_num} (current)")

                # Rebuild content area with restored prompt data
                self.update_content_area()

                messagebox.showinfo(
                    "Rollback Complete",
                    f"Rolled back to version {selected_version_num}"
                )

    def on_play_version(self):
        """Play audio for selected version"""
        selected_version_num = self.get_selected_version_number()
        versions = self.marker.get('versions', [])

        # Find the selected version data
        version_data = None
        for v in versions:
            if v['version'] == selected_version_num:
                version_data = v
                break

        if not version_data:
            messagebox.showerror("No Version", "Selected version not found.")
            return

        asset_file = version_data.get('asset_file')
        if not asset_file:
            messagebox.showerror(
                "No Audio",
                f"Version {selected_version_num} has no generated audio file."
            )
            return

        # Build file path
        marker_type = self.marker.get('type', 'sfx')
        file_path = os.path.join("generated_audio", marker_type, asset_file)

        # Check if file exists
        if not os.path.exists(file_path):
            messagebox.showerror(
                "File Not Found",
                f"Audio file not found:\n{file_path}"
            )
            return

        # Play using GUI's audio player if available
        if self.gui_ref and hasattr(self.gui_ref, 'audio_player'):
            success = self.gui_ref.audio_player.play_audio_file(file_path)
            if not success:
                messagebox.showerror(
                    "Playback Error",
                    f"Failed to play audio file:\n{file_path}"
                )
        else:
            messagebox.showinfo(
                "Audio Player Not Available",
                "Cannot play audio - audio player not initialized."
            )

    def create_ui(self):
        """Build the editor UI"""
        # Version History section (at top)
        self.create_version_history_section()

        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Top section: Type dropdown
        type_frame = tk.Frame(self.window, padx=20, pady=10)
        type_frame.pack(fill=tk.X)

        tk.Label(type_frame, text="Type:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.type_var = tk.StringVar(value=self.marker["type"])
        self.type_dropdown = ttk.Combobox(
            type_frame,
            textvariable=self.type_var,
            values=["sfx", "music", "voice"],
            state="readonly",
            width=15
        )
        self.type_dropdown.pack(side=tk.LEFT)
        self.type_dropdown.bind("<<ComboboxSelected>>", self.on_type_changed)

        # Name field
        name_frame = tk.Frame(self.window, padx=20, pady=10)
        name_frame.pack(fill=tk.X)

        tk.Label(name_frame, text="Name:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        self.name_entry = tk.Entry(
            name_frame,
            font=("Arial", 10),
            width=40,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Load existing name
        marker_name = self.marker.get("name", "")
        if marker_name:
            self.name_entry.insert(0, marker_name)

        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Dynamic content area (changes based on type)
        self.content_frame = tk.Frame(self.window, padx=20, pady=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Load content for current type
        self.update_content_area()

        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Bottom section: Cancel/Save buttons
        button_frame = tk.Frame(self.window, padx=20, pady=15)
        button_frame.pack(fill=tk.X)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=12,
            font=("Arial", 10)
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            button_frame,
            text="Save",
            command=self.on_save,
            bg=COLORS.btn_primary_bg,
            fg=COLORS.btn_primary_fg,
            width=12,
            font=("Arial", 10, "bold")
        ).pack(side=tk.RIGHT, padx=5)

    def on_type_changed(self, event=None):
        """Handle type dropdown change - update content area"""
        new_type = self.type_var.get()
        old_type = self.marker["type"]

        # If type hasn't actually changed, no action needed
        if new_type == old_type:
            return

        # Check if user has existing prompt data that might be lost
        has_data = False
        if "prompt_data" in self.marker and self.marker["prompt_data"]:
            prompt_data = self.marker["prompt_data"]

            # Check if there's any non-empty data
            if old_type == "sfx":
                has_data = bool(prompt_data.get("description", "").strip())
            elif old_type == "voice":
                has_data = bool(prompt_data.get("text", "").strip()) or bool(prompt_data.get("voice_profile", "").strip())
            elif old_type == "music":
                has_data = bool(prompt_data.get("positiveGlobalStyles")) or bool(prompt_data.get("negativeGlobalStyles")) or bool(prompt_data.get("sections"))

        # Warn user if they have data that will be lost
        if has_data:
            response = messagebox.askyesno(
                "Confirm Type Change",
                f"Changing from {old_type.upper()} to {new_type.upper()} will reset the prompt data.\n\n"
                "This cannot be undone. Continue?",
                parent=self.window,
                icon='warning'
            )

            if not response:
                # User cancelled - revert dropdown to old type
                self.type_var.set(old_type)
                return

        # Update marker type
        self.marker["type"] = new_type

        # Reset prompt_data to default for new type
        self.marker["prompt_data"] = self.gui_ref.create_default_prompt_data(new_type) if self.gui_ref else {}

        # Clear and rebuild content area
        self.update_content_area()

    def update_content_area(self):
        """Update the content area based on current marker type"""
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        marker_type = self.marker["type"]

        # Call appropriate content creation method
        if marker_type == "sfx":
            self.create_sfx_content()
        elif marker_type == "voice":
            self.create_voice_content()  # Will implement in Checkpoint 6
        elif marker_type == "music":
            self.create_music_content()  # Will implement in Checkpoints 7-8
        else:
            tk.Label(
                self.content_frame,
                text=f"Unknown marker type: {marker_type}",
                font=("Arial", 12),
                fg="#666"
            ).pack(expand=True)

    def create_sfx_content(self):
        """Create SFX editor content - single description field"""
        # Ensure prompt_data exists
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {"description": ""}

        prompt_data = self.marker["prompt_data"]

        # Label
        tk.Label(
            self.content_frame,
            text="SFX Description:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        # Multi-line text entry
        self.sfx_description = tk.Text(
            self.content_frame,
            height=4,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.sfx_description.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Load existing description
        description = prompt_data.get("description", "")
        if description:
            self.sfx_description.insert("1.0", description)

        # Set focus to show cursor
        self.sfx_description.focus_set()

        # Hint text
        tk.Label(
            self.content_frame,
            text="Describe the sound effect to be generated (e.g., 'UI click, subtle, clean')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W)

    def create_voice_content(self):
        """Create Voice editor content - voice profile + text fields"""
        # Ensure prompt_data exists
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {"voice_profile": "", "text": ""}

        prompt_data = self.marker["prompt_data"]

        # Voice Profile field
        tk.Label(
            self.content_frame,
            text="Voice Profile:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.voice_profile_entry = tk.Entry(
            self.content_frame,
            font=("Arial", 10),
            width=50,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.voice_profile_entry.pack(fill=tk.X, pady=(0, 5))

        # Load existing voice profile
        voice_profile = prompt_data.get("voice_profile", "")
        if voice_profile:
            self.voice_profile_entry.insert(0, voice_profile)

        # Hint for voice profile
        tk.Label(
            self.content_frame,
            text="Optional: e.g., 'Warm female narrator, Australian accent'",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 15))

        # Text to speak field
        tk.Label(
            self.content_frame,
            text="Text to Speak:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.voice_text = tk.Text(
            self.content_frame,
            height=4,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.voice_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Load existing text
        text = prompt_data.get("text", "")
        if text:
            self.voice_text.insert("1.0", text)

        # Set focus to show cursor (text field is required, so focus here)
        self.voice_text.focus_set()

        # Hint for text
        tk.Label(
            self.content_frame,
            text="Required: The exact words to be spoken",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W)

    def create_music_content(self):
        """Create Music editor content - global styles + sections list"""
        # Ensure prompt_data exists with music structure
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {
                "positiveGlobalStyles": [],
                "negativeGlobalStyles": [],
                "sections": []
            }

        prompt_data = self.marker["prompt_data"]

        # Global Positive Styles
        tk.Label(
            self.content_frame,
            text="Global Positive Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.music_positive_styles = tk.Text(
            self.content_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.music_positive_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing positive styles
        positive_styles = prompt_data.get("positiveGlobalStyles", [])
        if positive_styles:
            self.music_positive_styles.insert("1.0", ", ".join(positive_styles))

        # Set focus to show cursor
        self.music_positive_styles.focus_set()

        # Hint for positive styles
        tk.Label(
            self.content_frame,
            text="Comma-separated styles (e.g., 'electronic, fast-paced, energetic')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Global Negative Styles
        tk.Label(
            self.content_frame,
            text="Global Negative Styles:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        self.music_negative_styles = tk.Text(
            self.content_frame,
            height=3,
            width=50,
            font=("Arial", 10),
            wrap=tk.WORD,
            bg=COLORS.bg_input,
            fg=COLORS.fg_input
        )
        self.music_negative_styles.pack(fill=tk.X, pady=(0, 5))

        # Load existing negative styles
        negative_styles = prompt_data.get("negativeGlobalStyles", [])
        if negative_styles:
            self.music_negative_styles.insert("1.0", ", ".join(negative_styles))

        # Hint for negative styles
        tk.Label(
            self.content_frame,
            text="Comma-separated styles to avoid (e.g., 'acoustic, slow, ambient')",
            font=("Arial", 9),
            fg="#666"
        ).pack(anchor=tk.W, pady=(0, 10))

        # Sections
        tk.Label(
            self.content_frame,
            text="Sections:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        # Sections listbox
        sections_frame = tk.Frame(self.content_frame)
        sections_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.music_sections_listbox = tk.Listbox(
            sections_frame,
            height=4,
            font=("Arial", 10)
        )
        self.music_sections_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for sections
        scrollbar = tk.Scrollbar(sections_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.music_sections_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.music_sections_listbox.yview)

        # Double-click to edit section
        self.music_sections_listbox.bind("<Double-Button-1>", self.on_section_double_click)

        # Load existing sections
        self.update_music_sections_list()

        # Section buttons
        section_buttons_frame = tk.Frame(self.content_frame)
        section_buttons_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(
            section_buttons_frame,
            text="+ Add Section",
            command=self.add_music_section,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            section_buttons_frame,
            text="Remove Section",
            command=self.remove_music_section,
            font=("Arial", 9)
        ).pack(side=tk.LEFT)

        # Note about section editing
        tk.Label(
            self.content_frame,
            text="Note: Section editing will be available in Checkpoint 8",
            font=("Arial", 9),
            fg="#999",
            style="italic"
        ).pack(anchor=tk.W, pady=(5, 0))

    def update_music_sections_list(self):
        """Update the sections listbox display"""
        self.music_sections_listbox.delete(0, tk.END)

        sections = self.marker["prompt_data"].get("sections", [])
        for section in sections:
            name = section.get("sectionName", "Unnamed")
            duration = section.get("durationMs", 0)
            display = f"{name} - {duration}ms"
            self.music_sections_listbox.insert(tk.END, display)

    def add_music_section(self):
        """Add a new placeholder section"""
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {
                "positiveGlobalStyles": [],
                "negativeGlobalStyles": [],
                "sections": []
            }

        sections = self.marker["prompt_data"].get("sections", [])
        section_num = len(sections) + 1

        new_section = {
            "sectionName": f"Section {section_num}",
            "durationMs": 1000,
            "positiveLocalStyles": [],
            "negativeLocalStyles": [],
            "lines": []
        }

        sections.append(new_section)
        self.marker["prompt_data"]["sections"] = sections
        self.update_music_sections_list()

    def remove_music_section(self):
        """Remove selected section"""
        selection = self.music_sections_listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "No Selection",
                "Please select a section to remove",
                parent=self.window
            )
            return

        index = selection[0]
        sections = self.marker["prompt_data"].get("sections", [])
        sections.pop(index)
        self.marker["prompt_data"]["sections"] = sections
        self.update_music_sections_list()

    def on_section_double_click(self, event):
        """Handle double-click on section - open section editor"""
        selection = self.music_sections_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        sections = self.marker["prompt_data"].get("sections", [])
        if index >= len(sections):
            return

        section = sections[index]
        # Open nested section editor
        editor = MusicSectionEditorWindow(
            parent=self.window,
            section=section,
            section_index=index,
            on_save_callback=self.on_section_edited
        )

    def on_section_edited(self, updated_section, index):
        """Callback when section is edited and saved"""
        sections = self.marker["prompt_data"].get("sections", [])
        sections[index] = updated_section
        self.marker["prompt_data"]["sections"] = sections
        self.update_music_sections_list()
        print(f"✓ Updated section at index {index}: {updated_section['sectionName']}")

    def on_cancel(self):
        """Cancel button - close without saving"""
        self.result = None
        try:
            self.window.destroy()
        except Exception as e:
            print(f"Warning: Error closing editor window: {e}")
        # Call cancel callback if provided
        if self.on_cancel_callback:
            try:
                self.on_cancel_callback()
            except Exception as e:
                print(f"Warning: Error in cancel callback: {e}")

    def on_save(self):
        """Save button - validate and save changes"""
        try:
            # Save marker name
            marker_name = self.name_entry.get().strip()
            self.marker["name"] = marker_name

            marker_type = self.marker["type"]

            # Capture data from UI and validate based on type
            if marker_type == "sfx":
                if not self.save_sfx_data():
                    return  # Validation failed
            elif marker_type == "voice":
                if not self.save_voice_data():  # Will implement in Checkpoint 6
                    return
            elif marker_type == "music":
                if not self.save_music_data():  # Will implement in Checkpoints 7-8
                    return
            else:
                messagebox.showerror(
                    "Unknown Type",
                    f"Unknown marker type: {marker_type}",
                    parent=self.window
                )
                return

            # Check if prompt_data actually changed
            prompt_data_changed = self._check_if_prompt_changed()

            # If prompt data changed, create new version (not_yet_generated status)
            if prompt_data_changed and self.gui_ref and hasattr(self.gui_ref, 'add_new_version'):
                try:
                    new_version = self.gui_ref.add_new_version(self.marker, self.marker["prompt_data"])
                    # Update current version in marker
                    self.marker["current_version"] = new_version
                except Exception as e:
                    print(f"Warning: Failed to create new version: {e}")

            # If validation passed, save and close
            self.result = self.marker

            try:
                self.on_save_callback(self.marker, self.marker_index)
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save marker:\n{str(e)}",
                    parent=self.window
                )
                return

            try:
                self.window.destroy()
            except Exception as e:
                print(f"Warning: Error closing editor window: {e}")

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An unexpected error occurred:\n{str(e)}",
                parent=self.window
            )
            print(f"Error in on_save: {e}")
            import traceback
            traceback.print_exc()

    def _check_if_prompt_changed(self):
        """Check if prompt_data changed from current version's snapshot"""
        # Get current version's prompt snapshot
        current_version = self.marker.get('current_version', 1)
        versions = self.marker.get('versions', [])

        for v in versions:
            if v['version'] == current_version:
                snapshot = v.get('prompt_data_snapshot', {})
                # Compare with current prompt_data
                return self.marker.get('prompt_data') != snapshot

        # If no version found, consider it changed
        return True

    def save_sfx_data(self):
        """Save SFX data from UI to marker - returns True if valid"""
        try:
            description = self.sfx_description.get("1.0", "end-1c").strip()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read SFX description:\n{str(e)}",
                parent=self.window
            )
            return False

        # Validation: description cannot be empty
        if not description:
            messagebox.showwarning(
                "Validation Error",
                "SFX description cannot be empty",
                parent=self.window
            )
            return False

        # Save to marker
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {}
        self.marker["prompt_data"]["description"] = description
        return True

    def save_voice_data(self):
        """Save Voice data from UI to marker - returns True if valid"""
        try:
            voice_profile = self.voice_profile_entry.get().strip()
            text = self.voice_text.get("1.0", "end-1c").strip()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read voice data:\n{str(e)}",
                parent=self.window
            )
            return False

        # Validation: text cannot be empty (voice_profile is optional)
        if not text:
            messagebox.showwarning(
                "Validation Error",
                "Text to speak cannot be empty",
                parent=self.window
            )
            return False

        # Save to marker
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {}
        self.marker["prompt_data"]["voice_profile"] = voice_profile
        self.marker["prompt_data"]["text"] = text
        return True

    def save_music_data(self):
        """Save Music data from UI to marker - returns True if valid"""
        try:
            # Get text from positive/negative styles fields
            positive_text = self.music_positive_styles.get("1.0", "end-1c").strip()
            negative_text = self.music_negative_styles.get("1.0", "end-1c").strip()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to read music data:\n{str(e)}",
                parent=self.window
            )
            return False

        # Parse comma-separated styles into lists
        positive_styles = []
        if positive_text:
            positive_styles = [s.strip() for s in positive_text.split(",") if s.strip()]

        negative_styles = []
        if negative_text:
            negative_styles = [s.strip() for s in negative_text.split(",") if s.strip()]

        # Validation: At least one positive style should be provided
        if not positive_styles:
            messagebox.showwarning(
                "Validation Error",
                "Please provide at least one positive style for the music",
                parent=self.window
            )
            return False

        # Save to marker (sections are already in prompt_data from add/remove operations)
        if "prompt_data" not in self.marker:
            self.marker["prompt_data"] = {
                "positiveGlobalStyles": [],
                "negativeGlobalStyles": [],
                "sections": []
            }

        self.marker["prompt_data"]["positiveGlobalStyles"] = positive_styles
        self.marker["prompt_data"]["negativeGlobalStyles"] = negative_styles
        # sections are already updated by add/remove methods
        return True


# ============================================================================
# AUDIO PLAYER - Simple audio playback for generated files
# ============================================================================

import pygame
import os
from pathlib import Path

# DON'T initialize pygame here - it conflicts with Tkinter on macOS
# pygame.init() will be called in AudioPlayer.__init__ instead

# Import ElevenLabs API for audio generation
try:
    from elevenlabs_api import generate_sfx, generate_voice, generate_music
except ImportError:
    print("WARNING: elevenlabs_api.py not found. Audio generation will not work.")
    generate_sfx = None
    generate_voice = None
    generate_music = None

class AudioPlayer:
    """
    Simple audio player for playing generated marker audio files

    Uses pygame.mixer for reliable cross-platform playback
    """

    def __init__(self):
        """Initialize the audio player"""
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self.current_sound = None
        self.current_marker_index = None
        self.is_playing = False

        print("✓ AudioPlayer initialized")

    def play_audio_file(self, file_path, marker_index=None):
        """
        Play an audio file

        Args:
            file_path: Path to audio file (MP3, WAV, OGG)
            marker_index: Optional marker index for tracking

        Returns:
            True if playback started, False if file not found or error
        """
        # Stop any currently playing audio
        self.stop_audio()

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"✗ Audio file not found: {file_path}")
            return False

        try:
            # Load and play the audio file
            self.current_sound = pygame.mixer.Sound(file_path)
            self.current_sound.play()
            self.current_marker_index = marker_index
            self.is_playing = True

            print(f"▶ Playing: {Path(file_path).name}")
            return True

        except Exception as e:
            print(f"✗ Error playing audio: {e}")
            self.current_sound = None
            self.is_playing = False
            return False

    def stop_audio(self):
        """Stop currently playing audio"""
        if self.current_sound is not None:
            self.current_sound.stop()
            print(f"⏸ Stopped audio")

        self.current_sound = None
        self.current_marker_index = None
        self.is_playing = False

    def is_playing_marker(self, marker_index):
        """
        Check if a specific marker's audio is currently playing

        Args:
            marker_index: Index to check

        Returns:
            True if this marker is playing
        """
        return self.is_playing and self.current_marker_index == marker_index

    def get_playing_status(self):
        """
        Get current playback status

        Returns:
            Tuple of (is_playing, marker_index)
        """
        # Update is_playing status based on pygame mixer
        if self.current_sound is not None:
            # Check if sound is actually playing
            if not pygame.mixer.get_busy():
                # Sound finished playing
                self.is_playing = False
                self.current_marker_index = None
                self.current_sound = None

        return (self.is_playing, self.current_marker_index)


# ============================================================================
# MARKER ROW - Custom row widget for marker list
# ============================================================================

class MarkerRow:
    """
    Custom widget representing a single marker row with interactive controls

    Layout: [▶] [🔄] 0:00.150 | SFX | Marker Name | ✓ v1
    """

    def __init__(self, parent, marker, marker_index, gui_ref):
        """
        Initialize a marker row

        Args:
            parent: Parent frame/canvas to pack into
            marker: Marker data dict
            marker_index: Index in markers list
            gui_ref: Reference to main AudioMapperGUI instance
        """
        self.marker = marker
        self.marker_index = marker_index
        self.gui = gui_ref
        self.is_selected = False

        # Main row frame
        self.frame = tk.Frame(parent, bg=COLORS.bg_secondary, relief=tk.RAISED, bd=1)
        self.frame.pack(fill=tk.X, padx=2, pady=1)

        # Row click handling (for selection)
        self.frame.bind("<Button-1>", self.on_row_click)
        self.frame.bind("<Double-Button-1>", self.on_row_double_click)

        # Create row contents
        self.create_widgets()

    def create_widgets(self):
        """Build the row UI components"""
        # Play button
        self.play_btn = tk.Button(
            self.frame,
            text="▶",
            width=3,
            height=1,
            command=self.on_play_click,
            bg=COLORS.info_bg,
            fg=COLORS.fg_primary,
            font=("Arial", 10),
            relief=tk.RAISED,
            bd=1
        )
        self.play_btn.pack(side=tk.LEFT, padx=(5, 2), pady=2)
        ToolTip(self.play_btn, "Play current version (P)")

        # Generate button
        self.generate_btn = tk.Button(
            self.frame,
            text="🔄",
            width=3,
            height=1,
            command=self.on_generate_click,
            bg=COLORS.success_bg,
            fg=COLORS.fg_primary,
            font=("Arial", 10),
            relief=tk.RAISED,
            bd=1
        )
        self.generate_btn.pack(side=tk.LEFT, padx=2, pady=2)
        ToolTip(self.generate_btn, "Generate/Regenerate audio (G/R)")

        # Time label
        time_str = self.format_time(self.marker["time_ms"])
        time_label = tk.Label(
            self.frame,
            text=time_str,
            width=10,
            font=("Courier", 10),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary,
            anchor=tk.W
        )
        time_label.pack(side=tk.LEFT, padx=5)
        time_label.bind("<Button-1>", self.on_row_click)
        time_label.bind("<Double-Button-1>", self.on_row_double_click)

        # Type label
        marker_type = self.marker["type"].upper()
        type_bg, type_fg = self.get_type_color(self.marker["type"])
        type_label = tk.Label(
            self.frame,
            text=marker_type,
            width=8,
            font=("Arial", 10, "bold"),
            bg=type_bg,
            fg=type_fg,
            anchor=tk.W
        )
        type_label.pack(side=tk.LEFT, padx=2)
        type_label.bind("<Button-1>", self.on_row_click)
        type_label.bind("<Double-Button-1>", self.on_row_double_click)

        # Name label
        marker_name = self.marker.get("name", "")
        name_display = marker_name if marker_name else "(unnamed)"
        name_label = tk.Label(
            self.frame,
            text=name_display,
            width=30,
            font=("Arial", 10),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary,
            anchor=tk.W
        )
        name_label.pack(side=tk.LEFT, padx=5)
        name_label.bind("<Button-1>", self.on_row_click)
        name_label.bind("<Double-Button-1>", self.on_row_double_click)

        # Status icon + Version badge
        status_icon = self.get_status_icon(self.marker.get("status", "not yet generated"))
        current_version = self.marker.get("current_version", 1)
        status_version_text = f"{status_icon} v{current_version}"

        status_label = tk.Label(
            self.frame,
            text=status_version_text,
            width=8,
            font=("Arial", 10),
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary,
            anchor=tk.W
        )
        status_label.pack(side=tk.LEFT, padx=5)
        status_label.bind("<Button-1>", self.on_row_click)
        status_label.bind("<Double-Button-1>", self.on_row_double_click)

        # Add tooltip for status icon
        status_tooltips = {
            "not_yet_generated": "⭕ Not yet generated",
            "generating": "⏳ Generating...",
            "generated": "✓ Generated successfully",
            "failed": "⚠️ Generation failed"
        }
        current_status = self.gui.get_current_version_data(self.marker)
        if current_status:
            status_key = current_status.get("status", "not_yet_generated")
            tooltip_text = status_tooltips.get(status_key, "Unknown status")
            ToolTip(status_label, tooltip_text)

    def format_time(self, ms):
        """Format milliseconds as M:SS.mmm"""
        total_seconds = ms / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int(ms % 1000)
        return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

    def get_type_color(self, marker_type):
        """Get background and foreground colors for marker type"""
        type_colors = {
            "sfx": (COLORS.sfx_bg, COLORS.sfx_fg),
            "music": (COLORS.music_bg, COLORS.music_fg),
            "voice": (COLORS.voice_bg, COLORS.voice_fg)
        }
        return type_colors.get(marker_type, (COLORS.bg_tertiary, COLORS.fg_primary))

    def get_status_icon(self, status):
        """Get icon for marker status"""
        status_icons = {
            "not yet generated": "⭕",
            "generating": "⏳",
            "generated": "✓",
            "failed": "⚠️"
        }
        return status_icons.get(status, "⭕")

    def on_row_click(self, event=None):
        """Handle row click - select this marker"""
        self.gui.select_marker_row(self.marker_index)

    def on_row_double_click(self, event=None):
        """Handle double-click - edit marker"""
        self.gui.open_marker_editor(self.marker, self.marker_index)

    def on_play_click(self):
        """Handle play button click"""
        print(f"▶ Play marker {self.marker_index}: {self.marker.get('name', '(unnamed)')}")
        # Stub for now - will implement in Checkpoint 3
        self.gui.play_marker_audio(self.marker_index)

    def on_generate_click(self):
        """Handle generate button click"""
        print(f"🔄 Generate marker {self.marker_index}: {self.marker.get('name', '(unnamed)')}")
        # Stub for now - will implement in Checkpoint 5
        self.gui.generate_marker_audio(self.marker_index)

    def set_selected(self, selected):
        """Set selection state and update visual appearance"""
        self.is_selected = selected
        if selected:
            self.frame.config(bg=COLORS.selection_bg, relief=tk.SUNKEN, bd=2)
        else:
            self.frame.config(bg=COLORS.bg_secondary, relief=tk.RAISED, bd=1)

    def update_display(self):
        """Refresh row display (useful when marker data changes)"""
        # Destroy and recreate widgets
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.create_widgets()


class AudioMapperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Mapper - Timecode Mapping Tool")
        self.root.geometry("1200x800")

        # Video player components
        self.video_capture = None
        self.current_frame = None
        self.photo_image = None

        # State variables
        self.current_time_ms = 0
        self.duration_ms = 0
        self.fps = 30  # Default FPS
        self.total_frames = 0
        self.is_playing = False
        self.video_loaded = False
        self.markers = []
        self.template_id = ""
        self.template_name = ""

        # Undo/redo system
        self.history = HistoryManager(max_history=50)

        # Audio player for marker audio playback
        self.audio_player = AudioPlayer()

        # Auto-assembly setting
        self.auto_assemble_enabled = tk.BooleanVar(value=False)

        # Drag state for marker repositioning
        self.dragging_marker = None
        self.drag_start_x = None
        self.drag_marker_index = None

        # Selected marker for keyboard nudging
        self.selected_marker_index = None

        # Waveform data
        self.waveform_data = None
        self.waveform_canvas_height = 80

        # Film strip data
        self.filmstrip_frames = []  # List of thumbnail images
        self.filmstrip_frame_times = []  # Corresponding time positions in ms
        self.filmstrip_canvas_height = 60
        self.filmstrip_thumb_width = 80
        self.filmstrip_thumb_height = 45

        # Build UI
        self.create_menu_bar()
        self.create_video_frame()
        self.create_filmstrip_display()
        self.create_waveform_display()
        self.create_timeline_controls()
        self.create_marker_controls()
        self.create_marker_list()

        # Bind keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Start update loop for timeline
        self.update_timeline()

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Video", command=self.load_video)
        file_menu.add_command(label="Create Blank Timeline", command=self.create_blank_timeline)
        file_menu.add_separator()
        file_menu.add_command(label="Export JSON", command=self.export_json)
        file_menu.add_command(label="Import JSON", command=self.import_json)
        file_menu.add_separator()
        file_menu.add_checkbutton(
            label="Auto-assemble after generation",
            variable=self.auto_assemble_enabled,
            onvalue=True,
            offvalue=False
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def create_video_frame(self):
        """Create video player frame with Canvas"""
        video_container = tk.Frame(self.root, bg="black", height=400)
        video_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        # Video display canvas
        self.video_canvas = tk.Canvas(video_container, bg="black", highlightthickness=0)
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # No video loaded message
        self.video_canvas.create_text(
            600, 200,
            text="No video loaded\nFile → Open Video or Create Blank Timeline",
            fill="white",
            font=("Arial", 14),
            tags="placeholder"
        )

    def create_filmstrip_display(self):
        """Create film strip visualization canvas"""
        filmstrip_container = tk.Frame(self.root, bg="#2C2C2C")
        filmstrip_container.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Film strip canvas
        self.filmstrip_canvas = tk.Canvas(
            filmstrip_container,
            bg="#1E1E1E",
            height=self.filmstrip_canvas_height,
            highlightthickness=1,
            highlightbackground="#444"
        )
        self.filmstrip_canvas.pack(fill=tk.BOTH, expand=True)

        # Placeholder text
        self.filmstrip_canvas.create_text(
            600, 30,
            text="Film strip will appear here",
            fill="#666",
            font=("Arial", 10),
            tags="filmstrip_placeholder"
        )

        # Bind click event for scrubbing
        self.filmstrip_canvas.bind("<Button-1>", self.on_filmstrip_click)

        # Bind resize event to redraw filmstrip
        self.filmstrip_canvas.bind("<Configure>", self.on_filmstrip_resize)

    def create_waveform_display(self):
        """Create waveform visualization canvas"""
        waveform_container = tk.Frame(self.root, bg="#2C2C2C")
        waveform_container.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Waveform canvas
        self.waveform_canvas = tk.Canvas(
            waveform_container,
            bg="#1E1E1E",
            height=self.waveform_canvas_height,
            highlightthickness=1,
            highlightbackground="#444"
        )
        self.waveform_canvas.pack(fill=tk.BOTH, expand=True)

        # Placeholder text
        self.waveform_canvas.create_text(
            600, 40,
            text="Audio waveform will appear here",
            fill="#666",
            font=("Arial", 10),
            tags="waveform_placeholder"
        )

        # Bind click event for scrubbing
        self.waveform_canvas.bind("<Button-1>", self.on_waveform_click)

        # Bind resize event to redraw waveform
        self.waveform_canvas.bind("<Configure>", self.on_waveform_resize)

    def create_timeline_controls(self):
        """Create timeline scrubber and controls"""
        timeline_frame = tk.Frame(self.root)
        timeline_frame.pack(fill=tk.X, padx=10, pady=5)

        # Playback controls
        control_frame = tk.Frame(timeline_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        self.play_button = tk.Button(control_frame, text="▶ Play", command=self.toggle_playback, width=10)
        self.play_button.pack(side=tk.LEFT, padx=5)

        tk.Button(control_frame, text="◀◀ -50ms", command=lambda: self.step_time(-50), width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="50ms ▶▶", command=lambda: self.step_time(50), width=10).pack(side=tk.LEFT, padx=5)

        # Timestamp display
        self.timestamp_label = tk.Label(control_frame, text="00:00:00.000", font=("Courier", 14, "bold"))
        self.timestamp_label.pack(side=tk.LEFT, padx=20)

        # FPS display (for video mode)
        self.fps_label = tk.Label(control_frame, text="", font=("Courier", 10))
        self.fps_label.pack(side=tk.LEFT, padx=10)

        # Timeline slider
        slider_frame = tk.Frame(timeline_frame)
        slider_frame.pack(fill=tk.X)

        tk.Label(slider_frame, text="Timeline:").pack(side=tk.LEFT, padx=(0, 5))

        self.timeline_slider = ttk.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.on_timeline_change
        )
        self.timeline_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_marker_controls(self):
        """Create marker input controls - three button design"""
        marker_frame = tk.LabelFrame(self.root, text="Add Marker", padx=10, pady=10)
        marker_frame.pack(fill=tk.X, padx=10, pady=5)

        # Button container
        button_container = tk.Frame(marker_frame)
        button_container.pack(fill=tk.X, pady=5)

        tk.Label(button_container, text="Add Marker:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))

        # Three colored buttons for each marker type
        tk.Button(
            button_container,
            text="SFX",
            command=lambda: self.add_marker_by_type("sfx"),
            bg=COLORS.sfx_bg,
            fg=COLORS.sfx_fg,
            font=("Arial", 10, "bold"),
            width=10,
            height=2,
            relief=tk.RAISED,
            bd=2
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_container,
            text="Music",
            command=lambda: self.add_marker_by_type("music"),
            bg=COLORS.music_bg,
            fg=COLORS.music_fg,
            font=("Arial", 10, "bold"),
            width=10,
            height=2,
            relief=tk.RAISED,
            bd=2
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_container,
            text="Voice",
            command=lambda: self.add_marker_by_type("voice"),
            bg=COLORS.voice_bg,
            fg=COLORS.voice_fg,
            font=("Arial", 10, "bold"),
            width=10,
            height=2,
            relief=tk.RAISED,
            bd=2
        ).pack(side=tk.LEFT, padx=5)

    def create_marker_list(self):
        """Create marker list display with custom interactive rows"""
        list_frame = tk.LabelFrame(self.root, text="Markers", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        # Main container for marker list and export button side by side
        main_container = tk.Frame(list_frame)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Scrollable marker list container
        list_container = tk.Frame(main_container)
        list_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create canvas with scrollbar for custom rows
        self.marker_canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, command=self.marker_canvas.yview)
        self.marker_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.marker_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame inside canvas to hold marker rows
        self.marker_rows_frame = tk.Frame(self.marker_canvas, bg="white")
        self.marker_canvas_window = self.marker_canvas.create_window(
            (0, 0),
            window=self.marker_rows_frame,
            anchor=tk.NW
        )

        # Configure canvas scrolling
        self.marker_rows_frame.bind("<Configure>", self.on_marker_frame_configure)
        self.marker_canvas.bind("<Configure>", self.on_marker_canvas_configure)

        # Store marker row widgets
        self.marker_row_widgets = []
        self.selected_marker_index = None

        # Right side panel - Export and batch operations
        export_container = tk.Frame(main_container, padx=10, width=180)
        export_container.pack(side=tk.RIGHT, fill=tk.Y)
        export_container.pack_propagate(False)

        # Export button with symbol and text
        export_btn = tk.Button(
            export_container,
            text="⬇\nExport\nJSON",
            command=self.export_json,
            bg=COLORS.info_bg,
            fg=COLORS.fg_primary,
            font=("Arial", 9, "bold"),
            width=18,
            height=4,
            relief=tk.RAISED,
            bd=2
        )
        export_btn.pack(pady=(0, 10), fill=tk.X)

        # Batch operation buttons - stacked vertically
        tk.Button(
            export_container,
            text="🔄 Generate All Missing",
            command=self.batch_generate_missing,
            bg=COLORS.btn_success_bg,
            fg=COLORS.btn_success_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2,
            relief=tk.RAISED,
            bd=2
        ).pack(pady=2, fill=tk.X)

        tk.Button(
            export_container,
            text="🔄 Regenerate All",
            command=self.batch_regenerate_all,
            bg=COLORS.btn_warning_bg,
            fg=COLORS.btn_warning_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2,
            relief=tk.RAISED,
            bd=2
        ).pack(pady=2, fill=tk.X)

        tk.Button(
            export_container,
            text="🔄 Generate Type...",
            command=self.batch_generate_by_type,
            bg=COLORS.btn_primary_bg,
            fg=COLORS.btn_primary_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2,
            relief=tk.RAISED,
            bd=2
        ).pack(pady=2, fill=tk.X)

        tk.Button(
            export_container,
            text="🎵 Assemble Now",
            command=self.manual_assemble_audio,
            bg=COLORS.btn_special_bg,
            fg=COLORS.btn_special_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2,
            relief=tk.RAISED,
            bd=2
        ).pack(pady=2, fill=tk.X)

        # Control buttons
        button_frame = tk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(
            button_frame,
            text="Jump to Marker",
            command=self.jump_to_marker,
            width=15,
            height=2,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Delete Marker",
            command=self.delete_marker,
            bg=COLORS.btn_danger_bg,
            fg=COLORS.btn_danger_fg,
            width=15,
            height=2,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Clear All",
            command=self.clear_all_markers,
            width=15,
            height=2,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

    def on_marker_frame_configure(self, event=None):
        """Update scroll region when marker frame size changes"""
        self.marker_canvas.configure(scrollregion=self.marker_canvas.bbox("all"))

    def on_marker_canvas_configure(self, event):
        """Resize marker rows frame to match canvas width"""
        canvas_width = event.width
        self.marker_canvas.itemconfig(self.marker_canvas_window, width=canvas_width)

    def setup_keyboard_shortcuts(self):
        """Bind keyboard shortcuts"""
        # Track if shortcuts are enabled
        self.shortcuts_enabled = True

        # Bind shortcuts that check if enabled
        self.root.bind("<space>", lambda e: self.shortcuts_enabled and self.toggle_playback())
        self.root.bind("m", lambda e: self.shortcuts_enabled and self.add_marker())
        self.root.bind("M", lambda e: self.shortcuts_enabled and self.add_marker())
        self.root.bind("<Delete>", lambda e: self.shortcuts_enabled and self.delete_marker())
        self.root.bind("<BackSpace>", lambda e: self.shortcuts_enabled and self.delete_marker())

        # Arrow keys - context sensitive (nudge marker if selected, otherwise scrub timeline)
        self.root.bind("<Left>", lambda e: self.shortcuts_enabled and self.handle_left_arrow())
        self.root.bind("<Right>", lambda e: self.shortcuts_enabled and self.handle_right_arrow())

        # Shift+Arrow - frame-precise (nudge marker by frame if selected, otherwise step timeline by frame)
        self.root.bind("<Shift-Left>", lambda e: self.shortcuts_enabled and self.handle_shift_left_arrow())
        self.root.bind("<Shift-Right>", lambda e: self.shortcuts_enabled and self.handle_shift_right_arrow())

        # Alt/Cmd+Arrow - millisecond-precise (nudge marker by 1ms)
        self.root.bind("<Alt-Left>", lambda e: self.shortcuts_enabled and self.nudge_selected_marker(-1))
        self.root.bind("<Alt-Right>", lambda e: self.shortcuts_enabled and self.nudge_selected_marker(1))
        self.root.bind("<Command-Left>", lambda e: self.shortcuts_enabled and self.nudge_selected_marker(-1))
        self.root.bind("<Command-Right>", lambda e: self.shortcuts_enabled and self.nudge_selected_marker(1))

        # Undo/Redo (works on both macOS and other platforms)
        # On macOS: Cmd+Z / Cmd+Shift+Z
        # On other platforms: Ctrl+Z / Ctrl+Shift+Z
        self.root.bind("<Command-z>", lambda e: self.undo())  # macOS
        self.root.bind("<Control-z>", lambda e: self.undo())  # Windows/Linux
        self.root.bind("<Command-Shift-Z>", lambda e: self.redo())  # macOS
        self.root.bind("<Control-Shift-Z>", lambda e: self.redo())  # Windows/Linux
        self.root.bind("<Command-y>", lambda e: self.redo())  # macOS alternative
        self.root.bind("<Control-y>", lambda e: self.redo())  # Windows alternative

        # Marker operations (require a selected marker)
        self.root.bind("p", lambda e: self.shortcuts_enabled and self.play_selected_marker_shortcut())
        self.root.bind("P", lambda e: self.shortcuts_enabled and self.play_selected_marker_shortcut())
        self.root.bind("g", lambda e: self.shortcuts_enabled and self.generate_selected_marker_shortcut())
        self.root.bind("G", lambda e: self.shortcuts_enabled and self.generate_selected_marker_shortcut())
        self.root.bind("r", lambda e: self.shortcuts_enabled and self.regenerate_selected_marker_shortcut())
        self.root.bind("R", lambda e: self.shortcuts_enabled and self.regenerate_selected_marker_shortcut())

        # Deselect marker
        self.root.bind("<Escape>", lambda e: self.deselect_marker())

        # File operations
        self.root.bind("<Command-o>", lambda e: self.load_video())  # macOS
        self.root.bind("<Control-o>", lambda e: self.load_video())  # Windows/Linux

    def disable_shortcuts(self):
        """Disable keyboard shortcuts when typing in text boxes"""
        self.shortcuts_enabled = False

    def enable_shortcuts(self):
        """Re-enable keyboard shortcuts"""
        self.shortcuts_enabled = True

    def handle_left_arrow(self):
        """Context-sensitive left arrow: nudge marker or scrub timeline"""
        if self.selected_marker_index is not None:
            self.nudge_selected_marker(-50)
        else:
            self.step_time(-50)

    def handle_right_arrow(self):
        """Context-sensitive right arrow: nudge marker or scrub timeline"""
        if self.selected_marker_index is not None:
            self.nudge_selected_marker(50)
        else:
            self.step_time(50)

    def handle_shift_left_arrow(self):
        """Context-sensitive Shift+Left: nudge marker by frame or step timeline by frame"""
        if self.selected_marker_index is not None:
            self.nudge_selected_marker_by_frame(-1)
        else:
            self.step_frame(-1)

    def handle_shift_right_arrow(self):
        """Context-sensitive Shift+Right: nudge marker by frame or step timeline by frame"""
        if self.selected_marker_index is not None:
            self.nudge_selected_marker_by_frame(1)
        else:
            self.step_frame(1)

    def play_selected_marker_shortcut(self):
        """Play selected marker's audio (keyboard shortcut: P)"""
        if self.selected_marker_index is not None:
            self.play_marker_audio(self.selected_marker_index)
        else:
            # No marker selected - show brief info
            messagebox.showinfo(
                "No Marker Selected",
                "Select a marker first (click on it in the list or timeline)\n\n"
                "Keyboard shortcut: P → Play selected marker"
            )

    def generate_selected_marker_shortcut(self):
        """Generate audio for selected marker (keyboard shortcut: G)"""
        if self.selected_marker_index is not None:
            self.generate_marker_audio(self.selected_marker_index)
        else:
            # No marker selected - show brief info
            messagebox.showinfo(
                "No Marker Selected",
                "Select a marker first (click on it in the list or timeline)\n\n"
                "Keyboard shortcut: G → Generate selected marker"
            )

    def regenerate_selected_marker_shortcut(self):
        """Regenerate audio for selected marker (keyboard shortcut: R)"""
        if self.selected_marker_index is not None:
            # Regenerate is the same as generate - it creates a new version
            self.generate_marker_audio(self.selected_marker_index)
        else:
            # No marker selected - show brief info
            messagebox.showinfo(
                "No Marker Selected",
                "Select a marker first (click on it in the list or timeline)\n\n"
                "Keyboard shortcut: R → Regenerate selected marker"
            )

    def deselect_marker(self):
        """Deselect the currently selected marker"""
        if self.selected_marker_index is not None and self.selected_marker_index < len(self.marker_row_widgets):
            self.marker_row_widgets[self.selected_marker_index].set_selected(False)
        self.selected_marker_index = None
        self.redraw_marker_indicators()
        print("○ Marker deselected")

    # ========================================================================
    # MARKER DATA STRUCTURE HELPERS
    # ========================================================================

    def migrate_marker_to_new_format(self, marker):
        """Convert old marker format (prompt string) to new format (prompt_data)"""
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

    # ========================================================================
    # VERSION MANAGEMENT METHODS
    # ========================================================================

    def get_current_version_data(self, marker):
        """
        Get the current version object from a marker

        Returns the version object for the current active version, or None if no versions exist
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

    def add_new_version(self, marker, prompt_data):
        """
        Create a new version for a marker

        Args:
            marker: The marker dict to add version to
            prompt_data: The prompt_data to use for this version

        Returns:
            The new version number
        """
        from datetime import datetime

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

    def rollback_to_version(self, marker, version_num):
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

    def migrate_marker_to_version_format(self, marker):
        """
        Migrate a marker to the new version-based format

        Handles both old format (no versions) and ensures version structure exists
        """
        from datetime import datetime

        # If already has versions, just ensure it's valid
        if "versions" in marker and marker["versions"]:
            # Ensure current_version exists
            if "current_version" not in marker:
                marker["current_version"] = marker["versions"][-1]["version"]
            return marker

        # Create initial version from current marker state
        prompt_data = marker.get("prompt_data", self.create_default_prompt_data(marker.get("type", "sfx")))
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

    def get_prompt_preview(self, marker):
        """Get a short preview string of the prompt for display in marker list"""
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

    def create_default_prompt_data(self, marker_type):
        """Create empty but valid prompt_data structure for a given marker type"""
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

    # ========================================================================
    # VIDEO PLAYBACK METHODS (OpenCV)
    # ========================================================================

    def load_video(self):
        """Load video file using OpenCV"""
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.flv *.wmv"),
                ("All files", "*.*")
            ]
        )

        if not filepath:
            return

        # Release previous video if any
        if self.video_capture:
            self.video_capture.release()

        # Open video with OpenCV
        self.video_capture = cv2.VideoCapture(filepath)

        if not self.video_capture.isOpened():
            messagebox.showerror("Error", "Could not open video file")
            return

        # Get video properties
        self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration_ms = int((self.total_frames / self.fps) * 1000)

        # Update UI
        self.timeline_slider.config(to=self.duration_ms)
        self.video_loaded = True
        self.fps_label.config(text=f"{self.fps:.2f} FPS")

        # Remove placeholder
        self.video_canvas.delete("placeholder")

        # Display first frame
        self.seek_to_time(0)

        # Extract and display film strip
        self.extract_filmstrip_frames(num_thumbs=15)
        self.draw_filmstrip()

        # Extract and display audio waveform
        self.extract_and_display_waveform(filepath)

        # Prompt for template info
        self.prompt_template_info()

        print(f"✓ Video loaded: {self.total_frames} frames, {self.fps:.2f} FPS, {self.duration_ms}ms duration")

    def create_blank_timeline(self):
        """Create blank timeline without video"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Blank Timeline")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Duration (seconds):").pack(pady=(20, 5))

        duration_var = tk.StringVar(value="12")
        duration_entry = tk.Entry(dialog, textvariable=duration_var, width=10)
        duration_entry.pack(pady=5)

        def create():
            try:
                seconds = float(duration_var.get())
                self.duration_ms = int(seconds * 1000)
                self.timeline_slider.config(to=self.duration_ms)
                self.video_loaded = True
                self.fps_label.config(text="Blank Timeline")
                self.video_canvas.delete("placeholder")
                self.video_canvas.create_text(
                    600, 200,
                    text=f"Blank Timeline\n{seconds}s duration",
                    fill="white",
                    font=("Arial", 14),
                    tags="blank_info"
                )
                dialog.destroy()
                self.prompt_template_info()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number")

        tk.Button(dialog, text="Create", command=create, bg="#4CAF50", fg="white", padx=20).pack(pady=10)

    def prompt_template_info(self):
        """Prompt user for template ID and name"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Template Information")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Template ID:", font=("Arial", 10)).pack(pady=(20, 5))
        id_var = tk.StringVar(value="DM01")
        tk.Entry(dialog, textvariable=id_var, width=30).pack(pady=5)

        tk.Label(dialog, text="Template Name:", font=("Arial", 10)).pack(pady=(10, 5))
        name_var = tk.StringVar(value="Untitled Template")
        tk.Entry(dialog, textvariable=name_var, width=30).pack(pady=5)

        def save():
            self.template_id = id_var.get()
            self.template_name = name_var.get()
            dialog.destroy()

        tk.Button(dialog, text="OK", command=save, bg="#4CAF50", fg="white", padx=30).pack(pady=15)

    def seek_to_time(self, time_ms):
        """Seek to specific time in milliseconds"""
        if not self.video_loaded:
            return

        self.current_time_ms = max(0, min(time_ms, self.duration_ms))

        # If we have a video, seek to the frame
        if self.video_capture:
            frame_number = int((self.current_time_ms / 1000) * self.fps)
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.display_current_frame()

        self.update_timestamp_display()

    def display_current_frame(self):
        """Read and display the current frame on canvas"""
        if not self.video_capture:
            return

        ret, frame = self.video_capture.read()

        if not ret:
            return

        # Convert BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get canvas size
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()

        # Skip if canvas not ready
        if canvas_width <= 1 or canvas_height <= 1:
            return

        # Resize frame to fit canvas while maintaining aspect ratio
        frame_height, frame_width = frame_rgb.shape[:2]
        scale = min(canvas_width / frame_width, canvas_height / frame_height)
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)

        frame_resized = cv2.resize(frame_rgb, (new_width, new_height))

        # Convert to PIL Image then to PhotoImage
        image = Image.fromarray(frame_resized)
        self.photo_image = ImageTk.PhotoImage(image)

        # Display on canvas
        self.video_canvas.delete("all")
        self.video_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo_image,
            anchor=tk.CENTER
        )

    def toggle_playback(self):
        """Toggle play/pause"""
        if not self.video_loaded:
            messagebox.showwarning("No Video", "Please load a video or create a blank timeline first")
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_button.config(text="⏸ Pause")
        else:
            self.play_button.config(text="▶ Play")

    def step_time(self, delta_ms):
        """Step forward/backward by delta_ms milliseconds"""
        if not self.video_loaded:
            return

        new_time = self.current_time_ms + delta_ms
        self.seek_to_time(new_time)
        self.timeline_slider.set(self.current_time_ms)

    def step_frame(self, delta_frames):
        """Step forward/backward by exact number of frames"""
        if not self.video_loaded or not self.video_capture:
            return

        # Calculate time per frame in milliseconds
        frame_duration_ms = 1000 / self.fps if self.fps > 0 else 33

        # Step by the specified number of frames
        delta_ms = int(delta_frames * frame_duration_ms)
        new_time = self.current_time_ms + delta_ms
        self.seek_to_time(new_time)
        self.timeline_slider.set(self.current_time_ms)

    def on_timeline_change(self, value):
        """Handle timeline slider change"""
        if not self.video_loaded:
            return

        new_time_ms = int(float(value))
        self.seek_to_time(new_time_ms)

    def update_timeline(self):
        """Update timeline position and display (called repeatedly)"""
        if self.video_loaded and self.is_playing:
            # Advance time based on FPS
            frame_duration_ms = 1000 / self.fps if self.fps > 0 else 33  # Default ~30fps
            self.current_time_ms += int(frame_duration_ms)

            if self.current_time_ms >= self.duration_ms:
                self.current_time_ms = self.duration_ms
                self.is_playing = False
                self.play_button.config(text="▶ Play")

            # Update slider and display
            self.timeline_slider.set(self.current_time_ms)

            if self.video_capture:
                self.display_current_frame()

        # Update timestamp
        self.update_timestamp_display()

        # Update film strip position indicator
        self.update_filmstrip_position()

        # Update waveform position indicator
        self.update_waveform_position()

        # Schedule next update (30 FPS refresh rate)
        self.root.after(33, self.update_timeline)

    def update_timestamp_display(self):
        """Update timestamp label"""
        ms = self.current_time_ms
        seconds = ms // 1000
        milliseconds = ms % 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60

        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        self.timestamp_label.config(text=timestamp)

    # ========================================================================
    # FILM STRIP METHODS
    # ========================================================================

    def extract_filmstrip_frames(self, num_thumbs=15):
        """Extract thumbnail frames at regular intervals for film strip"""
        if not self.video_capture or self.duration_ms == 0:
            return

        print(f"⏳ Extracting {num_thumbs} thumbnail frames for film strip...")

        # Clear previous frames
        self.filmstrip_frames = []
        self.filmstrip_frame_times = []

        # Calculate time intervals
        interval_ms = self.duration_ms / (num_thumbs - 1) if num_thumbs > 1 else 0

        for i in range(num_thumbs):
            time_ms = int(i * interval_ms)
            if time_ms > self.duration_ms:
                time_ms = self.duration_ms

            # Seek to this time
            frame_number = int((time_ms / 1000) * self.fps)
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            # Read frame
            ret, frame = self.video_capture.read()
            if not ret:
                continue

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize to thumbnail size
            frame_resized = cv2.resize(
                frame_rgb,
                (self.filmstrip_thumb_width, self.filmstrip_thumb_height),
                interpolation=cv2.INTER_AREA
            )

            # Convert to PIL Image then PhotoImage
            pil_image = Image.fromarray(frame_resized)
            photo_image = ImageTk.PhotoImage(pil_image)

            # Store frame and time
            self.filmstrip_frames.append(photo_image)
            self.filmstrip_frame_times.append(time_ms)

        # Reset video to beginning
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

        print(f"✓ Extracted {len(self.filmstrip_frames)} thumbnail frames")

    def draw_filmstrip(self):
        """Draw film strip thumbnails on canvas"""
        if not self.filmstrip_frames or self.duration_ms == 0:
            return

        # Clear canvas
        self.filmstrip_canvas.delete("all")

        # Get canvas width
        canvas_width = self.filmstrip_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200  # Default width

        # Draw each thumbnail positioned by its actual time
        for photo, time_ms in zip(self.filmstrip_frames, self.filmstrip_frame_times):
            # Calculate x position based on time (proportional to duration)
            x_pos = int((time_ms / self.duration_ms) * canvas_width)
            y_pos = self.filmstrip_canvas_height // 2

            # Draw thumbnail
            self.filmstrip_canvas.create_image(
                x_pos, y_pos,
                image=photo,
                anchor=tk.CENTER,
                tags="thumbnail"
            )

            # Draw frame border
            half_width = self.filmstrip_thumb_width // 2
            half_height = self.filmstrip_thumb_height // 2
            self.filmstrip_canvas.create_rectangle(
                x_pos - half_width, y_pos - half_height,
                x_pos + half_width, y_pos + half_height,
                outline="#444",
                width=1,
                tags="thumbnail_border"
            )

    def update_filmstrip_position(self):
        """Update position indicator on film strip"""
        if not self.filmstrip_frames or self.duration_ms == 0:
            return

        # Remove old position indicator
        self.filmstrip_canvas.delete("position")

        # Calculate position
        canvas_width = self.filmstrip_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200

        x_pos = int((self.current_time_ms / self.duration_ms) * canvas_width)

        # Draw position indicator
        self.filmstrip_canvas.create_line(
            x_pos, 0,
            x_pos, self.filmstrip_canvas_height,
            fill="#FF6B00",
            width=2,
            tags="position"
        )

    def on_filmstrip_click(self, event):
        """Handle click on film strip for scrubbing"""
        if not self.video_loaded or self.duration_ms == 0:
            return

        # Check if we clicked on a marker
        items = self.filmstrip_canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        clicked_on_marker = False
        for item in items:
            tags = self.filmstrip_canvas.gettags(item)
            if "marker" in tags:
                clicked_on_marker = True
                break

        # If didn't click on a marker, deselect and scrub timeline
        if not clicked_on_marker:
            self.deselect_marker()

            # Get canvas width
            canvas_width = self.filmstrip_canvas.winfo_width()
            if canvas_width <= 1:
                return

            # Calculate time from click position
            x_pos = event.x
            time_ms = int((x_pos / canvas_width) * self.duration_ms)

            # Seek to this time
            self.seek_to_time(time_ms)
            self.timeline_slider.set(self.current_time_ms)

    def on_filmstrip_resize(self, event):
        """Handle filmstrip canvas resize - redraw filmstrip"""
        if self.filmstrip_frames:
            self.draw_filmstrip()
        self.redraw_marker_indicators()

    # ========================================================================
    # WAVEFORM METHODS
    # ========================================================================

    def extract_and_display_waveform(self, video_filepath):
        """Extract audio from video and display waveform"""
        try:
            print("⏳ Extracting audio for waveform...")

            # Load video with moviepy
            video = VideoFileClip(video_filepath)

            if video.audio is None:
                print("⚠ No audio track found in video")
                self.waveform_canvas.delete("waveform_placeholder")
                self.waveform_canvas.create_text(
                    600, 40,
                    text="No audio track in video",
                    fill="#888",
                    font=("Arial", 10)
                )
                video.close()
                return

            # Get audio as numpy array
            audio_array = video.audio.to_soundarray(fps=22050)  # Downsample for performance
            video.close()

            # If stereo, convert to mono by averaging channels
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)

            # Calculate waveform data (downsample for display)
            self.calculate_waveform_data(audio_array)

            # Draw waveform
            self.draw_waveform()

            print("✓ Waveform extracted and displayed")

        except Exception as e:
            print(f"⚠ Could not extract waveform: {e}")
            self.waveform_canvas.delete("waveform_placeholder")
            self.waveform_canvas.create_text(
                600, 40,
                text="Could not extract audio waveform",
                fill="#888",
                font=("Arial", 10)
            )

    def calculate_waveform_data(self, audio_array, target_width=1200):
        """Calculate downsampled waveform data for display"""
        # Ensure we have enough samples to fill the target width
        total_samples = len(audio_array)

        # Calculate samples per pixel
        samples_per_pixel = max(1, total_samples // target_width)

        # Calculate RMS (root mean square) for each pixel
        waveform = []
        for i in range(target_width):
            start_idx = i * samples_per_pixel
            end_idx = min(start_idx + samples_per_pixel, total_samples)

            if start_idx < total_samples:
                chunk = audio_array[start_idx:end_idx]
                if len(chunk) > 0:
                    rms = np.sqrt(np.mean(chunk**2))
                    waveform.append(rms)
                else:
                    waveform.append(0)
            else:
                # Pad with silence if audio is shorter than target
                waveform.append(0)

        # Normalize to 0-1 range
        max_val = max(waveform) if waveform else 1
        if max_val > 0:
            waveform = [w / max_val for w in waveform]

        self.waveform_data = waveform

    def draw_waveform(self):
        """Draw waveform on canvas"""
        if not self.waveform_data:
            return

        # Clear canvas
        self.waveform_canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self.waveform_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200  # Default width

        canvas_height = self.waveform_canvas_height
        mid_y = canvas_height // 2

        # Draw waveform - ensure it fills the full canvas width
        num_samples = len(self.waveform_data)

        # Draw each sample, stretching to fill full canvas width
        for i, amplitude in enumerate(self.waveform_data):
            # Calculate x positions to fill entire canvas width
            x_start = int((i / num_samples) * canvas_width)
            x_end = int(((i + 1) / num_samples) * canvas_width)

            # Use the midpoint or draw a rectangle for better coverage
            x = (x_start + x_end) // 2

            # Scale amplitude to fit canvas height
            height = int(amplitude * (canvas_height / 2) * 0.9)

            # Draw vertical line for this sample (use width=2 for better visibility)
            self.waveform_canvas.create_line(
                x, mid_y - height,
                x, mid_y + height,
                fill="#00D4FF",
                width=2,
                tags="waveform"
            )

        # Draw center line
        self.waveform_canvas.create_line(
            0, mid_y,
            canvas_width, mid_y,
            fill="#444",
            width=1,
            tags="centerline"
        )

    def update_waveform_position(self):
        """Update position indicator on waveform"""
        if not self.waveform_data or self.duration_ms == 0:
            return

        # Remove old position indicator
        self.waveform_canvas.delete("position")

        # Calculate position
        canvas_width = self.waveform_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200

        x_pos = int((self.current_time_ms / self.duration_ms) * canvas_width)

        # Draw position indicator
        self.waveform_canvas.create_line(
            x_pos, 0,
            x_pos, self.waveform_canvas_height,
            fill="#FF6B00",
            width=2,
            tags="position"
        )

    def on_waveform_click(self, event):
        """Handle click on waveform for scrubbing"""
        if not self.video_loaded or self.duration_ms == 0:
            return

        # Check if we clicked on a marker (markers have tags)
        items = self.waveform_canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        clicked_on_marker = False
        for item in items:
            tags = self.waveform_canvas.gettags(item)
            if "marker" in tags:
                clicked_on_marker = True
                break

        # If didn't click on a marker, deselect and scrub timeline
        if not clicked_on_marker:
            self.deselect_marker()

            # Get canvas width
            canvas_width = self.waveform_canvas.winfo_width()
            if canvas_width <= 1:
                return

            # Calculate time from click position
            x_pos = event.x
            time_ms = int((x_pos / canvas_width) * self.duration_ms)

            # Seek to this time
            self.seek_to_time(time_ms)
            self.timeline_slider.set(self.current_time_ms)

    def on_waveform_resize(self, event):
        """Handle waveform canvas resize - redraw waveform"""
        if self.waveform_data:
            self.draw_waveform()
        self.redraw_marker_indicators()

    # ========================================================================
    # MARKER MANAGEMENT METHODS
    # ========================================================================

    def add_marker_by_type(self, marker_type):
        """Add marker of specific type at current position and open editor"""
        if not self.video_loaded:
            messagebox.showwarning("No Timeline", "Please load a video or create a blank timeline first")
            return

        from datetime import datetime

        # Generate asset slot and filename
        type_prefix_map = {
            "music": "MUS",
            "sfx": "SFX",
            "voice": "VOX",
            "music_control": "CTRL"
        }

        prefix = type_prefix_map.get(marker_type, "ASSET")
        marker_count = len([m for m in self.markers if m["type"] == marker_type])
        asset_slot = f"{marker_type}_{marker_count}"
        asset_file = f"{prefix}_{marker_count:05d}_v1.mp3"  # Include version suffix

        # Create empty but valid prompt_data structure
        prompt_data = self.create_default_prompt_data(marker_type)

        # Create initial version object
        version_obj = {
            "version": 1,
            "asset_file": asset_file,
            "asset_id": None,
            "created_at": datetime.now().isoformat(),
            "status": "not yet generated",
            "prompt_data_snapshot": prompt_data.copy()
        }

        marker = {
            "time_ms": self.current_time_ms,
            "type": marker_type,
            "name": "",  # Custom marker name (to be filled in editor)
            "prompt_data": prompt_data,
            "asset_slot": asset_slot,
            "asset_file": asset_file,
            "asset_id": None,
            "status": "not yet generated",
            "current_version": 1,
            "versions": [version_obj]
        }

        # Execute via command pattern for undo/redo support
        command = AddMarkerCommand(self, marker)
        self.history.execute_command(command)

        # Get the index of the newly added marker (last one in the list)
        marker_index = len(self.markers) - 1

        # Define cancel callback that undoes the add if user cancels
        def on_cancel():
            self.history.undo()

        # Immediately open editor for the new marker
        self.open_marker_editor(self.markers[marker_index], marker_index, on_cancel_callback=on_cancel)

        print(f"✓ Added {marker_type} marker at {self.current_time_ms}ms")

    def add_marker(self):
        """Legacy add_marker for backward compatibility - defaults to SFX"""
        # This is called by keyboard shortcut 'M'
        # Default to SFX type
        self.add_marker_by_type("sfx")

    def update_marker_list(self):
        """Refresh marker list with custom row widgets"""
        # Clear existing row widgets
        for row_widget in self.marker_row_widgets:
            row_widget.frame.destroy()
        self.marker_row_widgets.clear()

        # Create new row widgets for each marker
        for index, marker in enumerate(self.markers):
            row = MarkerRow(self.marker_rows_frame, marker, index, self)
            self.marker_row_widgets.append(row)

        # Update scroll region
        self.marker_rows_frame.update_idletasks()
        self.marker_canvas.configure(scrollregion=self.marker_canvas.bbox("all"))

    def select_marker_row(self, marker_index):
        """
        Select a marker row and update visual state

        Args:
            marker_index: Index of marker to select
        """
        # Deselect previous selection
        if self.selected_marker_index is not None and self.selected_marker_index < len(self.marker_row_widgets):
            self.marker_row_widgets[self.selected_marker_index].set_selected(False)

        # Select new row
        if 0 <= marker_index < len(self.marker_row_widgets):
            self.selected_marker_index = marker_index
            self.marker_row_widgets[marker_index].set_selected(True)

            # Scroll to make selected row visible
            row_widget = self.marker_row_widgets[marker_index]
            self.marker_canvas.yview_moveto(marker_index / len(self.marker_row_widgets))

            # Also highlight corresponding timeline marker
            self.redraw_marker_indicators()

    def play_marker_audio(self, marker_index):
        """
        Play or stop audio for a marker

        Args:
            marker_index: Index of marker to play/stop
        """
        if not (0 <= marker_index < len(self.markers)):
            return

        marker = self.markers[marker_index]

        # Check if this marker is already playing - if so, stop it
        if self.audio_player.is_playing_marker(marker_index):
            self.audio_player.stop_audio()
            self.update_marker_row_play_button(marker_index, is_playing=False)
            return

        # Get current version's asset file
        current_version_data = self.get_current_version_data(marker)
        if current_version_data:
            asset_file = current_version_data.get("asset_file")
        else:
            asset_file = marker.get("asset_file")

        if not asset_file:
            messagebox.showerror(
                "No Audio File",
                f"Marker has no asset file assigned.\n\nMarker: {marker.get('name', '(unnamed)')}"
            )
            return

        # Build full path to audio file
        # Check multiple possible locations
        possible_paths = [
            os.path.join("generated_audio", marker["type"], asset_file),
            os.path.join("generated_audio", asset_file),
            asset_file  # Direct path
        ]

        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break

        if not file_path:
            messagebox.showerror(
                "Audio File Not Found",
                f"Could not find audio file:\n{asset_file}\n\n"
                f"Searched in:\n" + "\n".join(f"  • {p}" for p in possible_paths) + "\n\n"
                f"Generate the audio first using the 🔄 button."
            )
            return

        # Play the audio
        success = self.audio_player.play_audio_file(file_path, marker_index)

        if success:
            # Update button to show pause icon
            self.update_marker_row_play_button(marker_index, is_playing=True)
            # Start checking when playback finishes
            self.root.after(100, lambda: self.check_playback_finished(marker_index))
        else:
            messagebox.showerror(
                "Playback Error",
                f"Failed to play audio file:\n{file_path}\n\n"
                f"The file may be corrupted or in an unsupported format."
            )

    def update_marker_row_play_button(self, marker_index, is_playing):
        """
        Update play button icon for a marker row

        Args:
            marker_index: Index of marker
            is_playing: True to show pause icon, False to show play icon
        """
        if 0 <= marker_index < len(self.marker_row_widgets):
            row_widget = self.marker_row_widgets[marker_index]
            if is_playing:
                row_widget.play_btn.config(text="⏸", bg=COLORS.warning_bg)  # Pause - warning color
            else:
                row_widget.play_btn.config(text="▶", bg=COLORS.info_bg)  # Play - info color

    def check_playback_finished(self, marker_index):
        """
        Check if audio playback has finished and update UI

        Args:
            marker_index: Index of marker being played
        """
        is_playing, playing_index = self.audio_player.get_playing_status()

        if not is_playing or playing_index != marker_index:
            # Playback finished or stopped
            self.update_marker_row_play_button(marker_index, is_playing=False)
        else:
            # Still playing - check again in 100ms
            self.root.after(100, lambda: self.check_playback_finished(marker_index))

    def generate_marker_audio(self, marker_index):
        """
        Generate audio for a marker using ElevenLabs API

        Args:
            marker_index: Index of marker to generate
        """
        if not (0 <= marker_index < len(self.markers)):
            return

        # Check if API functions are available
        if generate_sfx is None or generate_voice is None or generate_music is None:
            messagebox.showerror(
                "API Not Available",
                "ElevenLabs API module not found.\n\n"
                "Make sure elevenlabs_api.py exists and dependencies are installed."
            )
            return

        marker = self.markers[marker_index]
        marker_type = marker['type']
        prompt_data = marker.get('prompt_data', {})

        # Store old state for undo
        old_marker_state = marker.copy()

        # Set status to generating
        current_version_data = self.get_current_version_data(marker)
        if current_version_data:
            current_version_data['status'] = 'generating'

        # Update UI to show generating status (⏳)
        self.update_marker_list()

        # Start generation in background thread
        thread = threading.Thread(
            target=self._generate_audio_background,
            args=(marker_index, marker_type, prompt_data, old_marker_state),
            daemon=True
        )
        thread.start()

    def _generate_audio_background(self, marker_index, marker_type, prompt_data, old_marker_state):
        """
        Background thread for audio generation (doesn't block UI)

        Args:
            marker_index: Index of marker
            marker_type: Type of marker (sfx/voice/music)
            prompt_data: Prompt data for generation
            old_marker_state: Marker state before generation (for undo)
        """
        try:
            marker = self.markers[marker_index]

            # Determine next version number
            next_version = self.add_new_version(marker, prompt_data)

            # Build output path
            marker_name = marker.get('name', f'{marker_type.upper()}_{marker_index:05d}')
            output_filename = f"{marker_name}_v{next_version}.mp3"
            output_path = os.path.join("generated_audio", marker_type, output_filename)

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Call appropriate API function
            result = None
            if marker_type == 'sfx':
                description = prompt_data.get('description', '')
                if not description:
                    raise ValueError("SFX description is required")
                result = generate_sfx(description=description, output_path=output_path)

            elif marker_type == 'voice':
                voice_profile = prompt_data.get('voice_profile', '')
                text = prompt_data.get('text', '')
                if not text:
                    raise ValueError("Voice text is required")
                result = generate_voice(voice_profile=voice_profile, text=text, output_path=output_path)

            elif marker_type == 'music':
                positive_styles = prompt_data.get('positiveGlobalStyles', [])
                negative_styles = prompt_data.get('negativeGlobalStyles', [])
                sections = prompt_data.get('sections', [])
                if not positive_styles:
                    raise ValueError("Music requires at least one positive style")
                result = generate_music(
                    positive_styles=positive_styles,
                    negative_styles=negative_styles,
                    sections=sections,
                    output_path=output_path
                )

            # Check if generation succeeded
            if result and result.get('success'):
                # Update version data with success
                current_version_data = self.get_current_version_data(marker)
                if current_version_data:
                    current_version_data['status'] = 'generated'
                    current_version_data['asset_file'] = output_filename
                    current_version_data['asset_id'] = result.get('asset_id', f'{marker_type}_{next_version}')

                # Schedule UI update on main thread
                self.root.after(0, lambda: self._on_generation_success(marker_index, old_marker_state))
            else:
                # Generation failed
                error_msg = result.get('error', 'Unknown error') if result else 'No response from API'
                self.root.after(0, lambda: self._on_generation_failed(marker_index, error_msg))

        except Exception as e:
            # Handle any errors
            error_msg = str(e)
            self.root.after(0, lambda: self._on_generation_failed(marker_index, error_msg))

    def _on_generation_success(self, marker_index, old_marker_state):
        """
        Called on main thread after successful generation

        Args:
            marker_index: Index of marker
            old_marker_state: State before generation (for undo)
        """
        # Create undo command
        command = GenerateAudioCommand(self, marker_index, old_marker_state)
        command.new_marker_state = self.markers[marker_index].copy()
        self.history.execute_command(command)

        # Update UI
        self.update_marker_list()

        # Show success message
        marker = self.markers[marker_index]
        marker_name = marker.get('name', '(unnamed)')
        messagebox.showinfo(
            "Generation Complete",
            f"Audio generated successfully!\n\n"
            f"Marker: {marker_name}\n"
            f"Version: {marker.get('current_version', 1)}"
        )

        # Trigger auto-assembly if enabled
        self.auto_assemble_audio()

    def _on_generation_failed(self, marker_index, error_msg):
        """
        Called on main thread after generation failure

        Args:
            marker_index: Index of marker
            error_msg: Error message
        """
        # Update status to failed
        marker = self.markers[marker_index]
        current_version_data = self.get_current_version_data(marker)
        if current_version_data:
            current_version_data['status'] = 'failed'

        # Update UI
        self.update_marker_list()

        # Show error message
        marker_name = marker.get('name', '(unnamed)')
        messagebox.showerror(
            "Generation Failed",
            f"Failed to generate audio for marker:\n{marker_name}\n\n"
            f"Error: {error_msg}"
        )

    # ========================================================================
    # BATCH GENERATION OPERATIONS
    # ========================================================================

    def batch_generate_missing(self):
        """Generate all markers that haven't been generated yet (status: not_yet_generated)"""
        # Collect markers to generate
        markers_to_generate = []
        for i, marker in enumerate(self.markers):
            current_version_data = self.get_current_version_data(marker)
            if current_version_data:
                status = current_version_data.get('status', 'not_yet_generated')
                if status == 'not_yet_generated':
                    markers_to_generate.append((i, marker))

        if not markers_to_generate:
            messagebox.showinfo(
                "No Markers to Generate",
                "All markers have already been generated.\n\n"
                "Use 'Regenerate All' to create new versions."
            )
            return

        # Confirm operation
        if not messagebox.askyesno(
            "Batch Generate Missing",
            f"Generate audio for {len(markers_to_generate)} marker(s)?\n\n"
            f"This will call the ElevenLabs API {len(markers_to_generate)} time(s)."
        ):
            return

        # Start batch operation
        self._run_batch_generation(
            markers_to_generate,
            "Generate All Missing"
        )

    def batch_regenerate_all(self):
        """Regenerate all markers (creates new versions)"""
        if not self.markers:
            messagebox.showinfo("No Markers", "Add some markers first.")
            return

        # Collect all markers
        markers_to_generate = [(i, marker) for i, marker in enumerate(self.markers)]

        # Confirm operation
        if not messagebox.askyesno(
            "Batch Regenerate All",
            f"Regenerate audio for all {len(markers_to_generate)} marker(s)?\n\n"
            f"This will:\n"
            f"  • Create new versions for each marker\n"
            f"  • Call the ElevenLabs API {len(markers_to_generate)} time(s)\n"
            f"  • Preserve existing versions in history"
        ):
            return

        # Start batch operation
        self._run_batch_generation(
            markers_to_generate,
            "Regenerate All"
        )

    def batch_generate_by_type(self):
        """Generate all markers of a specific type (SFX, Voice, or Music)"""
        if not self.markers:
            messagebox.showinfo("No Markers", "Add some markers first.")
            return

        # Show type selection dialog
        type_dialog = tk.Toplevel(self.root)
        type_dialog.title("Select Marker Type")
        type_dialog.geometry("300x200")
        type_dialog.resizable(False, False)
        type_dialog.transient(self.root)
        type_dialog.grab_set()

        # Center dialog
        type_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (200 // 2)
        type_dialog.geometry(f"+{x}+{y}")

        # Title
        tk.Label(
            type_dialog,
            text="Select marker type to generate:",
            font=("Arial", 11, "bold")
        ).pack(pady=20)

        selected_type = tk.StringVar()

        # Type buttons
        button_frame = tk.Frame(type_dialog)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="SFX",
            command=lambda: [selected_type.set("sfx"), type_dialog.destroy()],
            bg="#F44336",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).pack(pady=5)

        tk.Button(
            button_frame,
            text="Voice",
            command=lambda: [selected_type.set("voice"), type_dialog.destroy()],
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).pack(pady=5)

        tk.Button(
            button_frame,
            text="Music",
            command=lambda: [selected_type.set("music"), type_dialog.destroy()],
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).pack(pady=5)

        # Wait for selection
        type_dialog.wait_window()

        if not selected_type.get():
            return  # User closed dialog

        # Collect markers of selected type
        marker_type = selected_type.get()
        markers_to_generate = [
            (i, marker) for i, marker in enumerate(self.markers)
            if marker['type'] == marker_type
        ]

        if not markers_to_generate:
            messagebox.showinfo(
                "No Markers Found",
                f"No {marker_type.upper()} markers found in timeline."
            )
            return

        # Confirm operation
        if not messagebox.askyesno(
            f"Generate All {marker_type.upper()}",
            f"Generate audio for {len(markers_to_generate)} {marker_type.upper()} marker(s)?\n\n"
            f"This will call the ElevenLabs API {len(markers_to_generate)} time(s)."
        ):
            return

        # Start batch operation
        self._run_batch_generation(
            markers_to_generate,
            f"Generate All {marker_type.upper()}"
        )

    def _run_batch_generation(self, markers_list, operation_name):
        """
        Run batch generation for a list of markers

        Args:
            markers_list: List of (index, marker) tuples to generate
            operation_name: Display name for the operation
        """
        # Create progress window
        progress = BatchProgressWindow(self, operation_name, len(markers_list))

        # Process markers one at a time (queue-based)
        def process_next_marker(current_idx=0):
            # Check if cancelled
            if progress.cancelled:
                progress.show_summary()
                return

            # Check if done
            if current_idx >= len(markers_list):
                progress.close()
                progress.show_summary()

                # Trigger auto-assembly if enabled
                self.auto_assemble_audio()
                return

            # Get next marker
            marker_index, marker = markers_list[current_idx]
            marker_name = marker.get('name', '(unnamed)')
            marker_type = marker['type']

            # Update progress display
            progress.update_progress(current_idx, marker_name, marker_type)

            # Generate audio (synchronously in this context)
            def on_generation_complete(success):
                if success:
                    progress.mark_success()
                else:
                    progress.mark_failed()

                # Process next marker after a short delay
                self.root.after(500, lambda: process_next_marker(current_idx + 1))

            # Start generation for this marker
            self._generate_marker_for_batch(marker_index, on_generation_complete)

        # Start processing first marker
        process_next_marker(0)

    def _generate_marker_for_batch(self, marker_index, completion_callback):
        """
        Generate audio for a single marker in batch mode

        Args:
            marker_index: Index of marker to generate
            completion_callback: Function to call with success/failure (bool)
        """
        if not (0 <= marker_index < len(self.markers)):
            completion_callback(False)
            return

        # Check if API functions are available
        if generate_sfx is None or generate_voice is None or generate_music is None:
            completion_callback(False)
            return

        marker = self.markers[marker_index]
        marker_type = marker['type']
        prompt_data = marker.get('prompt_data', {})
        old_marker_state = marker.copy()

        # Set status to generating
        current_version_data = self.get_current_version_data(marker)
        if current_version_data:
            current_version_data['status'] = 'generating'

        # Update UI to show generating status (⏳)
        self.update_marker_list()

        # Start generation in background thread
        def on_success(marker_idx, asset_file, asset_id, size_bytes):
            self._on_generation_success(marker_idx, asset_file, asset_id, size_bytes)
            completion_callback(True)

        def on_failed(marker_idx, error_msg):
            # Update status but don't show messagebox (batch mode)
            marker = self.markers[marker_idx]
            current_version_data = self.get_current_version_data(marker)
            if current_version_data:
                current_version_data['status'] = 'failed'
            self.update_marker_list()
            completion_callback(False)

        thread = threading.Thread(
            target=self._generate_audio_background_for_batch,
            args=(marker_index, marker_type, prompt_data, old_marker_state, on_success, on_failed),
            daemon=True
        )
        thread.start()

    def _generate_audio_background_for_batch(self, marker_index, marker_type, prompt_data, old_marker_state, success_callback, failure_callback):
        """
        Background thread function for batch generation
        (Modified version that uses callbacks instead of root.after)
        """
        try:
            # Prepare output directory
            output_dir = os.path.join("generated_audio", marker_type)
            os.makedirs(output_dir, exist_ok=True)

            # Generate unique filename
            marker = self.markers[marker_index]
            current_version = marker.get('current_version', 1)
            marker_name = marker.get('name', '(unnamed)')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{marker_type.upper()}_{marker_index:05d}_v{current_version}_{timestamp}.mp3"
            output_path = os.path.join(output_dir, base_filename)

            # Call appropriate API based on type
            result = None
            if marker_type == 'sfx':
                description = prompt_data.get('description', '')
                result = generate_sfx(description, output_path)

            elif marker_type == 'voice':
                voice_profile = prompt_data.get('voice_profile', '')
                text = prompt_data.get('text', '')
                result = generate_voice(voice_profile, text, output_path)

            elif marker_type == 'music':
                positive_styles = prompt_data.get('positiveGlobalStyles', [])
                negative_styles = prompt_data.get('negativeGlobalStyles', [])
                sections = prompt_data.get('sections', [])
                result = generate_music(positive_styles, negative_styles, sections, output_path)

            # Check result
            if result and result.get('success'):
                asset_file = base_filename
                asset_id = result.get('asset_id')
                size_bytes = result.get('size_bytes', 0)

                # Call success callback
                success_callback(marker_index, asset_file, asset_id, size_bytes)

            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                failure_callback(marker_index, error_msg)

        except Exception as e:
            error_msg = str(e)
            failure_callback(marker_index, error_msg)

    # NOTE: Old listbox handlers - no longer used with custom MarkerRow widgets
    # Selection and double-click are now handled by MarkerRow class

    def open_marker_editor(self, marker, index, on_cancel_callback=None):
        """Open the prompt editor window for a marker"""
        # Create and show editor window
        editor = PromptEditorWindow(
            parent=self.root,
            marker=marker,
            marker_index=index,
            on_save_callback=self.on_marker_edited,
            on_cancel_callback=on_cancel_callback,
            gui_ref=self  # Pass reference to main GUI
        )

    def on_marker_edited(self, updated_marker, index):
        """Callback when marker is edited and saved"""
        # Get old marker state before editing
        old_marker = self.markers[index].copy()

        # Create and execute EditMarkerCommand for undo/redo support
        command = EditMarkerCommand(self, index, old_marker, updated_marker)
        self.history.execute_command(command)

        print(f"✓ Updated marker at index {index}: {updated_marker['type']}")

    def jump_to_marker(self):
        """Jump timeline to selected marker"""
        if self.selected_marker_index is None:
            return

        index = self.selected_marker_index
        marker = self.markers[index]

        self.seek_to_time(marker["time_ms"])
        self.timeline_slider.set(self.current_time_ms)
        self.redraw_marker_indicators()  # Redraw to show selection highlight

    def delete_marker(self):
        """Delete selected marker using command pattern"""
        if self.selected_marker_index is None:
            return

        index = self.selected_marker_index
        marker = self.markers[index]

        # Execute via command pattern for undo/redo support
        command = DeleteMarkerCommand(self, marker, index)
        self.history.execute_command(command)

    def clear_all_markers(self):
        """Clear all markers with confirmation"""
        if not self.markers:
            return

        if messagebox.askyesno("Clear All Markers", f"Delete all {len(self.markers)} markers?"):
            self.markers.clear()
            self.update_marker_list()
            self.redraw_marker_indicators()

    # ========================================================================
    # MARKER DRAG-TO-REPOSITION
    # ========================================================================

    def start_drag_marker(self, event, marker_index):
        """Start dragging a marker"""
        if marker_index >= len(self.markers):
            return

        # Select this marker using custom row selection
        self.select_marker_row(marker_index)

        self.dragging_marker = self.markers[marker_index]
        self.drag_marker_index = marker_index
        self.drag_start_x = event.x

        # Store original time for undo/redo
        self._drag_original_time = self.dragging_marker["time_ms"]

        print(f"⊙ Dragging marker {marker_index}")

    def drag_marker(self, event):
        """Update marker position during drag"""
        if self.dragging_marker is None:
            return

        # Calculate new time based on drag position
        canvas_width = self.waveform_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200

        # Calculate time from x position
        new_time_ms = int((event.x / canvas_width) * self.duration_ms)
        new_time_ms = max(0, min(new_time_ms, self.duration_ms))  # Clamp to valid range

        # Update marker temporarily (visual feedback only)
        self.dragging_marker["time_ms"] = new_time_ms

        # Redraw markers
        self.redraw_marker_indicators()

    def end_drag_marker(self, event):
        """Finish dragging and commit the change"""
        if self.dragging_marker is None:
            return

        # Calculate final time
        canvas_width = self.waveform_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200

        new_time_ms = int((event.x / canvas_width) * self.duration_ms)
        new_time_ms = max(0, min(new_time_ms, self.duration_ms))

        # Get the original time (before we started dragging)
        # We need to find the marker's original position from history
        # For simplicity, we'll track this in start_drag_marker
        old_time_ms = getattr(self, '_drag_original_time', self.dragging_marker["time_ms"])

        # Only create command if time actually changed
        if new_time_ms != old_time_ms:
            # Revert to old time first
            self.dragging_marker["time_ms"] = old_time_ms

            # Create and execute move command
            command = MoveMarkerCommand(self, self.dragging_marker, old_time_ms, new_time_ms)
            self.history.execute_command(command)

            print(f"✓ Moved marker from {old_time_ms}ms to {new_time_ms}ms")
        else:
            # No change, just redraw to clean up
            self.redraw_marker_indicators()

        # Clear drag state
        self.dragging_marker = None
        self.drag_marker_index = None
        self.drag_start_x = None

    def nudge_selected_marker(self, delta_ms):
        """Nudge selected marker by delta_ms milliseconds"""
        if self.selected_marker_index is None or self.selected_marker_index >= len(self.markers):
            print("No marker selected for nudging")
            return

        marker = self.markers[self.selected_marker_index]
        old_time_ms = marker["time_ms"]
        new_time_ms = max(0, min(old_time_ms + delta_ms, self.duration_ms))

        if new_time_ms != old_time_ms:
            # Create and execute move command
            command = MoveMarkerCommand(self, marker, old_time_ms, new_time_ms)
            self.history.execute_command(command)
            print(f"→ Nudged marker {delta_ms:+d}ms: {old_time_ms}ms → {new_time_ms}ms")

    def nudge_selected_marker_by_frame(self, delta_frames):
        """Nudge selected marker by exact number of frames"""
        if not self.video_loaded or not self.video_capture:
            print("Frame nudging only works with video loaded")
            return

        # Calculate time per frame
        frame_duration_ms = 1000 / self.fps if self.fps > 0 else 33
        delta_ms = int(delta_frames * frame_duration_ms)

        self.nudge_selected_marker(delta_ms)

    def undo(self):
        """Undo the last action"""
        if self.history.undo():
            print("↶ Undo")
        else:
            print("Nothing to undo")

    def redo(self):
        """Redo the last undone action"""
        if self.history.redo():
            print("↷ Redo")
        else:
            print("Nothing to redo")

    def redraw_marker_indicators(self):
        """Redraw marker indicators on waveform and filmstrip canvases"""
        # Remove old markers
        self.waveform_canvas.delete("marker")
        self.filmstrip_canvas.delete("marker")

        if not self.video_loaded or self.duration_ms == 0:
            return

        # Get canvas widths
        waveform_width = self.waveform_canvas.winfo_width()
        filmstrip_width = self.filmstrip_canvas.winfo_width()

        if waveform_width <= 1:
            waveform_width = 1200
        if filmstrip_width <= 1:
            filmstrip_width = 1200

        # Marker colors by type
        marker_colors = {
            "music": "#2196F3",      # Blue
            "sfx": "#F44336",        # Red
            "voice": "#4CAF50",      # Green
            "music_control": "#9C27B0"  # Purple
        }

        # Draw each marker
        for i, marker in enumerate(self.markers):
            time_ms = marker["time_ms"]
            marker_type = marker.get("type", "music")
            color = marker_colors.get(marker_type, "#FFF")

            # Check if this marker is selected
            is_selected = (i == self.selected_marker_index)

            # Calculate x position
            waveform_x = int((time_ms / self.duration_ms) * waveform_width)
            filmstrip_x = int((time_ms / self.duration_ms) * filmstrip_width)

            # Draw on waveform (thicker if selected)
            line_width = 5 if is_selected else 3
            self.waveform_canvas.create_line(
                waveform_x, 0,
                waveform_x, self.waveform_canvas_height,
                fill=color,
                width=line_width,
                tags=("marker", f"marker_{i}")
            )

            # Draw selection glow if selected
            if is_selected:
                self.waveform_canvas.create_line(
                    waveform_x, 0,
                    waveform_x, self.waveform_canvas_height,
                    fill="white",
                    width=9,
                    tags=("marker", f"marker_{i}", "glow")
                )
                # Move glow behind the main line
                self.waveform_canvas.tag_lower("glow")

            # Draw marker head (draggable handle) - larger if selected
            head_size = 10 if is_selected else 8
            outline_width = 3 if is_selected else 1
            self.waveform_canvas.create_polygon(
                waveform_x - head_size, 0,
                waveform_x + head_size, 0,
                waveform_x, 12 if is_selected else 10,
                fill=color,
                outline="white" if is_selected else "black",
                width=outline_width,
                tags=("marker", f"marker_{i}", "marker_handle")
            )

            # Draw on filmstrip (thicker if selected)
            filmstrip_width_val = 5 if is_selected else 3
            self.filmstrip_canvas.create_line(
                filmstrip_x, 0,
                filmstrip_x, self.filmstrip_canvas_height,
                fill=color,
                width=filmstrip_width_val,
                tags=("marker", f"marker_{i}")
            )

        # Bind drag events to all marker tags (do this once after all markers are drawn)
        for i in range(len(self.markers)):
            # Bind to the tag name, not the items
            self.waveform_canvas.tag_bind(f"marker_{i}", "<Button-1>", lambda e, idx=i: self.start_drag_marker(e, idx))
            self.waveform_canvas.tag_bind(f"marker_{i}", "<B1-Motion>", self.drag_marker)
            self.waveform_canvas.tag_bind(f"marker_{i}", "<ButtonRelease-1>", self.end_drag_marker)

    # ========================================================================
    # EXPORT METHODS
    # ========================================================================

    # ========================================================================
    # AUDIO ASSEMBLY
    # ========================================================================

    def auto_assemble_audio(self):
        """
        Automatically assemble audio after generation completes
        (called if auto_assemble_enabled is True)
        """
        if not self.auto_assemble_enabled.get():
            return

        # Only assemble if there are markers with generated audio
        has_audio = any(
            self.get_current_version_data(m) and
            self.get_current_version_data(m).get('status') == 'generated'
            for m in self.markers
        )

        if not has_audio:
            return

        # Perform assembly
        self._assemble_audio_internal(auto=True)

    def manual_assemble_audio(self):
        """
        Manually assemble audio when user clicks 'Assemble Now' button
        """
        # Perform assembly
        self._assemble_audio_internal(auto=False)

    def _assemble_audio_internal(self, auto=False):
        """
        Internal method to assemble all marker audio files into a single output

        Args:
            auto: True if auto-triggered, False if manual
        """
        try:
            # Check if we have any markers
            if not self.markers:
                messagebox.showinfo(
                    "No Markers",
                    "Add some markers with generated audio first."
                )
                return

            # Check if we have a duration
            if self.duration_ms <= 0:
                messagebox.showerror(
                    "No Timeline",
                    "Create a timeline first (Open Video or Create Blank Timeline)"
                )
                return

            # Import pydub here (only when needed)
            try:
                from pydub import AudioSegment
            except ImportError:
                messagebox.showerror(
                    "Missing Dependency",
                    "Pydub is required for audio assembly.\n\n"
                    "Install it with: pip install pydub\n"
                    "Also requires FFmpeg: brew install ffmpeg"
                )
                return

            # Collect markers with generated audio
            markers_with_audio = []
            for marker in self.markers:
                current_version_data = self.get_current_version_data(marker)
                if current_version_data:
                    status = current_version_data.get('status')
                    asset_file = current_version_data.get('asset_file')
                    if status == 'generated' and asset_file:
                        markers_with_audio.append((marker, asset_file))

            if not markers_with_audio:
                messagebox.showinfo(
                    "No Generated Audio",
                    "No markers have generated audio files.\n\n"
                    "Generate some audio first using the 🔄 buttons."
                )
                return

            # Create silent base track
            print(f"Creating silent base track ({self.duration_ms}ms)...")
            assembled = AudioSegment.silent(duration=self.duration_ms)

            # Overlay each marker's audio
            print(f"Assembling {len(markers_with_audio)} audio file(s)...")
            for marker, asset_file in markers_with_audio:
                marker_type = marker['type']
                time_ms = marker['time_ms']
                marker_name = marker.get('name', '(unnamed)')

                # Find audio file
                possible_paths = [
                    os.path.join("generated_audio", marker_type, asset_file),
                    os.path.join("generated_audio", asset_file),
                    asset_file
                ]

                file_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        file_path = path
                        break

                if not file_path:
                    print(f"  ⚠️  Skipping {marker_name}: File not found ({asset_file})")
                    continue

                # Load and overlay audio
                try:
                    audio = AudioSegment.from_file(file_path)
                    assembled = assembled.overlay(audio, position=time_ms)
                    print(f"  ✓ Overlaid {marker_name} at {time_ms}ms")
                except Exception as e:
                    print(f"  ⚠️  Skipping {marker_name}: {str(e)}")
                    continue

            # Prepare output directory and filename
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)

            template_id = self.template_id or "template"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_auto" if auto else "_manual"
            output_filename = f"{template_id}{suffix}_{timestamp}.wav"
            output_path = output_dir / output_filename

            # Export assembled audio
            print(f"Exporting to {output_path}...")
            assembled.export(str(output_path), format="wav")

            # Show success message
            duration_sec = len(assembled) / 1000
            success_msg = (
                f"Audio assembly complete!\n\n"
                f"Output: {output_path}\n"
                f"Duration: {duration_sec:.2f} seconds\n"
                f"Markers included: {len(markers_with_audio)}"
            )

            messagebox.showinfo("Assembly Complete", success_msg)
            print(f"✓ Assembly complete: {output_path}")

        except Exception as e:
            error_msg = f"Failed to assemble audio:\n\n{str(e)}"
            messagebox.showerror("Assembly Failed", error_msg)
            print(f"✗ Assembly error: {e}")
            import traceback
            traceback.print_exc()

    def import_json(self):
        """Import markers from JSON file"""
        # Confirm if markers already exist
        if self.markers:
            response = messagebox.askyesno(
                "Confirm Import",
                f"This will replace {len(self.markers)} existing marker(s).\n\nContinue?",
                icon='warning'
            )
            if not response:
                return

        # File dialog to select JSON
        filepath = filedialog.askopenfilename(
            title="Import Template Map",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="template_maps"
        )

        if not filepath:
            return

        try:
            # Load JSON file
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Validate required fields
            if "markers" not in data:
                messagebox.showerror("Import Error", "Invalid JSON: 'markers' field missing")
                return

            # Load template metadata
            self.template_id = data.get("template_id", "")
            self.template_name = data.get("template_name", "")
            duration_ms = data.get("duration_ms", 0)

            # Validate duration
            if duration_ms < 0:
                messagebox.showwarning(
                    "Invalid Data",
                    f"Duration cannot be negative ({duration_ms}ms). Setting to 0.",
                    parent=self.root
                )
                duration_ms = 0

            # Migrate markers from old format to new format if needed
            migrated_markers = []
            for i, marker in enumerate(data["markers"]):
                # First migrate prompt format (old string -> new prompt_data)
                migrated = self.migrate_marker_to_new_format(marker)
                # Then migrate to version format
                migrated = self.migrate_marker_to_version_format(migrated)

                # Validate marker time_ms
                if migrated.get("time_ms", 0) < 0:
                    print(f"WARNING: Marker {i} has negative time ({migrated.get('time_ms')}ms), setting to 0")
                    migrated["time_ms"] = 0

                migrated_markers.append(migrated)

            # Clear existing markers
            self.markers = migrated_markers

            # Set duration if provided and no video loaded
            if duration_ms > 0 and not self.video_loaded:
                self.duration_ms = duration_ms
                self.video_loaded = True
                self.update_timeline()

            # Update displays
            self.update_marker_list()
            self.redraw_marker_indicators()

            messagebox.showinfo(
                "Import Success",
                f"Imported {len(self.markers)} marker(s) from:\n{filepath}"
            )
            print(f"✓ Imported {len(self.markers)} markers from {filepath}")

        except json.JSONDecodeError as e:
            messagebox.showerror("Import Error", f"Invalid JSON file:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import:\n{str(e)}")

    def export_json(self):
        """Export markers to JSON file"""
        if not self.markers:
            messagebox.showwarning("No Markers", "Add some markers before exporting")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export Template Map",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="template_maps",
            initialfile=f"{self.template_id}_map.json" if self.template_id else "template_map.json"
        )

        if not filepath:
            return

        # Build JSON structure
        template = {
            "template_id": self.template_id or "TEMPLATE",
            "template_name": self.template_name or "Untitled",
            "duration_ms": self.duration_ms,
            "markers": self.markers
        }

        # Write to file
        with open(filepath, 'w') as f:
            json.dump(template, f, indent=2)

        messagebox.showinfo("Export Success", f"Template exported to:\n{filepath}")
        print(f"✓ Exported {len(self.markers)} markers to {filepath}")


def main():
    """Launch the application"""
    root = tk.Tk()
    app = AudioMapperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
