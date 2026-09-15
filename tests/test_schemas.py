from src.common.schemas import (
    PersonalInformation,
    SkillEntry,
    EvidenceLevel,
    ExperienceEntry,
    ResumeProfile,
    UserPreferences,
    RemotePreference,
    EmploymentType,
)
import pytest
from pydantic import ValidationError


def test_personal_information_valid():
    p = PersonalInformation(full_name="Karan Lakhani", email="karan@example.com")
    assert p.full_name == "Karan Lakhani"
    assert p.email == "karan@example.com"
    assert p.phone is None


def test_personal_information_requires_full_name():
    with pytest.raises(ValidationError):
        PersonalInformation()


def test_personal_information_invalid_email():
    with pytest.raises(ValidationError):
        PersonalInformation(full_name="Karan", email="not-an-email")


def test_skill_entry_defaults_to_weak():
    skill = SkillEntry(name="Python")
    assert skill.evidence_level == EvidenceLevel.WEAK


def test_skill_entry_invalid_evidence_level():
    with pytest.raises(ValidationError):
        SkillEntry(name="Python", evidence_level="expert")


def test_experience_entry_valid():
    exp = ExperienceEntry(
        job_title="Data Analyst",
        company="Acme Corp",
        start_date="Feb 2025",
        is_current=True,
    )
    assert exp.is_current is True
    assert exp.responsibilities == []


def test_resume_profile_assembled():
    resume = ResumeProfile(
        personal_information=PersonalInformation(full_name="Karan Lakhani")
    )
    assert resume.personal_information.full_name == "Karan Lakhani"
    assert resume.skills == []
    assert resume.experience == []


def test_user_preferences_enums():
    prefs = UserPreferences(
        remote_preference=RemotePreference.ANY,
        employment_type=EmploymentType.FULL_TIME,
    )
    assert prefs.remote_preference == RemotePreference.ANY


def test_user_preferences_invalid_enum():
    with pytest.raises(ValidationError):
        UserPreferences(remote_preference="flexible")