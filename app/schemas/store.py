from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID


class StoreCreate(BaseModel):

    name: str
    description: str | None = None

    does_delivery: bool = False
    does_pick_up: bool = False

    phone: str | None = None
    whatsapp: str | None = None
    address: str | None = None
    instagram: str | None = None
    email: EmailStr | None = None

    logo: str | None = None

    color: str | None = None

    has_catalog_active: bool = False
    is_accepted_send_order_to_whatsapp: bool = False


class StoreUpdate(BaseModel):

    name: str | None = None
    description: str | None = None

    does_delivery: bool | None = None
    does_pick_up: bool | None = None

    phone: str | None = None
    whatsapp: str | None = None
    address: str | None = None
    instagram: str | None = None
    email: EmailStr | None = None

    logo: str | None = None

    color: str | None = None

    has_catalog_active: bool | None = None
    is_accepted_send_order_to_whatsapp: bool | None = None


class StoreResponse(BaseModel):

    id: UUID
    name: str
    slug: str
    description: str | None

    does_delivery: bool
    does_pick_up: bool

    phone: str | None
    whatsapp: str | None
    address: str | None
    instagram: str | None
    email: EmailStr | None

    logo: str | None
    color: str | None

    has_catalog_active: bool
    is_accepted_send_order_to_whatsapp: bool

    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
