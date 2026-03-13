from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.customer import CustomerCreate
from app.schemas.order import ProductOrderCreate, ProductOrderResponse


class ProductCartCreate(ProductOrderCreate):
    pass


class CartCreate(BaseModel):
    product: ProductCartCreate


class CartPatch(BaseModel):
    products: list[ProductCartCreate] | None = None
    customer: CustomerCreate | None = None
    is_to_deliver: bool | None = None
    payment_method: str | None = Field(default=None, min_length=1, max_length=60)


class CartProductsReplace(BaseModel):
    products: list[ProductCartCreate] = Field(default_factory=list)


class CartCustomerData(BaseModel):
    name: str
    phone: str
    address: str | None = None
    email: str | None = None


class CartResponse(BaseModel):
    id: UUID
    products: list[ProductOrderResponse]
    customer: CartCustomerData | None = None
    is_to_deliver: bool | None
    payment_method: str | None
    total_price: float
    created_at: datetime
    updated_at: datetime
