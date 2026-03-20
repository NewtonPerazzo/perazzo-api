from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CatalogStoreResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    phone: str | None
    whatsapp: str | None
    address: str | None
    instagram: str | None
    email: EmailStr | None
    logo: str | None
    color: str | None
    is_accepted_send_order_to_whatsapp: bool
    business_hours: dict
    is_open_now: bool

    model_config = ConfigDict(from_attributes=True)


class CatalogCategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    products_count: int


class CatalogProductResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    price: float
    description: str | None
    stock: int | None
    image_url: str | None


class CatalogHomeSectionResponse(BaseModel):
    category: CatalogCategoryResponse
    products: list[CatalogProductResponse]


class CatalogHomeResponse(BaseModel):
    store: CatalogStoreResponse
    categories: list[CatalogCategoryResponse]
    sections: list[CatalogHomeSectionResponse]


class CatalogProductsPageResponse(BaseModel):
    store: CatalogStoreResponse
    categories: list[CatalogCategoryResponse]
    selected_category: CatalogCategoryResponse | None = None
    products: list[CatalogProductResponse]


class CatalogProductPageResponse(BaseModel):
    store: CatalogStoreResponse
    product: CatalogProductResponse


class CatalogCartProductResponse(BaseModel):
    product: CatalogProductResponse
    amount: int
    price: float


class CatalogCartCustomerResponse(BaseModel):
    first_name: str
    last_name: str
    whatsapp: str
    address: str | None = None
    neighborhood: str | None = None


class CatalogCartResponse(BaseModel):
    id: UUID
    products: list[CatalogCartProductResponse]
    customer: CatalogCartCustomerResponse | None = None
    is_to_deliver: bool | None = None
    delivery_method_id: UUID | None = None
    payment_method_id: UUID | None = None
    observation: str | None = None
    total_price: float
    created_at: datetime
    updated_at: datetime


class CatalogCartPreviewTotalRequest(BaseModel):
    is_to_deliver: bool = False
    delivery_method_id: UUID | None = None


class CatalogCartPreviewTotalResponse(BaseModel):
    total_price: float


class CatalogCheckoutCustomerInput(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    whatsapp: str = Field(..., min_length=1, max_length=30)
    neighborhood: str | None = None
    address: str | None = None


class CatalogCartCheckoutRequest(BaseModel):
    payment_method_id: UUID
    is_to_deliver: bool = False
    delivery_method_id: UUID | None = None
    customer: CatalogCheckoutCustomerInput
    observation: str | None = None
