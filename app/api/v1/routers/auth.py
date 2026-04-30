from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.core.database import get_db
from app.domain.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserUpdate, UserResponse
from app.services.user import UserService
from app.util.jwt import create_access_token, decode_email_verification_token, create_password_reset_token, decode_password_reset_token
from app.core.dependencies import get_current_user
from app.core.rate_limit import login_rate_limit, password_recovery_rate_limit
from app.core.security import hash_password
from app.services.email import EmailDeliveryError, send_password_reset_email
from app.util.token_hash import hash_token, verify_token_hash
from app.util.password import validate_password_rules

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
  login_rate_limit(request)
  service = UserService(db)
  user = service.authenticate(data.email, data.password)

  if not user:
      raise HTTPException(status_code=401, detail="Invalid credentials")
  
  if not user.is_active:
      raise HTTPException(status_code=403, detail="User is inactive")

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

    db.commit()
    
    return {"id": user.id, "email": user.email, "message": "Account created successfully"}


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
    if not user or not verify_token_hash(token, user.email_verification_token, settings.EMAIL_SECRET_KEY):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/logout")
def logout(db: Session = Depends(get_db)):
    return {"message": "Logged out successfully"}


@router.post("/password/forgot")
def forgot_password(email: str, request: Request, db: Session = Depends(get_db)):
    password_recovery_rate_limit(request)
    service = UserService(db)
    user = service.get_by_email(email)
    if not user:
        return {"message": "If the email exists, a password reset link will be sent"}
    
    token = create_password_reset_token({"sub": str(user.id)})
    user.reset_password_token = hash_token(token, settings.RESET_SECRET_KEY)
    db.commit()

    try:
        send_password_reset_email(user.email, token)
    except EmailDeliveryError:
        user.reset_password_token = None
        db.commit()
        raise HTTPException(status_code=503, detail="Could not send password reset email")
    
    return {"message": "If the email exists, a password reset link will be sent"}


@router.post("/password/reset")
def reset_password(token: str, new_password: str, request: Request, db: Session = Depends(get_db)):
    password_recovery_rate_limit(request)
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
    if not user or not verify_token_hash(token, user.reset_password_token, settings.RESET_SECRET_KEY):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    try:
        validated_password = validate_password_rules(new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user.password = hash_password(validated_password)
    user.reset_password_token = None
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_user(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = UserService(db).update(current_user, data)
    return user
