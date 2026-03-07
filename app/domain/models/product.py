import uuid
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.domain.models.base import TimestampMixin, ActiveMixin
from app.domain.models.product_category import product_categories
from typing import Optional

class Product(Base, TimestampMixin, ActiveMixin):

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(
      String(140),
      unique=True,
      index=True,
      nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(nullable=True)

    categories = relationship(
      "Category",
      secondary=product_categories,
      back_populates="products"
    )
