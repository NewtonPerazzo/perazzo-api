from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.domain.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


class UserService:

  def __init__(self, db: Session):
      self.db = db


  def create(self, data: UserCreate) -> User:

    existing_user = self.get_by_email(data.email)

    if existing_user:
        raise ValueError("Email already registered")

    user = User(
        name=data.name,
        last_name=data.last_name,
        email=data.email,
        password=hash_password(data.password),
        birth_date=data.birth_date,
        photo=data.photo
    )

    self.db.add(user)
    self.db.commit()
    self.db.refresh(user)

    return user


  def authenticate(self, email: str, password: str) -> Optional[User]:

      user = self.get_by_email(email)

      if not user:
          return None

      if not verify_password(password, user.password):
          return None

      return user


  def get_by_email(self, email: str) -> Optional[User]:

      stmt = select(User).where(User.email == email)
      result = self.db.execute(stmt)

      return result.scalar_one_or_none()


  def get_by_id(self, user_id: int) -> Optional[User]:

      stmt = select(User).where(User.id == user_id)
      result = self.db.execute(stmt)

      return result.scalar_one_or_none()


  def update(self, user: User, data: UserUpdate) -> User:

      update_data = data.model_dump(exclude_unset=True)

      if "password" in update_data:
          update_data["password"] = hash_password(update_data["password"])

      for field, value in update_data.items():
          setattr(user, field, value)

      self.db.commit()
      self.db.refresh(user)

      return user


  def delete(self, user: User):

      self.db.delete(user)
      self.db.commit()