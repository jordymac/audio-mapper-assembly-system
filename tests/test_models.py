#!/usr/bin/env python3
"""Quick test to verify models.py works correctly"""

from core.models import (
    Marker, AudioVersion, MarkerType, MarkerStatus,
    SFXPromptData, VoicePromptData, MusicPromptData, MusicSection,
    create_marker
)


def test_sfx_marker():
    """Test SFX marker creation"""
    marker = create_marker(
        time_ms=5000,
        marker_type="sfx",
        name="Door Slam",
        asset_slot="sfx_0",
        asset_file="SFX_00000_v1.mp3"
    )

    assert marker.time_ms == 5000
    assert marker.type == "sfx"
    assert marker.name == "Door Slam"
    assert len(marker.versions) == 1
    assert marker.versions[0].version == 1

    # Test to_dict/from_dict round trip
    marker_dict = marker.to_dict()
    marker2 = Marker.from_dict(marker_dict)
    assert marker2.time_ms == marker.time_ms
    assert marker2.type == marker.type

    print("✓ SFX marker test passed")


def test_voice_marker():
    """Test voice marker with prompt data"""
    prompt_data = VoicePromptData(
        voice_profile="narrator",
        text="Hello world"
    ).to_dict()

    marker = create_marker(
        time_ms=10000,
        marker_type="voice",
        prompt_data=prompt_data,
        asset_file="VOX_00000_v1.mp3"
    )

    typed_prompt = marker.get_typed_prompt_data()
    assert isinstance(typed_prompt, VoicePromptData)
    assert typed_prompt.voice_profile == "narrator"
    assert typed_prompt.text == "Hello world"

    print("✓ Voice marker test passed")


def test_music_marker():
    """Test music marker with sections"""
    section = MusicSection(
        duration_s=30.0,
        positiveStyles=["epic", "orchestral"],
        negativeStyles=["calm"]
    )

    prompt_data = MusicPromptData(
        positiveGlobalStyles=["cinematic"],
        negativeGlobalStyles=["jazz"],
        sections=[section]
    ).to_dict()

    marker = create_marker(
        time_ms=20000,
        marker_type="music",
        prompt_data=prompt_data,
        asset_file="MUS_00000_v1.mp3"
    )

    typed_prompt = marker.get_typed_prompt_data()
    assert isinstance(typed_prompt, MusicPromptData)
    assert len(typed_prompt.sections) == 1
    assert typed_prompt.sections[0].duration_s == 30.0

    print("✓ Music marker test passed")


def test_marker_copy():
    """Test marker deep copy"""
    marker1 = create_marker(
        time_ms=1000,
        marker_type="sfx",
        name="Original"
    )

    marker2 = marker1.copy()
    marker2.name = "Copy"

    assert marker1.name == "Original"
    assert marker2.name == "Copy"

    print("✓ Marker copy test passed")


def test_version_management():
    """Test version tracking"""
    marker = create_marker(
        time_ms=5000,
        marker_type="sfx",
        asset_file="SFX_00000_v1.mp3"
    )

    # Get current version
    current = marker.get_current_version()
    assert current is not None
    assert current.version == 1

    # Add a new version
    new_version = AudioVersion(
        version=2,
        asset_file="SFX_00000_v2.mp3",
        status=MarkerStatus.GENERATED.value
    )
    marker.versions.append(new_version)
    marker.current_version = 2

    current = marker.get_current_version()
    assert current.version == 2

    print("✓ Version management test passed")


if __name__ == "__main__":
    print("Testing models.py...")
    test_sfx_marker()
    test_voice_marker()
    test_music_marker()
    test_marker_copy()
    test_version_management()
    print("\n✅ All tests passed!")
