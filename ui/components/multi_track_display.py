"""
Multi-Track Waveform Display Component
Displays 5 audio channels with individual waveforms and volume controls
"""

import tkinter as tk
from tkinter import ttk
from config.color_scheme import COLORS


class MultiTrackDisplay:
    """
    Multi-track waveform visualization with 5 channels:
    - Channels 1-2: Music (Stereo L/R) - shown as 2 rows
    - Channel 3: SFX 1 (Mono)
    - Channel 4: SFX 2 (Mono)
    - Channel 5: Voice (Mono)
    """

    # Track configuration
    TRACK_CONFIG = [
        {"id": "music_lr", "label": "Music L/R", "channels": [1, 2], "type": "stereo", "height": 90, "color": COLORS.music_bg},
        {"id": "sfx_1", "label": "Ch 3 (SFX 1)", "channels": [3], "type": "mono", "height": 45, "color": COLORS.sfx_bg},
        {"id": "sfx_2", "label": "Ch 4 (SFX 2)", "channels": [4], "type": "mono", "height": 45, "color": COLORS.sfx_bg},
        {"id": "voice", "label": "Ch 5 (Voice)", "channels": [5], "type": "mono", "height": 45, "color": COLORS.voice_bg},
    ]

    LABEL_WIDTH = 100
    VOLUME_SLIDER_WIDTH = 100

    def __init__(self, parent, on_seek_callback=None):
        """
        Initialize multi-track display

        Args:
            parent: Parent Tkinter widget
            on_seek_callback: Callback when user clicks track to seek (time_ms)
        """
        self.parent = parent
        self.on_seek_callback = on_seek_callback

        # Container frame
        self.container = tk.Frame(parent, bg=COLORS.bg_secondary)
        self.container.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Track widgets: {track_id: {"canvas": Canvas, "volume": Scale, "label": Label}}
        self.track_widgets = {}

        # Volume values: {track_id: IntVar}
        self.volume_vars = {}

        # Build tracks
        self._create_tracks()

    def _create_tracks(self):
        """Create all track rows"""
        for track_config in self.TRACK_CONFIG:
            track_id = track_config["id"]
            self._create_track_row(track_config)

    def _create_track_row(self, track_config):
        """Create a single track row with label, waveform canvas, and volume slider"""
        track_id = track_config["id"]
        label_text = track_config["label"]
        height = track_config["height"]
        color = track_config["color"]
        is_stereo = track_config["type"] == "stereo"

        # Row frame
        row_frame = tk.Frame(self.container, bg=COLORS.bg_secondary, height=height)
        row_frame.pack(fill=tk.X, pady=1)
        row_frame.pack_propagate(False)

        # Left: Track label
        label_frame = tk.Frame(row_frame, bg=COLORS.bg_secondary, width=self.LABEL_WIDTH)
        label_frame.pack(side=tk.LEFT, fill=tk.Y)
        label_frame.pack_propagate(False)

        track_label = tk.Label(
            label_frame,
            text=label_text,
            bg=COLORS.bg_secondary,
            fg=COLORS.fg_primary,
            font=("Arial", 9),
            anchor=tk.W,
            padx=5
        )
        track_label.pack(fill=tk.BOTH, expand=True)

        # Middle: Waveform canvas
        if is_stereo:
            # Stereo: Create 2 canvases stacked vertically (L on top, R on bottom)
            canvas_container = tk.Frame(row_frame, bg=COLORS.bg_primary)
            canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

            # L channel (top)
            canvas_l = tk.Canvas(
                canvas_container,
                bg=COLORS.bg_primary,
                height=height // 2,
                highlightthickness=1,
                highlightbackground=COLORS.border
            )
            canvas_l.pack(fill=tk.BOTH, expand=True, pady=(0, 1))
            canvas_l.bind("<Button-1>", lambda e: self._on_canvas_click(e, canvas_l))

            # R channel (bottom)
            canvas_r = tk.Canvas(
                canvas_container,
                bg=COLORS.bg_primary,
                height=height // 2,
                highlightthickness=1,
                highlightbackground=COLORS.border
            )
            canvas_r.pack(fill=tk.BOTH, expand=True)
            canvas_r.bind("<Button-1>", lambda e: self._on_canvas_click(e, canvas_r))

            # Store both canvases
            waveform_canvas = {"L": canvas_l, "R": canvas_r}
        else:
            # Mono: Single canvas
            waveform_canvas = tk.Canvas(
                row_frame,
                bg=COLORS.bg_primary,
                height=height,
                highlightthickness=1,
                highlightbackground=COLORS.border
            )
            waveform_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
            waveform_canvas.bind("<Button-1>", lambda e: self._on_canvas_click(e, waveform_canvas))

        # Right: Volume slider
        volume_frame = tk.Frame(row_frame, bg=COLORS.bg_secondary, width=self.VOLUME_SLIDER_WIDTH)
        volume_frame.pack(side=tk.RIGHT, fill=tk.Y)
        volume_frame.pack_propagate(False)

        # Volume variable (0-100)
        volume_var = tk.IntVar(value=100)
        self.volume_vars[track_id] = volume_var

        # Volume icon
        tk.Label(
            volume_frame,
            text="🔊",
            bg=COLORS.bg_secondary,
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=2)

        # Volume slider
        volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=volume_var,
            command=lambda v: self._on_volume_change(track_id, v)
        )
        volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Store widgets
        self.track_widgets[track_id] = {
            "canvas": waveform_canvas,
            "volume": volume_slider,
            "label": track_label,
            "config": track_config
        }

    def _on_canvas_click(self, event, canvas):
        """Handle click on waveform canvas to seek"""
        if not self.on_seek_callback:
            return

        # Calculate time position from click x coordinate
        # This will be implemented when we have duration info
        # For now, just pass 0
        canvas_width = canvas.winfo_width()
        if canvas_width > 0:
            click_ratio = event.x / canvas_width
            # We'll need duration from video player - for now just pass the ratio
            # The callback will handle converting to actual time
            self.on_seek_callback(click_ratio)

    def _on_volume_change(self, track_id, value):
        """Handle volume slider change"""
        # Volume changes are preview-only (don't affect export)
        # This will be wired to audio playback in Phase 4
        pass

    def get_canvas(self, track_id):
        """
        Get canvas(es) for a track

        Args:
            track_id: Track identifier (e.g., "music_lr", "sfx_1")

        Returns:
            Canvas widget (mono) or dict {"L": canvas, "R": canvas} (stereo)
        """
        if track_id not in self.track_widgets:
            return None
        return self.track_widgets[track_id]["canvas"]

    def get_volume(self, track_id):
        """Get current volume for a track (0-100)"""
        if track_id not in self.volume_vars:
            return 100
        return self.volume_vars[track_id].get()

    def set_volume(self, track_id, volume):
        """Set volume for a track (0-100)"""
        if track_id in self.volume_vars:
            self.volume_vars[track_id].set(volume)

    def clear_waveform(self, track_id):
        """Clear waveform on a track"""
        if track_id not in self.track_widgets:
            return

        canvas = self.track_widgets[track_id]["canvas"]
        if isinstance(canvas, dict):
            # Stereo: clear both L and R
            canvas["L"].delete("all")
            canvas["R"].delete("all")
        else:
            # Mono: clear single canvas
            canvas.delete("all")

    def clear_all_waveforms(self):
        """Clear all track waveforms"""
        for track_id in self.track_widgets.keys():
            self.clear_waveform(track_id)

    def draw_waveform(self, track_id, waveform_data, channel="mono"):
        """
        Draw waveform on a track

        Args:
            track_id: Track identifier
            waveform_data: List of amplitude values (normalized -1 to 1)
            channel: "mono", "L", or "R" (for stereo tracks)
        """
        if track_id not in self.track_widgets:
            return

        canvas_widget = self.track_widgets[track_id]["canvas"]

        # Get appropriate canvas
        if isinstance(canvas_widget, dict):
            # Stereo track
            if channel not in ["L", "R"]:
                return
            canvas = canvas_widget[channel]
        else:
            # Mono track
            canvas = canvas_widget

        # Clear existing waveform
        canvas.delete("waveform")

        if not waveform_data or len(waveform_data) == 0:
            return

        # Get canvas dimensions
        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 0 or height <= 0:
            return

        # Draw waveform
        mid_y = height / 2
        points = []

        for i, amplitude in enumerate(waveform_data):
            x = (i / len(waveform_data)) * width
            y = mid_y - (amplitude * (height / 2) * 0.8)  # 80% of half-height
            points.extend([x, y])

        if len(points) >= 4:  # Need at least 2 points
            # Get track color
            color = self.track_widgets[track_id]["config"]["color"]
            canvas.create_line(points, fill=color, width=1, tags="waveform")

    def draw_marker_indicators(self, track_id, markers, duration_ms):
        """
        Draw vertical marker indicators on a track

        Args:
            track_id: Track identifier
            markers: List of markers on this track
            duration_ms: Total duration for position calculation
        """
        if track_id not in self.track_widgets:
            return

        canvas_widget = self.track_widgets[track_id]["canvas"]
        color = self.track_widgets[track_id]["config"]["color"]

        # Get canvas(es)
        canvases = []
        if isinstance(canvas_widget, dict):
            # Stereo: draw on both L and R
            canvases = [canvas_widget["L"], canvas_widget["R"]]
        else:
            # Mono: single canvas
            canvases = [canvas_widget]

        for canvas in canvases:
            canvas.update_idletasks()
            width = canvas.winfo_width()
            height = canvas.winfo_height()

            if width <= 0 or duration_ms <= 0:
                continue

            # Draw vertical line for each marker
            for marker in markers:
                x_pos = (marker.time_ms / duration_ms) * width

                # Draw vertical line
                canvas.create_line(
                    x_pos, 0,
                    x_pos, height,
                    fill=color,
                    width=2,
                    tags="marker_indicator"
                )

    def clear_marker_indicators(self, track_id):
        """Clear marker indicators from a track"""
        if track_id not in self.track_widgets:
            return

        canvas_widget = self.track_widgets[track_id]["canvas"]

        # Get canvas(es)
        canvases = []
        if isinstance(canvas_widget, dict):
            canvases = [canvas_widget["L"], canvas_widget["R"]]
        else:
            canvases = [canvas_widget]

        for canvas in canvases:
            canvas.delete("marker_indicator")

    def destroy(self):
        """Clean up resources"""
        self.container.destroy()
