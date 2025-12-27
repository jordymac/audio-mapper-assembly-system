#!/usr/bin/env python3
"""
Create test audio files for testing playback
Generates simple tone audio files
"""

import numpy as np
import wave
import os

def create_test_audio(filename, duration_ms=1000, frequency=440):
    """
    Create a simple sine wave audio file

    Args:
        filename: Output filename
        duration_ms: Duration in milliseconds
        frequency: Frequency in Hz
    """
    sample_rate = 44100
    duration_sec = duration_ms / 1000.0
    num_samples = int(sample_rate * duration_sec)

    # Generate sine wave
    t = np.linspace(0, duration_sec, num_samples, False)
    audio_data = np.sin(frequency * 2 * np.pi * t)

    # Apply fade in/out to avoid clicks
    fade_samples = int(sample_rate * 0.01)  # 10ms fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    audio_data[:fade_samples] *= fade_in
    audio_data[-fade_samples:] *= fade_out

    # Scale to 16-bit range
    audio_data = (audio_data * 32767).astype(np.int16)

    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    print(f"✓ Created: {filename} ({duration_ms}ms, {frequency}Hz)")


def main():
    """Create test audio files"""
    print("=" * 70)
    print("CREATING TEST AUDIO FILES")
    print("=" * 70)

    # Create SFX test files (short beeps)
    create_test_audio("generated_audio/sfx/SFX_00000_v1.wav", duration_ms=500, frequency=880)
    create_test_audio("generated_audio/sfx/SFX_00001_v1.wav", duration_ms=300, frequency=1320)

    # Create Voice test files (mid-frequency tones)
    create_test_audio("generated_audio/voice/VOX_00000_v1.wav", duration_ms=2000, frequency=440)
    create_test_audio("generated_audio/voice/VOX_00001_v1.wav", duration_ms=1500, frequency=523)

    # Create Music test files (longer, lower tones)
    create_test_audio("generated_audio/music/MUS_00000_v1.wav", duration_ms=3000, frequency=261)
    create_test_audio("generated_audio/music/MUS_00001_v1.wav", duration_ms=4000, frequency=329)

    print("\n" + "=" * 70)
    print("✓ ALL TEST AUDIO FILES CREATED")
    print("=" * 70)
    print("\nTest files created in generated_audio/")
    print("  • SFX: Short beeps (500-300ms)")
    print("  • Voice: Mid tones (2000-1500ms)")
    print("  • Music: Longer tones (3000-4000ms)")
    print("\nYou can now test playback in audio_mapper.py!")


if __name__ == "__main__":
    main()
