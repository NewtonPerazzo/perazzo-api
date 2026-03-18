import random
import string
import uuid
from datetime import date, datetime
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.domain.models.customer import Customer
from app.domain.models.delivery_method import DeliveryMethod
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate, ProductOrderCreate
from app.util.calculations import calculate_order_item_total, calculate_order_total


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: OrderCreate) -> Order:
        products_by_id = self._get_products_map([item.product_id for item in data.products])
        order_number = self._generate_order_number()

        customer = Customer(
            name=data.customer.name,
            phone=data.customer.phone,
            address=data.customer.address,
            neighborhood=data.customer.neighborhood,
            email=data.customer.email,
        )
        self.db.add(customer)
        self.db.flush()

        delivery_method = self._resolve_delivery_method(
            is_to_deliver=data.is_to_deliver,
            delivery_method_id=data.delivery_method_id,
        )

        order = Order(
            order_number=order_number,
            customer_id=customer.id,
            is_to_deliver=data.is_to_deliver,
            delivery_method_id=delivery_method.id if delivery_method else None,
            status="pending",
            payment_method=data.payment_method,
            observation=data.observation,
            total_price=0,
        )

        order_items, items_total = self._build_order_items(data.products, products_by_id)
        order.total_price = self._calculate_total_price(items_total, delivery_method)
        order.items = order_items

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return self.get_by_id(order.id)

    def update(self, order: Order, data: OrderUpdate) -> Order:
        products_by_id = self._get_products_map([item.product_id for item in data.products])
        delivery_method = self._resolve_delivery_method(
            is_to_deliver=data.is_to_deliver,
            delivery_method_id=data.delivery_method_id,
        )
        order_items, items_total = self._build_order_items(data.products, products_by_id)

        order.is_to_deliver = data.is_to_deliver
        order.delivery_method_id = delivery_method.id if delivery_method else None
        order.payment_method = data.payment_method
        order.observation = data.observation
        order.total_price = self._calculate_total_price(items_total, delivery_method)
        order.items = order_items

        order.customer.name = data.customer.name
        order.customer.phone = data.customer.phone
        order.customer.address = data.customer.address
        order.customer.neighborhood = data.customer.neighborhood
        order.customer.email = data.customer.email

        self.db.commit()
        self.db.refresh(order)
        return self.get_by_id(order.id)

    def delete(self, order: Order) -> None:
        self.db.delete(order)
        self.db.commit()

    def update_status(self, order: Order, status_value: str) -> Order:
        order.status = status_value
        self.db.commit()
        self.db.refresh(order)
        return self.get_by_id(order.id)

    def preview_total(self, products: List[ProductOrderCreate]) -> float:
        return self.preview_total_with_delivery(products=products, is_to_deliver=False, delivery_method_id=None)

    def preview_total_with_delivery(
        self,
        products: List[ProductOrderCreate],
        is_to_deliver: bool,
        delivery_method_id: uuid.UUID | None,
    ) -> float:
        products_by_id = self._get_products_map([item.product_id for item in products])
        item_totals: List[float] = []

        for item in products:
            product = products_by_id.get(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product not found: {item.product_id}",
                )
            item_total = calculate_order_item_total(item.amount, float(product.price))
            item_totals.append(item_total)

        delivery_method = self._resolve_delivery_method(
            is_to_deliver=is_to_deliver,
            delivery_method_id=delivery_method_id,
        )
        return self._calculate_total_price(calculate_order_total(item_totals), delivery_method)

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        order_date: date | None = None,
    ) -> List[Order]:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.delivery_method),
                selectinload(Order.items)
                .joinedload(OrderItem.product)
                .selectinload(Product.categories)
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        stmt = self._apply_filters(stmt, search=search, order_date=order_date)
        return self.db.execute(stmt).scalars().all()

    def count(self, search: str | None = None, order_date: date | None = None) -> int:
        stmt = select(func.count(Order.id))
        stmt = self._apply_filters(stmt, search=search, order_date=order_date)
        return int(self.db.execute(stmt).scalar_one())

    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.delivery_method),
                selectinload(Order.items)
                .joinedload(OrderItem.product)
                .selectinload(Product.categories)
            )
            .where(Order.id == order_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def serialize(self, order: Order) -> dict:
        customer_email = order.customer.email
        if customer_email and str(customer_email).endswith(".local"):
            customer_email = None

        return {
            "id": order.id,
            "order_number": order.order_number,
            "products": [
                {
                    "product": item.product,
                    "amount": item.amount,
                    "price": item.price,
                }
                for item in order.items
            ],
            "customer": {
                "id": order.customer.id,
                "name": order.customer.name,
                "phone": order.customer.phone,
                "address": order.customer.address,
                "neighborhood": order.customer.neighborhood,
                "email": customer_email,
                "created_at": order.customer.created_at,
            },
            "is_to_deliver": order.is_to_deliver,
            "delivery_method": order.delivery_method,
            "status": order.status,
            "payment_method": order.payment_method,
            "observation": order.observation,
            "total_price": order.total_price,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }

    def _get_products_map(self, product_ids: List[uuid.UUID]) -> Dict[uuid.UUID, Product]:
        unique_ids = list(dict.fromkeys(product_ids))
        stmt = (
            select(Product)
            .options(selectinload(Product.categories))
            .where(Product.is_active.is_(True))
            .where(Product.id.in_(unique_ids))
        )
        products = self.db.execute(stmt).scalars().all()
        return {product.id: product for product in products}

    def _generate_order_number(self) -> str:
        for _ in range(20):
            random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            order_number = f"#{random_part}"
            exists = self.db.execute(
                select(Order.id).where(Order.order_number == order_number)
            ).scalar_one_or_none()
            if not exists:
                return order_number

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate order number",
        )

    def _apply_filters(self, stmt, search: str | None, order_date: date | None):
        target_date = order_date or datetime.now().date()
        stmt = stmt.where(func.date(Order.created_at) == target_date)

        if not search:
            return stmt

        term = f"%{search.strip()}%"
        return stmt.where(
            or_(
                Order.order_number.ilike(term),
                Order.customer.has(
                    or_(
                        Customer.name.ilike(term),
                        Customer.phone.ilike(term),
                    )
                ),
                Order.items.any(
                    OrderItem.product.has(Product.name.ilike(term))
                ),
            )
        )

    def _resolve_delivery_method(
        self,
        is_to_deliver: bool,
        delivery_method_id: uuid.UUID | None,
    ) -> DeliveryMethod | None:
        if not is_to_deliver:
            return None

        if not delivery_method_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery method is required when delivery is selected",
            )

        method = self.db.execute(
            select(DeliveryMethod).where(DeliveryMethod.id == delivery_method_id)
        ).scalar_one_or_none()

        if not method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Delivery method not found",
            )

        return method

    def _calculate_total_price(self, items_total: float, delivery_method: DeliveryMethod | None) -> float:
        delivery_price = float(delivery_method.price) if delivery_method else 0.0
        return float(items_total + delivery_price)

    def _build_order_items(
        self,
        products: List[ProductOrderCreate],
        products_by_id: Dict[uuid.UUID, Product],
    ) -> tuple[List[OrderItem], float]:
        item_totals: List[float] = []
        order_items: List[OrderItem] = []

        for item in products:
            product = products_by_id.get(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product not found: {item.product_id}",
                )

            unit_price = float(product.price)
            item_total = calculate_order_item_total(item.amount, unit_price)
            item_totals.append(item_total)
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    amount=item.amount,
                    unit_price=unit_price,
                    price=item_total,
                )
            )

        return order_items, calculate_order_total(item_totals)
