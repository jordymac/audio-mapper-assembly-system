# Codebase Structure

**Analysis Date:** 2026-01-22

## Directory Layout

```
audio-mapper-assembly-system/
├── audio_mapper.py              # Main entry point - AudioMapperGUI orchestrator (1860 lines)
├── pyproject.toml               # Project config, dependencies, test config
├── requirements.txt             # pip dependencies
├── run.sh                        # Shell script to activate venv and run app
├── .env.local                   # Environment variables (API keys, settings)
├── .planning/
│   └── codebase/                # GSD mapping documents
│       ├── STACK.md
│       ├── ARCHITECTURE.md
│       └── STRUCTURE.md
├── config/                      # Configuration and theming
│   ├── __init__.py
│   └── color_scheme.py          # Dark mode detection, color palette
├── core/                        # Domain models and core business logic
│   ├── __init__.py
│   ├── models.py                # Dataclasses: Marker, AudioVersion, prompt data types (372 lines)
│   ├── marker_repository.py     # Repository pattern for marker CRUD (175 lines)
│   ├── commands.py              # Command pattern: AddMarker, DeleteMarker, MoveMarker, EditMarker, GenerateAudio (172 lines)
│   └── categories.py            # SFX/Music category definitions (372 lines)
├── controllers/                 # Specialized I/O handlers
│   ├── __init__.py
│   ├── file_handler.py          # JSON import/export for template persistence (265 lines)
│   └── video_player_controller.py # Video loading, playback, frame rendering (374 lines)
├── managers/                    # Business logic coordinators and state managers
│   ├── __init__.py
│   ├── history_manager.py       # Undo/redo stack management (51 lines)
│   ├── marker_manager.py        # Marker creation, deletion, coordination (291 lines)
│   ├── marker_selection_manager.py # Track selected marker, UI sync (96 lines)
│   ├── version_manager.py       # Audio version history, generation status (305 lines)
│   ├── waveform_manager.py      # Waveform rendering, audio data processing (343 lines)
│   ├── filmstrip_manager.py     # Video thumbnail generation and caching (264 lines)
│   └── keyboard_manager.py      # Keyboard shortcut handling and dispatch (193 lines)
├── services/                    # External integrations and cross-cutting services
│   ├── __init__.py
│   ├── audio_service.py         # Audio generation dispatch and batch operations (925 lines)
│   ├── assembly_service.py      # Multi-track audio assembly and mixing (1174 lines)
│   ├── assembly_playback_service.py # Synchronized audio/video playback (239 lines)
│   ├── audio_player.py          # Audio playback control (103 lines)
│   └── elevenlabs_api.py        # ElevenLabs API client wrapper (403 lines)
├── ui/                          # User interface components and layouts
│   ├── __init__.py
│   ├── components/              # Reusable UI widgets
│   │   ├── __init__.py
│   │   ├── marker_row.py        # Individual marker list item with controls
│   │   ├── multi_track_display.py # 5-channel waveform visualization
│   │   ├── video_waveform_display.py # Single video audio channel visualization
│   │   ├── notes_dialog.py      # Version notes modal dialog
│   │   └── tooltip.py           # Hover tooltips for UI elements
│   ├── editors/                 # Prompt editing dialogs
│   │   ├── __init__.py
│   │   ├── prompt_editor.py     # Base prompt editor window
│   │   ├── sfx_editor.py        # SFX description editor
│   │   ├── voice_editor.py      # Voice text + profile editor
│   │   ├── music_editor.py      # Music style/mood section editor
│   │   └── music_section_editor.py # Individual music section editor
│   └── export/                  # Export dialogs
│       ├── __init__.py
│       └── export_center_window.py # Multi-project export interface
├── tests/                       # Test suite (pytest)
│   ├── test_audio_mapper.py
│   ├── test_models.py           # Model serialization and creation tests (139 lines)
│   ├── test_command_refactor.py # Command pattern undo/redo tests (238 lines)
│   ├── test_version_management.py # Version history tracking tests (246 lines)
│   ├── test_file_handler.py     # JSON import/export tests (213 lines)
│   ├── test_waveform_manager.py # Waveform rendering tests (124 lines)
│   ├── test_filmstrip_manager.py # Thumbnail generation tests (134 lines)
│   ├── test_auto_assembly.py    # Assembly workflow tests (169 lines)
│   ├── test_batch_operations.py # Batch generation tests (162 lines)
│   ├── test_audio_playback.py   # Playback control tests (119 lines)
│   ├── test_selection_sync.py   # Marker selection UI tests (139 lines)
│   ├── test_generation_button.py # Generation trigger tests (120 lines)
│   ├── test_enhanced_rows.py    # MarkerRow widget tests (85 lines)
│   ├── test_elevenlabs_integration.py # API integration tests (124 lines)
│   ├── test_version_history_ui.py # Version display tests (130 lines)
│   ├── test_assemble_audio.py   # Assembly service tests
│   └── test_polish.py           # Polish and edge case tests (168 lines)
├── utils/                       # Utility functions and helpers
│   ├── __init__.py
│   └── create_test_audio.py     # Test audio file generation for development (78 lines)
├── generated_audio/             # Output directory for generated audio files
│   ├── sfx/                     # Generated SFX audio files
│   ├── voice/                   # Generated voice audio files
│   └── music/                   # Generated music audio files
├── output/                      # Project output directory (user-facing)
│   ├── {template_id}_template/  # Per-project directory
│   │   ├── {template_id}_template.json # Exported marker map
│   │   ├── {template_id}_export_metadata.json # Export metadata
│   │   ├── MUSIC/               # Music assembly output
│   │   ├── SFX/                 # SFX assembly output
│   │   └── VOICE/               # Voice assembly output
│   └── DM01_Daily_Moments_Personal_-_Indoor_Routine/ # Example project
├── temp/                        # Temporary assembly files (cleaned on startup)
├── template_maps/               # Legacy template maps directory
├── docs/                        # Documentation
│   └── archive/                 # Archived documentation
├── venv/                        # Python virtual environment
└── .gitignore                   # Git ignore rules
```

## Directory Purposes

**audio_mapper.py:**
- Purpose: Application entry point and main GUI orchestrator
- Contains: AudioMapperGUI class managing all UI, state, and component coordination
- Key files: Single 1860-line file (monolithic but well-organized with methods grouped by UI section)

**config/:**
- Purpose: Centralized configuration and styling system
- Contains: Color schemes, dark mode detection, UI helper functions
- Key files: `color_scheme.py` (dark/light mode palettes, accent colors)

**core/:**
- Purpose: Domain models, repository pattern, and command pattern
- Contains: Type-safe data structures (Marker, AudioVersion), observable data store, reversible operations
- Key files:
  - `models.py`: Marker, AudioVersion, MarkerType enum, MarkerStatus enum, prompt data classes
  - `marker_repository.py`: CRUD operations with change listeners
  - `commands.py`: Command pattern implementations for undo/redo
  - `categories.py`: SFX and Music category definitions

**controllers/:**
- Purpose: Specialized I/O and external system handlers
- Contains: File I/O, video playback control
- Key files:
  - `file_handler.py`: JSON import/export with validation
  - `video_player_controller.py`: OpenCV video loading, frame display, playback state

**managers/:**
- Purpose: High-level business logic coordinators
- Contains: State management, workflow orchestration, UI synchronization
- Key files:
  - `marker_manager.py`: Coordinates marker creation/deletion/editing
  - `history_manager.py`: Undo/redo stack
  - `version_manager.py`: Audio version tracking and generation status
  - `waveform_manager.py`: Waveform data processing and rendering
  - `filmstrip_manager.py`: Video thumbnail extraction and display
  - `marker_selection_manager.py`: Track and sync selected marker across UI
  - `keyboard_manager.py`: Keyboard shortcut dispatch

**services/:**
- Purpose: External integrations and cross-cutting concerns
- Contains: Audio generation, assembly, playback, API clients
- Key files:
  - `audio_service.py`: ElevenLabs API dispatch, batch generation UI, progress tracking
  - `assembly_service.py`: Multi-track audio mixing, track assignment logic
  - `assembly_playback_service.py`: Synchronized audio/video playback
  - `audio_player.py`: Audio playback control via pydub
  - `elevenlabs_api.py`: ElevenLabs API client wrapper

**ui/components/:**
- Purpose: Reusable UI widgets and components
- Contains: Marker row, multi-track display, waveforms, dialogs, tooltips
- Key files:
  - `marker_row.py`: Individual marker list item with edit/play/generate/delete buttons
  - `multi_track_display.py`: 5-channel waveform visualization
  - `video_waveform_display.py`: Single-channel video audio waveform
  - `notes_dialog.py`: Version notes modal
  - `tooltip.py`: Hover tooltips

**ui/editors/:**
- Purpose: Type-specific prompt editor dialogs
- Contains: SFX, voice, music editor windows with validation
- Key files:
  - `prompt_editor.py`: Base editor window launcher
  - `sfx_editor.py`: SFX description input
  - `voice_editor.py`: Voice text + voice profile selector
  - `music_editor.py`: Music section collection editor
  - `music_section_editor.py`: Individual music section (duration, styles)

**ui/export/:**
- Purpose: Export workflow interfaces
- Contains: Export center window for managing multi-project exports
- Key files:
  - `export_center_window.py`: Export coordination window

**tests/:**
- Purpose: Unit and integration test suite
- Contains: Pytest tests for all major components
- Test patterns: Fixtures, mocking, assertions, coverage

**utils/:**
- Purpose: Development utilities and helpers
- Contains: Test audio file generation
- Key files: `create_test_audio.py` (generates test MP3 files)

**generated_audio/:**
- Purpose: Output directory for audio generation service
- Contains: Generated audio files organized by type (sfx, voice, music)
- Structure: {type}/{asset_slot}_v{version_number}.{format}
- Generated: Runtime by AudioGenerationService

**output/:**
- Purpose: User-facing project output directory
- Contains: Per-project folders with exported templates and assembled audio
- Structure: {template_id}/{template_id}_template.json + MUSIC/SFX/VOICE/ subdirectories
- User accessible: Yes (intended for end-user projects)

**temp/:**
- Purpose: Temporary workspace for assembly operations
- Contains: Per-channel audio files and preview mix files
- Lifecycle: Cleaned on assembly, not committed to git
- Auto-created: Yes

## Key File Locations

**Entry Points:**
- `audio_mapper.py`: Application entry (line 64+ AudioMapperGUI class, main event loop at end of file)
- `run.sh`: Shell launcher script (activates venv, runs audio_mapper.py)

**Configuration:**
- `config/color_scheme.py`: Global color scheme with dark mode detection
- `pyproject.toml`: Project metadata, dependencies, pytest config
- `.env.local`: Environment variables (ELEVENLABS_API_KEY, custom settings)

**Core Logic:**
- `core/models.py`: Data model definitions
- `core/marker_repository.py`: Observable marker data store
- `core/commands.py`: Undo/redo command implementations
- `managers/marker_manager.py`: High-level marker operations
- `services/audio_service.py`: Audio generation orchestration
- `services/assembly_service.py`: Multi-track assembly logic

**Testing:**
- `tests/`: All test files (20+ test files)
- `tests/test_models.py`: Model serialization
- `tests/test_command_refactor.py`: Undo/redo
- `tests/test_file_handler.py`: JSON import/export
- `tests/test_auto_assembly.py`: Assembly workflow

## Naming Conventions

**Files:**
- `snake_case.py` for all Python files
- `test_*.py` for test files (pytest discovery)
- Manager classes: `*_manager.py` (history_manager.py, marker_manager.py)
- Service classes: `*_service.py` (audio_service.py, assembly_service.py)
- Controllers: `*_controller.py` (video_player_controller.py)

**Directories:**
- `lowercase/` for all package directories
- Logical grouping: `managers/`, `services/`, `controllers/`, `ui/components/`, `ui/editors/`, `ui/export/`

**Classes:**
- `PascalCase` for class names (AudioMapperGUI, MarkerRepository, AudioGenerationService)
- Manager classes: `{Concept}Manager` (HistoryManager, MarkerManager, WaveformManager)
- Service classes: `{Concept}Service` (AudioGenerationService, AssemblyService)
- Dialog/Window classes: `{Name}Window` or `{Name}Dialog` (PromptEditorWindow, NotesDialog)

**Functions/Methods:**
- `snake_case` for functions and methods
- Private methods: `_private_method()` convention used
- Callbacks: `on_*` or `_on_*` (on_seek_callback, _on_markers_changed)
- Getters: `get_*` (get_current_time, get_typed_prompt_data)
- Setters: `set_*` (set_selected_index)
- Event handlers: `on_*` (on_click, on_enter)

**Variables:**
- `snake_case` for local variables and attributes
- `CONSTANTS_IN_CAPS` for module-level constants (e.g., TRACK_MUSIC_LR in AssemblyService)
- UI widgets: descriptive names (video_canvas, timeline_slider, marker_canvas)
- Collections: plural names (markers, versions, listeners)

**Enums:**
- `PascalCase` for enum names (MarkerType, MarkerStatus)
- `UPPER_SNAKE_CASE` for enum values (MarkerType.SFX, MarkerStatus.GENERATED)

## Where to Add New Code

**New Feature (e.g., marker tagging system):**
- Primary code: `managers/` (coordinate feature) + `core/models.py` (data model)
- Tests: `tests/test_*.py` (new test file or add to existing)
- UI: `ui/components/` (if widget needed) or `ui/editors/` (if dialog needed)
- Example structure: Add TaggedMarker mixin to Marker, create TagManager in managers/

**New Component/Module (e.g., timeline ruler):**
- Implementation: `ui/components/{component_name}.py` (new file)
- Integration: Import in `audio_mapper.py`, instantiate in create_* method
- Tests: Create `tests/test_{component_name}.py`
- Pattern: Follow MarkerRow or MultiTrackDisplay structure with parent reference and callbacks

**Utilities (e.g., audio format converter):**
- Shared helpers: `utils/{helper_name}.py` (new file)
- Import in relevant service/manager
- Test in `tests/test_utils.py` or dedicated test file

**New Service Integration (e.g., new AI provider):**
- Service wrapper: `services/{provider_name}_api.py` (new file)
- Service orchestrator: Add to `services/audio_service.py` or new `services/{feature}_service.py`
- Configuration: Add API keys to `.env.local`
- Example: Create `services/mubert_api.py`, import in AudioGenerationService

**Database/Persistence (future):**
- Data layer: `core/db_repository.py` (replace/supplement MarkerRepository)
- Migrations: `db/migrations/` directory structure
- Connection management: `core/db_connection.py`

**New Test Coverage:**
- Test patterns: Follow existing test files (test_*.py)
- Fixtures: Use markers fixture for common data setup
- Mocking: Use unittest.mock or pytest monkeypatch
- Location: Add to existing test file if testing existing component, or create new test_*.py

## Special Directories

**generated_audio/:**
- Purpose: Runtime output directory for audio generation
- Generated: Yes (created by AudioGenerationService)
- Committed: No (in .gitignore)
- Lifecycle: Files accumulate during runtime, can be cleaned manually

**output/:**
- Purpose: User project outputs and exports
- Generated: Yes (created by export workflows)
- Committed: Partially (template structure exists, user files added at runtime)
- Lifecycle: User-facing, should be preserved between sessions

**temp/:**
- Purpose: Temporary workspace for assembly operations
- Generated: Yes (created by AssemblyService)
- Committed: No (in .gitignore)
- Lifecycle: Files cleaned up or used for assembly preview

**venv/:**
- Purpose: Python virtual environment
- Generated: Yes (created by user with `python -m venv venv`)
- Committed: No (in .gitignore)
- Lifecycle: Local development only

---

*Structure analysis: 2026-01-22*
