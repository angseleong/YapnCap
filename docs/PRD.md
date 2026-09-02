# YapnCap — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-09-02

---

## 1. Overview

YapnCap is a **Python CLI tool for automated fact-checking** of YouTube videos, podcasts, and audio content. It extracts spoken claims from media sources and cross-references them against real-world data using Large Language Models (LLMs) with Search Grounding capabilities.

The tool provides instant, terminal-based fact-check reports with a distinctive, Gen-Z-friendly classification system:
- 🟢 **[NO CAP]** — Verified / True
- 🔴 **[CAP!]** — False / Hoax
- 🟡 **[YAPPIN!]** — Misleading / Needs Context

**Tagline:** *Detect if they are just yappin' and cappin' in real-time.*

---

## 2. Background & Motivation

Misinformation spreads faster than ever. Public figures, influencers, and content creators regularly make factual claims in videos and podcasts that go unchecked by their audiences.

Current problems:
- **Manual fact-checking is slow:** Watching a full video, identifying claims, and Googling each one takes significant effort.
- **No developer-friendly tools exist:** Most fact-checking services are web-based, manual, and not scriptable.
- **Lack of audio/video support:** Existing tools focus on text — there's no CLI pipeline that goes from video URL → verified claims.

YapnCap solves this by automating the entire pipeline: **extract speech → identify factual claims → verify each claim → present results** — all from a single terminal command.

---

## 3. Scope

### 3.1 In-Scope (MVP v1.0)

- **Interactive first-time setup** (`yapncap setup`) — configure language, AI provider, API key, and fact-check intensity.
- **YouTube transcript extraction** — automatically pull subtitles/CC from YouTube URLs.
- **Audio download & transcription fallback** — use `yt-dlp` to download audio and transcribe via STT when CC is unavailable.
- **AI-powered fact-checking engine** — extract factual claims and verify them using LLM + Search Grounding.
- **Rich terminal output** — animated progress bars, colored status badges, and formatted tables using `rich`.
- **Export support** — save results to Markdown (`.md`) or JSON (`.json`).
- **Multi-provider AI support** — Gemini (recommended), OpenAI, and Groq — user picks during setup.
- **Configurable intensity levels** — Lenient, Balanced, and Strict (Nitpick) modes.
- **Installable via pip** — publish-ready `pyproject.toml` with CLI entry point.

### 3.2 Out-of-Scope (v1.0)

- Live stream real-time analysis — planned for future version.
- Web-based UI / dashboard — CLI only for MVP.
- Batch processing of multiple URLs in one command.
- Support for non-YouTube platforms (Spotify, Apple Podcasts, etc.).
- Local LLM inference (Ollama, llama.cpp) — cloud API only for MVP.
- User accounts, authentication, or any server-side persistence.

---

## 4. Target Users

**Primary:** Gen-Z users, researchers, journalists, and netizens who need a fast, developer-friendly tool to verify claims made by public figures in video/audio content.

**Secondary:** Content creators who want to fact-check their own content before publishing, and educators who want to teach media literacy with concrete tools.

---

## 5. Core Features

### F1 — Interactive Configuration (`yapncap setup`)

An interactive CLI wizard that guides first-time users through configuration:

| Setting | Options | Storage |
|---|---|---|
| Language | `id` (Indonesian), `en` (English) | `~/.yapncap/config.json` |
| AI Provider | `gemini` (recommended), `openai`, `groq` | `~/.yapncap/config.json` |
| API Key | Provider-specific key | `~/.yapncap/config.json` |
| Fact-Check Intensity | `lenient`, `balanced`, `strict` | `~/.yapncap/config.json` |

Config is stored locally in `~/.yapncap/config.json` — never committed to any repository.

### F2 — YouTube Transcript Extractor

Automatically extracts subtitles/closed captions from a YouTube URL using `youtube-transcript-api`. Supports multiple languages. This is the **fastest path** — no download needed.

### F3 — Media Downloader & STT Fallback

When CC is unavailable:
1. Download audio-only stream using `yt-dlp` (smallest format).
2. Transcribe audio to text using a Speech-to-Text API or local Whisper model.
3. Feed transcript to the fact-check engine.

### F4 — Fact-Check Engine ("The Anti-Cap Engine")

The core intelligence layer. Takes transcript text and:
1. **Filters opinions** — skips subjective statements, greetings, filler.
2. **Extracts factual claims** — identifies verifiable statements (numbers, dates, policies, events) along with their start and end timestamps.
3. **Verifies each claim** — uses LLM with Search Grounding (web search) to cross-reference against current data.
4. **Provides correction & source** — returns the actual truth/clarification backed by a trusted, reputable source.
5. **Classifies results:**
   - 🟢 **[NO CAP]** — Claim is factually accurate.
   - 🔴 **[CAP!]** — Claim is false or fabricated.
   - 🟡 **[YAPPIN!]** — Claim is misleading, exaggerated, or lacks critical context.
6. **Adjusts depth** based on intensity setting (Lenient / Balanced / Strict).

### F5 — Rich Terminal Output

Beautiful, readable terminal output using the `rich` library:
- Animated progress bar during processing.
- Color-coded result table with status badges.
- Exact timestamps for when the claim was made in the video.
- Clear corrections and trusted source citations for each verification.
- Summary statistics (total claims, % NO CAP, % CAP, % YAPPIN).

### F6 — Export

Save fact-check results to file:
- **Markdown** (`.md`) — human-readable report with formatting.
- **JSON** (`.json`) — machine-readable structured data for integration.

---

## 6. Success Criteria (MVP)

| # | Criteria | Verification |
|---|---|---|
| C1 | `yapncap setup` creates a valid config file at `~/.yapncap/config.json` | Config file exists and is readable |
| C2 | `yapncap <youtube-url>` with CC available completes in < 30 seconds | Timed execution |
| C3 | Fact-check results display correctly in terminal with color badges | Visual inspection |
| C4 | At least 3 AI providers work (Gemini, OpenAI, Groq) | Test each provider |
| C5 | Export to `.md` and `.json` produces valid, well-formatted files | File content inspection |
| C6 | Fallback to yt-dlp + STT works when CC is unavailable | Test with a video without CC |
| C7 | All 3 intensity modes produce different levels of output granularity | Compare outputs |

---

## 7. Constraints & Known Limitations

| Constraint | Explanation |
|---|---|
| **BYOK (Bring Your Own Key)** | Users must provide their own API key for the chosen AI provider. No built-in keys. |
| **AI accuracy is not guaranteed** | LLMs can hallucinate. Results should be treated as a starting point, not absolute truth. |
| **Search Grounding availability** | Only Gemini natively supports Search Grounding. OpenAI/Groq rely on the LLM's training data or tool-use for verification. |
| **YouTube-only for MVP** | Only YouTube URLs are supported. Other platforms require custom extractors. |
| **Rate limits** | All AI providers have rate limits. Heavy usage may hit quota. YapnCap does not implement retry/backoff for MVP. |
| **Transcript quality** | Auto-generated YouTube CC can be inaccurate, especially for non-English content. This directly affects fact-check quality. |
| **No persistent storage** | Results are not saved to a database. Each run is independent. Export to file is available. |

---

## 8. Dependencies

**Python Libraries:**
- `typer` — CLI framework with auto-generated help.
- `rich` — Terminal formatting (tables, progress bars, panels).
- `youtube-transcript-api` — YouTube subtitle/CC extraction.
- `yt-dlp` — Audio/video downloading from YouTube.
- `google-genai` — Gemini API client (with Search Grounding).
- `openai` — OpenAI API client.
- `groq` — Groq API client.

**External Services:**
- **Google Gemini API** — Recommended provider. Free tier available with Search Grounding.
- **OpenAI API** — Alternative provider. Paid, widely supported.
- **Groq API** — Alternative provider. Fast inference, free tier available.
- **YouTube** — Source of video content and transcripts.

---

## 9. Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | AI provider changes API or pricing | High | Medium | Support multiple providers; abstract engine layer |
| R2 | YouTube blocks transcript extraction | High | Low | Fallback to yt-dlp audio download + STT |
| R3 | LLM produces inaccurate fact-checks | Medium | High | Clearly label results as AI-assisted, not authoritative |
| R4 | `yt-dlp` breaks due to YouTube changes | Medium | Medium | Pin version, monitor upstream releases |
| R5 | Rate limiting on AI API | Low | Medium | Document limits, suggest Gemini free tier |

---

## 10. Deliverables

| # | Deliverable | Status |
|---|---|---|
| D1 | Context documents (`README`, `PRD`, `ARCHITECTURE`, `TODO`, `AGENTS`) | 🔄 In Progress |
| D2 | Project scaffold (`pyproject.toml`, folder structure, config) | ⏳ Pending |
| D3 | Interactive Setup CLI (`yapncap setup`) | ⏳ Pending |
| D4 | YouTube Transcript Extractor | ⏳ Pending |
| D5 | Media Downloader & STT Fallback | ⏳ Pending |
| D6 | Fact-Check Engine (multi-provider) | ⏳ Pending |
| D7 | Rich Terminal Output | ⏳ Pending |
| D8 | Export to Markdown & JSON | ⏳ Pending |
| D9 | README final + PyPI-ready packaging | ⏳ Pending |

---

## 11. Glossary

| Term | Definition |
|---|---|
| **CAP** | Slang for lying or exaggerating. In YapnCap: a claim classified as false. |
| **YAPPIN** | Slang for talking without substance. In YapnCap: a claim that is misleading or lacks context. |
| **NO CAP** | Slang for "no lie" / telling the truth. In YapnCap: a verified factual claim. |
| **Search Grounding** | An LLM capability that allows the model to search the web in real-time to verify or supplement its answers with current information. |
| **BYOK** | Bring Your Own Key — users supply their own API credentials. |
| **CC** | Closed Captions — subtitles embedded in YouTube videos, either manually added or auto-generated. |
| **STT** | Speech-to-Text — converting spoken audio into written text. |
| **Intensity** | The thoroughness level of fact-checking: Lenient (major claims only), Balanced (all numbers and policies), Strict (every detail). |
