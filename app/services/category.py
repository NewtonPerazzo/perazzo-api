import uuid
from typing import Optional

from sqlalchemy import select
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
        stmt = select(Category).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def create(self, data: CategoryCreate) -> Category:
        slug = generate_unique_slug(data.name, self.get_by_slug)
        category = Category(
            name=data.name,
            slug=slug,
            description=data.description,
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
