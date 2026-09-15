from src.tracker.db import init_db, SessionLocal
from src.tracker.models import JobSource, Job

init_db()
session = SessionLocal()

source = JobSource(name="adzuna", type="api")
session.add(source)
session.commit()

job = Job(
    source_id=source.id,
    source_job_id="abc123",
    title="Data Analyst",
    company="Acme Corp",
    location="Bangalore",
    description="We are looking for a data analyst...",
    application_url="https://example.com/job/abc123",
    skills_json=["Python", "SQL", "Power BI"],
)
session.add(job)
session.commit()

print(f"Job saved with id: {job.id}")
print(f"Job source: {job.source.name}")
print(f"Source has {len(source.jobs)} job(s)")

session.close()