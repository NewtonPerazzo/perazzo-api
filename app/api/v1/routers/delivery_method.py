import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.delivery_method import (
    DeliveryMethodCreate,
    DeliveryMethodResponse,
    DeliveryMethodUpdate,
)
from app.services.delivery_method import DeliveryMethodService


router = APIRouter(
    prefix="/delivery-methods",
    tags=["Delivery Methods"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=DeliveryMethodResponse, status_code=status.HTTP_201_CREATED)
def create_delivery_method(
    data: DeliveryMethodCreate,
    db: Session = Depends(get_db),
):
    return DeliveryMethodService(db).create(data)


@router.get("", response_model=list[DeliveryMethodResponse])
def list_delivery_methods(
    response: Response,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    service = DeliveryMethodService(db)
    items = service.list(skip=skip, limit=limit, search=search)
    total = service.count(search=search)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{delivery_method_id}", response_model=DeliveryMethodResponse)
def get_delivery_method(
    delivery_method_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    method = DeliveryMethodService(db).get_by_id(delivery_method_id)
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery method not found")
    return method


@router.patch("/{delivery_method_id}", response_model=DeliveryMethodResponse)
def update_delivery_method(
    delivery_method_id: uuid.UUID,
    data: DeliveryMethodUpdate,
    db: Session = Depends(get_db),
):
    service = DeliveryMethodService(db)
    method = service.get_by_id(delivery_method_id)
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery method not found")
    return service.update(method, data)


@router.delete("/{delivery_method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery_method(
    delivery_method_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = DeliveryMethodService(db)
    method = service.get_by_id(delivery_method_id)
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery method not found")
    service.delete(method)
    return None
