import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.category import CategoryCreate, CategoryReorderRequest, CategoryResponse, CategoryUpdate
from app.services.category import CategoryService


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
):
    return CategoryService(db).create(data)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return CategoryService(db).list(skip=skip, limit=limit)


@router.get("/{slug}", response_model=CategoryResponse)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    category = CategoryService(db).get_by_slug(slug)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    category = service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return service.update(category, data)


@router.post("/reorder", response_model=list[CategoryResponse])
def reorder_categories(
    data: CategoryReorderRequest,
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    try:
        return service.reorder(data.category_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    category = service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    service.delete(category)
    return None
