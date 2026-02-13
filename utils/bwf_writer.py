"""
BWF Writer - Broadcast Wave Format file creation with bext + iXML chunks

Creates self-describing WAV files with embedded timecode (bext) and rich
metadata (iXML) for automatic timeline placement in NLEs/DAWs.

Follows:
- EBU Tech 3285 (BWF bext chunk)
- iXML specification v3.00
"""

import struct
import tempfile
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydub import AudioSegment


BWF_SAMPLE_RATE = 48000
BWF_BIT_DEPTH = 24


@dataclass
class BWFMetadata:
    """All fields needed for bext + iXML chunks"""

    # bext fields
    description: str = ""
    originator: str = "Audio Mapper"
    originator_reference: str = ""
    origination_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    origination_time: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    time_reference: int = 0  # Sample position on timeline

    # iXML fields
    project_name: str = ""
    scene: str = ""  # template_id
    take: int = 1  # version number
    note: str = ""
    track_name: str = ""
    marker_type: str = ""
    template_id: str = ""
    timestamp_ms: int = 0
    duration_ms: int = 0
    asset_id: str = ""
    sample_rate: int = BWF_SAMPLE_RATE


def create_bext_data(metadata: BWFMetadata) -> bytes:
    """
    Build the 602-byte bext chunk body per EBU Tech 3285.

    Layout:
        Description       256 bytes  ASCII
        Originator         32 bytes  ASCII
        OriginatorReference 32 bytes ASCII
        OriginationDate    10 bytes  ASCII (YYYY-MM-DD)
        OriginationTime     8 bytes  ASCII (HH:MM:SS)
        TimeReference       8 bytes  uint64 LE
        Version             2 bytes  uint16 LE (= 1)
        UMID               64 bytes  zeros
        Reserved          190 bytes  zeros
    """
    def pad_ascii(text: str, length: int) -> bytes:
        encoded = text.encode('ascii', errors='replace')[:length]
        return encoded.ljust(length, b'\x00')

    data = bytearray()
    data += pad_ascii(metadata.description, 256)
    data += pad_ascii(metadata.originator, 32)
    data += pad_ascii(metadata.originator_reference, 32)
    data += pad_ascii(metadata.origination_date, 10)
    data += pad_ascii(metadata.origination_time, 8)
    data += struct.pack('<Q', metadata.time_reference)  # uint64 LE
    data += struct.pack('<H', 1)  # Version = 1
    data += b'\x00' * 64   # UMID (unused)
    data += b'\x00' * 190  # Reserved

    return bytes(data)


def create_ixml_data(metadata: BWFMetadata) -> bytes:
    """
    Build iXML chunk body as UTF-8 XML string.

    Follows iXML spec v3.00 with custom USER fields for
    application-specific data.
    """
    root = ET.Element("BWFXML")

    ET.SubElement(root, "IXML_VERSION").text = "3.00"
    ET.SubElement(root, "PROJECT").text = metadata.project_name
    ET.SubElement(root, "SCENE").text = metadata.scene
    ET.SubElement(root, "TAKE").text = str(metadata.take)
    ET.SubElement(root, "NOTE").text = metadata.note

    # Track list
    track_list = ET.SubElement(root, "TRACK_LIST")
    ET.SubElement(track_list, "TRACK_COUNT").text = "1"
    track = ET.SubElement(track_list, "TRACK")
    ET.SubElement(track, "CHANNEL_INDEX").text = "1"
    ET.SubElement(track, "NAME").text = metadata.track_name

    # Speed info
    speed = ET.SubElement(root, "SPEED")
    ET.SubElement(speed, "MASTER_SPEED").text = str(metadata.sample_rate)

    # Custom user fields
    user = ET.SubElement(root, "USER")
    ET.SubElement(user, "MARKER_TYPE").text = metadata.marker_type
    ET.SubElement(user, "TEMPLATE_ID").text = metadata.template_id
    ET.SubElement(user, "TIMESTAMP_MS").text = str(metadata.timestamp_ms)
    ET.SubElement(user, "DURATION_MS").text = str(metadata.duration_ms)
    ET.SubElement(user, "ASSET_ID").text = metadata.asset_id

    xml_str = ET.tostring(root, encoding='unicode', xml_declaration=True)
    return xml_str.encode('utf-8')


def _pad_to_even(data: bytes) -> bytes:
    """Pad data to even byte boundary (RIFF word alignment)."""
    if len(data) % 2 != 0:
        return data + b'\x00'
    return data


def _make_chunk(chunk_id: bytes, data: bytes) -> bytes:
    """Create a RIFF chunk: 4-byte ID + 4-byte size (LE) + data + padding."""
    padded = _pad_to_even(data)
    return chunk_id + struct.pack('<I', len(data)) + padded


def write_bwf(audio_segment: AudioSegment, output_path: str, metadata: BWFMetadata) -> bool:
    """
    Write an AudioSegment as a BWF file with bext and iXML chunks.

    Process:
    1. Resample to 48kHz
    2. Export to temp WAV as 24-bit PCM
    3. Parse RIFF chunks from temp WAV
    4. Rebuild RIFF with bext + iXML injected before data chunk
    5. Write final BWF file

    Args:
        audio_segment: pydub AudioSegment to export
        output_path: Destination file path
        metadata: BWFMetadata with timecode and descriptive fields

    Returns:
        True on success, False on failure
    """
    temp_path = None
    try:
        # 1. Resample to 48kHz if needed
        if audio_segment.frame_rate != BWF_SAMPLE_RATE:
            audio_segment = audio_segment.set_frame_rate(BWF_SAMPLE_RATE)

        # 2. Export to temp WAV as 24-bit PCM
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(temp_fd)

        audio_segment.export(
            temp_path,
            format="wav",
            parameters=["-acodec", "pcm_s24le"]
        )

        # 3. Read temp WAV and parse RIFF chunks
        with open(temp_path, 'rb') as f:
            wav_bytes = f.read()

        if wav_bytes[:4] != b'RIFF' or wav_bytes[8:12] != b'WAVE':
            print(f"  ✗ Invalid WAV file from pydub export")
            return False

        # Parse existing chunks (skip RIFF header: 12 bytes)
        chunks = []
        pos = 12
        fmt_chunk_data = None
        data_chunk_data = None

        while pos < len(wav_bytes):
            if pos + 8 > len(wav_bytes):
                break
            chunk_id = wav_bytes[pos:pos + 4]
            chunk_size = struct.unpack('<I', wav_bytes[pos + 4:pos + 8])[0]
            chunk_data = wav_bytes[pos + 8:pos + 8 + chunk_size]

            if chunk_id == b'fmt ':
                fmt_chunk_data = chunk_data
            elif chunk_id == b'data':
                data_chunk_data = chunk_data
            else:
                # Keep other chunks (e.g., LIST)
                chunks.append((chunk_id, chunk_data))

            # Advance past chunk (word-aligned)
            pos += 8 + chunk_size
            if chunk_size % 2 != 0:
                pos += 1

        if fmt_chunk_data is None or data_chunk_data is None:
            print(f"  ✗ Missing fmt or data chunk in temp WAV")
            return False

        # 4. Build new RIFF: fmt → bext → iXML → (other chunks) → data
        bext_data = create_bext_data(metadata)
        ixml_data = create_ixml_data(metadata)

        body = bytearray()
        body += b'WAVE'
        body += _make_chunk(b'fmt ', fmt_chunk_data)
        body += _make_chunk(b'bext', bext_data)
        body += _make_chunk(b'iXML', ixml_data)

        for chunk_id, chunk_data in chunks:
            body += _make_chunk(chunk_id, chunk_data)

        body += _make_chunk(b'data', data_chunk_data)

        # 5. Write final BWF file with correct RIFF size
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(b'RIFF')
            f.write(struct.pack('<I', len(body)))
            f.write(body)

        return True

    except Exception as e:
        print(f"  ✗ BWF write failed: {e}")
        return False

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
