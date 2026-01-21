# Architecture

**Analysis Date:** 2026-01-22

## Pattern Overview

**Overall:** Layered MVC with Separation of Concerns

**Key Characteristics:**
- Tkinter-based GUI application with decoupled business logic
- Repository pattern for data persistence and change notification
- Command pattern for undo/redo functionality
- Service layer for audio generation, assembly, and playback
- Manager layer coordinating UI, state, and business operations
- Clean separation between GUI, models, controllers, and services

## Layers

**Presentation Layer (UI):**
- Purpose: Render visual components and handle user interaction
- Location: `ui/` directory with `audio_mapper.py` as main orchestrator
- Contains: Components (marker rows, multi-track display, waveform display), editors (prompt editors, music section editors), dialogs, tooltips
- Depends on: Models, Managers, Services
- Used by: End users via Tkinter GUI

**Business Logic / Manager Layer:**
- Purpose: Coordinate operations between UI, repository, and services
- Location: `managers/` directory
- Contains: HistoryManager, MarkerManager, WaveformManager, FilmstripManager, MarkerSelectionManager, VersionManager, KeyboardShortcutManager
- Depends on: Core models, Repository, Services
- Used by: Main GUI class (AudioMapperGUI)

**Service Layer:**
- Purpose: Encapsulate cross-cutting concerns and external integrations
- Location: `services/` directory
- Contains: AudioGenerationService, AudioPlayer, AssemblyService, AssemblyPlaybackService, ElevenLabs API client
- Depends on: Core models
- Used by: Main GUI, Managers

**Controller Layer:**
- Purpose: Handle specialized operations and I/O
- Location: `controllers/` directory
- Contains: FileHandler (JSON import/export), VideoPlayerController (video playback and frame management)
- Depends on: Core models
- Used by: Main GUI

**Data Access Layer (Repository):**
- Purpose: Provide CRUD operations and change notification for markers
- Location: `core/marker_repository.py`
- Contains: MarkerRepository with add_change_listener pattern for observable data
- Depends on: Core models
- Used by: Commands, Manager layer, Main GUI

**Domain Model Layer:**
- Purpose: Define type-safe data structures
- Location: `core/` directory (models.py, commands.py, categories.py)
- Contains: Marker, AudioVersion, MarkerType, MarkerStatus enums, prompt data classes (SFXPromptData, VoicePromptData, MusicPromptData), Command base classes
- Depends on: Python stdlib only
- Used by: All other layers

**Configuration Layer:**
- Purpose: Centralized configuration and styling
- Location: `config/` directory
- Contains: Color scheme with dark mode detection, helper functions for UI creation
- Depends on: Python stdlib
- Used by: UI components and main GUI

## Data Flow

**Video Loading & Timeline Initialization:**

1. User selects "Open Video" from File menu → calls `load_video()`
2. `VideoPlayerController.load_video()` opens file dialog and loads video with OpenCV
3. Video metadata (FPS, duration, total frames) extracted and stored in VideoPlayerController
4. Canvas displays first frame as PIL ImageTk
5. Timeline slider range set to total video duration
6. Filmstrip and Waveform managers initialized with video duration and FPS
7. "Create Blank Timeline" option creates timeline without video

**Marker Creation Workflow:**

1. User clicks "Add Marker" or presses keyboard shortcut
2. MarkerManager.create_marker() called with marker type (sfx/voice/music)
3. New Marker object created with proper initialization:
   - Auto-generated asset slot name (SFX_00000, VOX_00000, etc.)
   - First AudioVersion initialized
   - Prompt data structure prepared (empty initially)
4. AddMarkerCommand created and executed via HistoryManager
5. Repository notifies all listeners (UI update callback)
6. MarkerRow widget created and added to marker list panel
7. UI redraws marker indicators on waveform and filmstrip

**Marker Audio Generation Workflow:**

1. User clicks "Generate" on marker row or selects from batch menu
2. Opens PromptEditorWindow for marker type-specific data entry
3. User enters prompt (SFX description, voice text, music style)
4. On confirm: calls AudioGenerationService.generate_marker_audio()
5. ElevenLabs API called via elevenlabs_api.py
6. Generated audio downloaded to file: `generated_audio/{type}/{asset_slot}_v{version}.mp3`
7. MarkerVersionManager tracks generation status and creates AudioVersion
8. Marker updated with asset file reference and GENERATED status
9. If auto-assemble enabled: AssemblyService.assemble() called automatically
10. UI updates marker status indicator (✓, ⚠, etc.)

**Audio Assembly & Playback Workflow:**

1. AssemblyService.assign_markers_to_tracks() distributes markers to 5 audio channels:
   - Channel 1-2: All music markers (stereo)
   - Channel 3: SFX markers (alternating even indices)
   - Channel 4: SFX markers (alternating odd indices)
   - Channel 5: Voice markers
2. Per-channel audio files generated or collected from generated_audio/
3. Channels mixed to stereo preview in temp/ directory
4. AssemblyPlaybackService synchronized playback:
   - AudioPlayer plays preview file
   - Timeline slider updated in sync
   - Playhead position displayed on waveforms

**File Persistence Workflow:**

1. User exports markers to JSON
2. FileHandler.export_to_json() creates JSON structure:
   - Template metadata (ID, name, duration_ms)
   - Markers array with full data (time_ms, type, prompt_data, versions)
3. Saved to output/{template_id}/{template_id}_template.json
4. Import reverses process: FileHandler.import_from_json() validates and deserializes

**State Management & Undo/Redo:**

1. Every marker operation (add, delete, move, edit) wrapped in Command object
2. HistoryManager.execute_command() calls command.execute() and pushes to undo stack
3. Repository notifies listeners when marker data changes
4. UI components re-render based on listener callbacks
5. Undo/Redo: pop from stack, call command.undo() or command.redo()
6. Repository notification triggers UI update

## Key Abstractions

**Marker:**
- Purpose: Type-safe representation of a single audio event pinned to timecode
- Examples: `core/models.py` (Marker dataclass), `core/marker_repository.py` (collection)
- Pattern: Dataclass with version history, typed prompt data, status tracking

**MarkerRepository:**
- Purpose: Observable data store for markers with CRUD + change notification
- Examples: `core/marker_repository.py` MarkerRepository class
- Pattern: Repository pattern with listener callbacks for decoupled UI updates

**Command:**
- Purpose: Encapsulate reversible operations for undo/redo
- Examples: `core/commands.py` (AddMarkerCommand, DeleteMarkerCommand, MoveMarkerCommand, EditMarkerCommand)
- Pattern: Command pattern with execute()/undo() interface

**Manager Classes:**
- Purpose: Coordinate complex workflows between UI, repository, and services
- Examples: `managers/marker_manager.py` (marker creation/deletion), `managers/history_manager.py` (undo/redo), `managers/version_manager.py` (audio version tracking)
- Pattern: Facade pattern simplifying interaction between components

**AudioService:**
- Purpose: Encapsulate audio generation and assembly logic
- Examples: `services/audio_service.py`, `services/assembly_service.py`
- Pattern: Service layer with external dependency injection (ElevenLabs API)

**UI Components:**
- Purpose: Modular, reusable UI building blocks
- Examples: `ui/components/marker_row.py` (individual marker display), `ui/components/multi_track_display.py` (5-channel waveform), `ui/components/video_waveform_display.py` (video audio visualization)
- Pattern: Component pattern with parent reference and callbacks for loose coupling

## Entry Points

**Application Entry:**
- Location: `audio_mapper.py` (main executable)
- Triggers: User runs `./run.sh` or `python audio_mapper.py`
- Responsibilities: Creates root Tkinter window, instantiates AudioMapperGUI, starts event loop

**AudioMapperGUI Class:**
- Location: `audio_mapper.py` (lines 64+)
- Triggers: Instantiated when app starts
- Responsibilities: Orchestrates entire application, creates UI, initializes managers/services, handles all user commands

## Error Handling

**Strategy:** Try-catch at service boundaries with user feedback dialogs

**Patterns:**
- Import guards at module level (video, audio libraries) with helpful error messages
- Try-except in FileHandler.import_from_json() with validation and error tuples (success, data, error_message)
- Try-except in audio service with messagebox.showerror() for user feedback
- Exception handling in ElevenLabs API calls with fallback status indicators
- Negative time validation (sanitize to 0) rather than reject

## Cross-Cutting Concerns

**Logging:** Console prints in critical paths (missing dependencies, warnings), no structured logging framework

**Validation:**
- Marker time bounds checking in FileHandler and MarkerManager
- Marker type validation against MarkerType enum
- Duration validation (non-negative)

**Authentication:**
- ElevenLabs API key sourced from environment (ELEVENLABS_API_KEY)
- VideoPlayerController handles video file access validation

**Threading:**
- AudioPlayer uses threading for background playback
- AudioGenerationService uses threading for batch generation (BatchProgressWindow modal)
- Main event loop handled by Tkinter mainloop()

---

*Architecture analysis: 2026-01-22*
