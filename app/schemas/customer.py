from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    phone: str = Field(..., min_length=1, max_length=30)
    address: str | None = None
    neighborhood: str | None = None
    email: EmailStr | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=1, max_length=30)
    address: str | None = None
    neighborhood: str | None = None
    email: EmailStr | None = None


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    address: str | None
    neighborhood: str | None
    email: EmailStr | None
    delivered_orders_count: int
    delivered_total_spent: float
    orders_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
