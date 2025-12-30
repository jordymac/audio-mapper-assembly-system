"""
Assembly Service - Multi-track Audio Assembly
Handles track assignment, per-channel audio generation, and preview mixing
"""

import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from pydub import AudioSegment
from core.models import Marker, MarkerType


class AssemblyService:
    """
    Service for assembling multi-track audio from markers

    Responsibilities:
    - Assign markers to tracks (music stereo, SFX channels, voice)
    - Generate per-channel audio files
    - Create stereo preview mix for playback
    - Manage temporary assembly files
    """

    # Track configuration (matches MultiTrackDisplay)
    TRACK_MUSIC_LR = "music_lr"
    TRACK_SFX_1 = "sfx_1"
    TRACK_SFX_2 = "sfx_2"
    TRACK_VOICE = "voice"

    def __init__(self, temp_dir: str = "temp"):
        """
        Initialize assembly service

        Args:
            temp_dir: Directory for temporary assembly files
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

        # Track assignment results
        self.track_assignments: Dict[str, List[Marker]] = {}

    def assign_markers_to_tracks(self, markers: List[Marker]) -> Dict[str, List[Marker]]:
        """
        Assign markers to tracks based on type

        Algorithm:
        - All music markers → Track 1 (Music L/R Stereo)
        - SFX markers alternate → Ch 3 (SFX 1) and Ch 4 (SFX 2)
        - All voice markers → Ch 5 (Voice)

        Args:
            markers: List of markers to assign

        Returns:
            Dict mapping track_id to list of markers
        """
        # Collect markers by type
        music_markers = [m for m in markers if m.type == MarkerType.MUSIC.value]
        sfx_markers = [m for m in markers if m.type == MarkerType.SFX.value]
        voice_markers = [m for m in markers if m.type == MarkerType.VOICE.value]

        # Sort SFX by time for even distribution
        sfx_markers_sorted = sorted(sfx_markers, key=lambda m: m.time_ms)

        # Assign to tracks
        track_assignments = {
            self.TRACK_MUSIC_LR: music_markers,
            self.TRACK_SFX_1: sfx_markers_sorted[::2],   # Even indices (0, 2, 4, ...)
            self.TRACK_SFX_2: sfx_markers_sorted[1::2],  # Odd indices (1, 3, 5, ...)
            self.TRACK_VOICE: voice_markers
        }

        # Update marker track assignments
        for marker in music_markers:
            marker.assigned_track = self.TRACK_MUSIC_LR
            marker.assigned_channels = [1, 2]  # Stereo

        for marker in track_assignments[self.TRACK_SFX_1]:
            marker.assigned_track = self.TRACK_SFX_1
            marker.assigned_channels = [3]  # Mono

        for marker in track_assignments[self.TRACK_SFX_2]:
            marker.assigned_track = self.TRACK_SFX_2
            marker.assigned_channels = [4]  # Mono

        for marker in voice_markers:
            marker.assigned_track = self.TRACK_VOICE
            marker.assigned_channels = [5]  # Mono

        self.track_assignments = track_assignments
        return track_assignments

    def generate_track_audio(
        self,
        track_id: str,
        markers: List[Marker],
        duration_ms: int,
        is_stereo: bool = False
    ) -> Optional[AudioSegment]:
        """
        Generate audio for a single track by overlaying marker audio

        Args:
            track_id: Track identifier
            markers: Markers assigned to this track
            duration_ms: Total duration in milliseconds
            is_stereo: True for stereo track, False for mono

        Returns:
            AudioSegment for this track, or None if no markers
        """
        if not markers:
            # Return silent track if no markers
            channels = 2 if is_stereo else 1
            return AudioSegment.silent(duration=duration_ms).set_channels(channels)

        # Create silent base track
        channels = 2 if is_stereo else 1
        track_audio = AudioSegment.silent(duration=duration_ms).set_channels(channels)

        # Overlay each marker's audio at its timestamp
        for marker in markers:
            # Check if audio file exists
            if not marker.asset_file or not os.path.exists(marker.asset_file):
                print(f"Warning: Audio file not found for marker {marker.name}: {marker.asset_file}")
                continue

            try:
                # Load audio clip
                audio_clip = AudioSegment.from_file(marker.asset_file)

                # Convert to appropriate channel count
                if is_stereo and audio_clip.channels == 1:
                    # Convert mono to stereo for music track
                    audio_clip = audio_clip.set_channels(2)
                elif not is_stereo and audio_clip.channels == 2:
                    # Convert stereo to mono for SFX/Voice tracks
                    audio_clip = audio_clip.set_channels(1)

                # Overlay at marker position
                track_audio = track_audio.overlay(audio_clip, position=marker.time_ms)

            except Exception as e:
                print(f"Error loading audio for marker {marker.name}: {e}")
                continue

        return track_audio

    def assemble_audio(
        self,
        markers: List[Marker],
        duration_ms: int
    ) -> Tuple[Dict[str, str], str]:
        """
        Assemble multi-track audio from markers

        Steps:
        1. Assign markers to tracks
        2. Generate per-track audio files
        3. Create stereo preview mix
        4. Save all files to temp directory

        Args:
            markers: List of all markers
            duration_ms: Total duration in milliseconds

        Returns:
            Tuple of (track_files_dict, preview_file_path)
            - track_files_dict: {track_id: file_path}
            - preview_file_path: Path to stereo preview mix
        """
        # Step 1: Assign markers to tracks
        print("Assigning markers to tracks...")
        track_assignments = self.assign_markers_to_tracks(markers)

        # Step 2: Generate per-track audio
        print("Generating per-track audio...")
        track_files = {}
        track_audio_segments = {}

        # Music track (stereo)
        music_audio = self.generate_track_audio(
            self.TRACK_MUSIC_LR,
            track_assignments[self.TRACK_MUSIC_LR],
            duration_ms,
            is_stereo=True
        )
        if music_audio:
            music_file = str(self.temp_dir / "channel_1_2_music_stereo.wav")
            music_audio.export(music_file, format="wav")
            track_files[self.TRACK_MUSIC_LR] = music_file
            track_audio_segments[self.TRACK_MUSIC_LR] = music_audio

        # SFX Track 1 (mono)
        sfx1_audio = self.generate_track_audio(
            self.TRACK_SFX_1,
            track_assignments[self.TRACK_SFX_1],
            duration_ms,
            is_stereo=False
        )
        if sfx1_audio:
            sfx1_file = str(self.temp_dir / "channel_3_sfx_1.wav")
            sfx1_audio.export(sfx1_file, format="wav")
            track_files[self.TRACK_SFX_1] = sfx1_file
            track_audio_segments[self.TRACK_SFX_1] = sfx1_audio

        # SFX Track 2 (mono)
        sfx2_audio = self.generate_track_audio(
            self.TRACK_SFX_2,
            track_assignments[self.TRACK_SFX_2],
            duration_ms,
            is_stereo=False
        )
        if sfx2_audio:
            sfx2_file = str(self.temp_dir / "channel_4_sfx_2.wav")
            sfx2_audio.export(sfx2_file, format="wav")
            track_files[self.TRACK_SFX_2] = sfx2_file
            track_audio_segments[self.TRACK_SFX_2] = sfx2_audio

        # Voice track (mono)
        voice_audio = self.generate_track_audio(
            self.TRACK_VOICE,
            track_assignments[self.TRACK_VOICE],
            duration_ms,
            is_stereo=False
        )
        if voice_audio:
            voice_file = str(self.temp_dir / "channel_5_voice.wav")
            voice_audio.export(voice_file, format="wav")
            track_files[self.TRACK_VOICE] = voice_file
            track_audio_segments[self.TRACK_VOICE] = voice_audio

        # Step 3: Create stereo preview mix
        print("Creating stereo preview mix...")
        preview_audio = AudioSegment.silent(duration=duration_ms).set_channels(2)

        # Mix all tracks into stereo preview
        for track_id, audio_segment in track_audio_segments.items():
            # Ensure stereo for mixing
            if audio_segment.channels == 1:
                audio_segment = audio_segment.set_channels(2)
            preview_audio = preview_audio.overlay(audio_segment)

        # Export preview
        preview_file = str(self.temp_dir / "assembled_preview_stereo.wav")
        preview_audio.export(preview_file, format="wav")

        print(f"✓ Assembly complete! Generated {len(track_files)} track files + preview")
        return track_files, preview_file

    def get_track_assignment_summary(self) -> str:
        """
        Get human-readable summary of track assignments

        Returns:
            Formatted string showing which markers are on which tracks
        """
        if not self.track_assignments:
            return "No track assignments yet"

        summary = []
        summary.append("Track Assignments:")
        summary.append("-" * 50)

        for track_id, markers in self.track_assignments.items():
            track_label = {
                self.TRACK_MUSIC_LR: "Music L/R (Ch 1-2 Stereo)",
                self.TRACK_SFX_1: "SFX 1 (Ch 3 Mono)",
                self.TRACK_SFX_2: "SFX 2 (Ch 4 Mono)",
                self.TRACK_VOICE: "Voice (Ch 5 Mono)"
            }.get(track_id, track_id)

            summary.append(f"\n{track_label}: {len(markers)} markers")
            for marker in markers:
                time_str = f"{marker.time_ms / 1000:.3f}s"
                summary.append(f"  - {time_str}: {marker.name or marker.type}")

        return "\n".join(summary)

    def generate_waveform_data(
        self,
        audio_segment: AudioSegment,
        num_samples: int = 1000
    ) -> List[float]:
        """
        Generate waveform data from audio segment for visualization

        Args:
            audio_segment: AudioSegment to generate waveform from
            num_samples: Number of data points to generate (resolution)

        Returns:
            List of amplitude values normalized to -1.0 to 1.0
        """
        if not audio_segment:
            return []

        # Get raw audio data as numpy array
        samples = np.array(audio_segment.get_array_of_samples())

        # If stereo, convert to mono by averaging channels
        if audio_segment.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)

        # Normalize to -1.0 to 1.0 range
        max_val = np.abs(samples).max()
        if max_val > 0:
            samples = samples / max_val

        # Downsample to num_samples points
        if len(samples) > num_samples:
            # Calculate step size
            step = len(samples) / num_samples
            indices = np.arange(num_samples) * step
            indices = indices.astype(int)
            waveform_data = samples[indices]
        else:
            waveform_data = samples

        return waveform_data.tolist()

    def get_track_waveforms(
        self,
        track_files: Dict[str, str],
        num_samples: int = 1000
    ) -> Dict[str, Dict[str, List[float]]]:
        """
        Generate waveform data for all tracks

        Args:
            track_files: Dict mapping track_id to file path
            num_samples: Number of samples per waveform

        Returns:
            Dict mapping track_id to waveform data
            For stereo tracks: {"L": [...], "R": [...]}
            For mono tracks: {"mono": [...]}
        """
        waveforms = {}

        for track_id, file_path in track_files.items():
            if not os.path.exists(file_path):
                continue

            try:
                # Load audio
                audio = AudioSegment.from_file(file_path)

                # Generate waveform based on channel count
                if audio.channels == 2 and track_id == self.TRACK_MUSIC_LR:
                    # Stereo: separate L and R channels
                    samples = np.array(audio.get_array_of_samples())
                    samples = samples.reshape((-1, 2))

                    # Left channel
                    left_samples = samples[:, 0]
                    max_val = np.abs(left_samples).max()
                    if max_val > 0:
                        left_samples = left_samples / max_val
                    waveforms[track_id] = {
                        "L": self._downsample_waveform(left_samples, num_samples)
                    }

                    # Right channel
                    right_samples = samples[:, 1]
                    max_val = np.abs(right_samples).max()
                    if max_val > 0:
                        right_samples = right_samples / max_val
                    waveforms[track_id]["R"] = self._downsample_waveform(right_samples, num_samples)
                else:
                    # Mono
                    waveform_data = self.generate_waveform_data(audio, num_samples)
                    waveforms[track_id] = {"mono": waveform_data}

            except Exception as e:
                print(f"Error generating waveform for {track_id}: {e}")

        return waveforms

    def _downsample_waveform(self, samples: np.ndarray, num_samples: int) -> List[float]:
        """Helper to downsample waveform data"""
        if len(samples) > num_samples:
            step = len(samples) / num_samples
            indices = np.arange(num_samples) * step
            indices = indices.astype(int)
            return samples[indices].tolist()
        return samples.tolist()

    def cleanup_temp_files(self):
        """Remove temporary assembly files"""
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("*.wav"):
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Warning: Could not delete temp file {file}: {e}")
