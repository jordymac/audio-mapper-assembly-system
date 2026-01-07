"""
Assembly Service - Multi-track Audio Assembly
Handles track assignment, per-channel audio generation, and preview mixing
"""

import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from pydub import AudioSegment
from scipy.io import wavfile
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
            markers: List of markers (can be dicts or Marker objects)

        Returns:
            Dict mapping track_id to list of markers
        """
        # Helper to get marker type (works with both dict and Marker objects)
        def get_type(m):
            return m.get('type') if isinstance(m, dict) else m.type

        def get_time_ms(m):
            return m.get('time_ms', 0) if isinstance(m, dict) else m.time_ms

        # Collect markers by type
        music_markers = [m for m in markers if get_type(m) == MarkerType.MUSIC.value]
        sfx_markers = [m for m in markers if get_type(m) == MarkerType.SFX.value]
        voice_markers = [m for m in markers if get_type(m) == MarkerType.VOICE.value]

        # Sort SFX by time for even distribution
        sfx_markers_sorted = sorted(sfx_markers, key=get_time_ms)

        # Assign to tracks
        track_assignments = {
            self.TRACK_MUSIC_LR: music_markers,
            self.TRACK_SFX_1: sfx_markers_sorted[::2],   # Even indices (0, 2, 4, ...)
            self.TRACK_SFX_2: sfx_markers_sorted[1::2],  # Odd indices (1, 3, 5, ...)
            self.TRACK_VOICE: voice_markers
        }

        # Update marker track assignments (works with both dict and Marker objects)
        for marker in music_markers:
            if isinstance(marker, dict):
                marker['assigned_track'] = self.TRACK_MUSIC_LR
                marker['assigned_channels'] = [1, 2]
            else:
                marker.assigned_track = self.TRACK_MUSIC_LR
                marker.assigned_channels = [1, 2]

        for marker in track_assignments[self.TRACK_SFX_1]:
            if isinstance(marker, dict):
                marker['assigned_track'] = self.TRACK_SFX_1
                marker['assigned_channels'] = [3]
            else:
                marker.assigned_track = self.TRACK_SFX_1
                marker.assigned_channels = [3]

        for marker in track_assignments[self.TRACK_SFX_2]:
            if isinstance(marker, dict):
                marker['assigned_track'] = self.TRACK_SFX_2
                marker['assigned_channels'] = [4]
            else:
                marker.assigned_track = self.TRACK_SFX_2
                marker.assigned_channels = [4]

        for marker in voice_markers:
            if isinstance(marker, dict):
                marker['assigned_track'] = self.TRACK_VOICE
                marker['assigned_channels'] = [5]
            else:
                marker.assigned_track = self.TRACK_VOICE
                marker.assigned_channels = [5]

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
            # Get current version data (handles both dict and Marker objects)
            if isinstance(marker, dict):
                # Dict marker - get current version's asset_file
                versions = marker.get('versions', [])
                current_version = marker.get('current_version', 1)
                current_version_data = next((v for v in versions if v.get('version') == current_version), None)

                if not current_version_data:
                    continue

                asset_file = current_version_data.get('asset_file', '')
                marker_name = marker.get('name', '(unnamed)')
                marker_type = marker.get('type', 'unknown')
                time_ms = marker.get('time_ms', 0)
            else:
                # Marker object
                asset_file = marker.asset_file
                marker_name = marker.name
                marker_type = marker.type
                time_ms = marker.time_ms

            # Check if audio file exists - try multiple paths
            if not asset_file:
                continue

            possible_paths = [
                os.path.join("generated_audio", marker_type, asset_file),
                os.path.join("generated_audio", asset_file),
                asset_file
            ]

            audio_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    audio_path = path
                    break

            if not audio_path:
                print(f"Warning: Audio file not found for marker {marker_name}: {asset_file}")
                continue

            try:
                # Load audio clip
                audio_clip = AudioSegment.from_file(audio_path)

                # Convert to appropriate channel count
                if is_stereo and audio_clip.channels == 1:
                    # Convert mono to stereo for music track
                    audio_clip = audio_clip.set_channels(2)
                elif not is_stereo and audio_clip.channels == 2:
                    # Convert stereo to mono for SFX/Voice tracks
                    audio_clip = audio_clip.set_channels(1)

                # Overlay at marker position
                track_audio = track_audio.overlay(audio_clip, position=time_ms)

            except Exception as e:
                print(f"Error loading audio for marker {marker_name}: {e}")
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
            For stereo tracks: {"stereo": [...]}  (averaged L+R)
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
                    # Stereo: average L and R channels into single waveform
                    samples = np.array(audio.get_array_of_samples())
                    samples = samples.reshape((-1, 2))

                    # Average L and R channels
                    left_samples = samples[:, 0]
                    right_samples = samples[:, 1]
                    stereo_avg = (left_samples + right_samples) / 2

                    # Normalize
                    max_val = np.abs(stereo_avg).max()
                    if max_val > 0:
                        stereo_avg = stereo_avg / max_val

                    waveforms[track_id] = {
                        "stereo": self._downsample_waveform(stereo_avg, num_samples)
                    }
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

    def get_next_asset_ids(self, output_dir: str) -> Dict[str, int]:
        """
        Find highest existing asset IDs and return next available IDs

        Args:
            output_dir: Directory to scan for existing asset files

        Returns:
            Dict with next available IDs for each type: {'music': 1, 'sfx': 1, 'voice': 1}
        """
        import re
        import glob

        # Check existing files in output directory
        existing_files = glob.glob(os.path.join(output_dir, "*.wav"))

        # Track highest ID for each type
        max_ids = {'music': 0, 'sfx': 0, 'voice': 0}

        for filepath in existing_files:
            filename = os.path.basename(filepath)

            # Match MUS_00001, SFX_00002, VOX_00003 patterns
            mus_match = re.match(r'MUS_(\d+)_', filename)
            sfx_match = re.match(r'SFX_(\d+)_', filename)
            vox_match = re.match(r'VOX_(\d+)_', filename)

            if mus_match:
                max_ids['music'] = max(max_ids['music'], int(mus_match.group(1)))
            elif sfx_match:
                max_ids['sfx'] = max(max_ids['sfx'], int(sfx_match.group(1)))
            elif vox_match:
                max_ids['voice'] = max(max_ids['voice'], int(vox_match.group(1)))

        # Return next available IDs
        return {
            'music': max_ids['music'] + 1,
            'sfx': max_ids['sfx'] + 1,
            'voice': max_ids['voice'] + 1
        }

    def generate_track_description(self, markers: List, default: str = "Track") -> str:
        """
        Generate descriptive filename suffix from marker data

        Args:
            markers: List of markers on this track
            default: Default description if no data available

        Returns:
            Sanitized filename suffix (max 50 chars)
        """
        import re

        if not markers:
            return default

        # Try to get description from first marker's name
        first_marker = markers[0]

        # Handle both dict and Marker objects
        if isinstance(first_marker, dict):
            marker_name = first_marker.get('name', '')
            marker_type = first_marker.get('type', 'unknown')
            prompt_data = first_marker.get('prompt_data', {})
        else:
            marker_name = getattr(first_marker, 'name', '')
            marker_type = getattr(first_marker, 'type', 'unknown')
            prompt_data = getattr(first_marker, 'prompt_data', {})

        if marker_name:
            # Use marker name, sanitize for filename
            desc = marker_name
            desc = desc.replace(' ', '_')
            desc = re.sub(r'[^\w\-_]', '', desc)  # Remove special chars
            return desc[:50]  # Limit length

        # Fallback: try to extract from prompt_data
        if marker_type == 'music':
            styles = prompt_data.get('positiveGlobalStyles', [])
            if styles:
                desc = '_'.join(styles[:2])  # First 2 styles
                return desc.replace(' ', '_')[:50]

        elif marker_type == 'voice':
            voice_profile = prompt_data.get('voice_profile', '')
            if voice_profile:
                desc = voice_profile.replace(' ', '_')
                return desc[:50]

        elif marker_type == 'sfx':
            description = prompt_data.get('description', '')
            if description:
                desc = description.replace(' ', '_')
                return desc[:50]

        # Ultimate fallback
        return default

    def save_multichannel_wav(
        self,
        filename: str,
        music_track: Optional[AudioSegment],
        sfx1_track: Optional[AudioSegment],
        sfx2_track: Optional[AudioSegment],
        voice_track: Optional[AudioSegment]
    ):
        """
        Save multiple audio tracks into a single multi-channel WAV file

        Channel layout:
        - Channels 1-2: Music (Stereo L/R)
        - Channel 3: SFX 1 (Mono)
        - Channel 4: SFX 2 (Mono)
        - Channel 5: Voice (Mono)

        Args:
            filename: Output file path
            music_track: Stereo music AudioSegment (or None)
            sfx1_track: Mono SFX 1 AudioSegment (or None)
            sfx2_track: Mono SFX 2 AudioSegment (or None)
            voice_track: Mono voice AudioSegment (or None)
        """
        # Get target sample rate (use highest sample rate among tracks)
        target_sample_rate = 48000  # Default to 48kHz
        max_duration_ms = 0

        for track in [music_track, sfx1_track, sfx2_track, voice_track]:
            if track:
                target_sample_rate = max(target_sample_rate, track.frame_rate)
                max_duration_ms = max(max_duration_ms, len(track))

        if max_duration_ms == 0:
            raise ValueError("At least one track must be provided")

        # Normalize all tracks to the same sample rate and duration
        def normalize_track(track: Optional[AudioSegment], target_duration_ms: int, target_sample_rate: int, channels: int) -> AudioSegment:
            """Ensure track has correct sample rate, duration, and channel count"""
            if track is None:
                # Create silent track with correct properties
                return AudioSegment.silent(
                    duration=target_duration_ms,
                    frame_rate=target_sample_rate
                ).set_channels(channels)

            # Resample to target sample rate if needed
            if track.frame_rate != target_sample_rate:
                track = track.set_frame_rate(target_sample_rate)

            # Adjust duration
            current_duration = len(track)
            if current_duration < target_duration_ms:
                # Pad with silence
                silence_needed = target_duration_ms - current_duration
                silence = AudioSegment.silent(
                    duration=silence_needed,
                    frame_rate=target_sample_rate
                ).set_channels(track.channels)
                track = track + silence
            elif current_duration > target_duration_ms:
                # Trim to target duration
                track = track[:target_duration_ms]

            return track

        # Normalize all tracks to max duration and target sample rate
        music_track = normalize_track(music_track, max_duration_ms, target_sample_rate, 2)  # Stereo
        sfx1_track = normalize_track(sfx1_track, max_duration_ms, target_sample_rate, 1)    # Mono
        sfx2_track = normalize_track(sfx2_track, max_duration_ms, target_sample_rate, 1)    # Mono
        voice_track = normalize_track(voice_track, max_duration_ms, target_sample_rate, 1)  # Mono

        # Debug: Check track durations
        print(f"  Track durations after normalization:")
        print(f"    Music: {len(music_track)}ms, {music_track.frame_rate}Hz, {music_track.channels}ch")
        print(f"    SFX1:  {len(sfx1_track)}ms, {sfx1_track.frame_rate}Hz, {sfx1_track.channels}ch")
        print(f"    SFX2:  {len(sfx2_track)}ms, {sfx2_track.frame_rate}Hz, {sfx2_track.channels}ch")
        print(f"    Voice: {len(voice_track)}ms, {voice_track.frame_rate}Hz, {voice_track.channels}ch")

        # Convert each AudioSegment to numpy array
        arrays = []

        # Music track (stereo - 2 channels)
        data = np.array(music_track.get_array_of_samples())
        if music_track.channels == 2:
            data = data.reshape((-1, 2))
        else:
            # Convert mono to stereo
            data = data.reshape((-1, 1))
            data = np.hstack([data, data])
        arrays.append(data)

        # SFX 1 track (mono - 1 channel)
        data = np.array(sfx1_track.get_array_of_samples())
        arrays.append(data.reshape((-1, 1)))

        # SFX 2 track (mono - 1 channel)
        data = np.array(sfx2_track.get_array_of_samples())
        arrays.append(data.reshape((-1, 1)))

        # Voice track (mono - 1 channel)
        data = np.array(voice_track.get_array_of_samples())
        arrays.append(data.reshape((-1, 1)))

        # Debug: Check array sizes
        print(f"  Array sizes after conversion:")
        print(f"    Music: {arrays[0].shape}")
        print(f"    SFX1:  {arrays[1].shape}")
        print(f"    SFX2:  {arrays[2].shape}")
        print(f"    Voice: {arrays[3].shape}")

        # Ensure all arrays have exactly the same length (fix rounding errors)
        max_samples = max(arr.shape[0] for arr in arrays)
        print(f"  Max samples: {max_samples}, will normalize all arrays to this length")

        normalized_arrays = []
        for arr in arrays:
            current_samples = arr.shape[0]
            if current_samples < max_samples:
                # Pad with zeros
                padding = max_samples - current_samples
                if arr.ndim == 2:
                    # For 2D arrays (stereo), pad along first axis
                    arr = np.vstack([arr, np.zeros((padding, arr.shape[1]), dtype=arr.dtype)])
                else:
                    # For 1D arrays (mono), pad along first axis
                    arr = np.concatenate([arr, np.zeros(padding, dtype=arr.dtype)])
            elif current_samples > max_samples:
                # Trim to max length
                arr = arr[:max_samples]

            normalized_arrays.append(arr)

        # Concatenate along channel axis: (samples, 5)
        # Result: [Music_L, Music_R, SFX1, SFX2, Voice]
        multichannel = np.hstack(normalized_arrays)

        # Write to WAV file
        wavfile.write(filename, target_sample_rate, multichannel.astype(np.int16))

    def export_with_metadata(
        self,
        markers: List,
        duration_ms: int,
        template_id: str,
        template_name: str = "",
        video_reference: str = "",
        output_dir: str = "output"
    ) -> Dict[str, any]:
        """
        Export with full metadata structure (METADATA_EXPORT_PLAN.md)

        Creates:
        - MUSIC/, SFX/, VOICE/ subdirectories with individual audio files
        - Individual metadata JSON per audio file
        - Multi-channel 5ch WAV file
        - Assembled metadata JSON
        - Template JSON

        Args:
            markers: List of all markers
            duration_ms: Total duration in milliseconds
            template_id: Template identifier (e.g., "DM01")
            template_name: Template name (e.g., "Indoor Routine")
            video_reference: Original video filename
            output_dir: Base output directory

        Returns:
            Dict with export summary
        """
        import json
        import shutil
        from datetime import datetime
        from pydub.utils import mediainfo

        # Create output directory structure
        output_path = Path(output_dir) / f"{template_id}_{template_name.replace(' ', '_')}"
        output_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        music_dir = output_path / "MUSIC"
        sfx_dir = output_path / "SFX"
        voice_dir = output_path / "VOICE"
        music_dir.mkdir(exist_ok=True)
        sfx_dir.mkdir(exist_ok=True)
        voice_dir.mkdir(exist_ok=True)

        print(f"Exporting to: {output_path}")
        print("Creating organized folder structure...")

        # Track what gets exported
        exported_files = []
        markers_included = []

        # Process each marker and export individual files + metadata
        for marker in markers:
            # Get marker data (works with both dict and Marker objects)
            if isinstance(marker, dict):
                marker_type = marker.get('type', '')
                time_ms = marker.get('time_ms', 0)
                title = marker.get('title', marker.get('name', ''))
                categories = marker.get('categories', {})
                notes = marker.get('notes', '')
                prompt_data = marker.get('prompt_data', {})
                used_in_templates = marker.get('used_in_templates', [])
                if template_id not in used_in_templates:
                    used_in_templates.append(template_id)

                # Get asset_file from versions if available
                versions = marker.get('versions', [])
                if versions:
                    current_version = marker.get('current_version', 1)
                    current_version_data = next(
                        (v for v in versions if v.get('version') == current_version),
                        versions[-1] if versions else {}
                    )
                    asset_file = current_version_data.get('asset_file', '')
                else:
                    asset_file = marker.get('asset_file', '')
            else:
                marker_type = marker.type
                time_ms = marker.time_ms
                title = marker.title or marker.name
                categories = marker.categories
                notes = marker.notes
                prompt_data = marker.prompt_data
                used_in_templates = marker.used_in_templates.copy()
                if template_id not in used_in_templates:
                    used_in_templates.append(template_id)

                # Get asset_file from versions if available
                if marker.versions:
                    current_version_data = next(
                        (v for v in marker.versions if v.version == marker.current_version),
                        marker.versions[-1] if marker.versions else None
                    )
                    asset_file = current_version_data.asset_file if current_version_data else marker.asset_file
                else:
                    asset_file = marker.asset_file

            # Skip markers without generated audio
            if not asset_file:
                print(f"  ⚠ Skipping marker at {time_ms}ms - no asset file")
                continue

            # Find source audio file
            print(f"  Looking for audio file: {asset_file} (type: {marker_type})")
            source_path = self._find_audio_file(asset_file, marker_type)
            if not source_path:
                print(f"  ⚠ Warning: Audio file not found for {asset_file}")
                continue
            print(f"    Found at: {source_path}")

            # Get audio duration
            try:
                info = mediainfo(source_path)
                audio_duration_ms = int(float(info.get('duration', 0)) * 1000)
            except:
                audio_duration_ms = 0

            # Determine destination directory
            if marker_type == 'music':
                dest_dir = music_dir
            elif marker_type == 'sfx':
                dest_dir = sfx_dir
            elif marker_type == 'voice':
                dest_dir = voice_dir
            else:
                continue

            # Copy audio file
            dest_file = dest_dir / asset_file
            shutil.copy2(source_path, dest_file)
            print(f"  ✓ {marker_type.upper()}/{asset_file}")

            # Generate individual metadata JSON
            metadata = {
                "file": asset_file,
                "type": marker_type,
                "timestamp_ms": time_ms,
                "duration_ms": audio_duration_ms,
                "title": title,
                "categories": categories,
                "notes": notes,
                "usedInTemplates": used_in_templates,
                "generated_at": datetime.now().isoformat(),
                "prompt_used": prompt_data
            }

            # Write metadata file
            metadata_file = dest_dir / f"{Path(asset_file).stem}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            exported_files.append(str(dest_file.relative_to(output_path)))
            markers_included.append(asset_file)

        # Assemble multi-channel WAV file
        print("\nAssembling multi-channel WAV...")
        track_assignments = self.assign_markers_to_tracks(markers)

        # Generate tracks
        music_track = self.generate_track_audio(
            self.TRACK_MUSIC_LR,
            track_assignments[self.TRACK_MUSIC_LR],
            duration_ms,
            is_stereo=True
        )

        sfx1_track = self.generate_track_audio(
            self.TRACK_SFX_1,
            track_assignments[self.TRACK_SFX_1],
            duration_ms,
            is_stereo=False
        )

        sfx2_track = self.generate_track_audio(
            self.TRACK_SFX_2,
            track_assignments[self.TRACK_SFX_2],
            duration_ms,
            is_stereo=False
        )

        voice_track = self.generate_track_audio(
            self.TRACK_VOICE,
            track_assignments[self.TRACK_VOICE],
            duration_ms,
            is_stereo=False
        )

        # Save multi-channel assembled file in main output directory
        assembled_filename = f"{template_id}_assembled.wav"
        assembled_filepath = output_path / assembled_filename
        self.save_multichannel_wav(
            str(assembled_filepath),
            music_track,
            sfx1_track,
            sfx2_track,
            voice_track
        )
        print(f"  ✓ {assembled_filename}")

        # Generate assembled audio metadata
        marker_counts = {
            'music': len([m for m in markers if (m.get('type') if isinstance(m, dict) else m.type) == 'music']),
            'sfx': len([m for m in markers if (m.get('type') if isinstance(m, dict) else m.type) == 'sfx']),
            'voice': len([m for m in markers if (m.get('type') if isinstance(m, dict) else m.type) == 'voice']),
        }
        marker_counts['total'] = sum(marker_counts.values())

        assembled_metadata = {
            "template_id": template_id,
            "template_name": template_name,
            "total_duration_ms": duration_ms,
            "video_reference": video_reference,
            "marker_count": marker_counts,
            "markers_included": markers_included,
            "assembled_file": f"{template_id}_assembled.wav",
            "export_format": {
                "channels": 5,
                "channel_map": {
                    "1": "music_left",
                    "2": "music_right",
                    "3": "sfx_1",
                    "4": "sfx_2",
                    "5": "voice"
                },
                "channel_types": {
                    "1-2": "stereo",
                    "3": "mono",
                    "4": "mono",
                    "5": "mono"
                },
                "sample_rate": 48000,
                "bit_depth": 24
            },
            "exported_at": datetime.now().isoformat(),
            "exported_by": "Audio Mapper v1.0",
            "version": "1.0"
        }

        # Write assembled metadata
        assembled_metadata_file = output_path / f"{template_id}_export_metadata.json"
        with open(assembled_metadata_file, 'w') as f:
            json.dump(assembled_metadata, f, indent=2)
        print(f"  ✓ {template_id}_export_metadata.json")

        # Export template JSON
        template_data = {
            "template_id": template_id,
            "template_name": template_name,
            "duration_ms": duration_ms,
            "markers": [self._serialize_marker_for_export(m) for m in markers]
        }
        template_file = output_path / f"{template_id}_template.json"
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
        print(f"  ✓ {template_id}_template.json")

        print(f"\n✅ Export complete!")
        print(f"  - {len(exported_files)} audio files exported")
        print(f"  - {len(exported_files)} metadata files created")
        print(f"  - 1 assembled multi-channel WAV")
        print(f"  - 1 assembled metadata JSON")
        print(f"  - 1 template JSON")

        return {
            "output_dir": str(output_path),
            "exported_files": exported_files,
            "assembled_file": assembled_filename,
            "metadata_file": f"{template_id}_export_metadata.json",
            "template_file": f"{template_id}_template.json"
        }

    def _find_audio_file(self, asset_file: str, marker_type: str) -> Optional[Path]:
        """Find audio file in various possible locations"""
        possible_paths = [
            Path("generated_audio") / marker_type / asset_file,
            Path("generated_audio") / asset_file,
            Path(asset_file)
        ]

        for path in possible_paths:
            if path.exists():
                return path
        return None

    def export_tracks(
        self,
        markers: List,
        duration_ms: int,
        template_id: str,
        template_name: str = "",
        output_dir: str = "output"
    ) -> Dict[str, any]:
        """
        Export both individual track files AND multi-channel consolidated WAV

        Creates:
        - Individual track files with asset naming (MUS_00001_[desc].wav, etc.)
        - 5-channel consolidated WAV file
        - Metadata JSON file with track assignments and marker data

        Args:
            markers: List of all markers
            duration_ms: Total duration in milliseconds
            template_id: Template identifier (e.g., "DM01")
            template_name: Template name (e.g., "Indoor Routine")
            output_dir: Base output directory

        Returns:
            Dict with export summary:
            {
                'output_dir': str,
                'individual_tracks': Dict[str, str],  # track_id -> filename
                'multichannel_file': str,
                'metadata_file': str
            }
        """
        import json
        from datetime import datetime

        # 1. Group markers by track assignment
        print("Assigning markers to tracks...")
        track_assignments = self.assign_markers_to_tracks(markers)

        # 2. Create output directory structure
        output_path = Path(output_dir) / template_id
        output_path.mkdir(parents=True, exist_ok=True)

        # 3. Get next available asset IDs
        next_ids = self.get_next_asset_ids(str(output_path))

        # 4. Generate individual track files with asset naming
        print("Generating track files...")
        track_files = {}
        track_audio_segments = {}

        # Music: Stereo (Channels 1-2)
        music_markers = track_assignments[self.TRACK_MUSIC_LR]
        music_track = self.generate_track_audio(
            self.TRACK_MUSIC_LR,
            music_markers,
            duration_ms,
            is_stereo=True
        )
        if music_track:
            music_desc = self.generate_track_description(music_markers, "Music_Track")
            music_filename = f"MUS_{next_ids['music']:05d}_{music_desc}.wav"
            music_file = str(output_path / music_filename)
            music_track.export(music_file, format="wav")
            track_files["channels_1_2"] = music_filename
            track_audio_segments["music"] = music_track
            print(f"  ✓ {music_filename}")

        # SFX Channel 3: Mono
        sfx1_markers = track_assignments[self.TRACK_SFX_1]
        sfx1_track = self.generate_track_audio(
            self.TRACK_SFX_1,
            sfx1_markers,
            duration_ms,
            is_stereo=False
        )
        if sfx1_track:
            sfx1_desc = self.generate_track_description(sfx1_markers, "SFX_Ch3")
            sfx1_filename = f"SFX_{next_ids['sfx']:05d}_{sfx1_desc}.wav"
            sfx1_file = str(output_path / sfx1_filename)
            sfx1_track.export(sfx1_file, format="wav")
            track_files["channel_3"] = sfx1_filename
            track_audio_segments["sfx1"] = sfx1_track
            next_ids['sfx'] += 1  # Increment for next SFX track
            print(f"  ✓ {sfx1_filename}")

        # SFX Channel 4: Mono
        sfx2_markers = track_assignments[self.TRACK_SFX_2]
        sfx2_track = self.generate_track_audio(
            self.TRACK_SFX_2,
            sfx2_markers,
            duration_ms,
            is_stereo=False
        )
        if sfx2_track:
            sfx2_desc = self.generate_track_description(sfx2_markers, "SFX_Ch4")
            sfx2_filename = f"SFX_{next_ids['sfx']:05d}_{sfx2_desc}.wav"
            sfx2_file = str(output_path / sfx2_filename)
            sfx2_track.export(sfx2_file, format="wav")
            track_files["channel_4"] = sfx2_filename
            track_audio_segments["sfx2"] = sfx2_track
            print(f"  ✓ {sfx2_filename}")

        # Voice Channel 5: Mono
        voice_markers = track_assignments[self.TRACK_VOICE]
        voice_track = self.generate_track_audio(
            self.TRACK_VOICE,
            voice_markers,
            duration_ms,
            is_stereo=False
        )
        if voice_track:
            voice_desc = self.generate_track_description(voice_markers, "Voice_Track")
            voice_filename = f"VOX_{next_ids['voice']:05d}_{voice_desc}.wav"
            voice_file = str(output_path / voice_filename)
            voice_track.export(voice_file, format="wav")
            track_files["channel_5"] = voice_filename
            track_audio_segments["voice"] = voice_track
            print(f"  ✓ {voice_filename}")

        # 5. Create 5-channel consolidated WAV
        print("Creating 5-channel consolidated WAV...")
        multichannel_filename = f"{template_id}_5ch.wav"
        multichannel_file = str(output_path / multichannel_filename)
        self.save_multichannel_wav(
            multichannel_file,
            track_audio_segments.get("music"),
            track_audio_segments.get("sfx1"),
            track_audio_segments.get("sfx2"),
            track_audio_segments.get("voice")
        )
        print(f"  ✓ {multichannel_filename}")

        # 6. Write metadata JSON
        print("Writing metadata...")
        metadata = {
            "template_id": template_id,
            "template_name": template_name,
            "duration_ms": duration_ms,
            "export_date": datetime.now().isoformat(),
            "individual_tracks": track_files,
            "multichannel_file": multichannel_filename,
            "channel_layout": "5.0 (Music L/R, SFX1, SFX2, Voice)",
            "markers": [
                self._serialize_marker_for_export(m) for m in markers
            ]
        }
        metadata_file = str(output_path / "metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"  ✓ metadata.json")

        print(f"\n✅ Export complete! Output: {output_path}")
        print(f"  - {len(track_files)} individual track files")
        print(f"  - 1 multi-channel consolidated WAV")
        print(f"  - 1 metadata JSON file")

        return {
            "output_dir": str(output_path),
            "individual_tracks": track_files,
            "multichannel_file": multichannel_filename,
            "metadata_file": "metadata.json"
        }

    def _serialize_marker_for_export(self, marker) -> Dict:
        """
        Serialize marker to dict for JSON export

        Args:
            marker: Marker object or dict

        Returns:
            Dict representation of marker
        """
        if isinstance(marker, dict):
            return marker
        else:
            # Convert Marker object to dict
            return {
                "time_ms": marker.time_ms,
                "type": marker.type,
                "name": marker.name,
                "prompt_data": marker.prompt_data,
                "asset_slot": getattr(marker, 'asset_slot', ''),
                "asset_file": marker.asset_file,
                "asset_id": getattr(marker, 'asset_id', None),
                "status": getattr(marker, 'status', 'not yet generated'),
                "assigned_track": getattr(marker, 'assigned_track', ''),
                "assigned_channels": getattr(marker, 'assigned_channels', [])
            }
