# Metadata & Export Plan

**Last Updated**: 2025-12-30

This document defines the metadata structures, category taxonomies, and export workflow for the Audio Mapper & Assembly System.

---

## Table of Contents
1. [Export Center Workflow](#export-center-workflow)
2. [Metadata Structures](#metadata-structures)
3. [Category Taxonomies](#category-taxonomies)
4. [Export File Structure](#export-file-structure)
5. [Implementation Plan](#implementation-plan)

---

## Export Center Workflow

### Main Window UI Changes

**Button Changes**:
- **Old**: "Export JSON" button in main window
- **New**: "Assemble" button in main window
  - Clicking "Assemble" → Generates assembled audio and plays in main window video player
  - Replaces original video audio with assembled audio (Music + SFX + Voice)
  - User can preview assembled result immediately in existing video player
- **New**: "Export" button in main window
  - Clicking "Export" → Opens Export Center for metadata editing and file export
  - Primary workflow: Generate → Assemble (preview in main window) → Export (metadata + files)

**File Menu Updates**:
- File → Export JSON (new menu item)
  - Exports template JSON without opening Export Center
  - Quick export for saving work-in-progress
- File → Export Center (Cmd+E)
  - Opens Export Center for metadata editing and final export

### UI Design: Export Center (Metadata & File Export)

**Access**:
- Click "Export" button in main window (after assembling) (primary)
- File → Export Center (Cmd+E) (alternative)

**Simplified - No Assembly Section** (assembly happens in main window)

```
┌────────────────────────────────────────────────────────────────────┐
│  Export Center - DM01_Indoor_Routine                     [X Close] │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────────────────────────────┐│
│  │ Generated Audio │  │ Metadata & Preview                      ││
│  │                 │  │                                         ││
│  │ 🎵 MUSIC        │  │ MUS_00001_Electronic_Upbeat.mp3        ││
│  │ ✓ MUS_00001     │  │ Duration: 12.5s  |  Position: 0:00.000 ││
│  │   MUS_00002     │  │                                         ││
│  │                 │  │ ┌───────────────────────────────────┐   ││
│  │ 🔊 SFX          │  │ │ Title: ____________________       │   ││
│  │ ✓ SFX_00001     │  │ │ Categories: [▼] [▼] [▼]           │   ││
│  │ ✓ SFX_00012     │  │ │ Notes: ____________________       │   ││
│  │   SFX_00013     │  │ │ Used in: DM01                     │   ││
│  │                 │  │ └───────────────────────────────────┘   ││
│  │ 🎤 VOICE        │  │                                         ││
│  │ ✓ VOX_00001     │  │ Waveform: [~~~~~~∿∿∿~~~~~~]            ││
│  │                 │  │ [▶ Play]  [Save Metadata]             ││
│  │                 │  │                                         ││
│  └─────────────────┘  └─────────────────────────────────────────┘│
│                                                                    │
│  [📦 Export All Files] ← Creates folder with audio + metadata     │
└────────────────────────────────────────────────────────────────────┘
```

### User Workflow (Simplified)

**In Main Window**:
1. **Create & Generate**: Create markers, generate audio for each
2. **Assemble**: Click **"Assemble"** button
   - Generates assembled audio (Music + SFX + Voice combined)
   - Replaces video audio with assembled result
   - Play video in main window to preview assembled audio with video
   - Verify sync and timing in existing video player
3. **Export**: Click **"Export"** button when satisfied
   - Opens Export Center window

**In Export Center**:
4. **Left Panel**: Shows all generated markers
   - ✓ = Audio generated and ready
   - Empty = Not yet generated (grayed out)
   - Grouped by type: Music, SFX, Voice
5. **Select Marker**: Click any marker in left panel
6. **Edit Metadata**: Right panel shows editable fields
   - Title (required)
   - Categories (type-specific fields)
   - Notes (optional, freeform text)
   - Used In Templates (auto-populated, shows current + any other templates using this asset)
   - Waveform visualization
   - Play button for individual preview
7. **Save Metadata**: Click "Save Metadata" button
8. **Repeat**: Navigate through markers non-linearly (fill in all metadata)
9. **Export All**: Click "Export All Files"
   - Creates organized folder structure
   - Exports individual audio files to MUSIC/, SFX/, VOICE/ folders
   - Generates metadata JSON files
   - Exports assembled audio
   - Exports template JSON

### Why This Approach?

✅ **No duplication** - Reuses existing main window video player for assembly preview
✅ **Simpler workflow** - Assemble in place, export when ready
✅ **Non-linear editing** - Jump to any marker's metadata without going through all
✅ **Visual overview** - See completion status at a glance
✅ **Focused Export Center** - Just metadata editing and file organization (no redundant video player)
✅ **Ingest-ready** - Organized folder structure for handoff
✅ **Professional** - Production-ready export workflow

---

## Metadata Structures

### SFX Metadata

```json
{
  "file": "SFX_00001_UI_Click.mp3",
  "type": "sfx",
  "timestamp_ms": 150,
  "duration_ms": 250,
  "title": "UI Click Sound",
  "categories": ["UI Elements", "Devices"],
  "notes": "Clean, subtle click for button interactions",
  "usedInTemplates": ["DM01", "DM03", "MTG01"],
  "generated_at": "2025-12-30T10:30:00Z",
  "prompt_used": {
    "description": "UI click, subtle, clean"
  }
}
```

**Fields**:
- `file` (string, required): Generated audio filename
- `type` (string, required): Always "sfx"
- `timestamp_ms` (integer, required): Position in video timeline
- `duration_ms` (integer, required): Length of audio file
- `title` (string, required): Human-readable name
- `categories` (array, required): 1-3 categories from SFX taxonomy
- `notes` (string, optional): Freeform description/usage notes
- `usedInTemplates` (array, required): List of template IDs using this asset
- `generated_at` (ISO 8601, required): Generation timestamp
- `prompt_used` (object, required): Original prompt data used for generation

---

### Music Metadata

```json
{
  "file": "MUS_00001_Electronic_Upbeat.mp3",
  "type": "music",
  "timestamp_ms": 0,
  "duration_ms": 12500,
  "title": "Electronic Upbeat Intro",
  "categories": {
    "genre": "Electronic",
    "subGenre": "Synth Pop",
    "key": "C Major",
    "bpm": 128,
    "instruments": ["Synthesizer", "Drums", "Bass"],
    "mood": ["Energetic", "Upbeat"],
    "intensity": "Moderate"
  },
  "notes": "High-energy intro, works well for tech/lifestyle content",
  "usedInTemplates": ["DM01", "MTG01"],
  "generated_at": "2025-12-30T10:30:00Z",
  "prompt_used": {
    "positiveGlobalStyles": ["electronic", "fast-paced", "energetic"],
    "negativeGlobalStyles": ["acoustic", "slow", "ambient"],
    "sections": [...]
  }
}
```

**Fields**:
- `file` (string, required): Generated audio filename
- `type` (string, required): Always "music"
- `timestamp_ms` (integer, required): Position in video timeline
- `duration_ms` (integer, required): Length of audio file
- `title` (string, required): Human-readable name
- `categories` (object, required): Structured music categorization
  - `genre` (string, 1 item): Primary musical genre
  - `subGenre` (string, 1 item): More specific genre classification
  - `key` (string, 1 item): Musical key (e.g., "C Major", "A Minor", "Unknown")
  - `bpm` (integer, 1 item): Beats per minute (actual tempo number)
  - `instruments` (array, 1-5 items): Primary instruments featured
  - `mood` (array, 1-3 items): Emotional quality
  - `intensity` (string, 1 item): Energy level
- `notes` (string, optional): Freeform description/usage notes
- `usedInTemplates` (array, required): List of template IDs using this asset
- `generated_at` (ISO 8601, required): Generation timestamp
- `prompt_used` (object, required): Original prompt data used for generation

---

### Voice Metadata

```json
{
  "file": "VOX_00001_Female_30s_Australian.mp3",
  "type": "voice",
  "timestamp_ms": 2000,
  "duration_ms": 3500,
  "title": "Camera Roll Quote",
  "categories": {
    "gender": "Female",
    "age": "Young Adult",
    "accent": "Australian",
    "tone": "Warm",
    "delivery": "Narration"
  },
  "notes": "First-person narration, conversational style",
  "usedInTemplates": ["DM01"],
  "generated_at": "2025-12-30T10:30:00Z",
  "prompt_used": {
    "voice_profile": "Warm female narrator, mid-30s, Australian accent",
    "text": "Camera roll lately..."
  }
}
```

**Fields**:
- `file` (string, required): Generated audio filename
- `type` (string, required): Always "voice"
- `timestamp_ms` (integer, required): Position in video timeline
- `duration_ms` (integer, required): Length of audio file
- `title` (string, required): Human-readable name
- `categories` (object, required): Structured voice categorization
  - `gender` (string, 1 item): Speaker gender
  - `age` (string, 1 item): Age category
  - `accent` (string, 1 item): Regional accent
  - `tone` (string, 1 item): Vocal quality
  - `delivery` (string, 1 item): Performance style
- `notes` (string, optional): Freeform description/usage notes
- `usedInTemplates` (array, required): List of template IDs using this asset
- `generated_at` (ISO 8601, required): Generation timestamp
- `prompt_used` (object, required): Original prompt data used for generation

---

### Assembled Audio Metadata

```json
{
  "template_id": "DM01",
  "template_name": "Indoor Routine",
  "total_duration_ms": 12000,
  "video_reference": "DM01_Indoor_Routine.mp4",
  "marker_count": {
    "music": 1,
    "sfx": 2,
    "voice": 1,
    "total": 4
  },
  "markers_included": [
    "MUS_00001_Electronic_Upbeat.mp3",
    "SFX_00001_UI_Click.mp3",
    "SFX_00012_Whoosh.mp3",
    "VOX_00001_Female_30s_Australian.mp3"
  ],
  "assembled_file": "DM01_assembled.wav",
  "export_format": {
    "channels": 5,
    "channel_map": {
      "1": "music_left",
      "2": "music_right",
      "3": "sfx_1",
      "4": "sfx_2",
      "5": "voice"
    },
    "channel_types": {
      "1-2": "stereo",
      "3": "mono",
      "4": "mono",
      "5": "mono"
    },
    "sample_rate": 48000,
    "bit_depth": 24
  },
  "exported_at": "2025-12-30T11:00:00Z",
  "exported_by": "Audio Mapper v1.0",
  "version": "1.0"
}
```

**Fields**:
- `template_id` (string, required): Unique template identifier
- `template_name` (string, required): Human-readable template name
- `total_duration_ms` (integer, required): Total timeline duration
- `video_reference` (string, optional): Original video filename
- `marker_count` (object, required): Breakdown by type + total
- `markers_included` (array, required): List of all audio files included
- `assembled_file` (string, required): Output filename
- `export_format` (object, required): Technical audio specs
- `exported_at` (ISO 8601, required): Export timestamp
- `exported_by` (string, required): Tool name and version
- `version` (string, required): Metadata schema version

---

## Category Taxonomies

### SFX Categories (38 total)

**Extracted from ElevenLabs SFX library**:

```
Animals          Bass            Booms           Braams
Brass            Cymbals         Devices         Drones
Fantasy          Foley           Guitar          Horror
Household        Humans          Impacts         Industrial
Keys             Misc            Nature          Ocean
Office           Parks           Percussion      Restaurants
Risers           School          Sci-Fi          Sports
Strings          Synth           Transport       UI Elements
Urban            Vehicles        Weapons         Weather
Whooshes         Woodwinds
```

**Usage in UI**:
- Multi-select dropdown (choose 1-3 categories)
- Searchable/filterable
- Most common: UI Elements, Foley, Impacts, Nature, Devices

---

### Music Categories

#### Genre (choose 1)
```
Acoustic         Ambient         Chillhop        Cinematic
Classical        Country         Electronic      Folk
Hip Hop          Indie           Jazz            Lo-Fi
Metal            Orchestral      Pop             R&B
Rock             Soul            Synth           Trap
World            Other
```

#### Sub-Genre (choose 1, genre-specific)
**Electronic Sub-genres:**
```
House            Techno          Trance          Dubstep
Drum & Bass      Synth Pop       Electro House   Future Bass
Chillwave        Vaporwave
```

**Hip Hop Sub-genres:**
```
Trap             Boom Bap        Lo-Fi Hip Hop   Cloud Rap
Jazz Rap         G-Funk
```

**Rock Sub-genres:**
```
Indie Rock       Alternative     Pop Rock        Hard Rock
Punk             Progressive
```

**Other genres**: Define sub-genres as needed

#### Musical Key (choose 1 or "Unknown")
```
C Major          C Minor         C# Major        C# Minor
D Major          D Minor         D# Major        D# Minor
E Major          E Minor         F Major         F Minor
F# Major         F# Minor        G Major         G Minor
G# Major         G# Minor        A Major         A Minor
A# Major         A# Minor        B Major         B Minor
Unknown
```

#### BPM (enter exact number or range)
```
Input field: [___] BPM
Examples: 120, 128, 90-100, Variable
```

#### Instruments (choose 1-5)
```
Acoustic Guitar  Electric Guitar  Bass Guitar     Piano
Synthesizer      Drums           Percussion      Strings
Brass            Woodwinds       Vocals          Pad/Ambient
808/Sub Bass     Bells           Harp            Organ
Other
```

#### Mood (choose 1-3)
```
Calm             Cheerful        Dark            Dramatic
Energetic        Epic            Happy           Hopeful
Inspirational    Intense         Melancholic     Mysterious
Nostalgic        Peaceful        Playful         Romantic
Sad              Tense           Upbeat          Uplifting
```

#### Intensity (choose 1)
```
Subtle           Moderate        Intense         Extreme
```

---

### Voice Categories

#### Gender (choose 1)
```
Male             Female          Non-binary      Multiple Voices
```

#### Age (choose 1)
```
Child (0-12)
Teen (13-19)
Young Adult (20-35)
Adult (36-55)
Senior (56+)
```

#### Accent (choose 1)
```
American (General)    American (Southern)   American (New York)
Australian            British (RP)          British (Cockney)
Canadian              Indian                Irish
Scottish              South African         None/Neutral
Other
```

#### Tone (choose 1-2)
```
Authoritative    Calm            Casual          Conversational
Dramatic         Emotional       Energetic       Formal
Friendly         Professional    Sarcastic       Serious
Warm             Whispered
```

#### Delivery (choose 1)
```
Narration        Dialogue        Announcement    Commercial
Documentary      Storytelling    Voiceover       Whisper
Shout            Singing
```

---

## Export File Structure

### Output Directory Layout

```
DM01_Indoor_Routine/
├── MUSIC/
│   ├── MUS_00001_Electronic_Upbeat.mp3
│   └── MUS_00001_metadata.json
├── SFX/
│   ├── SFX_00001_UI_Click.mp3
│   ├── SFX_00001_metadata.json
│   ├── SFX_00012_Whoosh.mp3
│   └── SFX_00012_metadata.json
├── VOICE/
│   ├── VOX_00001_Female_30s_Australian.mp3
│   └── VOX_00001_metadata.json
├── DM01_assembled.wav          # Multi-channel assembled audio
├── DM01_template.json          # Original template with all markers
└── DM01_export_metadata.json   # Assembled audio metadata
```

### File Naming Conventions

**Individual Audio Files**:
- Format: `{TYPE}_{INDEX}_{DESCRIPTIVE_NAME}.mp3`
- Example: `SFX_00002_Whoosh.mp3`
- Type prefix: `MUS` (music), `SFX` (sound effects), `VOX` (voice)
- Index: Zero-padded 5-digit number (auto-incremented)
- Name: User-provided descriptive name (from marker title)

**Auto-numbering Logic**:
1. User generates audio for marker named "Whoosh" (type: SFX)
2. System checks existing SFX files in project/library
3. Finds latest: `SFX_00001_UI_Click.mp3`
4. Auto-increments: Creates `SFX_00002_Whoosh.mp3`
5. Updates marker's `asset_file` field automatically

**Numbering is per-type**:
- SFX files: `SFX_00001`, `SFX_00002`, `SFX_00003`, ...
- Music files: `MUS_00001`, `MUS_00002`, `MUS_00003`, ...
- Voice files: `VOX_00001`, `VOX_00002`, `VOX_00003`, ...

**User Workflow**:
- User only provides descriptive name (e.g., "Whoosh", "Electronic_Upbeat")
- System handles numbering automatically
- No manual index management required

**Metadata Files**:
- Individual: `{AUDIO_FILENAME}_metadata.json`
- Assembled: `{TEMPLATE_ID}_export_metadata.json`
- Template: `{TEMPLATE_ID}_template.json`

**Assembled Audio**:
- Format: `{TEMPLATE_ID}_assembled.wav`
- 5-channel WAV (24-bit, 48kHz)
- Channel mapping:
  - Channels 1-2: Music (Stereo L/R)
  - Channel 3: SFX Track 1 (Mono)
  - Channel 4: SFX Track 2 (Mono)
  - Channel 5: Voice (Mono)

---

## Implementation Plan

### Phase 1: Data Structures (Week 1)
- [ ] Add metadata fields to `Marker` class in `core/models.py`
- [ ] Create category constants in new `core/categories.py`
- [ ] Add metadata validation functions
- [ ] Update JSON export/import to include metadata
- [ ] Implement auto-numbering logic in `services/audio_service.py`
  - Check existing files of same type
  - Auto-increment index (SFX_00001 → SFX_00002)
  - Generate filename: `{TYPE}_{INDEX}_{MARKER_NAME}.mp3`
- [ ] Update main window UI: Change "Export JSON" button → "Assemble" button
- [ ] Add File → Export JSON menu item

### Phase 2: Export Center UI (Week 2)
- [ ] Create `ExportCenterWindow` class in `ui/export/`
- [ ] Left panel: Marker list with checkmarks
- [ ] Right panel: Metadata editor
- [ ] Category dropdowns (multi-select for tags)
- [ ] Audio preview integration (reuse waveform manager)

### Phase 3: Assembly Integration (Week 3)
- [ ] "Assemble" button in main window
  - Generate multi-channel preview (reuse `assemble_audio.py` logic)
  - Replace video player audio with assembled result
  - Allow playback in existing main window video player
- [ ] Assembled waveform visualization in main window
  - Update waveform display to show combined layers
  - Visual confirmation of assembly
- [ ] "Export" button in main window (enabled after successful assembly)
  - Opens Export Center for metadata editing

### Phase 4: Export Functionality (Week 4)
- [ ] Create organized folder structure
- [ ] Copy audio files to categorized folders
- [ ] Generate individual metadata JSON files
- [ ] Generate assembled metadata JSON
- [ ] Generate final template JSON

### Phase 5: Polish & Testing (Week 5)
- [ ] Keyboard shortcuts (Cmd+E to open)
- [ ] Form validation (required fields)
- [ ] Error handling (missing files, invalid metadata)
- [ ] User feedback (progress indicators, success messages)
- [ ] Comprehensive testing

---

## Technical Notes

### Metadata Storage

**During Editing** (in-memory):
- Metadata stored in `Marker` object attributes
- Updated via Export Center UI

**On Export** (persisted):
- Individual JSON files per audio file
- Aggregate JSON for assembled audio
- Original template JSON preserved

### Category UI Components

**Multi-select Dropdowns**:
- Use `ttk.Combobox` with checkboxes
- Or custom listbox with multi-selection
- Max selections enforced (e.g., 1-3 for SFX categories)

**Validation Rules**:
- SFX: 1-3 categories required
- Music: Genre + Sub-genre + Key + BPM + 1-5 Instruments + 1-3 Moods + Intensity
- Voice: All 5 category fields required (gender, age, accent, tone, delivery)
- Title: Always required, max 100 characters
- Notes: Optional, max 500 characters

### "Used In Templates" Tracking

**Purpose**: Track which templates use each audio asset for reuse and library management.

**How It Works**:
1. **On First Export**: `usedInTemplates` initialized with current template ID
   ```json
   "usedInTemplates": ["DM01"]
   ```

2. **When Reusing Asset** (future "Existing Library" feature):
   - User loads audio from library into new template
   - Template ID automatically added to array
   ```json
   "usedInTemplates": ["DM01", "DM03", "MTG01"]
   ```

3. **Display in Export Center**:
   - Shows "Used in: DM01, DM03, MTG01" (read-only)
   - Helps user understand asset reuse
   - Warns if editing metadata will affect multiple templates

4. **Export Behavior**:
   - Each template export updates the asset's metadata file
   - Array maintains complete usage history
   - No duplicates (set-like behavior)

**Benefits**:
- Know which templates depend on an asset
- Avoid accidentally deleting assets still in use
- Understand asset popularity/reusability
- Foundation for future "Asset Library" feature

**Future "Existing Library" Feature**:
- Browse all previously generated assets
- Filter by type, categories, templates used
- Drag existing asset into new template
- Automatically updates `usedInTemplates` array
- Prevents regeneration of identical audio

---

## Future Enhancements

### Potential Features
- [ ] Metadata templates (save/load common category combinations)
- [ ] Bulk metadata editing (apply to multiple markers)
- [ ] Search/filter markers by metadata
- [ ] Export format options (WAV vs MP3, sample rate, bit depth)
- [ ] Cloud storage integration (upload to S3/GCS)
- [ ] Team collaboration (share templates + metadata)
- [ ] Version control (track metadata changes over time)

---

**End of Metadata & Export Plan**

This is a living document. Update as requirements evolve and features are implemented.
