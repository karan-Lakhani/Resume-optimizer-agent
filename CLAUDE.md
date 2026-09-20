# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"AI Career Agent" — a Streamlit app that parses a master resume, matches it against jobs, tailors application materials, and tracks applications. Being built incrementally by milestone; most feature areas are still empty package stubs.

## Commands

```bash
# Setup (venv already exists at .venv/)
source .venv/bin/activate
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Run the full automated test suite
pytest tests/ -v

# Run a single test
pytest tests/test_schemas.py::test_resume_profile_assembled -v

# Run the manual smoke-test script (hits the live LLM API — costs real tokens/credits,
# NOT part of the pytest suite). Must run as a module, not `python tests/manual_checks.py`,
# or the `src` import fails.
python -m tests.manual_checks
```

CI (`.github/workflows/ci.yml`) runs `pytest tests/ -v` on push/PR to `main`/`feature/*`. There is no linter/formatter configured in this repo.

## Architecture

**LLM provider is swappable, not hardcoded.** `config/settings.py` loads `.env` and exposes `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` through `get_settings()` (cached singleton). `src/common/llm_client.py` is the **only** place that talks to a provider SDK — `call_llm(prompt, system)` branches on `settings.llm_provider` to `_call_groq`, `_call_anthropic`, or `_call_agentrouter`. Adding a new provider means adding a `_call_<provider>` function and a branch here, nothing else.

- Currently configured for Groq (`openai/gpt-oss-20b`). Anthropic (`claude-sonnet-5`) and AgentRouter (`deepseek-v4-flash`) configs are present but commented out in `.env` — flip `LLM_PROVIDER` and uncomment their three lines to switch.
- **Reasoning models cost optimization:** `gpt-oss-*` and AgentRouter models use hidden chain-of-thought that eats token budget before producing output. Groq calls use `reasoning_effort="low"`; AgentRouter calls use `thinking={"type": "disabled"}`. This reduced per-resume token cost from 4096 (truncated, broken JSON) to ~2200-2400 (complete, valid). Keep these params when touching these functions.
- **Empty response handling:** All three providers can return responses with no text block (only thinking blocks, or genuinely empty content). `llm_client.py` now raises `LLMEmptyResponseError` for these cases, and `src/job_application/resume_parser.py`'s retry loop wraps `call_llm()` to catch both `JSONDecodeError` and `LLMEmptyResponseError`, retrying up to 3 times.

**Resume parsing pipeline** (`src/job_application/resume_parser.py`): PDF → raw text with link reconstruction (`PyMuPDF`) → LLM call using the system prompt in `prompts/resume_parser.txt` → strict JSON → validated into the `ResumeProfile` Pydantic model (`src/common/schemas.py`). Key details:
- `_extract_page_text()` reads PDF annotations (links) and splices them into the word stream by position, appending URLs in parentheses after the text they link. This recovers project GitHub links that exist as invisible PDF glyphs, not visible text.
- Multi-column layout detection via `_detect_column_split()`: when a page has a significant horizontal gap, left and right columns are extracted and ordered separately (left column fully, then right), then merged. Single-column resumes skip this and use the original top-to-bottom ordering.
- `parse_resume_with_llm()` retries up to 3 times on JSON or empty-response errors, logging warnings, and raises the last error if all attempts exhaust.
- The master resume text is never mutated — the pipeline only produces a validated structured copy.

**Persistence is single-user, no auth.** SQLAlchemy models live in `src/tracker/models.py`; `src/tracker/db.py` builds the engine from `settings.database_url` and exposes `init_db()` / `SessionLocal`. Since there's no login system, `src/job_application/profile_service.py` establishes the "local user" pattern other features should follow: `get_or_create_default_user(session)` fetches-or-creates the single `User` row, then upserts onto that user's row rather than inserting duplicates. Follow this pattern for any new per-user data rather than introducing real multi-user auth.

**UI is one file.** `app.py` is a single Streamlit script with a sidebar `st.radio` for page nav; each page corresponds to a milestone. **Milestone 2 (My Profile)** is now built: file upload → parse → display with clickable links (`as_href()` adds `https://` scheme to schemeless URLs), grouped sections (Leadership entries grouped by section_title), and GitHub project links from recovered annotations. Unbuilt milestones show a placeholder `st.warning("Coming in Milestone N — ...")` — check `app.py` to see which milestone is next before assuming a feature doesn't exist elsewhere.

**Package layout mirrors milestones, not layers.** `src/` is organized by domain area (`job_application`, `job_search`, `tracker`, `linkedin_optimizer`, `market_intelligence`, `feedback`), not by technical layer. `job_application` and `tracker` now have real code; others are still `__init__.py` stubs. `src/common/` holds cross-cutting code shared across milestones (LLM client, schemas, logging).

**Logging**: `src/common/logging.py` — call `get_logger(__name__)`, never configure logging handlers yourself; `setup_logging()` is idempotent and wired in automatically on first `get_logger()` call.

## Commit convention

Commits are tagged sequentially by milestone/feature step (`v0: project skeleton`, `v1: restructure...`, ... `v15: add GitHub Actions CI...` — see `git log`). Follow this `vN: <what changed>` pattern for new commits on this project.

## Environment

`.env` (gitignored; `.env.example` is the template) holds `LLM_PROVIDER`/`LLM_MODEL`/`LLM_API_KEY`, job-source keys for the not-yet-built job search milestone (`JSEARCH_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`), `DATABASE_URL` (defaults to `sqlite:///./data/career_agent.db`), and `LOG_LEVEL`.

## Milestone Progress

**Milestone 1 (Dashboard / Skeleton)** — ✅ Done. Basic app structure, Streamlit UI, sidebar nav, database init.

**Milestone 2 (Resume Parsing)** — ✅ Done (committed as v16). Parses master resume from PDF → Pydantic model → database. Includes:
- Multi-provider LLM client (Groq/Anthropic/AgentRouter swappable)
- PyMuPDF text extraction with link annotation splicing + multi-column layout detection
- Retry logic with JSON and empty-response error handling
- "My Profile" page: file upload → parse → display with clickable links and grouped sections
- 10 automated tests (schemas + regression test for ProjectEntry.description)
- No blocking bugs; token efficiency tuned (reasoning_effort, thinking block control)

**Milestone 3 onwards** — Not started. Job search, recommendation engine, application tracker, etc. are placeholder pages.

## Known Limitations & Notes

- `.env` reload requires server restart — Streamlit doesn't watch for changes to cached singletons (like `get_settings()`).
- Multi-column layout detection works in theory but hasn't been tested against a real two-column PDF — sanity-check against your actual resume template if you have one.
- `max_tokens=4096` is hardcoded in `call_llm()` — for longer resumes, this may need tuning upward.
