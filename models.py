#!/usr/bin/env python3
"""
Data Models - Type-safe data structures for Audio Mapper
Replaces dictionary-based data with proper dataclasses for type safety and validation
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class MarkerType(str, Enum):
    """Marker type enumeration"""
    SFX = "sfx"
    VOICE = "voice"
    MUSIC = "music"
    MUSIC_CONTROL = "music_control"


class MarkerStatus(str, Enum):
    """Marker generation status"""
    NOT_GENERATED = "not yet generated"
    GENERATING = "generating"
    GENERATED = "generated"
    FAILED = "failed"


# ============================================================================
# PROMPT DATA MODELS (Type-specific)
# ============================================================================

@dataclass
class SFXPromptData:
    """Prompt data for SFX markers"""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"description": self.description}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SFXPromptData':
        return cls(description=data.get("description", ""))


@dataclass
class VoicePromptData:
    """Prompt data for voice markers"""
    voice_profile: str = ""
    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voice_profile": self.voice_profile,
            "text": self.text
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoicePromptData':
        return cls(
            voice_profile=data.get("voice_profile", ""),
            text=data.get("text", "")
        )


@dataclass
class MusicSection:
    """A section within a music prompt"""
    duration_s: float = 0.0
    positiveStyles: List[str] = field(default_factory=list)
    negativeStyles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_s": self.duration_s,
            "positiveStyles": self.positiveStyles.copy(),
            "negativeStyles": self.negativeStyles.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MusicSection':
        return cls(
            duration_s=data.get("duration_s", 0.0),
            positiveStyles=data.get("positiveStyles", []).copy(),
            negativeStyles=data.get("negativeStyles", []).copy()
        )


@dataclass
class MusicPromptData:
    """Prompt data for music markers"""
    positiveGlobalStyles: List[str] = field(default_factory=list)
    negativeGlobalStyles: List[str] = field(default_factory=list)
    sections: List[MusicSection] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "positiveGlobalStyles": self.positiveGlobalStyles.copy(),
            "negativeGlobalStyles": self.negativeGlobalStyles.copy(),
            "sections": [s.to_dict() for s in self.sections]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MusicPromptData':
        sections_data = data.get("sections", [])
        sections = [MusicSection.from_dict(s) if isinstance(s, dict) else s for s in sections_data]
        return cls(
            positiveGlobalStyles=data.get("positiveGlobalStyles", []).copy(),
            negativeGlobalStyles=data.get("negativeGlobalStyles", []).copy(),
            sections=sections
        )


# Type alias for prompt data union
PromptData = SFXPromptData | VoicePromptData | MusicPromptData


# ============================================================================
# VERSION MODEL
# ============================================================================

@dataclass
class AudioVersion:
    """Represents a version of generated audio for a marker"""
    version: int
    asset_file: str
    asset_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = MarkerStatus.NOT_GENERATED.value
    prompt_data_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "version": self.version,
            "asset_file": self.asset_file,
            "asset_id": self.asset_id,
            "created_at": self.created_at,
            "status": self.status,
            "prompt_data_snapshot": self.prompt_data_snapshot.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioVersion':
        """Create from dictionary (e.g., from JSON)"""
        return cls(
            version=data["version"],
            asset_file=data["asset_file"],
            asset_id=data.get("asset_id"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            status=data.get("status", MarkerStatus.NOT_GENERATED.value),
            prompt_data_snapshot=data.get("prompt_data_snapshot", {}).copy()
        )


# ============================================================================
# MARKER MODEL
# ============================================================================

@dataclass
class Marker:
    """
    Represents an audio marker on the timeline

    A marker defines a point in time where audio should be generated,
    with type-specific prompt data and version history.
    """
    time_ms: int
    type: str  # Use string for backward compatibility, but validate against MarkerType
    name: str = ""
    prompt_data: Dict[str, Any] = field(default_factory=dict)
    asset_slot: str = ""
    asset_file: str = ""
    asset_id: Optional[str] = None
    status: str = MarkerStatus.NOT_GENERATED.value
    current_version: int = 1
    versions: List[AudioVersion] = field(default_factory=list)

    def __post_init__(self):
        """Validate and convert after initialization"""
        # Validate type
        valid_types = {t.value for t in MarkerType}
        if self.type not in valid_types:
            raise ValueError(f"Invalid marker type: {self.type}. Must be one of {valid_types}")

        # Convert version dicts to AudioVersion objects if needed
        if self.versions and isinstance(self.versions[0], dict):
            self.versions = [AudioVersion.from_dict(v) for v in self.versions]

    def get_typed_prompt_data(self) -> PromptData:
        """Get prompt data as typed object"""
        if self.type == MarkerType.SFX.value:
            return SFXPromptData.from_dict(self.prompt_data)
        elif self.type == MarkerType.VOICE.value:
            return VoicePromptData.from_dict(self.prompt_data)
        elif self.type == MarkerType.MUSIC.value:
            return MusicPromptData.from_dict(self.prompt_data)
        else:
            # Fallback to SFX for unknown types
            return SFXPromptData.from_dict(self.prompt_data)

    def set_prompt_data(self, prompt_data: PromptData):
        """Set prompt data from typed object"""
        self.prompt_data = prompt_data.to_dict()

    def get_current_version(self) -> Optional[AudioVersion]:
        """Get the current version object"""
        for v in self.versions:
            if v.version == self.current_version:
                return v
        return None

    def copy(self) -> 'Marker':
        """Create a deep copy of this marker"""
        return Marker.from_dict(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "time_ms": self.time_ms,
            "type": self.type,
            "name": self.name,
            "prompt_data": self.prompt_data.copy(),
            "asset_slot": self.asset_slot,
            "asset_file": self.asset_file,
            "asset_id": self.asset_id,
            "status": self.status,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Marker':
        """Create from dictionary (e.g., from JSON)"""
        # Handle versions
        versions_data = data.get("versions", [])
        versions = [
            AudioVersion.from_dict(v) if isinstance(v, dict) else v
            for v in versions_data
        ]

        return cls(
            time_ms=data["time_ms"],
            type=data["type"],
            name=data.get("name", ""),
            prompt_data=data.get("prompt_data", {}).copy(),
            asset_slot=data.get("asset_slot", ""),
            asset_file=data.get("asset_file", ""),
            asset_id=data.get("asset_id"),
            status=data.get("status", MarkerStatus.NOT_GENERATED.value),
            current_version=data.get("current_version", 1),
            versions=versions
        )

    @staticmethod
    def create_default_prompt_data(marker_type: str) -> Dict[str, Any]:
        """Create default prompt data for a marker type"""
        if marker_type == MarkerType.SFX.value:
            return SFXPromptData().to_dict()
        elif marker_type == MarkerType.VOICE.value:
            return VoicePromptData().to_dict()
        elif marker_type == MarkerType.MUSIC.value:
            return MusicPromptData().to_dict()
        else:
            return SFXPromptData().to_dict()


# ============================================================================
# VIDEO INFO MODEL
# ============================================================================

@dataclass
class VideoInfo:
    """Information about loaded video"""
    filepath: str
    duration_ms: int
    fps: float
    frame_count: int
    width: int
    height: int

    @classmethod
    def from_video_capture(cls, filepath: str, cap) -> 'VideoInfo':
        """Create from OpenCV VideoCapture object"""
        import cv2
        return cls(
            filepath=filepath,
            duration_ms=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) * 1000),
            fps=cap.get(cv2.CAP_PROP_FPS),
            frame_count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_marker(
    time_ms: int,
    marker_type: str,
    name: str = "",
    prompt_data: Optional[Dict[str, Any]] = None,
    asset_slot: str = "",
    asset_file: str = "",
) -> Marker:
    """
    Factory function to create a new marker with proper initialization

    Args:
        time_ms: Timeline position in milliseconds
        marker_type: Type of marker (sfx, voice, music, music_control)
        name: Optional custom name
        prompt_data: Optional prompt data dict (will use default if None)
        asset_slot: Optional asset slot identifier
        asset_file: Optional asset filename

    Returns:
        Newly created Marker instance
    """
    if prompt_data is None:
        prompt_data = Marker.create_default_prompt_data(marker_type)

    # Create initial version
    version_obj = AudioVersion(
        version=1,
        asset_file=asset_file,
        asset_id=None,
        status=MarkerStatus.NOT_GENERATED.value,
        prompt_data_snapshot=prompt_data.copy()
    )

    return Marker(
        time_ms=time_ms,
        type=marker_type,
        name=name,
        prompt_data=prompt_data,
        asset_slot=asset_slot,
        asset_file=asset_file,
        asset_id=None,
        status=MarkerStatus.NOT_GENERATED.value,
        current_version=1,
        versions=[version_obj]
    )
