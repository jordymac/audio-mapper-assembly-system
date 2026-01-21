# Testing Patterns

**Analysis Date:** 2026-01-22

## Test Framework

**Runner:**
- pytest 7.4.0+ (configured in `pyproject.toml`)
- Config: `[tool.pytest.ini_options]` in `pyproject.toml`
  - `testpaths = ["tests"]` - test directory location
  - `python_files = "test_*.py"` - test file naming pattern
  - `python_functions = "test_*"` - test function naming pattern

**Assertion Library:**
- Built-in `assert` statements with descriptive messages
- No external assertion library used

**Run Commands:**
```bash
pytest tests/                    # Run all tests
pytest tests/ -v               # Run with verbose output
pytest tests/ --cov=.          # Run with coverage (pytest-cov)
pytest tests/test_models.py    # Run specific test file
python tests/test_models.py    # Run standalone (test-specific pattern)
```

## Test File Organization

**Location:**
- All tests in `/Users/jordymcintyre/audio-mapper-assembly-system/tests/` directory
- Co-located pattern: test files grouped in single `tests/` directory, not alongside source files

**Naming:**
- Test files: `test_*.py` pattern (e.g., `test_models.py`, `test_audio_playback.py`)
- Test functions: `test_*` pattern (e.g., `test_sfx_marker()`, `test_batch_operations()`)
- Integration tests named by feature: `test_elevenlabs_integration.py`, `test_auto_assembly.py`
- UI tests named by feature: `test_generation_button.py`, `test_enhanced_rows.py`

**Structure:**
```
tests/
├── test_audio_mapper.py           # Main GUI tests
├── test_audio_playback.py         # Audio playback functionality
├── test_models.py                 # Data model tests
├── test_file_handler.py           # File import/export tests
├── test_batch_operations.py       # Batch generation UI
├── test_auto_assembly.py          # Assembly functionality
├── test_elevenlabs_integration.py # API integration
├── test_version_management.py     # Version tracking
├── test_waveform_manager.py       # Waveform display
└── test_filmstrip_manager.py      # Video filmstrip
```

## Test Structure

**Suite Organization:**

Most tests follow a simple function-based structure without a test class framework:

```python
#!/usr/bin/env python3
"""Test description"""

def test_feature_name():
    """Test description for single feature"""
    # Arrange: Setup test data
    marker = create_marker(
        time_ms=5000,
        marker_type="sfx",
        name="Door Slam"
    )

    # Act: Execute code under test
    assert marker.time_ms == 5000
    assert marker.type == "sfx"

    # Print success feedback
    print("✓ Feature test passed")

if __name__ == "__main__":
    test_feature_name()
```

**Patterns:**
- No formal test classes; standalone test functions are preferred
- Setup implicit via function parameters or inline initialization
- No teardown; tests clean up via context managers or explicit cleanup
- Assertion pattern: `assert condition, "descriptive message"`

## Mocking

**Framework:** No mocking library in use (pytest-mock not installed)

**Patterns:**
- Real integration tests used instead of mocks for external services
- Example from `test_elevenlabs_integration.py`: actual API calls to ElevenLabs
- File system tests use `tempfile.NamedTemporaryFile()` for temp files
- Example from `test_file_handler.py`:
  ```python
  with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
      temp_path = f.name

  # Test operations on temp file
  FileHandler.export_to_json(temp_path, markers)
  success, data, error = FileHandler.import_from_json(temp_path)

  # Cleanup
  Path(temp_path).unlink(missing_ok=True)
  ```

**What to Mock:**
- No mocking library configured; avoid external API mocks
- For external services: provide real test credentials via `.env.local`
- Database: Not applicable (no database in this project)

**What NOT to Mock:**
- File I/O: Use real temp files with proper cleanup
- Model creation: Use real `create_marker()` and dataclass instantiation
- Repository operations: Test with real `MarkerRepository` instances

## Fixtures and Factories

**Test Data:**
- Factory pattern: `create_marker()` function in `core/models.py`
  ```python
  from core.models import create_marker

  # Creates marker with sensible defaults
  marker = create_marker(
      time_ms=5000,
      marker_type="sfx",
      name="Door Slam",
      asset_slot="sfx_0",
      asset_file="SFX_00000_v1.mp3"
  )
  ```
- Hardcoded test data within test functions (no fixture files)
- Example from `test_file_handler.py`:
  ```python
  markers = [
      {
          "time_ms": 0,
          "type": "music",
          "name": "Background Music",
          "prompt_data": {...},
          "asset_slot": "music_0",
          "asset_file": "MUS_00000_v1.mp3",
          ...
      }
  ]
  ```

**Location:**
- No centralized fixture file (conftest.py not used)
- Test data defined inline in each test function
- Factory functions imported from source modules: `from core.models import create_marker`

## Coverage

**Requirements:** No coverage requirements enforced (no threshold set in config)

**View Coverage:**
```bash
pytest tests/ --cov=. --cov-report=html    # Generate HTML coverage report
pytest tests/ --cov=. --cov-report=term    # Print coverage to terminal
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and methods
- Approach: Test data model creation, validation, serialization
- Example: `test_models.py` tests marker creation, copying, version management
- Location: `tests/test_models.py`, `tests/test_file_handler.py`

**Integration Tests:**
- Scope: Multiple components working together
- Approach: Test API integration, file I/O workflows, service operations
- Example: `test_elevenlabs_integration.py` tests full audio generation pipeline
- Example: `test_file_handler.py` tests export/import round-trip
- Location: `tests/test_elevenlabs_integration.py`, `tests/test_auto_assembly.py`

**E2E Tests:**
- Framework: Not used - no end-to-end test automation configured
- Approach: Manual testing with interactive GUI validation
- Instructions embedded in test output (e.g., in `test_audio_playback.py`):
  ```python
  print("\nTo test interactively:")
  print("  1. Run: python3 audio_mapper.py")
  print("  2. Create blank timeline (10000ms)")
  print("  3. Add SFX marker at 0ms")
  print("  4. Click ▶ button on each marker")
  ```

## Common Patterns

**Async Testing:**
No async code in this project; all operations are synchronous.

**Error Testing:**
```python
# Test error cases with try/except
def test_missing_file():
    """Test handling of missing file"""
    success = player.play_audio_file("nonexistent.wav")
    assert not success, "Should fail gracefully for missing file"
    assert not player.is_playing, "Should not be playing"
    print("✓ Missing file handled correctly")

# Test validation errors
def test_invalid_marker_type():
    """Test invalid marker type raises error"""
    try:
        marker = create_marker(
            time_ms=5000,
            marker_type="invalid_type"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid marker type" in str(e)
        print("✓ Invalid type caught correctly")
```

**Standalone Test Execution:**
Most tests can run standalone with `python3 tests/test_*.py` pattern:
```python
if __name__ == "__main__":
    try:
        test_audio_player_class()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

## Current Test Coverage

**35 test functions** across 17 test files:
- `test_models.py`: 5 tests (marker creation, versions, copying)
- `test_audio_playback.py`: 8 tests (playback functionality)
- `test_file_handler.py`: 5+ tests (import/export, migrations)
- `test_batch_operations.py`: 10 tests (batch generation UI)
- `test_elevenlabs_integration.py`: 4+ tests (API integration)
- `test_auto_assembly.py`: Assembly workflow tests
- `test_version_management.py`: Version tracking tests
- Others: Feature-specific integration tests

---

*Testing analysis: 2026-01-22*
