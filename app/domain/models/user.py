from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)

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