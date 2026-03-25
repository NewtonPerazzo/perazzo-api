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
    current_user=Depends(get_current_user),
):
    return CategoryService(db).create(data, current_user=current_user)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return CategoryService(db).list(skip=skip, limit=limit, current_user=current_user)


@router.get("/{slug}", response_model=CategoryResponse)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    category = CategoryService(db).get_by_slug(slug, current_user=current_user)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CategoryService(db)
    category = service.get_by_id(category_id, current_user=current_user)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return service.update(category, data, current_user=current_user)


@router.post("/reorder", response_model=list[CategoryResponse])
def reorder_categories(
    data: CategoryReorderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CategoryService(db)
    try:
        return service.reorder(data.category_ids, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CategoryService(db)
    category = service.get_by_id(category_id, current_user=current_user)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    service.delete(category, current_user=current_user)
    return None
