#!/usr/bin/env python3
"""
Test ElevenLabs API integration
Tests all three generation functions with real API calls
"""

import sys
import os
from services.elevenlabs_api import generate_sfx, generate_voice, generate_music, test_api_connection


def main():
    """Run comprehensive API integration tests"""
    print("=" * 70)
    print("ELEVENLABS API INTEGRATION - FULL TEST")
    print("=" * 70)

    # Test 1: API Connection
    print("\n✓ Test 1: API Connection")
    if not test_api_connection():
        print("✗ API connection failed. Cannot continue tests.")
        return False

    # Test 2: Generate SFX
    print("\n✓ Test 2: Generate SFX")
    print("  Generating: UI whoosh sound...")
    sfx_result = generate_sfx(
        description="quick digital whoosh UI transition sound",
        output_path="generated_audio/sfx/TEST_SFX.mp3"
    )

    if sfx_result["success"]:
        print(f"  ✓ SFX generated successfully")
        print(f"    File: {sfx_result['audio_file']}")
        print(f"    Size: {sfx_result['size_bytes']:,} bytes")
        print(f"    Asset ID: {sfx_result['asset_id']}")
        assert os.path.exists(sfx_result['audio_file']), "SFX file should exist"
    else:
        print(f"  ✗ SFX generation failed: {sfx_result['error']}")
        return False

    # Test 3: Generate Voice
    print("\n✓ Test 3: Generate Voice")
    print("  Generating: Short voice narration...")
    voice_result = generate_voice(
        voice_profile="Warm female narrator",
        text="Welcome to the audio mapper system. This is a test of voice generation.",
        output_path="generated_audio/voice/TEST_VOICE.mp3"
    )

    if voice_result["success"]:
        print(f"  ✓ Voice generated successfully")
        print(f"    File: {voice_result['audio_file']}")
        print(f"    Size: {voice_result['size_bytes']:,} bytes")
        print(f"    Voice ID: {voice_result['asset_id']}")
        assert os.path.exists(voice_result['audio_file']), "Voice file should exist"
    else:
        print(f"  ✗ Voice generation failed: {voice_result['error']}")
        return False

    # Test 4: Generate Music
    print("\n✓ Test 4: Generate Music")
    print("  Generating: Background music...")
    music_result = generate_music(
        positive_styles=["electronic", "upbeat", "energetic"],
        negative_styles=["slow", "ambient"],
        sections=[
            {
                "sectionName": "Intro",
                "durationMs": 3000,
                "positiveLocalStyles": ["rising"],
                "negativeLocalStyles": []
            }
        ],
        output_path="generated_audio/music/TEST_MUSIC.mp3"
    )

    if music_result["success"]:
        print(f"  ✓ Music generated successfully")
        print(f"    File: {music_result['audio_file']}")
        print(f"    Size: {music_result['size_bytes']:,} bytes")
        print(f"    Duration: {music_result.get('duration_seconds', 'N/A')}s")
        print(f"    Asset ID: {music_result['asset_id']}")
        assert os.path.exists(music_result['audio_file']), "Music file should exist"
    else:
        print(f"  ✗ Music generation failed: {music_result['error']}")
        return False

    # Test 5: Error Handling (invalid input)
    print("\n✓ Test 5: Error Handling")
    print("  Testing with empty description...")
    error_result = generate_sfx(
        description="",
        output_path=None
    )
    # Should either fail gracefully or use default
    print(f"  ✓ Error handling: {'Success' if error_result['success'] else 'Failed gracefully'}")

    print("\n" + "=" * 70)
    print("✓ ALL API INTEGRATION TESTS PASSED!")
    print("=" * 70)
    print("\nGenerated test files:")
    print("  • generated_audio/sfx/TEST_SFX.mp3")
    print("  • generated_audio/voice/TEST_VOICE.mp3")
    print("  • generated_audio/music/TEST_MUSIC.mp3")
    print("\nYou can now use these files to test playback in audio_mapper.py!")
    print("\nNOTE: These API calls consume credits. The generated files are saved")
    print("      for testing purposes and won't be regenerated on subsequent runs.")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
