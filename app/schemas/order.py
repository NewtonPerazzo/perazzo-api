from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.product import ProductResponse


class ProductOrderCreate(BaseModel):
    product_id: UUID
    amount: int = Field(..., gt=0)


class ProductOrderResponse(BaseModel):
    product: ProductResponse
    amount: int
    price: float


class OrderCreate(BaseModel):
    products: list[ProductOrderCreate] = Field(..., min_length=1)
    customer: CustomerCreate
    is_to_deliver: bool = False
    payment_method: str = Field(..., min_length=1, max_length=60)


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    products: list[ProductOrderResponse]
    customer: CustomerResponse
    is_to_deliver: bool
    payment_method: str
    total_price: float
    created_at: datetime
    updated_at: datetime
