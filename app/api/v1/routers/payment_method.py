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
    current_user=Depends(get_current_user),
):
    return PaymentMethodService(db).create(data, current_user=current_user)


@router.get("", response_model=list[PaymentMethodResponse])
def list_payment_methods(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return PaymentMethodService(db).list(skip=skip, limit=limit, current_user=current_user)


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
def get_payment_method(
    payment_method_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payment_method = PaymentMethodService(db).get_by_id(payment_method_id, current_user=current_user)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return payment_method


@router.patch("/{payment_method_id}", response_model=PaymentMethodResponse)
def update_payment_method(
    payment_method_id: uuid.UUID,
    data: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = PaymentMethodService(db)
    payment_method = service.get_by_id(payment_method_id, current_user=current_user)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    return service.update(payment_method, data, current_user=current_user)


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(
    payment_method_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = PaymentMethodService(db)
    payment_method = service.get_by_id(payment_method_id, current_user=current_user)
    if not payment_method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    service.delete(payment_method, current_user=current_user)
    return None
