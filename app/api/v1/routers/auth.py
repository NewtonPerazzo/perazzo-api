from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.domain.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserUpdate, UserResponse
from app.services.user import UserService
from app.util.jwt import create_access_token, create_email_verification_token, decode_email_verification_token, create_password_reset_token, decode_password_reset_token
from app.core.dependencies import get_current_user
from app.core.security import hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
  service = UserService(db)
  user = service.authenticate(data.email, data.password)

  if not user:
      raise HTTPException(status_code=401, detail="Invalid credentials")

  token = create_access_token({"sub": str(user.id)})

  return {
      "access_token": token,
      "token_type": "bearer"
  }

@router.post("/register")
def register(data: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    try:
        user = service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    token = create_email_verification_token({"sub": str(user.id)})
    user.email_verification_token = token
    db.commit()
    
    return {"id": user.id, "email": user.email, "email_verification_token": token}


@router.post("/email/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_email_verification_token(token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    try:
        parsed_user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    user = UserService(db).get_by_id(parsed_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/logout")
def logout(db: Session = Depends(get_db)):
    return {"message": "Logged out successfully"}


@router.post("/password/forgot")
def forgot_password(email: str, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = create_password_reset_token({"sub": str(user.id)})
    user.reset_password_token = token
    db.commit()
    
    return {"reset_token": token}


@router.post("/password/reset")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    try:
        payload = decode_password_reset_token(token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    try:
        parsed_user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    user = UserService(db).get_by_id(parsed_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = hash_password(new_password)
    user.reset_password_token = None
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.put("/me", response_model=UserResponse)
def update_user(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = UserService(db).update(current_user, data)
    return user
