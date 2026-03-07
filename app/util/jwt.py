from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import settings


def _create_token(data: dict, secret: str, expires_minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm=settings.ALGORITHM)


def _decode_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise e


# -------- ACCESS TOKEN (login) --------
def create_access_token(data: dict) -> str:
    return _create_token(
        data=data,
        secret=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_EXPIRE_MINUTES,
    )


def decode_access_token(token: str) -> dict:
    return _decode_token(token, settings.SECRET_KEY)


# -------- EMAIL VERIFICATION TOKEN --------
def create_email_verification_token(data: dict) -> str:
    return _create_token(
        data=data,
        secret=settings.EMAIL_SECRET_KEY,
        expires_minutes=settings.EMAIL_EXPIRE_MINUTES,
    )


def decode_email_verification_token(token: str) -> dict:
    return _decode_token(token, settings.EMAIL_SECRET_KEY)


# -------- PASSWORD RESET TOKEN --------
def create_password_reset_token(data: dict) -> str:
    return _create_token(
        data=data,
        secret=settings.RESET_SECRET_KEY,
        expires_minutes=settings.RESET_EXPIRE_MINUTES,
    )


def decode_password_reset_token(token: str) -> dict:
    return _decode_token(token, settings.RESET_SECRET_KEY)