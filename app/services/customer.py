import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(
            name=data.name,
            phone=data.phone,
            address=data.address,
            email=data.email,
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def list(self, skip: int = 0, limit: int = 20) -> list[Customer]:
        stmt = select(Customer).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()

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
        self.db.delete(customer)
        self.db.commit()
