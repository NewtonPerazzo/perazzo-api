import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.domain.models.courier import Courier
from app.domain.models.courier_adjustment import CourierAdjustment
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.schemas.courier import (
    CourierAdjustmentCreate,
    CourierAdjustmentType,
    CourierAdjustmentUpdate,
    CourierCreate,
    CourierPeriodView,
    CourierUpdate,
)
from app.services.store import StoreService


class CourierService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, current_user, data: CourierCreate) -> Courier:
        store = self._get_store_or_404(current_user)
        courier = Courier(
            store_id=store.id,
            name=data.name.strip(),
            address=self._normalize_text(data.address),
        )
        self.db.add(courier)
        self.db.commit()
        self.db.refresh(courier)
        return courier

    def list(self, current_user, skip: int = 0, limit: int = 20, search: str | None = None) -> List[Courier]:
        store = self._get_store_or_404(current_user)
        stmt = (
            select(Courier)
            .where(Courier.store_id == store.id)
            .order_by(Courier.name.asc())
            .offset(skip)
            .limit(limit)
        )
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where((Courier.name.ilike(term)) | (Courier.address.ilike(term)))
        return self.db.execute(stmt).scalars().all()

    def count(self, current_user, search: str | None = None) -> int:
        store = self._get_store_or_404(current_user)
        stmt = select(func.count(Courier.id)).where(Courier.store_id == store.id)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where((Courier.name.ilike(term)) | (Courier.address.ilike(term)))
        return int(self.db.execute(stmt).scalar_one())

    def get_by_id(self, current_user, courier_id: uuid.UUID) -> Courier | None:
        store = self._get_store_or_404(current_user)
        stmt = select(Courier).where(Courier.id == courier_id, Courier.store_id == store.id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(self, courier: Courier, data: CourierUpdate) -> Courier:
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"] is not None:
            courier.name = payload["name"].strip()
        if "address" in payload:
            courier.address = self._normalize_text(payload["address"])
        self.db.commit()
        self.db.refresh(courier)
        return courier

    def delete(self, courier: Courier) -> None:
        self.db.delete(courier)
        self.db.commit()

    def create_adjustment(self, current_user, data: CourierAdjustmentCreate) -> CourierAdjustment:
        store = self._get_store_or_404(current_user)
        courier = self._resolve_courier_or_none(store_id=store.id, courier_id=data.courier_id)
        adjustment = CourierAdjustment(
            store_id=store.id,
            courier_id=courier.id if courier else None,
            adjustment_type=data.adjustment_type,
            amount=float(data.amount),
            payment_method=self._normalize_text(data.payment_method),
            note=self._normalize_text(data.note),
            occurred_on=data.occurred_on or datetime.now().date(),
        )
        self.db.add(adjustment)
        self.db.commit()
        self.db.refresh(adjustment)
        return adjustment

    def update_adjustment(
        self,
        current_user,
        adjustment_id: uuid.UUID,
        data: CourierAdjustmentUpdate,
    ) -> CourierAdjustment:
        store = self._get_store_or_404(current_user)
        adjustment = self.get_adjustment(current_user=current_user, adjustment_id=adjustment_id)
        if not adjustment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier adjustment not found")

        payload = data.model_dump(exclude_unset=True)
        if "courier_id" in payload:
            courier = self._resolve_courier_or_none(store_id=store.id, courier_id=payload["courier_id"])
            adjustment.courier_id = courier.id if courier else None
        if "adjustment_type" in payload and payload["adjustment_type"] is not None:
            adjustment.adjustment_type = payload["adjustment_type"]
        if "amount" in payload and payload["amount"] is not None:
            adjustment.amount = float(payload["amount"])
        if "payment_method" in payload:
            adjustment.payment_method = self._normalize_text(payload.get("payment_method"))
        if "note" in payload:
            adjustment.note = self._normalize_text(payload.get("note"))
        if "occurred_on" in payload and payload["occurred_on"] is not None:
            adjustment.occurred_on = payload["occurred_on"]

        self.db.commit()
        self.db.refresh(adjustment)
        return adjustment

    def get_adjustment(self, current_user, adjustment_id: uuid.UUID) -> CourierAdjustment | None:
        store = self._get_store_or_404(current_user)
        stmt = (
            select(CourierAdjustment)
            .options(joinedload(CourierAdjustment.courier))
            .where(
                CourierAdjustment.id == adjustment_id,
                CourierAdjustment.store_id == store.id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete_adjustment(self, current_user, adjustment_id: uuid.UUID) -> None:
        adjustment = self.get_adjustment(current_user=current_user, adjustment_id=adjustment_id)
        if not adjustment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier adjustment not found")
        self.db.delete(adjustment)
        self.db.commit()

    def get_summary(self, current_user, target_date: date, period_view: CourierPeriodView):
        store = self._get_store_or_404(current_user)
        period_start, period_end = self._resolve_period_range(target_date=target_date, period_view=period_view)

        riders = self.db.execute(
            select(Courier).where(Courier.store_id == store.id).order_by(Courier.name.asc())
        ).scalars().all()
        riders_by_id = {rider.id: rider for rider in riders}

        order_rows = self._query_delivery_rows(period_start=period_start, period_end=period_end)
        delivery_map: Dict[uuid.UUID | None, Dict[str, float]] = {}
        for row in order_rows:
            key = row.courier_id
            if key is not None and key not in riders_by_id:
                continue
            if key not in delivery_map:
                delivery_map[key] = {"count": 0.0, "amount": 0.0}
            delivery_map[key]["count"] += int(row.deliveries_count or 0)
            delivery_map[key]["amount"] += float(row.deliveries_amount or 0)

        adjustments = self.db.execute(
            select(CourierAdjustment)
            .options(joinedload(CourierAdjustment.courier))
            .where(
                CourierAdjustment.store_id == store.id,
                CourierAdjustment.occurred_on >= period_start,
                CourierAdjustment.occurred_on <= period_end,
            )
            .order_by(CourierAdjustment.created_at.desc())
        ).scalars().all()

        adjustment_map: Dict[uuid.UUID | None, float] = {}
        for item in adjustments:
            key = item.courier_id
            signed = self._signed_adjustment(item.adjustment_type, float(item.amount))
            adjustment_map[key] = adjustment_map.get(key, 0.0) + signed

        rider_items = []
        for rider in riders:
            delivery_count = int(delivery_map.get(rider.id, {}).get("count", 0))
            deliveries_amount = float(delivery_map.get(rider.id, {}).get("amount", 0.0))
            adjustments_total = float(adjustment_map.get(rider.id, 0.0))
            total_earnings = deliveries_amount + adjustments_total
            rider_items.append(
                {
                    "courier": rider,
                    "totals": {
                        "deliveries_count": delivery_count,
                        "deliveries_amount": round(deliveries_amount, 2),
                        "adjustments_total": round(adjustments_total, 2),
                        "total_earnings": round(total_earnings, 2),
                    },
                }
            )

        unassigned_deliveries_count = int(delivery_map.get(None, {}).get("count", 0))
        unassigned_deliveries_amount = float(delivery_map.get(None, {}).get("amount", 0.0))
        unassigned_adjustments_total = float(adjustment_map.get(None, 0.0))
        unassigned_total = unassigned_deliveries_amount + unassigned_adjustments_total

        total_deliveries_count = unassigned_deliveries_count + sum(item["totals"]["deliveries_count"] for item in rider_items)
        total_deliveries_amount = unassigned_deliveries_amount + sum(item["totals"]["deliveries_amount"] for item in rider_items)
        total_adjustments = unassigned_adjustments_total + sum(item["totals"]["adjustments_total"] for item in rider_items)
        total_earnings = total_deliveries_amount + total_adjustments

        return {
            "period_view": period_view,
            "period_start": period_start,
            "period_end": period_end,
            "target_date": target_date,
            "riders": rider_items,
            "unassigned": {
                "courier": None,
                "totals": {
                    "deliveries_count": unassigned_deliveries_count,
                    "deliveries_amount": round(unassigned_deliveries_amount, 2),
                    "adjustments_total": round(unassigned_adjustments_total, 2),
                    "total_earnings": round(unassigned_total, 2),
                },
            },
            "adjustments": adjustments,
            "totals": {
                "deliveries_count": int(total_deliveries_count),
                "deliveries_amount": round(total_deliveries_amount, 2),
                "adjustments_total": round(total_adjustments, 2),
                "total_earnings": round(total_earnings, 2),
            },
        }

    def resolve_courier_for_order(
        self,
        current_user,
        is_to_deliver: bool,
        courier_id: uuid.UUID | None,
    ) -> uuid.UUID | None:
        if not is_to_deliver:
            return None
        if not current_user:
            return None
        if not courier_id:
            return None

        store = self._get_store_or_404(current_user)
        courier = self._resolve_courier_or_none(store_id=store.id, courier_id=courier_id)
        return courier.id if courier else None

    def _query_delivery_rows(self, period_start: date, period_end: date):
        items_total_subquery = (
            select(
                OrderItem.order_id.label("order_id"),
                func.coalesce(func.sum(OrderItem.price), 0).label("items_total"),
            )
            .group_by(OrderItem.order_id)
            .subquery()
        )

        delivery_amount_expr = case(
            (
                (Order.total_price - func.coalesce(items_total_subquery.c.items_total, 0)) < 0,
                0,
            ),
            else_=(Order.total_price - func.coalesce(items_total_subquery.c.items_total, 0)),
        )

        return self.db.execute(
            select(
                Order.courier_id.label("courier_id"),
                func.count(Order.id).label("deliveries_count"),
                func.coalesce(func.sum(delivery_amount_expr), 0).label("deliveries_amount"),
            )
            .outerjoin(items_total_subquery, items_total_subquery.c.order_id == Order.id)
            .where(
                func.date(Order.created_at) >= period_start,
                func.date(Order.created_at) <= period_end,
                Order.is_to_deliver.is_(True),
                Order.status != "canceled",
            )
            .group_by(Order.courier_id)
        ).all()

    def _resolve_courier_or_none(self, store_id: uuid.UUID, courier_id: uuid.UUID | None) -> Courier | None:
        if not courier_id:
            return None
        courier = self.db.execute(
            select(Courier).where(Courier.id == courier_id, Courier.store_id == store_id)
        ).scalar_one_or_none()
        if not courier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier not found")
        return courier

    def _get_store_or_404(self, current_user):
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return store

    def _normalize_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        return text or None

    def _signed_adjustment(self, adjustment_type: CourierAdjustmentType, amount: float) -> float:
        return amount if adjustment_type == "add" else -amount

    def _resolve_period_range(self, target_date: date, period_view: CourierPeriodView) -> tuple[date, date]:
        if period_view == "day":
            return target_date, target_date

        if period_view == "week":
            start = target_date - timedelta(days=target_date.weekday())
            end = start + timedelta(days=6)
            return start, end

        if period_view == "month":
            start = target_date.replace(day=1)
            if start.month == 12:
                next_month = start.replace(year=start.year + 1, month=1, day=1)
            else:
                next_month = start.replace(month=start.month + 1, day=1)
            end = next_month - timedelta(days=1)
            return start, end

        start = target_date.replace(month=1, day=1)
        end = target_date.replace(month=12, day=31)
        return start, end
