from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from app.util.password import validate_password_rules


class UserCreate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    password: str
    birth_date: Optional[date] = None
    photo: Optional[str] = None


    @field_validator("password")
    def validate_password(cls, v):
        return validate_password_rules(v)


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


    @field_validator("password")
    def validate_password(cls, v):
        if v is None:
            return v
        return validate_password_rules(v)


class UserResponse(BaseModel):
    id: UUID
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
