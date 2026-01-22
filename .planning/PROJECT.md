# Audio Mapper Assembly System — Bug Fixes & Security

## What This Is

A bug fix and security hardening milestone for the Audio Mapper Assembly System. The app maps audio markers (SFX, voice, music) to video timelines and generates audio via ElevenLabs. This milestone addresses 6 bugs causing workflow friction and silent failures, plus 3 security hygiene items.

## Core Value

**Bugs get surfaced, not hidden.** When something fails, the user knows what happened and what to do about it. Silent failures become visible errors with actionable feedback.

## Requirements

### Validated

Existing functionality that works and should not regress:

- ✓ Create/edit/delete markers on video timeline — existing
- ✓ Generate SFX, voice, and music via ElevenLabs API — existing
- ✓ Multi-track audio assembly with 5 channels — existing
- ✓ Version management for generated audio — existing
- ✓ Export templates and assembled audio — existing
- ✓ Video playback with waveform visualization — existing
- ✓ Keyboard shortcuts for marker operations — existing

### Active

Bug fixes and security items for this milestone:

**Bugs — User-facing:**
- [ ] Waveform displays correctly on SFX regeneration (no blue rectangle)
- [ ] New marker creation opens editor for the new marker, not previous
- [ ] Playback triggers all markers regardless of start position

**Bugs — Silent failures:**
- [ ] Duration calculation failure shows error instead of returning 0
- [ ] Marker dict/object handling is consistent (no type confusion crashes)
- [ ] Missing audio files are reported to user, not silently skipped

**Security hygiene:**
- [ ] Missing .env.local gives clear error message with instructions
- [ ] File paths validated against allowed directories
- [ ] ElevenLabs prompts validated (length limits, basic sanitization)

### Out of Scope

Deferred to future milestone — documented in CONCERNS.md:

- Tech debt cleanup (841 print statements, bare excepts) — not causing user pain
- Performance optimizations (waveform caching, marker indexing) — current scale is fine
- Test coverage gaps — address after bugs are fixed
- Missing features (project save/load, undo for assembly) — separate milestone
- Dependency migrations (moviepy, pygame) — working fine currently

## Context

**Codebase state:** Mapped in `.planning/codebase/`. Key areas:
- `managers/waveform_manager.py` — waveform extraction and display
- `managers/marker_selection_manager.py` — tracks selected marker
- `services/assembly_playback_service.py` — marker triggering during playback
- `services/assembly_service.py` — duration calculation, marker handling
- `services/elevenlabs_api.py` — API integration, prompt handling
- `controllers/file_handler.py` — file path handling

**Bug context:**
- Waveform bug happens on regeneration, not first generation — likely state not clearing
- Editor bug is selection state not syncing when new marker created
- Playback bug is trigger logic only looking forward, not handling markers passed

## Constraints

- **No new dependencies**: Fix within existing stack
- **No breaking changes**: Existing templates and workflows must continue working
- **Desktop app**: Security is hygiene, not critical (single user, local machine)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fix bugs before tech debt | Bugs cause user pain, tech debt is internal | — Pending |
| Security as hygiene, not urgent | Single-user desktop app, not distributed | — Pending |
| Keep existing marker format | Migration complexity not worth it for this milestone | — Pending |

---
*Last updated: 2026-01-22 after initialization*
