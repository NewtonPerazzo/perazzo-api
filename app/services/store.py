import uuid
from fastapi import HTTPException, status

from app.domain.models.store import Store
from app.domain.repositories.store import StoreRepository
from app.schemas.store import StoreCreate, StoreUpdate
from app.util.slug import generate_unique_slug
from app.util.store_hours import (
  DAY_KEYS,
  WEEKDAY_TO_KEY,
  default_business_hours,
  is_open_now,
  normalize_business_hours,
  validate_business_hours,
)


class StoreService:
  def __init__(self, db):
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
      logo=data.logo,
      color=data.color,
      has_catalog_active=data.has_catalog_active,
      is_accepted_send_order_to_whatsapp=data.is_accepted_send_order_to_whatsapp,
      business_hours=self._validate_and_normalize_business_hours(data.business_hours),
      user_id=current_user.id
    )

    return self.repository.create(store)

  def update(self, store: Store, data: StoreUpdate):
    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] and update_data["name"] != store.name:
      store.slug = generate_unique_slug(update_data["name"], self.repository.get_by_slug)

    if "business_hours" in update_data:
      store.business_hours = self._validate_and_normalize_business_hours(update_data.get("business_hours"))

    for field, value in update_data.items():
      if field == "business_hours":
        continue
      setattr(store, field, value)

    return self.repository.update(store)

  def get_by_slug(self, slug: str):
    return self.repository.get_by_slug(slug)

  def get_by_user_id(self, user_id: uuid.UUID):
    return self.repository.get_by_user_id(user_id)

  def is_open_now(self, store: Store) -> bool:
    return is_open_now(store.business_hours)

  def toggle_today_open(self, store: Store, should_open: bool) -> Store:
    hours = normalize_business_hours(store.business_hours)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    day_key = WEEKDAY_TO_KEY[datetime.now(ZoneInfo("America/Sao_Paulo")).weekday()]
    day_item = hours.get(day_key, {})
    hours[day_key] = {
      "enabled": should_open,
      "start_time": day_item.get("start_time"),
      "end_time": day_item.get("end_time"),
    }
    validate_business_hours(hours)
    store.business_hours = hours
    return self.repository.update(store)

  def serialize(self, store: Store) -> dict:
    return {
      "id": store.id,
      "name": store.name,
      "slug": store.slug,
      "description": store.description,
      "does_delivery": store.does_delivery,
      "does_pick_up": store.does_pick_up,
      "phone": store.phone,
      "whatsapp": store.whatsapp,
      "address": store.address,
      "instagram": store.instagram,
      "email": store.email,
      "logo": store.logo,
      "color": store.color,
      "has_catalog_active": store.has_catalog_active,
      "is_accepted_send_order_to_whatsapp": store.is_accepted_send_order_to_whatsapp,
      "business_hours": normalize_business_hours(store.business_hours),
      "is_open_now": self.is_open_now(store),
      "user_id": store.user_id,
      "created_at": store.created_at,
    }

  def _validate_and_normalize_business_hours(self, value: dict | None) -> dict:
    hours = normalize_business_hours(value)
    try:
      validate_business_hours(hours)
    except ValueError as exc:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return hours
