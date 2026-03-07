import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.store import Store
from app.domain.repositories.store import StoreRepository
from app.schemas.store import StoreCreate
from app.util.slug import generate_unique_slug


class StoreService:
  def __init__(self, db: Session):
    self.repository = StoreRepository(db)

  def create(self, data: StoreCreate, current_user):
    existing_store = self.repository.get_by_user_id(current_user.id)

    if existing_store:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User already has a store"
      )

    slug = generate_unique_slug(data.name, self.repository.get_by_slug)

    store = Store(
      name=data.name,
      slug=slug,
      description=data.description,
      does_delivery=data.does_delivery,
      does_pick_up=data.does_pick_up,
      phone=data.phone,
      whatsapp=data.whatsapp,
      address=data.address,
      instagram=data.instagram,
      email=data.email,
      logo=str(data.logo) if data.logo else None,
      color=data.color,
      has_catalog_active=data.has_catalog_active,
      user_id=current_user.id
    )

    return self.repository.create(store)

  def get_by_slug(self, slug: str):
    return self.repository.get_by_slug(slug)

  def get_by_user_id(self, user_id: uuid.UUID):
    return self.repository.get_by_user_id(user_id)
