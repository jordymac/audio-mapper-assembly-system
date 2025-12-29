#!/usr/bin/env python3
"""
Waveform Manager - Audio Waveform Visualization Component
Handles waveform extraction, display, and interaction
"""

import tkinter as tk
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from typing import Optional, Callable, Tuple
from config.color_scheme import COLORS


class WaveformManager:
    """
    Manages audio waveform visualization and interactions

    Handles:
    - Extracting audio from video files
    - Calculating waveform data (RMS downsampling)
    - Drawing waveform on canvas
    - Position indicator updates
    - Click-to-seek interaction
    """

    def __init__(self,
                 canvas: tk.Canvas,
                 canvas_height: int = 80,
                 on_seek: Optional[Callable[[int], None]] = None,
                 on_deselect_marker: Optional[Callable[[], None]] = None):
        """
        Initialize waveform manager

        Args:
            canvas: Tkinter canvas widget for drawing waveform
            canvas_height: Height of the waveform canvas in pixels
            on_seek: Callback function when user clicks to seek (receives time_ms)
            on_deselect_marker: Callback function to deselect markers
        """
        self.canvas = canvas
        self.canvas_height = canvas_height
        self.waveform_data: Optional[list[float]] = None
        self.duration_ms: int = 0

        # Callbacks
        self.on_seek = on_seek
        self.on_deselect_marker = on_deselect_marker

        # Bind events
        self.canvas.bind("<Button-1>", self._handle_click)
        self.canvas.bind("<Configure>", self._handle_resize)

        # Show placeholder
        self._show_placeholder("Audio waveform will appear here")

    def _show_placeholder(self, text: str, color: str = None):
        """Show placeholder text on canvas"""
        if color is None:
            color = COLORS.placeholder_text
        self.canvas.delete("waveform_placeholder")
        self.canvas.create_text(
            600, 40,
            text=text,
            fill=color,
            font=("Arial", 10),
            tags="waveform_placeholder"
        )

    def extract_and_display(self, video_filepath: str) -> bool:
        """
        Extract audio from video and display waveform

        Args:
            video_filepath: Path to video file

        Returns:
            True if successful, False otherwise
        """
        try:
            print("⏳ Extracting audio for waveform...")

            # Load video with moviepy
            video = VideoFileClip(video_filepath)

            if video.audio is None:
                print("⚠ No audio track found in video")
                self._show_placeholder("No audio track in video", COLORS.disabled_text)
                video.close()
                return False

            # Get audio as numpy array
            audio_array = video.audio.to_soundarray(fps=22050)  # Downsample for performance

            # Get duration in milliseconds
            self.duration_ms = int(video.duration * 1000)

            video.close()

            # If stereo, convert to mono by averaging channels
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)

            # Calculate waveform data (downsample for display)
            self._calculate_waveform_data(audio_array)

            # Draw waveform
            self.draw()

            print("✓ Waveform extracted and displayed")
            return True

        except Exception as e:
            print(f"⚠ Could not extract waveform: {e}")
            self._show_placeholder("Could not extract audio waveform", COLORS.disabled_text)
            return False

    @staticmethod
    def extract_waveform_from_audio(audio_filepath: str, target_width: int = 150) -> Tuple[Optional[list[float]], int]:
        """
        Extract waveform data from an audio file (MP3, WAV, etc.)

        Static method for use by MarkerRow and MusicEditor components.

        Args:
            audio_filepath: Path to audio file (MP3, WAV, etc.)
            target_width: Number of pixels/samples in waveform (default: 150 for mini-waveforms)

        Returns:
            Tuple of (waveform_data, duration_ms):
            - waveform_data: List of normalized amplitudes (0-1), or None if extraction failed
            - duration_ms: Duration in milliseconds, or 0 if extraction failed
        """
        try:
            # Load audio file with moviepy
            audio_clip = AudioFileClip(audio_filepath)

            # Get audio as numpy array (downsample to 22050 Hz for performance)
            audio_array = audio_clip.to_soundarray(fps=22050)

            # Get duration in milliseconds
            duration_ms = int(audio_clip.duration * 1000)

            audio_clip.close()

            # If stereo, convert to mono by averaging channels
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)

            # Calculate waveform data (same logic as _calculate_waveform_data)
            total_samples = len(audio_array)
            samples_per_pixel = max(1, total_samples // target_width)

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
                    waveform.append(0)

            # Normalize to 0-1 range
            max_val = max(waveform) if waveform else 1
            if max_val > 0:
                waveform = [w / max_val for w in waveform]

            return waveform, duration_ms

        except Exception as e:
            print(f"⚠ Could not extract waveform from audio: {e}")
            return None, 0

    def _calculate_waveform_data(self, audio_array: np.ndarray, target_width: int = 1200):
        """
        Calculate downsampled waveform data for display using RMS

        Args:
            audio_array: Raw audio samples
            target_width: Number of pixels/samples in waveform (default: 1200)
        """
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

    def draw(self):
        """Draw waveform on canvas"""
        if not self.waveform_data:
            return

        # Clear canvas
        self.canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 1200  # Default width

        mid_y = self.canvas_height // 2

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
            height = int(amplitude * (self.canvas_height / 2) * 0.9)

            # Draw vertical line for this sample (use width=2 for better visibility)
            self.canvas.create_line(
                x, mid_y - height,
                x, mid_y + height,
                fill=COLORS.waveform_color,
                width=2,
                tags="waveform"
            )

        # Draw center line
        self.canvas.create_line(
            0, mid_y,
            canvas_width, mid_y,
            fill=COLORS.centerline,
            width=1,
            tags="centerline"
        )

    def update_position(self, current_time_ms: int):
        """
        Update position indicator on waveform

        Args:
            current_time_ms: Current playback position in milliseconds
        """
        if not self.waveform_data or self.duration_ms == 0:
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
            fill=COLORS.position_indicator,
            width=2,
            tags="position"
        )

    def _handle_click(self, event):
        """Handle click on waveform for scrubbing"""
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
        """Handle waveform canvas resize - redraw waveform"""
        if self.waveform_data:
            self.draw()

    def clear(self):
        """Clear waveform data and canvas"""
        self.waveform_data = None
        self.duration_ms = 0
        self.canvas.delete("all")
        self._show_placeholder("Audio waveform will appear here")

    def has_data(self) -> bool:
        """Check if waveform data exists"""
        return self.waveform_data is not None

    def get_data(self) -> Optional[list[float]]:
        """Get raw waveform data"""
        return self.waveform_data
