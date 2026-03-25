import uuid
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func, delete
from sqlalchemy.orm import selectinload

from app.domain.models.cart_item import CartItem
from app.domain.models.category import Category
from app.domain.models.product import Product
from app.services.store import StoreService
from app.schemas.product import ProductCreate, ProductUpdate
from app.util.slug import generate_unique_slug


class ProductService:

  def __init__(self, db: Session):
    self.db = db


  def get_by_id(self, product_id: uuid.UUID, *, current_user=None, store_id: uuid.UUID | None = None) -> Optional[Product]:
    scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
    stmt = (
      select(Product)
      .options(selectinload(Product.categories))
      .where(Product.id == product_id, Product.store_id == scope_store_id)
    )
    result = self.db.execute(stmt).scalar_one_or_none()
    return result


  def get_by_slug(self, slug: str, *, current_user=None, store_id: uuid.UUID | None = None) -> Optional[Product]:
      scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
      stmt = (
        select(Product)
        .options(selectinload(Product.categories))
        .where(Product.slug == slug, Product.store_id == scope_store_id)
      )
      result = self.db.execute(stmt).scalar_one_or_none()
      return result


  def list(
    self,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    uncategorized: bool = False,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
    catalog_mode: bool = False,
    only_active: bool = True,
    current_user=None,
    store_id: uuid.UUID | None = None,
  ) -> List[Product]:
    scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
    stmt = select(Product).options(selectinload(Product.categories))
    stmt = self._apply_filters(
      stmt,
      store_id=scope_store_id,
      search=search,
      category_id=category_id,
      uncategorized=uncategorized,
      catalog_mode=catalog_mode,
      only_active=only_active
    )
    stmt = self._apply_sorting(stmt, sort_by=sort_by, sort_order=sort_order)
    stmt = stmt.offset(skip).limit(limit)

    result = self.db.execute(stmt).scalars().all()
    return result


  def count(
    self,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    uncategorized: bool = False,
    catalog_mode: bool = False,
    only_active: bool = True,
    current_user=None,
    store_id: uuid.UUID | None = None,
  ) -> int:
    scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
    stmt = select(func.count(Product.id))
    stmt = self._apply_filters(
      stmt,
      store_id=scope_store_id,
      search=search,
      category_id=category_id,
      uncategorized=uncategorized,
      catalog_mode=catalog_mode,
      only_active=only_active
    )

    result = self.db.execute(stmt).scalar_one()
    return int(result)


  def create(self, data: ProductCreate, *, current_user=None, store_id: uuid.UUID | None = None) -> Product:
    scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
    slug = generate_unique_slug(data.name, lambda value: self.get_by_slug(value, store_id=scope_store_id))
    categories = self._get_categories_by_ids(data.category_ids, store_id=scope_store_id)

    product = Product(
      store_id=scope_store_id,
      name=data.name,
      slug=slug,
      price=data.price,
      description=data.description,
      stock=data.stock,
      image_url=data.image_url,
      is_active=data.is_active,
      categories=categories,
    )

    if product.stock == 0:
      product.is_active = False

    self.db.add(product)
    self.db.commit()
    self.db.refresh(product)

    return product


  def update(self, product: Product, data: ProductUpdate, *, current_user=None, store_id: uuid.UUID | None = None) -> Product:
    scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
    if product.store_id != scope_store_id:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if data.name and data.name != product.name:
        product.slug = generate_unique_slug(data.name, lambda value: self.get_by_slug(value, store_id=scope_store_id))

    update_data = data.model_dump(exclude_unset=True)

    if "category_ids" in update_data:
      product.categories = self._get_categories_by_ids(update_data.pop("category_ids"), store_id=scope_store_id)

    for field, value in update_data.items():
        setattr(product, field, value)

    if product.stock == 0:
      product.is_active = False

    self.db.commit()
    self.db.refresh(product)

    return product


  def delete(self, product: Product, *, current_user=None, store_id: uuid.UUID | None = None) -> None:
    scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
    if product.store_id != scope_store_id:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.is_active = False
    self.db.execute(delete(CartItem).where(CartItem.product_id == product.id))
    self.db.commit()


  def _apply_filters(
    self,
    stmt,
    store_id: uuid.UUID,
    search: str | None,
    category_id: uuid.UUID | None,
    uncategorized: bool = False,
    catalog_mode: bool = False,
    only_active: bool = True
  ):
    stmt = stmt.where(Product.store_id == store_id)

    if only_active:
      stmt = stmt.where(Product.is_active.is_(True))

    if catalog_mode:
      stmt = stmt.where(
        or_(
          Product.stock.is_(None),
          Product.stock > 0
        )
      )

    if search:
      search_term = f"%{search}%"
      stmt = stmt.where(
        or_(
          Product.name.ilike(search_term),
          Product.description.ilike(search_term)
        )
      )

    if uncategorized:
      stmt = stmt.where(~Product.categories.any())
    elif category_id:
      stmt = stmt.where(Product.categories.any(Category.id == category_id))

    return stmt


  def _apply_sorting(self, stmt, sort_by: str | None, sort_order: str | None):
    descending = (sort_order or "desc").lower() != "asc"
    if sort_by == "name":
      return stmt.order_by(Product.name.desc() if descending else Product.name.asc())
    if sort_by == "price":
      return stmt.order_by(Product.price.desc() if descending else Product.price.asc())
    return stmt.order_by(Product.created_at.desc() if descending else Product.created_at.asc())


  def _get_categories_by_ids(self, category_ids: Optional[List[uuid.UUID]], *, store_id: uuid.UUID) -> List[Category]:
    if not category_ids:
      return []

    unique_ids = list(dict.fromkeys(category_ids))
    stmt = select(Category).where(Category.id.in_(unique_ids), Category.store_id == store_id)
    categories = self.db.execute(stmt).scalars().all()

    if len(categories) != len(unique_ids):
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="One or more categories were not found",
      )

    return categories

  def _resolve_store_id(self, *, current_user=None, store_id: uuid.UUID | None = None) -> uuid.UUID:
    if store_id:
      return store_id
    if not current_user:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store scope is required")
    store = StoreService(self.db).get_by_user_id(current_user.id)
    if not store:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store.id
