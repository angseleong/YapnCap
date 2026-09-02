# YapnCap — System Architecture

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-09-02

---

## 1. System Overview

YapnCap is a **single-process CLI application** built in Python. It follows a linear pipeline architecture — data flows from input (URL/file) through a series of processing stages to output (terminal/file).

There is no server, no database, and no background process. Each invocation is a self-contained run.

---

## 2. High-Level Data Flow

```
[ User Input: YouTube URL ]
          │
          ▼
┌─────────────────────────────┐
│   Input Resolver            │  ← Determines input type (URL vs file)
│   (parse URL, validate)     │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   Transcript Extractor      │  ← youtube-transcript-api
│   (try CC first)            │
└──────────┬──────────────────┘
           │ success?
     ┌─────┴─────┐
     │ YES       │ NO
     ▼           ▼
  [Text]    ┌─────────────────────┐
            │  Audio Downloader   │  ← yt-dlp
            │  + STT Transcriber  │
            └──────────┬──────────┘
                       │
                       ▼
                    [Text]
           │           │
           └─────┬─────┘
                 ▼
┌─────────────────────────────┐
│   Fact-Check Engine         │  ← google-genai / openai / groq
│   (Anti-Cap Engine)         │
│                             │
│   1. Filter opinions        │
│   2. Extract factual claims │
│   3. Verify via LLM +      │
│      Search Grounding       │
│   4. Classify: NO CAP /     │
│      CAP / YAPPIN           │
└──────────┬──────────────────┘
           │  structured results (JSON)
           ▼
┌─────────────────────────────┐
│   Output Renderer           │  ← rich
│   (terminal table + export) │
└─────────────────────────────┘
```

---

## 3. Project Structure

```
yapncap/
├── docs/
│   ├── PRD.md                  # Product requirements
│   ├── ARCHITECTURE.md         # This file
│   └── TODO.md                 # Implementation roadmap
├── yapncap/
│   ├── __init__.py             # Package init, version info
│   ├── cli.py                  # Entry point — Typer app, command definitions
│   ├── config.py               # Config read/write to ~/.yapncap/config.json
│   ├── scraper.py              # YouTube transcript extraction + yt-dlp fallback
│   ├── engine.py               # AI fact-check engine (multi-provider)
│   └── output.py               # Rich terminal renderer + export (MD/JSON)
├── tests/                      # Unit tests (pytest)
│   ├── test_config.py
│   ├── test_scraper.py
│   ├── test_engine.py
│   └── test_output.py
├── pyproject.toml              # Package metadata, dependencies, CLI entry point
├── AGENTS.md                   # AI agent rules for this project
├── README.md                   # User-facing documentation
├── LICENSE                     # Project license
└── .gitignore
```

---

## 4. Component Details

### 4.1 CLI Layer (`cli.py`)

The entry point for all user interaction. Built with `typer` for automatic help generation and argument parsing.

**Commands:**

| Command | Description |
|---|---|
| `yapncap setup` | Interactive first-time configuration wizard |
| `yapncap <url>` | Run fact-check on a YouTube URL |
| `yapncap --export md <url>` | Run and export results to Markdown |
| `yapncap --export json <url>` | Run and export results to JSON |
| `yapncap --intensity strict <url>` | Override intensity for this run |
| `yapncap --provider gemini <url>` | Override AI provider for this run |

**Responsibilities:**
- Parse CLI arguments and options.
- Load config from `~/.yapncap/config.json`.
- Orchestrate the pipeline: scraper → engine → output.
- Display errors gracefully using `rich` console.

### 4.2 Config Manager (`config.py`)

Manages persistent user configuration stored at `~/.yapncap/config.json`.

**Config schema:**
```json
{
  "language": "en",
  "provider": "gemini",
  "api_key": "user-api-key-here",
  "intensity": "balanced"
}
```

**Key behaviors:**
- Creates `~/.yapncap/` directory if it doesn't exist.
- Validates config on load — if corrupt or missing fields, prompts user to re-run `yapncap setup`.
- API keys are stored locally, never transmitted anywhere except to the chosen AI provider's API.

### 4.3 Scraper / Transcript Extractor (`scraper.py`)

Handles all data extraction from the input source.

**Pipeline:**
1. **YouTube CC extraction** (fast path): Use `youtube-transcript-api` to pull subtitles. Try user's configured language first, then fall back to available languages.
2. **Audio download** (fallback): If CC is unavailable, use `yt-dlp` to download the smallest audio-only stream to a temp file.
3. **Speech-to-Text** (fallback): Transcribe the downloaded audio using an STT service. Returns plain text transcript.
4. **Metadata extraction**: Pull video title, channel name, and duration for the output report header.

**Returns:** A `TranscriptResult` dataclass:
```python
@dataclass
class TranscriptResult:
    title: str           # Video title
    channel: str         # Channel name
    url: str             # Original URL
    duration: str        # Video duration
    text: str            # Full transcript text
    source: str          # "cc" or "stt"
    language: str        # Transcript language code
```

### 4.4 Fact-Check Engine (`engine.py`)

The core intelligence module. Takes transcript text and returns structured fact-check results.

**Provider abstraction:**

All providers implement the same interface:
```python
def fact_check(text: str, intensity: str, language: str) -> list[ClaimResult]:
    """Send transcript to AI provider and return structured results."""
    ...
```

**Provider-specific details:**

| Provider | Library | Grounding | Notes |
|---|---|---|---|
| Gemini | `google-genai` | ✅ Native Search Grounding | Recommended — free tier with real-time web search |
| OpenAI | `openai` | ❌ Training data only | Relies on model's knowledge cutoff |
| Groq | `groq` | ❌ Training data only | Fast inference, free tier available |

**`ClaimResult` schema:**
```python
@dataclass
class ClaimResult:
    claim: str            # The original claim from the transcript
    verdict: str          # "NO CAP" | "CAP" | "YAPPIN"
    correction: str       # The actual truth / clarification
    source: str           # Trusted, reputable source URL or reference supporting the verdict
    time_start: str       # Start timestamp in the video (e.g., "12:34")
    time_end: str         # End timestamp in the video (e.g., "12:45")
```

**Intensity levels:**

| Level | Behavior |
|---|---|
| `lenient` | Only check major, high-impact claims (numbers, policies, major events) |
| `balanced` | Check all statistics, dates, policy references, and significant factual statements |
| `strict` | Check every verifiable detail — names, minor stats, promises, even tangential claims |

### 4.5 Output Renderer (`output.py`)

Handles all output formatting — both terminal display and file export.

**Terminal output (via `rich`):**
- Header panel with video metadata (title, channel, URL, duration).
- Animated progress bar during AI processing.
- Result table with columns: `#`, `Claim`, `Verdict` (color-coded badge), `Explanation`, `Source`.
- Summary footer: total claims, breakdown by verdict type.

**Export formats:**
- **Markdown** (`.md`): Human-readable report with headers, tables, and formatted text.
- **JSON** (`.json`): Array of `ClaimResult` objects for programmatic use.

---

## 5. Configuration

### 5.1 User Config (`~/.yapncap/config.json`)

Created by `yapncap setup`. Stores user preferences and API credentials locally.

| Field | Type | Default | Description |
|---|---|---|---|
| `language` | string | `"en"` | Output language (`en` or `id`) |
| `provider` | string | `"gemini"` | AI provider: `gemini`, `openai`, `groq` |
| `api_key` | string | — | API key for the selected provider |
| `intensity` | string | `"balanced"` | Fact-check depth: `lenient`, `balanced`, `strict` |

### 5.2 Environment Variables (Development)

For development and testing, API keys can also be set via environment variables. These take precedence over `config.json`:

```env
# AI Providers (at least one required)
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here

# Optional overrides
YAPNCAP_LANGUAGE=en
YAPNCAP_INTENSITY=balanced
YAPNCAP_PROVIDER=gemini
```

---

## 6. Error Handling Strategy

| Scenario | Handling |
|---|---|
| No config file found | Prompt user to run `yapncap setup` with a helpful message |
| Invalid API key | Catch auth error from provider, display clear message with instructions |
| YouTube URL invalid or video not found | Validate URL format first, then catch extraction errors |
| CC not available + yt-dlp fails | Log error, suggest user check URL or try a different video |
| AI provider rate limited | Display rate limit error, suggest waiting or switching provider |
| AI response is malformed JSON | Retry once with a stricter prompt; if still fails, show raw response and error |
| Network timeout | Catch `requests.Timeout` / `httpx.TimeoutException`, suggest retry |
| Export path not writable | Catch `PermissionError`, suggest alternative path |

---

## 7. Tech Stack Summary

| Component | Technology | Version Target |
|---|---|---|
| Language | Python | 3.11+ |
| CLI Framework | `typer` | latest |
| Terminal UI | `rich` | latest |
| YouTube Transcripts | `youtube-transcript-api` | latest |
| Audio Downloader | `yt-dlp` | latest |
| AI (Gemini) | `google-genai` | latest |
| AI (OpenAI) | `openai` | latest |
| AI (Groq) | `groq` | latest |
| Testing | `pytest` | latest |
| Packaging | `pyproject.toml` (Hatchling) | PEP 621 |
