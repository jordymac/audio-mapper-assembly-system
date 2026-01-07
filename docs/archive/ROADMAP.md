# Audio Mapper & Assembly System - Development Roadmap

**Last Updated**: 2025-12-30

This document outlines planned improvements, known issues, and feature ideas for the Audio Mapper & Assembly System.

---

## 🔴 Critical Issues

### 1. Versioning Logic Bug ✅ FIXED (2025-12-28)
**Problem**: When saving a newly created marker for the first time, it creates version 1 even though audio hasn't been generated yet. Then clicking "Generate" creates version 2.

**Expected Behavior**:
- First save should trigger generation → version 1
- Subsequent generations create version 2, 3, etc.

**Fix Applied**:
- [x] Don't create version until first generation completes
- Removed version creation from `PromptEditorWindow.on_save()` method
- Versions now created ONLY during generation (not on save)
- Workflow: Create → Save (no version) → Generate (v1) → Regenerate (v2, v3, etc.)

**Files Changed**:
- `ui/editors/prompt_editor.py` - Removed version creation from save logic
- `tests/test_version_history_ui.py` - Updated test to match new behavior
- `ui/components/marker_row.py` - Fixed diagnostic warnings

---

### 2. Music Assembly Timing & Duration Flexibility 📋 SPEC COMPLETE (2025-12-29)
**Problem**:
1. When generated music is longer than video, which portion gets used?
2. When creator extends video in Canva, music needs to extend too
3. Need control over which part of music track to use

**Solution Designed**:
- ✅ Generate long music tracks (2-3min) regardless of template duration
- ✅ User can select start offset (where in music track video 0:00 begins)
- ✅ Waveform visualization in popup editor for visual offset selection
- ✅ Offset validation: max_offset = audio_duration - video_duration
- ✅ Fades: 50ms default (subtle, not jarring)
- ✅ Multiple music markers supported (each with own offset)

**Comprehensive Spec Created**:
📄 See `docs/MUSIC_ASSEMBLY_SPEC.md` for full design document

**Data Model**:
```json
{
  "type": "music",
  "assemblyConfig": {
    "startOffsetMs": 30000,  // Start video at 30s into music
    "fadeInMs": 50,           // Default: 50ms
    "fadeOutMs": 50,          // Default: 50ms
    "targetDurationMs": null
  }
}
```

**Implementation Status**:
- [x] Problem analysis complete
- [x] Solution designed
- [x] UI mockups complete
- [x] Data model defined
- [x] Tech stack identified (numpy + moviepy + pygame)
- [ ] Phase 1: Backend implementation
- [ ] Phase 2: UI implementation
- [ ] Phase 3: Testing & documentation

**Files to Modify**:
- `core/models.py` - Add assemblyConfig to Marker
- `ui/editors/music_editor.py` - Add waveform preview section
- `assemble_audio.py` - Apply offset and fades
- `managers/waveform_manager.py` - Reuse for popup waveform

---

### 3. Export Center & Metadata Workflow 📋 SPEC COMPLETE (2025-12-30)
**Goal**: Create professional export workflow with metadata tagging and organized file structure for ingest team handoff.

**Solution Designed**:
- ✅ Dedicated Export Center window (File → Export Center, Cmd+E)
- ✅ Non-linear metadata editing (jump between markers)
- ✅ Type-specific category taxonomies (38 SFX categories from ElevenLabs)
- ✅ Assembly preview with video sync validation
- ✅ Organized export structure (MUSIC/, SFX/, VOICE/ folders)
- ✅ Individual + assembled metadata JSON files

**Comprehensive Specs Created**:
- 📄 `docs/ASSEMBLY_PLAN.md` - Multi-track assembly preview in main window
- 📄 `docs/METADATA_EXPORT_PLAN.md` - Export Center workflow and metadata structures

**Key Features**:
- Left panel: Marker list with completion checkmarks
- Right panel: Metadata editor (title, categories, notes, waveform, play)
- Bottom section: Assembly preview + export button
- Export creates organized folder with audio files + metadata JSONs

**Category Taxonomies**:
- **SFX**: 38 categories (UI Elements, Foley, Impacts, Nature, etc.)
- **Music**: Genre + Mood + Tempo + Intensity
- **Voice**: Gender + Age + Accent + Tone + Delivery

**Implementation Status**:
- [x] Requirements gathered
- [x] Assembly Plan complete (multi-track preview design)
- [x] Metadata Export Plan complete (Export Center design)
- [x] UI/UX designed (both assembly and export workflows)
- [x] Metadata structures defined
- [x] Category taxonomies finalized (SFX extracted from ElevenLabs)
- [x] Channel configuration finalized (stereo music + mono SFX/Voice)
- [x] Phase 1: Multi-track UI implemented (5 tracks with labels & volume sliders)
- [x] Phase 2: Assembly logic implemented (track assignment + audio generation)
- [x] Phase 3: Multi-track waveform visualization (waveforms + marker indicators)
- [ ] Phase 4: Playback integration (replace video audio with assembled preview)
- [ ] Phase 5: Export Center UI implementation
- [ ] Phase 6: Export functionality (metadata JSON generation)
- [ ] Phase 7: Polish & testing

**Files to Create/Modify**:

**Phase 1-2: Assembly Preview**
- `audio_mapper.py` - Multi-track waveform display, Assemble button UI
- `managers/waveform_manager.py` - Multi-track waveform generation
- `assemble_audio.py` - Multi-channel assembly logic (5-channel WAV)
- NEW: `ui/components/multi_track_display.py` - Multi-track visualization component

**Phase 3-4: Export Center & Metadata**
- NEW: `core/categories.py` - Category constants (38 SFX categories, etc.)
- `core/models.py` - Add metadata fields to Marker class
- NEW: `ui/export/export_center.py` - Export Center window
- `managers/file_handler.py` - Export folder structure logic, metadata JSON generation

---

## 🎨 UI/UX Issues

### 3. Button Styling & UI Consistency ✅ COMPLETE (2025-12-29)
**Completed Work**:
- ✅ All marker type buttons styled consistently:
  - SFX: Red (#F44336) with black text
  - Music: Blue (#2196F3) with black text
  - Voice: Green (#4CAF50) with black text
- ✅ All Save buttons: Blue (#2196F3) with black text
- ✅ Text input fields: Light gray background (#F5F5F5)
- ✅ Proper button relief and borders (raised, 2px)
- ✅ Consistent styling across all editor windows

**Remaining UI Tasks**:
- [ ] Some UI elements don't respect dark mode
- [ ] Hover states missing on some interactive elements
- [ ] Marker indicators on timeline styling
- [ ] Tooltip backgrounds
- [ ] Generation loading indicator (when pressing G)

**Strategy for Remaining Work**:
- Audit all widgets for COLORS usage
- Create widget factory functions that auto-apply theme
- Test in both light and dark modes

**Files Affected**:
- `ui/editors/prompt_editor.py` - Editor button styling ✅
- `ui/editors/music_section_editor.py` - Section editor styling ✅
- `audio_mapper.py` - Main window buttons ✅
- `color_scheme.py` - May need additional color definitions for dark mode

---

### 4. Generation Progress Feedback ✅ COMPLETE (2025-12-30)
**Problem**: When user presses 'G' to generate audio, there's no visual feedback that generation has started or is in progress.

**User Experience Issue**:
- User presses 'G' → nothing visible happens immediately
- Takes several seconds for API response
- User doesn't know if key was registered
- No indication of progress or completion

**Implemented Solution**:
Progress bar shown in waveform column during generation, replaced with actual waveform on completion.

**Design**: Waveform Column Progress Bar
```
✏️ 0:00.150  SFX  SFX_00001  [████████░░░░░░░░] 45%  (not yet generated)
✏️ 0:02.000  VOICE VOX_00001  [              ]       (not yet generated)
```
**How it works**:
- Progress bar appears in waveform column during generation (0-100%)
- Once complete, progress bar is replaced by actual waveform
- Visual progression fills the space where waveform will appear
- Non-blocking (can continue working on other markers)

**Benefits**:
- Uses otherwise-empty waveform column (no extra UI needed)
- Smooth transition: progress bar → waveform in same space
- Visually intuitive (filling = progress, waveform = complete)
- Supports batch generation (multiple progress bars visible simultaneously)
- Error states can show in same column (red bar or error icon)

**Related Feature**: This enables the waveform column for audio preview (#9), where clicking the waveform plays the audio.

**Completed Implementation**:
- [x] Add progress bar rendering in waveform column
- [x] Show progress percentage during generation (0-100%)
- [x] Replace progress bar with waveform on completion
- [x] Add timeout handling (30s max)
- [x] Show error state in waveform column if generation fails
- [x] Support batch generation (multiple progress bars visible)

**Files Modified**:
- `services/audio_service.py` - Added progress callbacks during generation
- `ui/components/marker_row.py` - Progress bar rendering in waveform column
- `managers/waveform_manager.py` - Progress → waveform transition coordination
- `audio_mapper.py` - Generation progress update wiring

---

## 🎵 Music Workflow Improvements

### 5. BPM & Bar-Based Sections
**Problem**: Hard to know how long a music section is in milliseconds. Natural to think in bars (e.g., "intro is 32 bars at 120 BPM").

**Proposed Solution**:
Add BPM + bar count input option alongside milliseconds.

**UI Mockup** (MusicSectionEditorWindow):
```
Duration Input Mode: ( ) Milliseconds  (•) Bars + BPM

[If Milliseconds selected]
Duration (ms): [_________]

[If Bars + BPM selected]
BPM: [120]
Bars: [32]
→ Calculated: 16000ms (displayed below)
```

**Data Structure**:
```json
{
  "sectionName": "Intro",
  "durationMs": 16000,
  "durationBars": 32,
  "bpm": 120,
  "positiveLocalStyles": [...]
}
```

**Implementation Notes**:
- Formula: `duration_ms = (bars * 4 * 60000) / bpm`
- Always store final `durationMs` for assembly
- Store `durationBars` + `bpm` as metadata for editing
- Allow switching between input modes

**Files Affected**:
- `audio_mapper.py` - MusicSectionEditorWindow UI
- Template JSON schema (backward compatible)

---

## 📚 Prompt Library System

### 6. Reusable Prompt Templates
**Goal**: Save commonly used prompts for quick reuse across projects.

**User Stories**:
- As a user, I want to save "Cinematic Orchestral Swell" as a preset
- As a user, I want to browse my saved SFX presets when adding a marker
- As a user, I want to share prompt templates with team members

**Proposed Features**:

#### 6.1 Save Prompt as Template
- [ ] Button in PromptEditorWindow: "Save as Template"
- [ ] Name template (e.g., "Cinematic Orchestral")
- [ ] Add tags (e.g., "epic", "music", "orchestral")
- [ ] Store in `~/.audio_mapper/templates/` or project `/templates/`

#### 6.2 Load Template
- [ ] Dropdown/browser in PromptEditorWindow
- [ ] Filter by type (SFX/Music/Voice)
- [ ] Search by name/tags
- [ ] Preview template details before loading

#### 6.3 Template Management
- [ ] Edit existing templates
- [ ] Delete templates
- [ ] Export/import template packs (JSON)
- [ ] Template categories/folders

**Data Structure**:
```json
{
  "templateId": "uuid-1234",
  "name": "Cinematic Orchestral Swell",
  "type": "music",
  "tags": ["epic", "orchestral", "cinematic"],
  "createdAt": "2025-12-28T10:00:00Z",
  "prompt_data": {
    "positiveGlobalStyles": ["orchestral", "cinematic", "epic"],
    "negativeGlobalStyles": ["electronic", "synth"],
    "sections": [...]
  }
}
```

**UI Design Ideas**:
- Combobox at top of editor: [Load Template ▼]
- Side panel with template browser (thumbnails + names)
- Context menu: Right-click marker → "Apply Template"

**Files Affected**:
- NEW: `template_manager.py` - CRUD operations for templates
- `audio_mapper.py` - Template UI integration
- NEW: `~/.audio_mapper/templates.json` - User template library

---

## 🔧 Technical Improvements

### 7. Metadata Management → See Export Center (#3)
**Status**: Comprehensive metadata system designed as part of Export Center workflow.

📄 **See `docs/METADATA_EXPORT_PLAN.md` for complete metadata structures**

**Key Changes from Old Approach**:
- Metadata captured during export (not during editing)
- Type-specific categorization (SFX/Music/Voice have different fields)
- Individual JSON files per audio file (not embedded in template)
- Separate assembled audio metadata JSON

**What's Defined**:
- ✅ Metadata fields for SFX, Music, Voice, Assembled audio
- ✅ Category taxonomies (38 SFX categories, Music genres/moods, Voice attributes)
- ✅ Export file structure (organized folders with metadata)
- ✅ Validation rules for required/optional fields

**Implementation Plan**:
- Part of Export Center implementation (#3)
- Phase 1: Add metadata fields to Marker class
- Phase 2: Export Center UI for metadata editing
- Phase 4: Generate metadata JSON files on export

---

### 8. Auto-Save Implementation
**Goal**: Automatically save project state to prevent data loss.

**Problem**:
- Users can lose work if app crashes before manual save
- No indication of unsaved changes
- Manual save workflow interrupts creative flow

**Auto-Save Implementation Steps**:
1. Create the save/load module → handles JSON read/write
2. Add auto-save timer → saves every N seconds when changes detected
3. Track dirty state → flag when markers/template modified
4. Visual indicator → show "saving..." / "saved" status
5. Recovery on crash → load last auto-saved state on startup

**Files Affected**:
- NEW: `managers/autosave_manager.py` - Auto-save logic and timer
- `audio_mapper.py` - Integrate auto-save status indicator
- `managers/file_handler.py` - Reuse for save/load operations

---


### 9. Audio Preview in Marker Section ✅ COMPLETE (2025-12-30)
**Goal**: Play generated audio directly in the tool from marker rows.

**Related Feature**: Builds on generation progress feedback (#4) - the waveform column shows waveforms, this makes them clickable/playable.

**Waveform Column Evolution**:
```
1. Empty:      [              ]  (no audio yet)
2. Generating: [████████░░░░░░] 45%  (progress bar - feature #4)
3. Generated:  [~waveform~visual~]  (waveform appears)
4. Playable:   [~waveform~visual~] ▶️  (click to play - this feature)
```

**Implemented Features**:
- [x] Click waveform to play/pause audio
- [x] Waveform visualization in marker rows
- [x] Playback integration with marker system
- [ ] Play button next to each marker (alternative to clicking waveform) - Not needed, waveform click works well
- [ ] Scrub to marker position + auto-play - Future enhancement
- [ ] Volume control - Future enhancement
- [ ] Solo/mute tracks (Music/SFX/Voice) - Future enhancement

**Implementation Details**:
- Uses `pygame` for audio playback
- Waveform visualization integrated in marker row component
- Click waveform to toggle play/pause
- Visual feedback during playback

**Files Modified**:
- `ui/components/marker_row.py` - Waveform click handlers and playback controls
- `managers/waveform_manager.py` - Waveform display integration
- Audio playback logic integrated into marker row system

---

### 12. Variation Management UI
**Goal**: Compare multiple audio versions side-by-side.

**Features**:
- [ ] Version selector dropdown per marker
- [ ] A/B comparison (play v1 vs v2)
- [ ] Visual diff of prompts between versions
- [ ] Mark preferred version

**Files Affected**:
- `audio_mapper.py` - Version comparison UI
- Template JSON with version metadata


---

## 🎯 Priority Matrix

### High Priority (Do Next)
1. **Export Center & Metadata Workflow** (#3) - Critical for ingest team handoff
2. **Music Assembly Timing** (#2) - Core functionality for music markers
3. **Remaining UI/UX Polish** (#4) - Dark mode support, hover states

### Medium Priority
4. **BPM & Bar-Based Sections** (#5) - Quality of life improvement
5. **Auto-Save Implementation** (#8) - Prevent data loss
6. **Prompt Library** (#6) - Reusable templates for faster workflow

### Low Priority (Nice to Have)
7. **Batch Operations** (#11) - Requires selection UI design
8. **Variation Management UI** (#12) - Depends on metadata work

---

## 📋 Next Session Checklist

When starting next work session, tackle in this order:

**Immediate (This Week)**:
- [x] ~~Fix versioning bug (Issue #1)~~ ✅ COMPLETE
- [x] ~~Button styling and UI consistency (Issue #3)~~ ✅ COMPLETE
- [x] ~~Add generation loading indicator (Issue #4)~~ ✅ COMPLETE
- [x] ~~Audio preview in marker section (Issue #9)~~ ✅ COMPLETE
- [x] ~~Design Export Center & Metadata workflow (Issue #3)~~ ✅ COMPLETE
- [ ] Implement Export Center Phase 1: Data structures
- [ ] Complete remaining UI polish (dark mode, hover states)

**Short Term (Next 2 Weeks)**:
- [ ] Implement Export Center Phase 2: UI window
- [ ] Implement Export Center Phase 3: Assembly preview
- [ ] Implement Export Center Phase 4: Export functionality
- [ ] Define music assembly timing behavior (Issue #2)

**Medium Term (Next Month)**:
- [ ] Export Center Phase 5: Polish & testing
- [ ] Design + implement BPM/bar input (Issue #5)
- [ ] Design prompt library system (Issue #6)

---

## 💡 Ideas Parking Lot

Random ideas that need more thought:

- **Marker Colors**: Custom colors beyond type defaults
- **Timeline Zoom**: Magnify timeline for precise positioning
- **Grid Snap**: Snap markers to frame boundaries or BPM grid
- **Hotkey Customization**: User-defined keyboard shortcuts

**End of Roadmap**

This is a living document. Update as priorities shift and new issues/ideas emerge.
