"""
Profile persistence — takes a parsed ResumeProfile and stores it
against the local user's Profile row.

This app is single-user (local tool), so there is one implicit
"default" user rather than a login system.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from src.common.schemas import ResumeProfile
from src.job_application.resume_parser import parse_resume
from src.tracker.db import SessionLocal
from src.tracker.models import Profile, User

DEFAULT_USER_NAME = "Default User"


def get_or_create_default_user(session: Session) -> User:
    user = session.query(User).first()
    if user is None:
        user = User(name=DEFAULT_USER_NAME)
        session.add(user)
        session.flush()
    return user


def save_parsed_profile(pdf_path: str, session: Session | None = None) -> Profile:
    """
    Parse the resume at pdf_path and upsert it into the user's Profile row.
    """
    owns_session = session is None
    session = session or SessionLocal()

    try:
        resume_profile: ResumeProfile = parse_resume(pdf_path)
        user = get_or_create_default_user(session)

        profile = session.query(Profile).filter_by(user_id=user.id).first()
        if profile is None:
            profile = Profile(user_id=user.id)
            session.add(profile)

        profile.raw_resume_path = pdf_path
        profile.parsed_json = resume_profile.model_dump(mode="json")
        profile.summary = resume_profile.summary
        profile.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(profile)
        return profile
    finally:
        if owns_session:
            session.close()


def get_current_profile(session: Session | None = None) -> Profile | None:
    owns_session = session is None
    session = session or SessionLocal()

    try:
        user = session.query(User).first()
        if user is None:
            return None
        return session.query(Profile).filter_by(user_id=user.id).first()
    finally:
        if owns_session:
            session.close()
