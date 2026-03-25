import uuid

from fastapi import HTTPException, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.domain.models.delivery_method import DeliveryMethod
from app.services.store import StoreService
from app.schemas.delivery_method import DeliveryMethodCreate, DeliveryMethodUpdate


class DeliveryMethodService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: DeliveryMethodCreate, *, current_user=None, store_id: uuid.UUID | None = None) -> DeliveryMethod:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if self.get_by_name(data.name, store_id=scope_store_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery method name already exists",
            )

        method = DeliveryMethod(
            store_id=scope_store_id,
            name=data.name,
            price=float(data.price),
            description=data.description,
        )
        self.db.add(method)
        self.db.commit()
        self.db.refresh(method)
        return method

    def list(
        self, skip: int = 0, limit: int = 20, search: str | None = None, *, current_user=None, store_id: uuid.UUID | None = None
    ) -> list[DeliveryMethod]:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(DeliveryMethod).where(DeliveryMethod.store_id == scope_store_id)
        stmt = self._apply_filters(stmt, search)
        stmt = stmt.order_by(DeliveryMethod.name.asc()).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def count(self, search: str | None = None, *, current_user=None, store_id: uuid.UUID | None = None) -> int:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(func.count()).select_from(DeliveryMethod).where(DeliveryMethod.store_id == scope_store_id)
        stmt = self._apply_filters(stmt, search)
        return int(self.db.execute(stmt).scalar_one())

    def get_by_id(self, method_id: uuid.UUID, *, current_user=None, store_id: uuid.UUID | None = None) -> DeliveryMethod | None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(DeliveryMethod).where(DeliveryMethod.id == method_id, DeliveryMethod.store_id == scope_store_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str, *, current_user=None, store_id: uuid.UUID | None = None) -> DeliveryMethod | None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(DeliveryMethod).where(DeliveryMethod.name == name, DeliveryMethod.store_id == scope_store_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(self, method: DeliveryMethod, data: DeliveryMethodUpdate, *, current_user=None, store_id: uuid.UUID | None = None) -> DeliveryMethod:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if method.store_id != scope_store_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery method not found")
        existing = self.get_by_name(data.name, store_id=scope_store_id)
        if existing and existing.id != method.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery method name already exists",
            )

        method.name = data.name
        method.price = float(data.price)
        method.description = data.description

        self.db.commit()
        self.db.refresh(method)
        return method

    def delete(self, method: DeliveryMethod, *, current_user=None, store_id: uuid.UUID | None = None) -> None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if method.store_id != scope_store_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery method not found")
        self.db.delete(method)
        self.db.commit()

    def _apply_filters(self, stmt, search: str | None):
        if not search:
            return stmt

        term = f"%{search.strip()}%"
        return stmt.where(
            or_(
                DeliveryMethod.name.ilike(term),
                DeliveryMethod.description.ilike(term),
                cast(DeliveryMethod.price, String).ilike(term),
            )
        )

    def _resolve_store_id(self, *, current_user=None, store_id: uuid.UUID | None = None) -> uuid.UUID:
        if store_id:
            return store_id
        if not current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store scope is required")
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return store.id
