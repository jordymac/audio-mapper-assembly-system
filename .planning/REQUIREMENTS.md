# Requirements: Audio Mapper Bug Fixes & Security

**Defined:** 2026-01-22
**Core Value:** Bugs get surfaced, not hidden. Errors give actionable feedback.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### User-Facing Bugs

- [ ] **BUG-01**: Waveform displays correctly on SFX regeneration (no blue rectangle artifact)
- [ ] **BUG-02**: New marker creation opens editor for the new marker, not previous marker
- [ ] **BUG-03**: Playback triggers all markers regardless of playhead start position

### Silent Failures

- [ ] **BUG-04**: Duration calculation failure shows error instead of silently returning 0
- [ ] **BUG-05**: Marker dict/object handling is consistent throughout codebase (no type confusion)
- [ ] **BUG-06**: Missing audio files are reported to user, not silently skipped during playback

### Security Hygiene

- [ ] **SEC-01**: Missing .env.local gives clear error message with setup instructions
- [ ] **SEC-02**: File paths validated against allowed directories (prevent traversal)
- [ ] **SEC-03**: ElevenLabs prompts validated for length limits and basic sanitization

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Tech Debt

- **DEBT-01**: Replace 841 print() statements with proper logging module
- **DEBT-02**: Replace bare exception handlers with specific types
- **DEBT-03**: Complete marker format migration, remove backward compatibility
- **DEBT-04**: Consolidate duplicate migration code to single location

### Performance

- **PERF-01**: Cache waveform data to disk
- **PERF-02**: Index markers for O(1) lookups
- **PERF-03**: Implement connection pooling for ElevenLabs API

### Test Coverage

- **TEST-01**: Add tests for export functionality
- **TEST-02**: Add tests for video player controller
- **TEST-03**: Add tests for assembly playback triggering

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Project save/load | Separate feature milestone, not a bug fix |
| Undo/redo for assembly | Separate feature milestone |
| Dependency migrations (moviepy, pygame) | Working fine, no immediate need |
| UI refactoring | Not causing bugs, just internal quality |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUG-01 | Phase 1 | Pending |
| BUG-02 | Phase 1 | Pending |
| BUG-03 | Phase 2 | Pending |
| BUG-04 | Phase 3 | Pending |
| BUG-05 | Phase 3 | Pending |
| BUG-06 | Phase 2 | Pending |
| SEC-01 | Phase 4 | Pending |
| SEC-02 | Phase 4 | Pending |
| SEC-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-01-22 after roadmap creation*
