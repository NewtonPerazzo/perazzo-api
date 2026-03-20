import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.courier import (
    CourierAdjustmentCreate,
    CourierAdjustmentResponse,
    CourierAdjustmentUpdate,
    CourierCreate,
    CourierPeriodView,
    CourierResponse,
    CourierSummaryResponse,
    CourierUpdate,
)
from app.services.courier import CourierService


router = APIRouter(
    prefix="/couriers",
    tags=["Couriers"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=CourierResponse, status_code=status.HTTP_201_CREATED)
def create_courier(
    data: CourierCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return CourierService(db).create(current_user=current_user, data=data)


@router.get("", response_model=list[CourierResponse])
def list_couriers(
    response: Response,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CourierService(db)
    couriers = service.list(current_user=current_user, skip=skip, limit=limit, search=search)
    total = service.count(current_user=current_user, search=search)
    response.headers["X-Total-Count"] = str(total)
    return couriers


@router.patch("/{courier_id}", response_model=CourierResponse)
def update_courier(
    courier_id: uuid.UUID,
    data: CourierUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CourierService(db)
    courier = service.get_by_id(current_user=current_user, courier_id=courier_id)
    if not courier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier not found")
    return service.update(courier=courier, data=data)


@router.delete("/{courier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_courier(
    courier_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CourierService(db)
    courier = service.get_by_id(current_user=current_user, courier_id=courier_id)
    if not courier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier not found")
    service.delete(courier)
    return None


@router.post("/adjustments", response_model=CourierAdjustmentResponse, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    data: CourierAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return CourierService(db).create_adjustment(current_user=current_user, data=data)


@router.patch("/adjustments/{adjustment_id}", response_model=CourierAdjustmentResponse)
def update_adjustment(
    adjustment_id: uuid.UUID,
    data: CourierAdjustmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return CourierService(db).update_adjustment(
        current_user=current_user,
        adjustment_id=adjustment_id,
        data=data,
    )


@router.delete("/adjustments/{adjustment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_adjustment(
    adjustment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    CourierService(db).delete_adjustment(current_user=current_user, adjustment_id=adjustment_id)
    return None


@router.get("/summary", response_model=CourierSummaryResponse)
def get_couriers_summary(
    target_date: date | None = None,
    period_view: CourierPeriodView = "day",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CourierService(db)
    resolved_date = target_date or datetime.now().date()
    return service.get_summary(
        current_user=current_user,
        target_date=resolved_date,
        period_view=period_view,
    )

