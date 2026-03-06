from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Optional
from fastapi import HTTPException, status

SECRET_KEY = "CHANGE_THIS_SECRET"
EMAIL_SECRET_KEY = "CHANGE_THIS_SECRET_FOR_EMAIL"
RESET_SECRET_KEY = "CHANGE_THIS_SECRET_FOR_RESET"

ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = 60
EMAIL_EXPIRE_MINUTES = 60 * 24
RESET_EXPIRE_MINUTES = 15


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None


def create_password_reset_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=RESET_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, RESET_SECRET_KEY, algorithm=ALGORITHM)


def decode_password_reset_token(token: str) -> int:
    try:
        payload = jwt.decode(token, RESET_SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")


def create_email_verification_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EMAIL_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, EMAIL_SECRET_KEY, algorithm=ALGORITHM)


def decode_email_verification_token(token: str) -> int:
    try:
        payload = jwt.decode(token, EMAIL_SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")