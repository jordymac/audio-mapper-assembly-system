#!/usr/bin/env python3
"""
Audio Mapper - Maps audio files to timecode positions and creates JSON templates.

This tool scans a directory of audio files and creates a JSON mapping template
that defines how audio segments should be positioned in the final assembly.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import click
import librosa
import soundfile as sf


def analyze_audio_file(file_path: Path) -> Dict:
    """
    Analyze an audio file and extract metadata.

    Args:
        file_path: Path to the audio file

    Returns:
        Dictionary containing audio metadata
    """
    y, sr = librosa.load(file_path, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)

    return {
        "file": str(file_path.name),
        "duration": duration,
        "sample_rate": sr,
        "channels": 1 if y.ndim == 1 else y.shape[0],
    }


def create_audio_map(
    input_dir: Path,
    output_file: Path,
    timecode_offset: float = 0.0
) -> Dict:
    """
    Create an audio mapping template from a directory of audio files.

    Args:
        input_dir: Directory containing audio files
        output_file: Path to save the JSON template
        timecode_offset: Starting timecode offset in seconds

    Returns:
        Dictionary representing the audio map
    """
    audio_extensions = {'.wav', '.mp3', '.flac', '.aiff', '.m4a'}
    audio_files = [
        f for f in input_dir.iterdir()
        if f.suffix.lower() in audio_extensions
    ]

    audio_map = {
        "version": "1.0",
        "segments": [],
        "metadata": {
            "source_directory": str(input_dir),
            "total_files": len(audio_files),
        }
    }

    current_timecode = timecode_offset

    for audio_file in sorted(audio_files):
        file_info = analyze_audio_file(audio_file)

        segment = {
            "file": file_info["file"],
            "start_timecode": current_timecode,
            "duration": file_info["duration"],
            "end_timecode": current_timecode + file_info["duration"],
            "sample_rate": file_info["sample_rate"],
            "channels": file_info["channels"],
        }

        audio_map["segments"].append(segment)
        current_timecode += file_info["duration"]

    # Save to JSON file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(audio_map, f, indent=2)

    return audio_map


@click.command()
@click.option(
    '--input', '-i',
    'input_dir',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help='Directory containing audio files to map'
)
@click.option(
    '--output', '-o',
    'output_file',
    type=click.Path(path_type=Path),
    required=True,
    help='Output JSON template file path'
)
@click.option(
    '--offset',
    type=float,
    default=0.0,
    help='Starting timecode offset in seconds'
)
def main(input_dir: Path, output_file: Path, offset: float):
    """Map audio files to timecode positions and create a JSON template."""
    click.echo(f"Scanning audio files in: {input_dir}")

    audio_map = create_audio_map(input_dir, output_file, offset)

    click.echo(f"\nCreated audio map with {len(audio_map['segments'])} segments")
    click.echo(f"Output saved to: {output_file}")


if __name__ == '__main__':
    main()
