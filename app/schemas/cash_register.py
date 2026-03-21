from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CashEntryType = Literal["entry", "expense"]
CashPeriodView = Literal["day", "week", "month", "year"]


class CashRegisterEntryCreate(BaseModel):
    entry_type: CashEntryType
    name: str = Field(..., min_length=1, max_length=140)
    amount: float = Field(..., gt=0)
    payment_method: str | None = Field(default=None, max_length=60)
    is_profit: bool = False
    note: str | None = None
    occurred_on: date | None = None


class CashRegisterEntryUpdate(BaseModel):
    entry_type: CashEntryType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=140)
    amount: float | None = Field(default=None, gt=0)
    payment_method: str | None = Field(default=None, max_length=60)
    is_profit: bool | None = None
    note: str | None = None
    occurred_on: date | None = None


class CashRegisterEntryResponse(BaseModel):
    id: UUID
    entry_type: CashEntryType
    name: str
    amount: float
    payment_method: str | None
    is_profit: bool
    note: str | None
    occurred_on: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CashRegisterOrderAutoEntryResponse(BaseModel):
    name: str
    amount: float
    payment_method: str


class CashRegisterByPaymentResponse(BaseModel):
    payment_method: str
    entries: float
    expenses: float
    net: float


class CashRegisterTotalsResponse(BaseModel):
    auto_entries: float
    auto_entries_with_delivery: float
    delivery_total: float
    manual_entries: float
    entries_total: float
    expenses_total: float
    profits_total: float
    balance: float


class CashRegisterSummaryResponse(BaseModel):
    period_view: CashPeriodView
    period_start: date
    period_end: date
    target_date: date
    auto_entries: list[CashRegisterOrderAutoEntryResponse]
    manual_entries: list[CashRegisterEntryResponse]
    manual_expenses: list[CashRegisterEntryResponse]
    profit_entries: list[CashRegisterEntryResponse]
    by_payment_method: list[CashRegisterByPaymentResponse]
    totals: CashRegisterTotalsResponse
