"""
Managers - Coordinator classes for application subsystems

Contains manager classes that coordinate various aspects of the application.
"""

from managers.history_manager import HistoryManager
from managers.keyboard_manager import KeyboardShortcutManager
from managers.marker_manager import MarkerManager
from managers.marker_selection_manager import MarkerSelectionManager
from managers.version_manager import MarkerVersionManager
from managers.filmstrip_manager import FilmstripManager
from managers.waveform_manager import WaveformManager

__all__ = [
    "HistoryManager",
    "KeyboardShortcutManager",
    "MarkerManager",
    "MarkerSelectionManager",
    "MarkerVersionManager",
    "FilmstripManager",
    "WaveformManager",
]
