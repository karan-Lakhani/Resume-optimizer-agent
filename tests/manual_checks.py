from src.tracker.db import init_db, SessionLocal
from src.tracker.models import JobSource, Job, ResumeVersion, Application, ApplicationMaterial

init_db()
session = SessionLocal()

# reuse existing source and job
source = JobSource(name="jsearch", type="api")
session.add(source)
session.commit()

job = Job(
    source_id=source.id,
    source_job_id="xyz999",
    title="Data Scientist",
    company="Beta Corp",
    location="Remote",
    description="Looking for a data scientist...",
    application_url="https://example.com/job/xyz999",
)
session.add(job)
session.commit()

# create an application (no resume version yet)
application = Application(
    job_id=job.id,
    status="saved",
)
session.add(application)
session.commit()

print(f"Application saved with id: {application.id}")
print(f"Status: {application.status}")

# attach a cover letter
material = ApplicationMaterial(
    application_id=application.id,
    type="cover_letter",
    content="Dear Hiring Manager, I am excited to apply...",
)
session.add(material)
session.commit()

print(f"Material saved: {material.type}")
print(f"Application has {len(application.materials)} material(s)")

session.close()