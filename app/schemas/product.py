from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class ProductCreate(BaseModel):

  name: str = Field(..., min_length=1, max_length=120)

  price: float = Field(..., gt=0)

  description: Optional[str] = None

  stock: Optional[int] = Field(default=None, ge=0)

  image_url: Optional[str] = None


class ProductUpdate(BaseModel):

  name: Optional[str] = Field(default=None, min_length=1, max_length=120)

  price: Optional[float] = Field(default=None, gt=0)

  description: Optional[str] = None

  stock: Optional[int] = Field(default=None, ge=0)

  image_url: Optional[str] = None

class ProductResponse(BaseModel):

  id: UUID
  slug: str
  name: str
  price: float
  description: Optional[str]
  stock: Optional[int]
  image_url: Optional[str]

  is_active: bool
  created_at: datetime
  updated_at: datetime

  class Config:
      from_attributes = True
