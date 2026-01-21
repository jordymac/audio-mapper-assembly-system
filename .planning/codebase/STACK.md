# Technology Stack

**Analysis Date:** 2026-01-22

## Languages

**Primary:**
- Python 3.11 - Core application language for entire system

**Secondary:**
- None - Monolithic Python application

## Runtime

**Environment:**
- Python 3.11.14
- Virtual environment (`venv/`) used for package isolation

**Package Manager:**
- pip - Python package manager
- Lockfile: `requirements.txt` present for core dependencies
- `pyproject.toml` present for project metadata and dev dependencies

## Frameworks

**Core:**
- Tkinter - Built-in Python GUI framework for desktop application interface
- Tkinter ttk - Widget styling and enhanced controls

**Audio Processing:**
- librosa 0.10.0 - Audio feature extraction and analysis
- pydub 0.25.1 - Audio file manipulation and format conversion
- soundfile 0.12.1 - Audio I/O operations
- pygame 2.5.0 - Audio playback and media control
- moviepy 1.0.3 - Video processing and frame extraction

**Image & Video:**
- opencv-python 4.8.0 - Video reading, frame processing, image manipulation
- Pillow 10.0.0 - Image manipulation and display in GUI

**Development & Testing:**
- pytest 7.4.0 - Test framework and runner
- pytest-cov 4.1.0 - Code coverage measurement
- black 23.0.0 - Code formatter (line-length: 100)
- ruff 0.1.0 - Linter and code quality tool

## Key Dependencies

**Critical:**
- elevenlabs 1.0.0 - ElevenLabs API SDK for audio generation (SFX, Voice, Music APIs)
  - Provides Text-to-Sound-Effects, Text-to-Speech with Voice Design, and Music Composition APIs
  - Used extensively in `services/elevenlabs_api.py`
  - Authentication via `ELEVENLABS_API_KEY` environment variable

- numpy 1.24.0 - Numerical computations for audio processing
- scipy 1.11.0 - Scientific computing utilities for audio signal processing

**Infrastructure:**
- python-dotenv 1.0.0 - Environment variable loading from `.env.local`
- click 8.1.0 - Command-line interface utilities
- tqdm 4.66.0 - Progress bar functionality for batch operations

## Configuration

**Environment:**
- Configuration via `.env.local` file for API keys and secrets
- Primary env var required: `ELEVENLABS_API_KEY` (ElevenLabs API authentication)
- loaded by `services/elevenlabs_api.py` at startup
- Dotenv uses `load_dotenv('.env.local')` for local development

**Build:**
- `pyproject.toml` - Project metadata and tool configuration
- `[tool.black]` - Code formatter config (line-length: 100, target Python 3.9+)
- `[tool.ruff]` - Linter config (line-length: 100, target Python 3.9+)
- `[tool.pytest.ini_options]` - Test discovery config (testpaths: `tests/`, pattern: `test_*.py`)

**Entry Point:**
- `audio_mapper.py` - Main GUI application entry point
- `run.sh` - Shell script that activates venv and launches `audio_mapper.py`

## Platform Requirements

**Development:**
- Python 3.9+ (minimum requirement per pyproject.toml)
- macOS/Linux/Windows with GUI support (Tkinter available)
- FFmpeg (required by moviepy for video processing)
- Audio device for playback testing

**Production:**
- Runs as standalone desktop application on macOS, Linux, or Windows
- Requires system audio output device
- Requires internet connection for ElevenLabs API calls
- Optional: Video files (MP4, MOV, AVI) for video mapping features

## Data Persistence

**Format:**
- JSON files for template data and marker definitions
- Template files stored in `output/` directory with structure: `[TEMPLATE_ID]_template.json`
- Metadata files stored alongside audio files: `[AUDIO_FILE]_metadata.json`

**Example Storage Paths:**
- `output/DM01_Untitled_Template/DM01_template.json` - Template marker configuration
- `output/DM01_Untitled_Template/SFX/whoosh_v1_metadata.json` - Audio asset metadata
- `output/DM01_Untitled_Template/MUSIC/lofi_chill_v2_metadata.json` - Generated music metadata

**Temporary Files:**
- `temp/` directory for intermediate audio processing files
- `generated_audio/` directory for audio generation outputs

## Architecture Style

**Desktop GUI Application:**
- Single-window, multi-panel Tkinter GUI
- Model-View-Controller (MVC) pattern with separation of concerns:
  - Models: `core/models.py` - Data structures (Marker, AudioVersion, etc.)
  - Controllers: `controllers/` - Business logic orchestration
  - Views: `ui/` - GUI components and display logic
  - Services: `services/` - External integrations and specialized operations
  - Managers: `managers/` - State and feature management (waveform, filmstrip, history, etc.)

---

*Stack analysis: 2026-01-22*
