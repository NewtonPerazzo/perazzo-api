import re


def validate_password_rules(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must have at least 8 characters")

    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must have at most 72 bytes")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain uppercase letter")

    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain number")

    if not re.search(r"[!@#$%^&*]", password):
        raise ValueError("Password must contain special character")

    return password

def validate_password_bcrypt_length(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must have at most 72 bytes")
    return password