import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderTotalPreviewRequest,
    OrderTotalPreviewResponse,
    OrderUpdate,
)
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
    current_user=Depends(get_current_user),
):
    order = OrderService(db).create(current_user=current_user, data=data)
    return OrderService(db).serialize(order)


@router.get("", response_model=list[OrderResponse])
def list_orders(
    response: Response,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    order_date: date | None = None,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    orders = service.list(skip=skip, limit=limit, search=search, order_date=order_date)
    total = service.count(search=search, order_date=order_date)
    response.headers["X-Total-Count"] = str(total)
    return [service.serialize(order) for order in orders]


@router.post("/preview-total", response_model=OrderTotalPreviewResponse)
def preview_order_total(
    data: OrderTotalPreviewRequest,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    total = service.preview_total_with_delivery(
        products=data.products,
        is_to_deliver=data.is_to_deliver,
        delivery_method_id=data.delivery_method_id,
    )
    return {"total_price": total}


@router.get("/search", response_model=list[OrderResponse])
def search_orders(
    response: Response,
    q: str,
    skip: int = 0,
    limit: int = 20,
    order_date: date | None = None,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    orders = service.list(skip=skip, limit=limit, search=q, order_date=order_date)
    total = service.count(search=q, order_date=order_date)
    response.headers["X-Total-Count"] = str(total)
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


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: uuid.UUID,
    data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    order = service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    updated = service.update(current_user=current_user, order=order, data=data)
    return service.serialize(updated)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    order = service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    service.delete(order)
    return None


@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    order = service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    updated = service.update_status(order, data.status)
    return service.serialize(updated)
