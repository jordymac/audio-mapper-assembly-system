"""
Audio Player - Simple audio playback for generated marker files

Uses pygame.mixer for reliable cross-platform playback of generated audio files.
"""

import pygame
import os
from pathlib import Path


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
