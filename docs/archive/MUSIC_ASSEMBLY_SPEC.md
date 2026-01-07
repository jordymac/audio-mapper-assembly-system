# Music Assembly & Duration Flexibility - Design Specification

**Created**: 2025-12-29
**Status**: Design Phase
**Related Roadmap Issue**: #2 - Music Assembly Timing

---

## Problem Statement

### Scenario: Template Duration vs Creator Duration

**Template Designer Workflow:**
1. Create 15s video template in Canva
2. Generate audio markers and timecode map
3. Generate audio assets (music, SFX, voice)
4. Export template for creators to use

**Creator Workflow in Canva:**
1. Open 15s template
2. Add more clips/content → video becomes 45s, 1min, or longer
3. Need audio to extend to match new duration
4. Want control over which part of music plays

### Current Problem

**Issue 1: Fixed Duration Generation**
- If we generate exactly 15s of music, creators can't extend beyond 15s
- Annoying when they add clips and need longer audio

**Issue 2: No Start Point Control**
- Generated music always starts at 0:00
- Can't skip intro, start at drop, or use climax section
- No way to select "this video should start at 0:30 into the music"

---

## Solution Design

### Part 1: Generate Long Music Upfront

**Strategy**: Always generate 2-3min music tracks regardless of template duration

**Benefits:**
- Covers any reasonable creator extension
- Same music file reusable for multiple durations
- Creator can trim/extend in Canva timeline editor
- No special looping logic needed

**Workflow:**
```
Template Duration: 15s
Generated Music: 3min (180s)

Creator extends to 45s:
→ Drags music clip in Canva to 45s
→ Uses 0:00-0:45 of 3min track ✓

Creator makes 2min version:
→ Drags music clip to 2min
→ Uses 0:00-2:00 of 3min track ✓
```

**Recommendation:**
- Default music generation: 2-3min
- Template can specify longer if needed
- Document this as best practice

---

### Part 2: Music Start Offset Control

**Feature**: Select where in the music track the video timeline starts

**Use Cases:**
- Skip 30s intro, start video at the main section
- Start at 1:45 climax for high-energy templates
- Avoid slow outro, use middle section
- Different start points for variations

**Visual Example:**
```
Music File (3min):
[0:00 === Intro === 0:30 === Main === 1:45 === Climax === 3:00]
                      ↑                  ↑
                 Option A           Option B

Video Timeline (45s):
Option A: [0:00 ============== 0:45]
           ↓                     ↓
        Music 0:30          Music 1:15

Option B: [0:00 ============== 0:45]
           ↓                     ↓
        Music 1:45          Music 2:30
```

---

## Data Model

### Marker Type Schemas

Different marker types have different schemas based on their use cases:

---

### Music Marker (Has Offset Control):

```json
{
  "time_ms": 0,
  "type": "music",
  "name": "MUS_00001_Electronic_Upbeat",
  "prompt_data": {
    "positiveGlobalStyles": ["electronic", "upbeat", "energetic"],
    "negativeGlobalStyles": ["slow", "acoustic"],
    "sections": [...]
  },
  "asset_slot": "music_0",
  "asset_file": "MUS_00001.mp3",
  "asset_id": "elevenlabs-xyz789",
  "status": "generated",

  "assemblyConfig": {
    "startOffsetMs": 30000,      // NEW: Start video at 30s into music
    "fadeInMs": 50,               // NEW: Fade in duration (default: 50ms)
    "fadeOutMs": 50,              // NEW: Fade out duration (default: 50ms)
    "targetDurationMs": null      // Optional: Force specific duration
  }
}
```

**Why Music has assemblyConfig:**
- Music tracks are often 2-3min long
- Creator may extend video beyond template duration
- Need to select which portion of music to use
- Start offset provides creative control over which part plays

---

### SFX Marker (No Offset Control):

```json
{
  "time_ms": 2000,
  "type": "sfx",
  "name": "SFX_00001_Door_Slam",
  "prompt_data": {
    "description": "heavy wooden door slam, sharp attack",
    "duration": 1.5,              // ElevenLabs param: 0.1-30s (optional)
    "looping": false,             // ElevenLabs param: seamless loop
    "promptInfluence": "high"     // ElevenLabs param: literal vs creative
  },
  "asset_slot": "sfx_0",
  "asset_file": "SFX_00000.mp3",
  "asset_id": "elevenlabs-abc123",
  "status": "generated"

  // NO assemblyConfig - SFX are one-shots, use full clip
}
```

**Why SFX has NO assemblyConfig (for now):**
- SFX are typically short (< 30s)
- Triggered at specific moments (one-shot sounds)
- Usually want the entire generated clip
- Duration controlled during generation, not assembly

**ElevenLabs SFX Generation Parameters:**
- `duration`: 0.1 to 30 seconds (optional, auto-determined if not specified)
  - Cost: 40 credits per second when specified
- `looping`: Enable seamless loop for sounds > 30s
  - Perfect for ambient textures, background elements
  - Example: Generate 30s of 'soft rain' then loop endlessly
- `promptInfluence`: How strictly to follow prompt
  - `"high"`: More literal interpretation
  - `"low"`: More creative interpretation with variations

---

### Voice Marker (No Offset Control):

```json
{
  "time_ms": 5000,
  "type": "voice",
  "name": "VOX_00001_Female_30s_Australian",
  "prompt_data": {
    "voice_profile": "Warm female narrator, mid-30s, Australian accent",
    "text": "Camera roll lately..."
    // Voice-specific generation params TBD
  },
  "asset_slot": "voice_0",
  "asset_file": "VOX_00000.mp3",
  "asset_id": "elevenlabs-def456",
  "status": "generated"

  // NO assemblyConfig - Voice clips use full spoken text
}
```

**Why Voice has NO assemblyConfig:**
- Voice clips are exact text-to-speech of provided text
- Duration determined by text length
- Usually want the entire spoken phrase
- Trimming would cut off words

---

### Feature Comparison

| Feature | Music | SFX | Voice |
|---------|-------|-----|-------|
| **assemblyConfig** | ✅ Yes | ❌ No (for now) | ❌ No |
| **Start Offset** | ✅ Yes | ❌ No | ❌ No |
| **Fade In/Out** | ✅ Yes | ❌ No | ❌ No |
| **Generation Params** | In prompt_data | ✅ Yes (duration, looping, influence) | TBD |
| **Waveform Preview** | ✅ Yes (in popup) | ✅ Yes (visual only) | ✅ Yes (visual only) |
| **Audio Playback** | ✅ Yes | ✅ Yes | ✅ Yes |

**Notes:**
- **Music** is the only type with assembly-time controls (offset, fades)
- **SFX** and **Voice** use full generated clips (no trimming/offset)
- All types show waveform for visual reference
- All types have playback preview button

---

### Field Definitions (Music Only)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `startOffsetMs` | integer | No | 0 | Milliseconds into music file where video 0:00 starts |
| `fadeInMs` | integer | No | 50 | Fade in duration at start (50ms default) |
| `fadeOutMs` | integer | No | 50 | Fade out duration at end (50ms default) |
| `targetDurationMs` | integer | No | null | Force music to specific duration (null = use full file from offset) |

### Offset Validation

**Maximum Offset Calculation:**
```python
# Maximum allowed offset
max_offset = audio_duration_ms - video_duration_ms

# Example:
# Audio: 3min (180,000ms)
# Video: 45s (45,000ms)
# Max Offset: 180,000 - 45,000 = 135,000ms (2:15)

if user_offset > max_offset:
    show_error(f"Offset too large. Maximum: {format_time(max_offset)}\n"
               f"Audio must cover full video duration.")
```

**Why this validation:**
- Starting at offset means "play audio from this point forward"
- Need enough audio remaining to cover entire video duration
- If audio is 3min and video is 45s, can start up to 2:15 into the audio
- Starting later would run out of audio before video ends

**UI Implementation:**
- Calculate and display max offset when waveform loads
- Show error tooltip if user exceeds max
- Gray out waveform area beyond max offset (visual feedback)

---

### Backward Compatibility

**Missing `assemblyConfig`:**
- Default to `startOffsetMs: 0` (start at beginning)
- Default to no fades
- Existing templates work unchanged

**Old Format Support:**
```json
// Old format (still works)
{
  "type": "music",
  "asset_file": "MUS_00001.mp3"
}

// Automatically treated as:
{
  "type": "music",
  "asset_file": "MUS_00001.mp3",
  "assemblyConfig": {
    "startOffsetMs": 0,
    "fadeInMs": 0,
    "fadeOutMs": 0
  }
}
```

---

## UI Design

### Music Editor Window - Audio Preview at Top

**Layout Behavior:**
- **Before Generation**: Standard prompt editor (500x600px)
- **After Generation**: Audio preview section appears at top (550-600px wide, 750-800px tall)

---

### Before Generation (New Marker):
```
┌─ Edit Marker ───────────────────────┐
│                                  [×] │
│  Name: [MUS_00001_Electronic___]    │
│  Type: [Music ▼]                    │
│                                      │
│  Positive Global Styles:             │
│  ┌──────────────────────────────┐   │
│  │ electronic, upbeat           │   │
│  └──────────────────────────────┘   │
│                                      │
│  Negative Global Styles:             │
│  ┌──────────────────────────────┐   │
│  │ slow, acoustic               │   │
│  └──────────────────────────────┘   │
│                                      │
│  Sections:                           │
│  - Intro (3000ms)                    │
│  - Main (10000ms)                    │
│  [Add Section] [Edit] [Remove]       │
│                                      │
│         [Save]  [Cancel]             │
└──────────────────────────────────────┘
```

---

### After Generation (Editing Generated Marker):
```
┌─ Edit Marker ───────────────────────────────────┐
│                                              [×] │
│  ┌─ Audio Preview ───────────────────────────┐  │
│  │                                           │  │
│  │  ████▆▅▇██▅▄▆███▇▅▄▃▅▇███▅▄▆███         │  │
│  │  ^              ^                         │  │
│  │  0:00         0:30 (offset)               │  │
│  │                                           │  │
│  │  [▶ Play from offset] [⏸ Pause]          │  │
│  │                                           │  │
│  │  Music Start Offset: [00:30] ← Click ↑   │  │
│  │  Fade In:  [500ms]   Fade Out: [1000ms]  │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  ─────────────────────────────────────────────  │
│                                                  │
│  Name: [MUS_00001_Electronic___]                │
│  Type: [Music ▼]                                │
│                                                  │
│  Positive Global Styles:                        │
│  ┌──────────────────────────────────┐           │
│  │ electronic, upbeat               │           │
│  └──────────────────────────────────┘           │
│                                                  │
│  Negative Global Styles:                        │
│  ┌──────────────────────────────────┐           │
│  │ slow, acoustic                   │           │
│  └──────────────────────────────────┘           │
│                                                  │
│  Sections:                                       │
│  - Intro (3000ms)                                │
│  - Main (10000ms)                                │
│  [Add Section] [Edit] [Remove]                   │
│                                                  │
│         [Save]  [Cancel]                         │
└──────────────────────────────────────────────────┘
```

---

### Audio Preview Section Details:

**Components:**
1. **Waveform Canvas** (400px wide, 60px tall)
   - Visual representation of audio amplitude
   - Vertical line indicator at offset position
   - Click anywhere to set new offset

2. **Playback Controls**
   - Play button: Starts playback from offset position
   - Pause button: Pauses playback
   - Auto-updates offset field when waveform clicked

3. **Offset Control**
   - Text input: MM:SS format (e.g., "00:30")
   - Synced with waveform click position
   - Tooltip: "Click waveform or enter time"

4. **Fade Controls**
   - Fade In (ms): Integer input, default 500
   - Fade Out (ms): Integer input, default 1000

**Visibility:**
- Only shown when `marker.status == "generated"`
- Hidden for new markers (not yet generated)
- Appears after successful generation

---

### Window Dimensions:

| State | Width | Height |
|-------|-------|--------|
| **Before Generation** | 500px | 600px |
| **After Generation** | 550-600px | 750-800px |

**Auto-resize:** Window expands when audio preview section appears

---

### User Experience Flow:

1. **Create new marker** → Popup opens (500x600) → No audio preview → Edit prompt → Save
2. **Click Generate** (main window) → API call → Audio generated → Status updates
3. **Edit generated marker** → Popup opens (600x800) → Audio preview at top → Adjust offset → Save
4. **Regenerate** → New audio → Waveform updates → **Offset preserved** (if previously set)
5. **Click waveform** → Offset marker moves → Input field updates → Can preview immediately

---

### Main Window Marker Section (Optional Enhancement)

**Enhanced Marker List with Waveform Column:**

**Before generation:**
```
┌─ Markers ─────────────────────────────────────────────────────────────┐
│ Time    Type   Name                    Status              Actions    │
│ ✏️ 0:00  MUSIC  MUS_00001_Electronic   [Generate]          [Edit][Del]│
│ ✏️ 2:00  SFX    SFX_00001_Click        not yet generated   [Edit][Del]│
└───────────────────────────────────────────────────────────────────────┘
```

**After generation (with waveform preview):**
```
┌─ Markers ────────────────────────────────────────────────────────────────────────┐
│ Time  Type  Name              Waveform Preview    Offset      Actions            │
│────────────────────────────────────────────────────────────────────────────────│
│ ✏️ 0:00 MUSIC MUS_00001_Elec  [▄▅▇██▇▅▄▃▅▇█▅▄]   🎵 Start:    [▶][Edit][Del]   │
│                                 ^                 [00:30]                        │
│                                 └─ offset marker                                 │
│                                                                                   │
│ ✏️ 2:00 SFX   SFX_00001_Click  [█▅▄]              -           [▶][Edit][Del]    │
│                                                                                   │
│ ✏️ 5:00 VOICE VOX_Narration    [▃▅█▅▃]            -           [▶][Edit][Del]    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Main Window Dimensions:**
- Current width: ~800px
- With waveform: **~1000px** (to fit waveform + offset columns comfortably)

**Column Widths:**
- Time: 60px
- Type: 50px
- Name: 200px
- **Waveform: 300px** (new)
- Offset: 80px (new, music only)
- Actions: 100px

**Benefits:**
- Quick visual reference for all markers
- See offset at a glance without opening editor
- Play button for quick preview
- Waveform shows for all marker types (music, SFX, voice)

**Note:** This is an optional enhancement. The core feature (waveform in popup editor) works independently.

---

## Implementation Plan

### Phase 1: Data Model & Backend

**Files to Modify:**
- `core/models.py` - Add `assemblyConfig` to marker schema
- `assemble_audio.py` - Implement offset and fade logic

**Task List:**
- [ ] Add `assemblyConfig` dict to Marker model
- [ ] Add validation for `startOffsetMs`, `fadeInMs`, `fadeOutMs`
- [ ] Update `assemble_audio.py` to read `assemblyConfig`
- [ ] Implement audio trimming (start offset)
- [ ] Implement fade in/out using pydub
- [ ] Add backward compatibility checks
- [ ] Write tests for assembly with offsets

**Assembly Logic (pseudocode):**
```python
def assemble_music_marker(marker, audio_dir, video_duration_ms):
    # Load music file
    audio = AudioSegment.from_file(marker['asset_file'])

    # Get assembly config (with defaults)
    config = marker.get('assemblyConfig', {})
    start_offset = config.get('startOffsetMs', 0)
    fade_in = config.get('fadeInMs', 0)
    fade_out = config.get('fadeOutMs', 0)

    # Apply start offset (trim from beginning)
    if start_offset > 0:
        audio = audio[start_offset:]

    # Trim to video duration (optional)
    if len(audio) > video_duration_ms:
        audio = audio[:video_duration_ms]

    # Apply fades
    if fade_in > 0:
        audio = audio.fade_in(fade_in)
    if fade_out > 0:
        audio = audio.fade_out(fade_out)

    return audio
```

---

### Phase 2: UI Implementation

**Files to Modify:**
- `ui/editors/music_editor.py` - Add Assembly Settings section

**Task List:**
- [ ] Add collapsible "Assembly Settings" frame
- [ ] Add start offset input (ms and MM:SS format)
- [ ] Add fade in/out inputs
- [ ] Add helper text that updates dynamically
- [ ] Update save logic to include `assemblyConfig`
- [ ] Update load logic to populate `assemblyConfig` fields
- [ ] Test round-trip (save → export → import → edit)

**UI Component Structure:**
```python
class MusicEditorWindow:
    def create_assembly_settings_section(self):
        # Collapsible frame
        assembly_frame = ttk.LabelFrame(
            self.content_frame,
            text="Assembly Settings (Optional)",
            padding=10
        )

        # Start offset input
        tk.Label(assembly_frame, text="Music Start Offset:").grid(...)
        self.start_offset_ms = tk.Entry(assembly_frame)
        self.start_offset_mmss = tk.Entry(assembly_frame)

        # Bind to sync ms <-> MM:SS
        self.start_offset_ms.bind('<KeyRelease>', self.update_mmss_from_ms)
        self.start_offset_mmss.bind('<KeyRelease>', self.update_ms_from_mmss)

        # Fade inputs
        tk.Label(assembly_frame, text="Fade In (ms):").grid(...)
        self.fade_in = tk.Entry(assembly_frame)

        tk.Label(assembly_frame, text="Fade Out (ms):").grid(...)
        self.fade_out = tk.Entry(assembly_frame)

        return assembly_frame

    def save_music_data(self):
        # ... existing prompt_data save logic ...

        # Add assembly config
        assembly_config = {
            'startOffsetMs': int(self.start_offset_ms.get() or 0),
            'fadeInMs': int(self.fade_in.get() or 0),
            'fadeOutMs': int(self.fade_out.get() or 0)
        }

        self.updated_marker['assemblyConfig'] = assembly_config
```

---

### Phase 3: Testing & Documentation

**Test Cases:**
- [ ] Music with no offset (0ms) - verify starts at beginning
- [ ] Music with 30s offset - verify starts at 0:30
- [ ] Music with fade in/out - verify smooth transitions
- [ ] Import old format (no assemblyConfig) - verify defaults
- [ ] Round-trip test (create → export → import → edit)
- [ ] Assembly with 3min music, 45s video, 30s offset
- [ ] Edge case: offset > music duration (should error gracefully)

**Documentation Updates:**
- [ ] Update CLAUDE.md with assemblyConfig schema
- [ ] Update README.md with music offset workflow
- [ ] Add example JSON with assemblyConfig
- [ ] Update ROADMAP.md to mark Issue #2 complete

---

## Example Workflows

### Workflow 1: Standard Template (No Offset)

**Template Designer:**
```json
{
  "markers": [
    {
      "time_ms": 0,
      "type": "music",
      "asset_file": "MUS_00001.mp3",
      "assemblyConfig": {
        "startOffsetMs": 0,
        "fadeInMs": 500,
        "fadeOutMs": 1000
      }
    }
  ]
}
```

**Result:**
- Music starts at 0:00 of track
- Smooth fade in (500ms)
- Smooth fade out at end (1000ms)

---

### Workflow 2: Skip Intro, Start at Drop

**Template Designer:**
```json
{
  "markers": [
    {
      "time_ms": 0,
      "type": "music",
      "name": "MUS_00001_Electronic_Drop",
      "asset_file": "MUS_00001.mp3",
      "assemblyConfig": {
        "startOffsetMs": 45000,  // Start at 0:45 (the drop)
        "fadeInMs": 200,         // Quick fade in
        "fadeOutMs": 1000
      }
    }
  ]
}
```

**Result:**
- Video 0:00 starts at 0:45 into music (skips intro)
- Drop hits immediately at video start
- Quick 200ms fade in to avoid click

---

### Workflow 3: Multiple Templates, Same Music, Different Offsets

**Use Case:** Create variations of same template using different parts of one long track

```json
// Variation A: Calm intro (start at 0:30)
{
  "template_id": "DM01_A",
  "markers": [
    {"time_ms": 0, "type": "music", "assemblyConfig": {"startOffsetMs": 30000}}
  ]
}

// Variation B: High energy (start at 1:45 climax)
{
  "template_id": "DM01_B",
  "markers": [
    {"time_ms": 0, "type": "music", "assemblyConfig": {"startOffsetMs": 105000}}
  ]
}

// Variation C: Outro vibes (start at 2:30)
{
  "template_id": "DM01_C",
  "markers": [
    {"time_ms": 0, "type": "music", "assemblyConfig": {"startOffsetMs": 150000}}
  ]
}
```

**Result:**
- One 3min music generation
- Three template variations
- Each uses different portion of same track

---

## Future Enhancements

### Phase 4 (Optional): Advanced Features

**Loop Points:**
```json
{
  "assemblyConfig": {
    "startOffsetMs": 30000,
    "loopEnabled": true,
    "loopStartMs": 45000,  // Loop from 0:45
    "loopEndMs": 90000,    // Loop to 1:30
    "crossfadeMs": 2000
  }
}
```

**BPM-Aware Trimming:**
```json
{
  "assemblyConfig": {
    "startOffsetBars": 8,   // Start 8 bars in
    "bpm": 120,
    "snapToBar": true       // Ensure cuts on bar boundaries
  }
}
```

**Auto-Detect Best Start:**
```json
{
  "assemblyConfig": {
    "autoDetectStart": true,
    "avoidSilence": true,      // Skip quiet intro
    "preferHighEnergy": true   // Start at peak energy
  }
}
```

---

## Success Criteria

Feature is complete when:

- [x] `assemblyConfig` added to marker schema
- [x] Assembly script respects `startOffsetMs`
- [x] Assembly script applies fade in/out
- [x] Music Editor UI has Assembly Settings section
- [x] Can set offset in milliseconds or MM:SS format
- [x] Backward compatible with old templates
- [x] All tests pass
- [x] Documentation updated
- [x] Example templates created
- [x] Workflow validated end-to-end

---

## Open Questions

### Resolved ✓
1. ~~**UI Placement**~~ → ✓ Waveform at TOP of popup, only visible after generation
2. ~~**Window Dimensions**~~ → ✓ 500x600 before, 550-600x750-800 after generation
3. ~~**Offset Preservation**~~ → ✓ Preserve offset when regenerating
4. ~~**Waveform Preview**~~ → ✓ Yes, in popup editor (required) and main window (optional)
5. ~~**Default Fade Values**~~ → ✓ 50ms (super short, subtle)
6. ~~**Offset Validation**~~ → ✓ Max offset = audio_duration - video_duration, show error if exceeded
7. ~~**Multiple Music Tracks**~~ → ✓ Yes, each marker (song) has its own offset
8. ~~**Waveform Library**~~ → ✓ Use existing: numpy + moviepy + Tkinter Canvas
9. ~~**Audio Playback**~~ → ✓ Use existing: pygame.mixer (already implemented in audio_player.py)

### Still Open
None! All questions resolved. Ready to implement.

---

**Next Steps**: Review this spec, answer open questions, begin Phase 1 implementation.
