import json

from src.job_application.profile_service import save_parsed_profile
from src.tracker.db import init_db

init_db()
profile = save_parsed_profile("data/karan_lakhani.pdf")

print(f"Saved to database: profile id={profile.id}, user_id={profile.user_id}")
print(f"Source PDF: {profile.raw_resume_path}")
print()
print(json.dumps(profile.parsed_json, indent=2))
