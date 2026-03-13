from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentMethodCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class PaymentMethodUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class PaymentMethodResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
