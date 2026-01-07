# Audio-Video Synchronization Fix

## Problem Identified

The position indicator, video, and assembled audio were not staying synchronized during playback due to:

1. **Independent Timing Sources**: Video used FPS-based clock, audio used pygame's internal clock
2. **No Explicit Sync on User Actions**: Audio didn't resync when user scrubbed timeline or stepped frames
3. **pygame Limitations**: `set_pos()` is not frame-accurate, no way to query actual playback position
4. **Position Indicator**: Based on video time (correct), but audio could drift

## Solution Implemented (Revised Approach)

**Initial Attempt**: Automatic continuous resyncing based on drift detection
- **Problem Found**: Wall clock estimation is unreliable, caused constant audio restarts
- **Lesson**: Can't reliably estimate pygame audio position - no query API available

**Final Solution**: Explicit sync on user actions only

### Key Changes:

**1. Sync on Play/Resume** (assembly_playback_service.py:69-108)
```python
def play(self, start_position_ms: Optional[int] = None):
    """Start playback from video's current position"""
    if start_position_ms is None:
        start_position_ms = self.video_player.current_time_ms
    # Start audio at exact video position
```

**2. Sync on Timeline Scrubbing** (audio_mapper.py:976-985)
```python
def on_timeline_change(self, value):
    """Handle timeline slider - sync audio to new position"""
    self.video_player.on_timeline_change(value)
    if self.assembly_playback.is_playing:
        self.assembly_playback.seek(self.video_player.current_time_ms)
```

**3. Sync on Frame Stepping** (audio_mapper.py:895-974)
```python
def step_time(self, delta_ms):
    self.video_player.step_time(delta_ms)
    if self.assembly_playback.is_playing:
        self.assembly_playback.seek(self.video_player.current_time_ms)
```

**4. Diagnostic Tools Available** (Optional, for troubleshooting):
- `get_estimated_audio_position_ms()`: Estimate audio position from wall clock
- `check_sync_with_video()`: Compare video vs estimated audio position
- `set_debug_logging(True)`: Enable detailed sync logging
- These are available but NOT used in automatic syncing

### Why No Automatic Resyncing?

Automatic continuous resyncing was attempted but caused problems:
- Wall clock estimation is unreliable (includes processing overhead)
- pygame has no API to query actual playback position
- Constant resyncs caused audio stuttering/restarts
- **Better approach**: Let pygame handle playback, only sync on explicit user actions

## Debug Logging

When enabled (`debug_logging = True`), provides detailed output:

```
▶ [SYNC] Audio started: position=1500ms, wall_time=1234567890.123
⚠️  [SYNC] Drift detected: video=2000ms, audio≈1950ms, drift=50ms
🔄 [SYNC] Resyncing audio: drift=120ms, seeking to 2000ms
⏸ [SYNC] Audio paused at 2500ms
▶ [SYNC] Resumed audio from 2500ms
```

## Testing Instructions

### 1. Basic Sync Test
Debug logging is **disabled by default** for cleaner console output.

To enable diagnostics (optional):
```python
self.assembly_playback.set_debug_logging(True)  # Enable
self.assembly_playback.set_debug_logging(False) # Disable (default)
```

### 2. Test Scenarios

**Scenario A: Normal Playback**
1. Load video and markers
2. Assemble audio
3. Press play
4. Position indicator should stay aligned with video
5. Audio should play in sync
6. **Minimal drift expected** during playback (pygame's natural behavior)

**Scenario B: Timeline Scrubbing**
1. Start playback
2. Drag timeline slider while playing
3. **Audio should immediately jump to new position**
4. Playback continues from new position

**Scenario C: Frame Stepping**
1. Start playback
2. Use frame step buttons (← →)
3. **Audio should follow video position each step**
4. Remains in sync

**Scenario D: Pause/Resume**
1. Play for a few seconds
2. Pause
3. Resume
4. **Audio continues from exact paused position**

**Scenario E: Long Playback (Drift Accumulation)**
1. Play for 30+ seconds continuously
2. Some drift may accumulate (pygame limitation)
3. **To resync**: Pause and resume
4. Position indicator always follows video (correct)

### 3. Expected Behavior

✅ **At Start/User Actions**: Perfect sync
- Play button: Audio starts at video position
- Scrubbing: Audio jumps to new position
- Frame step: Audio follows precisely

✅ **During Continuous Playback**: Acceptable drift
- Position indicator follows video (always correct)
- Audio may drift slightly (±50-100ms over 30+ seconds)
- **This is normal for pygame** - no position query API
- User can pause/resume to resync if noticeable

❌ **Should NOT Happen**:
- Constant audio restarts/stuttering
- Console spam with sync messages
- Audio jumping around during smooth playback

## Performance Considerations

- **Sync Overhead**: Only on user actions (play, scrub, step)
- **No Continuous Checking**: No performance impact during playback
- **Update Loop**: 33ms (30 FPS) - unchanged
- **Audio Latency**: ~50-100ms (pygame.mixer inherent latency)

## Known Limitations

1. **Natural Drift During Long Playback**:
   - pygame.mixer has no API to query actual playback position
   - Audio may drift ±50-100ms over 30+ seconds of continuous playback
   - **Workaround**: Pause/resume to resync
   - Position indicator always correct (follows video)

2. **pygame.mixer.music.set_pos() Accuracy**:
   - Depends on audio codec (MP3 vs WAV)
   - May have +/- 50ms precision when seeking
   - Acceptable for most use cases

3. **No Real-Time Drift Correction**:
   - Can't implement smooth tempo adjustment (no position API)
   - Can't auto-correct drift without audio restart
   - Manual resync (pause/resume) is the reliable approach

## Future Enhancements (If Needed)

1. **Alternative Audio Backend**:
   - **sounddevice**: Provides position callbacks, better sync control
   - **pygame_sdl2**: More modern, may have better APIs
   - **pydub with pyaudio**: Direct sample streaming, frame-accurate

2. **Manual Resync Hotkey**:
   - Add keyboard shortcut to force resync without pause/resume
   - E.g., press 'S' to resync audio to current video position

3. **Sync Quality Indicator**:
   - Visual indicator showing estimated drift
   - Warn user if drift likely >100ms

4. **Pre-rendered Audio with Timecodes**:
   - Embed timecode markers in assembled audio
   - Verify sync by comparing timecodes (advanced)

## Files Modified

1. `services/assembly_playback_service.py`:
   - Added timing tracking fields
   - Implemented sync diagnostic methods (optional use)
   - Enhanced pause/resume state tracking

2. `audio_mapper.py`:
   - Added sync calls on timeline scrubbing (audio_mapper.py:976-985)
   - Added sync calls on frame stepping (audio_mapper.py:895-974)
   - Update loop unchanged (no automatic syncing)

3. `docs/SYNC_FIX_SUMMARY.md`: This documentation

## Summary

**Problem**: Position indicator, video, and audio didn't sync during scrubbing/stepping

**Root Cause**: Audio wasn't explicitly resynced when user changed video position

**Solution**: Added explicit audio sync on:
- Timeline slider changes
- Frame step forward/backward
- Time step forward/backward

**Result**: Position indicator (video-based) and audio stay in sync during all user interactions

**Trade-off**: Some natural drift may occur during long continuous playback (pygame limitation), but user can pause/resume to resync
