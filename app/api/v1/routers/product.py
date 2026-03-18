import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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
  response: Response,
  skip: int = 0,
  limit: int = 20,
  search: str | None = None,
  category_id: uuid.UUID | None = None,
  sort_by: str | None = "created_at",
  sort_order: str | None = "desc",
  db: Session = Depends(get_db)
):
    service = ProductService(db)
    total = service.count(search=search, category_id=category_id)
    products = service.list(
      skip=skip,
      limit=limit,
      search=search,
      category_id=category_id,
      sort_by=sort_by,
      sort_order=sort_order,
    )

    response.headers["X-Total-Count"] = str(total)

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
  try:
    service.delete(product)
  except IntegrityError:
    db.rollback()
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Product cannot be deleted because it is linked to existing orders"
    )

  return None
