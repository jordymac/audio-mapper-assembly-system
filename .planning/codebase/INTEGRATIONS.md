# External Integrations

**Analysis Date:** 2026-01-22

## APIs & External Services

**ElevenLabs AI Audio Generation:**
- Service: ElevenLabs (https://elevenlabs.io/)
  - Text-to-Sound-Effects (SFX) API - Generates sound effects from text descriptions
  - Text-to-Speech (TTS) Voice API - Generates voice narration with preset or custom voices
  - Voice Design API - Creates custom voices from text descriptions
  - Music Generation API - Composes original music from style parameters
  - SDK/Client: `elevenlabs` 1.0.0 Python package
  - Auth: Environment variable `ELEVENLABS_API_KEY` (loaded from `.env.local`)
  - Implementation: `services/elevenlabs_api.py`

**Key ElevenLabs Functions:**
- `generate_sfx(description, output_path)` - Generates sound effects
  - Uses: `client.text_to_sound_effects.convert(text, duration_seconds, prompt_influence)`
  - Duration auto-determined, prompt_influence: 0.3

- `generate_voice(voice_profile, text, output_path)` - Generates voice narration
  - Custom voices: Uses `client.text_to_voice.design()` with Voice Design API
  - Preset voices: Uses default voice ID "21m00Tcm4TlvDq8ikWAM" (Rachel)
  - Uses: `client.text_to_speech.convert()` with model `eleven_multilingual_v2`
  - Voice settings: stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True

- `generate_music(positive_styles, negative_styles, sections, output_path)` - Generates music
  - Uses: `client.music.compose()` with composition_plan
  - Composition format: composition_plan with positive_global_styles, negative_global_styles, sections
  - Section duration limit: Max 120 seconds (120000ms) per section
  - Returns: Audio bytes, generation ID, composition metadata

**API Testing:**
- `test_api_connection()` - Lightweight connection test using `client.voices.get_all()`

## Data Storage

**File Format:**
- JSON for all persistent data
- Local filesystem only - no cloud storage integration

**Template Data Storage:**
- Location: `output/[TEMPLATE_ID]/[TEMPLATE_ID]_template.json`
- Contains: Marker definitions, prompt data, version history, timing information
- Managed by: `controllers/file_handler.py` (FileHandler class)

**Audio Asset Storage:**
- SFX: `output/[TEMPLATE_ID]/SFX/[NAME]_v[VERSION].mp3`
- Voice: `output/[TEMPLATE_ID]/VOICE/[NAME]_v[VERSION].mp3`
- Music: `output/[TEMPLATE_ID]/MUSIC/[NAME]_v[VERSION].mp3`
- Metadata: `[AUDIO_FILE]_metadata.json` alongside each audio file

**Temporary Storage:**
- `temp/` - Intermediate audio files during assembly and processing
- `generated_audio/` - Audio generation working directory

## Authentication & Identity

**Auth Provider:**
- ElevenLabs API Key authentication
  - Custom implementation: API key stored in `.env.local`
  - Env var name: `ELEVENLABS_API_KEY`
  - Loaded at application startup by `services/elevenlabs_api.py`
  - No user account/identity system - API key is application-level credential

**No Other Auth:**
- Desktop application (no user login system)
- No OAuth, JWT, or session-based authentication
- Single API key per installation

## Monitoring & Observability

**Error Tracking:**
- None detected - No external error tracking service integration

**Logs:**
- Console-based logging
- Print statements used throughout codebase for debugging and progress reporting
- ElevenLabs API integration prints detailed diagnostic information:
  - API call details, request parameters, response status
  - Examples in `services/elevenlabs_api.py` with formatted output blocks

## Video Processing

**Requires FFmpeg (via moviepy):**
- Implementation: `controllers/video_player_controller.py` and `managers/filmstrip_manager.py`
- Used for:
  - Video file reading and metadata extraction
  - Frame extraction for filmstrip display
  - Video duration detection
  - Frame rate detection

**Video Format Support:**
- MP4, MOV, AVI (via FFmpeg support)
- Extracted via `moviepy.video.io.VideoFileClip`

## CI/CD & Deployment

**Hosting:**
- Desktop application - No server hosting
- Runs locally on user machines via `run.sh` shell script

**CI Pipeline:**
- No automated CI/CD pipeline detected
- Manual testing via pytest framework

**Build Artifacts:**
- No build process required beyond Python venv activation
- Distributed as source code repository

## Environment Configuration

**Required env vars:**
- `ELEVENLABS_API_KEY` - ElevenLabs authentication token

**Optional env vars:**
- None identified in codebase

**Secrets location:**
- `.env.local` file in project root (not committed to git per `.gitignore`)
- Format: `ELEVENLABS_API_KEY=sk_[API_KEY_STRING]`

## Webhooks & Callbacks

**Incoming:**
- None detected - Desktop application with no server component

**Outgoing:**
- None detected - Only direct API calls to ElevenLabs endpoints, no webhook callbacks

## File I/O Operations

**Video Input:**
- User selects video files via file dialog in `audio_mapper.py`
- Supported formats: MP4, MOV, AVI (FFmpeg-supported formats)
- Processed by `controllers/video_player_controller.py`

**Audio Input:**
- Playback of locally stored audio files in `generated_audio/` and `output/` directories
- Uses pygame for audio playback via `services/audio_player.py`

**Audio Output:**
- Generated audio saved to disk by ElevenLabs API integration
- Assembly outputs saved to `output/[TEMPLATE_ID]/ASSEMBLED/` (inferred from assembly service)
- File format: MP3 (44100 Hz, 128 kbps for voice; variable for music/SFX)

**Template I/O:**
- Import templates: `FileHandler.import_from_json(filepath)` - reads JSON template files
- Export templates: `FileHandler.export_to_json(filepath, markers, template_id, template_name, duration_ms)` - writes JSON
- Validation: Checks for required 'markers' field, validates time values

## Media Format Handling

**Audio Formats Supported:**
- Input: MP3, WAV, OGG (via librosa/pydub/soundfile)
- Output: MP3 (from ElevenLabs APIs)
- Processing: In-memory bytes handling with streaming support

**Metadata Format:**
- JSON metadata files alongside audio assets
- Contains: Generation timestamps, version numbers, style parameters, composition plans

---

*Integration audit: 2026-01-22*
