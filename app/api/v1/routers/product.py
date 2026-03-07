import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product import ProductService
from app.core.dependencies import get_current_user


router = APIRouter(
  prefix="/products",
  tags=["Products"],
  dependencies=[Depends(get_current_user)]
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db)
  ):
    service = ProductService(db)
    product = service.create(data)

    return product


@router.get(
  "",
  response_model=List[ProductResponse]
)
def list_products(
  skip: int = 0,
  limit: int = 20,
  db: Session = Depends(get_db)
):
    service = ProductService(db)
    products = service.list(skip=skip, limit=limit)

    return products


@router.get(
  "/{slug}",
  response_model=ProductResponse
)
def get_product(
  slug: str,
  db: Session = Depends(get_db)
):
    service = ProductService(db)
    product = service.get_by_slug(slug)

    if not product:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Product not found"
      )

    return product


@router.patch(
  "/{product_id}",
  response_model=ProductResponse
)
def update_product(
  product_id: uuid.UUID,
  data: ProductUpdate,
  db: Session = Depends(get_db)
):
  service = ProductService(db)
  product = service.get_by_id(product_id)

  if not product:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Product not found"
      )

  updated_product = service.update(product, data)

  return updated_product


@router.delete(
  "/{product_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
def delete_product(
  product_id: uuid.UUID,
  db: Session = Depends(get_db)
):
  service = ProductService(db)
  product = service.get_by_id(product_id)

  if not product:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Product not found"
    )
  service.delete(product)

  return None
