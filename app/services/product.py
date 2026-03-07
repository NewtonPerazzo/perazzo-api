import uuid
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.models.category import Category
from app.domain.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.util.slug import generate_unique_slug

class ProductService:

  def __init__(self, db: Session):
    self.db = db


  def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
    stmt = (
      select(Product)
      .options(selectinload(Product.categories))
      .where(Product.id == product_id)
    )
    result = self.db.execute(stmt).scalar_one_or_none()
    return result


  def get_by_slug(self, slug: str) -> Optional[Product]:
      stmt = (
        select(Product)
        .options(selectinload(Product.categories))
        .where(Product.slug == slug)
      )
      result = self.db.execute(stmt).scalar_one_or_none()
      return result


  def list(self, skip: int = 0, limit: int = 20) -> List[Product]:
    stmt = (
      select(Product)
      .options(selectinload(Product.categories))
      .offset(skip)
      .limit(limit)
    )

    result = self.db.execute(stmt).scalars().all()
    return result


  def create(self, data: ProductCreate) -> Product:
    slug = generate_unique_slug(data.name, self.get_by_slug)
    categories = self._get_categories_by_ids(data.category_ids)

    product = Product(
      name=data.name,
      slug=slug,
      price=data.price,
      description=data.description,
      stock=data.stock,
      image_url=data.image_url,
      categories=categories,
    )

    self.db.add(product)
    self.db.commit()
    self.db.refresh(product)

    return product


  def update(self, product: Product, data: ProductUpdate) -> Product:

    if data.name and data.name != product.name:
        product.slug = generate_unique_slug(data.name, self.get_by_slug)

    update_data = data.model_dump(exclude_unset=True)

    if "category_ids" in update_data:
      product.categories = self._get_categories_by_ids(update_data.pop("category_ids"))

    for field, value in update_data.items():
        setattr(product, field, value)

    self.db.commit()
    self.db.refresh(product)

    return product


  def delete(self, product: Product) -> None:
    self.db.delete(product)
    self.db.commit()


  def _get_categories_by_ids(self, category_ids: Optional[List[uuid.UUID]]) -> List[Category]:
    if not category_ids:
      return []

    unique_ids = list(dict.fromkeys(category_ids))
    stmt = select(Category).where(Category.id.in_(unique_ids))
    categories = self.db.execute(stmt).scalars().all()

    if len(categories) != len(unique_ids):
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="One or more categories were not found",
      )

    return categories
