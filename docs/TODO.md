# YapnCap — Implementation TODO

**Status Update Convention:**
- `[ ]` — Not started
- `[/]` — In progress (active)
- `[x]` — Done and verified

Use this file as the primary work guide. **Do not start the next phase before the active phase is complete.**

---

## Phase 0 — Project Foundation

- [ ] Create `pyproject.toml` with metadata, dependencies, and `[project.scripts]` entry point
- [ ] Create package structure: `yapncap/__init__.py`
- [ ] Create `yapncap/cli.py` — skeleton Typer app with `setup` and default URL command
- [ ] Create `yapncap/config.py` — skeleton config reader/writer for `~/.yapncap/config.json`
- [ ] Create `.gitignore` — ignore `venv/`, `dist/`, `*.egg-info/`, `.env`, `__pycache__/`
- [ ] Create `.env.example` — template with all supported env vars (no real values)
- [ ] Verify: `pip install -e .` works and `yapncap --help` shows help text

**Checkpoint Phase 0:** Running `pip install -e .` succeeds. `yapncap --help` prints the help message. Project structure matches `docs/ARCHITECTURE.md §3`.

---

## Phase 1 — Interactive Setup (`yapncap setup`)

- [x] Implement `yapncap setup` command with `rich.prompt` interactive wizard:
  - [x] Language selection (`en` / `id`)
  - [x] AI Provider selection (`gemini` (recommended) / `openai` / `groq`)
  - [x] API Key input (masked/secure prompt)
  - [x] Intensity selection (`lenient` / `balanced` / `strict`)
- [x] Save config to `~/.yapncap/config.json`
- [x] Implement config validation on load — detect missing/corrupt fields
- [x] Implement env var overrides (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`, etc.)
- [x] Test: run `yapncap setup`, verify config file is created with correct values

**Checkpoint Phase 1:** `yapncap setup` creates a valid `~/.yapncap/config.json`. Loading the config in Python returns all expected fields.

---

## Phase 2 — YouTube Transcript Extractor

- [x] Implement YouTube URL validation (extract video ID from various URL formats)
- [x] Implement CC extraction using `youtube-transcript-api`
  - [x] Try configured language first, fall back to available languages
  - [x] Handle `TranscriptsDisabled`, `NoTranscriptFound` errors gracefully
- [x] Extract video metadata (title, channel, duration) using `yt-dlp` metadata extraction (no download)
- [x] Return `TranscriptResult` dataclass with all fields populated
- [x] Test: run with a YouTube URL that has CC — transcript text is returned

**Checkpoint Phase 2:** `yapncap <youtube-url-with-cc>` extracts transcript text and prints it to terminal (raw text, no fact-checking yet).

---

## Phase 3 — Media Downloader & STT Fallback

- [ ] Implement audio-only download via `yt-dlp` (smallest format, temp file)
- [ ] Implement STT transcription (Gemini / OpenAI Whisper API / Groq Whisper)
- [ ] Wire fallback: if CC extraction fails → download audio → transcribe → return text
- [ ] Clean up temp audio files after transcription
- [ ] Test: run with a YouTube URL without CC — audio is downloaded, transcribed, and text returned

**Checkpoint Phase 3:** `yapncap <youtube-url-without-cc>` successfully downloads audio, transcribes it, and returns transcript text.

---

## Phase 4 — Fact-Check Engine

- [x] Implement base `fact_check()` function signature
- [x] Implement Gemini provider with Search Grounding
  - [x] Craft system prompt for claim extraction + verification
  - [x] Use structured output (JSON mode) for reliable parsing
  - [x] Handle Gemini-specific errors (quota, safety filters)
- [x] Implement OpenAI provider
  - [x] Adapt prompt for OpenAI's API format
  - [x] Handle OpenAI-specific errors
- [x] Implement Groq provider
  - [x] Adapt prompt for Groq's API format
  - [x] Handle Groq-specific errors
- [x] Implement intensity-based prompt adjustment (lenient / balanced / strict)
- [x] Return `list[ClaimResult]` with structured data
- [x] Test: send sample transcript text → receive structured fact-check results from each provider

**Checkpoint Phase 4:** Running `yapncap <url>` with each provider returns a `list[ClaimResult]` with valid verdicts (NO CAP / CAP / YAPPIN) and explanations.

---

## Phase 5 — Rich Terminal Output

- [x] Implement header panel (video title, channel, URL, duration, transcript source)
- [x] Implement animated progress bar during AI processing
- [x] Implement result table with color-coded verdict badges:
  - [x] 🟢 `[NO CAP]` — green
  - [x] 🔴 `[CAP!]` — red
  - [x] 🟡 `[YAPPIN!]` — yellow
- [x] Implement summary footer (total claims, % breakdown by verdict)
- [x] Test: full pipeline produces beautiful, readable terminal output

**Checkpoint Phase 5:** `yapncap <url>` produces a complete, styled terminal report. Visual inspection confirms colors, layout, and formatting are correct.

---

## Phase 6 — Export & Polish

- [ ] Implement Markdown export (`--export md`)
  - [ ] Include header, table, and summary in `.md` format
  - [ ] Auto-generate filename based on video title and date
- [ ] Implement JSON export (`--export json`)
  - [ ] Output array of `ClaimResult` objects
  - [ ] Pretty-printed with 2-space indentation
- [ ] Final `README.md` polish — installation, usage examples, screenshots
- [ ] Ensure `pyproject.toml` is PyPI-ready (metadata, classifiers, license)
- [ ] Test: exports produce valid, well-formatted files

**Checkpoint Phase 6:** Running `yapncap --export md <url>` and `yapncap --export json <url>` both produce correct output files. `README.md` is complete. Package is ready for `pip install`.

---

## BACKLOG — Future Phases

### Phase 7 — Live Mode 🔴
- [ ] Implement YouTube live stream audio interception
- [ ] Real-time chunked transcription
- [ ] Streaming fact-check results as claims are detected
- [ ] Terminal UI with live-updating table

### Phase 8 — Batch Processing
- [ ] Accept multiple URLs in one command
- [ ] Parallel processing with progress tracking
- [ ] Combined report output

### Phase 9 — Platform Expansion
- [ ] Support Spotify podcast URLs
- [ ] Support direct audio file input (`.mp3`, `.wav`, `.m4a`)
- [ ] Support Apple Podcasts URLs
