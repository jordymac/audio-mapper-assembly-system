#!/usr/bin/env python3
"""
Prompt Editor Window - Modal editor for marker prompt data

Refactored to use modular editor components (SfxEditor, VoiceEditor, MusicEditor).
Extracted from audio_mapper.py as part of Sprint 4.1 refactoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from config.color_scheme import COLORS
from ui.editors.sfx_editor import SfxEditor
from ui.editors.voice_editor import VoiceEditor
from ui.editors.music_editor import MusicEditor


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

        # Current editor component reference (SfxEditor, VoiceEditor, or MusicEditor)
        self.current_editor = None

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
                f"Version {selected_version_num} is already the current version.",
                parent=self.window
            )
            return

        # Confirm rollback
        confirm = messagebox.askyesno(
            "Confirm Rollback",
            f"Roll back to version {selected_version_num}?\n\n"
            f"This will make v{selected_version_num} the active version.\n"
            f"The prompt data will be restored from this version.",
            parent=self.window
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
                    f"Rolled back to version {selected_version_num}",
                    parent=self.window
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
            messagebox.showerror(
                "No Version",
                "Selected version not found.",
                parent=self.window
            )
            return

        asset_file = version_data.get('asset_file')
        if not asset_file:
            messagebox.showerror(
                "No Audio",
                f"Version {selected_version_num} has no generated audio file.",
                parent=self.window
            )
            return

        # Build file path
        marker_type = self.marker.get('type', 'sfx')
        file_path = os.path.join("generated_audio", marker_type, asset_file)

        # Check if file exists
        if not os.path.exists(file_path):
            messagebox.showerror(
                "File Not Found",
                f"Audio file not found:\n{file_path}",
                parent=self.window
            )
            return

        # Play using GUI's audio player if available
        if self.gui_ref and hasattr(self.gui_ref, 'audio_player'):
            success = self.gui_ref.audio_player.play_audio_file(file_path)
            if not success:
                messagebox.showerror(
                    "Playback Error",
                    f"Failed to play audio file:\n{file_path}",
                    parent=self.window
                )
        else:
            messagebox.showinfo(
                "Audio Player Not Available",
                "Cannot play audio - audio player not initialized.",
                parent=self.window
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

        # Clear current editor reference
        self.current_editor = None

        marker_type = self.marker["type"]

        # Instantiate appropriate editor component
        if marker_type == "sfx":
            self.current_editor = SfxEditor(self.content_frame, self.marker, self.window)
        elif marker_type == "voice":
            self.current_editor = VoiceEditor(self.content_frame, self.marker, self.window)
        elif marker_type == "music":
            self.current_editor = MusicEditor(self.content_frame, self.marker, self.window)
        else:
            tk.Label(
                self.content_frame,
                text=f"Unknown marker type: {marker_type}",
                font=("Arial", 12),
                fg="#666"
            ).pack(expand=True)

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

            # Validate and save via current editor component
            if self.current_editor is None:
                messagebox.showerror(
                    "No Editor",
                    "No editor component is active",
                    parent=self.window
                )
                return

            # Call editor's validate_and_save method
            if not self.current_editor.validate_and_save():
                return  # Validation failed

            # NOTE: Version creation now happens ONLY during generation (not on save)
            # This ensures the workflow: Create → Save → Generate (v1) → Regenerate (v2, v3, etc.)

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
