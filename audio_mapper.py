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

# Import extracted modules
from color_scheme import COLORS
from commands import (
    AddMarkerCommand,
    DeleteMarkerCommand,
    MoveMarkerCommand,
    EditMarkerCommand,
    GenerateAudioCommand
)
from history_manager import HistoryManager
from tooltip import ToolTip
from models import Marker, AudioVersion, MarkerType, MarkerStatus, create_marker
from waveform_manager import WaveformManager
from filmstrip_manager import FilmstripManager
from file_handler import FileHandler
from video_player_controller import VideoPlayerController
from version_manager import MarkerVersionManager
from keyboard_manager import KeyboardShortcutManager
from marker_selection_manager import MarkerSelectionManager
from audio_service import AudioGenerationService


# ============================================================================
# MUSIC SECTION EDITOR WINDOW - Nested modal for editing music sections
# ============================================================================

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
        self.gui.marker_selection_manager.select_marker_row(self.marker_index)

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

        # Video player controller (initialized after UI creation)
        self.video_player = None

        # State variables
        self.template_id = ""
        self.template_name = ""

        # Marker repository (decoupled data layer)
        from marker_repository import MarkerRepository
        self.marker_repository = MarkerRepository()

        # Register UI update callback for when markers change
        self.marker_repository.add_change_listener(self._on_markers_changed)

        # Backward compatibility: expose markers as property
        self.markers = self.marker_repository.markers

        # Undo/redo system
        self.history = HistoryManager(max_history=50)

        # Audio player for marker audio playback
        self.audio_player = AudioPlayer()

        # Audio generation service (extracted for modularity)
        self.audio_service = AudioGenerationService(self)

        # Auto-assembly setting
        self.auto_assemble_enabled = tk.BooleanVar(value=False)

        # Drag state for marker repositioning
        self.dragging_marker = None
        self.drag_start_x = None
        self.drag_marker_index = None

        # Marker selection manager (initialized after UI creation)
        self.marker_selection_manager = None

        # Waveform and Filmstrip managers (initialized after UI creation)
        self.waveform_manager = None
        self.filmstrip_manager = None
        self.waveform_canvas_height = 80
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

        # Initialize marker selection manager
        self.marker_selection_manager = MarkerSelectionManager(
            markers=self.markers,
            marker_row_widgets=self.marker_row_widgets,
            marker_canvas=self.marker_canvas,
            on_seek=self._on_marker_seek,
            on_redraw_indicators=self.redraw_marker_indicators
        )

        # Initialize video player controller
        self.video_player = VideoPlayerController(
            video_canvas=self.video_canvas,
            play_button=self.play_button,
            timeline_slider=self.timeline_slider,
            timestamp_label=self.timestamp_label,
            fps_label=self.fps_label,
            on_update_filmstrip=self._update_filmstrip_position,
            on_update_waveform=self._update_waveform_position,
            on_timeline_slider_update=lambda time_ms: self.timeline_slider.set(time_ms),
            on_template_prompt=self.prompt_template_info
        )

        # Initialize keyboard shortcut manager
        self.keyboard_manager = KeyboardShortcutManager(
            root=self.root,
            callbacks={
                'toggle_playback': lambda: self.video_player.toggle_playback() if self.video_player else None,
                'add_marker': self.add_marker,
                'delete_marker': self.delete_marker,
                'nudge_selected_marker': self.nudge_selected_marker,
                'nudge_selected_marker_by_frame': self.nudge_selected_marker_by_frame,
                'step_time': self.step_time,
                'step_frame': self.step_frame,
                'undo': self.undo,
                'redo': self.redo,
                'play_marker_audio': self.play_marker_audio,
                'generate_marker_audio': self.generate_marker_audio,
                'load_video': self.load_video,
                'get_selected_marker_index': lambda: self.marker_selection_manager.get_selected_index(),
                'set_selected_marker_index': lambda idx: self.marker_selection_manager.set_selected_index(idx),
                'redraw_marker_indicators': self.redraw_marker_indicators,
                'get_marker_row_widgets': lambda: self.marker_row_widgets
            }
        )

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

        # Initialize filmstrip manager
        self.filmstrip_manager = FilmstripManager(
            canvas=self.filmstrip_canvas,
            canvas_height=self.filmstrip_canvas_height,
            thumb_width=self.filmstrip_thumb_width,
            thumb_height=self.filmstrip_thumb_height,
            on_seek=self._on_filmstrip_seek,
            on_deselect_marker=lambda: self.marker_selection_manager.deselect_marker()
        )

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

        # Initialize waveform manager
        self.waveform_manager = WaveformManager(
            canvas=self.waveform_canvas,
            canvas_height=self.waveform_canvas_height,
            on_seek=self._on_waveform_seek,
            on_deselect_marker=lambda: self.marker_selection_manager.deselect_marker()
        )

    def _on_waveform_seek(self, time_ms):
        """Callback when user clicks waveform to seek"""
        self.seek_to_time(time_ms)
        self.timeline_slider.set(self.video_player.get_current_time())

    def _on_filmstrip_seek(self, time_ms):
        """Callback when user clicks filmstrip to seek"""
        self.seek_to_time(time_ms)
        self.timeline_slider.set(self.video_player.get_current_time())

    def _on_marker_seek(self, time_ms):
        """Callback when jumping to a marker"""
        self.seek_to_time(time_ms)
        self.timeline_slider.set(self.video_player.get_current_time())

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
            command=lambda: self.marker_selection_manager.jump_to_marker(),
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


    # ========================================================================
    # MARKER DATA STRUCTURE HELPERS
    # ========================================================================

    def migrate_marker_to_new_format(self, marker):
        """Convert old marker format (prompt string) to new format (prompt_data)"""
        return MarkerVersionManager.migrate_marker_to_new_format(marker)

    # ========================================================================
    # VERSION MANAGEMENT METHODS
    # ========================================================================

    def get_current_version_data(self, marker):
        """
        Get the current version object from a marker

        Returns the version object for the current active version, or None if no versions exist
        """
        return MarkerVersionManager.get_current_version_data(marker)

    def add_new_version(self, marker, prompt_data):
        """
        Create a new version for a marker

        Args:
            marker: The marker dict to add version to
            prompt_data: The prompt_data to use for this version

        Returns:
            The new version number
        """
        return MarkerVersionManager.add_new_version(marker, prompt_data)

    def rollback_to_version(self, marker, version_num):
        """
        Roll back a marker to a specific version

        Args:
            marker: The marker dict
            version_num: The version number to roll back to

        Returns:
            True if successful, False if version not found
        """
        return MarkerVersionManager.rollback_to_version(marker, version_num)

    def migrate_marker_to_version_format(self, marker):
        """
        Migrate a marker to the new version-based format

        Handles both old format (no versions) and ensures version structure exists
        """
        return MarkerVersionManager.migrate_marker_to_version_format(marker)

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
        return MarkerVersionManager.create_default_prompt_data(marker_type)

    # ========================================================================
    # VIDEO PLAYBACK METHODS (OpenCV)
    # ========================================================================

    def load_video(self):
        """Load video file using OpenCV - delegates to VideoPlayerController"""
        # Delegate to video player controller
        filepath = self.video_player.load_video()

        if not filepath:
            return

        # Extract and display film strip
        if self.filmstrip_manager:
            self.filmstrip_manager.extract_frames(
                self.video_player.video_capture,
                self.video_player.duration_ms,
                self.video_player.fps,
                num_thumbs=15
            )
            self.filmstrip_manager.draw()

        # Extract and display audio waveform
        if self.waveform_manager:
            self.waveform_manager.extract_and_display(filepath)

    def create_blank_timeline(self):
        """Create blank timeline without video - delegates to VideoPlayerController"""
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
            # Delegate to video player controller
            if self.video_player.create_blank_timeline(duration_var.get()):
                dialog.destroy()

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
        """Seek to specific time - delegates to VideoPlayerController"""
        self.video_player.seek_to_time(time_ms)

    def toggle_playback(self):
        """Toggle play/pause - delegates to VideoPlayerController"""
        self.video_player.toggle_playback()

    def step_time(self, delta_ms):
        """Step forward/backward by delta_ms - delegates to VideoPlayerController"""
        self.video_player.step_time(delta_ms)

    def step_frame(self, delta_frames):
        """Step forward/backward by frames - delegates to VideoPlayerController"""
        self.video_player.step_frame(delta_frames)

    def on_timeline_change(self, value):
        """Handle timeline slider change - delegates to VideoPlayerController"""
        self.video_player.on_timeline_change(value)

    def update_timeline(self):
        """Update timeline position and display - delegates to VideoPlayerController"""
        # Delegate to video player controller
        self.video_player.update_timeline()

        # Schedule next update (30 FPS refresh rate)
        self.root.after(33, self.update_timeline)

    def _update_filmstrip_position(self, time_ms):
        """Callback to update filmstrip position"""
        if self.filmstrip_manager:
            self.filmstrip_manager.update_position(time_ms)

    def _update_waveform_position(self, time_ms):
        """Callback to update waveform position"""
        if self.waveform_manager:
            self.waveform_manager.update_position(time_ms)

    # ========================================================================
    # FILM STRIP AND WAVEFORM METHODS - Now handled by managers
    # ========================================================================
    # Filmstrip and waveform display/interaction are now managed by
    # FilmstripManager and WaveformManager classes. See filmstrip_manager.py
    # and waveform_manager.py for implementation.

    def draw_filmstrip(self):
        """Draw film strip thumbnails on canvas - delegates to FilmstripManager"""
        if self.filmstrip_manager:
            self.filmstrip_manager.draw()

    def update_filmstrip_position(self):
        """Update position indicator on film strip - delegates to FilmstripManager"""
        if self.filmstrip_manager:
            self.filmstrip_manager.update_position(self.video_player.get_current_time())

    def on_filmstrip_resize(self, event):
        """Handle filmstrip canvas resize - redraw markers (filmstrip handled by manager)"""
        self.redraw_marker_indicators()

    # ========================================================================
    # WAVEFORM METHODS
    # ========================================================================

    def extract_and_display_waveform(self, video_filepath):
        """Extract audio from video and display waveform - delegates to WaveformManager"""
        if self.waveform_manager:
            self.waveform_manager.extract_and_display(video_filepath)

    def draw_waveform(self):
        """Draw waveform on canvas - delegates to WaveformManager"""
        if self.waveform_manager:
            self.waveform_manager.draw()

    def update_waveform_position(self):
        """Update position indicator on waveform - delegates to WaveformManager"""
        if self.waveform_manager:
            self.waveform_manager.update_position(self.video_player.get_current_time())

    def on_waveform_resize(self, event):
        """Handle waveform canvas resize - redraw markers (waveform handled by manager)"""
        self.redraw_marker_indicators()

    # ========================================================================
    # MARKER MANAGEMENT METHODS
    # ========================================================================

    def add_marker_by_type(self, marker_type):
        """Add marker of specific type at current position and open editor"""
        if not self.video_player.is_video_loaded():
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

        current_time = self.video_player.get_current_time()

        marker = {
            "time_ms": current_time,
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
        command = AddMarkerCommand(self.marker_repository, marker)
        self.history.execute_command(command)

        # Get the index of the newly added marker (last one in the list)
        marker_index = len(self.markers) - 1

        # Define cancel callback that undoes the add if user cancels
        def on_cancel():
            self.history.undo()

        # Immediately open editor for the new marker
        self.open_marker_editor(self.markers[marker_index], marker_index, on_cancel_callback=on_cancel)

        print(f"✓ Added {marker_type} marker at {current_time}ms")

    def add_marker(self):
        """Legacy add_marker for backward compatibility - defaults to SFX"""
        # This is called by keyboard shortcut 'M'
        # Default to SFX type
        self.add_marker_by_type("sfx")

    def open_marker_editor(self, marker, marker_index, on_cancel_callback=None):
        """Open the PromptEditorWindow modal for editing a marker"""
        # Create save callback that uses EditMarkerCommand
        def on_save(updated_marker):
            # Get current marker state before update
            old_marker = self.markers[marker_index].copy()

            # Execute edit via command pattern for undo/redo support
            command = EditMarkerCommand(
                self.marker_repository,
                marker_index,
                old_marker,
                updated_marker
            )
            self.history.execute_command(command)

            print(f"✓ Updated marker at {updated_marker['time_ms']}ms")

        # Open the editor window
        PromptEditorWindow(
            parent=self.root,
            marker=marker,
            marker_index=marker_index,
            on_save_callback=on_save,
            on_cancel_callback=on_cancel_callback,
            gui_ref=self
        )

    def delete_marker(self):
        """Delete the currently selected marker"""
        selected_index = self.marker_selection_manager.get_selected_index()

        if selected_index is None:
            messagebox.showwarning("No Selection", "Please select a marker to delete")
            return

        if not 0 <= selected_index < len(self.markers):
            return

        marker = self.markers[selected_index]

        # Execute via command pattern for undo/redo support
        command = DeleteMarkerCommand(self.marker_repository, marker)
        self.history.execute_command(command)

        print(f"✓ Deleted marker at {marker['time_ms']}ms")

    def clear_all_markers(self):
        """Clear all markers with confirmation"""
        if not self.markers:
            return

        if messagebox.askyesno("Clear All Markers", f"Delete all {len(self.markers)} markers?"):
            self.markers.clear()
            self.update_marker_list()
            self.redraw_marker_indicators()

    def nudge_selected_marker(self, delta_ms):
        """Nudge selected marker by delta_ms milliseconds"""
        selected_marker_index = self.marker_selection_manager.get_selected_index()

        if selected_marker_index is None or selected_marker_index >= len(self.markers):
            print("No marker selected for nudging")
            return

        marker = self.markers[selected_marker_index]
        old_time_ms = marker["time_ms"]
        duration = self.video_player.get_duration()
        new_time_ms = max(0, min(old_time_ms + delta_ms, duration))

        if new_time_ms != old_time_ms:
            # Create and execute move command
            command = MoveMarkerCommand(self.marker_repository, selected_marker_index, old_time_ms, new_time_ms)
            self.history.execute_command(command)
            print(f"→ Nudged marker {delta_ms:+d}ms: {old_time_ms}ms → {new_time_ms}ms")

    def nudge_selected_marker_by_frame(self, delta_frames):
        """Nudge selected marker by exact number of frames"""
        if not self.video_player.is_video_loaded() or not self.video_player.video_capture:
            print("Frame nudging only works with video loaded")
            return

        # Calculate time per frame
        fps = self.video_player.get_fps()
        frame_duration_ms = 1000 / fps if fps > 0 else 33
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

    def _on_markers_changed(self):
        """
        Callback triggered when marker repository changes.
        Updates UI to reflect data changes.
        This is registered as a listener with MarkerRepository.
        """
        self.update_marker_list()
        self.redraw_marker_indicators()

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

    def redraw_marker_indicators(self):
        """Redraw marker indicators on waveform and filmstrip canvases"""
        # Remove old markers
        self.waveform_canvas.delete("marker")
        self.filmstrip_canvas.delete("marker")

        duration = self.video_player.get_duration()
        if not self.video_player.is_video_loaded() or duration == 0:
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

            # Check if this marker is selected using MarkerSelectionManager
            is_selected = (i == self.marker_selection_manager.get_selected_index())

            # Calculate x position
            waveform_x = int((time_ms / duration) * waveform_width)
            filmstrip_x = int((time_ms / duration) * filmstrip_width)

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
        """Delegate to audio service"""
        self.audio_service.generate_marker_audio(marker_index)

    # ========================================================================
    # BATCH GENERATION OPERATIONS
    # ========================================================================

    def batch_generate_missing(self):
        """Delegate to audio service"""
        self.audio_service.batch_generate_missing()

    def batch_regenerate_all(self):
        """Delegate to audio service"""
        self.audio_service.batch_regenerate_all()

    def batch_generate_by_type(self):
        """Delegate to audio service"""
        self.audio_service.batch_generate_by_type()
    # ========================================================================
    # AUDIO ASSEMBLY
    # ========================================================================

    def auto_assemble_audio(self):
        """Delegate to audio service"""
        self.audio_service.auto_assemble_audio()

    def manual_assemble_audio(self):
        """Delegate to audio service"""
        self.audio_service.manual_assemble_audio()

    # ========================================================================
    # JSON IMPORT/EXPORT
    # ========================================================================

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
            if duration_ms > 0 and not self.video_player.is_video_loaded():
                self.video_player.create_blank_timeline(duration_ms / 1000.0)
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
            "duration_ms": self.video_player.get_duration(),
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
