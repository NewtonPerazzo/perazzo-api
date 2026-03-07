from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.store import StoreCreate, StoreResponse
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

  return store


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

  return store


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

  return store