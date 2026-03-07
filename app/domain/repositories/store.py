import uuid
from sqlalchemy.orm import Session

from app.domain.models.store import Store


class StoreRepository:
  def __init__(self, db: Session):
    self.db = db

  def create(self, store: Store):
    self.db.add(store)
    self.db.commit()
    self.db.refresh(store)

    return store

  def get_by_slug(self, slug: str):
    return self.db.query(Store).filter(Store.slug == slug).first()

  def get_by_user_id(self, user_id: uuid.UUID):
    return self.db.query(Store).filter(Store.user_id == user_id).first()
