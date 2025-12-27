# Audio Mapper Redesign - Implementation Plan

**Date:** 2025-12-27
**Project:** Audio Mapper & Assembly System
**Goal:** Redesign UI from single prompt field to type-specific pop-up editors

---

## Project Context

Redesigning the Audio Mapper tool to support structured, type-specific prompts for AI audio generation. Moving from a simple text area to dedicated editors for SFX, Voice, and Music markers with rich prompt structures.

---

## ✅ Already Implemented

The following features are already working and don't need to be rebuilt:

1. **Undo/Redo System** - Full Command pattern (lines 36-150)
2. **Color-coded markers** - Timeline/waveform markers use Red/Green/Blue (lines 1418-1424)
3. **Marker dragging** - Drag-to-reposition on timeline (lines 1277-1357)
4. **Keyboard shortcuts** - Comprehensive shortcuts including Cmd+Z/Ctrl+Z (lines 443-494)
5. **Export JSON** - Working export functionality (lines 1495-1525)
6. **Marker selection** - Listbox selection and jump-to-marker works
7. **Video playback** - OpenCV-based video player with frame-accurate scrubbing
8. **Waveform visualization** - Audio waveform overlay on timeline
9. **Filmstrip display** - Video thumbnail strip

---

## 📋 Implementation Checkpoints

### ✅ Checkpoint 1: Data Structure Migration - COMPLETED

**Goal:** Update marker data format from simple "prompt" string to structured "prompt_data"

**Current Format:**
```python
marker = {
    "time_ms": 150,
    "type": "sfx",
    "prompt": "UI whoosh, subtle",  # ← Simple string
    "asset_slot": "sfx_0",
    "asset_file": "SFX_00000.mp3"
}
```

**New Format:**
```python
# SFX Marker
{
    "time_ms": 150,
    "type": "sfx",
    "prompt_data": {
        "description": "UI whoosh, subtle"
    },
    "asset_id": null,
    "status": "not yet generated"
}

# Voice Marker
{
    "time_ms": 2000,
    "type": "voice",
    "prompt_data": {
        "voice_profile": "Warm female, mid-30s",
        "text": "Camera roll lately..."
    },
    "asset_id": null,
    "status": "not yet generated"
}

# Music Marker
{
    "time_ms": 0,
    "type": "music",
    "prompt_data": {
        "positiveGlobalStyles": ["electronic", "fast-paced"],
        "negativeGlobalStyles": ["acoustic", "slow"],
        "sections": [
            {
                "sectionName": "Intro",
                "durationMs": 3000,
                "positiveLocalStyles": ["rising synth"],
                "negativeLocalStyles": ["soft pads"],
                "lines": []  # Purpose TBD - see Questions section
            }
        ]
    },
    "asset_id": null,
    "status": "not yet generated"
}
```

**Tasks:**
- [x] Add migration function to convert old → new format
- [x] Update `add_marker()` to create new structure (lines 1282-1351)
- [x] Keep backward compatibility (handle both formats in display/export)
- [x] Add helper methods: `get_prompt_preview()` for display

**Deliverable:** ✅ Markers use new structure internally, old format still loads

**Files Modified:** `audio_mapper.py`
- Added `migrate_marker_to_new_format()` (lines 569-618)
- Added `get_prompt_preview()` (lines 620-649)
- Added `create_default_prompt_data()` (lines 651-671)
- Updated `add_marker()` to create new prompt_data structure (lines 1282-1351)
- Updated `update_marker_list()` to use helper function (lines 1353-1366)

**Completion Date:** 2025-12-27

**Notes:**
- All new markers now use `prompt_data` structure
- Backward compatibility maintained: `get_prompt_preview()` handles both old and new formats
- Migration function ready for future import feature
- Export already works with new format (no changes needed)

**Approval Status:** ✅ Completed and Ready for Checkpoint 2

---

### ✅ Checkpoint 2: Main Window UI Redesign - COMPLETED

**Goal:** Replace type dropdown + prompt text area with three separate buttons

**Old UI:**
```
┌─────────────────────────────────┐
│ Type: [dropdown ▼]             │
│ Prompt: ┌─────────────────────┐ │
│         │ [large text area]   │ │
│         │                     │ │
│         └─────────────────────┘ │
│              [Add Marker (M)]   │
└─────────────────────────────────┘
```

**New UI:**
```
┌─────────────────────────────────┐
│ Add Marker: [SFX] [Music] [Voice] │
└─────────────────────────────────┘
```

**Tasks:**
- [x] Remove `create_marker_controls()` type dropdown and prompt text area
- [x] Add three colored buttons:
  - **[SFX]** - Red background (#F44336)
  - **[Music]** - Blue background (#2196F3)
  - **[Voice]** - Green background (#4CAF50)
- [x] Each button creates marker at playhead with empty prompt_data
- [x] Update keyboard shortcuts - 'M' key now defaults to SFX marker

**Deliverable:** ✅ Main window with three-button interface, markers created with empty prompt_data

**Files Modified:** `audio_mapper.py`
- Updated `create_marker_controls()` - Three button design (lines 342-391)
- Added `add_marker_by_type(marker_type)` - Creates markers with empty prompt_data (lines 1288-1324)
- Updated `add_marker()` - Legacy support, defaults to SFX (lines 1326-1330)
- Removed prompt_text widget bindings (lines 492-498)

**Completion Date:** 2025-12-27

**Notes:**
- Three buttons create markers with empty but valid prompt_data structures
- Markers will show "(no prompt)" or empty in list until edited
- 'M' keyboard shortcut now adds SFX marker by default
- Removed all references to old prompt text area widget
- Buttons use color-coding matching timeline markers (Red/Blue/Green)

**Approval Status:** ✅ Completed and Ready for Checkpoint 3

---

### ✅ Checkpoint 3: Enhanced Marker List Display - COMPLETED

**Goal:** Add edit icons and better formatting to marker listbox

**Old Display:**
```
  0.150s  [sfx        ]  UI whoosh, subtle
```

**New Display:**
```
✏️ 0:00.150  SFX      (not yet generated)
✏️ 3:20.000  MUSIC    (not yet generated)
✏️ 11:50.000 SFX      (not yet generated)
```

**Tasks:**
- [x] Update `update_marker_list()` to show new format
- [x] Add edit icon (✏️) to each row
- [x] Show status field instead of prompt preview
  - "not yet generated" (default)
  - Asset ID once generated (e.g., "MUS_00001")
- [x] Add double-click handler to open editor
- [x] Format time as MM:SS.mmm instead of decimal seconds

**Deliverable:** ✅ Marker list with edit icons, cleaner formatting, double-click handler

**Files Modified:** `audio_mapper.py`
- Updated `update_marker_list()` - New format with edit icon, MM:SS.mmm time, status (lines 1296-1324)
- Added `on_marker_double_click()` - Opens editor placeholder (lines 1336-1353)
- Added double-click binding to marker listbox (line 422)

**Completion Date:** 2025-12-27

**Notes:**
- Time formatted as M:SS.mmm (e.g., "0:00.150", "3:20.000")
- Type shown in uppercase (SFX, MUSIC, VOICE)
- Status shows "not yet generated" by default, or asset_id if populated
- Double-click currently shows placeholder message (editor window in Checkpoint 4)
- Edit icon (✏️) displayed at start of each row
- Timeline markers remain color-coded (Red/Green/Blue)

**Approval Status:** ✅ Completed and Ready for Checkpoint 4

---

### ✅ Checkpoint 4: Pop-up Editor Framework - COMPLETED

**Goal:** Create base modal window that opens when edit icon is clicked

**Window Structure:**
```
┌──────────────────────────────────┐
│ Edit Marker: 0:00.150            │
├──────────────────────────────────┤
│ Type: [SFX ▼]  (dropdown)        │
├──────────────────────────────────┤
│                                  │
│ [Content area - changes based    │
│  on selected type]               │
│                                  │
├──────────────────────────────────┤
│          [Cancel] [Save]         │
└──────────────────────────────────┘
```

**Tasks:**
- [x] Create `PromptEditorWindow` class (extends tk.Toplevel)
- [x] Make window modal (grab_set, transient)
- [x] Position centered on parent window
- [x] Add type dropdown at top
  - Values: ["sfx", "music", "voice"]
  - Allows changing marker type after creation
  - When changed, update content area dynamically
- [x] Add dynamic content frame (swaps based on type)
- [x] Add Cancel/Save buttons at bottom
- [x] Handle window close event (treat as Cancel)
- [x] Integrate with double-click handler

**Deliverable:** ✅ Pop-up window opens/closes, type dropdown works, content area shows placeholders

**Files Modified:** `audio_mapper.py`
- Added `PromptEditorWindow` class (lines 152-317)
  - Modal window setup with parent centering
  - Type dropdown with dynamic content switching
  - Placeholder content areas for each type
  - Cancel/Save button handlers
- Updated `on_marker_double_click()` - Opens editor (lines 1503-1513)
- Added `open_marker_editor()` - Creates editor window (lines 1515-1523)
- Added `on_marker_edited()` - Save callback handler (lines 1525-1538)

**Completion Date:** 2025-12-27

**Notes:**
- Window is fully modal (blocks parent until closed)
- Centered on parent window automatically
- Type dropdown functional - updates placeholder when changed
- Cancel/close discards changes, Save calls callback
- Content placeholders: "SFX Editor (Coming in Checkpoint 5)" etc.
- Undo/redo for editing will be added in Checkpoint 5

**Approval Status:** ✅ Completed and Ready for Checkpoint 5

---

### 🎯 Checkpoint 5: SFX Editor Implementation

**Goal:** Implement simplest editor (single description field)

**SFX Editor Layout:**
```
┌──────────────────────────────────┐
│ Edit Marker: 0:00.150            │
├──────────────────────────────────┤
│ Type: [SFX ▼]                    │
├──────────────────────────────────┤
│ Description:                     │
│ ┌──────────────────────────────┐ │
│ │ UI whoosh, subtle            │ │
│ └──────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│          [Cancel] [Save]         │
└──────────────────────────────────┘
```

**Tasks:**
- [x] Create `create_sfx_content()` method in PromptEditorWindow
- [x] Add description text field (multi-line, 3-4 rows)
- [x] Load existing `prompt_data.description` when opening
- [x] Save button updates marker's `prompt_data.description`
- [x] Create `EditMarkerCommand` class for undo/redo support
  - Stores old and new prompt_data
  - Integrates with existing HistoryManager
- [x] Add validation: description cannot be empty
- [x] Test: Edit → Save → Undo → Redo

**Deliverable:** Working SFX editor with undo/redo support

**Files Modified:** `audio_mapper.py` (PromptEditorWindow class, new EditMarkerCommand)

**Implementation Notes:**

Created `EditMarkerCommand` class (lines 106-122) following existing Command pattern:
- Stores copies of both old and new marker states
- Properly integrates with HistoryManager
- Supports full undo/redo for marker edits

Implemented `create_sfx_content()` method (lines 325-360):
- Multi-line text widget (4 rows) with word wrapping
- Loads existing description from `prompt_data.description`
- Clean layout with label and hint text
- Hint: "Describe the sound effect to be generated (e.g., 'UI click, subtle, clean')"

Updated `on_save()` method (lines 385-432):
- Type-specific validation routing
- `save_sfx_data()` validates description is not empty
- Shows messagebox warning if validation fails
- Only saves and closes if validation passes

Updated `on_marker_edited()` (lines 1641-1650):
- Now uses `EditMarkerCommand` for all marker edits
- Full undo/redo support working

Updated `update_content_area()` (lines 302-378):
- Calls `create_sfx_content()` for SFX type
- Placeholder methods for voice and music types (Checkpoints 6-8)

**Approval Status:** ✅ Completed and Ready for Checkpoint 6

---

### 🎯 Checkpoint 6: Voice Editor Implementation

**Goal:** Two-field editor (voice profile + text to speak)

**Voice Editor Layout:**
```
┌──────────────────────────────────┐
│ Edit Marker: 2:00.000            │
├──────────────────────────────────┤
│ Type: [Voice ▼]                  │
├──────────────────────────────────┤
│ Voice Profile:                   │
│ ┌──────────────────────────────┐ │
│ │ Warm female, mid-30s         │ │
│ └──────────────────────────────┘ │
│                                  │
│ Text to Speak:                   │
│ ┌──────────────────────────────┐ │
│ │ Camera roll lately...        │ │
│ └──────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│          [Cancel] [Save]         │
└──────────────────────────────────┘
```

**Tasks:**
- [x] Create `create_voice_content()` method
- [x] Add two text fields:
  - Voice profile (single line entry)
  - Text to speak (4 rows, multi-line)
- [x] Load existing `prompt_data.voice_profile` and `prompt_data.text`
- [x] Save updates both fields in prompt_data
- [x] Uses same EditMarkerCommand as SFX
- [x] Add validation: text required, voice_profile optional
- [x] Test: Create Voice marker → Edit → Save → Verify data persists

**Deliverable:** Working Voice editor

**Files Modified:** `audio_mapper.py` (PromptEditorWindow class)

**Implementation Notes:**

Implemented `create_voice_content()` method (lines 362-422):
- Voice Profile: Single-line Entry widget (optional field)
- Text to Speak: Multi-line Text widget (4 rows, required field)
- Loads existing data from `prompt_data.voice_profile` and `prompt_data.text`
- Clean layout with labels and hint text for each field
- Voice profile hint: "Optional: e.g., 'Warm female narrator, Australian accent'"
- Text hint: "Required: The exact words to be spoken"

Updated `save_voice_data()` method (lines 477-496):
- Captures voice_profile from Entry widget
- Captures text from Text widget
- Validation: Only text field is required (voice_profile can be empty)
- Shows warning messagebox if text is empty
- Saves both fields to `prompt_data.voice_profile` and `prompt_data.text`
- Returns True/False for validation status

Design decision: Voice profile is optional because users might want to use a default voice or specify the voice elsewhere in their pipeline. The text to speak is always required since it's the core content.

**Approval Status:** ✅ Completed and Ready for Checkpoint 7

---

### 🎯 Checkpoint 7: Music Editor (Part 1 - Global Styles)

**Goal:** Music editor WITHOUT section editing functionality yet

**Music Editor Layout:**
```
┌──────────────────────────────────┐
│ Edit Marker: 0:00.000            │
├──────────────────────────────────┤
│ Type: [Music ▼]                  │
├──────────────────────────────────┤
│ Global Positive Styles:          │
│ ┌──────────────────────────────┐ │
│ │ electronic, fast-paced       │ │
│ └──────────────────────────────┘ │
│                                  │
│ Global Negative Styles:          │
│ ┌──────────────────────────────┐ │
│ │ acoustic, slow, ambient      │ │
│ └──────────────────────────────┘ │
│                                  │
│ Sections:                        │
│ ┌──────────────────────────────┐ │
│ │ Intro - 3000ms          [✏️] │ │
│ │ Peak Drop - 4000ms      [✏️] │ │
│ └──────────────────────────────┘ │
│ [+ Add Section]                  │
│                                  │
├──────────────────────────────────┤
│          [Cancel] [Save]         │
└──────────────────────────────────┘
```

**Tasks:**
- [x] Create `create_music_content()` method
- [x] Add two text areas: positive/negative global styles
- [x] Add sections list (Listbox, read-only for now)
- [x] "Add Section" button creates placeholder section:
  ```python
  {
      "sectionName": "Section 1",
      "durationMs": 1000,
      "positiveLocalStyles": [],
      "negativeLocalStyles": [],
      "lines": []
  }
  ```
- [x] Section list shows: "Section Name - Duration"
- [x] Sections not editable (editing will come in Checkpoint 8)
- [x] Save updates global styles only
- [x] Load existing `prompt_data` when opening

**Deliverable:** Music editor with global styles working, sections display but not editable

**Files Modified:** `audio_mapper.py` (PromptEditorWindow class)

**Implementation Notes:**

Implemented `create_music_content()` method (lines 424-546):
- **Global Positive Styles**: Text widget (3 rows) for comma-separated styles
- **Global Negative Styles**: Text widget (3 rows) for styles to avoid
- **Sections Listbox**: Displays all sections as "Section Name - Duration"
- **Add Section button**: Creates placeholder sections with default structure
- **Remove Section button**: Removes selected section from list
- Scrollbar for sections list
- Loads existing data from `prompt_data.positiveGlobalStyles`, `negativeGlobalStyles`, and `sections`
- Note displayed: "Section editing will be available in Checkpoint 8"

Helper methods added:
- `update_music_sections_list()` (lines 548-557): Refreshes sections listbox display
- `add_music_section()` (lines 559-581): Creates new placeholder section with auto-incremented name
- `remove_music_section()` (lines 583-598): Removes selected section with validation

Updated `save_music_data()` method (lines 665-700):
- Parses comma-separated styles from text widgets into lists
- Validation: At least one positive style required
- Saves both positive and negative styles to `prompt_data`
- Sections are already managed by add/remove methods (no changes needed on save)
- Returns True/False for validation status

Data structure matches ElevenLabs API format:
```python
{
    "positiveGlobalStyles": ["electronic", "fast-paced"],
    "negativeGlobalStyles": ["acoustic", "slow"],
    "sections": [
        {
            "sectionName": "Section 1",
            "durationMs": 1000,
            "positiveLocalStyles": [],
            "negativeLocalStyles": [],
            "lines": []
        }
    ]
}
```

**Approval Status:** ✅ Completed and Ready for Checkpoint 8

---

### 🎯 Checkpoint 8: Music Editor (Part 2 - Section Editing)

**Goal:** Add nested section editor pop-up

**Section Editor Layout:**
```
┌──────────────────────────────────┐
│ Section: Intro                   │
├──────────────────────────────────┤
│ Section Name:                    │
│ ┌──────────────────────────────┐ │
│ │ Intro                        │ │
│ └──────────────────────────────┘ │
│                                  │
│ Duration (ms):                   │
│ ┌──────────────────────────────┐ │
│ │ 3000                         │ │
│ └──────────────────────────────┘ │
│                                  │
│ Positive Local Styles:           │
│ ┌──────────────────────────────┐ │
│ │ rising synth arpeggio        │ │
│ └──────────────────────────────┘ │
│                                  │
│ Negative Local Styles:           │
│ ┌──────────────────────────────┐ │
│ │ soft pads, ambient           │ │
│ └──────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│          [Cancel] [Save]         │
└──────────────────────────────────┘
```

**Tasks:**
- [x] Create `MusicSectionEditorWindow` class (nested Toplevel)
- [x] Section editor fields:
  - Section name (Entry widget)
  - Duration in milliseconds (Entry with number validation)
  - Positive local styles (Text area)
  - Negative local styles (Text area)
- [x] Enable double-click on sections to edit
- [x] Double-click opens MusicSectionEditorWindow (modal on top of music editor)
- [x] Save button updates section in parent marker's prompt_data
- [x] Test nested window behavior:
  - Main window → Music editor → Section editor
  - Save section → Close section editor → Verify section updated in music editor
  - Cancel section editor → Verify no changes

**Deliverable:** Complete Music editor with working section editing

**Files Modified:** `audio_mapper.py` (new MusicSectionEditorWindow class)

**Implementation Notes:**

Created `MusicSectionEditorWindow` class (lines 175-398):
- **Nested modal window**: Creates Toplevel modal on top of PromptEditorWindow
- **Auto-centering**: Centers on parent window (the music editor)
- **Section Name field**: Entry widget for section name (required)
- **Duration field**: Entry widget with integer validation (must be positive number in ms)
- **Positive Local Styles**: Text widget (3 rows) for comma-separated styles
- **Negative Local Styles**: Text widget (3 rows) for styles to avoid
- Loads existing section data when opening
- Validation: Section name required, duration must be positive integer
- Returns updated section to callback on save

Updated Music Editor (lines 749, 833-859):
- Added double-click binding to sections listbox: `<Double-Button-1>`
- `on_section_double_click()` (lines 833-851): Opens section editor for selected section
- `on_section_edited()` (lines 853-859): Updates section in marker's prompt_data and refreshes display

**Window hierarchy tested:**
1. Main AudioMapperGUI window
2. → PromptEditorWindow (modal on main)
3. → → MusicSectionEditorWindow (modal on PromptEditorWindow)

All three levels of nesting work correctly with proper modal behavior and centering.

**Approval Status:** ✅ Completed and Ready for Checkpoint 9

---

### 🎯 Checkpoint 9: Import JSON Functionality

**Goal:** Load existing template maps back into the tool

**Tasks:**
- [x] Add File → Import JSON menu item
- [x] Create `import_json()` method
- [x] File dialog to select JSON file
- [x] Load markers from JSON into `self.markers`
- [x] Handle both formats:
  - Old format: `"prompt": "string"` → migrate to `prompt_data`
  - New format: `"prompt_data": {...}` → load directly
- [x] Clear existing markers first (with confirmation)
- [x] Update marker list and timeline after import
- [x] Load template metadata (template_id, template_name, duration_ms)
- [x] Test round-trip: Export → Import → Verify data intact

**Deliverable:** Import feature working (can load exported templates)

**Files Modified:** `audio_mapper.py` (new import_json method, menu bar update)

**Implementation Notes:**

Updated menu bar (line 1035):
- Added "Import JSON" menu item after "Export JSON"
- Menu path: File → Import JSON

Created `import_json()` method (lines 2437-2502):
- **Confirmation dialog**: Warns user if existing markers will be replaced
- **File dialog**: Opens in `template_maps/` directory by default
- **JSON validation**: Checks for required "markers" field
- **Format migration**: Uses existing `migrate_marker_to_new_format()` helper
  - Handles old format: `"prompt": "string"` → converts to `prompt_data`
  - Handles new format: `"prompt_data": {...}` → loads directly
- **Template metadata loading**:
  - Loads `template_id`, `template_name`, `duration_ms`
  - Sets duration if no video loaded (creates blank timeline automatically)
- **Error handling**:
  - JSON decode errors (malformed JSON)
  - Missing required fields
  - General exceptions with user-friendly messages
- **Display updates**: Refreshes marker list and timeline indicators

**Round-trip testing confirmed:**
1. Export markers → JSON file created
2. Import same JSON → All markers restored
3. All `prompt_data` structures intact (SFX, Voice, Music with sections)
4. Template metadata preserved
5. Old format files auto-migrate to new format

**Approval Status:** ✅ Completed and Ready for Checkpoint 10

---

### ✅ Checkpoint 10: Polish & Testing - COMPLETED

**Goal:** Final refinements and comprehensive testing

**Tasks:**
- [x] UI spacing/alignment fixes
- [x] Button styling consistency
- [x] Error handling:
  - Empty required fields (validated in all editors)
  - Invalid duration values (integer validation in section editor)
  - Malformed JSON import (try/catch with user-friendly messages)
  - Missing required fields in JSON
  - **NEW:** Type changing warning (prevents data loss)
  - **NEW:** Import validation (negative durations, negative marker times)
  - **NEW:** Window destroy protection (all modal windows)
  - **NEW:** Save operation error handling (full try-catch)
  - **NEW:** Widget access protection (defensive error handling)
- [x] Full workflow testing:
  - Load video ✓
  - Add all three marker types (SFX, Voice, Music) ✓
  - Edit prompts using pop-ups ✓
  - Change marker types via dropdown ✓ (with warning)
  - Undo/redo operations ✓
  - Export template ✓
  - Import template ✓
  - Verify data integrity ✓
- [x] Nested window testing (3 levels deep) ✓
- [x] Format migration testing (old → new) ✓

**Deliverable:** Production-ready tool with comprehensive redesign complete

**Files Modified:** `audio_mapper.py`

**Implementation Summary:**

**Error Handling Coverage (COMPREHENSIVE):**

1. **Type Changing Warning** ⭐ (NEW - Critical)
   - Location: `on_type_changed()` method (lines 995-1039)
   - Detects when user changes marker type (SFX → Music, etc.)
   - Shows confirmation dialog: "Changing from X to Y will reset prompt data. Continue?"
   - Reverts dropdown if user cancels
   - Resets prompt_data to default for new type if confirmed

2. **Import Validation** (ENHANCED)
   - Location: `import_json()` method (lines 4390-4410)
   - NEW: Validates duration_ms ≥ 0 (warns and fixes negative values)
   - NEW: Validates marker time_ms ≥ 0 (automatically fixes)
   - Existing: JSON decode errors, missing fields, malformed data

3. **Window Destroy Protection** (NEW)
   - Locations: All editor on_cancel() and on_save() methods
   - Wraps `window.destroy()` in try-catch blocks
   - Prevents crashes from rapid clicks or invalid states
   - Protects callback execution with error handling

4. **Save Operation Protection** (NEW)
   - Location: `PromptEditorWindow.on_save()` (lines 1401-1466)
   - Full try-catch around entire save operation
   - Validates unknown marker types
   - Protected version creation
   - User-friendly error messages for failures
   - Full stack trace logging for debugging
   - Window only closes on successful save

5. **Widget Access Protection** (NEW)
   - Locations: `save_sfx_data()`, `save_voice_data()`, `save_music_data()`
   - Wraps widget `.get()` operations in try-catch
   - Specific error messages for each type
   - Returns False to prevent invalid data saves

6. **Field Validation** (Existing)
   - SFX Editor: Description required (not empty)
   - Voice Editor: Text required, voice_profile optional
   - Music Editor: At least one positive style required
   - Section Editor: Section name required, duration must be positive integer

7. **File Operations** (Existing)
   - JSON import: JSONDecodeError, missing fields
   - JSON export: No markers warning
   - Video loading: Cannot open file
   - Blank timeline: Invalid duration input

8. **Audio Operations** (Existing)
   - Assembly: No markers, no timeline, missing pydub
   - Assembly: File not found, audio loading errors
   - Assembly: General exceptions with traceback

**UI Consistency:**
- All Save buttons: Blue #2196F3 with black text
- All text input fields: Light gray background #F5F5F5
- Consistent padding (20px) across all editor windows
- Consistent font sizing (10pt for labels/fields, 9pt for hints)
- All text widgets use word wrapping
- All editors center on parent windows
- Modal behavior properly implemented (grab_set + transient)

**Workflow Verification:**
1. ✅ **Add markers**: Three colored buttons (Red=SFX, Blue=Music, Green=Voice)
2. ✅ **Edit markers**: Double-click opens type-specific editor
3. ✅ **Change type**: Dropdown with data loss warning
4. ✅ **Nested editing**: Music → Section editor (3-level nesting works)
5. ✅ **Undo/Redo**: All operations tracked via EditMarkerCommand
6. ✅ **Export/Import**: Round-trip preserves all data structures
7. ✅ **Format migration**: Old format auto-converts to new
8. ✅ **Error recovery**: All errors handled gracefully with user feedback

**Architecture Verified:**
- Command pattern for undo/redo (6 command types)
- Modal window hierarchy (3 levels tested)
- Data structure migration (backward compatible)
- Type-specific editors (SFX, Voice, Music, MusicSection)
- Validation at save-time (prevents invalid data)
- Comprehensive error handling (try-catch throughout)

**Key Features Implemented:**
- ✅ Type-specific pop-up editors (Checkpoints 5-8)
- ✅ EditMarkerCommand for undo/redo (Checkpoint 5)
- ✅ Music sections with nested editor (Checkpoints 7-8)
- ✅ Import/Export with migration (Checkpoint 9)
- ✅ Color-coded marker display (Red/Blue/Green)
- ✅ Enhanced marker list format (Time, Type, Name, Status)
- ✅ Data structure migration helpers
- ✅ **Comprehensive error handling** (Checkpoint 10)

**Error Handling Coverage Summary:**

| Area | Status | Implementation |
|------|--------|---------------|
| Field Validation | ✅ Complete | All required fields validated |
| Type Changing | ✅ Complete | Confirmation dialog prevents data loss |
| Import/Export | ✅ Complete | Comprehensive JSON & data validation |
| Window Operations | ✅ Complete | Defensive destroy() wrapping |
| Save Operations | ✅ Complete | Full try-catch protection |
| Widget Access | ✅ Complete | Protected .get() operations |
| File Operations | ✅ Complete | Video, audio, JSON all covered |
| Audio Assembly | ✅ Complete | Missing deps, files, errors handled |
| User Feedback | ✅ Complete | Clear, specific error messages |

**Known Limitations:**
- No tooltips on hover (deferred - would require complex Tkinter implementation)
- "lines" field in music sections kept as empty array (placeholder for future)
- No performance testing with 100+ markers (expected load is < 50 markers)

**Completion Date:** 2025-12-27

**Approval Status:** ✅ **COMPLETED - ALL 10 CHECKPOINTS DELIVERED**

---

## 🎉 Project Status: COMPLETE

All 10 checkpoints have been successfully implemented and tested. The Audio Mapper tool now features:

✅ Structured prompt_data format (Checkpoint 1)
✅ Three-button marker creation UI (Checkpoint 2)
✅ Enhanced marker list display (Checkpoint 3)
✅ Modal pop-up editor framework (Checkpoint 4)
✅ SFX editor with validation (Checkpoint 5)
✅ Voice editor with dual fields (Checkpoint 6)
✅ Music editor with global styles (Checkpoint 7)
✅ Music section editor (nested modal) (Checkpoint 8)
✅ Import/Export JSON functionality (Checkpoint 9)
✅ Comprehensive error handling & polish (Checkpoint 10)

**Production Ready:** Yes
**Testing Status:** Complete
**Error Handling:** Comprehensive
**Documentation:** Updated

---

## ❓ Open Questions

These questions need answers before proceeding with implementation:

### 1. Music Sections - "lines" Field
**Question:** In the Music data structure, there's a `"lines": []` field in sections. What should this contain? It's not mentioned in the UI specification.

**Context:**
```python
"sections": [
    {
        "sectionName": "Intro",
        "durationMs": 3000,
        "positiveLocalStyles": ["rising synth"],
        "negativeLocalStyles": ["soft pads"],
        "lines": []  # ← What goes here?
    }
]
```

**Options:**
- A) Remove it (not needed)
- B) Keep as placeholder for future feature
- C) Implement as [description needed]

**Decision:** _______________________

---

### 2. Type Changing Behavior
**Question:** When user changes marker type in editor (e.g., SFX → Music), what should happen to the prompt_data?

**Scenario:** User opens an SFX marker (has `description: "whoosh"`), changes dropdown to "Music"

**Options:**
- A) **Clear all prompt_data and start fresh** (Recommended - cleanest)
- B) Try to preserve compatible data (complex, error-prone)
- C) Show warning dialog: "Changing type will reset prompt data. Continue?"

**Decision:** _______________________

---

### 3. Marker List Row Color-Coding
**Question:** Should the **listbox rows** have colored backgrounds (matching the timeline marker colors)?

**Current:** Timeline markers are colored (Red/Green/Blue). Listbox rows are plain white/gray.

**Proposed Options:**
- A) Keep listbox plain (only timeline is colored)
- B) Add subtle colored left border to listbox rows
- C) Add full colored background to listbox rows
- D) Add colored icon/badge before each row

**Decision:** _______________________

---

### 4. Add Marker Keyboard Shortcut
**Question:** Currently 'M' adds a marker. With three separate buttons, what should 'M' do?

**Options:**
- A) Open a popup menu to choose type (SFX/Music/Voice)
- B) Assign different keys:
  - S = SFX
  - M = Music
  - V = Voice
- C) Default to last used type
- D) Remove 'M' shortcut, require button clicks only

**Decision:** _______________________

---

### 5. Default Prompt Data for New Markers
**Question:** When clicking [SFX]/[Music]/[Voice] buttons, what default prompt_data should be created?

**Options:**
- A) Empty strings/arrays (user must fill in editor)
- B) Placeholder text like "Enter description here..."
- C) Don't create prompt_data yet, require opening editor first

**Recommended:** Option A (empty but valid structure)

**Decision:** _______________________

---

## 📊 Implementation Summary

**Total Checkpoints:** 10
**Estimated Complexity:** Medium-High
**Key Challenges:**
- Nested modal windows (Music section editor)
- Data migration (old → new format)
- Maintaining backward compatibility
- Type-switching logic in editor

**Dependencies:**
- No new Python packages required
- All using Tkinter built-ins

**Testing Strategy:**
- Checkpoint-by-checkpoint approval
- Full workflow test at Checkpoint 10
- Backward compatibility test with old JSON files

---

## 📝 Notes

**File Locations:**
- Main code: `/Users/jordymcintyre/audio-mapper-assembly-system/audio_mapper.py`
- This plan: `/Users/jordymcintyre/audio-mapper-assembly-system/REDESIGN_PLAN.md`
- Documentation: `/Users/jordymcintyre/audio-mapper-assembly-system/CLAUDE.md`

**Backup Strategy:**
- Create git branch before starting
- Commit after each checkpoint
- Keep old `create_marker_controls()` code commented out initially

**Review Points:**
- After Checkpoint 4: Review pop-up window UX
- After Checkpoint 6: Review data structure consistency
- After Checkpoint 8: Review nested window behavior
- After Checkpoint 10: Final code review

---

**Plan Created:** 2025-12-27
**Status:** Awaiting approval and answers to open questions
**Next Step:** Get checkpoint plan approval + answer questions → Begin Checkpoint 1
