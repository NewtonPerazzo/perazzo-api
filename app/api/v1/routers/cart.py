import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.cart import CartCreate, CartPatch, CartProductsReplace, CartResponse
from app.schemas.order import OrderResponse
from app.services.cart import CartService


router = APIRouter(
    prefix="/carts",
    tags=["Carts"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(
    data: CartCreate,
    db: Session = Depends(get_db),
):
    cart = CartService(db).create(data)
    return CartService(db).serialize(cart)


@router.get("", response_model=list[CartResponse])
def list_carts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    service = CartService(db)
    carts = service.list(skip=skip, limit=limit)
    return [service.serialize(cart) for cart in carts]


@router.get("/{cart_id}", response_model=CartResponse)
def get_cart(
    cart_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return service.serialize(cart)


@router.patch("/{cart_id}", response_model=CartResponse)
def patch_cart(
    cart_id: uuid.UUID,
    data: CartPatch,
    db: Session = Depends(get_db),
):
    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    updated = service.patch(cart, data)
    return service.serialize(updated)


@router.put("/{cart_id}/products", response_model=CartResponse)
def replace_cart_products(
    cart_id: uuid.UUID,
    data: CartProductsReplace,
    db: Session = Depends(get_db),
):
    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    updated = service.replace_products(cart, data.products)
    if updated is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return service.serialize(updated)


@router.post("/{cart_id}/checkout", response_model=OrderResponse)
def checkout_cart(
    cart_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return service.checkout(cart)


@router.delete("/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart(
    cart_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = CartService(db)
    cart = service.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    service.delete(cart)
    return None
