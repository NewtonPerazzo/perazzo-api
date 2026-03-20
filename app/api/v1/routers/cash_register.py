import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.cash_register import (
    CashPeriodView,
    CashRegisterEntryCreate,
    CashRegisterEntryResponse,
    CashRegisterEntryUpdate,
    CashRegisterSummaryResponse,
)
from app.services.cash_register import CashRegisterService

router = APIRouter(
    prefix="/cash-register",
    tags=["Cash Register"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary", response_model=CashRegisterSummaryResponse)
def get_cash_register_summary(
    target_date: date | None = None,
    period_view: CashPeriodView = "day",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CashRegisterService(db)
    safe_date = target_date or datetime.now().date()
    return service.get_summary(current_user=current_user, target_date=safe_date, period_view=period_view)


@router.post("/entries", response_model=CashRegisterEntryResponse)
def create_cash_register_entry(
    data: CashRegisterEntryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return CashRegisterService(db).create_entry(current_user=current_user, data=data)


@router.patch("/entries/{entry_id}", response_model=CashRegisterEntryResponse)
def update_cash_register_entry(
    entry_id: uuid.UUID,
    data: CashRegisterEntryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return CashRegisterService(db).update_entry(
        current_user=current_user,
        entry_id=entry_id,
        data=data,
    )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cash_register_entry(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    CashRegisterService(db).delete_entry(current_user=current_user, entry_id=entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
