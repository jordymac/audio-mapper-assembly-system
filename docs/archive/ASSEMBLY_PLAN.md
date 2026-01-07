# Audio Assembly Plan

**Last Updated**: 2025-12-30

This document defines the **automatic assembly workflow**, multi-track visualization, and UI improvements for real-time audio preview with video in the main window.

**Key Concepts:**
- **Automatic Placement** - Audio waveforms appear in tracks as soon as generated
- **Real-Time Updates** - Move markers, waveforms follow instantly (no re-assembly)
- **Dual Export Format** - Individual track files + 5-channel consolidated WAV

---

## Table of Contents
1. [Overview](#overview)
2. [Current UI Issues](#current-ui-issues)
3. [Proposed Multi-Track Layout](#proposed-multi-track-layout)
4. [Workflow: Gen → Placement → Review → Export](#workflow-gen--placement--review--export)
5. [Track Assignment Logic](#track-assignment-logic)
6. [Export Algorithm](#export-algorithm)
7. [Implementation Plan](#implementation-plan)

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

## Workflow: Gen → Placement → Review → Export

### Automatic Assembly Flow

```
1. Create Marker at Specific Time
   - Click marker type button ([+SFX], [+Music], [+Voice])
   - Marker appears at current timeline position
   - Edit prompt data in popup editor
   ↓
2. Generate Audio for Marker
   - Click generate button on marker
   - API call to ElevenLabs (or other service)
   - Audio file saved to generated_audio/
   ↓
3. Automatic Placement in Track
   - Waveform immediately appears in correct track
   - Music marker → Channels 1-2 (Stereo track)
   - SFX marker → Channel 3 or 4 (distributed evenly)
   - Voice marker → Channel 5 (Mono track)
   - Visual feedback: waveform drawn at marker's timestamp
   ↓
4. Repeat for All Markers
   - Each generation adds waveform to track
   - See audio building up across all tracks in real-time
   - No manual assembly or "refresh" needed
   ↓
5. Edit and Adjust (Real-Time Updates)
   - Move marker → Waveform moves with it automatically
   - Edit marker prompt → Can regenerate, waveform updates in place
   - Delete marker → Waveform removed from track
   - All changes reflected immediately in track display
   ↓
6. Review with Video Playback
   - Press Play → Video plays with all generated audio
   - All tracks mixed in real-time during playback
   - Audio perfectly synced to video timeline
   - Adjust marker positions as needed, playback stays in sync
   ↓
7. Export (Mixed Tracks + Multi-Channel)
   - Click [📦 Export] → Opens export dialog
   - Creates mixed track files with asset naming:
     - MUS_00001_[description].wav (all music markers mixed)
     - SFX_00001_[description].wav (SFX Ch 3 markers mixed)
     - SFX_00002_[description].wav (SFX Ch 4 markers mixed)
     - VOX_00001_[description].wav (all voice markers mixed)
   - Creates 5-channel consolidated WAV (all tracks in one file)
   - Writes metadata JSON with track assignments and filenames
   - Asset IDs auto-increment, descriptions from marker names/prompts
```

### Key Principles

**Automatic Placement:**
- ✅ Waveforms are **views** of the generated audio files
- ✅ Moving a marker = updating visual position (audio file unchanged)
- ✅ No "assembly" or "re-assembly" buttons - it's always assembled
- ✅ Tracks always show current state of all generated audio

**Real-Time Feedback:**
- ✅ Generate audio → See it immediately in track
- ✅ Move marker → Waveform follows in real-time
- ✅ Delete marker → Waveform disappears
- ✅ Regenerate → Waveform updates in place

**Export Creates Two Formats:**
- ✅ **Mixed track files** - Separate WAVs with asset naming (MUS_00001, SFX_00001, etc.)
  - Music: All music markers mixed to stereo track
  - SFX: Two mono tracks (Ch 3 and Ch 4 markers separated)
  - Voice: All voice markers mixed to mono track
- ✅ **Multi-channel consolidated WAV** - Single 5-channel file (Ch 1-2: Music, 3-5: SFX/Voice)
- ✅ **Metadata JSON** - Track filenames, assignments, marker data, timestamps
- ✅ Asset IDs auto-increment, descriptions from marker names/prompts

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

## Export Algorithm

### Export Process (Dual Output)

**When Export Button is Clicked:**

```python
def export_tracks():
    """Export both individual track files AND multi-channel consolidated WAV"""

    # 1. Group markers by track assignment
    music_markers = [m for m in markers if m.type == "music"]
    sfx_ch3 = [m for m in markers if m.type == "sfx"][::2]   # Even indices
    sfx_ch4 = [m for m in markers if m.type == "sfx"][1::2]  # Odd indices
    voice_markers = [m for m in markers if m.type == "voice"]

    # 2. Create output directory structure
    output_dir = f"output/{template_id}/"
    os.makedirs(output_dir, exist_ok=True)

    # 3. Get next available asset IDs
    next_ids = get_next_asset_ids(output_dir)

    # 4. Generate individual track files with asset naming
    track_files = {}

    # Music: Stereo (Channels 1-2)
    music_track = mix_markers_to_track(music_markers, stereo=True)
    music_desc = generate_track_description(music_markers, "Music_Track")
    music_filename = f"MUS_{next_ids['music']:05d}_{music_desc}.wav"
    music_file = os.path.join(output_dir, music_filename)
    music_track.export(music_file, format="wav")
    track_files["channels_1_2"] = music_filename

    # SFX Channel 3: Mono
    sfx1_track = mix_markers_to_track(sfx_ch3, stereo=False)
    sfx1_desc = generate_track_description(sfx_ch3, "SFX_Ch3")
    sfx1_filename = f"SFX_{next_ids['sfx']:05d}_{sfx1_desc}.wav"
    sfx1_file = os.path.join(output_dir, sfx1_filename)
    sfx1_track.export(sfx1_file, format="wav")
    track_files["channel_3"] = sfx1_filename
    next_ids['sfx'] += 1  # Increment for next SFX track

    # SFX Channel 4: Mono
    sfx2_track = mix_markers_to_track(sfx_ch4, stereo=False)
    sfx2_desc = generate_track_description(sfx_ch4, "SFX_Ch4")
    sfx2_filename = f"SFX_{next_ids['sfx']:05d}_{sfx2_desc}.wav"
    sfx2_file = os.path.join(output_dir, sfx2_filename)
    sfx2_track.export(sfx2_file, format="wav")
    track_files["channel_4"] = sfx2_filename
    next_ids['sfx'] += 1  # Increment for next SFX track

    # Voice Channel 5: Mono
    voice_track = mix_markers_to_track(voice_markers, stereo=False)
    voice_desc = generate_track_description(voice_markers, "Voice_Track")
    voice_filename = f"VOX_{next_ids['voice']:05d}_{voice_desc}.wav"
    voice_file = os.path.join(output_dir, voice_filename)
    voice_track.export(voice_file, format="wav")
    track_files["channel_5"] = voice_filename

    # 5. Create 5-channel consolidated WAV
    multichannel_filename = f"{template_id}_5ch.wav"
    multichannel_file = os.path.join(output_dir, multichannel_filename)
    save_multichannel_wav(
        multichannel_file,
        channels=[music_track, sfx1_track, sfx2_track, voice_track]
    )

    # 6. Write metadata JSON
    metadata = {
        "template_id": template_id,
        "duration_ms": video_duration_ms,
        "export_date": datetime.now().isoformat(),
        "individual_tracks": track_files,
        "multichannel_file": multichannel_filename,
        "channel_layout": "5.0 (Music L/R, SFX1, SFX2, Voice)",
        "markers": markers  # Full marker data with timestamps
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Exported to {output_dir}")
    print(f"  - {music_filename}")
    print(f"  - {sfx1_filename}")
    print(f"  - {sfx2_filename}")
    print(f"  - {voice_filename}")
    print(f"  - {multichannel_filename}")
    print(f"  - metadata.json")


def get_next_asset_ids(output_dir):
    """Find highest existing asset IDs and return next available IDs"""
    import re
    import glob

    # Check existing files in output directory
    existing_files = glob.glob(os.path.join(output_dir, "*.wav"))

    # Track highest ID for each type
    max_ids = {'music': 0, 'sfx': 0, 'voice': 0}

    for filepath in existing_files:
        filename = os.path.basename(filepath)

        # Match MUS_00001, SFX_00002, VOX_00003 patterns
        mus_match = re.match(r'MUS_(\d+)_', filename)
        sfx_match = re.match(r'SFX_(\d+)_', filename)
        vox_match = re.match(r'VOX_(\d+)_', filename)

        if mus_match:
            max_ids['music'] = max(max_ids['music'], int(mus_match.group(1)))
        elif sfx_match:
            max_ids['sfx'] = max(max_ids['sfx'], int(sfx_match.group(1)))
        elif vox_match:
            max_ids['voice'] = max(max_ids['voice'], int(vox_match.group(1)))

    # Return next available IDs
    return {
        'music': max_ids['music'] + 1,
        'sfx': max_ids['sfx'] + 1,
        'voice': max_ids['voice'] + 1
    }


def generate_track_description(markers, default="Track"):
    """Generate descriptive filename suffix from marker data"""
    if not markers:
        return default

    # Try to get description from first marker's name
    first_marker = markers[0]

    if first_marker.get('name'):
        # Use marker name, sanitize for filename
        desc = first_marker['name']
        desc = desc.replace(' ', '_')
        desc = re.sub(r'[^\w\-_]', '', desc)  # Remove special chars
        return desc[:50]  # Limit length

    # Fallback: try to extract from prompt_data
    prompt_data = first_marker.get('prompt_data', {})

    if first_marker['type'] == 'music':
        styles = prompt_data.get('positiveGlobalStyles', [])
        if styles:
            desc = '_'.join(styles[:2])  # First 2 styles
            return desc.replace(' ', '_')[:50]

    elif first_marker['type'] == 'voice':
        voice_profile = prompt_data.get('voice_profile', '')
        if voice_profile:
            desc = voice_profile.replace(' ', '_')
            return desc[:50]

    elif first_marker['type'] == 'sfx':
        description = prompt_data.get('description', '')
        if description:
            desc = description.replace(' ', '_')
            return desc[:50]

    # Ultimate fallback
    return default


def mix_markers_to_track(markers, stereo=False):
    """Mix multiple markers into a single track file"""
    channels = 2 if stereo else 1
    track = AudioSegment.silent(duration=video_duration_ms).set_channels(channels)

    for marker in markers:
        if not marker.get('asset_file'):
            continue  # Skip markers without generated audio

        audio = AudioSegment.from_file(marker['asset_file'])

        # Convert to correct channel count
        if audio.channels != channels:
            audio = audio.set_channels(channels)

        # Overlay at marker's timestamp
        track = track.overlay(audio, position=marker['time_ms'])

    return track


def save_multichannel_wav(filename, channels):
    """Save multiple audio tracks into a single multi-channel WAV file"""
    import numpy as np
    from scipy.io import wavfile

    # Assume all channels have same duration and sample rate
    sample_rate = channels[0].frame_rate

    # Convert each AudioSegment to numpy array
    arrays = []
    for i, channel in enumerate(channels):
        # Music is stereo (2 channels), others are mono (1 channel)
        data = np.array(channel.get_array_of_samples())

        if channel.channels == 2:
            # Stereo: reshape to (samples, 2)
            data = data.reshape((-1, 2))
            arrays.append(data)
        else:
            # Mono: reshape to (samples, 1)
            data = data.reshape((-1, 1))
            arrays.append(data)

    # Concatenate along channel axis: (samples, 5)
    # Result: [Music_L, Music_R, SFX1, SFX2, Voice]
    multichannel = np.hstack(arrays)

    # Write to WAV file
    wavfile.write(filename, sample_rate, multichannel.astype(np.int16))
```

### Output Structure

```
output/DM01_Indoor_Routine/
├── MUS_00001_Electronic_Upbeat.wav      # All music markers mixed (stereo)
├── SFX_00001_UI_Clicks.wav              # SFX Channel 3 markers mixed (mono)
├── SFX_00002_Whooshes.wav               # SFX Channel 4 markers mixed (mono)
├── VOX_00001_Female_Narration.wav       # All voice markers mixed (mono)
├── DM01_5ch.wav                         # 5-channel consolidated WAV
└── metadata.json                        # Track assignments, marker data
```

**Naming Convention:**
- `MUS_00001_[description].wav` - Music track (stereo)
- `SFX_00001_[description].wav` - SFX track 1 (mono)
- `SFX_00002_[description].wav` - SFX track 2 (mono)
- `VOX_00001_[description].wav` - Voice track (mono)
- `{template_id}_5ch.wav` - Multi-channel file

**Description Auto-Generation:**
- Uses first marker's `name` field if available
- Falls back to prompt_data content (styles, voice_profile, description)
- Sanitized for filename safety (no special chars, max 50 chars)
- Asset IDs auto-increment based on existing files in output directory

---

## Implementation Plan

### Phase 1: UI Restructure
- [ ] Move "Add Marker" buttons to bottom (compact layout)
- [ ] Reduce button sizes: `[+SFX] [+Music] [+Voice]`
- [ ] Create multi-track waveform display area (5 rows)
- [ ] Add track labels (Track 1, Track 2, etc.)
- [ ] Add volume sliders per track

### Phase 2: Assembly Logic
- [ ] Implement track assignment algorithm
  - Auto-assign music → Tracks 1-2
  - Auto-assign SFX → Tracks 3-4
  - Auto-assign voice → Track 5
- [ ] Generate per-track audio files (temporary)
- [ ] Mix all tracks into single assembled WAV
- [ ] Save to temp directory for preview

### Phase 3: Waveform Integration
- [x] Generate waveform for each track ✓ **COMPLETED 2025-12-30**
- [x] Display in compact rows (~40-50px each) ✓ **COMPLETED 2025-12-30**
- [x] Synchronize all waveforms with main timeline ✓ **COMPLETED 2025-12-30**
- [x] **Automatic waveform updates after generation** ✓ **COMPLETED 2025-12-30**
  - Waveforms automatically appear in tracks after marker audio is generated
  - No manual "Assemble" button needed
  - Real-time updates for both single and batch generation
- [ ] Add playhead indicator across all tracks
- [x] Show marker positions on waveforms (vertical bars) ✓ **COMPLETED 2025-12-30**



### Phase 5: Export & Polish
- [x] Export functionality (dual output) ✓ **COMPLETED 2025-12-31**
  - Individual track files with asset naming (MUS_00001_[desc].wav, SFX_00001_[desc].wav, etc.)
  - Multi-channel 5ch WAV (using numpy/scipy)
  - Metadata JSON with track assignments and marker data
  - Progress indicator during export
  - Auto-incrementing asset IDs based on existing files
  - Descriptive filenames from marker names and prompt data
- [ ] Color-coding per track type
- [ ] Track overflow warnings
- [ ] Error handling (missing audio files)
- [ ] Keyboard shortcuts (Space=Play/Pause, etc.)
- [ ] Auto-save project state

---

## Technical Notes

### File Management

**Generated Audio Files** (During Development):
- `generated_audio/music/MUS_00001.mp3` - Individual music clips
- `generated_audio/sfx/SFX_00001.mp3` - Individual SFX clips
- `generated_audio/voice/VOX_00001.mp3` - Individual voice clips
- These files persist and are NOT deleted when markers are removed

**Waveform Display** (In-Memory Only):
- Waveforms are generated from audio files on-demand
- Stored in memory as display data (not saved to disk)
- Regenerated when marker is moved or audio is regenerated
- No temporary WAV files needed for preview

**Final Export Files** (Dual Output):
- `output/DM01_Indoor_Routine/MUS_00001_Electronic_Upbeat.wav` - All music markers mixed (stereo)
- `output/DM01_Indoor_Routine/SFX_00001_UI_Clicks.wav` - SFX assigned to Channel 3 (mono)
- `output/DM01_Indoor_Routine/SFX_00002_Whooshes.wav` - SFX assigned to Channel 4 (mono)
- `output/DM01_Indoor_Routine/VOX_00001_Female_Narration.wav` - All voice markers mixed (mono)
- `output/DM01_Indoor_Routine/DM01_5ch.wav` - **5-channel consolidated WAV**
  - Ch 1-2: Music Stereo (L/R)
  - Ch 3: SFX 1 Mono
  - Ch 4: SFX 2 Mono
  - Ch 5: Voice Mono
- `output/DM01_Indoor_Routine/metadata.json` - Track assignments and marker data

**Asset Naming:**
- Follows same convention as generated assets: `TYPE_00001_Description.wav`
- Auto-increments based on existing files in output directory
- Description auto-generated from marker name or prompt data

**Cleanup**:
- No temporary files to clean up (waveforms are in-memory only)
- Generated audio files persist for re-use across sessions
- Only clean up generated_audio/ manually if needed

### Dependencies

**Required Python Packages**:
- `pydub` - Audio manipulation and mixing
- `numpy` - Array operations for multi-channel WAV
- `scipy` - WAV file writing (`scipy.io.wavfile`)
- `python-vlc` - Video playback (existing)
- `pillow` - Image handling (existing)

**Installation**:
```bash
pip install pydub numpy scipy python-vlc pillow
```

**System Requirements**:
- FFmpeg (for pydub audio processing)
- VLC Media Player (for python-vlc)

### Performance Considerations

**Waveform Generation**:
- Cache waveform data in memory (only regenerate if audio changes)

**Real-Time Playback Mixing**:
- Pre-mix audio when Play button is pressed (one-time operation)
- Cache mixed result until markers change or volume sliders adjust
- Use pygame mixer for audio playback with volume control
- Invalidate cache when:
  - Marker is moved, added, or deleted
  - Audio is regenerated for a marker
  - Volume slider is adjusted

**Lazy Loading**:
- Only generate waveforms for visible tracks
- Load audio files on-demand when needed for playback
- Don't load all audio files on project open

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
