#!/usr/bin/env python3
"""
Filmstrip Manager - Video Thumbnail Visualization Component
Handles filmstrip extraction, display, and interaction
"""

import tkinter as tk
import cv2
from PIL import Image, ImageTk
from typing import Optional, Callable, List


class FilmstripManager:
    """
    Manages filmstrip thumbnail visualization and interactions

    Handles:
    - Extracting thumbnail frames from video at regular intervals
    - Drawing thumbnails on canvas timeline
    - Position indicator updates
    - Click-to-seek interaction
    """

    def __init__(self,
                 canvas: tk.Canvas,
                 canvas_height: int = 60,
                 thumb_width: int = 80,
                 thumb_height: int = 45,
                 on_seek: Optional[Callable[[int], None]] = None,
                 on_deselect_marker: Optional[Callable[[], None]] = None):
        """
        Initialize filmstrip manager

        Args:
            canvas: Tkinter canvas widget for drawing filmstrip
            canvas_height: Height of the filmstrip canvas in pixels
            thumb_width: Width of each thumbnail in pixels
            thumb_height: Height of each thumbnail in pixels
            on_seek: Callback function when user clicks to seek (receives time_ms)
            on_deselect_marker: Callback function to deselect markers
        """
        self.canvas = canvas
        self.canvas_height = canvas_height
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

        # Filmstrip data
        self.frames: List[ImageTk.PhotoImage] = []
        self.frame_times: List[int] = []
        self.duration_ms: int = 0

        # Callbacks
        self.on_seek = on_seek
        self.on_deselect_marker = on_deselect_marker

        # Bind events
        self.canvas.bind("<Button-1>", self._handle_click)
        self.canvas.bind("<Configure>", self._handle_resize)

        # Show placeholder
        self._show_placeholder("Film strip will appear here")

    def _show_placeholder(self, text: str, color: str = "#666"):
        """Show placeholder text on canvas"""
        self.canvas.delete("filmstrip_placeholder")
        self.canvas.create_text(
            600, 30,
            text=text,
            fill=color,
            font=("Arial", 10),
            tags="filmstrip_placeholder"
        )

    def extract_frames(self, video_capture, duration_ms: int, fps: float, num_thumbs: int = 15):
        """
        Extract thumbnail frames at regular intervals for film strip

        Args:
            video_capture: OpenCV VideoCapture object
            duration_ms: Total duration in milliseconds
            fps: Frames per second of video
            num_thumbs: Number of thumbnails to extract

        Returns:
            True if successful, False otherwise
        """
        if not video_capture or duration_ms == 0:
            return False

        print(f"⏳ Extracting {num_thumbs} thumbnail frames for film strip...")

        try:
            # Clear previous frames
            self.frames.clear()
            self.frame_times.clear()
            self.duration_ms = duration_ms

            # Calculate time intervals
            interval_ms = duration_ms / (num_thumbs - 1) if num_thumbs > 1 else 0

            for i in range(num_thumbs):
                time_ms = int(i * interval_ms)
                if time_ms > duration_ms:
                    time_ms = duration_ms

                # Seek to this time
                frame_number = int((time_ms / 1000) * fps)
                video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

                # Read frame
                ret, frame = video_capture.read()
                if not ret:
                    continue

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Resize to thumbnail size
                frame_resized = cv2.resize(
                    frame_rgb,
                    (self.thumb_width, self.thumb_height),
                    interpolation=cv2.INTER_AREA
                )

                # Convert to PIL Image then PhotoImage
                pil_image = Image.fromarray(frame_resized)
                photo_image = ImageTk.PhotoImage(pil_image)

                # Store frame and time
                self.frames.append(photo_image)
                self.frame_times.append(time_ms)

            # Reset video to beginning
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

            print(f"✓ Extracted {len(self.frames)} thumbnail frames")
            return True

        except Exception as e:
            print(f"⚠ Could not extract filmstrip: {e}")
            self._show_placeholder("Could not extract video thumbnails", "#888")
            return False

    def draw(self):
        """Draw film strip thumbnails on canvas"""
        if not self.frames or self.duration_ms == 0:
            return

        # Clear canvas
        self.canvas.delete("all")

        # Get canvas width
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200  # Default width

        # Draw each thumbnail positioned by its actual time
        for photo, time_ms in zip(self.frames, self.frame_times):
            # Calculate x position based on time (proportional to duration)
            x_pos = int((time_ms / self.duration_ms) * canvas_width)
            y_pos = self.canvas_height // 2

            # Draw thumbnail
            self.canvas.create_image(
                x_pos, y_pos,
                image=photo,
                anchor=tk.CENTER,
                tags="thumbnail"
            )

            # Draw frame border
            half_width = self.thumb_width // 2
            half_height = self.thumb_height // 2
            self.canvas.create_rectangle(
                x_pos - half_width, y_pos - half_height,
                x_pos + half_width, y_pos + half_height,
                outline="#444",
                width=1,
                tags="thumbnail_border"
            )

    def update_position(self, current_time_ms: int):
        """
        Update position indicator on film strip

        Args:
            current_time_ms: Current playback position in milliseconds
        """
        if not self.frames or self.duration_ms == 0:
            return

        # Remove old position indicator
        self.canvas.delete("position")

        # Calculate position
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200

        x_pos = int((current_time_ms / self.duration_ms) * canvas_width)

        # Draw position indicator
        self.canvas.create_line(
            x_pos, 0,
            x_pos, self.canvas_height,
            fill="#FF6B00",
            width=2,
            tags="position"
        )

    def _handle_click(self, event):
        """Handle click on film strip for scrubbing"""
        if self.duration_ms == 0 or not self.on_seek:
            return

        # Check if we clicked on a marker (markers have tags)
        items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        clicked_on_marker = False
        for item in items:
            tags = self.canvas.gettags(item)
            if "marker" in tags:
                clicked_on_marker = True
                break

        # If didn't click on a marker, deselect and scrub timeline
        if not clicked_on_marker:
            if self.on_deselect_marker:
                self.on_deselect_marker()

            # Get canvas width
            canvas_width = self.canvas.winfo_width()
            if canvas_width <= 1:
                return

            # Calculate time from click position
            x_pos = event.x
            time_ms = int((x_pos / canvas_width) * self.duration_ms)

            # Call seek callback
            self.on_seek(time_ms)

    def _handle_resize(self, event):
        """Handle filmstrip canvas resize - redraw filmstrip"""
        if self.frames:
            self.draw()

    def clear(self):
        """Clear filmstrip data and canvas"""
        self.frames.clear()
        self.frame_times.clear()
        self.duration_ms = 0
        self.canvas.delete("all")
        self._show_placeholder("Film strip will appear here")

    def has_data(self) -> bool:
        """Check if filmstrip data exists"""
        return len(self.frames) > 0

    def get_frame_count(self) -> int:
        """Get number of thumbnail frames"""
        return len(self.frames)
