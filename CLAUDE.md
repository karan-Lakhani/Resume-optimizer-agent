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

**LLM provider is swappable, not hardcoded.** `config/settings.py` loads `.env` and exposes `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` through `get_settings()` (cached singleton). `src/common/llm_client.py` is the **only** place that talks to a provider SDK — `call_llm(prompt, system)` branches on `settings.llm_provider` to `_call_groq` or `_call_anthropic`. Adding a new provider means adding a `_call_<provider>` function and a branch here, nothing else.

- Currently configured for Groq (`openai/gpt-oss-20b`) to conserve API credits. Anthropic (`claude-sonnet-5`) config is present but commented out in `.env` — flip `LLM_PROVIDER` to `anthropic` and uncomment its three lines to switch back.
- `gpt-oss-*` models on Groq are reasoning models: without `reasoning_effort="low"` (set in `_call_groq`), they can spend the entire `max_tokens` budget on hidden chain-of-thought and return **empty content**. Keep that param when touching this function.

**Resume parsing pipeline** (`src/job_application/resume_parser.py`): PDF → raw text (`pdfplumber`) → LLM call using the system prompt in `prompts/resume_parser.txt` → strict JSON → validated into the `ResumeProfile` Pydantic model (`src/common/schemas.py`). The master resume text is never mutated by this pipeline — it only produces a validated structured copy.

**Persistence is single-user, no auth.** SQLAlchemy models live in `src/tracker/models.py`; `src/tracker/db.py` builds the engine from `settings.database_url` and exposes `init_db()` / `SessionLocal`. Since there's no login system, `src/job_application/profile_service.py` establishes the "local user" pattern other features should follow: `get_or_create_default_user(session)` fetches-or-creates the single `User` row, then upserts onto that user's row rather than inserting duplicates. Follow this pattern for any new per-user data rather than introducing real multi-user auth.

**UI is one file.** `app.py` is a single Streamlit script with a sidebar `st.radio` for page nav; each page corresponds to a milestone (Dashboard, My Profile, Job Search, Recommended Jobs, Resume Versions, Application Materials, Application Tracker, Job Market Insights, Settings). Unbuilt milestones show a placeholder `st.warning("Coming in Milestone N — ...")` — check `app.py` to see which milestone is next before assuming a feature doesn't exist elsewhere.

**Package layout mirrors milestones, not layers.** `src/` is organized by domain area (`job_application`, `job_search`, `tracker`, `linkedin_optimizer`, `market_intelligence`, `feedback`), not by technical layer. Most of these are still empty `__init__.py` stubs — only `job_application`, `tracker`, and `common` have real code so far. `src/common/` holds cross-cutting code shared across milestones (LLM client, schemas, logging) — put genuinely provider/domain-agnostic code there, domain logic in its matching package.

**Logging**: `src/common/logging.py` — call `get_logger(__name__)`, never configure logging handlers yourself; `setup_logging()` is idempotent and wired in automatically on first `get_logger()` call.

## Commit convention

Commits are tagged sequentially by milestone/feature step (`v0: project skeleton`, `v1: restructure...`, ... `v15: add GitHub Actions CI...` — see `git log`). Follow this `vN: <what changed>` pattern for new commits on this project.

## Environment

`.env` (gitignored; `.env.example` is the template) holds `LLM_PROVIDER`/`LLM_MODEL`/`LLM_API_KEY`, job-source keys for the not-yet-built job search milestone (`JSEARCH_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`), `DATABASE_URL` (defaults to `sqlite:///./data/career_agent.db`), and `LOG_LEVEL`.
