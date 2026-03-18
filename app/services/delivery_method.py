import uuid

from fastapi import HTTPException, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.domain.models.delivery_method import DeliveryMethod
from app.schemas.delivery_method import DeliveryMethodCreate, DeliveryMethodUpdate


class DeliveryMethodService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: DeliveryMethodCreate) -> DeliveryMethod:
        if self.get_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery method name already exists",
            )

        method = DeliveryMethod(
            name=data.name,
            price=float(data.price),
            description=data.description,
        )
        self.db.add(method)
        self.db.commit()
        self.db.refresh(method)
        return method

    def list(self, skip: int = 0, limit: int = 20, search: str | None = None) -> list[DeliveryMethod]:
        stmt = select(DeliveryMethod)
        stmt = self._apply_filters(stmt, search)
        stmt = stmt.order_by(DeliveryMethod.name.asc()).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def count(self, search: str | None = None) -> int:
        stmt = select(func.count()).select_from(DeliveryMethod)
        stmt = self._apply_filters(stmt, search)
        return int(self.db.execute(stmt).scalar_one())

    def get_by_id(self, method_id: uuid.UUID) -> DeliveryMethod | None:
        stmt = select(DeliveryMethod).where(DeliveryMethod.id == method_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> DeliveryMethod | None:
        stmt = select(DeliveryMethod).where(DeliveryMethod.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(self, method: DeliveryMethod, data: DeliveryMethodUpdate) -> DeliveryMethod:
        existing = self.get_by_name(data.name)
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

    def delete(self, method: DeliveryMethod) -> None:
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
