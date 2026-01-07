#!/usr/bin/env python3
"""
Category Taxonomies for Audio Metadata
Defines all available categories for SFX, Music, and Voice markers
Based on METADATA_EXPORT_PLAN.md
"""

# ============================================================================
# SFX CATEGORIES (38 total - from ElevenLabs library)
# ============================================================================

SFX_CATEGORIES = [
    "Animals",
    "Bass",
    "Booms",
    "Braams",
    "Brass",
    "Cymbals",
    "Devices",
    "Drones",
    "Fantasy",
    "Foley",
    "Guitar",
    "Horror",
    "Household",
    "Humans",
    "Impacts",
    "Industrial",
    "Keys",
    "Misc",
    "Nature",
    "Ocean",
    "Office",
    "Parks",
    "Percussion",
    "Restaurants",
    "Risers",
    "School",
    "Sci-Fi",
    "Sports",
    "Strings",
    "Synth",
    "Transport",
    "UI Elements",
    "Urban",
    "Vehicles",
    "Weapons",
    "Weather",
    "Whooshes",
    "Woodwinds"
]

# ============================================================================
# MUSIC CATEGORIES
# ============================================================================

MUSIC_GENRES = [
    "Acoustic",
    "Ambient",
    "Chillhop",
    "Cinematic",
    "Classical",
    "Country",
    "Electronic",
    "Folk",
    "Hip Hop",
    "Indie",
    "Jazz",
    "Lo-Fi",
    "Metal",
    "Orchestral",
    "Pop",
    "R&B",
    "Rock",
    "Soul",
    "Synth",
    "Trap",
    "World",
    "Other"
]

# Sub-genres organized by genre
MUSIC_SUBGENRES = {
    "Electronic": [
        "House",
        "Techno",
        "Trance",
        "Dubstep",
        "Drum & Bass",
        "Synth Pop",
        "Electro House",
        "Future Bass",
        "Chillwave",
        "Vaporwave"
    ],
    "Hip Hop": [
        "Trap",
        "Boom Bap",
        "Lo-Fi Hip Hop",
        "Cloud Rap",
        "Jazz Rap",
        "G-Funk"
    ],
    "Rock": [
        "Indie Rock",
        "Alternative",
        "Pop Rock",
        "Hard Rock",
        "Punk",
        "Progressive"
    ]
}

MUSIC_KEYS = [
    "C Major",
    "C Minor",
    "C# Major",
    "C# Minor",
    "D Major",
    "D Minor",
    "D# Major",
    "D# Minor",
    "E Major",
    "E Minor",
    "F Major",
    "F Minor",
    "F# Major",
    "F# Minor",
    "G Major",
    "G Minor",
    "G# Major",
    "G# Minor",
    "A Major",
    "A Minor",
    "A# Major",
    "A# Minor",
    "B Major",
    "B Minor",
    "Unknown"
]

MUSIC_INSTRUMENTS = [
    "Acoustic Guitar",
    "Electric Guitar",
    "Bass Guitar",
    "Piano",
    "Synthesizer",
    "Drums",
    "Percussion",
    "Strings",
    "Brass",
    "Woodwinds",
    "Vocals",
    "Pad/Ambient",
    "808/Sub Bass",
    "Bells",
    "Harp",
    "Organ",
    "Other"
]

MUSIC_MOODS = [
    "Calm",
    "Cheerful",
    "Dark",
    "Dramatic",
    "Energetic",
    "Epic",
    "Happy",
    "Hopeful",
    "Inspirational",
    "Intense",
    "Melancholic",
    "Mysterious",
    "Nostalgic",
    "Peaceful",
    "Playful",
    "Romantic",
    "Sad",
    "Tense",
    "Upbeat",
    "Uplifting"
]

MUSIC_INTENSITY_LEVELS = [
    "Subtle",
    "Moderate",
    "Intense",
    "Extreme"
]

# ============================================================================
# VOICE CATEGORIES
# ============================================================================

VOICE_GENDERS = [
    "Male",
    "Female",
    "Non-binary",
    "Multiple Voices"
]

VOICE_AGE_GROUPS = [
    "Child (0-12)",
    "Teen (13-19)",
    "Young Adult (20-35)",
    "Adult (36-55)",
    "Senior (56+)"
]

VOICE_ACCENTS = [
    "American (General)",
    "American (Southern)",
    "American (New York)",
    "Australian",
    "British (RP)",
    "British (Cockney)",
    "Canadian",
    "Indian",
    "Irish",
    "Scottish",
    "South African",
    "None/Neutral",
    "Other"
]

VOICE_TONES = [
    "Authoritative",
    "Calm",
    "Casual",
    "Conversational",
    "Dramatic",
    "Emotional",
    "Energetic",
    "Formal",
    "Friendly",
    "Professional",
    "Sarcastic",
    "Serious",
    "Warm",
    "Whispered"
]

VOICE_DELIVERY_STYLES = [
    "Narration",
    "Dialogue",
    "Announcement",
    "Commercial",
    "Documentary",
    "Storytelling",
    "Voiceover",
    "Whisper",
    "Shout",
    "Singing"
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_default_categories(marker_type: str) -> dict:
    """
    Get default category structure for a marker type

    Args:
        marker_type: "sfx", "music", or "voice"

    Returns:
        Default categories dict
    """
    if marker_type == "sfx":
        return {
            "categories": [],  # List of 1-3 SFX_CATEGORIES
            "duration_s": 0.0,
            "pro_tier": False
        }
    elif marker_type == "music":
        return {
            "genre": "",
            "subGenre": "",
            "key": "Unknown",
            "bpm": 0,
            "instruments": [],
            "mood": [],
            "intensity": "Moderate",
            "pro_tier": False
        }
    elif marker_type == "voice":
        return {
            "gender": "",
            "age": "",
            "accent": "",
            "tone": "",
            "delivery": "",
            "script_text": "",
            "speaker_voice_id": "",
            "pro_tier": False
        }
    else:
        return {}


def validate_categories(marker_type: str, categories: dict) -> tuple[bool, str]:
    """
    Validate category data for a marker type

    Args:
        marker_type: "sfx", "music", or "voice"
        categories: Categories dict to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if marker_type == "sfx":
        cats = categories.get("categories", [])
        if not cats or len(cats) < 1 or len(cats) > 3:
            return False, "SFX must have 1-3 categories"
        for cat in cats:
            if cat not in SFX_CATEGORIES:
                return False, f"Invalid SFX category: {cat}"
        return True, ""

    elif marker_type == "music":
        # Validate genre
        genre = categories.get("genre", "")
        if not genre or genre not in MUSIC_GENRES:
            return False, "Music must have a valid genre"

        # Validate key (optional but must be valid if provided)
        key = categories.get("key", "Unknown")
        if key and key not in MUSIC_KEYS:
            return False, f"Invalid music key: {key}"

        # Validate instruments (1-5 required)
        instruments = categories.get("instruments", [])
        if not instruments or len(instruments) < 1 or len(instruments) > 5:
            return False, "Music must have 1-5 instruments"

        # Validate mood (1-3 required)
        moods = categories.get("mood", [])
        if not moods or len(moods) < 1 or len(moods) > 3:
            return False, "Music must have 1-3 moods"

        # Validate intensity
        intensity = categories.get("intensity", "")
        if intensity and intensity not in MUSIC_INTENSITY_LEVELS:
            return False, f"Invalid intensity: {intensity}"

        return True, ""

    elif marker_type == "voice":
        # All fields required
        required_fields = ["gender", "age", "accent", "tone", "delivery"]
        for field in required_fields:
            if not categories.get(field):
                return False, f"Voice {field} is required"

        # Validate values
        if categories["gender"] not in VOICE_GENDERS:
            return False, f"Invalid gender: {categories['gender']}"
        if categories["age"] not in VOICE_AGE_GROUPS:
            return False, f"Invalid age: {categories['age']}"
        if categories["accent"] not in VOICE_ACCENTS:
            return False, f"Invalid accent: {categories['accent']}"
        if categories["tone"] not in VOICE_TONES:
            return False, f"Invalid tone: {categories['tone']}"
        if categories["delivery"] not in VOICE_DELIVERY_STYLES:
            return False, f"Invalid delivery: {categories['delivery']}"

        return True, ""

    return False, f"Unknown marker type: {marker_type}"
