#!/usr/bin/env python3
"""
Audio Assembler - Assembles audio files based on mapping templates.

This tool reads a JSON mapping template and assembles the referenced audio files
into a single output file with proper timecode alignment.
"""

import json
from pathlib import Path
from typing import Dict, List

import click
import numpy as np
from pydub import AudioSegment
from tqdm import tqdm


def load_template(template_path: Path) -> Dict:
    """
    Load an audio mapping template from JSON.

    Args:
        template_path: Path to the JSON template file

    Returns:
        Dictionary containing the template data
    """
    with open(template_path, 'r') as f:
        return json.load(f)


def assemble_audio(
    template: Dict,
    source_dir: Path,
    output_file: Path,
    format: str = 'wav'
) -> None:
    """
    Assemble audio files according to the template.

    Args:
        template: Audio mapping template dictionary
        source_dir: Directory containing source audio files
        output_file: Path to save the assembled audio
        format: Output audio format (wav, mp3, etc.)
    """
    segments = template.get('segments', [])

    if not segments:
        raise ValueError("No segments found in template")

    # Calculate total duration
    total_duration_ms = int(segments[-1]['end_timecode'] * 1000)

    # Create silent base track
    assembled = AudioSegment.silent(duration=total_duration_ms)

    click.echo(f"Assembling {len(segments)} audio segments...")

    for segment in tqdm(segments, desc="Processing segments"):
        file_path = source_dir / segment['file']

        if not file_path.exists():
            click.echo(f"\nWarning: File not found: {file_path}", err=True)
            continue

        # Load audio segment
        audio = AudioSegment.from_file(str(file_path))

        # Calculate position in milliseconds
        start_ms = int(segment['start_timecode'] * 1000)

        # Overlay the audio at the specified timecode
        assembled = assembled.overlay(audio, position=start_ms)

    # Export the assembled audio
    output_file.parent.mkdir(parents=True, exist_ok=True)
    assembled.export(str(output_file), format=format)

    click.echo(f"\nAssembly complete: {output_file}")
    click.echo(f"Total duration: {len(assembled) / 1000:.2f} seconds")


@click.command()
@click.option(
    '--template', '-t',
    'template_path',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help='JSON template file to use for assembly'
)
@click.option(
    '--source', '-s',
    'source_dir',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help='Directory containing source audio files (default: uses template metadata)'
)
@click.option(
    '--output', '-o',
    'output_file',
    type=click.Path(path_type=Path),
    required=True,
    help='Output audio file path'
)
@click.option(
    '--format', '-f',
    default='wav',
    help='Output audio format (wav, mp3, etc.)'
)
def main(
    template_path: Path,
    source_dir: Optional[Path],
    output_file: Path,
    format: str
):
    """Assemble audio files based on a JSON mapping template."""
    template = load_template(template_path)

    # Use source directory from template metadata if not specified
    if source_dir is None:
        source_dir = Path(template['metadata']['source_directory'])

    click.echo(f"Loading template: {template_path}")
    click.echo(f"Source directory: {source_dir}")

    assemble_audio(template, source_dir, output_file, format)


if __name__ == '__main__':
    main()
