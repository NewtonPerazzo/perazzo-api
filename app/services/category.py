import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models.category import Category
from fastapi import HTTPException, status
from app.services.store import StoreService
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.util.slug import generate_unique_slug


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self, category_id: uuid.UUID, *, current_user=None, store_id: uuid.UUID | None = None
    ) -> Optional[Category]:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(Category).where(Category.id == category_id, Category.store_id == scope_store_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(
        self, slug: str, *, current_user=None, store_id: uuid.UUID | None = None
    ) -> Optional[Category]:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(Category).where(Category.slug == slug, Category.store_id == scope_store_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self, skip: int = 0, limit: int = 20, *, current_user=None, store_id: uuid.UUID | None = None
    ) -> list[Category]:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = (
            select(Category)
            .where(Category.store_id == scope_store_id)
            .order_by(Category.sort_order.asc(), Category.name.asc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def create(self, data: CategoryCreate, *, current_user=None, store_id: uuid.UUID | None = None) -> Category:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        slug = generate_unique_slug(
            data.name,
            lambda value: self.get_by_slug(value, store_id=scope_store_id),
        )
        max_order = self.db.execute(
            select(func.max(Category.sort_order)).where(Category.store_id == scope_store_id)
        ).scalar_one_or_none()
        next_order = int(max_order or 0) + 1
        category = Category(
            store_id=scope_store_id,
            name=data.name,
            slug=slug,
            description=data.description,
            sort_order=next_order,
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category, data: CategoryUpdate, *, current_user=None, store_id: uuid.UUID | None = None) -> Category:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if category.store_id != scope_store_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] and update_data["name"] != category.name:
            category.slug = generate_unique_slug(
                update_data["name"],
                lambda value: self.get_by_slug(value, store_id=scope_store_id),
            )

        for field, value in update_data.items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category, *, current_user=None, store_id: uuid.UUID | None = None) -> None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if category.store_id != scope_store_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        self.db.delete(category)
        self.db.commit()

    def reorder(self, category_ids: List[uuid.UUID], *, current_user=None, store_id: uuid.UUID | None = None) -> List[Category]:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if not category_ids:
            return self.list(skip=0, limit=200, store_id=scope_store_id)

        existing_ids = set(
            self.db.execute(
                select(Category.id).where(Category.id.in_(category_ids), Category.store_id == scope_store_id)
            ).scalars().all()
        )
        if len(existing_ids) != len(set(category_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more categories were not found")

        for index, category_id in enumerate(category_ids):
            category = self.get_by_id(category_id, store_id=scope_store_id)
            if category:
                category.sort_order = index + 1

        self.db.commit()
        return self.list(skip=0, limit=200, store_id=scope_store_id)

    def _resolve_store_id(self, *, current_user=None, store_id: uuid.UUID | None = None) -> uuid.UUID:
        if store_id:
            return store_id
        if not current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store scope is required")
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return store.id
