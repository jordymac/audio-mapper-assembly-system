"""Tests for utils/bwf_writer.py — BWF file creation with bext + iXML chunks"""

import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from pydub import AudioSegment

from utils.bwf_writer import (
    BWFMetadata,
    BWF_SAMPLE_RATE,
    create_bext_data,
    create_ixml_data,
    write_bwf,
)


@pytest.fixture
def sample_metadata():
    """A fully-populated BWFMetadata for testing."""
    return BWFMetadata(
        description="Test click sound",
        originator="Audio Mapper",
        originator_reference="DM01",
        origination_date="2026-02-08",
        origination_time="14:30:00",
        time_reference=96000,  # 2000ms @ 48kHz
        project_name="Indoor Routine",
        scene="DM01",
        take=2,
        note="Crisp attack version",
        track_name="SFX/click_v2",
        marker_type="sfx",
        template_id="DM01",
        timestamp_ms=2000,
        duration_ms=250,
        asset_id="gen_abc123",
        sample_rate=48000,
    )


@pytest.fixture
def silent_audio():
    """A 1-second silent stereo AudioSegment at 44100 Hz."""
    return AudioSegment.silent(duration=1000, frame_rate=44100)


class TestCreateBextData:
    def test_length_is_602_bytes(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        assert len(data) == 602

    def test_description_field(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        description = data[:256].rstrip(b'\x00').decode('ascii')
        assert description == "Test click sound"

    def test_originator_field(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        originator = data[256:288].rstrip(b'\x00').decode('ascii')
        assert originator == "Audio Mapper"

    def test_originator_reference_field(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        orig_ref = data[288:320].rstrip(b'\x00').decode('ascii')
        assert orig_ref == "DM01"

    def test_origination_date(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        date_str = data[320:330].rstrip(b'\x00').decode('ascii')
        assert date_str == "2026-02-08"

    def test_origination_time(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        time_str = data[330:338].rstrip(b'\x00').decode('ascii')
        assert time_str == "14:30:00"

    def test_time_reference(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        time_ref = struct.unpack('<Q', data[338:346])[0]
        assert time_ref == 96000

    def test_version_is_one(self, sample_metadata):
        data = create_bext_data(sample_metadata)
        version = struct.unpack('<H', data[346:348])[0]
        assert version == 1

    def test_truncates_long_description(self):
        meta = BWFMetadata(description="A" * 300)
        data = create_bext_data(meta)
        assert len(data) == 602
        # Description capped at 256 bytes
        assert data[:256] == b'A' * 256


class TestCreateIxmlData:
    def test_returns_valid_xml(self, sample_metadata):
        data = create_ixml_data(sample_metadata)
        # Should parse without error
        root = ET.fromstring(data)
        assert root.tag == "BWFXML"

    def test_required_elements_present(self, sample_metadata):
        data = create_ixml_data(sample_metadata)
        root = ET.fromstring(data)

        assert root.find("IXML_VERSION").text == "3.00"
        assert root.find("PROJECT").text == "Indoor Routine"
        assert root.find("SCENE").text == "DM01"
        assert root.find("TAKE").text == "2"
        assert root.find("NOTE").text == "Crisp attack version"

    def test_track_list(self, sample_metadata):
        data = create_ixml_data(sample_metadata)
        root = ET.fromstring(data)

        track_list = root.find("TRACK_LIST")
        assert track_list is not None
        assert track_list.find("TRACK_COUNT").text == "1"
        assert track_list.find("TRACK/NAME").text == "SFX/click_v2"

    def test_speed_element(self, sample_metadata):
        data = create_ixml_data(sample_metadata)
        root = ET.fromstring(data)

        speed = root.find("SPEED")
        assert speed is not None
        assert speed.find("MASTER_SPEED").text == "48000"

    def test_user_fields(self, sample_metadata):
        data = create_ixml_data(sample_metadata)
        root = ET.fromstring(data)

        user = root.find("USER")
        assert user is not None
        assert user.find("MARKER_TYPE").text == "sfx"
        assert user.find("TEMPLATE_ID").text == "DM01"
        assert user.find("TIMESTAMP_MS").text == "2000"
        assert user.find("DURATION_MS").text == "250"
        assert user.find("ASSET_ID").text == "gen_abc123"


class TestTimeReferenceCalculation:
    """Verify ms → sample count conversion at 48kHz."""

    @pytest.mark.parametrize("time_ms, expected_samples", [
        (0, 0),
        (1000, 48000),
        (2000, 96000),
        (500, 24000),
        (150, 7200),
    ])
    def test_conversion(self, time_ms, expected_samples):
        result = int((time_ms / 1000.0) * BWF_SAMPLE_RATE)
        assert result == expected_samples


class TestWriteBwf:
    def test_creates_valid_riff_file(self, silent_audio, sample_metadata, tmp_path):
        out = str(tmp_path / "test.wav")
        result = write_bwf(silent_audio, out, sample_metadata)

        assert result is True
        assert Path(out).exists()

        with open(out, 'rb') as f:
            header = f.read(12)
        assert header[:4] == b'RIFF'
        assert header[8:12] == b'WAVE'

    def test_contains_bext_chunk(self, silent_audio, sample_metadata, tmp_path):
        out = str(tmp_path / "test.wav")
        write_bwf(silent_audio, out, sample_metadata)

        with open(out, 'rb') as f:
            data = f.read()
        assert b'bext' in data

    def test_contains_ixml_chunk(self, silent_audio, sample_metadata, tmp_path):
        out = str(tmp_path / "test.wav")
        write_bwf(silent_audio, out, sample_metadata)

        with open(out, 'rb') as f:
            data = f.read()
        assert b'iXML' in data

    def test_contains_data_chunk(self, silent_audio, sample_metadata, tmp_path):
        out = str(tmp_path / "test.wav")
        write_bwf(silent_audio, out, sample_metadata)

        with open(out, 'rb') as f:
            data = f.read()
        assert b'data' in data

    def test_contains_fmt_chunk(self, silent_audio, sample_metadata, tmp_path):
        out = str(tmp_path / "test.wav")
        write_bwf(silent_audio, out, sample_metadata)

        with open(out, 'rb') as f:
            data = f.read()
        assert b'fmt ' in data

    def test_riff_size_is_correct(self, silent_audio, sample_metadata, tmp_path):
        out = str(tmp_path / "test.wav")
        write_bwf(silent_audio, out, sample_metadata)

        with open(out, 'rb') as f:
            f.read(4)  # skip 'RIFF'
            riff_size = struct.unpack('<I', f.read(4))[0]
            f.seek(0, 2)
            file_size = f.tell()

        # RIFF size = file_size - 8 (RIFF header)
        assert riff_size == file_size - 8

    def test_resamples_to_48khz(self, tmp_path, sample_metadata):
        """Input at 22050 Hz should be resampled to 48000 Hz in the BWF."""
        audio = AudioSegment.silent(duration=500, frame_rate=22050)
        out = str(tmp_path / "test.wav")
        write_bwf(audio, out, sample_metadata)

        # Parse fmt chunk to check sample rate
        with open(out, 'rb') as f:
            data = f.read()

        # Find fmt chunk
        fmt_pos = data.index(b'fmt ')
        fmt_size = struct.unpack('<I', data[fmt_pos + 4:fmt_pos + 8])[0]
        fmt_data = data[fmt_pos + 8:fmt_pos + 8 + fmt_size]
        # Sample rate is at offset 4 in fmt chunk (after AudioFormat + NumChannels)
        sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
        assert sample_rate == 48000

    def test_bext_time_reference_in_file(self, silent_audio, sample_metadata, tmp_path):
        """Verify TimeReference is readable from the bext chunk in the output file."""
        out = str(tmp_path / "test.wav")
        write_bwf(silent_audio, out, sample_metadata)

        with open(out, 'rb') as f:
            data = f.read()

        bext_pos = data.index(b'bext')
        bext_size = struct.unpack('<I', data[bext_pos + 4:bext_pos + 8])[0]
        bext_body = data[bext_pos + 8:bext_pos + 8 + bext_size]

        # TimeReference is at offset 338 in the bext body
        time_ref = struct.unpack('<Q', bext_body[338:346])[0]
        assert time_ref == 96000

    def test_creates_parent_directories(self, silent_audio, sample_metadata, tmp_path):
        out = str(tmp_path / "nested" / "dir" / "test.wav")
        result = write_bwf(silent_audio, out, sample_metadata)
        assert result is True
        assert Path(out).exists()

    def test_mono_audio(self, sample_metadata, tmp_path):
        """Mono input should produce a valid BWF."""
        audio = AudioSegment.silent(duration=500, frame_rate=48000).set_channels(1)
        out = str(tmp_path / "mono.wav")
        result = write_bwf(audio, out, sample_metadata)
        assert result is True
        assert Path(out).exists()
