import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.models.customer import Customer
from app.domain.models.order import Order
from app.schemas.customer import CustomerCreate, CustomerUpdate

DELETED_CUSTOMER_EMAIL = "deleted-customer@perazzo.com"
LEGACY_DELETED_CUSTOMER_EMAIL = "deleted-customer@perazzo.local"


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(
            name=data.name,
            phone=data.phone,
            address=data.address,
            neighborhood=data.neighborhood,
            email=data.email,
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
    ) -> list[Customer]:
        stmt = select(Customer)
        stmt = self._apply_filters(stmt, search)
        stmt = stmt.offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def count(self, search: str | None = None) -> int:
        stmt = select(func.count()).select_from(Customer)
        stmt = self._apply_filters(stmt, search)
        return self.db.execute(stmt).scalar_one()

    def get_by_id(self, customer_id: uuid.UUID) -> Customer | None:
        stmt = select(Customer).where(Customer.id == customer_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(self, customer: Customer, data: CustomerUpdate) -> Customer:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete(self, customer: Customer) -> None:
        fallback_customer = self._get_or_create_deleted_customer()

        if fallback_customer.id != customer.id:
            self.db.execute(
                update(Order)
                .where(Order.customer_id == customer.id)
                .values(customer_id=fallback_customer.id)
            )

        self.db.delete(customer)
        self.db.commit()

    def _apply_filters(self, stmt, search: str | None):
        stmt = stmt.where(
            (Customer.email.is_(None))
            | (
                (Customer.email != DELETED_CUSTOMER_EMAIL)
                & (Customer.email != LEGACY_DELETED_CUSTOMER_EMAIL)
            )
        )

        if search:
            stmt = stmt.where(Customer.name.ilike(f"%{search}%"))
        return stmt

    def _get_or_create_deleted_customer(self) -> Customer:
        legacy_stmt = select(Customer).where(Customer.email == LEGACY_DELETED_CUSTOMER_EMAIL)
        legacy_existing = self.db.execute(legacy_stmt).scalar_one_or_none()
        if legacy_existing:
            legacy_existing.email = DELETED_CUSTOMER_EMAIL
            self.db.flush()
            return legacy_existing

        stmt = select(Customer).where(Customer.email == DELETED_CUSTOMER_EMAIL)
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            return existing

        customer = Customer(
            name="Cliente removido",
            phone="-",
            address=None,
            neighborhood=None,
            email=DELETED_CUSTOMER_EMAIL,
        )
        self.db.add(customer)
        self.db.flush()
        return customer
