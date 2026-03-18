import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.services.customer import CustomerService


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):
    return CustomerService(db).create(data)


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    response: Response,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)
    items = service.list(skip=skip, limit=limit, search=search)
    total = service.count(search=search)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    customer = CustomerService(db).get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)
    customer = service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return service.update(customer, data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)
    customer = service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    try:
        service.delete(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer cannot be deleted because it is linked to existing orders",
        )
    return None
