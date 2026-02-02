#!/usr/bin/env python3
"""
Prompt Validator - Validation utilities for API prompts
Ensures prompts meet length and content requirements before API calls
"""

from typing import Tuple, Optional


class PromptValidationError(Exception):
    """Raised when prompt validation fails"""
    pass


# ElevenLabs API limits (based on documented limits and practical testing)
PROMPT_LIMITS = {
    "sfx": {
        "max_length": 1000,  # Sound effect descriptions
        "min_length": 1,
        "field_name": "description"
    },
    "voice": {
        "max_length": 5000,  # Text-to-speech content
        "min_length": 1,
        "field_name": "text"
    },
    "voice_profile": {
        "max_length": 500,  # Voice profile description
        "min_length": 0,  # Optional field
        "field_name": "voice_profile"
    },
    "music_style": {
        "max_length": 200,  # Individual style description
        "min_length": 1,
        "field_name": "style"
    },
    "music_section": {
        "max_length": 100,  # Section name
        "min_length": 0,
        "field_name": "section_name"
    }
}


def validate_prompt_length(prompt: str, prompt_type: str) -> Tuple[bool, str]:
    """
    Validate prompt length against limits.

    Args:
        prompt: The prompt text to validate
        prompt_type: Type of prompt (sfx, voice, voice_profile, music_style, music_section)

    Returns:
        Tuple of (is_valid, error_message):
        - is_valid: True if prompt is within limits
        - error_message: Empty string if valid, explanation if invalid
    """
    if prompt_type not in PROMPT_LIMITS:
        return True, ""  # Unknown type, allow it

    limits = PROMPT_LIMITS[prompt_type]
    max_len = limits["max_length"]
    min_len = limits["min_length"]
    field_name = limits["field_name"]

    # Handle None
    if prompt is None:
        if min_len > 0:
            return False, f"{field_name} is required"
        return True, ""

    prompt_len = len(prompt.strip())

    if prompt_len < min_len:
        return False, f"{field_name} must be at least {min_len} character(s)"

    if prompt_len > max_len:
        return False, (
            f"{field_name} is too long ({prompt_len} characters).\n"
            f"Maximum allowed: {max_len} characters.\n\n"
            f"Please shorten your {field_name} and try again."
        )

    return True, ""


def validate_prompt(prompt: str, prompt_type: str, allow_empty: bool = False) -> str:
    """
    Validate a prompt and return the cleaned version.

    Args:
        prompt: The prompt text to validate
        prompt_type: Type of prompt (sfx, voice, voice_profile, music_style)
        allow_empty: If True, allow empty/None prompts

    Returns:
        The cleaned prompt string

    Raises:
        PromptValidationError: If prompt fails validation
    """
    # Handle None/empty
    if prompt is None or prompt.strip() == "":
        if allow_empty:
            return ""
        raise PromptValidationError(f"Prompt cannot be empty for {prompt_type}")

    # Clean the prompt
    cleaned = prompt.strip()

    # Validate length
    is_valid, error_msg = validate_prompt_length(cleaned, prompt_type)
    if not is_valid:
        raise PromptValidationError(error_msg)

    return cleaned


def validate_sfx_prompt(description: str) -> str:
    """Validate SFX description prompt"""
    return validate_prompt(description, "sfx", allow_empty=False)


def validate_voice_prompt(text: str, voice_profile: Optional[str] = None) -> Tuple[str, str]:
    """
    Validate voice prompt (text and optional voice profile).

    Returns:
        Tuple of (validated_text, validated_voice_profile)
    """
    validated_text = validate_prompt(text, "voice", allow_empty=False)
    validated_profile = validate_prompt(voice_profile or "", "voice_profile", allow_empty=True)
    return validated_text, validated_profile


def validate_music_styles(positive_styles: list, negative_styles: list) -> Tuple[list, list]:
    """
    Validate music style lists.

    Returns:
        Tuple of (validated_positive_styles, validated_negative_styles)
    """
    validated_positive = []
    for style in (positive_styles or []):
        if style and style.strip():
            validated = validate_prompt(style.strip(), "music_style", allow_empty=True)
            if validated:
                validated_positive.append(validated)

    validated_negative = []
    for style in (negative_styles or []):
        if style and style.strip():
            validated = validate_prompt(style.strip(), "music_style", allow_empty=True)
            if validated:
                validated_negative.append(validated)

    return validated_positive, validated_negative
