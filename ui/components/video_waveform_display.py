"""
Video Waveform Display Component
Displays the original video audio waveform (separate from generated tracks)
"""

import tkinter as tk
from config.color_scheme import COLORS


class VideoWaveformDisplay:
    """
    Video audio waveform visualization
    Shows the original audio from the loaded video file
    """

    def __init__(self, parent, on_seek_callback=None):
        """
        Initialize video waveform display

        Args:
            parent: Parent Tkinter widget
            on_seek_callback: Callback when user clicks waveform to seek (ratio 0-1)
        """
        self.parent = parent
        self.on_seek_callback = on_seek_callback

        # Container frame
        self.container = tk.Frame(parent, bg=COLORS.bg_secondary)
        self.container.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Waveform canvas (full width, no label)
        self.canvas = tk.Canvas(
            self.container,
            bg=COLORS.bg_primary,
            height=80,
            highlightthickness=1,
            highlightbackground=COLORS.border
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def _on_canvas_click(self, event):
        """Handle click on waveform canvas to seek"""
        if not self.on_seek_callback:
            return

        canvas_width = self.canvas.winfo_width()
        if canvas_width > 0:
            click_ratio = event.x / canvas_width
            self.on_seek_callback(click_ratio)

    def clear_waveform(self):
        """Clear waveform display"""
        self.canvas.delete("all")

    def draw_waveform(self, waveform_data):
        """
        Draw waveform on canvas

        Args:
            waveform_data: List of amplitude values (normalized -1 to 1)
        """
        # Clear existing waveform
        self.canvas.delete("waveform")

        if not waveform_data or len(waveform_data) == 0:
            return

        # Get canvas dimensions
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

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
            # Use accent color for video audio waveform
            self.canvas.create_line(points, fill=COLORS.accent, width=1, tags="waveform")

    def draw_playhead(self, position_ratio):
        """
        Draw playhead indicator at position

        Args:
            position_ratio: Position as ratio 0-1
        """
        self.canvas.delete("playhead")

        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 0:
            return

        x_pos = position_ratio * width
        self.canvas.create_line(
            x_pos, 0,
            x_pos, height,
            fill=COLORS.accent,
            width=2,
            tags="playhead"
        )

    def destroy(self):
        """Clean up resources"""
        self.container.destroy()
