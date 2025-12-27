# Project Structure Reorganization Plan

## Current Issues
- 11 test files scattered in root directory
- Duplicate `tools/` folder with old copies of main files
- Extracted modules (color_scheme, commands, etc.) in root
- 6 documentation files in root
- Old venv backups cluttering directory

## Proposed Clean Structure

```
audio-mapper-assembly-system/
├── src/                              # Main application code
│   ├── __init__.py
│   ├── audio_mapper.py              # Main GUI application
│   ├── assemble_audio.py            # Audio assembly CLI tool
│   ├── elevenlabs_api.py            # ElevenLabs API integration
│   │
│   ├── ui/                          # UI Components
│   │   ├── __init__.py
│   │   ├── color_scheme.py         # Theme/color system
│   │   ├── tooltip.py              # Tooltip widget
│   │   ├── batch_progress_window.py    # (Future) Batch progress dialog
│   │   ├── prompt_editor_window.py     # (Future) Main editor window
│   │   ├── music_section_editor.py     # (Future) Music section editor
│   │   └── widgets/                    # (Future) Custom widgets
│   │       ├── __init__.py
│   │       ├── timeline.py
│   │       ├── marker_list.py
│   │       └── video_player.py
│   │
│   ├── commands/                    # Command Pattern (Undo/Redo)
│   │   ├── __init__.py
│   │   ├── base.py                 # Command base class
│   │   ├── marker_commands.py      # Add/Edit/Delete/Move marker commands
│   │   └── history_manager.py      # Undo/redo stack
│   │
│   ├── models/                      # Data Models (Future)
│   │   ├── __init__.py
│   │   ├── marker.py               # Marker data structure
│   │   ├── template.py             # Template data structure
│   │   └── metadata.py             # Metadata schemas
│   │
│   ├── services/                    # Business Logic (Future)
│   │   ├── __init__.py
│   │   ├── template_manager.py     # Load/save templates
│   │   ├── audio_generator.py      # API calls to ElevenLabs
│   │   └── audio_assembler.py      # Audio assembly logic
│   │
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── create_test_audio.py    # Generate test audio files
│       └── helpers.py              # Misc helper functions
│
├── tests/                           # All test files
│   ├── __init__.py
│   ├── test_audio_mapper.py
│   ├── test_assemble_audio.py
│   ├── test_audio_playback.py
│   ├── test_auto_assembly.py
│   ├── test_batch_operations.py
│   ├── test_elevenlabs_integration.py
│   ├── test_enhanced_rows.py
│   ├── test_generation_button.py
│   ├── test_polish.py
│   ├── test_selection_sync.py
│   ├── test_version_history_ui.py
│   └── test_version_management.py
│
├── docs/                            # Documentation
│   ├── README.md                   # User-facing docs
│   ├── CLAUDE.md                   # AI assistant instructions
│   ├── ROADMAP.md                  # Development roadmap
│   ├── REDESIGN_PLAN.md            # Historical design notes
│   ├── IMPLEMENTATION_COMPLETE.md  # Completed features log
│   └── inline_generation_plan.md   # Feature planning doc
│
├── template_maps/                   # Example/saved templates
│   └── (user JSON templates)
│
├── generated_audio/                 # Output audio files
│   ├── music/
│   ├── sfx/
│   └── voice/
│
├── .gitignore
├── .env.local                       # Local environment config
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project metadata
└── run.sh                          # Launch script
```

## Migration Steps

### Phase 1: Create New Structure (Safe - No Breaking Changes)
1. Create `src/` directory structure
2. Create `tests/` consolidated directory
3. Create `docs/` directory
4. Keep originals in place (don't break anything yet)

### Phase 2: Move Files
1. Move extracted modules to `src/ui/` and `src/commands/`
2. Move all test files to `tests/`
3. Move all docs to `docs/`
4. Update imports in moved files

### Phase 3: Update Import Paths
1. Update `audio_mapper.py` imports from relative to package imports
2. Update test file imports
3. Add `__init__.py` files for package exports

### Phase 4: Cleanup
1. Remove `tools/` folder (duplicates)
2. Remove old venv backups
3. Update `run.sh` to reference new paths
4. Update `.gitignore` if needed

## Import Changes After Migration

### Before (Current):
```python
from color_scheme import COLORS
from commands import AddMarkerCommand, DeleteMarkerCommand
from history_manager import HistoryManager
from tooltip import ToolTip
```

### After (Package Structure):
```python
from src.ui.color_scheme import COLORS
from src.ui.tooltip import ToolTip
from src.commands import (
    AddMarkerCommand,
    DeleteMarkerCommand,
    MoveMarkerCommand,
    EditMarkerCommand,
    GenerateAudioCommand
)
from src.commands.history_manager import HistoryManager
```

### Or with proper `__init__.py` exports:
```python
from src.ui import COLORS, ToolTip
from src.commands import (
    AddMarkerCommand,
    DeleteMarkerCommand,
    MoveMarkerCommand,
    EditMarkerCommand,
    GenerateAudioCommand,
    HistoryManager
)
```

## Benefits

✅ **Cleaner Root**: Only config files and key docs in root
✅ **Logical Grouping**: Related code lives together
✅ **Easier Testing**: All tests in one place
✅ **Future Scalability**: Clear place for new modules
✅ **IDE Support**: Better autocomplete and navigation
✅ **Standard Python**: Follows community best practices

## Next Steps

**Option A - Full Migration Now:**
- Do all phases in one go
- ~30 minutes of work
- Tests may need fixing

**Option B - Gradual Migration:**
- Phase 1 now (create structure)
- Phase 2 next session (move files)
- Phase 3 as we refactor (update imports)

**Option C - Hybrid (Recommended):**
- Move tests and docs now (safe, no import changes)
- Move src modules as we refactor them
- Keeps working code working
