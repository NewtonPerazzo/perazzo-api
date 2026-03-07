from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base


product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)
