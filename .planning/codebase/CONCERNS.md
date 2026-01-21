# Codebase Concerns

**Analysis Date:** 2026-01-22

## Tech Debt

### 1. Bare Exception Handlers Masking Issues
- **Issue:** Multiple locations use bare `except:` or catch generic `Exception` without proper error handling/logging
- **Files:**
  - `services/audio_service.py:137-138` - bare except with pass
  - `services/assembly_service.py:815-816` - bare except handling duration extraction
  - `ui/export/export_center_window.py:333-334, 692, 712, 833-834` - multiple bare excepts
  - `ui/editors/music_editor.py:611` - bare except
  - `config/color_scheme.py:25` - bare except
- **Impact:** Errors silently fail, making debugging difficult. Invalid audio metadata (zero duration) is silently applied instead of flagged. Silent failures in UI operations prevent users from understanding what went wrong.
- **Fix approach:** Replace bare excepts with specific exception types and proper logging. For example, in `assembly_service.py:815`, catch `ffmpeg.Error` specifically and log a warning rather than silently using 0 duration.

### 2. Debug Print Statements in Production Code
- **Issue:** 841 print() calls scattered across codebase for debugging
- **Files:**
  - `services/audio_service.py:16 occurrences`
  - `services/assembly_service.py:50 occurrences`
  - `services/elevenlabs_api.py:87 occurrences` - extensive debug output
  - `audio_mapper.py:42 occurrences`
  - Many test files and UI components
- **Impact:** Clutters stdout/logs, makes debugging harder to find real issues, unprofessional output to users
- **Fix approach:** Replace print() with proper logging module. Configure log levels (DEBUG, INFO, WARNING) and route to file + console with appropriate filtering.

### 3. Incomplete Migration to New Format
- **Issue:** Code handles both old (prompt as string) and new (prompt_data) marker formats in multiple places
- **Files:**
  - `managers/version_manager.py:28-85` - format migration
  - `controllers/file_handler.py:114-168` - duplicate format migration
  - `services/assembly_service.py:60-70` - handles both dict and Marker objects
  - `managers/marker_manager.py` - compatibility handling
- **Impact:** Complexity in marker handling, potential format inconsistencies, makes code harder to maintain
- **Fix approach:** Complete full migration of all stored data to new format, remove backward compatibility code paths.

### 4. Duplicate Code - Format Migration Logic
- **Issue:** `migrate_marker_to_new_format` is defined identically in two places
- **Files:**
  - `managers/version_manager.py:28-85`
  - `controllers/file_handler.py:114-168`
- **Impact:** Risk of divergent behavior if one is updated without the other
- **Fix approach:** Keep single source of truth in one location, import from other.

### 5. Insufficient Error Context
- **Issue:** Many generic error messages that don't provide actionable feedback
- **Files:**
  - `services/elevenlabs_api.py:89-94` - "SFX generation failed" without specific reason context
  - `audio_mapper.py:1816` - generic exception handling without context
  - `controllers/file_handler.py:66` - broad exception message
- **Impact:** Users can't understand what went wrong or how to fix it
- **Fix approach:** Add context to error messages (what operation, what inputs, what specific failure).

## Known Bugs

### 1. Silent Duration Calculation Failure
- **Symptoms:** Video/audio duration reported as 0 when mediainfo fails to read file
- **Files:** `services/assembly_service.py:815-816`, `ui/export/export_center_window.py:333-334`
- **Trigger:** When ffmpeg/mediainfo can't extract duration from audio file
- **Current behavior:** Falls back to 0 duration silently instead of alerting user
- **Workaround:** Re-export file in standard format, manually set duration
- **Fix approach:** Log warning, return error instead of 0, notify user in UI

### 2. Type Safety Issue - Marker Dict vs Object
- **Symptoms:** Code fails intermittently depending on whether marker is dict or object
- **Files:**
  - `services/assembly_service.py:60-70` - uses `get()` and attribute access interchangeably
  - `services/assembly_playback_service.py:103-115` - similar pattern
  - `services/audio_service.py:255-266` - assumes dict structure
- **Trigger:** When migrating between data formats or mixing sources
- **Workaround:** Ensure all markers are same type before operations
- **Fix approach:** Standardize on single representation (Marker objects), convert all inputs

### 3. Unhandled pygame.mixer.Sound Loading Failures
- **Symptoms:** Audio playback silently skips when marker audio file is missing or corrupt
- **Files:** `services/assembly_playback_service.py:81-87`
- **Trigger:** When asset files are moved, deleted, or corrupted
- **Current behavior:** Catches exception but continues without notifying user
- **Workaround:** Ensure all asset files exist before playback
- **Fix approach:** Return error status, highlight broken markers in UI

## Security Considerations

### 1. API Key Exposed in Code
- **Risk:** ELEVENLABS_API_KEY is loaded at module import time without proper secret management
- **Files:** `services/elevenlabs_api.py:14-21`
- **Current mitigation:** Loaded from .env.local file (not in git), Python environment
- **Recommendations:**
  - Use secrets management system (AWS Secrets Manager, HashiCorp Vault)
  - Implement key rotation strategy
  - Add audit logging for all API calls
  - Consider API rate limiting and usage monitoring

### 2. File Path Traversal Not Validated
- **Risk:** User-provided paths could potentially escape intended directories
- **Files:** `controllers/file_handler.py:39, 104`, `managers/waveform_manager.py:84`
- **Current mitigation:** Relative paths only, but no explicit validation
- **Recommendations:**
  - Validate file paths against allowed directories using `pathlib.resolve()`
  - Restrict file access to specific directories

### 3. No Input Validation on ElevenLabs Prompts
- **Risk:** Arbitrary text sent to external API without sanitization
- **Files:** `services/elevenlabs_api.py:56-60, 139-143, 293-301`
- **Current mitigation:** None visible
- **Recommendations:**
  - Validate prompt length and content
  - Add rate limiting to prevent abuse
  - Log all generated content for audit trail

## Performance Bottlenecks

### 1. Waveform Extraction Not Cached
- **Problem:** Waveform data recalculated from video on every load
- **Files:** `managers/waveform_manager.py:70-111`
- **Cause:** No disk caching of extracted waveform data
- **Impact:** Long video files cause UI freeze during waveform extraction
- **Improvement path:**
  - Cache waveform data to disk (pickle or JSON)
  - Check cache validity before re-extracting
  - Implement background extraction for large files

### 2. Large Audio Arrays in Memory
- **Problem:** Entire waveform data held in memory as numpy array
- **Files:** `managers/waveform_manager.py:93-105`
- **Cause:** No chunking or streaming approach
- **Impact:** High memory usage for long videos, potential crashes on 4K+ content
- **Improvement path:**
  - Implement chunked waveform processing
  - Use mmap for large files
  - Downsample more aggressively for display (current 22050 Hz could go lower)

### 3. No Connection Pooling for ElevenLabs API
- **Problem:** New HTTP connection for each generation request
- **Files:** `services/elevenlabs_api.py:16-21`
- **Cause:** Client initialized per request or at module level without pooling
- **Impact:** High latency for batch operations, connection overhead
- **Improvement path:**
  - Implement connection pooling in elevenlabs client
  - Consider request batching if API supports it

### 4. O(n) Marker Lookups
- **Problem:** Finding markers by index or property requires linear scan
- **Files:** Multiple files accessing `self.markers[index]` or filtering by property
- **Cause:** Using list instead of indexed structure
- **Impact:** Slow for large marker counts (100+)
- **Improvement path:**
  - Build index maps (time_ms -> marker, id -> marker)
  - Use dict for O(1) lookups

## Fragile Areas

### 1. Version Management System
- **Files:** `managers/version_manager.py`, `core/models.py:250-310`
- **Why fragile:** Complex versioning logic with implicit assumptions about version structure
- **Fragile operations:**
  - Version number increment logic (assumes sequential)
  - Marker version list mutation
  - Current version tracking (can be out of sync with actual files)
- **Safe modification:**
  - Always use `MarkerVersionManager` methods rather than direct mutation
  - Add invariant checks (version count, version numbers sequential, current_version valid)
  - Test migrations thoroughly

### 2. Assembly Service Track Assignment
- **Files:** `services/assembly_service.py:45-110`
- **Why fragile:** Complex track assignment algorithm with alternating SFX distribution
- **Fragile operations:**
  - SFX alternation to two tracks depends on sort order
  - Modifying track strategy requires changes in multiple places
  - No validation that assignment matches expected output
- **Safe modification:**
  - Add unit tests for each track assignment scenario
  - Document expected output format clearly
  - Add assertions after assignment

### 3. UI State Synchronization
- **Files:** `audio_mapper.py`, `managers/marker_selection_manager.py`
- **Why fragile:** Multiple managers track overlapping state (selected marker, edited marker, etc)
- **Fragile operations:**
  - Clearing selection across multiple managers
  - Updating UI after marker changes
  - Keyboard shortcuts while dialogs open
- **Safe modification:**
  - Centralize state in single source (MarkerRepository already exists)
  - Add state validation checks
  - Test cross-manager consistency

### 4. Pygame Mixer State
- **Files:** `services/assembly_playback_service.py:29-55`
- **Why fragile:** Pygame mixer is global singleton with implicit state
- **Fragile operations:**
  - Multiple init() calls
  - Channel allocation for simultaneous playback
  - Proper cleanup on shutdown
- **Safe modification:**
  - Wrap pygame.mixer in dedicated manager
  - Ensure cleanup in destructor
  - Test channel exhaustion scenarios

## Test Coverage Gaps

### 1. Export Functionality Not Tested
- **What's not tested:** Complete export workflow (metadata editing, file generation, template export)
- **Files:** `ui/export/export_center_window.py` (839 lines, 0 tests), `controllers/file_handler.py` partial coverage
- **Risk:** Export failures break critical user workflow
- **Priority:** HIGH - Core feature with no coverage

### 2. ElevenLabs Integration Tests Minimal
- **What's not tested:** Voice generation with custom Voice Design API, batch generation completeness
- **Files:** `services/elevenlabs_api.py` (403 lines), only `test_elevenlabs_integration.py` (59 lines)
- **Risk:** API failures or changes break silently
- **Priority:** HIGH - Depends on external API

### 3. Video Player Controller
- **What's not tested:** Seeking, duration calculation, audio extraction, framerate handling
- **Files:** `controllers/video_player_controller.py` (374 lines, 0 tests)
- **Risk:** Video playback breaks unexpectedly
- **Priority:** MEDIUM - Core feature

### 4. Marker Manager Operations
- **What's not tested:** Marker editing, deletion during playback, concurrent operations
- **Files:** `managers/marker_manager.py` (291 lines, limited test coverage)
- **Risk:** Data corruption during concurrent operations
- **Priority:** MEDIUM - Affects data integrity

### 5. Music Editor Complex Logic
- **What's not tested:** Section management, style blending, complex prompt operations
- **Files:** `ui/editors/music_editor.py` (648 lines, no dedicated tests)
- **Risk:** Music generation silently produces incorrect output
- **Priority:** MEDIUM - Complex business logic

### 6. Assembly Playback Triggering
- **What's not tested:** Marker trigger detection, simultaneous playback, edge cases (rapid seeking, looping)
- **Files:** `services/assembly_playback_service.py` (239 lines, no tests)
- **Risk:** Playback bugs undetected, difficult to reproduce
- **Priority:** MEDIUM - Core feature

### 7. Threading and Concurrency
- **What's not tested:** Background audio generation thread safety, UI update thread safety
- **Files:** `services/audio_service.py:233-238, 663` - daemon threads without proper synchronization
- **Risk:** Race conditions, data corruption, crashes under load
- **Priority:** MEDIUM - Affects reliability under stress

## Scaling Limits

### 1. Memory Usage with Large Videos
- **Current capacity:** Tested with videos up to ~10 minutes
- **Limit:** Waveform extraction becomes very slow (>10 seconds) and memory-heavy for 30+ minute videos
- **Scaling path:**
  - Implement chunked waveform processing
  - Add progress UI for waveform extraction
  - Cache extracted waveforms

### 2. Marker List Performance
- **Current capacity:** ~50 markers without noticeable slowdown
- **Limit:** >200 markers causes UI lag in marker list updates and drawing
- **Scaling path:**
  - Virtualize marker list (only render visible items)
  - Index marker lookups with hash map
  - Batch UI updates

### 3. ElevenLabs API Rate Limits
- **Current capacity:** ~10-15 concurrent generations before API throttling
- **Limit:** API has rate limits (typically 3000 chars/day for free tier)
- **Scaling path:**
  - Implement request queuing
  - Add rate limit tracking
  - Cache generated audio to reduce API calls

### 4. Temporary File Cleanup
- **Current capacity:** Assembly temp files accumulate unbounded
- **Limit:** Disk space exhaustion after prolonged use
- **Scaling path:**
  - Implement automatic temp file cleanup
  - Add disk space monitoring
  - Warn user when approaching disk limits

## Dependencies at Risk

### 1. moviepy - Maintenance Risk
- **Risk:** moviepy is not actively maintained, ffmpeg integration can be fragile
- **Impact:** Breaking changes in ffmpeg, video format support issues
- **Migration plan:** Consider moving to `opencv-python` (more actively maintained) or `ffmpeg-python` for video operations

### 2. pygame - Singleton State Risk
- **Risk:** pygame.mixer is global state that's difficult to properly clean up
- **Impact:** Resource leaks if mixer not properly initialized/destroyed
- **Migration plan:** Consider alternatives like `pydub` (already used) or `sounddevice` for audio playback

### 3. ElevenLabs SDK - API Surface Risk
- **Risk:** Depends on external SDK that could change API
- **Impact:** Code breaks with SDK updates
- **Migration plan:**
  - Implement own API wrapper to isolate SDK changes
  - Add API version pinning in requirements
  - Have fallback to direct HTTP API

### 4. dotenv - Load Order Dependency
- **Risk:** .env.local must exist and be in correct directory
- **Impact:** Code fails at import time with cryptic error if .env missing
- **Migration plan:**
  - Move env check to runtime
  - Provide better error messages
  - Support config file fallback

## Missing Critical Features

### 1. Project Save/Load
- **Problem:** No way to save project state between sessions
- **Blocks:** Users must re-create everything on each startup
- **Impact:** Major UX pain point

### 2. Undo/Redo for Assembly Operations
- **Problem:** Assembly operations not in history system
- **Blocks:** Users can't undo assembly or track assignment changes
- **Impact:** Potential data loss if user makes wrong track assignment

### 3. Playback Audio Synchronization
- **Problem:** Assembly playback doesn't properly sync with video playhead
- **Blocks:** Users can't preview what assembly will sound like in sync with video
- **Impact:** Exported assembly may not align with video

### 4. Audio File Validation
- **Problem:** No validation that generated audio files exist or are valid before export
- **Blocks:** Broken exports with missing files
- **Impact:** Users discover issues only after export

### 5. Conflict Resolution for Simultaneous Markers
- **Problem:** No handling of overlapping marker times or simultaneous marker generation
- **Blocks:** Can't properly handle multiple markers at same timestamp
- **Impact:** Unexpected behavior with precisely-timed audio

---

*Concerns audit: 2026-01-22*
