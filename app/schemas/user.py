from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
import re


class UserCreate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    password: str
    birth_date: Optional[date] = None
    photo: Optional[str] = None

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must have at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain special character")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    birth_date: Optional[date] = None
    photo: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    birth_date: Optional[date]
    photo: Optional[str]
    is_active: bool
    is_email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True