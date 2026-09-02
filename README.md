# YapnCap 🧢

> *Detect if they are just yappin' and cappin' in real-time.*

**YapnCap** is a Python CLI tool that fact-checks YouTube videos, podcasts, and audio content. It extracts spoken claims and verifies them against real-world data using AI with Search Grounding.

```
$ yapncap https://youtube.com/watch?v=example

 YapnCap 🧢 — Fact-Check Report
 ┌─────────────────────────────────────────────┐
 │ 📺 Title:    Some Political Speech 2026     │
 │ 👤 Channel:  News Channel                   │
 │ 🕐 Duration: 12:34                          │
 │ 📝 Source:   YouTube CC (English)            │
 └─────────────────────────────────────────────┘

 # │ Time          │ Claim                        │ Verdict    │ Correction & Source
 ──┼───────────────┼──────────────────────────────┼────────────┼───────────────────────────────────────
 1 │ 01:12 - 01:18 │ "GDP grew 5% last quarter"   │ 🟢 NO CAP │ True. Q3 GDP was 5.01% (Source: BPS)
 2 │ 03:45 - 03:52 │ "Unemployment is at 2%"      │ 🔴 CAP!   │ False. Rate is 5.3% (Source: World Bank)
 3 │ 10:05 - 10:20 │ "We built 1000 schools"      │ 🟡 YAPPIN │ Misleading. 600 were just renovations. (Source: Kemdikbud)

 Summary: 3 claims checked — 1 verified, 1 false, 1 misleading
```

---

## 🎯 What It Does

- **🟢 [NO CAP]** — Claim is factually accurate
- **🔴 [CAP!]** — Claim is false or fabricated
- **🟡 [YAPPIN!]** — Claim is misleading or needs context

---

## ⚡ Features

- **One-command fact-checking** — paste a YouTube URL, get instant results
- **Multiple AI providers** — Gemini (recommended), OpenAI, Groq
- **Search Grounding** — Gemini verifies claims against real-time web data
- **Auto-transcript** — pulls YouTube CC automatically, falls back to audio download + STT
- **Configurable intensity** — Lenient, Balanced, or Strict (Nitpick) mode
- **Beautiful terminal output** — rich tables, color-coded badges, progress bars
- **Export** — save reports as Markdown or JSON

---

## 📦 Installation

```bash
pip install yapncap
```

Or install from source:

```bash
git clone https://github.com/angseleong/YapnCap.git
cd YapnCap
pip install -e .
```

**Requirements:** Python 3.11+

---

## 🚀 Quick Start

### 1. First-time setup

```bash
yapncap setup
```

This interactive wizard will ask you to:
- Choose your language (English / Indonesian)
- Select an AI provider (Gemini recommended — it has free Search Grounding)
- Enter your API key
- Set fact-check intensity

### 2. Fact-check a video

```bash
yapncap https://youtube.com/watch?v=VIDEO_ID
```

### 3. Export results

```bash
# Save as Markdown
yapncap --export md https://youtube.com/watch?v=VIDEO_ID

# Save as JSON
yapncap --export json https://youtube.com/watch?v=VIDEO_ID
```

---

## ⚙️ Configuration

Config is stored at `~/.yapncap/config.json`:

```json
{
  "language": "en",
  "provider": "gemini",
  "api_key": "your-api-key",
  "intensity": "balanced"
}
```

You can also use environment variables (these override config.json):

```bash
export GEMINI_API_KEY=your_key
export YAPNCAP_PROVIDER=gemini
export YAPNCAP_INTENSITY=strict
```

### CLI Overrides

```bash
# Override provider for one run
yapncap --provider openai https://youtube.com/watch?v=VIDEO_ID

# Override intensity for one run
yapncap --intensity strict https://youtube.com/watch?v=VIDEO_ID
```

---

## 🤖 Supported AI Providers

| Provider | Search Grounding | Free Tier | Library |
|---|---|---|---|
| **Gemini** (recommended) | ✅ Yes | ✅ Yes | `google-genai` |
| OpenAI | ❌ No | ❌ Paid | `openai` |
| Groq | ❌ No | ✅ Yes | `groq` |

> **Tip:** Gemini is recommended because it supports **Search Grounding** — the AI can search the web in real-time to verify claims, making fact-checks significantly more accurate.

---

## 📊 Intensity Levels

| Level | Description |
|---|---|
| `lenient` | Only checks major, high-impact claims |
| `balanced` | Checks all statistics, policies, and significant statements |
| `strict` | Checks every verifiable detail — names, minor stats, even tangential claims |

---

## 🛠 Development

```bash
# Clone the repo
git clone https://github.com/angseleong/YapnCap.git
cd YapnCap

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
yapncap/
├── docs/               # PRD, Architecture, TODO
├── yapncap/
│   ├── cli.py          # CLI entry point (Typer)
│   ├── config.py       # Config manager (~/.yapncap/config.json)
│   ├── scraper.py      # YouTube transcript + yt-dlp fallback
│   ├── engine.py       # AI fact-check engine (multi-provider)
│   └── output.py       # Rich terminal output + export
├── tests/              # pytest tests
├── pyproject.toml      # Package config
└── AGENTS.md           # AI agent rules
```

---

## 📄 License

MIT

---

## 🤝 Contributing

Contributions welcome! Please read the project docs in `docs/` before starting:
- [`docs/PRD.md`](docs/PRD.md) — What we're building
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — How it's built
- [`docs/TODO.md`](docs/TODO.md) — What needs to be done
