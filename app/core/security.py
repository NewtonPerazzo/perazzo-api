from passlib.context import CryptContext
from app.util.password import validate_password_bcrypt_length

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    validate_password_bcrypt_length(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    validate_password_bcrypt_length(plain_password)
    return pwd_context.verify(plain_password, hashed_password)