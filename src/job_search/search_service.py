from datetime import datetime

from sqlalchemy.orm import Session

from src.common.logging import get_logger
from src.common.schemas import EvidenceLevel, ResumeProfile
from src.job_search.sources.jsearch import normalise_job, search_jobs
from src.tracker.models import Job, JobSource

logger = get_logger(__name__)

JSEARCH_SOURCE_NAME = "jsearch"


def generate_search_params(profile: ResumeProfile) -> dict:
    """
    Derive sensible default search params from a parsed resume.

    Returns a dict with keys: query, location, remote_only, date_posted.
    All values are editable by the user before the actual search.
    """
    # Most recent job title as the primary keyword
    current_title = ""
    if profile.experience:
        # is_current first, otherwise the first entry (assumed most recent)
        current = next((e for e in profile.experience if e.is_current), profile.experience[0])
        current_title = current.job_title

    # Top strong/moderate skills (cap at 3 so the query stays readable)
    top_skills = [
        s.name for s in profile.skills
        if s.evidence_level in (EvidenceLevel.STRONG, EvidenceLevel.MODERATE)
    ][:3]

    query_parts = [current_title] + top_skills
    query = " ".join(filter(None, query_parts))

    location = profile.personal_information.location or ""

    return {
        "query": query,
        "location": location,
        "remote_only": False,
        "date_posted": "month",
    }


def _get_or_create_source(session: Session) -> JobSource:
    source = session.query(JobSource).filter_by(name=JSEARCH_SOURCE_NAME).first()
    if not source:
        source = JobSource(name=JSEARCH_SOURCE_NAME, type="api")
        session.add(source)
        session.flush()
    return source


def run_search(
    api_key: str,
    query: str,
    location: str,
    remote_only: bool,
    date_posted: str,
    session: Session,
    num_pages: int = 1,
) -> list[dict]:
    """
    Run a JSearch query, upsert results into the DB, and return normalised job dicts.
    The returned list is what the UI renders directly — no extra DB read needed.
    """
    raw_jobs = search_jobs(
        api_key=api_key,
        query=query,
        location=location,
        remote_only=remote_only,
        date_posted=date_posted,
        num_pages=num_pages,
    )

    source = _get_or_create_source(session)
    normalised = []

    for raw in raw_jobs:
        job_data = normalise_job(raw)
        source_job_id = job_data["source_job_id"]

        existing = (
            session.query(Job)
            .filter_by(source_id=source.id, source_job_id=source_job_id)
            .first()
        )
        if existing:
            # refresh fields that can change between searches
            existing.title = job_data["title"]
            existing.company = job_data["company"]
            existing.location = job_data["location"]
            existing.salary_min = job_data["salary_min"]
            existing.salary_max = job_data["salary_max"]
            existing.raw_json = job_data["raw_json"]
            job_db_id = existing.id
        else:
            posted_at = None
            if job_data["posted_at"]:
                try:
                    posted_at = datetime.fromisoformat(job_data["posted_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            new_job = Job(
                source_id=source.id,
                source_job_id=source_job_id,
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                description=job_data["description"],
                employment_type=job_data["employment_type"],
                salary_min=job_data["salary_min"],
                salary_max=job_data["salary_max"],
                application_url=job_data["application_url"],
                posted_at=posted_at,
                raw_json=job_data["raw_json"],
            )
            session.add(new_job)
            session.flush()
            job_db_id = new_job.id

        normalised.append({**job_data, "db_id": job_db_id})

    session.commit()
    logger.info("Upserted %d jobs to DB", len(normalised))
    return normalised


def save_job(job_db_id: int, session: Session) -> None:
    """Mark a job as 'saved' — creates an Application row in status='saved'."""
    from src.tracker.models import Application

    existing = session.query(Application).filter_by(job_id=job_db_id, status="saved").first()
    if not existing:
        session.add(Application(job_id=job_db_id, status="saved"))
        session.commit()
        logger.info("Saved job db_id=%d", job_db_id)
