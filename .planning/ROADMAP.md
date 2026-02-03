# Roadmap: Audio Mapper Bug Fixes & Security

## Overview

This milestone addresses critical bugs that create user friction and silent failures in the Audio Mapper Assembly System. The work progresses from visible UI issues through hidden data problems to security hygiene. Four phases deliver observable fixes that make errors visible and actionable rather than silent.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: UI State & Visual Bugs** - Fix waveform display and marker selection state issues
- [x] **Phase 2: Playback & Audio Issues** - Fix marker triggering and missing audio handling
- [x] **Phase 3: Data Handling Failures** - Surface silent duration and type confusion errors
- [x] **Phase 4: Security Hygiene** - Validate environment setup, paths, and API inputs

## Phase Details

### Phase 1: UI State & Visual Bugs
**Goal**: User sees correct waveforms and edits correct markers
**Depends on**: Nothing (first phase)
**Requirements**: BUG-01, BUG-02
**Success Criteria** (what must be TRUE):
  1. User regenerates SFX and sees correct waveform without blue rectangle artifact
  2. User creates new marker and editor opens for that new marker, not previous marker
  3. Waveform state clears properly between regenerations
  4. Selection state syncs between marker creation and editor opening
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Fix waveform state clearing and marker selection sync
- [x] 01-02-PLAN.md — (gap closure) Diagnose and fix waveform blue rectangle artifact root cause

### Phase 2: Playback & Audio Issues
**Goal**: Playback triggers all markers and reports missing audio
**Depends on**: Phase 1
**Requirements**: BUG-03, BUG-06
**Success Criteria** (what must be TRUE):
  1. User starts playback from any position and all markers in range trigger correctly
  2. User plays assembly with missing audio file and sees error dialog identifying which marker failed
  3. Missing audio files no longer silently skip during playback
  4. Playback trigger logic handles markers before current playhead position
**Plans**: 1 plan

Plans:
- [x] 02-01: Type-specific playback (MUSIC vs SFX) and error surfacing

### Phase 3: Data Handling Failures
**Goal**: Silent failures become visible errors with actionable feedback
**Depends on**: Phase 2
**Requirements**: BUG-04, BUG-05
**Success Criteria** (what must be TRUE):
  1. User opens file with invalid duration and sees error dialog instead of 0 duration applied silently
  2. User performs marker operations and code handles dict/object consistently without crashes
  3. Duration calculation failures are logged with file path and error details
  4. Type confusion errors are eliminated across assembly, playback, and audio services
**Plans**: 1 plan

Plans:
- [x] 03-01-PLAN.md — Duration validation and marker normalization utilities

### Phase 4: Security Hygiene
**Goal**: Environment and inputs are validated with helpful error messages
**Depends on**: Phase 3
**Requirements**: SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):
  1. User starts app without .env.local and sees clear error message with setup instructions
  2. User attempts file operation outside allowed directories and operation is blocked with error
  3. User enters excessively long prompt and sees validation error before API call
  4. File path traversal attempts are detected and rejected
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Environment validation with clear error messages (SEC-01)
- [x] 04-02-PLAN.md — Path traversal protection and prompt length validation (SEC-02, SEC-03)
- [x] 04-03-PLAN.md — (gap closure) Fix tkinter import shadowing in main()

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. UI State & Visual Bugs | 2/2 | ✓ Complete | 2026-01-31 |
| 2. Playback & Audio Issues | 1/1 | ✓ Complete | 2026-02-02 |
| 3. Data Handling Failures | 1/1 | ✓ Complete | 2026-02-02 |
| 4. Security Hygiene | 3/3 | ✓ Complete | 2026-02-03 |

---
*Last updated: 2026-02-03*
