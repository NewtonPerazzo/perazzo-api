import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models.cash_register_entry import CashRegisterEntry
from app.domain.models.order import Order
from app.services.store import StoreService
from app.schemas.cash_register import CashPeriodView, CashRegisterEntryCreate, CashRegisterEntryUpdate


class CashRegisterService:
    def __init__(self, db: Session):
        self.db = db

    def create_entry(self, current_user, data: CashRegisterEntryCreate) -> CashRegisterEntry:
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        entry = CashRegisterEntry(
            store_id=store.id,
            entry_type=data.entry_type,
            name=data.name.strip(),
            amount=float(data.amount),
            payment_method=self._normalize_payment_method(data.payment_method),
            is_profit=bool(data.is_profit),
            note=data.note,
            occurred_on=data.occurred_on or datetime.now().date(),
        )

        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update_entry(
        self,
        current_user,
        entry_id: uuid.UUID,
        data: CashRegisterEntryUpdate,
    ) -> CashRegisterEntry:
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        entry = self.get_entry(entry_id=entry_id, store_id=store.id)
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash entry not found")

        payload = data.model_dump(exclude_unset=True)
        if "name" in payload and payload["name"] is not None:
            payload["name"] = payload["name"].strip()
        if "payment_method" in payload:
            payload["payment_method"] = self._normalize_payment_method(payload.get("payment_method"))

        for field, value in payload.items():
            setattr(entry, field, value)

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_entry(self, entry_id: uuid.UUID, store_id: uuid.UUID) -> CashRegisterEntry | None:
        stmt = select(CashRegisterEntry).where(
            CashRegisterEntry.id == entry_id,
            CashRegisterEntry.store_id == store_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete_entry(self, current_user, entry_id: uuid.UUID) -> None:
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        entry = self.get_entry(entry_id=entry_id, store_id=store.id)
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cash entry not found")

        self.db.delete(entry)
        self.db.commit()

    def get_summary(self, current_user, target_date: date, period_view: CashPeriodView):
        store = StoreService(self.db).get_by_user_id(current_user.id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        period_start, period_end = self._resolve_period_range(target_date=target_date, period_view=period_view)

        manual_entries = self._list_manual(
            store_id=store.id,
            period_start=period_start,
            period_end=period_end,
            entry_type="entry",
            is_profit=False,
        )
        manual_expenses = self._list_manual(
            store_id=store.id,
            period_start=period_start,
            period_end=period_end,
            entry_type="expense",
            is_profit=False,
        )
        profit_entries = self._list_manual(
            store_id=store.id,
            period_start=period_start,
            period_end=period_end,
            entry_type="expense",
            is_profit=True,
        )
        auto_entries = self._list_auto_orders(
            period_start=period_start,
            period_end=period_end,
            period_view=period_view,
        )

        auto_total = sum(float(item["amount"]) for item in auto_entries)
        manual_entries_total = sum(float(item.amount) for item in manual_entries)
        manual_expenses_total = sum(float(item.amount) for item in manual_expenses)
        profits_total = sum(float(item.amount) for item in profit_entries)
        entries_total = auto_total + manual_entries_total
        balance = entries_total - manual_expenses_total - profits_total

        by_method_map: Dict[str, Dict[str, float]] = {}
        for auto in auto_entries:
            method = auto["payment_method"]
            self._ensure_method(by_method_map, method)
            by_method_map[method]["entries"] += float(auto["amount"])

        for entry in manual_entries:
            method = self._normalize_payment_method(entry.payment_method) or "Sem forma"
            self._ensure_method(by_method_map, method)
            by_method_map[method]["entries"] += float(entry.amount)

        for expense in manual_expenses:
            method = self._normalize_payment_method(expense.payment_method) or "Sem forma"
            self._ensure_method(by_method_map, method)
            by_method_map[method]["expenses"] += float(expense.amount)
        for profit in profit_entries:
            method = self._normalize_payment_method(profit.payment_method) or "Sem forma"
            self._ensure_method(by_method_map, method)
            by_method_map[method]["expenses"] += float(profit.amount)

        by_payment_method = [
            {
                "payment_method": method,
                "entries": round(values["entries"], 2),
                "expenses": round(values["expenses"], 2),
                "net": round(values["entries"] - values["expenses"], 2),
            }
            for method, values in sorted(by_method_map.items(), key=lambda item: item[0].lower())
        ]

        return {
            "period_view": period_view,
            "period_start": period_start,
            "period_end": period_end,
            "target_date": target_date,
            "auto_entries": auto_entries,
            "manual_entries": manual_entries,
            "manual_expenses": manual_expenses,
            "profit_entries": profit_entries,
            "by_payment_method": by_payment_method,
            "totals": {
                "auto_entries": round(auto_total, 2),
                "manual_entries": round(manual_entries_total, 2),
                "entries_total": round(entries_total, 2),
                "expenses_total": round(manual_expenses_total, 2),
                "profits_total": round(profits_total, 2),
                "balance": round(balance, 2),
            },
        }

    def _list_manual(
        self,
        store_id: uuid.UUID,
        period_start: date,
        period_end: date,
        entry_type: str,
        is_profit: bool,
    ) -> List[CashRegisterEntry]:
        stmt = (
            select(CashRegisterEntry)
            .where(
                CashRegisterEntry.store_id == store_id,
                CashRegisterEntry.occurred_on >= period_start,
                CashRegisterEntry.occurred_on <= period_end,
                CashRegisterEntry.entry_type == entry_type,
                CashRegisterEntry.is_profit.is_(is_profit),
            )
            .order_by(CashRegisterEntry.created_at.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def _list_auto_orders(self, period_start: date, period_end: date, period_view: CashPeriodView) -> List[dict]:
        stmt = (
            select(
                func.coalesce(func.nullif(Order.payment_method, ""), "Sem forma").label("payment_method"),
                func.coalesce(func.sum(Order.total_price), 0).label("amount"),
            )
            .where(
                func.date(Order.created_at) >= period_start,
                func.date(Order.created_at) <= period_end,
                Order.status != "canceled",
            )
            .group_by(func.coalesce(func.nullif(Order.payment_method, ""), "Sem forma"))
            .order_by(func.coalesce(func.nullif(Order.payment_method, ""), "Sem forma").asc())
        )

        rows = self.db.execute(stmt).all()
        period_label = {
            "day": "dia",
            "week": "semana",
            "month": "mês",
            "year": "ano",
        }[period_view]
        return [
            {
                "name": f"Pedidos do {period_label} - {str(row.payment_method).upper()}",
                "payment_method": str(row.payment_method),
                "amount": round(float(row.amount or 0), 2),
            }
            for row in rows
            if float(row.amount or 0) > 0
        ]

    def _resolve_period_range(self, target_date: date, period_view: CashPeriodView) -> tuple[date, date]:
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

    def _normalize_payment_method(self, payment_method: str | None) -> str | None:
        if payment_method is None:
            return None
        value = payment_method.strip()
        return value or None

    def _ensure_method(self, by_method_map: Dict[str, Dict[str, float]], method: str) -> None:
        if method not in by_method_map:
            by_method_map[method] = {"entries": 0.0, "expenses": 0.0}
