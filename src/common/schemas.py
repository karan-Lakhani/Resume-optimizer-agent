from __future__ import annotations


from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import date


class Link(BaseModel):
    label: str   # e.g. "GitHub", "Portfolio", "LinkedIn"
    url: str


class PersonalInformation(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None



class EvidenceLevel(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class SkillEntry(BaseModel):
    name: str
    category: Optional[str] = None
    evidence_level: EvidenceLevel = EvidenceLevel.WEAK
    source_evidence: list[str] = []


class ExperienceEntry(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    responsibilities: list[str] = []
    technologies: list[str] = []

class EducationEntry(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_present: bool = False
    coursework: list[str] = []

class CertificationEntry(BaseModel):
    name: str
    issuer: Optional[str] = None
    date_earned: Optional[str] = None
    credential_id: Optional[str] = None

class ProjectEntry(BaseModel):
    name: str
    description: list[str] = None
    technologies: list[str] = []
    link: Optional[str] = None