from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.common.llm_client import LLMEmptyResponseError, call_llm
from src.common.logging import get_logger
from src.common.schemas import JobMatchResult, ResumeProfile
from src.tracker.models import Job, JobMatch

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"
MAX_MATCH_ATTEMPTS = 3

# Loaded once at import time so a missing file fails fast and is never retried.
_SYSTEM_PROMPT = (PROMPTS_DIR / "job_matcher.txt").read_text()


def _build_resume_summary(profile: ResumeProfile) -> str:
    """Compact resume representation to keep token cost low."""
    lines: list[str] = []

    skills = [s.name for s in profile.skills]
    if skills:
        lines.append(f"SKILLS: {', '.join(skills)}")

    for exp in profile.experience:
        techs = f" [{', '.join(exp.technologies)}]" if exp.technologies else ""
        lines.append(f"EXPERIENCE: {exp.job_title} at {exp.company}{techs}")

    for proj in profile.projects:
        techs = f" [{', '.join(proj.technologies)}]" if proj.technologies else ""
        lines.append(f"PROJECT: {proj.name}{techs}")

    for edu in profile.education:
        lines.append(f"EDUCATION: {edu.degree} in {edu.field_of_study} at {edu.institution}")

    return "\n".join(lines)


def _extract_json(text: str) -> str:
    """Pull the first {...} block out of a response regardless of surrounding markdown."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group()
    return text


def _match_with_llm(profile: ResumeProfile, job: Job) -> JobMatchResult:
    resume_summary = _build_resume_summary(profile)

    prompt = f"""Evaluate this candidate's fit for the job and return the JSON structure as instructed.

CANDIDATE PROFILE:
{resume_summary}

JOB TITLE: {job.title}
COMPANY: {job.company}
JOB DESCRIPTION:
{job.description}
"""

    last_error: Exception | None = None
    for attempt in range(1, MAX_MATCH_ATTEMPTS + 1):
        logger.info("Matching job %d (attempt %d/%d)", job.id, attempt, MAX_MATCH_ATTEMPTS)
        try:
            response = call_llm(prompt=prompt, system=_SYSTEM_PROMPT)
            parsed = json.loads(_extract_json(response))
            result = JobMatchResult.model_validate(parsed)
            logger.info("Job %d matched — score %d", job.id, result.match_score)
            return result
        except (json.JSONDecodeError, LLMEmptyResponseError, ValidationError) as e:
            last_error = e
            logger.warning("Match attempt %d/%d failed for job %d: %s", attempt, MAX_MATCH_ATTEMPTS, job.id, e)

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"_match_with_llm exhausted {MAX_MATCH_ATTEMPTS} attempts with no error recorded")


def get_or_compute_match(
    profile_id: int,
    profile: ResumeProfile,
    job: Job,
    session: Session,
) -> JobMatch:
    """Return cached JobMatch if it exists, otherwise run the LLM and store the result."""
    existing = (
        session.query(JobMatch)
        .filter_by(profile_id=profile_id, job_id=job.id)
        .first()
    )
    if existing:
        return existing

    result = _match_with_llm(profile, job)

    match = JobMatch(
        profile_id=profile_id,
        job_id=job.id,
        match_score=result.match_score,
        matched_skills_json=result.matched_skills,
        missing_skills_json=result.missing_skills,
        summary=result.summary,
    )
    session.add(match)
    session.commit()
    session.refresh(match)
    return match
