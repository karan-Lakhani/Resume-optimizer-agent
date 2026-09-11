from src.common.schemas import UserPreferences, RemotePreference, EmploymentType

prefs = UserPreferences(
    target_roles=["Data Analyst", "Data Scientist"],
    preferred_locations=["Bangalore", "Remote"],
    remote_preference=RemotePreference.REMOTE,
    employment_type=EmploymentType.FULL_TIME,
    min_salary=600000,
)
print(prefs)

bad_prefs = UserPreferences(remote_preference="flexible")  # should fail — not a valid option