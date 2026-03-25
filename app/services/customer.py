import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.models.customer import Customer
from app.domain.models.order import Order
from app.services.store import StoreService
from fastapi import HTTPException, status
from app.schemas.customer import CustomerCreate, CustomerUpdate

DELETED_CUSTOMER_EMAIL = "deleted-customer@perazzo.com"
LEGACY_DELETED_CUSTOMER_EMAIL = "deleted-customer@perazzo.local"


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CustomerCreate, *, current_user=None, store_id: uuid.UUID | None = None) -> dict:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        customer = Customer(
            store_id=scope_store_id,
            name=data.name,
            phone=data.phone,
            address=data.address,
            neighborhood=data.neighborhood,
            email=data.email,
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return self._serialize(customer, 0)

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        *,
        current_user=None,
        store_id: uuid.UUID | None = None,
    ) -> list[dict]:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        orders_count_subquery = (
            select(
                Order.customer_id.label("customer_id"),
                func.count(Order.id).label("orders_count"),
            )
            .where(Order.store_id == scope_store_id)
            .group_by(Order.customer_id)
            .subquery()
        )

        stmt = (
            select(
                Customer,
                func.coalesce(orders_count_subquery.c.orders_count, 0).label("orders_count"),
            )
            .outerjoin(orders_count_subquery, orders_count_subquery.c.customer_id == Customer.id)
        )
        stmt = self._apply_filters(stmt, search, store_id=scope_store_id)
        stmt = stmt.offset(skip).limit(limit)
        rows = self.db.execute(stmt).all()
        return [self._serialize(row[0], int(row[1] or 0)) for row in rows]

    def count(self, search: str | None = None, *, current_user=None, store_id: uuid.UUID | None = None) -> int:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        stmt = select(func.count()).select_from(Customer)
        stmt = self._apply_filters(stmt, search, store_id=scope_store_id)
        return self.db.execute(stmt).scalar_one()

    def get_by_id(self, customer_id: uuid.UUID, *, current_user=None, store_id: uuid.UUID | None = None) -> dict | None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        orders_count_subquery = (
            select(
                Order.customer_id.label("customer_id"),
                func.count(Order.id).label("orders_count"),
            )
            .where(Order.store_id == scope_store_id)
            .group_by(Order.customer_id)
            .subquery()
        )
        stmt = (
            select(
                Customer,
                func.coalesce(orders_count_subquery.c.orders_count, 0).label("orders_count"),
            )
            .outerjoin(orders_count_subquery, orders_count_subquery.c.customer_id == Customer.id)
            .where(Customer.id == customer_id, Customer.store_id == scope_store_id)
        )
        row = self.db.execute(stmt).first()
        if not row:
            return None
        return self._serialize(row[0], int(row[1] or 0))

    def update(self, customer_id: uuid.UUID, data: CustomerUpdate, *, current_user=None, store_id: uuid.UUID | None = None) -> dict | None:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        customer = self._get_customer_model_by_id(customer_id, store_id=scope_store_id)
        if not customer:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        self.db.commit()
        self.db.refresh(customer)
        orders_count = self.db.execute(
            select(func.count(Order.id)).where(Order.customer_id == customer.id, Order.store_id == scope_store_id)
        ).scalar_one()
        return self._serialize(customer, int(orders_count or 0))

    def delete(self, customer_id: uuid.UUID, *, current_user=None, store_id: uuid.UUID | None = None) -> bool:
        scope_store_id = self._resolve_store_id(current_user=current_user, store_id=store_id)
        customer = self._get_customer_model_by_id(customer_id, store_id=scope_store_id)
        if not customer:
            return False

        fallback_customer = self._get_or_create_deleted_customer(store_id=scope_store_id)

        if fallback_customer.id != customer.id:
            self.db.execute(
                update(Order)
                .where(Order.customer_id == customer.id, Order.store_id == scope_store_id)
                .values(customer_id=fallback_customer.id)
            )

        self.db.delete(customer)
        self.db.commit()
        return True

    def _apply_filters(self, stmt, search: str | None, *, store_id: uuid.UUID):
        stmt = stmt.where(
            Customer.store_id == store_id,
            (Customer.email.is_(None))
            | (
                (Customer.email != DELETED_CUSTOMER_EMAIL)
                & (Customer.email != LEGACY_DELETED_CUSTOMER_EMAIL)
            )
        )

        if search:
            stmt = stmt.where(Customer.name.ilike(f"%{search}%"))
        return stmt

    def _get_or_create_deleted_customer(self, *, store_id: uuid.UUID) -> Customer:
        legacy_stmt = select(Customer).where(
            Customer.email == LEGACY_DELETED_CUSTOMER_EMAIL,
            Customer.store_id == store_id,
        )
        legacy_existing = self.db.execute(legacy_stmt).scalars().first()
        if legacy_existing:
            legacy_existing.email = DELETED_CUSTOMER_EMAIL
            self.db.flush()
            return legacy_existing

        stmt = select(Customer).where(Customer.email == DELETED_CUSTOMER_EMAIL, Customer.store_id == store_id)
        existing = self.db.execute(stmt).scalars().first()
        if existing:
            return existing

        customer = Customer(
            store_id=store_id,
            name="Cliente removido",
            phone="-",
            address=None,
            neighborhood=None,
            email=DELETED_CUSTOMER_EMAIL,
        )
        self.db.add(customer)
        self.db.flush()
        return customer

    def _get_customer_model_by_id(self, customer_id: uuid.UUID, *, store_id: uuid.UUID) -> Customer | None:
        stmt = select(Customer).where(Customer.id == customer_id, Customer.store_id == store_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def _serialize(self, customer: Customer, orders_count: int) -> dict:
        return {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "address": customer.address,
            "neighborhood": customer.neighborhood,
            "email": customer.email,
            "delivered_orders_count": customer.delivered_orders_count,
            "delivered_total_spent": customer.delivered_total_spent,
            "orders_count": orders_count,
            "created_at": customer.created_at,
        }

    def _resolve_store_id(self, *, current_user=None, store_id: uuid.UUID | None = None) -> uuid.UUID:
        if store_id:
            return store_id
        if not current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store scope is required")
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return store.id
