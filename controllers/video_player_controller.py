#!/usr/bin/env python3
"""
Video Player Controller - Manages video playback and frame display
Extracted from audio_mapper.py for better modularity
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk


class VideoPlayerController:
    """
    Manages video playback, frame display, and timeline control.

    Handles:
    - Video file loading (OpenCV)
    - Playback state (play/pause, seeking)
    - Frame rendering on canvas
    - Timeline updates and timestamp display
    """

    def __init__(
        self,
        video_canvas,
        play_button,
        timeline_slider,
        timestamp_label,
        fps_label,
        on_update_filmstrip=None,
        on_update_waveform=None,
        on_timeline_slider_update=None,
        on_template_prompt=None
    ):
        """
        Initialize video player controller.

        Args:
            video_canvas: tk.Canvas for video display
            play_button: tk.Button for play/pause control
            timeline_slider: tk.Scale for timeline scrubbing
            timestamp_label: tk.Label for timestamp display
            fps_label: tk.Label for FPS display
            on_update_filmstrip: Optional callback(time_ms) to update filmstrip position
            on_update_waveform: Optional callback(time_ms) to update waveform position
            on_timeline_slider_update: Optional callback(time_ms) to update slider position
            on_template_prompt: Optional callback() to prompt for template info after loading
        """
        # UI components
        self.video_canvas = video_canvas
        self.play_button = play_button
        self.timeline_slider = timeline_slider
        self.timestamp_label = timestamp_label
        self.fps_label = fps_label

        # Callbacks
        self.on_update_filmstrip = on_update_filmstrip
        self.on_update_waveform = on_update_waveform
        self.on_timeline_slider_update = on_timeline_slider_update
        self.on_template_prompt = on_template_prompt

        # Video capture and state
        self.video_capture = None
        self.current_frame = None
        self.photo_image = None

        # Playback state
        self.current_time_ms = 0
        self.duration_ms = 0
        self.fps = 30  # Default FPS
        self.total_frames = 0
        self.is_playing = False
        self.video_loaded = False

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
            return None

        # Release previous video if any
        if self.video_capture:
            self.video_capture.release()

        # Open video with OpenCV
        self.video_capture = cv2.VideoCapture(filepath)

        if not self.video_capture.isOpened():
            messagebox.showerror("Error", "Could not open video file")
            return None

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

        # Prompt for template info if callback provided
        if self.on_template_prompt:
            self.on_template_prompt()

        print(f"✓ Video loaded: {self.total_frames} frames, {self.fps:.2f} FPS, {self.duration_ms}ms duration")

        return filepath

    def create_blank_timeline(self, duration_seconds):
        """
        Create blank timeline without video.

        Args:
            duration_seconds: Duration in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            seconds = float(duration_seconds)
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

            # Prompt for template info if callback provided
            if self.on_template_prompt:
                self.on_template_prompt()

            return True
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number")
            return False

    def seek_to_time(self, time_ms):
        """
        Seek to specific time in milliseconds.

        Args:
            time_ms: Time in milliseconds
        """
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
        """
        Step forward/backward by delta_ms milliseconds.

        Args:
            delta_ms: Time delta in milliseconds (can be negative)
        """
        if not self.video_loaded:
            return

        new_time = self.current_time_ms + delta_ms
        self.seek_to_time(new_time)

        # Update slider if callback provided
        if self.on_timeline_slider_update:
            self.on_timeline_slider_update(self.current_time_ms)

    def step_frame(self, delta_frames):
        """
        Step forward/backward by exact number of frames.

        Args:
            delta_frames: Number of frames to step (can be negative)
        """
        if not self.video_loaded or not self.video_capture:
            return

        # Calculate time per frame in milliseconds
        frame_duration_ms = 1000 / self.fps if self.fps > 0 else 33

        # Step by the specified number of frames
        delta_ms = int(delta_frames * frame_duration_ms)
        new_time = self.current_time_ms + delta_ms
        self.seek_to_time(new_time)

        # Update slider if callback provided
        if self.on_timeline_slider_update:
            self.on_timeline_slider_update(self.current_time_ms)

    def on_timeline_change(self, value):
        """
        Handle timeline slider change.

        Args:
            value: New slider value (time in ms)
        """
        if not self.video_loaded:
            return

        new_time_ms = int(float(value))
        self.seek_to_time(new_time_ms)

    def update_timeline(self):
        """
        Update timeline position and display.

        Should be called repeatedly (e.g., every 33ms for 30 FPS).

        Returns:
            True if still playing, False if stopped
        """
        if self.video_loaded and self.is_playing:
            # Advance time based on FPS
            frame_duration_ms = 1000 / self.fps if self.fps > 0 else 33  # Default ~30fps
            self.current_time_ms += int(frame_duration_ms)

            if self.current_time_ms >= self.duration_ms:
                self.current_time_ms = self.duration_ms
                self.is_playing = False
                self.play_button.config(text="▶ Play")

            # Update slider if callback provided
            if self.on_timeline_slider_update:
                self.on_timeline_slider_update(self.current_time_ms)

            # Seek to current position and display frame
            if self.video_capture:
                frame_number = int((self.current_time_ms / 1000) * self.fps)
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                self.display_current_frame()

        # Update timestamp
        self.update_timestamp_display()

        # Update film strip position indicator if callback provided
        if self.on_update_filmstrip:
            self.on_update_filmstrip(self.current_time_ms)

        # Update waveform position indicator if callback provided
        if self.on_update_waveform:
            self.on_update_waveform(self.current_time_ms)

        return self.is_playing

    def update_timestamp_display(self):
        """Update timestamp label with current time"""
        ms = self.current_time_ms
        seconds = ms // 1000
        milliseconds = ms % 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60

        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        self.timestamp_label.config(text=timestamp)

    def get_current_time(self):
        """Get current playback time in milliseconds"""
        return self.current_time_ms

    def get_duration(self):
        """Get total duration in milliseconds"""
        return self.duration_ms

    def get_fps(self):
        """Get current FPS"""
        return self.fps

    def is_video_loaded(self):
        """Check if video is loaded"""
        return self.video_loaded

    def is_currently_playing(self):
        """Check if currently playing"""
        return self.is_playing

    def cleanup(self):
        """Release video resources"""
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
