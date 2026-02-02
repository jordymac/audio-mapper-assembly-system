"""
Assembly Playback Service - Marker-Triggered Audio Playback
Triggers individual marker audio clips as playhead crosses marker positions
"""

import pygame
import os
import time
from pathlib import Path
from typing import Optional, List, Set, Callable
from core.marker_utils import get_marker_attr, get_current_version_data as get_version_data


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
    - MUSIC markers use pygame.mixer.music (single track, supports offset)
    - SFX/VOICE markers use pygame.Sound (multiple simultaneous channels)
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

        # Audio cache: marker_index -> pygame.Sound (for SFX/VOICE only)
        self.marker_sounds: dict = {}

        # Track current music marker (only one music stream at a time)
        self.current_music_marker: Optional[int] = None

        # Error callback for missing audio
        self.on_playback_error: Optional[Callable[[str, str], None]] = None

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
        Preload all marker audio files into memory for instant playback.
        Music markers are not preloaded (they use pygame.mixer.music).
        SFX/VOICE markers are preloaded as pygame.Sound for simultaneous playback.
        """
        loaded_count = 0
        missing_files = []

        for i, marker in enumerate(self.markers):
            marker_type = get_marker_attr(marker, 'type', 'sfx')
            marker_name = get_marker_attr(marker, 'name', f'Marker {i}')

            # Get marker audio file path
            audio_path = self._get_marker_audio_path(marker)

            if not audio_path or not os.path.exists(audio_path):
                # Track missing files for error reporting
                expected_file = self._get_expected_audio_filename(marker)
                if expected_file:
                    missing_files.append((marker_name, expected_file))
                continue

            # Music markers use pygame.mixer.music, not preloaded as Sound
            if marker_type == 'music':
                loaded_count += 1
                continue

            try:
                # Load SFX/VOICE as pygame.Sound (allows simultaneous playback)
                sound = pygame.mixer.Sound(audio_path)
                self.marker_sounds[i] = sound
                loaded_count += 1
            except Exception as e:
                print(f"⚠️  Could not preload marker {i}: {e}")
                missing_files.append((marker_name, f"Load error: {e}"))

        if self.debug_logging:
            print(f"✓ Preloaded {loaded_count}/{len(self.markers)} marker sounds")

        # Report missing files via callback
        if missing_files and self.on_playback_error:
            for marker_name, error_msg in missing_files:
                self.on_playback_error(marker_name, f"Audio file missing or failed to load: {error_msg}")

    def _get_expected_audio_filename(self, marker) -> Optional[str]:
        """Get the expected audio filename for a marker (for error reporting)"""
        version_data = get_version_data(marker)
        if version_data:
            return version_data.get('asset_file', '')
        # Fallback to direct asset_file attribute
        return get_marker_attr(marker, 'asset_file')

    def _get_marker_audio_path(self, marker) -> Optional[str]:
        """
        Get the audio file path for a marker

        Args:
            marker: Marker object or dict

        Returns:
            Path to audio file or None
        """
        # Use marker_utils for consistent handling
        version_data = get_version_data(marker)
        if version_data:
            asset_file = version_data.get('asset_file', '')
        else:
            asset_file = get_marker_attr(marker, 'asset_file', '')

        marker_type = get_marker_attr(marker, 'type', 'unknown')

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
        Also triggers any markers that should already be playing at current position.
        """
        self.is_playing = True
        self.last_playhead_position_ms = self.video_player.current_time_ms
        self.triggered_markers.clear()  # Reset trigger history

        if self.debug_logging:
            print(f"▶ [TRIGGER] Playback started at {self.last_playhead_position_ms}ms")

        # Trigger markers that should already be playing at current position
        self._trigger_already_playing_markers(self.last_playhead_position_ms)

    def _trigger_already_playing_markers(self, current_position_ms: int):
        """
        Check for and trigger markers that should already be playing at current position.
        This handles the case where user seeks to middle of a long marker then presses play.

        For MUSIC markers: Calculate offset and start from that point.
        For SFX/VOICE: Play from beginning (they're typically short).

        Args:
            current_position_ms: Current playhead position in milliseconds
        """
        for i, marker in enumerate(self.markers):
            marker_time_ms = get_marker_attr(marker, 'time_ms', 0)
            marker_type = get_marker_attr(marker, 'type', 'sfx')
            duration_ms = get_marker_attr(marker, 'duration_ms', 0)

            # Check if playhead is within this marker's duration
            # marker_time_ms <= current_position < marker_time_ms + duration_ms
            if duration_ms > 0 and marker_time_ms <= current_position_ms < marker_time_ms + duration_ms:
                if marker_type == 'music':
                    # Calculate offset into the track
                    offset_ms = current_position_ms - marker_time_ms
                    offset_seconds = offset_ms / 1000.0

                    # Get audio path
                    audio_path = self._get_marker_audio_path(marker)
                    if audio_path and os.path.exists(audio_path):
                        try:
                            pygame.mixer.music.load(audio_path)
                            pygame.mixer.music.play(start=offset_seconds)
                            self.current_music_marker = i
                            self.triggered_markers.add(i)

                            if self.debug_logging:
                                marker_name = get_marker_attr(marker, 'name', f'Marker {i}')
                                print(f"🔊 [TRIGGER] Started music from offset {offset_seconds:.2f}s: {marker_name}")
                        except Exception as e:
                            if self.debug_logging:
                                print(f"⚠️  Could not start music marker {i} from offset: {e}")
                else:
                    # SFX/VOICE - play from beginning (typically short)
                    self._trigger_marker(i, marker)
                    self.triggered_markers.add(i)

    def stop_playback(self):
        """
        Stop marker triggering and all playing sounds
        """
        self.is_playing = False
        pygame.mixer.stop()  # Stop all SFX/VOICE channels
        pygame.mixer.music.stop()  # Stop music stream
        self.current_music_marker = None

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
            marker_time_ms = get_marker_attr(marker, 'time_ms', 0)

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

    def _trigger_marker(self, marker_index: int, marker, offset_seconds: float = 0.0):
        """
        Trigger (play) a marker's audio

        Args:
            marker_index: Index of marker in markers list
            marker: Marker object or dict
            offset_seconds: Start offset in seconds (only used for music markers)
        """
        marker_type = get_marker_attr(marker, 'type', 'sfx')
        marker_name = get_marker_attr(marker, 'name', f'Marker {marker_index}')

        if marker_type == 'music':
            # Music uses pygame.mixer.music (single stream, supports offset)
            audio_path = self._get_marker_audio_path(marker)

            if not audio_path or not os.path.exists(audio_path):
                # Report missing audio via callback
                if self.on_playback_error:
                    expected_file = self._get_expected_audio_filename(marker)
                    self.on_playback_error(marker_name, f"Audio file not found: {expected_file}")
                return

            try:
                # Stop any currently playing music
                pygame.mixer.music.stop()

                # Load and play new music
                pygame.mixer.music.load(audio_path)

                # Get music duration to check if offset is valid
                # Note: pygame doesn't provide easy duration check, so we'll try to play
                # and let it handle edge cases
                pygame.mixer.music.play(start=offset_seconds)
                self.current_music_marker = marker_index

                if self.debug_logging:
                    if offset_seconds > 0:
                        print(f"🔊 [TRIGGER] Played music from {offset_seconds:.2f}s: {marker_name}")
                    else:
                        print(f"🔊 [TRIGGER] Played music: {marker_name}")

            except Exception as e:
                if self.debug_logging:
                    print(f"⚠️  Error playing music marker {marker_index}: {e}")
                if self.on_playback_error:
                    self.on_playback_error(marker_name, f"Playback error: {e}")

        else:
            # SFX/VOICE use pygame.Sound (multiple simultaneous channels)

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
                        if self.on_playback_error:
                            self.on_playback_error(marker_name, f"Failed to load audio: {e}")
                        return
                else:
                    # Report missing audio via callback
                    if self.on_playback_error:
                        expected_file = self._get_expected_audio_filename(marker)
                        self.on_playback_error(marker_name, f"Audio file not found: {expected_file}")
                    return

            # Play the sound
            try:
                sound = self.marker_sounds[marker_index]
                sound.play()

                if self.debug_logging:
                    print(f"🔊 [TRIGGER] Played: {marker_name}")

            except Exception as e:
                if self.debug_logging:
                    print(f"⚠️  Error playing marker {marker_index}: {e}")
                if self.on_playback_error:
                    self.on_playback_error(marker_name, f"Playback error: {e}")

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
        pygame.mixer.music.stop()
        self.current_music_marker = None

        if self.debug_logging:
            print("🧹 [TRIGGER] Sound cache cleared")
