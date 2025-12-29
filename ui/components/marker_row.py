"""
Marker Row - Custom row widget for marker list

Provides interactive controls for individual markers in the marker list.
Layout: [▶] [🔄] 0:00.150 | SFX | Marker Name | ✓ v1
"""

import tkinter as tk
from tkinter import ttk
import os
from config.color_scheme import COLORS
from ui.components.tooltip import ToolTip
from managers.waveform_manager import WaveformManager


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

        # Waveform canvas (150px × 40px)
        self.waveform_canvas = tk.Canvas(
            self.frame,
            width=150,
            height=40,
            bg=COLORS.bg_tertiary,
            highlightthickness=0
        )
        self.waveform_canvas.pack(side=tk.LEFT, padx=5)
        self.waveform_canvas.bind("<Button-1>", self.on_row_click)
        self.waveform_canvas.bind("<Double-Button-1>", self.on_row_double_click)

        # Initialize waveform data
        self.waveform_data = None
        self.audio_duration_ms = 0

        # Try to load waveform if audio exists
        self.load_waveform()

        # Status icon + Version badge
        status_icon = self.get_status_icon(self.marker.get("status", "not yet generated"))
        current_version = self.marker.get("current_version", 0)

        # Show version only if at least one version exists (current_version > 0)
        if current_version > 0:
            status_version_text = f"{status_icon} v{current_version}"
        else:
            status_version_text = f"{status_icon} (not generated)"

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

        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=150
        )
        # Don't pack it yet - will show when generating

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

    def on_row_click(self, _event=None):
        """Handle row click - select this marker"""
        self.gui.marker_selection_manager.select_marker_row(self.marker_index)

    def on_row_double_click(self, _event=None):
        """Handle double-click - edit marker"""
        self.gui.open_marker_editor(self.marker, self.marker_index)

    def on_play_click(self):
        """Handle play button click"""
        print(f"▶ Play marker {self.marker_index}: {self.marker.get('name', '(unnamed)')}")
        self.gui.play_marker_audio(self.marker_index)

    def on_generate_click(self):
        """Handle generate button click"""
        print(f"🔄 Generate marker {self.marker_index}: {self.marker.get('name', '(unnamed)')}")
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

    def show_progress(self):
        """Show progress bar and set to 0%"""
        self.progress_var.set(0)
        self.progress_bar.pack(side=tk.LEFT, padx=5)

    def update_progress(self, percentage):
        """
        Update progress bar percentage

        Args:
            percentage: Progress value from 0-100
        """
        self.progress_var.set(percentage)

    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.pack_forget()

    def load_waveform(self):
        """
        Load waveform data from audio file if it exists

        Checks for audio file in generated_audio directory and extracts waveform
        """
        # Get current version data to find audio file
        current_version_data = self.gui.get_current_version_data(self.marker)
        if not current_version_data:
            self.draw_waveform_placeholder("No audio yet")
            return

        # Get asset file path
        asset_file = current_version_data.get("asset_file")
        if not asset_file:
            self.draw_waveform_placeholder("No audio file")
            return

        # Construct full path (check multiple possible locations)
        audio_path = None
        possible_paths = [
            os.path.join("generated_audio", asset_file),
            os.path.join("generated_audio", self.marker["type"], asset_file),
            asset_file  # Absolute path
        ]

        for path in possible_paths:
            if os.path.exists(path):
                audio_path = path
                break

        if not audio_path:
            self.draw_waveform_placeholder("Audio not found")
            return

        # Extract waveform data using WaveformManager
        self.waveform_data, self.audio_duration_ms = WaveformManager.extract_waveform_from_audio(
            audio_path,
            target_width=150  # Match canvas width
        )

        if self.waveform_data:
            self.draw_waveform()
        else:
            self.draw_waveform_placeholder("Load failed")

    def draw_waveform(self):
        """Draw waveform visualization on canvas"""
        if not self.waveform_data:
            return

        # Clear canvas
        self.waveform_canvas.delete("all")

        canvas_width = 150
        canvas_height = 40
        mid_y = canvas_height // 2

        # Draw waveform bars
        for i, amplitude in enumerate(self.waveform_data):
            # Calculate x position
            x = int((i / len(self.waveform_data)) * canvas_width)

            # Scale amplitude to fit canvas
            height = int(amplitude * (canvas_height / 2) * 0.9)

            # Draw vertical line
            self.waveform_canvas.create_line(
                x, mid_y - height,
                x, mid_y + height,
                fill=COLORS.waveform_color,
                width=1,
                tags="waveform"
            )

        # Draw center line
        self.waveform_canvas.create_line(
            0, mid_y,
            canvas_width, mid_y,
            fill=COLORS.centerline,
            width=1,
            tags="centerline"
        )

    def draw_waveform_placeholder(self, text: str):
        """Draw placeholder text on waveform canvas"""
        self.waveform_canvas.delete("all")
        self.waveform_canvas.create_text(
            75, 20,  # Center of 150×40 canvas
            text=text,
            fill=COLORS.placeholder_text,
            font=("Arial", 8),
            tags="placeholder"
        )

    def refresh_waveform(self):
        """Refresh waveform display (call after audio generation completes)"""
        self.load_waveform()
