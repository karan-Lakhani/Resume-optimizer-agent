from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr


class Link(BaseModel):
    label: str   # e.g. "GitHub", "Portfolio", "LinkedIn"
    url: str


class PersonalInformation(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None