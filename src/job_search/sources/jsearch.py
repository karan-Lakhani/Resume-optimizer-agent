import httpx
from src.common.logging import get_logger

logger = get_logger(__name__)

# OpenWebNinja JSearch (api.openwebninja.com) — auth via X-API-Key header
JSEARCH_BASE_URL = "https://api.openwebninja.com/jsearch/search-v2"


def search_jobs(
    api_key: str,
    query: str,
    location: str = "",
    remote_only: bool = False,
    date_posted: str = "month",
    num_pages: int = 1,
) -> list[dict]:
    """
    Call the OpenWebNinja JSearch endpoint and return a flat list of job dicts.

    date_posted: "all" | "today" | "3days" | "week" | "month"
    remote_only: filtered client-side via job_is_remote (the API ignores remote_jobs_only)
    """
    q = f"{query} in {location}" if location else query

    params: dict = {
        "query": q,
        "num_pages": str(num_pages),
        "date_posted": date_posted,
    }

    headers = {"X-API-Key": api_key}

    logger.info("Calling JSearch: query=%r date_posted=%s remote_only=%s", q, date_posted, remote_only)

    response = httpx.get(JSEARCH_BASE_URL, params=params, headers=headers, timeout=15)

    if response.status_code == 403:
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        msg = body.get("message", "Access denied")
        raise PermissionError(f"JSearch API returned 403: {msg}. Check your API key.")

    response.raise_for_status()
    data = response.json()
    jobs = data.get("data", {}).get("jobs", [])

    # API doesn't support remote filtering natively — apply client-side
    if remote_only:
        jobs = [j for j in jobs if j.get("job_is_remote")]

    logger.info("JSearch returned %d jobs (remote_only=%s)", len(jobs), remote_only)
    return jobs


def normalise_job(raw: dict) -> dict:
    """Flatten a JSearch job record to our internal shape, matching the Job model columns."""
    salary_min = raw.get("job_min_salary")
    salary_max = raw.get("job_max_salary")

    return {
        "source_job_id": raw.get("job_id", ""),
        "title": raw.get("job_title", ""),
        "company": raw.get("employer_name", ""),
        "location": ", ".join(
            filter(None, [raw.get("job_city"), raw.get("job_state"), raw.get("job_country")])
        ),
        "description": raw.get("job_description", ""),
        "employment_type": raw.get("job_employment_type", ""),
        "is_remote": raw.get("job_is_remote", False),
        "salary_min": float(salary_min) if salary_min is not None else None,
        "salary_max": float(salary_max) if salary_max is not None else None,
        "application_url": raw.get("job_apply_link", ""),
        "posted_at": raw.get("job_posted_at_datetime_utc"),
        "raw_json": raw,
    }
