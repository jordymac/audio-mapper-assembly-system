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
from config.color_scheme import COLORS, create_colored_button
from core.commands import (
    AddMarkerCommand,
    DeleteMarkerCommand,
    MoveMarkerCommand,
    EditMarkerCommand,
    GenerateAudioCommand
)
from core.models import Marker, AudioVersion, MarkerType, MarkerStatus, create_marker
from managers.history_manager import HistoryManager
from managers.waveform_manager import WaveformManager
from managers.filmstrip_manager import FilmstripManager
from managers.version_manager import MarkerVersionManager
from managers.keyboard_manager import KeyboardShortcutManager
from managers.marker_selection_manager import MarkerSelectionManager
from managers.marker_manager import MarkerManager
from controllers.file_handler import FileHandler
from controllers.video_player_controller import VideoPlayerController
from services.audio_service import AudioGenerationService
from services.audio_player import AudioPlayer
from services.assembly_service import AssemblyService
from ui.components.tooltip import ToolTip
from ui.components.marker_row import MarkerRow
from ui.components.multi_track_display import MultiTrackDisplay
from ui.editors.prompt_editor import PromptEditorWindow


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
        from core.marker_repository import MarkerRepository
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

        # Assembly service (multi-track audio assembly)
        self.assembly_service = AssemblyService(temp_dir="temp")

        # Auto-assembly setting
        self.auto_assemble_enabled = tk.BooleanVar(value=False)

        # Assembly state
        self.assembled_preview_file = None
        self.is_assembled = False

        # Drag state for marker repositioning
        self.dragging_marker = None
        self.drag_start_x = None
        self.drag_marker_index = None

        # Marker selection manager (initialized after UI creation)
        self.marker_selection_manager = None

        # Marker manager (coordinates marker operations)
        self.marker_manager = None

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
        self.create_multi_track_display()
        self.create_timeline_controls()
        self.create_marker_list()
        self.create_bottom_button_bar()

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

        # Initialize marker manager
        self.marker_manager = MarkerManager(
            marker_repository=self.marker_repository,
            history_manager=self.history,
            get_current_time=lambda: self.video_player.get_current_time() if self.video_player else 0,
            get_duration=lambda: self.video_player.get_duration() if self.video_player else 0,
            is_video_loaded=lambda: self.video_player.is_video_loaded() if self.video_player else False
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
        filmstrip_container = tk.Frame(self.root, bg=COLORS.bg_secondary)
        filmstrip_container.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Film strip canvas
        self.filmstrip_canvas = tk.Canvas(
            filmstrip_container,
            bg=COLORS.bg_primary,
            height=self.filmstrip_canvas_height,
            highlightthickness=1,
            highlightbackground=COLORS.border
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

    def create_multi_track_display(self):
        """Create multi-track waveform display (5 channels)"""
        # Initialize multi-track display component
        self.multi_track_display = MultiTrackDisplay(
            parent=self.root,
            on_seek_callback=self._on_multitrack_seek
        )

        # Keep waveform_canvas reference for backward compatibility (points to music track for now)
        # This will be refactored in later phases
        music_canvas = self.multi_track_display.get_canvas("music_lr")
        if isinstance(music_canvas, dict):
            self.waveform_canvas = music_canvas["L"]  # Use L channel as default
        else:
            self.waveform_canvas = music_canvas

        # Keep waveform manager for single-track backward compatibility
        # This will be replaced with multi-track waveform generation in Phase 3
        if self.waveform_canvas:
            self.waveform_manager = WaveformManager(
                canvas=self.waveform_canvas,
                canvas_height=45,  # Half of stereo height
                on_seek=self._on_waveform_seek,
                on_deselect_marker=lambda: self.marker_selection_manager.deselect_marker() if self.marker_selection_manager else None
            )

    def _on_multitrack_seek(self, click_ratio):
        """Handle seek from multi-track display click"""
        if self.video_player:
            duration_ms = self.video_player.get_duration()
            time_ms = click_ratio * duration_ms
            self._on_waveform_seek(time_ms)

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

    def create_bottom_button_bar(self):
        """Create bottom button bar with Add Marker buttons, Assemble, and Export"""
        button_bar = tk.Frame(self.root, bg=COLORS.bg_secondary, padx=10, pady=10)
        button_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Left side: Add Marker buttons (smaller, compact)
        left_buttons = tk.Frame(button_bar, bg=COLORS.bg_secondary)
        left_buttons.pack(side=tk.LEFT)

        create_colored_button(
            left_buttons,
            text="+SFX",
            command=lambda: self.add_marker_by_type("sfx"),
            bg_color=COLORS.sfx_bg,
            fg_color=COLORS.sfx_fg,
            font=("Arial", 9, "bold"),
            width=8,
            height=1
        ).pack(side=tk.LEFT, padx=2)

        create_colored_button(
            left_buttons,
            text="+Music",
            command=lambda: self.add_marker_by_type("music"),
            bg_color=COLORS.music_bg,
            fg_color=COLORS.music_fg,
            font=("Arial", 9, "bold"),
            width=8,
            height=1
        ).pack(side=tk.LEFT, padx=2)

        create_colored_button(
            left_buttons,
            text="+Voice",
            command=lambda: self.add_marker_by_type("voice"),
            bg_color=COLORS.voice_bg,
            fg_color=COLORS.voice_fg,
            font=("Arial", 9, "bold"),
            width=8,
            height=1
        ).pack(side=tk.LEFT, padx=2)

        # Right side: Assemble and Export buttons
        right_buttons = tk.Frame(button_bar, bg=COLORS.bg_secondary)
        right_buttons.pack(side=tk.RIGHT)

        # Assemble button (will be implemented in Phase 4)
        self.assemble_button = create_colored_button(
            right_buttons,
            text="🔨 Assemble",
            command=self.assemble_audio,
            bg_color=COLORS.btn_success_bg,
            fg_color=COLORS.btn_success_fg,
            font=("Arial", 9, "bold"),
            width=12,
            height=1
        )
        self.assemble_button.pack(side=tk.LEFT, padx=5)

        # Export button
        create_colored_button(
            right_buttons,
            text="📦 Export",
            command=self.open_export_center,
            bg_color=COLORS.btn_primary_bg,
            fg_color=COLORS.btn_primary_fg,
            font=("Arial", 9, "bold"),
            width=12,
            height=1
        ).pack(side=tk.LEFT, padx=5)

    def assemble_audio(self):
        """Assemble multi-track audio from all markers"""
        # Check if we have markers
        if not self.markers:
            messagebox.showwarning("Assembly", "No markers to assemble. Add some markers first!")
            return

        # Check if video is loaded (need duration)
        if not self.video_player or not self.video_player.is_video_loaded():
            messagebox.showwarning("Assembly", "Please load a video first to get duration.")
            return

        # Get duration
        duration_ms = self.video_player.get_duration()

        # Check if any markers have generated audio
        markers_with_audio = [m for m in self.markers if m.asset_file and os.path.exists(m.asset_file)]
        if not markers_with_audio:
            response = messagebox.askyesno(
                "Assembly",
                "No markers have generated audio yet.\n\nWould you like to generate all missing audio first?"
            )
            if response:
                # Trigger batch generation
                self.batch_generate_missing()
                return
            else:
                return

        try:
            # Show assembly progress
            messagebox.showinfo("Assembly", "Assembling audio tracks...\n\nThis may take a moment.")

            # Call assembly service
            track_files, preview_file = self.assembly_service.assemble_audio(
                markers=self.markers,
                duration_ms=duration_ms
            )

            # Store preview file
            self.assembled_preview_file = preview_file
            self.is_assembled = True

            # Update button text
            self.assemble_button.config(text="🔄 Re-assemble")

            # Generate waveforms for each track
            print("Generating track waveforms...")
            track_waveforms = self.assembly_service.get_track_waveforms(track_files, num_samples=1000)

            # Draw waveforms on multi-track display
            for track_id, waveform_data in track_waveforms.items():
                if "L" in waveform_data and "R" in waveform_data:
                    # Stereo track (music)
                    self.multi_track_display.draw_waveform(track_id, waveform_data["L"], channel="L")
                    self.multi_track_display.draw_waveform(track_id, waveform_data["R"], channel="R")
                elif "mono" in waveform_data:
                    # Mono track
                    self.multi_track_display.draw_waveform(track_id, waveform_data["mono"], channel="mono")

            # Draw marker indicators on tracks
            self._draw_marker_indicators_on_tracks(duration_ms)

            # Show summary
            summary = self.assembly_service.get_track_assignment_summary()
            messagebox.showinfo(
                "Assembly Complete",
                f"✓ Assembly successful!\n\n{summary}\n\nWaveforms displayed on tracks!"
            )

            # TODO Phase 4: Replace video player audio with assembled preview

        except Exception as e:
            messagebox.showerror("Assembly Error", f"Failed to assemble audio:\n\n{str(e)}")
            print(f"Assembly error: {e}")
            import traceback
            traceback.print_exc()

    def _draw_marker_indicators_on_tracks(self, duration_ms):
        """Draw marker indicators on their assigned tracks"""
        if not self.is_assembled or not self.assembly_service.track_assignments:
            return

        # Draw markers on each track
        for track_id, markers in self.assembly_service.track_assignments.items():
            if markers:
                self.multi_track_display.draw_marker_indicators(track_id, markers, duration_ms)

    def open_export_center(self):
        """Open Export Center window (to be implemented)"""
        # Placeholder for Export Center
        messagebox.showinfo("Export", "Export Center coming soon!")

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
        self.marker_canvas = tk.Canvas(list_container, bg=COLORS.bg_primary, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, command=self.marker_canvas.yview)
        self.marker_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.marker_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame inside canvas to hold marker rows
        self.marker_rows_frame = tk.Frame(self.marker_canvas, bg=COLORS.bg_primary)
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
        export_btn = create_colored_button(
            export_container,
            text="⬇\nExport\nJSON",
            command=self.export_json,
            bg_color=COLORS.btn_primary_bg,
            fg_color=COLORS.btn_primary_fg,
            font=("Arial", 9, "bold"),
            width=18,
            height=4
        )
        export_btn.pack(pady=(0, 10), fill=tk.X)

        # Batch operation buttons - stacked vertically
        create_colored_button(
            export_container,
            text="🔄 Generate All Missing",
            command=self.batch_generate_missing,
            bg_color=COLORS.btn_success_bg,
            fg_color=COLORS.btn_success_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2
        ).pack(pady=2, fill=tk.X)

        create_colored_button(
            export_container,
            text="🔄 Regenerate All",
            command=self.batch_regenerate_all,
            bg_color=COLORS.btn_warning_bg,
            fg_color=COLORS.btn_warning_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2
        ).pack(pady=2, fill=tk.X)

        create_colored_button(
            export_container,
            text="🔄 Generate Type...",
            command=self.batch_generate_by_type,
            bg_color=COLORS.btn_primary_bg,
            fg_color=COLORS.btn_primary_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2
        ).pack(pady=2, fill=tk.X)

        create_colored_button(
            export_container,
            text="🎵 Assemble Now",
            command=self.manual_assemble_audio,
            bg_color=COLORS.btn_special_bg,
            fg_color=COLORS.btn_special_fg,
            font=("Arial", 8, "bold"),
            width=18,
            height=2
        ).pack(pady=2, fill=tk.X)

        # Control buttons
        button_frame = tk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        create_colored_button(
            button_frame,
            text="Jump to Marker",
            command=lambda: self.marker_selection_manager.jump_to_marker(),
            bg_color=COLORS.btn_primary_bg,
            fg_color=COLORS.btn_primary_fg,
            width=15,
            height=2,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        create_colored_button(
            button_frame,
            text="Delete Marker",
            command=self.delete_marker,
            bg_color=COLORS.btn_danger_bg,
            fg_color=COLORS.btn_danger_fg,
            width=15,
            height=2,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)

        create_colored_button(
            button_frame,
            text="Clear All",
            command=self.clear_all_markers,
            bg_color=COLORS.bg_secondary,
            fg_color=COLORS.fg_primary,
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

        create_colored_button(dialog, text="Create", command=create, bg_color=COLORS.btn_success_bg, fg_color=COLORS.btn_success_fg, font=("Arial", 10)).pack(pady=10)

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

        create_colored_button(dialog, text="OK", command=save, bg_color=COLORS.btn_success_bg, fg_color=COLORS.btn_success_fg, font=("Arial", 10)).pack(pady=15)

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

        # Delegate marker creation to marker_manager
        marker_index = self.marker_manager.add_marker_by_type(marker_type)

        if marker_index is None:
            return

        # Define cancel callback that undoes the add if user cancels
        def on_cancel():
            self.history.undo()

        # Immediately open editor for the new marker
        self.open_marker_editor(self.markers[marker_index], marker_index, on_cancel_callback=on_cancel)

        current_time = self.markers[marker_index]["time_ms"]
        print(f"✓ Added {marker_type} marker at {current_time}ms")

    def add_marker(self):
        """Legacy add_marker for backward compatibility - defaults to SFX"""
        # This is called by keyboard shortcut 'M'
        # Default to SFX type
        self.add_marker_by_type("sfx")

    def open_marker_editor(self, marker, marker_index, on_cancel_callback=None):
        """Open the PromptEditorWindow modal for editing a marker"""
        # Create save callback that uses marker_manager
        def on_save(updated_marker, index):
            # Delegate to marker_manager
            if self.marker_manager.update_marker(index, updated_marker):
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

        marker = self.markers[selected_index]
        marker_time = marker['time_ms']

        # Delegate to marker_manager
        if self.marker_manager.delete_marker_at_index(selected_index):
            print(f"✓ Deleted marker at {marker_time}ms")

    def clear_all_markers(self):
        """Clear all markers with confirmation"""
        if not self.markers:
            return

        count = len(self.markers)
        if messagebox.askyesno("Clear All Markers", f"Delete all {count} markers?"):
            # Delegate to marker_manager
            self.marker_manager.clear_all_markers()
            print(f"✓ Cleared {count} markers")

    def nudge_selected_marker(self, delta_ms):
        """Nudge selected marker by delta_ms milliseconds"""
        selected_marker_index = self.marker_selection_manager.get_selected_index()

        if selected_marker_index is None or selected_marker_index >= len(self.markers):
            print("No marker selected for nudging")
            return

        marker = self.markers[selected_marker_index]
        old_time_ms = marker["time_ms"]

        # Delegate to marker_manager
        if self.marker_manager.nudge_marker(selected_marker_index, delta_ms):
            new_time_ms = self.markers[selected_marker_index]["time_ms"]
            print(f"→ Nudged marker {delta_ms:+d}ms: {old_time_ms}ms → {new_time_ms}ms")

    def nudge_selected_marker_by_frame(self, delta_frames):
        """Nudge selected marker by exact number of frames"""
        if not self.video_player.is_video_loaded() or not self.video_player.video_capture:
            print("Frame nudging only works with video loaded")
            return

        selected_marker_index = self.marker_selection_manager.get_selected_index()

        if selected_marker_index is None:
            print("No marker selected for nudging")
            return

        # Get FPS for frame calculation
        fps = self.video_player.get_fps()
        if fps <= 0:
            fps = 30.0  # Default fallback

        # Delegate to marker_manager
        if self.marker_manager.nudge_marker_by_frame(selected_marker_index, delta_frames, fps):
            marker = self.markers[selected_marker_index]
            print(f"→ Nudged marker by {delta_frames:+d} frames to {marker['time_ms']}ms")

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
            "music": COLORS.music_bg,
            "sfx": COLORS.sfx_bg,
            "voice": COLORS.voice_bg,
            "music_control": COLORS.btn_special_bg
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

    def show_marker_progress(self, marker_index):
        """
        Show progress bar for a marker row

        Args:
            marker_index: Index of marker
        """
        if 0 <= marker_index < len(self.marker_row_widgets):
            row_widget = self.marker_row_widgets[marker_index]
            row_widget.show_progress()

    def update_marker_progress(self, marker_index, percentage):
        """
        Update progress bar for a marker row

        Args:
            marker_index: Index of marker
            percentage: Progress percentage (0-100)
        """
        if 0 <= marker_index < len(self.marker_row_widgets):
            row_widget = self.marker_row_widgets[marker_index]
            row_widget.update_progress(percentage)

    def hide_marker_progress(self, marker_index):
        """
        Hide progress bar for a marker row

        Args:
            marker_index: Index of marker
        """
        if 0 <= marker_index < len(self.marker_row_widgets):
            row_widget = self.marker_row_widgets[marker_index]
            row_widget.hide_progress()

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
