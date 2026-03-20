from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.store import StoreCreate, StoreResponse, StoreTodayOpenToggle, StoreUpdate
from app.services.store import StoreService

router = APIRouter(
  prefix="/store",
  tags=["Store"],
  dependencies=[Depends(get_current_user)]
)


@router.post(
  "",
  response_model=StoreResponse,
  status_code=status.HTTP_201_CREATED
)
def create_store(
  data: StoreCreate,
  db: Session = Depends(get_db),
  current_user = Depends(get_current_user)
):
  service = StoreService(db)
  store = service.create(data, current_user)
  return service.serialize(store)


@router.patch(
  "/me",
  response_model=StoreResponse
)
def update_my_store(
  data: StoreUpdate,
  db: Session = Depends(get_db),
  current_user = Depends(get_current_user)
):
  service = StoreService(db)
  store = service.get_by_user_id(current_user.id)

  if not store:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Store not found"
    )

  updated = service.update(store, data)
  return service.serialize(updated)


@router.get(
  "/me",
  response_model=StoreResponse
)
def get_my_store(
  db: Session = Depends(get_db),
  current_user = Depends(get_current_user)
):
  service = StoreService(db)
  store = service.get_by_user_id(current_user.id)

  if not store:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Store not found"
    )

  return service.serialize(store)


@router.patch(
  "/me/today-open",
  response_model=StoreResponse
)
def toggle_today_open(
  data: StoreTodayOpenToggle,
  db: Session = Depends(get_db),
  current_user = Depends(get_current_user)
):
  service = StoreService(db)
  store = service.get_by_user_id(current_user.id)

  if not store:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Store not found"
    )

  updated = service.toggle_today_open(store=store, should_open=data.should_open)
  return service.serialize(updated)


@router.get(
  "/{slug}",
  response_model=StoreResponse
)
def get_store_by_slug(
  slug: str,
  db: Session = Depends(get_db)
):
  service = StoreService(db)
  store = service.get_by_slug(slug)

  if not store:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Store not found"
    )

  return service.serialize(store)
