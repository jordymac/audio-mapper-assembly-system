# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Audio Mapper & Assembly System is a Python desktop application for creating timecode-locked audio variations for video templates. The system enables precision timecode mapping through visual video scrubbing, then programmatic assembly of AI-generated audio elements.

**Core Concept:** Map timecodes once → generate multiple audio variations → assemble programmatically → output multiple final tracks with identical timing but different sonic palettes.

## Development Environment

### Local Python Desktop Application

This is a **native desktop GUI application** built with Python's Tkinter framework. It runs on the user's local machine (macOS primary development target).

**Tech Stack:**
- **GUI Framework:** Tkinter (built into Python 3.x, no installation required)
- **Video Playback:** python-vlc (VLC integration for frame-accurate scrubbing)
- **Image Handling:** Pillow (for video frame display)
- **Audio Assembly:** Pydub + FFmpeg (for combining audio files)

**Why Tkinter?**
- Native to Python (zero-dependency GUI)
- Full control over UI elements and keyboard bindings
- Lightweight and responsive
- Cross-platform compatible
- Perfect for internal production tools

**NOT using:**
- Web frameworks (Gradio, Streamlit, Flask)
- MCP tools or skills (those are for document creation, not GUI apps)
- Claude's computer environment (this runs on local machine)
- Browser-based interfaces

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install python-vlc pillow pydub

# Install FFmpeg (required for audio assembly)
brew install ffmpeg  # macOS
# or for Linux: sudo apt-get install ffmpeg
# or for Windows: download from https://ffmpeg.org/download.html

# Verify Tkinter availability (should already be installed with Python)
python3 -c "import tkinter; print('✓ Tkinter ready')"
```

### Running the Tools

**Audio Mapper (GUI)** - Visual timecode mapping with video playback:
```bash
python3 audio_mapper.py
```

**Workflow:**
1. Load video file (or create blank timeline with duration)
2. Scrub timeline to exact moments using video playback
3. Click [SFX], [Music], or [Voice] button to add marker at current position
4. Popup editor opens immediately - enter custom name and prompt details
5. Save marker with structured prompt data
6. Repeat for all audio moments
7. File → Export JSON

**Keyboard Shortcuts:**
- `Space` - Play/Pause video
- `M` - Add SFX marker at current position (opens editor popup)
- `←/→` - Step backward/forward (50ms increments)
- `Delete` - Remove selected marker
- `Cmd+Z` / `Ctrl+Z` - Undo last marker operation
- `Cmd+Shift+Z` / `Ctrl+Shift+Z` - Redo marker operation

**Audio Assembler** - Programmatic assembly from timecode maps:
```bash
python3 assemble_audio.py template_maps/DM01_map.json
```

**What it does:**
1. Reads JSON timecode map
2. Loads generated audio files (from ElevenLabs or other sources)
3. Places audio at precise millisecond positions
4. Outputs multi-channel WAV (Ch1: Music, Ch2: SFX, Ch3: Voice)

## Architecture

### Core Components

**audio_mapper.py** - Tkinter GUI application
- VLC-based video player embedded in Tkinter window
- Timeline scrubber with millisecond-precise position tracking
- Waveform visualization overlay on timeline
- Marker management (add, edit, delete, drag-to-reposition)
- **Type-specific pop-up editors** - SFX, Voice, and Music with structured prompts
- Undo/redo system for marker operations (Command pattern)
- JSON export/import of timecode maps
- Keyboard shortcut handling

**assemble_audio.py** - Command-line assembly tool
- Reads JSON timecode maps
- Loads audio files via Pydub
- Creates silent base track
- Overlays audio at specified timecodes
- Exports multi-channel WAV

### GUI Component Hierarchy
```
Root Window (tk.Tk)
├── Video Frame
│   └── VLC Player (embedded)
├── Timeline Control
│   ├── Waveform Canvas (tk.Canvas) - visual audio representation
│   ├── Slider (ttk.Scale) - scrub through video
│   ├── Marker Indicators (draggable) - visual marker positions
│   └── Timestamp Display (tk.Label) - shows current position in ms
├── Marker Controls
│   ├── Add Marker Buttons:
│   │   ├── [SFX] - Red button, black text
│   │   ├── [Music] - Blue button, black text
│   │   └── [Voice] - Green button, black text
│   └── (Opens type-specific editor popup on click)
├── Marker List (tk.Listbox) - shows all markers with edit icons
│   └── Format: ✏️ TIME  TYPE  NAME  (status)
└── Edit Controls
    ├── Undo (Cmd+Z / Ctrl+Z)
    └── Redo (Cmd+Shift+Z / Ctrl+Shift+Z)
```

### Pop-up Editor Windows

**PromptEditorWindow** - Main editor (opens when adding/editing markers)
- Modal window centered on parent
- Type dropdown (can change marker type: SFX/Music/Voice)
- **Name field** - Custom marker name (e.g., "VOX_00001_Female-30s-Australian")
- Dynamic content area (changes based on selected type)
- Blue Save button with black text
- Auto-focuses appropriate input field

**Type-Specific Content Areas:**

1. **SFX Editor** - Single description field
   - Multi-line text area (light gray background #F5F5F5)
   - Required: Description of sound effect
   - Cursor auto-focuses on description field

2. **Voice Editor** - Two fields
   - Voice Profile (single-line, optional): e.g., "Warm female, mid-30s, Australian"
   - Text to Speak (multi-line, required): The exact words to be spoken
   - Cursor auto-focuses on text field

3. **Music Editor** - Global styles + sections
   - Positive Global Styles (multi-line): Comma-separated (e.g., "electronic, fast-paced")
   - Negative Global Styles (multi-line): Styles to avoid
   - Sections listbox with add/remove/edit functionality
   - Double-click section to open nested editor
   - Cursor auto-focuses on positive styles field

**MusicSectionEditorWindow** - Nested editor for music sections
- Modal window on top of Music Editor (550x600px)
- Section Name (required)
- Duration in milliseconds (required, integer validation)
- Positive Local Styles (comma-separated)
- Negative Local Styles (comma-separated)
- All text fields have light gray background (#F5F5F5)
- Blue Save button with black text

### Data Flow

1. **Mapping Phase**: `audio_mapper.py` → JSON template
   - Input: Video file (or duration value)
   - User scrubs to exact moments
   - User clicks type button → popup opens immediately
   - User enters custom name and structured prompt
   - Output: JSON file with timecode markers

2. **Generation Phase**: External (ElevenLabs API)
   - Input: Structured prompts from JSON template
   - Output: Individual audio files (music, SFX, voice)

3. **Assembly Phase**: JSON template + audio files → `assemble_audio.py` → Final audio
   - Input: JSON template + generated audio directory
   - Output: Multi-channel WAV file

### JSON Template Schema

Templates now use structured `prompt_data` format (backward compatible with old format):

```json
{
  "template_id": "DM01",
  "template_name": "Indoor Routine",
  "duration_ms": 12000,
  "markers": [
    {
      "time_ms": 0,
      "type": "music",
      "name": "MUS_00001_Electronic_Upbeat",
      "prompt_data": {
        "positiveGlobalStyles": ["electronic", "fast-paced", "energetic"],
        "negativeGlobalStyles": ["acoustic", "slow", "ambient"],
        "sections": [
          {
            "sectionName": "Intro",
            "durationMs": 3000,
            "positiveLocalStyles": ["rising synth arpeggio"],
            "negativeLocalStyles": ["soft pads"],
            "lines": []
          }
        ]
      },
      "asset_slot": "music_0",
      "asset_file": "MUS_00000.mp3",
      "asset_id": null,
      "status": "not yet generated"
    },
    {
      "time_ms": 150,
      "type": "sfx",
      "name": "SFX_00001_UI_Click",
      "prompt_data": {
        "description": "UI click, subtle, clean"
      },
      "asset_slot": "sfx_0",
      "asset_file": "SFX_00000.mp3",
      "asset_id": null,
      "status": "not yet generated"
    },
    {
      "time_ms": 2000,
      "type": "voice",
      "name": "VOX_00001_Female_30s_Australian",
      "prompt_data": {
        "voice_profile": "Warm female narrator, mid-30s, Australian accent",
        "text": "Camera roll lately..."
      },
      "asset_slot": "voice_0",
      "asset_file": "VOX_00000.mp3",
      "asset_id": null,
      "status": "not yet generated"
    }
  ]
}
```

### Marker Types & Data Structures

| Type | Purpose | prompt_data Structure |
|------|---------|----------------------|
| `sfx` | Sound effect hit point | `{"description": "string"}` |
| `voice` | Voice quote/narration | `{"voice_profile": "string", "text": "string"}` |
| `music` | Music bed placement | `{"positiveGlobalStyles": [], "negativeGlobalStyles": [], "sections": []}` |

**Music Section Structure:**
```json
{
  "sectionName": "Intro",
  "durationMs": 3000,
  "positiveLocalStyles": ["rising synth"],
  "negativeLocalStyles": ["soft pads"],
  "lines": []
}
```

## Key Implementation Details

### Command Pattern for Undo/Redo

The application uses the Command pattern for all marker operations:

```python
# Command classes
class AddMarkerCommand(Command):
    """Add a marker to the timeline"""

class EditMarkerCommand(Command):
    """Edit an existing marker"""

class DeleteMarkerCommand(Command):
    """Delete a marker"""

# History manager
class HistoryManager:
    def execute_command(self, command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self):
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
```

All marker operations (add, edit, delete, drag) support full undo/redo.

### Video Player Integration (python-vlc)
```python
import vlc

class VideoMapper:
    def __init__(self):
        # Create VLC instance and player
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Embed in Tkinter frame
        self.player.set_hwnd(self.video_frame.winfo_id())
```

### Timecode Management
- All timecodes stored as **integers in milliseconds**
- Avoids floating-point precision errors
- Matches ElevenLabs API output format
- Example: `150` = 0.150 seconds, `2000` = 2.000 seconds

### Pop-up Editor Workflow

**Add New Marker:**
```python
def add_marker_by_type(self, marker_type):
    """Add marker and immediately open editor"""
    # 1. Create marker with empty prompt_data
    marker = {
        "time_ms": self.current_time_ms,
        "type": marker_type,
        "name": "",  # User fills in editor
        "prompt_data": self.create_default_prompt_data(marker_type),
        "asset_slot": f"{marker_type}_{count}",
        "asset_file": f"{prefix}_{count:05d}.mp3",
        "asset_id": None,
        "status": "not yet generated"
    }

    # 2. Add via command pattern (for undo support)
    command = AddMarkerCommand(self, marker)
    self.history.execute_command(command)

    # 3. Immediately open editor popup
    marker_index = len(self.markers) - 1
    self.open_marker_editor(self.markers[marker_index], marker_index,
                           on_cancel_callback=lambda: self.history.undo())
```

**Edit Existing Marker:**
```python
def on_marker_double_click(self, event):
    """Handle double-click on marker in list"""
    selection = self.marker_listbox.curselection()
    if not selection:
        return

    index = selection[0]
    marker = self.markers[index]
    self.open_marker_editor(marker, index)

def on_marker_edited(self, updated_marker, index):
    """Callback when marker is saved"""
    old_marker = self.markers[index].copy()
    command = EditMarkerCommand(self, index, old_marker, updated_marker)
    self.history.execute_command(command)
```

### Data Migration (Backward Compatibility)

The application supports both old and new marker formats:

```python
def migrate_marker_to_new_format(self, marker):
    """Convert old 'prompt' string to new 'prompt_data' structure"""
    if "prompt_data" in marker:
        return marker  # Already new format

    marker_type = marker.get("type", "sfx")
    old_prompt = marker.get("prompt", "")

    # Convert based on type
    if marker_type == "sfx":
        prompt_data = {"description": old_prompt}
    elif marker_type == "voice":
        prompt_data = {"voice_profile": "", "text": old_prompt}
    elif marker_type == "music":
        prompt_data = {
            "positiveGlobalStyles": [old_prompt] if old_prompt else [],
            "negativeGlobalStyles": [],
            "sections": []
        }

    new_marker = marker.copy()
    del new_marker["prompt"]
    new_marker["prompt_data"] = prompt_data
    return new_marker
```

### Audio Assembly
```python
from pydub import AudioSegment

def assemble_audio(template_path, audio_dir):
    # Load template
    with open(template_path) as f:
        data = json.load(f)

    # Create silent base track
    duration_ms = data['duration_ms']
    base = AudioSegment.silent(duration=duration_ms)

    # Overlay each marker's audio at specified time
    for marker in data['markers']:
        if marker['type'] in ['music', 'sfx', 'voice']:
            audio = AudioSegment.from_file(
                os.path.join(audio_dir, marker['asset_file'])
            )
            base = base.overlay(audio, position=marker['time_ms'])

    return base
```

## Common Workflows

### Creating a New Template Map
1. Run `python3 audio_mapper.py`
2. Load video file (File → Open Video) or create blank timeline
3. Scrub timeline to first audio moment
4. Click [SFX], [Music], or [Voice] button
5. **Popup editor opens immediately**:
   - Enter custom name (e.g., "VOX_00001_Female_30s")
   - Fill in type-specific prompt fields
   - Click blue Save button
6. Repeat for all audio moments
7. File → Export JSON
8. Save to `template_maps/` directory

### Editing Existing Markers
1. **Double-click** any marker in the list
2. Popup editor opens with existing data
3. Modify name, prompt data, or even change type
4. Save changes
5. Use Cmd+Z to undo if needed

### Importing Existing Templates
1. File → Import JSON
2. Select JSON file (supports both old and new formats)
3. Template automatically migrates to new format if needed
4. All markers appear in list
5. Double-click any marker to edit

### Generating Audio from Template
1. Open exported JSON file
2. Extract structured prompts from each marker's `prompt_data`
3. Use ElevenLabs API to generate audio:
   - **SFX**: Use `description` field
   - **Voice**: Use `voice_profile` + `text` fields
   - **Music**: Use `positiveGlobalStyles`, `negativeGlobalStyles`, and `sections`
4. Save generated files with names matching `asset_file` field
5. Store in `generated_audio/` directory

### Assembling Final Audio
1. Ensure generated audio files exist
2. Run `python3 assemble_audio.py template_maps/DM01_map.json`
3. Script reads JSON, loads audio files, combines at timecodes
4. Output: `output/DM01_final.wav` (multi-channel)

### Creating Variations
1. Use same JSON timecode map (markers stay in same positions)
2. Generate different audio with same prompts (e.g., different voice actors)
3. Update `asset_file` fields to point to new audio
4. Run assembly script again
5. Output: New variation with identical timing

## UI Design Details

### Color Scheme

**Marker Type Buttons:**
- SFX: Red background (#F44336) with black text
- Music: Blue background (#2196F3) with black text
- Voice: Green background (#4CAF50) with black text

**Timeline Markers:**
- SFX: Red indicators
- Music: Blue indicators
- Voice: Green indicators

**Pop-up Editors:**
- Save button: Blue background (#2196F3) with black text
- Cancel button: Default gray
- Text input fields: Light gray background (#F5F5F5)
- All fields auto-focus cursor on open

**Marker List Display:**
```
✏️ 0:00.150  SFX      SFX_00001_UI_Click              (not yet generated)
✏️ 0:02.000  VOICE    VOX_00001_Female_30s            (not yet generated)
✏️ 3:20.000  MUSIC    MUS_00001_Electronic_Upbeat     (not yet generated)
```
- Format: Edit icon, Time (M:SS.mmm), Type, Name (30 chars), Status
- Shows "(unnamed)" if no custom name provided
- Shows asset_id once generated, or "not yet generated"

### Window Sizes

- **PromptEditorWindow**: 500x600px
- **MusicSectionEditorWindow**: 550x600px (slightly wider for better field visibility)
- Both windows center on parent automatically

## Dependencies Notes

**Required**:
- Python 3.8+
- python-vlc: Requires VLC media player installed on system
- Pillow: Image handling for video frames
- Pydub: Requires FFmpeg for audio processing

**Installing VLC** (if not already installed):
```bash
# macOS
brew install --cask vlc

# Ubuntu/Debian
sudo apt-get install vlc

# Windows
# Download from https://www.videolan.org/vlc/
```

**Installing FFmpeg** (required for Pydub):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Project Structure

```
/audio-mapper-assembly-system/
  audio_mapper.py          # Tkinter GUI application (main tool)
  assemble_audio.py        # CLI assembly script
  requirements.txt         # Python dependencies
  README.md               # User-facing documentation
  CLAUDE.md               # This file (for Claude Code)
  redesign_plan.md        # Implementation checkpoints (all completed)

  /template_maps/         # JSON timecode maps (output from mapper)
    DM01_indoor_routine.json
    DM03_hybrid_recap.json
    MTG01_month_recap.json

  /generated_audio/       # AI-generated audio files
    /music/
      MUS_00001_DM01_Lofi_Warm.mp3
      MUS_00002_DM01_Acoustic_Indie.mp3
    /sfx/
      SFX_00012_UI_Click.mp3
      SFX_00013_Whoosh.mp3
    /voice/
      VOX_00001_Camera_Roll.mp3

  /output/                # Assembled final audio (multi-channel WAV)
    DM01_final_v1.wav
    DM01_final_v2.wav
```

## Troubleshooting

### "VLC player not found"
- Ensure VLC is installed: `brew install --cask vlc`
- Check VLC is in Applications folder (macOS)

### "No module named 'vlc'"
- Install python-vlc: `pip install python-vlc`

### "FFmpeg not found" (during audio assembly)
- Install FFmpeg: `brew install ffmpeg`
- Verify: `ffmpeg -version`

### Video won't play in mapper
- Check video codec compatibility with VLC
- Try converting video to MP4 (H.264) format
- Ensure video file path has no special characters

### Timeline scrubbing is laggy
- Use lower resolution video for mapping
- Close other applications
- Try different video format

### Popup editor buttons cut off
- MusicSectionEditorWindow should be 550x600px
- If still cut off, increase window height in code

### Markers show "(unnamed)"
- Double-click marker to edit
- Enter custom name in Name field
- Name appears in marker list after saving

## Project Context

This toolchain was built as part of the Canva AI Audio Designer challenge to demonstrate:

1. **Systems thinking** - Not just audio creation, but a reusable production pipeline
2. **Workflow innovation** - The "timecode-locked variation" concept enables multiple audio palettes with identical timing
3. **Technical capability** - Building functional production tools, not just concepts
4. **Scalability mindset** - Tools designed for repeatable, maintainable workflows

### The "Third Editorial Workflow"

Traditional approaches:
- **Audio-to-picture:** Edit video first, then choose music to fit
- **Picture-to-audio:** Start with audio, cut video to match beats

This system enables:
- **Template-driven variation:** One video edit → multiple audio variations with identical timing
- User can swap between lo-fi, acoustic, electronic versions without re-editing
- SFX palettes (organic, digital, retro) all sync to same video
- Enables rapid A/B testing and content variation for social media

## Development Philosophy

### Why Build Custom Tools?

**Instead of:** Using DAW for every template manually
**We built:** Visual mapper + programmatic assembly

**Benefits:**
- Separation of creative decisions (when/what) from mechanical execution (placement)
- Reproducible results (JSON is single source of truth)
- Variation-friendly (same map, different audio, instant recombination)
- Scalable (works for 6 templates or 600 templates)

### Design Decisions

**Tkinter over web frameworks:**
- No server overhead
- Native keyboard shortcuts
- Better video performance
- Simpler deployment (just Python)

**Pop-up editors over inline forms:**
- Cleaner main UI
- Focus user attention on one marker at a time
- Type-specific interfaces (SFX vs Voice vs Music)
- Modal workflow prevents accidental edits

**Structured prompts over simple text:**
- Better for AI generation (ElevenLabs API format)
- Separates voice profile from text
- Music sections enable precise timing control
- Positive/negative styles give better generation results

**Command pattern for undo/redo:**
- Full edit history
- Consistent behavior across all operations
- Easy to extend with new command types

**JSON over database:**
- Human-readable and editable
- Version control friendly (git diff works)
- Easy to inspect and debug
- No setup required

**Multi-channel WAV output:**
- DAW compatibility (separate tracks maintain sync)
- Flexibility for post-processing
- Can export as separate MP3s later if needed

**Millisecond integers over float seconds:**
- No floating-point precision issues
- Matches ElevenLabs API format
- Unambiguous (no 0.1499999 vs 0.15 confusion)

## Development Status

### ✅ Completed Features (UI Redesign - All 10 Checkpoints)

**Checkpoint 1: Data Structure Migration**
- Migrated from simple `"prompt"` string to structured `"prompt_data"` objects
- Full backward compatibility with old format
- Auto-migration on import

**Checkpoint 2: Main Window UI Redesign**
- Replaced type dropdown + text area with three colored buttons
- [SFX] Red, [Music] Blue, [Voice] Green (all with black text)
- Immediate popup on button click

**Checkpoint 3: Enhanced Marker List Display**
- Edit icons (✏️) on each row
- MM:SS.mmm time format
- Custom name column (30 chars width)
- Status field (shows generation state or asset_id)

**Checkpoint 4: Pop-up Editor Framework**
- Modal window with type dropdown
- Dynamic content area (swaps based on type)
- Blue Save button with black text
- Cancel button
- Auto-focus cursor in main field

**Checkpoint 5: SFX Editor Implementation**
- Single description field
- Required field validation
- EditMarkerCommand for undo/redo support
- Light gray background (#F5F5F5)

**Checkpoint 6: Voice Editor Implementation**
- Voice profile field (optional)
- Text to speak field (required)
- Both fields with light gray backgrounds
- Auto-focus on text field

**Checkpoint 7: Music Editor (Part 1 - Global Styles)**
- Positive global styles (required, at least one)
- Negative global styles (optional)
- Sections listbox display
- Add/Remove section buttons

**Checkpoint 8: Music Editor (Part 2 - Section Editing)**
- Nested MusicSectionEditorWindow (550x600px)
- Section name, duration (ms), local styles
- Double-click to edit sections
- Modal on top of music editor

**Checkpoint 9: Import JSON Functionality**
- File → Import JSON menu item
- Loads both old and new format files
- Auto-migrates old format to new
- Preserves template metadata

**Checkpoint 10: Polish & Testing**
- All UI spacing/alignment finalized
- Comprehensive error handling
- Full workflow testing completed
- Nested window behavior verified

### Recent Enhancements (2025-12-27)

**Immediate Editor Popup:**
- Clicking [SFX], [Music], or [Voice] buttons now opens editor immediately
- No more empty markers in list
- If user cancels, marker is automatically removed (undo)

**Custom Marker Names:**
- Added "Name" field to all editors
- Appears as column in marker list between Type and Status
- Example: "VOX_00001_Female_30s_Australian"
- Shows "(unnamed)" if left blank

**UI Styling Improvements:**
- All Save buttons: Blue (#2196F3) with black text (was green with white text)
- All text input fields: Light gray background (#F5F5F5) for better visibility
- Auto-focus cursor in appropriate field when editor opens
- MusicSectionEditorWindow increased to 550x600px (was 500x500px)

**Marker Button Colors:**
- SFX button: Red (#F44336) with black text
- Music button: Blue (#2196F3) with black text
- Voice button: Green (#4CAF50) with black text
- All buttons have raised relief and 2px border

### Phase 3 Features - Future
- **Preset prompt templates** - Dropdown of common prompts for faster workflow
- **Batch export** - Export multiple templates in one operation
- **Direct ElevenLabs API integration** - Generate audio directly from tool
- **Auto-assembly after generation** - Automatic assembly when generation completes
- **Variation management UI** - Compare multiple audio versions side-by-side
- **Real-time preview** - Hear assembled audio before exporting

### Production Scale Features - Long Term
- **Web-based interface** - Team collaboration and remote access
- **Database-backed marker storage** - Centralized template management
- **Version control for timecode maps** - Track changes and rollback capability
- **Integration with Canva ingest pipeline** - Direct publishing workflow
- **Batch processing for template libraries** - Process hundreds of templates automatically

## Implementation Notes

### Command Pattern Classes

Six command types support full undo/redo:
1. `AddMarkerCommand` - Add new marker
2. `EditMarkerCommand` - Edit marker prompt_data
3. `DeleteMarkerCommand` - Delete marker
4. `DragMarkerCommand` - Drag marker to new time
5. `ClearAllMarkersCommand` - Clear all markers
6. `AddMultipleMarkersCommand` - Import markers from JSON

### Window Hierarchy

Three levels of modal windows work correctly:
1. **Main Window** - AudioMapperGUI (tk.Tk)
2. **→ PromptEditorWindow** - Modal on main (tk.Toplevel)
3. **→ → MusicSectionEditorWindow** - Modal on PromptEditorWindow (tk.Toplevel)

All levels properly center on parent and handle modal behavior.

### Data Validation

**SFX Editor:**
- Description: Required, cannot be empty

**Voice Editor:**
- Voice profile: Optional
- Text to speak: Required, cannot be empty

**Music Editor:**
- Positive styles: Required, at least one
- Negative styles: Optional
- Sections: Optional (can have zero sections)

**Music Section Editor:**
- Section name: Required, cannot be empty
- Duration: Required, must be positive integer
- Local styles: Optional

### File Format Support

**Export:**
- Always exports new format with `prompt_data`
- Includes `name`, `asset_id`, `status` fields
- Template metadata: `template_id`, `template_name`, `duration_ms`

**Import:**
- Supports both old format (`"prompt": "string"`)
- Supports new format (`"prompt_data": {...}`)
- Auto-migrates old → new on load
- Preserves all metadata

## Code Organization

### Main Classes

- `AudioMapperGUI` - Main application window
- `PromptEditorWindow` - Pop-up editor for markers
- `MusicSectionEditorWindow` - Nested editor for music sections
- `HistoryManager` - Undo/redo stack management
- `Command` - Base class for command pattern
- `AddMarkerCommand`, `EditMarkerCommand`, etc. - Specific commands

### Key Methods

- `add_marker_by_type(marker_type)` - Create and immediately edit marker
- `open_marker_editor(marker, index)` - Open editor popup
- `on_marker_edited(updated_marker, index)` - Save callback
- `migrate_marker_to_new_format(marker)` - Convert old → new format
- `create_default_prompt_data(marker_type)` - Generate empty prompt_data
- `export_json()` - Export template to JSON
- `import_json()` - Import template from JSON

### Data Helpers

- `get_prompt_preview(marker)` - Display string for marker list
- `create_sfx_content()` - Build SFX editor UI
- `create_voice_content()` - Build Voice editor UI
- `create_music_content()` - Build Music editor UI
- `save_sfx_data()` - Validate and save SFX data
- `save_voice_data()` - Validate and save Voice data
- `save_music_data()` - Validate and save Music data

## Testing Guidelines

### Full Workflow Test

1. **Video Loading**: Load video or create blank timeline
2. **Add Markers**: Click each type button (SFX, Music, Voice)
3. **Verify Popups**: Each opens immediately with correct fields
4. **Enter Data**: Fill in name and prompt fields
5. **Save**: Verify marker appears in list with correct info
6. **Edit**: Double-click marker, modify, save
7. **Type Change**: Change type in dropdown, verify content switches
8. **Music Sections**: Add sections, double-click to edit
9. **Undo/Redo**: Test Cmd+Z and Cmd+Shift+Z
10. **Export**: File → Export JSON
11. **Import**: File → Import JSON (same file)
12. **Verify**: All data intact after round-trip

### Edge Cases

- Cancel editor without saving (marker removed if new, unchanged if edit)
- Empty required fields (validation should prevent save)
- Invalid section duration (should show error)
- Import malformed JSON (should show user-friendly error)
- Import old format (should auto-migrate)
- Change marker type (content area should update)
- Edit marker while video playing (should work)

## Future Considerations

### Potential Enhancements

1. **Preset Templates**: Common prompts for each type
2. **Drag-and-drop reordering**: Drag markers in list to reorder
3. **Batch operations**: Select multiple markers, edit in bulk
4. **Search/filter**: Filter markers by type or name
5. **Hotkeys**: Keyboard shortcuts for each marker type (S/M/V)
6. **Copy/paste markers**: Duplicate markers quickly
7. **Marker colors**: Custom colors beyond red/green/blue
8. **Timeline zoom**: Zoom in/out on timeline
9. **Multi-track display**: Show all marker types on separate tracks

### Known Limitations

- No tooltips on UI elements (Tkinter limitation)
- "lines" field in music sections unused (placeholder for future)
- No performance testing with 100+ markers (expected load is < 50)
- Nested windows limited to 3 levels (sufficient for current needs)
