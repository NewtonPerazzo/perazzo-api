from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.customer import CustomerCreate, CustomerResponse
from app.schemas.courier import CourierResponse
from app.schemas.delivery_method import DeliveryMethodResponse
from app.schemas.product import ProductResponse


OrderStatus = Literal["confirmed", "canceled", "preparing", "in_transit", "pending", "deliveried"]


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
    delivery_method_id: UUID | None = None
    courier_id: UUID | None = None
    payment_method: str = Field(..., min_length=1, max_length=60)
    observation: str | None = None


class OrderUpdate(OrderCreate):
    pass


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderTotalPreviewRequest(BaseModel):
    products: list[ProductOrderCreate] = Field(default_factory=list)
    is_to_deliver: bool = False
    delivery_method_id: UUID | None = None


class OrderTotalPreviewResponse(BaseModel):
    total_price: float


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    products: list[ProductOrderResponse]
    customer: CustomerResponse
    is_to_deliver: bool
    delivery_method: DeliveryMethodResponse | None
    courier: CourierResponse | None = None
    status: OrderStatus
    payment_method: str
    observation: str | None
    total_price: float
    created_at: datetime
    updated_at: datetime
