from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    sort_order: int

    class Config:
        from_attributes = True


class CategoryReorderRequest(BaseModel):
    category_ids: list[UUID] = Field(default_factory=list)
