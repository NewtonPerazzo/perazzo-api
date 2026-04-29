import hashlib
import hmac


def hash_token(token: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_token_hash(token: str, token_hash: str | None, secret: str) -> bool:
    if not token_hash:
        return False
    return hmac.compare_digest(hash_token(token, secret), token_hash)
