# Audio Assembly Plan

**Last Updated**: 2025-12-30

This document defines the assembly workflow, multi-track visualization, and UI improvements for previewing assembled audio with video in the main window.

---

## Table of Contents
1. [Overview](#overview)
2. [Current UI Issues](#current-ui-issues)
3. [Proposed Multi-Track Layout](#proposed-multi-track-layout)
4. [Assembly Workflow](#assembly-workflow)
5. [Track Assignment Logic](#track-assignment-logic)
6. [Implementation Plan](#implementation-plan)

---

## Overview

**Goal**: Allow users to preview assembled audio (Music + SFX + Voice) synced with video in the main window before exporting.

**Key Requirements**:
- Show multiple audio tracks simultaneously (5 tracks)
- Compact UI to fit all tracks on screen
- Visual clarity: which markers are on which tracks
- Playback assembled audio with video
- Re-assemble when markers change

---

## Current UI Issues

### Screenshot Analysis

**Problems Identified**:
1. **"Add Marker" section takes too much space**
   - Three large horizontal buttons (SFX, Music, Voice)
   - Could be more compact (vertical stack or smaller buttons)
   - Takes valuable vertical space needed for track display

2. **Single waveform display**
   - Currently shows one large waveform
   - Need to show 5 separate tracks:
     - Track 1: Music 1
     - Track 2: Music 2 (or more music)
     - Track 3: SFX (multiple markers)
     - Track 4: SFX (more SFX markers)
     - Track 5: Voice

3. **Waveform height too tall**
   - Current waveform takes ~200px height
   - With 5 tracks, need ~40-50px per track max
   - Need compact waveform visualization

---

## Proposed Multi-Track Layout

### Compact UI Design

```
┌────────────────────────────────────────────────────────────────────────┐
│ Filmstrip: [frame][frame][frame][frame][frame][frame][frame][frame]   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ Track 1 (Music L/R): [~~~~~∿∿∿∿Music∿∿∿∿~~~~~]         🔊 ━━━━━━●   │
│                      [~~~~~∿∿∿∿Music∿∿∿∿~~~~~]         ↑ Stereo      │
│ Ch 3 (SFX 1):        [~~▌~~▌~~~~▌~~~~]                 🔊 ━━━━━━●   │
│ Ch 4 (SFX 2):        [~▌~~~~~~~~~▌~~]                  🔊 ━━━━━━●   │
│ Ch 5 (Voice):        [      ~Voice~        ]           🔊 ━━━━━━●   │
│                                                                        │
│ Timeline: [━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━━━] 0:06.8 / 0:12.0     │
│           ▲ Playhead                                                   │
├────────────────────────────────────────────────────────────────────────┤
│ [▶ Play] [⏸ Pause] [◀◀ -50ms] [▶▶ +50ms]  00:00:06.847  30.00 FPS   │
├────────────────────────────────────────────────────────────────────────┤
│ Markers:                                                               │
│ ✏️ 0:00.000  MUSIC  MUS_00001  ✅  [Ch 1-2 Stereo]                    │
│ ✏️ 0:00.150  SFX    SFX_00001  ✅  [Ch 3 Mono]                        │
│ ✏️ 0:02.000  VOICE  VOX_00001  ✅  [Ch 5 Mono]                        │
├────────────────────────────────────────────────────────────────────────┤
│ [+SFX] [+Music] [+Voice]  [🔨 Assemble] [📦 Export]                  │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Improvements

**1. Compact Multi-Track Display**
- 4 visual tracks (Music stereo shown as 2 rows, SFX 1, SFX 2, Voice)
- Music stereo track: ~80-100px height (L/R waveforms)
- SFX/Voice mono tracks: ~40-50px height each
- Individual volume control per track (🔊 slider on right)
- Track labels on left: "Track 1 (Music L/R)", "Ch 3 (SFX 1)", "Ch 5 (Voice)", etc.
- Waveforms aligned with timeline

**2. Smaller "Add Marker" Buttons**
- Moved to bottom as small buttons: `[+SFX] [+Music] [+Voice]`
- Saves vertical space for track display
- Still color-coded (Red, Blue, Green)

**3. Track Assignment in Marker List**
- Each marker shows assigned track: `[Track 1]`, `[Track 3]`, etc.
- Visual clarity: which marker is on which track
- Can reassign tracks by editing marker

**4. Individual Track Volume**
- Slider on right of each track
- Adjust relative levels during preview
- Doesn't affect export (exports at original levels)

---

## Assembly Workflow

### User Flow

```
1. Create Markers
   ↓
2. Generate Audio for Each Marker
   ↓
3. Click "Assemble" Button
   ↓
4. System assigns markers to tracks:
   - Music markers → Tracks 1-2 (up to 2 music tracks)
   - SFX markers → Tracks 3-4 (distributed across tracks)
   - Voice markers → Track 5
   ↓
5. Generate Multi-Track Preview
   - Combine all markers according to track assignment
   - Create temporary assembled WAV file
   ↓
6. Display Multi-Track Waveforms
   - Show 5 tracks with individual waveforms
   - Timeline synced across all tracks
   ↓
7. Playback with Video
   - Press Play → Video plays with assembled audio
   - All 5 tracks mixed in real-time
   - User verifies sync and timing
   ↓
8. Adjust if Needed
   - Edit markers
   - Re-assemble (click "Assemble" again)
   - Preview again
   ↓
9. Export When Satisfied
   - Click "Export" → Opens Export Center
```

### Assembly Button Behavior

**Before Assemble**:
- Button: `[🔨 Assemble]` (enabled if markers exist)
- Tracks: Empty/grayed out
- Playback: Video plays with original audio (if any)

**After Clicking Assemble**:
- Button changes to: `[🔄 Re-assemble]`
- Tracks: Populated with waveforms
- Playback: Video plays with assembled audio
- Export button: `[📦 Export]` becomes enabled

**Re-assembly**:
- If user edits/adds/removes markers
- Click `[🔄 Re-assemble]` to regenerate preview
- Tracks update with new waveforms

---

## Track Assignment Logic

### Channel Configuration

**5-Channel Layout** (Stereo Music + Mono SFX/Voice):
- **Channels 1-2**: Music (Stereo L/R)
- **Channel 3**: SFX Track 1 (Mono)
- **Channel 4**: SFX Track 2 (Mono)
- **Channel 5**: Voice (Mono)

**Why This Configuration?**
- Music benefits from stereo (wider soundstage, better quality)
- Music markers rarely overlap (can mix all on one stereo track)
- SFX are typically mono point sources (can overlap, need separate channels)
- Voice is typically mono (centered, narrative clarity)

---

### Automatic Track Assignment

**Music Markers** (1 stereo track = Channels 1-2):
- **All** music markers → Track 1 (Stereo)
- Mixed together on same stereo track
- Example:
  - MUS_00001 (0:00.000) → Track 1 (L/R)
  - MUS_00002 (0:03.000) → Track 1 (L/R) - mixed with MUS_00001
- **Unlikely to overlap**: Music markers typically cover different time ranges

**SFX Markers** (2 mono tracks = Channels 3-4):
- Distribute evenly across Channel 3 and Channel 4
- Goal: Balance number of markers per track
- Algorithm: Sort by timestamp, alternate between channels
- **Can overlap**: Multiple SFX can play simultaneously
- Example:
  - SFX_00001 (0:00.150) → Channel 3 (Mono)
  - SFX_00002 (0:01.200) → Channel 4 (Mono)
  - SFX_00003 (0:03.500) → Channel 3 (Mono)
  - SFX_00004 (0:05.800) → Channel 4 (Mono)

**Voice Markers** (1 mono track = Channel 5):
- All voice markers → Channel 5 (Mono)
- Mixed together on same mono track
- Example:
  - VOX_00001 (0:02.000) → Channel 5 (Mono)
  - VOX_00002 (0:08.000) → Channel 5 (Mono)

### Manual Track Assignment (Future Enhancement)

**Drag & Drop**:
- Drag marker from marker list to desired track
- Override automatic assignment
- Useful for complex projects

**Track Overflow**:
- If too many markers for available tracks
- Show warning: "Track 3 has 8 markers - consider splitting"
- Still allows assembly (mix all on same track)

---

## Multi-Track Waveform Visualization

### Compact Waveform Design

**Per-Track Waveform** (~40-50px height):
```
Track 3 (SFX):  [~~▌~~▌~~~~▌~~~~]  🔊 ━━━━━━●
                 ↑  ↑     ↑
                 SFX markers shown as peaks
```

**Features**:
- **Amplitude visualization**: Show waveform shape
- **Marker indicators**: Vertical bars where markers start
- **Color-coded**: Match track type (Music=Blue, SFX=Red, Voice=Green)
- **Synchronized timeline**: All tracks aligned with main timeline
- **Playhead**: Vertical line moves across all tracks during playback

### Track Labels

```
Track 1 (Music 1):   ← Label on left (80px width)
Track 2 (Music 2):
Track 3 (SFX):
Track 4 (SFX):
Track 5 (Voice):
```

### Volume Sliders

```
🔊 ━━━━━━●   ← Volume slider on right (100px width)
   ↑      ↑
   Min    Current position
```

- Range: 0% to 100% (default: 100%)
- Adjusts playback volume for preview only
- Does NOT affect exported audio levels
- Helps user balance tracks during preview

---

## Assembly Algorithm

### Step-by-Step Process

**1. Collect Markers by Type**:
```python
music_markers = [m for m in markers if m.type == "music"]
sfx_markers = [m for m in markers if m.type == "sfx"]
voice_markers = [m for m in markers if m.type == "voice"]
```

**2. Assign to Channels**:
```python
music_stereo = music_markers  # All music → Channels 1-2 (Stereo)
sfx_channel_3 = sfx_markers[::2]   # Even indices → Channel 3
sfx_channel_4 = sfx_markers[1::2]  # Odd indices → Channel 4
voice_mono = voice_markers  # All voice → Channel 5 (Mono)
```

**3. Generate Per-Channel Audio**:
```python
# Music: Stereo (Channels 1-2)
music_stereo_audio = AudioSegment.silent(duration=total_duration_ms).set_channels(2)
for marker in music_markers:
    audio_clip = AudioSegment.from_file(marker.asset_file)
    # Ensure stereo
    if audio_clip.channels == 1:
        audio_clip = audio_clip.set_channels(2)
    music_stereo_audio = music_stereo_audio.overlay(audio_clip, position=marker.time_ms)
save_to_temp("channel_1_2_music_stereo.wav")

# SFX Channel 3: Mono
sfx_3_audio = AudioSegment.silent(duration=total_duration_ms).set_channels(1)
for marker in sfx_channel_3:
    audio_clip = AudioSegment.from_file(marker.asset_file).set_channels(1)
    sfx_3_audio = sfx_3_audio.overlay(audio_clip, position=marker.time_ms)
save_to_temp("channel_3_sfx_1.wav")

# SFX Channel 4: Mono
sfx_4_audio = AudioSegment.silent(duration=total_duration_ms).set_channels(1)
for marker in sfx_channel_4:
    audio_clip = AudioSegment.from_file(marker.asset_file).set_channels(1)
    sfx_4_audio = sfx_4_audio.overlay(audio_clip, position=marker.time_ms)
save_to_temp("channel_4_sfx_2.wav")

# Voice Channel 5: Mono
voice_audio = AudioSegment.silent(duration=total_duration_ms).set_channels(1)
for marker in voice_markers:
    audio_clip = AudioSegment.from_file(marker.asset_file).set_channels(1)
    voice_audio = voice_audio.overlay(audio_clip, position=marker.time_ms)
save_to_temp("channel_5_voice.wav")
```

**4. Combine into 5-Channel WAV**:
```python
# Create 5-channel multi-track WAV
# Channels: 1-2 (Music Stereo), 3 (SFX 1), 4 (SFX 2), 5 (Voice)
from pydub import AudioSegment

# Load all channels
music_lr = AudioSegment.from_file("channel_1_2_music_stereo.wav")  # Stereo
sfx_1 = AudioSegment.from_file("channel_3_sfx_1.wav")  # Mono
sfx_2 = AudioSegment.from_file("channel_4_sfx_2.wav")  # Mono
voice = AudioSegment.from_file("channel_5_voice.wav")  # Mono

# Combine into 5-channel array
# Note: This requires custom WAV writing or using numpy + scipy
# Export as 5-channel WAV for DAW import
save_multichannel_wav("assembled_5ch.wav", [music_lr, sfx_1, sfx_2, voice])

# For preview playback, create stereo mix:
preview = music_lr.overlay(sfx_1).overlay(sfx_2).overlay(voice)
save_to_temp("assembled_preview_stereo.wav")
```

**5. Load into Video Player**:
- Replace video player audio with `assembled_preview.wav`
- Video playback now uses assembled audio instead of original

**6. Generate Waveforms**:
- For each track: `generate_waveform("track_1.wav")`
- Display in compact waveform rows

---

## Implementation Plan

### Phase 1: UI Restructure (Week 1)
- [ ] Move "Add Marker" buttons to bottom (compact layout)
- [ ] Reduce button sizes: `[+SFX] [+Music] [+Voice]`
- [ ] Create multi-track waveform display area (5 rows)
- [ ] Add track labels (Track 1, Track 2, etc.)
- [ ] Add volume sliders per track

### Phase 2: Assembly Logic (Week 2)
- [ ] Implement track assignment algorithm
  - Auto-assign music → Tracks 1-2
  - Auto-assign SFX → Tracks 3-4
  - Auto-assign voice → Track 5
- [ ] Generate per-track audio files (temporary)
- [ ] Mix all tracks into single assembled WAV
- [ ] Save to temp directory for preview

### Phase 3: Waveform Integration (Week 3)
- [ ] Generate waveform for each track
- [ ] Display in compact rows (~40-50px each)
- [ ] Synchronize all waveforms with main timeline
- [ ] Add playhead indicator across all tracks
- [ ] Show marker positions on waveforms (vertical bars)

### Phase 4: Playback Integration (Week 4)
- [ ] "Assemble" button functionality
  - Generate assembled preview
  - Replace video player audio
  - Display multi-track waveforms
- [ ] Playback controls integration
  - Play/Pause applies to assembled audio
  - Timeline scrubber syncs with tracks
- [ ] Volume control per track (real-time mixing)
- [ ] "Re-assemble" button (regenerate if markers changed)

### Phase 5: Polish (Week 5)
- [ ] Color-coding per track type
- [ ] Track overflow warnings
- [ ] Assembly progress indicator
- [ ] Error handling (missing audio files)
- [ ] Keyboard shortcuts (Space=Play/Pause, etc.)

---

## Technical Notes

### File Management

**Temporary Files** (During Preview):
- `temp/channel_1_2_music_stereo.wav` - Music (Stereo L/R)
- `temp/channel_3_sfx_1.wav` - SFX Track 1 (Mono)
- `temp/channel_4_sfx_2.wav` - SFX Track 2 (Mono)
- `temp/channel_5_voice.wav` - Voice (Mono)
- `temp/assembled_preview_stereo.wav` - Stereo mix for playback

**Final Export Files**:
- `DM01_Indoor_Routine/DM01_assembled.wav` - 5-channel WAV
  - Ch 1-2: Music Stereo
  - Ch 3: SFX 1 Mono
  - Ch 4: SFX 2 Mono
  - Ch 5: Voice Mono

**Cleanup**:
- Delete temp files when closing project
- Delete on re-assembly (regenerate fresh)

### Performance Considerations

**Waveform Generation**:
- Use downsampled audio for waveform visualization (faster rendering)
- Cache waveforms (only regenerate if track changes)

**Real-time Mixing**:
- Use pygame/pyaudio for real-time volume adjustments
- Mix tracks on-the-fly during playback based on volume sliders

---

## Future Enhancements

### Track Management
- [ ] Manual drag-and-drop track assignment
- [ ] Solo/mute individual tracks
- [ ] Lock tracks (prevent changes)
- [ ] Rename tracks

### Advanced Features
- [ ] More than 5 tracks (scrollable track list)
- [ ] Track panning (left/right stereo positioning)
- [ ] Track effects (reverb, EQ) for preview only
- [ ] Export multi-track stems (separate files per track)

---

**End of Assembly Plan**

This is a living document. Update as requirements evolve and features are implemented.
