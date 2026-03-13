import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.payment_method import PaymentMethod
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate


class PaymentMethodService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PaymentMethodCreate) -> PaymentMethod:
        if self.get_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment method name already exists",
            )

        payment_method = PaymentMethod(name=data.name)
        self.db.add(payment_method)
        self.db.commit()
        self.db.refresh(payment_method)
        return payment_method

    def list(self, skip: int = 0, limit: int = 20) -> list[PaymentMethod]:
        stmt = select(PaymentMethod).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def get_by_id(self, payment_method_id: uuid.UUID) -> PaymentMethod | None:
        stmt = select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> PaymentMethod | None:
        stmt = select(PaymentMethod).where(PaymentMethod.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(self, payment_method: PaymentMethod, data: PaymentMethodUpdate) -> PaymentMethod:
        existing = self.get_by_name(data.name)
        if existing and existing.id != payment_method.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment method name already exists",
            )

        payment_method.name = data.name
        self.db.commit()
        self.db.refresh(payment_method)
        return payment_method

    def delete(self, payment_method: PaymentMethod) -> None:
        self.db.delete(payment_method)
        self.db.commit()
