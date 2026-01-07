"""
Assembly Playback Service - Marker-Triggered Audio Playback
Triggers individual marker audio clips as playhead crosses marker positions
"""

import pygame
import os
import time
from pathlib import Path
from typing import Optional, List, Set


class AssemblyPlaybackService:
    """
    Service for marker-triggered audio playback

    New Approach:
    - Triggers individual marker sounds as playhead crosses marker positions
    - No continuous assembled audio during playback
    - Assembly only happens on export (which already works)

    Responsibilities:
    - Track marker positions
    - Detect playhead crossing markers
    - Trigger appropriate marker audio clips
    - Handle simultaneous marker playback
    """

    def __init__(self, video_player):
        """
        Initialize marker-triggered playback service

        Args:
            video_player: VideoPlayerController instance for timeline position
        """
        self.video_player = video_player
        self.is_playing = False

        # Marker tracking
        self.markers: List = []  # List of all markers
        self.last_playhead_position_ms = 0  # Last known playhead position
        self.triggered_markers: Set[int] = set()  # Marker indices that have been triggered

        # Audio cache: marker_index -> pygame.Sound
        self.marker_sounds: dict = {}

        # Debug
        self.debug_logging = False

        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            # Use more channels for simultaneous marker playback
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)  # Support up to 16 simultaneous sounds

    def set_markers(self, markers: List):
        """
        Set the list of markers for triggering

        Args:
            markers: List of marker objects or dicts
        """
        self.markers = markers
        self.marker_sounds.clear()  # Clear cached sounds
        self.triggered_markers.clear()  # Clear trigger history

        if self.debug_logging:
            print(f"🎵 [TRIGGER] Loaded {len(markers)} markers for triggering")

    def preload_marker_sounds(self):
        """
        Preload all marker audio files into memory for instant playback
        """
        loaded_count = 0
        for i, marker in enumerate(self.markers):
            # Get marker audio file path
            audio_path = self._get_marker_audio_path(marker)
            if not audio_path or not os.path.exists(audio_path):
                continue

            try:
                # Load as pygame.Sound (not music - allows simultaneous playback)
                sound = pygame.mixer.Sound(audio_path)
                self.marker_sounds[i] = sound
                loaded_count += 1
            except Exception as e:
                print(f"⚠️  Could not preload marker {i}: {e}")

        if self.debug_logging:
            print(f"✓ Preloaded {loaded_count}/{len(self.markers)} marker sounds")

    def _get_marker_audio_path(self, marker) -> Optional[str]:
        """
        Get the audio file path for a marker

        Args:
            marker: Marker object or dict

        Returns:
            Path to audio file or None
        """
        # Handle both dict and object markers
        if isinstance(marker, dict):
            versions = marker.get('versions', [])
            current_version = marker.get('current_version', 1)
            current_version_data = next((v for v in versions if v.get('version') == current_version), None)

            if not current_version_data:
                return None

            asset_file = current_version_data.get('asset_file', '')
            marker_type = marker.get('type', 'unknown')
        else:
            asset_file = marker.asset_file
            marker_type = marker.type

        if not asset_file:
            return None

        # Try multiple possible paths
        possible_paths = [
            os.path.join("generated_audio", marker_type, asset_file),
            os.path.join("generated_audio", asset_file),
            asset_file
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def start_playback(self):
        """
        Start marker triggering (called when user presses play)
        """
        self.is_playing = True
        self.last_playhead_position_ms = self.video_player.current_time_ms
        self.triggered_markers.clear()  # Reset trigger history

        if self.debug_logging:
            print(f"▶ [TRIGGER] Playback started at {self.last_playhead_position_ms}ms")

    def stop_playback(self):
        """
        Stop marker triggering and all playing sounds
        """
        self.is_playing = False
        pygame.mixer.stop()  # Stop all channels

        if self.debug_logging:
            print("⏹ [TRIGGER] Playback stopped, all sounds stopped")

    def update_playhead(self, current_time_ms: int):
        """
        Update playhead position and trigger markers if crossed

        Args:
            current_time_ms: Current playhead position in milliseconds
        """
        if not self.is_playing:
            return

        # Detect direction of playback
        is_forward = current_time_ms >= self.last_playhead_position_ms

        # Check each marker to see if playhead crossed it
        for i, marker in enumerate(self.markers):
            marker_time_ms = marker.get('time_ms', 0) if isinstance(marker, dict) else marker.time_ms

            # Check if we crossed this marker
            if is_forward:
                # Forward playback: crossed if we went from before to at-or-after
                crossed = (self.last_playhead_position_ms < marker_time_ms <= current_time_ms)
            else:
                # Backward (scrubbing back): crossed if we went from after to before
                crossed = (current_time_ms < marker_time_ms <= self.last_playhead_position_ms)

            if crossed:
                self._trigger_marker(i, marker)

        # Update last position
        self.last_playhead_position_ms = current_time_ms

    def _trigger_marker(self, marker_index: int, marker):
        """
        Trigger (play) a marker's audio

        Args:
            marker_index: Index of marker in markers list
            marker: Marker object or dict
        """
        # Check if sound is preloaded
        if marker_index not in self.marker_sounds:
            # Try to load on-the-fly
            audio_path = self._get_marker_audio_path(marker)
            if audio_path and os.path.exists(audio_path):
                try:
                    self.marker_sounds[marker_index] = pygame.mixer.Sound(audio_path)
                except Exception as e:
                    if self.debug_logging:
                        print(f"⚠️  Could not load marker {marker_index}: {e}")
                    return
            else:
                return

        # Play the sound
        try:
            sound = self.marker_sounds[marker_index]
            sound.play()

            if self.debug_logging:
                marker_name = marker.get('name', f'Marker {marker_index}') if isinstance(marker, dict) else marker.name
                print(f"🔊 [TRIGGER] Played: {marker_name}")

        except Exception as e:
            if self.debug_logging:
                print(f"⚠️  Error playing marker {marker_index}: {e}")

    def set_debug_logging(self, enabled: bool):
        """
        Enable or disable debug logging

        Args:
            enabled: True to enable debug logs, False to disable
        """
        self.debug_logging = enabled
        if enabled:
            print("🔍 [TRIGGER] Debug logging enabled")
        else:
            print("🔇 [TRIGGER] Debug logging disabled")

    def clear_cache(self):
        """Clear all preloaded marker sounds from memory"""
        self.marker_sounds.clear()
        pygame.mixer.stop()

        if self.debug_logging:
            print("🧹 [TRIGGER] Sound cache cleared")
