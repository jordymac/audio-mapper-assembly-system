#!/usr/bin/env python3
"""
ElevenLabs API Integration
Handles audio generation for SFX, Voice, and Music markers
"""

import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings
from pathlib import Path
from datetime import datetime

# Load environment variables from .env.local
load_dotenv('.env.local')

# Initialize ElevenLabs client
API_KEY = os.getenv('ELEVENLABS_API_KEY')
if not API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not found in .env.local")

client = ElevenLabs(api_key=API_KEY)


def generate_sfx(description: str, output_path: str = None) -> dict:
    """
    Generate sound effect from text description

    Args:
        description: Text description of the sound effect
        output_path: Optional path to save the audio file

    Returns:
        dict: {
            "success": bool,
            "audio_file": str (path to saved file),
            "asset_id": str (ElevenLabs generation ID),
            "error": str (if failed)
        }
    """
    try:
        print(f"🔄 Generating SFX: {description[:50]}...")

        # Generate sound effect
        # Note: ElevenLabs sound effects API
        audio_generator = client.text_to_sound_effects.convert(
            text=description,
            duration_seconds=None,  # Auto-determine duration
            prompt_influence=0.3    # Balance between prompt and quality
        )

        # Collect audio bytes
        audio_bytes = b""
        for chunk in audio_generator:
            if isinstance(chunk, bytes):
                audio_bytes += chunk

        if not audio_bytes:
            return {
                "success": False,
                "error": "No audio data received from API"
            }

        # Save to file
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"✓ SFX saved: {output_path}")

        return {
            "success": True,
            "audio_bytes": audio_bytes,
            "audio_file": output_path if output_path else None,
            "asset_id": f"sfx_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "size_bytes": len(audio_bytes)
        }

    except Exception as e:
        print(f"✗ SFX generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def generate_voice(voice_profile: str, text: str, output_path: str = None) -> dict:
    """
    Generate voice narration from text

    Args:
        voice_profile: Description of voice characteristics (optional)
        text: Text to speak
        output_path: Optional path to save the audio file

    Returns:
        dict: {
            "success": bool,
            "audio_file": str (path to saved file),
            "asset_id": str (voice ID used),
            "error": str (if failed)
        }
    """
    try:
        print(f"🔄 Generating Voice: {text[:50]}...")

        # Use default voice (you can customize this)
        # Popular voice IDs:
        # - "21m00Tcm4TlvDq8ikWAM" - Rachel (calm, clear)
        # - "EXAVITQu4vr4xnSDxMaL" - Bella (soft, friendly)
        # - "ErXwobaYiN019PkySvjV" - Antoni (well-rounded male)

        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel

        # Generate speech
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            optimize_streaming_latency=0,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )

        # Collect audio bytes
        audio_bytes = b""
        for chunk in audio_generator:
            if isinstance(chunk, bytes):
                audio_bytes += chunk

        if not audio_bytes:
            return {
                "success": False,
                "error": "No audio data received from API"
            }

        # Save to file
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"✓ Voice saved: {output_path}")

        return {
            "success": True,
            "audio_bytes": audio_bytes,
            "audio_file": output_path if output_path else None,
            "asset_id": voice_id,
            "size_bytes": len(audio_bytes)
        }

    except Exception as e:
        print(f"✗ Voice generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def generate_music(positive_styles: list, negative_styles: list, sections: list, output_path: str = None) -> dict:
    """
    Generate music from style descriptions and sections

    Args:
        positive_styles: List of desired musical styles
        negative_styles: List of styles to avoid
        sections: List of section dicts with structure, duration, styles
        output_path: Optional path to save the audio file

    Returns:
        dict: {
            "success": bool,
            "audio_file": str (path to saved file),
            "asset_id": str (generation ID),
            "error": str (if failed)
        }
    """
    try:
        # Build comprehensive prompt from styles and sections
        prompt_parts = []

        if positive_styles:
            prompt_parts.append(f"Musical style: {', '.join(positive_styles)}")

        # Add section details if provided
        if sections:
            for i, section in enumerate(sections):
                section_name = section.get('sectionName', f'Section {i+1}')
                duration_ms = section.get('durationMs', 0)
                local_positive = section.get('positiveLocalStyles', [])

                section_desc = f"{section_name}"
                if local_positive:
                    section_desc += f": {', '.join(local_positive)}"
                if duration_ms:
                    section_desc += f" ({duration_ms/1000:.1f}s)"

                prompt_parts.append(section_desc)

        # Combine into single prompt
        prompt = ". ".join(prompt_parts) if prompt_parts else "instrumental background music"

        # Calculate total duration from sections
        total_duration_ms = sum(s.get('durationMs', 3000) for s in sections) if sections else 10000
        duration_seconds = max(3, min(60, total_duration_ms / 1000))  # Clamp to 3-60s

        print(f"🔄 Generating Music: {prompt[:50]}... ({duration_seconds}s)")

        # Generate music using text-to-sound-effects with music prompt
        # Note: ElevenLabs doesn't have a dedicated music API yet,
        # so we use text-to-sound-effects with musical descriptions
        audio_generator = client.text_to_sound_effects.convert(
            text=prompt,
            duration_seconds=duration_seconds,
            prompt_influence=0.5
        )

        # Collect audio bytes
        audio_bytes = b""
        for chunk in audio_generator:
            if isinstance(chunk, bytes):
                audio_bytes += chunk

        if not audio_bytes:
            return {
                "success": False,
                "error": "No audio data received from API"
            }

        # Save to file
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"✓ Music saved: {output_path}")

        return {
            "success": True,
            "audio_bytes": audio_bytes,
            "audio_file": output_path if output_path else None,
            "asset_id": f"music_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "size_bytes": len(audio_bytes),
            "duration_seconds": duration_seconds
        }

    except Exception as e:
        print(f"✗ Music generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def test_api_connection():
    """
    Test ElevenLabs API connection

    Returns:
        bool: True if API is accessible
    """
    try:
        # Try to list voices (lightweight API call)
        voices = client.voices.get_all()
        print(f"✓ ElevenLabs API connected ({len(voices.voices)} voices available)")
        return True
    except Exception as e:
        print(f"✗ ElevenLabs API connection failed: {e}")
        return False


if __name__ == "__main__":
    # Quick API test
    print("=" * 70)
    print("ELEVENLABS API - CONNECTION TEST")
    print("=" * 70)

    success = test_api_connection()

    if success:
        print("\n✓ API integration ready!")
        print("\nAvailable functions:")
        print("  • generate_sfx(description) - Sound effects")
        print("  • generate_voice(voice_profile, text) - Text-to-speech")
        print("  • generate_music(positive_styles, negative_styles, sections) - Music")
    else:
        print("\n✗ API integration failed. Check your API key in .env.local")

    print("=" * 70)
