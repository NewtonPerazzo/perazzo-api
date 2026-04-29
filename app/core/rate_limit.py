from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status


_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(request: Request, *, key: str, limit: int, window_seconds: int) -> None:
    now = monotonic()
    bucket_key = f"{key}:{_client_ip(request)}"
    bucket = _buckets[bucket_key]

    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later",
        )

    bucket.append(now)


def login_rate_limit(request: Request) -> None:
    check_rate_limit(request, key="auth-login", limit=10, window_seconds=60)


def password_recovery_rate_limit(request: Request) -> None:
    check_rate_limit(request, key="auth-password-recovery", limit=5, window_seconds=300)


def catalog_cart_rate_limit(request: Request) -> None:
    check_rate_limit(request, key="catalog-cart", limit=60, window_seconds=60)
