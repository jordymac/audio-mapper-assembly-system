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
        print("\n" + "="*70)
        print("🔊 SFX GENERATION REQUEST")
        print("="*70)
        print(f"\n📋 Description: \"{description}\"")
        print(f"\n📡 API Call:")
        print(f"  Method: client.text_to_sound_effects.convert()")
        print(f"  Params:")
        print(f"    text: \"{description}\"")
        print(f"    duration_seconds: None (auto-determine)")
        print(f"    prompt_influence: 0.3")
        print("="*70)
        print(f"🔄 Sending request to ElevenLabs...")

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
    Generate voice narration from text using either preset voices or Voice Design API

    Args:
        voice_profile: Description of voice characteristics (e.g., "deep male voice, authoritative")
                      If empty/None, uses preset voice
        text: Text to speak
        output_path: Optional path to save the audio file

    Returns:
        dict: {
            "success": bool,
            "audio_file": str (path to saved file),
            "audio_bytes": bytes,
            "asset_id": str (voice ID used),
            "voice_description": str (description used),
            "error": str (if failed)
        }
    """
    try:
        print("\n" + "="*70)
        print("🎙️  VOICE GENERATION REQUEST")
        print("="*70)

        print(f"\n📋 Input Parameters:")
        print(f"  Voice Profile: \"{voice_profile}\"")
        print(f"  Text: \"{text}\"")

        voice_id = None
        voice_description = None

        # If custom voice profile is provided, use Voice Design API
        if voice_profile and voice_profile.strip():
            print(f"\n🎨 Using Voice Design API for custom voice...")
            print(f"\n📡 Step 1: Design voice from description")
            print(f"  Method: client.text_to_voice.design()")
            print(f"  Description: \"{voice_profile}\"")
            print("="*70)
            print(f"🔄 Generating voice previews...")

            # Generate voice previews based on description
            voices = client.text_to_voice.design(
                model_id="eleven_multilingual_ttv_v2",
                voice_description=voice_profile,
                text=text
            )

            if not voices.previews or len(voices.previews) == 0:
                raise ValueError("No voice previews generated from description")

            # Use the first preview (best match)
            preview = voices.previews[0]
            voice_id = preview.generated_voice_id
            voice_description = voice_profile

            print(f"✓ Voice designed successfully!")
            print(f"  Generated Voice ID: {voice_id}")
            print(f"  Preview count: {len(voices.previews)}")

        else:
            # Use default preset voice
            # Popular voice IDs:
            # - "21m00Tcm4TlvDq8ikWAM" - Rachel (calm, clear)
            # - "EXAVITQu4vr4xnSDxMaL" - Bella (soft, friendly)
            # - "ErXwobaYiN019PkySvjV" - Antoni (well-rounded male)
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel
            voice_description = "Rachel (preset voice - calm, clear)"
            print(f"\n🎤 Using preset voice: Rachel")

        print(f"\n📡 Step 2: Generate speech with voice")
        print(f"  Method: client.text_to_speech.convert()")
        print(f"  Params:")
        print(f"    voice_id: {voice_id}")
        print(f"    model_id: eleven_multilingual_v2")
        print(f"    output_format: mp3_44100_128")
        print(f"    text: \"{text}\"")
        print(f"    voice_settings:")
        print(f"      stability: 0.5")
        print(f"      similarity_boost: 0.75")
        print(f"      style: 0.0")
        print(f"      use_speaker_boost: True")
        print("="*70)
        print(f"🔄 Sending request to ElevenLabs TTS API...")

        # Generate speech with the selected voice
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

        print(f"\n✓ Voice generation successful!")
        print(f"  Size: {len(audio_bytes):,} bytes")
        print(f"  Voice: {voice_description}")

        return {
            "success": True,
            "audio_bytes": audio_bytes,
            "audio_file": output_path if output_path else None,
            "asset_id": voice_id,
            "voice_description": voice_description,
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
    Generate music from style descriptions and sections using ElevenLabs Music API

    Args:
        positive_styles: List of desired musical styles
        negative_styles: List of styles to avoid
        sections: List of section dicts with structure, duration, styles
        output_path: Optional path to save the audio file

    Returns:
        dict: {
            "success": bool,
            "audio_file": str (path to saved file),
            "audio_bytes": bytes,
            "asset_id": str (generation ID),
            "composition_plan": dict (the plan used),
            "error": str (if failed)
        }
    """
    try:
        print("\n" + "="*70)
        print("🎵 MUSIC GENERATION REQUEST")
        print("="*70)

        print(f"\n📋 Input Parameters:")
        print(f"  Positive Styles: {positive_styles}")
        print(f"  Negative Styles: {negative_styles}")
        print(f"  Sections: {len(sections) if sections else 0}")

        # Calculate total duration from sections
        total_duration_ms = sum(s.get('durationMs', 3000) for s in sections) if sections else 10000

        # Build composition plan in ElevenLabs format (snake_case required)
        composition_plan = {
            "positive_global_styles": positive_styles if positive_styles else [],
            "negative_global_styles": negative_styles if negative_styles else [],
            "sections": []
        }

        # Convert sections to ElevenLabs format
        if sections:
            print(f"\n📐 Section Breakdown:")
            for i, section in enumerate(sections):
                section_name = section.get('sectionName', f'Section {i+1}')
                duration_ms = section.get('durationMs', 3000)
                local_positive = section.get('positiveLocalStyles', [])
                local_negative = section.get('negativeLocalStyles', [])

                print(f"  Section {i+1}: {section_name}")
                print(f"    Duration: {duration_ms}ms ({duration_ms/1000:.1f}s)")
                print(f"    Local Positive: {local_positive}")
                print(f"    Local Negative: {local_negative}")

                composition_plan["sections"].append({
                    "section_name": section_name,
                    "positive_local_styles": local_positive,
                    "negative_local_styles": local_negative,
                    "duration_ms": duration_ms,
                    "lines": []  # No lyrics for instrumental music
                })

        print(f"\n🔧 Composition Plan:")
        print(f"  Global Positive: {composition_plan['positive_global_styles']}")
        print(f"  Global Negative: {composition_plan['negative_global_styles']}")
        print(f"  Total Duration: {total_duration_ms}ms ({total_duration_ms/1000:.1f}s)")
        print(f"\n📡 API Call:")
        print(f"  Method: client.music.compose()")
        print(f"  Using composition_plan with {len(composition_plan['sections'])} sections")
        print("="*70)
        print(f"🔄 Sending request to ElevenLabs Music API...")

        # Generate music using the dedicated Music API
        audio_generator = client.music.compose(
            composition_plan=composition_plan
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

        print(f"\n✓ Music generation successful!")
        print(f"  Size: {len(audio_bytes):,} bytes")
        print(f"  Duration: {total_duration_ms/1000:.1f}s")

        return {
            "success": True,
            "audio_bytes": audio_bytes,
            "audio_file": output_path if output_path else None,
            "asset_id": f"music_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "size_bytes": len(audio_bytes),
            "duration_ms": total_duration_ms,
            "composition_plan": composition_plan
        }

    except Exception as e:
        error_msg = str(e)
        print(f"✗ Music generation failed: {error_msg}")

        # Parse validation errors for clearer messages
        if "duration_ms" in error_msg and "120000" in error_msg:
            # Extract which section failed
            if "sections" in error_msg:
                import re
                section_match = re.search(r"sections', (\d+)", error_msg)
                if section_match:
                    section_num = int(section_match.group(1)) + 1  # Convert to 1-based
                    error_msg = f"Section {section_num} exceeds the 120-second (120000ms) limit.\n\nPlease split long sections into smaller parts (each ≤ 120 seconds)."
                else:
                    error_msg = "One or more sections exceed the 120-second (120000ms) limit.\n\nPlease split long sections into smaller parts."

        return {
            "success": False,
            "error": error_msg
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
