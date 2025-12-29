# Refactoring Plan - Categorized by Risk Level

## Overview
AudioMapperGUI is a **2,665-line GOD CLASS** that needs to be broken down into focused, maintainable components.

---

## 🟢 LOW RISK - Start Here (Safe, High Value)

### 1. Extract Data Models
**Risk**: Very Low | **Impact**: High | **Effort**: Small
- Create `models.py` with data classes:
  - `Marker` dataclass (currently dict)
  - `PromptData` dataclass
  - `VideoInfo` dataclass
  - `AudioVersion` dataclass
- Benefits: Type safety, validation, better IDE support
- Why Low Risk: Pure data structures, no behavior changes

### 2. Extract Waveform Manager
**Risk**: Low | **Impact**: Medium | **Effort**: Small
- Create `waveform_manager.py` with class `WaveformManager`
- Extract 6 methods:
  - `extract_and_display_waveform()`
  - `calculate_waveform_data()`
  - `draw_waveform()`
  - `update_waveform_position()`
  - `on_waveform_click()`
  - `on_waveform_resize()`
- Why Low Risk: Self-contained, minimal dependencies on GUI state

### 3. Extract Filmstrip Manager
**Risk**: Low | **Impact**: Medium | **Effort**: Small
- Create `filmstrip_manager.py` with class `FilmstripManager`
- Extract 6 methods:
  - `extract_filmstrip_frames()`
  - `draw_filmstrip()`
  - `update_filmstrip_position()`
  - `on_filmstrip_click()`
  - `on_filmstrip_resize()`
  - `create_filmstrip_display()`
- Why Low Risk: Self-contained display component, clear boundaries

### 4. Extract File I/O Handler
**Risk**: Low | **Impact**: Medium | **Effort**: Small
- Create `file_handler.py` with functions:
  - `import_markers_from_json()`
  - `export_markers_to_json()`
  - `load_project_state()`
  - `save_project_state()`
- Why Low Risk: Pure I/O operations, no complex state

---

## 🟡 MEDIUM RISK - Next Phase (Careful Testing Required)

### 5. Extract Video Player Controller
**Risk**: Medium | **Impact**: High | **Effort**: Medium
- Create `video_controller.py` with class `VideoController`
- Extract ~15 methods:
  - Video loading and timeline management
  - Playback controls (play, pause, seek)
  - Frame stepping and time updates
- Why Medium Risk: Shared state with timeline UI, needs careful interface design
- Testing: Verify playback, seeking, frame stepping still work correctly

### 6. Extract Marker Version Manager
**Risk**: Medium | **Impact**: Medium | **Effort**: Medium
- Create `version_manager.py` with class `MarkerVersionManager`
- Extract version-related methods:
  - `migrate_marker_to_new_format()`
  - `get_current_version_data()`
  - `add_new_version()`
  - `rollback_to_version()`
  - `migrate_marker_to_version_format()`
- Why Medium Risk: Version data structure changes, migration logic is critical
- Testing: Verify all existing projects can load, version history preserved

### 7. Decouple Commands from GUI
**Risk**: Medium | **Impact**: High | **Effort**: Medium
- Refactor `commands.py`:
  - Commands should not directly reference `self.gui`
  - Pass callbacks or use events/observers
  - Commands should work with data models, not GUI widgets
- Why Medium Risk: Changes command execution flow
- Testing: Verify undo/redo still works for all operations

### 8. Extract Keyboard Shortcut Manager
**Risk**: Medium | **Impact**: Low | **Effort**: Small
- Create `keyboard_manager.py` with class `KeyboardShortcutManager`
- Extract ~12 shortcut methods
- Why Medium Risk: Event binding can be tricky, but isolated

---

## 🔴 HIGH RISK - Final Phase (Requires Extensive Testing)

### 9. Extract Audio Generator Service
**Risk**: High | **Impact**: High | **Effort**: Large
- Create `audio_service.py` with class `AudioGenerationService`
- Extract ~15 audio-related methods:
  - ElevenLabs API integration
  - Audio generation (single & batch)
  - Background thread management
  - Progress tracking
  - Error handling
- Why High Risk:
  - Threading/async complexity
  - External API dependency
  - Critical functionality (data loss risk)
  - Complex error handling paths
- Testing Required:
  - Single generation with success/failure paths
  - Batch operations with cancellation
  - Network error handling
  - Thread safety verification
  - Progress callbacks

### 10. Extract Marker Manager/Repository
**Risk**: High | **Impact**: Very High | **Effort**: Large
- Create `marker_manager.py` with class `MarkerManager`
- Extract ~20 marker management methods:
  - Add, delete, update markers
  - Selection management
  - Drag-and-drop logic
  - Marker list synchronization
- Why High Risk:
  - Core business logic
  - Touches almost everything
  - State synchronization critical
  - UI updates depend on this
- Testing Required:
  - All CRUD operations
  - Undo/redo integration
  - Selection state management
  - UI synchronization

### 11. Refactor AudioMapperGUI to Coordinator
**Risk**: Very High | **Impact**: Very High | **Effort**: Large
- After all extractions, AudioMapperGUI becomes:
  - Pure UI layout/creation
  - Coordination between components
  - Event routing
- Why Very High Risk:
  - Touches entire application
  - Integration point for everything
  - Many refactored pieces must work together
- Testing Required:
  - Full regression testing
  - All features end-to-end
  - Cross-component interactions

---

## 📊 Recommended Execution Order

### Sprint 1: Foundation (Low Risk)
1. ✅ Extract data models (`models.py`)
2. ✅ Extract waveform manager
3. ✅ Extract filmstrip manager
4. ✅ Extract file I/O handler

**Goal**: Reduce AudioMapperGUI by ~400 lines, establish patterns

### Sprint 2: Controllers (Medium Risk)
5. ✅ Extract video controller
6. ✅ Extract version manager
7. ✅ Decouple commands from GUI
8. ✅ Extract keyboard manager

**Goal**: Reduce AudioMapperGUI by ~800 lines, isolate business logic

### Sprint 3: Core Services (High Risk)
9. ✅ Extract audio generator service
10. ✅ Extract marker manager

**Goal**: Reduce AudioMapperGUI by ~1,000 lines, separate concerns

### Sprint 4: Integration (Very High Risk)
11. ⬜ Refactor AudioMapperGUI to coordinator
12. ⬜ Add comprehensive tests
13. ⬜ Performance optimization
14. ⬜ Documentation

**Goal**: Clean, maintainable architecture

---

## Success Metrics

### After Sprint 1 (Low Risk) Done
- AudioMapperGUI: ~2,265 lines (from 2,665)
- New modules: 4
- Test coverage: 40%+

### After Sprint 2 (Medium Risk) Done
- AudioMapperGUI: ~1,465 lines
- New modules: 8
- Test coverage: 60%+

### After Sprint 3 (High Risk) Done
- AudioMapperGUI: ~465 lines
- New modules: 10
- Test coverage: 80%+

### After Sprint 4 (Final)
- AudioMapperGUI: ~300 lines (just UI coordination)
- New modules: 12+
- Test coverage: 90%+
- All features working
- Performance same or better

---

## Risk Mitigation Strategies

### For All Phases
- ✅ Git commit after each extraction
- ✅ Run existing tests after each change
- ✅ Manual smoke test of affected features
- ✅ Keep old code commented for 1-2 commits

### For Medium Risk
- Create integration tests before refactoring
- Verify state synchronization
- Test undo/redo paths

### For High Risk
- Full feature freeze during refactor
- Create comprehensive test suite first
- Pair programming/code review
- Feature flags for gradual rollout
- Keep parallel implementation for 1 release

---

## Current Status
- ✅ Phase 0: Extracted color_scheme, commands, history_manager, tooltip
- ✅ Sprint 1 (Low Risk): ALL COMPLETE
  - ✅ models.py
  - ✅ waveform_manager.py
  - ✅ filmstrip_manager.py
  - ✅ file_handler.py
- ✅ Sprint 2 (Medium Risk): COMPLETE (4/4 complete)
  - ✅ video_player_controller.py
  - ✅ version_manager.py
  - ✅ Decouple commands from GUI
  - ✅ Extract keyboard manager
- ✅ Sprint 3 (High Risk): Done
- ⬜ Sprint 4 (Integration): Not started
