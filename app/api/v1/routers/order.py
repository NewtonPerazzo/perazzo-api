import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order import OrderService


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
):
    order = OrderService(db).create(data)
    return OrderService(db).serialize(order)


@router.get("", response_model=list[OrderResponse])
def list_orders(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    orders = service.list(skip=skip, limit=limit)
    return [service.serialize(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    order = service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return service.serialize(order)
