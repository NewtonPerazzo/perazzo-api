import uuid

from sqlalchemy import Column, String, Boolean, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.core.database import Base
from sqlalchemy.orm import relationship

class User(Base):
  __tablename__ = "users"

  id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

  name = Column(String, nullable=True)
  last_name = Column(String, nullable=True)

  email = Column(String, unique=True, index=True, nullable=False)
  password = Column(String, nullable=False)

  birth_date = Column(Date, nullable=True)
  photo = Column(String, nullable=True)

  is_active = Column(Boolean, default=True)
  is_email_verified = Column(Boolean, default=False)

  email_verification_token = Column(String, nullable=True)
  reset_password_token = Column(String, nullable=True)

  created_at = Column(DateTime(timezone=True), server_default=func.now())

  store = relationship("Store", back_populates="user", uselist=False)
