# Coding Conventions

**Analysis Date:** 2026-01-22

## Naming Patterns

**Files:**
- Snake case for all Python files: `audio_mapper.py`, `marker_repository.py`, `elevenlabs_api.py`
- UI component files: `marker_row.py`, `video_waveform_display.py`, `prompt_editor.py`
- Test files: `test_models.py`, `test_audio_playback.py`, `test_file_handler.py`

**Functions:**
- Snake case for all function names: `create_marker()`, `generate_audio()`, `execute_command()`
- Private/internal methods prefixed with underscore: `_notify_change()`, `_run_batch_generation()`, `_generate_audio_background_for_batch()`
- Callback methods follow pattern: `on_*_click()`, `on_*_change()` (e.g., `on_row_click()`, `on_generate_click()`)

**Variables:**
- Snake case for all local and instance variables: `marker_index`, `duration_ms`, `audio_file`, `progress_var`
- Constant-like values in UPPERCASE: `COLORS`, `MAX_HISTORY`, `DEFAULT_BITRATE`
- Boolean variables use `is_*` or `has_*` prefix: `is_playing`, `is_selected`, `can_undo`, `has_markers`

**Types/Classes:**
- PascalCase for all class names: `AudioMapperGUI`, `MarkerRepository`, `HistoryManager`, `FileHandler`
- Enum classes in PascalCase with UPPERCASE members: `MarkerType`, `MarkerStatus`
- Dataclass models with PascalCase: `Marker`, `AudioVersion`, `SFXPromptData`, `VoicePromptData`, `MusicPromptData`

## Code Style

**Formatting:**
- Black formatter configured with 100-character line limit (see `pyproject.toml`)
- Target Python version: 3.9+
- Consistent spacing: 2 blank lines between classes, 1 blank line between methods

**Linting:**
- Ruff configured with 100-character line limit
- Target version: Python 3.9
- Configuration in `pyproject.toml` under `[tool.ruff]`

## Import Organization

**Order:**
1. Standard library imports: `tkinter`, `json`, `os`, `sys`, `pathlib`, `copy`, `typing`, `datetime`, `enum`
2. Third-party imports: `cv2`, `PIL`, `numpy`, `moviepy`, `pygame`, `pydub`, `librosa`, `elevenlabs`
3. Local application imports: `from config.*`, `from core.*`, `from managers.*`, `from controllers.*`, `from services.*`, `from ui.*`

**Path Aliases:**
- No path aliases configured; all imports use relative module paths from project root
- Example: `from core.models import Marker`, `from managers.history_manager import HistoryManager`

## Error Handling

**Patterns:**
- Try/except blocks used for external API calls and file I/O operations
- Functions that can fail return tuples: `(success: bool, result: Any, error: Optional[str])`
- Example from `FileHandler`: `(success, data, error) = FileHandler.import_from_json(filepath)`
- Validation errors logged via `print()` statements for user-facing messages
- Silent failures avoided; errors always communicated to user via `messagebox` dialogs
- Model validation raises `ValueError` with descriptive messages: `raise ValueError(f"Invalid marker type: {self.type}. Must be one of {valid_types}")`

## Logging

**Framework:** Console print statements (no logging module used)

**Patterns:**
- User-facing operations use `tkinter.messagebox` for errors, warnings, confirmations
- Development/debug logging available in services (e.g., `assembly_playback_service.py` has `debug_logging` flag)
- Progress feedback via custom modal windows with progress bars and status labels
- File operations log warnings for data migration: `print(f"WARNING: Marker {i} has negative time ({marker.get('time_ms')}ms), setting to 0")`

## Comments

**When to Comment:**
- Module docstrings present on all files with format:
  ```python
  #!/usr/bin/env python3
  """
  Short description
  Longer description of module purpose
  """
  ```
- Class docstrings describe class purpose and responsibilities
- Complex algorithms and non-obvious logic documented inline
- TODO comments for planned improvements: `# TODO Phase 4: Replace video player audio with assembled preview`

**JSDoc/TSDoc:**
- Google-style docstrings used throughout codebase
- All public methods include docstrings with Args, Returns, and description
- Example from `MarkerRepository.find_by_time()`:
  ```python
  def find_by_time(self, time_ms: int, tolerance: int = 0) -> Optional[int]:
      """
      Find marker index by time with optional tolerance.

      Args:
          time_ms: Time to search for
          tolerance: Allowed time difference in milliseconds

      Returns:
          Index of matching marker or None if not found
      """
  ```

## Function Design

**Size:**
- Most functions kept to 20-50 lines
- Complex operations broken into smaller helper functions
- Large file: `audio_mapper.py` (1860 lines) - monolithic GUI class, candidates for further refactoring
- Service files moderate size: `audio_service.py` (925 lines), `core/models.py` (372 lines)

**Parameters:**
- Functions use explicit parameters, not `**kwargs`
- Optional parameters have sensible defaults: `max_history=50`, `template_id="TEMPLATE"`, `tolerance: int = 0`
- Callbacks registered as function references: `listener: Callable[[], None]`

**Return Values:**
- Single return value for simple operations
- Tuple returns for operations that can fail: `Tuple[bool, Optional[Dict], Optional[str]]`
- Repository methods return copies of data: `copy.deepcopy(marker)` to prevent external mutation
- Commands don't return values; side effects managed via listener notifications

## Module Design

**Exports:**
- `__init__.py` files used to export public API from modules
- Example from `core/__init__.py`: exports `Marker`, `MarkerRepository`, `Command` classes
- Example from `services/__init__.py`: exports `AudioGenerationService`, `AudioPlayer`

**Barrel Files:**
- Simple barrel files expose module public API: `from core.models import Marker`
- No wildcard imports used

---

*Convention analysis: 2026-01-22*
