from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models.order import Order
from app.domain.models.store import Store
from app.domain.models.user import User

PlanId = Literal["free", "essential", "pro"]

LOCAL_TIMEZONE = "America/Sao_Paulo"
FREE_PLAN_ID: PlanId = "free"
ESSENTIAL_PLAN_ID: PlanId = "essential"
PRO_PLAN_ID: PlanId = "pro"

PLAN_CATALOG: dict[PlanId, dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_cents": 0,
        "billing_period_days": None,
        "monthly_order_limit": 10,
        "advanced_features_trial_days": 7,
        "features": {
            "catalog": "unlimited",
            "orders": "10/month",
            "whatsapp_orders": "7_days",
            "order_editing": "7_days",
            "cash_register": "7_days",
            "couriers": "7_days",
            "tutorials_and_support": "9h_to_20h_every_day",
        },
    },
    "essential": {
        "id": "essential",
        "name": "Essential",
        "price_cents": 2500,
        "billing_period_days": 30,
        "monthly_order_limit": 50,
        "advanced_features_trial_days": None,
        "features": {
            "catalog": "unlimited",
            "orders": "50/month",
            "whatsapp_orders": "unlimited",
            "order_editing": "unlimited",
            "cash_register": "unlimited",
            "couriers": "unlimited",
            "tutorials_and_support": "9h_to_20h_every_day",
        },
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_cents": 5000,
        "billing_period_days": 30,
        "monthly_order_limit": None,
        "advanced_features_trial_days": None,
        "features": {
            "catalog": "unlimited",
            "orders": "unlimited",
            "whatsapp_orders": "unlimited",
            "order_editing": "unlimited",
            "cash_register": "unlimited",
            "couriers": "unlimited",
            "tutorials_and_support": "9h_to_20h_every_day",
        },
    },
}


def normalize_plan(plan: str | None) -> PlanId:
    if plan in PLAN_CATALOG:
        return plan  # type: ignore[return-value]
    return FREE_PLAN_ID


def get_plan(plan: str | None) -> dict[str, Any]:
    return PLAN_CATALOG[normalize_plan(plan)]


def is_free(plan: str | None) -> bool:
    return normalize_plan(plan) == FREE_PLAN_ID


def is_essential(plan: str | None) -> bool:
    return normalize_plan(plan) == ESSENTIAL_PLAN_ID


def is_pro(plan: str | None) -> bool:
    return normalize_plan(plan) == PRO_PLAN_ID


def serialize_plan(plan: str | None) -> dict[str, Any]:
    selected = get_plan(plan)
    return {
        "id": selected["id"],
        "name": selected["name"],
        "price_cents": selected["price_cents"],
        "billing_period_days": selected["billing_period_days"],
        "monthly_order_limit": selected["monthly_order_limit"],
        "advanced_features_trial_days": selected["advanced_features_trial_days"],
        "features": selected["features"],
    }


def user_has_advanced_features(user: User, now: datetime | None = None) -> bool:
    plan = normalize_plan(user.plan)
    if plan in {ESSENTIAL_PLAN_ID, PRO_PLAN_ID}:
        return True

    selected = get_plan(plan)
    trial_days = selected["advanced_features_trial_days"]
    if trial_days is None:
        return True

    started_at = user.plan_started_at or user.created_at
    if not started_at:
        return False

    reference = now or datetime.now(ZoneInfo(LOCAL_TIMEZONE))
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=ZoneInfo(LOCAL_TIMEZONE))

    return reference <= started_at + timedelta(days=int(trial_days))


def ensure_advanced_feature_access(user: User, feature_name: str) -> None:
    if user_has_advanced_features(user):
        return

    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=f"{feature_name} is available during the Free trial or on paid plans",
    )


def get_store_owner(db: Session, store_id) -> User | None:
    stmt = select(User).join(Store, Store.user_id == User.id).where(Store.id == store_id)
    return db.execute(stmt).scalar_one_or_none()


def current_month_range(now: datetime | None = None) -> tuple[datetime, datetime]:
    reference = now or datetime.now(ZoneInfo(LOCAL_TIMEZONE))
    start = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def count_orders_in_current_month(db: Session, store_id) -> int:
    period_start, period_end = current_month_range()
    stmt = select(func.count(Order.id)).where(
        Order.store_id == store_id,
        Order.created_at >= period_start,
        Order.created_at < period_end,
    )
    return int(db.execute(stmt).scalar_one() or 0)


def ensure_monthly_order_limit(db: Session, user: User | None, store_id) -> None:
    owner = user or get_store_owner(db, store_id)
    if not owner:
        return

    plan = get_plan(owner.plan)
    limit = plan["monthly_order_limit"]
    if limit is None:
        return

    used = count_orders_in_current_month(db, store_id)
    if used < int(limit):
        return

    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=f"Monthly order limit reached for the {plan['name']} plan",
    )
