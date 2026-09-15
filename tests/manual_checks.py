from src.tracker.db import init_db, SessionLocal
from src.tracker.models import User, Profile
from src.common.schemas import ResumeProfile, PersonalInformation

init_db()

session = SessionLocal()

# create a user
user = User(name="Karan Lakhani", email="karanlakhani2712@gmail.com")
session.add(user)
session.commit()

# create a minimal resume profile
resume = ResumeProfile(
    personal_information=PersonalInformation(
        full_name="Karan Lakhani",
        email="karanlakhani2712@gmail.com",
    )
)

# save it as a profile row
profile = Profile(
    user_id=user.id,
    raw_resume_path="data/karan_lakhani.pdf",
    parsed_json=resume.model_dump(),
    summary="Aspiring data analyst with experience in Power BI and SQL.",
)
session.add(profile)
session.commit()

print(f"Profile saved with id: {profile.id}")
print(f"Belongs to user: {profile.user.name}")
print(f"User's profiles count: {len(user.profiles)}")

session.close()