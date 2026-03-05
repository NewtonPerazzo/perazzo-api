from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select
from slugify import slugify

from app.domain.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:

  def __init__(self, db: Session):
    self.db = db


  def get_by_id(self, product_id: int) -> Optional[Product]:
    stmt = select(Product).where(Product.id == product_id)
    result = self.db.execute(stmt).scalar_one_or_none()
    return result


  def get_by_slug(self, slug: str) -> Optional[Product]:
      stmt = select(Product).where(Product.slug == slug)
      result = self.db.execute(stmt).scalar_one_or_none()
      return result


  def list(self, skip: int = 0, limit: int = 20) -> List[Product]:
    stmt = (
      select(Product)
      .offset(skip)
      .limit(limit)
    )

    result = self.db.execute(stmt).scalars().all()
    return result


  def create(self, data: ProductCreate) -> Product:

    slug = self._generate_unique_slug(data.name)

    product = Product(
      name=data.name,
      slug=slug,
      price=data.price,
      description=data.description,
      stock=data.stock,
      image_url=data.image_url
    )

    self.db.add(product)
    self.db.commit()
    self.db.refresh(product)

    return product


  def update(self, product: Product, data: ProductUpdate) -> Product:

    if data.name and data.name != product.name:
        product.slug = self._generate_unique_slug(data.name)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    self.db.commit()
    self.db.refresh(product)

    return product


  def delete(self, product: Product) -> None:
    self.db.delete(product)
    self.db.commit()


  def _generate_unique_slug(self, name: str) -> str:

    base_slug = slugify(name)
    slug = base_slug
    counter = 1

    while self.get_by_slug(slug):
      slug = f"{base_slug}-{counter}"
      counter += 1

    return slug