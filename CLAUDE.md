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

**LLM provider is swappable, not hardcoded.** `config/settings.py` loads `.env` and exposes `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` through `get_settings()` (cached singleton). `src/common/llm_client.py` is the **only** place that talks to a provider SDK — `call_llm(prompt, system)` branches on `settings.llm_provider` to `_call_groq` or `_call_agentrouter`. Adding a new provider means adding a `_call_<provider>` function and a branch here, nothing else.

- Currently configured for Groq (`openai/gpt-oss-20b`). AgentRouter (`deepseek-v4-flash`) is available as a backup — flip `LLM_PROVIDER=agentrouter` and uncomment its three lines in `.env` to switch. Anthropic has been removed as a provider; only `groq` and `agentrouter` are supported. AgentRouter uses plain `httpx` (no anthropic SDK).
- **Reasoning models cost optimization:** `gpt-oss-*` and AgentRouter models use hidden chain-of-thought that eats token budget before producing output. Groq calls use `reasoning_effort="low"`; AgentRouter calls use `thinking={"type": "disabled"}`. This reduced per-resume token cost from 4096 (truncated, broken JSON) to ~2200-2400 (complete, valid). Keep these params when touching these functions.
- **Empty response handling:** Both providers can return responses with no text block (only thinking blocks, or genuinely empty content). `llm_client.py` raises `LLMEmptyResponseError` for these cases. All LLM-calling pipelines (resume parser, job matcher) retry up to 3 times on `JSONDecodeError`, `LLMEmptyResponseError`, or `ValidationError`.

**Resume parsing pipeline** (`src/job_application/resume_parser.py`): PDF → raw text with link reconstruction (`PyMuPDF`) → LLM call using the system prompt in `prompts/resume_parser.txt` → strict JSON → validated into the `ResumeProfile` Pydantic model (`src/common/schemas.py`). Key details:
- `_extract_page_text()` reads PDF annotations (links) and splices them into the word stream by position, appending URLs in parentheses after the text they link. This recovers project GitHub links that exist as invisible PDF glyphs, not visible text.
- Multi-column layout detection via `_detect_column_split()`: when a page has a significant horizontal gap, left and right columns are extracted and ordered separately (left column fully, then right), then merged. Single-column resumes skip this and use the original top-to-bottom ordering.
- `parse_resume_with_llm()` retries up to 3 times on JSON or empty-response errors, logging warnings, and raises the last error if all attempts exhaust.
- The master resume text is never mutated — the pipeline only produces a validated structured copy.

**Persistence is single-user, no auth.** SQLAlchemy models live in `src/tracker/models.py`; `src/tracker/db.py` builds the engine from `settings.database_url` and exposes `init_db()` / `SessionLocal`. Since there's no login system, `src/job_application/profile_service.py` establishes the "local user" pattern other features should follow: `get_or_create_default_user(session)` fetches-or-creates the single `User` row, then upserts onto that user's row rather than inserting duplicates. Follow this pattern for any new per-user data rather than introducing real multi-user auth.

**UI is one file.** `app.py` is a single Streamlit script with a sidebar `st.radio` for page nav; each page corresponds to a milestone. Built pages: My Profile (M2), Job Search (M3), Recommended Jobs (M4). Unbuilt milestones show a placeholder `st.warning("Coming in Milestone N — ...")` — check `app.py` to see which milestone is next before assuming a feature doesn't exist elsewhere. `as_href()` adds `https://` scheme to schemeless URLs for clickable links.

**Package layout mirrors milestones, not layers.** `src/` is organized by domain area (`job_application`, `job_search`, `job_matching`, `tracker`, `linkedin_optimizer`, `market_intelligence`, `feedback`), not by technical layer. `job_application`, `job_search`, `job_matching`, and `tracker` now have real code; others are still `__init__.py` stubs. `src/common/` holds cross-cutting code shared across milestones (LLM client, schemas, logging).

**Job matching pipeline** (`src/job_matching/matcher.py`): `ResumeProfile` + `Job` → compact resume summary → LLM call using `prompts/job_matcher.txt` → strict JSON → `JobMatchResult` Pydantic model → upserted to `JobMatch` table. Key details:
- `_SYSTEM_PROMPT` is loaded once at module import — a missing prompt file fails fast rather than burning retry attempts.
- `_extract_json()` uses `re.search(r'\{.*\}', ...)` to pull the JSON object out of the response regardless of surrounding markdown or trailing text.
- `get_or_compute_match()` checks the `JobMatch` table first; only calls the LLM when no cached result exists. `JobMatch` has a `UniqueConstraint("profile_id", "job_id")` to prevent duplicate rows under concurrent renders.
- Retry logic catches `(json.JSONDecodeError, LLMEmptyResponseError, ValidationError)` — only retries errors that a fresh LLM call could resolve.
- Score thresholds in `app.py` match the prompt's scoring guide: ≥80 Strong fit (green), ≥60 Good fit (blue), ≥40 Partial fit (orange), <40 Weak fit (red).

**Logging**: `src/common/logging.py` — call `get_logger(__name__)`, never configure logging handlers yourself; `setup_logging()` is idempotent and wired in automatically on first `get_logger()` call.

## Commit convention

Commits are tagged sequentially by milestone/feature step (`v0: project skeleton`, `v1: restructure...`, ... `v15: add GitHub Actions CI...` — see `git log`). Follow this `vN: <what changed>` pattern for new commits on this project.

## Environment

`.env` (gitignored; `.env.example` is the template) holds `LLM_PROVIDER`/`LLM_MODEL`/`LLM_API_KEY`, `JSEARCH_API_KEY` (required for Job Search), `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` (not yet used), `DATABASE_URL` (defaults to `sqlite:///./data/career_agent.db`), and `LOG_LEVEL`.

## Milestone Progress

**Milestone 1 (Dashboard / Skeleton)** — ✅ Done. Basic app structure, Streamlit UI, sidebar nav, database init.

**Milestone 2 (Resume Parsing)** — ✅ Done (committed as v16). Parses master resume from PDF → Pydantic model → database. Includes:
- Multi-provider LLM client (Groq/AgentRouter swappable; Anthropic removed)
- PyMuPDF text extraction with link annotation splicing + multi-column layout detection
- Retry logic with JSON and empty-response error handling
- "My Profile" page: file upload → parse → display with clickable links and grouped sections
- 10 automated tests (schemas + regression test for ProjectEntry.description)
- No blocking bugs; token efficiency tuned (reasoning_effort, thinking block control)

**Milestone 3 (Job Search)** — ✅ Done (committed as v17, branch `feature/job-search`). Discovers jobs via OpenWebNinja JSearch API. Includes:
- JSearch API client (`src/job_search/sources/jsearch.py`) — calls endpoint, normalises response to `Job` model shape
- Search service (`src/job_search/search_service.py`) — auto-generates search params from parsed profile, upserts results to DB, saves jobs as `Application` rows
- Job Search page: auto-filled editable form (keywords, location, remote toggle, date filter), results as cards with Apply + Save buttons
- `remote_only` filtered client-side (API ignores the param); `date_posted` and `num_pages` sent correctly
- Save button persists state in session (`st.toast` + disabled "✓ Saved" button)

**Milestone 4 (Job Matching)** — ✅ Done. Scores all saved jobs against the parsed resume using the LLM and surfaces them ranked by fit. Includes:
- `JobMatchResult` Pydantic schema + `JobMatch` SQLAlchemy table (with `UniqueConstraint` on `profile_id, job_id`)
- `prompts/job_matcher.txt` — scoring guide (0–100) + strict JSON output spec
- `src/job_matching/matcher.py` — compact resume summary builder, `_extract_json()` for robust JSON extraction, DB-cached results, 3-attempt retry
- "Recommended Jobs" page: auto-scores all jobs on load, renders cards sorted by score with colour-coded badge (≥80/≥60/≥40/<40), "📋 Details" expander with matched/missing skills and LLM summary
- 7 automated tests in `tests/test_matching.py`
- `.vscode/settings.json` added to point VS Code at `.venv`

**Milestone 5 (Resume Tailoring)** — 🔜 Next. Design decisions partially settled:
- **Mechanic**: full LLM rewrite of resume sections targeted at a specific job (not suggestions-only)
- **Sections in scope**: TBD (Q4 pending — likely summary + skills + experience bullets)
- **Entry point**: TBD (Q5 pending — likely button on Recommended Jobs card)
- **Output**: stored as a `ResumeVersion` DB row first; PDF export deferred to a later milestone
- Will use the existing `ResumeVersion` table (`src/tracker/models.py`) and add `src/job_matching/tailorer.py` + `prompts/resume_tailor.txt`

**Milestone 6 (Application Tracker)** — 📋 Planned. Track application status through Applied → Interviewing → Offer/Rejected using the existing `Application` table. Dedicated "📊 Application Tracker" page.

**Milestone 7+ (LinkedIn Optimizer, Market Intelligence, Feedback)** — 📋 Backlog. Package stubs exist in `src/`; not yet designed.

## Known Limitations & Notes

- `.env` reload requires server restart — Streamlit doesn't watch for changes to cached singletons (like `get_settings()`).
- Multi-column layout detection works in theory but hasn't been tested against a real two-column PDF — sanity-check against your actual resume template if you have one.
- `max_tokens=4096` is hardcoded in `call_llm()` — for longer resumes, this may need tuning upward.
