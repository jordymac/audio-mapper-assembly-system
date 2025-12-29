# Audio Mapper & Assembly System - Development Roadmap

**Last Updated**: 2025-12-29

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

### 4. Generation Progress Feedback
**Problem**: When user presses 'G' to generate audio, there's no visual feedback that generation has started or is in progress.

**User Experience Issue**:
- User presses 'G' → nothing visible happens immediately
- Takes several seconds for API response
- User doesn't know if key was registered
- No indication of progress or completion

**Proposed Solution**:
Show progress bar in waveform column during generation, then replace with actual waveform on completion.

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

**Related Feature**: This sets up the waveform column for future audio preview (#9), where clicking the waveform will play the audio.

**Implementation Tasks**:
- [ ] Add progress bar rendering in waveform column
- [ ] Show progress percentage during generation (0-100%)
- [ ] Replace progress bar with waveform on completion
- [ ] Add timeout handling (30s max)
- [ ] Show error state in waveform column if generation fails
- [ ] Support batch generation (multiple progress bars visible)

**Files Affected**:
- `services/audio_service.py` - Add progress callbacks during generation
- `ui/components/marker_row.py` - Render progress bar in waveform column
- `managers/waveform_manager.py` - Coordinate progress → waveform transition
- `audio_mapper.py` - Wire up generation progress updates

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

### 7. Metadata Management
**Current Issues**:
- [ ] `asset_id` field usage unclear
- [ ] `status` field not consistently updated
- [ ] Version history not tracked in template
- [ ] No creation/modification timestamps

**Proposed Metadata Schema**:
```json
{
  "time_ms": 150,
  "type": "sfx",
  "name": "SFX_00001_UI_Click",
  "prompt_data": {...},

  "asset_slot": "sfx_0",
  "asset_file": "SFX_00000.mp3",

  "metadata": {
    "createdAt": "2025-12-28T10:00:00Z",
    "modifiedAt": "2025-12-28T11:30:00Z",
    "status": "generated",  // not_generated | generating | generated | failed
    "currentVersion": 2,
    "versions": [
      {
        "versionNumber": 1,
        "asset_id": "elevenlabs-abc123",
        "asset_file": "SFX_00000_v1.mp3",
        "generatedAt": "2025-12-28T10:05:00Z",
        "prompt_data": {...}  // Snapshot of prompt used
      },
      {
        "versionNumber": 2,
        "asset_id": "elevenlabs-xyz789",
        "asset_file": "SFX_00000_v2.mp3",
        "generatedAt": "2025-12-28T11:30:00Z",
        "prompt_data": {...}
      }
    ]
  }
}
```

**Benefits**:
- Full version history with prompts
- Rollback to previous versions
- Track what prompts generated what audio
- Proper status tracking

**Migration Strategy**:
- [ ] Auto-migrate old format on import
- [ ] Maintain backward compatibility
- [ ] Default values for missing metadata

**Files Affected**:
- `audio_mapper.py` - All marker creation/edit logic
- Template JSON schema

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


### 9. Audio Preview
**Goal**: Play generated audio directly in the tool.

**Related Feature**: Builds on generation progress feedback (#4) - the waveform column will already show waveforms, this makes them clickable/playable.

**Waveform Column Evolution**:
```
1. Empty:      [              ]  (no audio yet)
2. Generating: [████████░░░░░░] 45%  (progress bar - feature #4)
3. Generated:  [~waveform~visual~]  (waveform appears)
4. Playable:   [~waveform~visual~] ▶️  (click to play - this feature)
```

**Features**:
- [ ] Click waveform to play/pause audio
- [ ] Play button next to each marker (alternative to clicking waveform)
- [ ] Scrub to marker position + auto-play
- [ ] Volume control
- [ ] Solo/mute tracks (Music/SFX/Voice)

**Implementation**:
- Use `pygame` or `pydub` for playback
- Display waveform using `matplotlib` or `PIL`

**Files Affected**:
- `audio_mapper.py` - Playback controls
- NEW: `audio_player.py` - Playback logic

---

### 11. Batch Operations
**Goal**: Apply operations to multiple markers at once.

**Features**:
- [ ] Select multiple markers (Ctrl+Click)
- [ ] Bulk delete
- [ ] Bulk regenerate
- [ ] Bulk tag/categorize
- [ ] Apply template to multiple markers

**Files Affected**:
- `audio_mapper.py` - Marker list selection logic
- `batch_progress_window.py` - Reuse for bulk ops

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
1. **Music Assembly Timing** (#2) - Core functionality unclear
2. **Remaining UI/UX Polish** (#3) - Dark mode support, hover states
3. **Generation Progress Feedback** (#4) - User needs feedback when pressing G

### Medium Priority
4. **BPM & Bar-Based Sections** (#5) - Quality of life improvement
5. **Metadata Management** (#7) - Foundation for future features

### Low Priority (Nice to Have)
6. **Prompt Library** (#6) - Can work around manually
7. **Audio Preview** (#9) - Can preview externally

### Future / Research Needed
8. **Batch Operations** (#11) - Requires selection UI design
9. **Variation Management UI** (#12) - Depends on metadata work

---

## 📋 Next Session Checklist

When starting next work session, tackle in this order:

**Immediate (This Week)**:
- [x] ~~Fix versioning bug (Issue #1)~~ ✅ COMPLETE
- [x] ~~Button styling and UI consistency (Issue #3)~~ ✅ COMPLETE
- [ ] Define music assembly timing behavior (Issue #2)
- [ ] Add generation loading indicator (Issue #4)
- [ ] Complete remaining UI polish (dark mode, hover states)

**Short Term (Next 2 Weeks)**:
- [ ] Design + implement BPM/bar input (Issue #5)
- [ ] Implement enhanced metadata schema (Issue #7)

**Medium Term (Next Month)**:
- [ ] Design prompt library system (Issue #6)
- [ ] Implement template save/load (Issue #6)
- [ ] Add audio preview (Issue #9)

---

## 💡 Ideas Parking Lot

Random ideas that need more thought:

- **Marker Colors**: Custom colors beyond type defaults
- **Timeline Zoom**: Magnify timeline for precise positioning
- **Grid Snap**: Snap markers to frame boundaries or BPM grid
- **Hotkey Customization**: User-defined keyboard shortcuts

**End of Roadmap**

This is a living document. Update as priorities shift and new issues/ideas emerge.
