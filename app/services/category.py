import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.util.slug import generate_unique_slug


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        stmt = select(Category).where(Category.id == category_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Optional[Category]:
        stmt = select(Category).where(Category.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, skip: int = 0, limit: int = 20) -> list[Category]:
        stmt = (
            select(Category)
            .order_by(Category.sort_order.asc(), Category.name.asc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def create(self, data: CategoryCreate) -> Category:
        slug = generate_unique_slug(data.name, self.get_by_slug)
        max_order = self.db.execute(select(func.max(Category.sort_order))).scalar_one_or_none()
        next_order = int(max_order or 0) + 1
        category = Category(
            name=data.name,
            slug=slug,
            description=data.description,
            sort_order=next_order,
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category, data: CategoryUpdate) -> Category:
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] and update_data["name"] != category.name:
            category.slug = generate_unique_slug(update_data["name"], self.get_by_slug)

        for field, value in update_data.items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()

    def reorder(self, category_ids: List[uuid.UUID]) -> List[Category]:
        if not category_ids:
            return self.list(skip=0, limit=200)

        existing_ids = set(
            self.db.execute(select(Category.id).where(Category.id.in_(category_ids))).scalars().all()
        )
        if len(existing_ids) != len(set(category_ids)):
            raise ValueError("One or more categories were not found")

        for index, category_id in enumerate(category_ids):
            category = self.get_by_id(category_id)
            if category:
                category.sort_order = index + 1

        self.db.commit()
        return self.list(skip=0, limit=200)
