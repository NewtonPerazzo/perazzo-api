from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryMethodCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    price: float = Field(..., ge=0)
    description: str | None = None


class DeliveryMethodUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    price: float = Field(..., ge=0)
    description: str | None = None


class DeliveryMethodResponse(BaseModel):
    id: UUID
    name: str
    price: float
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
