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

        # Track widgets: {track_id: {"canvas": Canvas, "config": dict}}
        self.track_widgets = {}

        # Build tracks
        self._create_tracks()

    def _create_tracks(self):
        """Create all track rows"""
        for track_config in self.TRACK_CONFIG:
            track_id = track_config["id"]
            self._create_track_row(track_config)

    def _create_track_row(self, track_config):
        """Create a single track row with waveform canvas only"""
        track_id = track_config["id"]
        height = track_config["height"]
        color = track_config["color"]

        # Row frame
        row_frame = tk.Frame(self.container, bg=COLORS.bg_secondary, height=height)
        row_frame.pack(fill=tk.X, pady=1)
        row_frame.pack_propagate(False)

        # Waveform canvas (full width, no label or volume controls)
        waveform_canvas = tk.Canvas(
            row_frame,
            bg=COLORS.bg_primary,
            height=height,
            highlightthickness=1,
            highlightbackground=COLORS.border
        )
        waveform_canvas.pack(fill=tk.BOTH, expand=True)
        waveform_canvas.bind("<Button-1>", lambda e: self._on_canvas_click(e, waveform_canvas))

        # Store widgets
        self.track_widgets[track_id] = {
            "canvas": waveform_canvas,
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

    def get_canvas(self, track_id):
        """
        Get canvas for a track

        Args:
            track_id: Track identifier (e.g., "music_lr", "sfx_1")

        Returns:
            Canvas widget
        """
        if track_id not in self.track_widgets:
            return None
        return self.track_widgets[track_id]["canvas"]

    def clear_waveform(self, track_id):
        """Clear waveform on a track"""
        if track_id not in self.track_widgets:
            return

        canvas = self.track_widgets[track_id]["canvas"]
        canvas.delete("waveform")

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
            channel: "mono" or "stereo" (stereo data should be pre-averaged)
        """
        if track_id not in self.track_widgets:
            print(f"Warning: track_id '{track_id}' not found in track_widgets")
            return

        canvas = self.track_widgets[track_id]["canvas"]

        # Clear existing waveform
        canvas.delete("waveform")

        if not waveform_data or len(waveform_data) == 0:
            print(f"Warning: No waveform data for track {track_id}")
            return

        # Get canvas dimensions
        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 0 or height <= 0:
            print(f"Warning: Invalid canvas dimensions for track {track_id}: {width}x{height}")
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
            print(f"✓ Drew waveform for track {track_id}: {len(waveform_data)} samples, canvas {width}x{height}")
        else:
            print(f"Warning: Not enough points to draw waveform for track {track_id}: {len(points)} points")

    def draw_marker_indicators(self, track_id, markers, duration_ms):
        """
        Draw vertical marker indicators on a track

        Args:
            track_id: Track identifier
            markers: List of markers on this track
            duration_ms: Total duration for position calculation
        """
        if track_id not in self.track_widgets:
            print(f"Warning: track_id '{track_id}' not found when drawing marker indicators")
            return

        canvas = self.track_widgets[track_id]["canvas"]
        color = self.track_widgets[track_id]["config"]["color"]

        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 0 or duration_ms <= 0:
            print(f"Warning: Invalid dimensions for marker indicators on track {track_id}: width={width}, duration={duration_ms}")
            return

        # Draw vertical line for each marker
        marker_count = 0
        for marker in markers:
            # Handle both dict and object markers
            time_ms = marker.get('time_ms', 0) if isinstance(marker, dict) else marker.time_ms
            x_pos = (time_ms / duration_ms) * width

            # Draw vertical line
            canvas.create_line(
                x_pos, 0,
                x_pos, height,
                fill=color,
                width=2,
                tags="marker_indicator"
            )
            marker_count += 1

        print(f"✓ Drew {marker_count} marker indicators on track {track_id}")

    def clear_marker_indicators(self, track_id):
        """Clear marker indicators from a track"""
        if track_id not in self.track_widgets:
            return

        canvas = self.track_widgets[track_id]["canvas"]
        deleted_count = len(canvas.find_withtag("marker_indicator"))
        canvas.delete("marker_indicator")
        print(f"✓ Cleared {deleted_count} marker indicators from track {track_id}")

    def draw_playhead(self, position_ratio):
        """
        Draw playhead position indicator on all tracks

        Args:
            position_ratio: Current position (0.0 to 1.0)
        """
        for track_id, widgets in self.track_widgets.items():
            canvas = widgets["canvas"]

            # Delete old playhead
            canvas.delete("playhead")

            # Get canvas width
            canvas_width = canvas.winfo_width()
            if canvas_width <= 1:
                canvas_width = 1200  # Default width

            # Calculate x position
            x_pos = int(position_ratio * canvas_width)

            # Draw playhead line (red, thin, prominent)
            canvas.create_line(
                x_pos, 0,
                x_pos, canvas.winfo_height(),
                fill="#FF0000",
                width=2,
                tags="playhead"
            )

    def destroy(self):
        """Clean up resources"""
        self.container.destroy()
