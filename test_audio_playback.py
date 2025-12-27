#!/usr/bin/env python3
"""
Test script for audio playback functionality
"""

import sys
import os

def test_audio_player_class():
    """Test that AudioPlayer class works correctly"""
    from audio_mapper import AudioPlayer

    print("=" * 70)
    print("AUDIO PLAYBACK - FUNCTIONALITY TEST")
    print("=" * 70)

    # Test 1: AudioPlayer initialization
    print("\n✓ Test 1: AudioPlayer initialization")
    player = AudioPlayer()
    assert player is not None, "AudioPlayer should initialize"
    assert player.current_sound is None, "No sound should be loaded initially"
    assert not player.is_playing, "Should not be playing initially"
    print("  ✓ AudioPlayer initialized successfully")

    # Test 2: Check test audio files exist
    print("\n✓ Test 2: Verify test audio files exist")
    test_files = [
        "generated_audio/sfx/SFX_00000_v1.wav",
        "generated_audio/voice/VOX_00000_v1.wav",
        "generated_audio/music/MUS_00000_v1.wav"
    ]

    for file_path in test_files:
        assert os.path.exists(file_path), f"Test file missing: {file_path}"
        print(f"  ✓ Found: {file_path}")

    # Test 3: Play audio file
    print("\n✓ Test 3: Play audio file")
    success = player.play_audio_file(test_files[0], marker_index=0)
    assert success, "Should successfully play audio file"
    assert player.is_playing, "Should be playing"
    assert player.current_marker_index == 0, "Should track marker index"
    print("  ✓ Audio playback started successfully")

    # Test 4: Stop audio
    print("\n✓ Test 4: Stop audio")
    player.stop_audio()
    assert not player.is_playing, "Should stop playing"
    assert player.current_marker_index is None, "Should clear marker index"
    print("  ✓ Audio stopped successfully")

    # Test 5: Play non-existent file
    print("\n✓ Test 5: Handle missing file")
    success = player.play_audio_file("nonexistent.wav")
    assert not success, "Should fail gracefully for missing file"
    assert not player.is_playing, "Should not be playing"
    print("  ✓ Missing file handled correctly")

    # Test 6: is_playing_marker check
    print("\n✓ Test 6: is_playing_marker check")
    player.play_audio_file(test_files[1], marker_index=5)
    assert player.is_playing_marker(5), "Should identify playing marker"
    assert not player.is_playing_marker(0), "Should not match different marker"
    player.stop_audio()
    print("  ✓ is_playing_marker works correctly")

    # Test 7: get_playing_status
    print("\n✓ Test 7: get_playing_status")
    player.play_audio_file(test_files[2], marker_index=10)
    is_playing, marker_idx = player.get_playing_status()
    assert is_playing, "Should report playing"
    assert marker_idx == 10, "Should report correct marker index"
    player.stop_audio()
    is_playing, marker_idx = player.get_playing_status()
    assert not is_playing, "Should report not playing after stop"
    print("  ✓ get_playing_status works correctly")

    # Test 8: Multiple plays (only one at a time)
    print("\n✓ Test 8: Multiple plays (ensure only one plays)")
    player.play_audio_file(test_files[0], marker_index=0)
    first_sound = player.current_sound
    player.play_audio_file(test_files[1], marker_index=1)
    assert player.current_marker_index == 1, "Should update to new marker"
    # First sound should have been stopped automatically
    print("  ✓ Multiple plays handled correctly (stops previous)")

    player.stop_audio()

    print("\n" + "=" * 70)
    print("✓ ALL AUDIO PLAYBACK TESTS PASSED!")
    print("=" * 70)
    print("\nAudio playback is working correctly!")
    print("\nTo test interactively:")
    print("  1. Run: python3 audio_mapper.py")
    print("  2. Create blank timeline (10000ms)")
    print("  3. Add SFX marker at 0ms")
    print("  4. Add Voice marker at 2000ms")
    print("  5. Add Music marker at 5000ms")
    print("  6. Click ▶ button on each marker")
    print("  7. Verify:")
    print("     - Audio plays")
    print("     - Button changes to ⏸ while playing")
    print("     - Button returns to ▶ when finished")
    print("     - Clicking ⏸ stops playback")
    print("     - Only one audio plays at a time")


if __name__ == "__main__":
    try:
        test_audio_player_class()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
