# YapnCap — Agent Rules

**You are working on the YapnCap project**, a Python CLI tool that fact-checks YouTube videos, podcasts, and audio content by extracting speech and verifying claims using LLMs with Search Grounding.  
**Follow all rules below without exception while working on this project.**

---

## Context Documents

Before making any architectural decision or starting any task, **ALWAYS read the following documents** in the `docs/` folder:

- **`docs/PRD.md`** — Single source of truth for features, scope, and product requirements.
- **`docs/ARCHITECTURE.md`** — Tech stack, folder structure, component design, and config schema.
- **`docs/TODO.md`** — Active task list. **Do not work on anything not in the currently active task.**

---

## 1. Tech Stack & Environment

- **Language:** Python 3.11+.
- **CLI Framework:** `typer` for commands, `rich` + `rich.prompt` for interactive UI and terminal output.
- **YouTube Data:** `youtube-transcript-api` for CC extraction, `yt-dlp` for audio download and metadata.
- **AI Providers:** `google-genai` (Gemini — recommended), `openai`, `groq`. User selects during `yapncap setup`.
- **Config Storage:** `~/.yapncap/config.json` via custom `config.py` module.
- **Packaging:** `pyproject.toml` with Hatchling build backend. CLI entry point via `[project.scripts]`.
- **Testing:** `pytest`.

---

## 2. Strict Constraints

- **NEVER hardcode API keys** in source code. Keys come from `~/.yapncap/config.json` or environment variables.
- **NEVER commit `~/.yapncap/config.json`** — it contains user credentials. This path is outside the repo, but document this clearly.
- **NEVER commit `.env` files** to Git.
- **Keep the CLI stateless** — no database, no server, no background processes. Each run is independent.
- **BYOK only** — YapnCap does not include or bundle any API keys. Users must provide their own.
- **No unnecessary dependencies** — every `pip install` must be justified. Prefer stdlib when possible.

---

## 3. Workflow & Scope

- **Follow TODO.md:** Only work on tasks marked `[/]` (in progress). Do not jump to the next phase before the active phase reaches its checkpoint.
- **Simplicity over Abstraction:** Choose the simplest implementation that meets current requirements. Avoid over-engineering.
- **Verify Checkpoint:** After completing each phase, ensure the checkpoint condition in `TODO.md` is met before marking the phase as done.
- **No Scope Creep:** Do not create files, folders, or logic outside the active task. Good ideas for new features → add to `BACKLOG` in `TODO.md`, don't implement.
- **No Premature Refactoring:** Don't refactor working code just for "cleanliness". Speed and correctness matter more than perfect abstraction in early phases.

---

## 4. Code Style & Quality

- **Use type hints** on all function signatures: `def fact_check(text: str, intensity: str) -> list[ClaimResult]:`
- **Use docstrings** on all public classes and functions — at minimum one line describing purpose.
- **Explicit error handling:** Every HTTP request and file operation must be wrapped in specific `try/except` (never bare `except Exception` without logging).
- **Logging** not `print()`: Use Python's standard `logging` module for all diagnostic output. Levels: `DEBUG` for details, `INFO` for normal flow, `WARNING` for non-ideal conditions, `ERROR` for failures.
- **Follow the folder structure** in `docs/ARCHITECTURE.md §3` exactly. Do not create folders or files in unlisted locations without clear justification.

---

## 5. CLI Rules

- **Typer is the only CLI framework** — do not use `argparse`, `click`, or manual `sys.argv` parsing.
- **All user-facing output** goes through `rich` — console, tables, panels, progress bars. No raw `print()` to the user.
- **Error messages must be helpful** — tell the user what went wrong AND what to do about it.
- **`yapncap setup` must be idempotent** — running it again should overwrite the existing config cleanly.
- **Support CLI overrides** — `--provider`, `--intensity`, `--export` flags override config.json for that run.

---

## 6. AI Engine Rules

- **Provider-agnostic interface:** The `engine.py` module must expose a single `fact_check()` function that routes to the correct provider based on config.
- **Structured output:** Always request JSON from the AI provider. Parse the response into `ClaimResult` dataclasses.
- **Prompt engineering:** Prompts must clearly instruct the AI to: (1) extract factual claims along with start/end timestamps, (2) verify each claim, (3) classify as NO CAP / CAP / YAPPIN, (4) provide a factual correction/clarification, (5) cite a trusted, reputable source for the correction.
- **Intensity affects the prompt** — adjust prompt instructions based on lenient/balanced/strict setting.
- **If the AI response is malformed,** retry once. If still malformed, show a clear error to the user.
- **Never expose raw AI responses** to the user in normal operation — always parse into the structured format.

---

## 7. Efficiency Rules (Caveman & Ponytail)

- **Caveman (Terse Prose):** Don't ramble. Give direct, to-the-point answers. Avoid unnecessary intros, outros, or filler. *"Why use many token when few token do trick"*.
- **Ponytail (Minimalist Code):** Act like a *"lazy senior developer"*. Write the minimum code needed to complete the task (YAGNI principle). Don't over-engineer or add abstractions/features that aren't currently needed. Use the simplest, most efficient approach.
