from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CourierPeriodView = Literal["day", "week", "month", "year"]
CourierAdjustmentType = Literal["add", "remove"]


class CourierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)


class CourierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=255)


class CourierResponse(BaseModel):
    id: UUID
    name: str
    address: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourierAdjustmentCreate(BaseModel):
    adjustment_type: CourierAdjustmentType
    amount: float = Field(..., gt=0)
    courier_id: UUID | None = None
    payment_method: str | None = Field(default=None, max_length=60)
    note: str | None = Field(default=None, max_length=255)
    occurred_on: date | None = None


class CourierAdjustmentUpdate(BaseModel):
    adjustment_type: CourierAdjustmentType | None = None
    amount: float | None = Field(default=None, gt=0)
    courier_id: UUID | None = None
    payment_method: str | None = Field(default=None, max_length=60)
    note: str | None = Field(default=None, max_length=255)
    occurred_on: date | None = None


class CourierAdjustmentResponse(BaseModel):
    id: UUID
    adjustment_type: CourierAdjustmentType
    amount: float
    courier_id: UUID | None
    payment_method: str | None
    note: str | None
    occurred_on: date
    created_at: datetime
    updated_at: datetime
    courier: CourierResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class CourierTotalsResponse(BaseModel):
    deliveries_count: int
    deliveries_amount: float
    adjustments_total: float
    total_earnings: float


class CourierSummaryItemResponse(BaseModel):
    courier: CourierResponse | None
    totals: CourierTotalsResponse


class CourierSummaryResponse(BaseModel):
    period_view: CourierPeriodView
    period_start: date
    period_end: date
    target_date: date
    riders: list[CourierSummaryItemResponse]
    unassigned: CourierSummaryItemResponse
    adjustments: list[CourierAdjustmentResponse]
    totals: CourierTotalsResponse

