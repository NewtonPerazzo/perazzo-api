import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodResponse, PaymentMethodUpdate
from app.services.payment_method import PaymentMethodService


router = APIRouter(
    prefix="/payment-methods",
    tags=["Payment Methods"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def create_payment_method(
    data: PaymentMethodCreate,
    db: Session = Depends(get_db),
):
    return PaymentMethodService(db).create(data)


@router.get("", response_model=list[PaymentMethodResponse])
def list_payment_methods(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return PaymentMethodService(db).list(skip=skip, limit=limit)


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
def get_payment_method(
    payment_method_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    payment_method = PaymentMethodService(db).get_by_id(payment_method_id)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return payment_method


@router.patch("/{payment_method_id}", response_model=PaymentMethodResponse)
def update_payment_method(
    payment_method_id: uuid.UUID,
    data: PaymentMethodUpdate,
    db: Session = Depends(get_db),
):
    service = PaymentMethodService(db)
    payment_method = service.get_by_id(payment_method_id)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return service.update(payment_method, data)


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(
    payment_method_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = PaymentMethodService(db)
    payment_method = service.get_by_id(payment_method_id)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    service.delete(payment_method)
    return None
