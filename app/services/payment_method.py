import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.payment_method import PaymentMethod
from app.services.store import StoreService
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate


class PaymentMethodService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PaymentMethodCreate, *, current_user=None, store_id: uuid.UUID | None = None) -> PaymentMethod:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if self.get_by_name(data.name, store_id=scope_store_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment method name already exists",
            )

        payment_method = PaymentMethod(store_id=scope_store_id, name=data.name)
        self.db.add(payment_method)
        self.db.commit()
        self.db.refresh(payment_method)
        return payment_method

    def list(self, skip: int = 0, limit: int = 20, *, current_user=None, store_id: uuid.UUID | None = None) -> list[PaymentMethod]:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(PaymentMethod).where(PaymentMethod.store_id == scope_store_id).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def get_by_id(
        self, payment_method_id: uuid.UUID, *, current_user=None, store_id: uuid.UUID | None = None
    ) -> PaymentMethod | None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(PaymentMethod).where(
            PaymentMethod.id == payment_method_id,
            PaymentMethod.store_id == scope_store_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str, *, current_user=None, store_id: uuid.UUID | None = None) -> PaymentMethod | None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(PaymentMethod).where(PaymentMethod.name == name, PaymentMethod.store_id == scope_store_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(self, payment_method: PaymentMethod, data: PaymentMethodUpdate, *, current_user=None, store_id: uuid.UUID | None = None) -> PaymentMethod:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if payment_method.store_id != scope_store_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        existing = self.get_by_name(data.name, store_id=scope_store_id)
        if existing and existing.id != payment_method.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment method name already exists",
            )

        payment_method.name = data.name
        self.db.commit()
        self.db.refresh(payment_method)
        return payment_method

    def delete(self, payment_method: PaymentMethod, *, current_user=None, store_id: uuid.UUID | None = None) -> None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        if payment_method.store_id != scope_store_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        self.db.delete(payment_method)
        self.db.commit()

    def _resolve_store_id(self, *, current_user=None, store_id: uuid.UUID | None = None) -> uuid.UUID:
        if store_id:
            return store_id
        if not current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store scope is required")
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return store.id
