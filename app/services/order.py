import random
import string
import uuid
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models.customer import Customer
from app.domain.models.order import Order
from app.domain.models.order_item import OrderItem
from app.domain.models.product import Product
from app.schemas.order import OrderCreate
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
            email=data.customer.email,
        )
        self.db.add(customer)
        self.db.flush()

        order = Order(
            order_number=order_number,
            customer_id=customer.id,
            is_to_deliver=data.is_to_deliver,
            payment_method=data.payment_method,
            total_price=0,
        )

        item_totals: List[float] = []
        order_items: List[OrderItem] = []
        for item in data.products:
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

        order.total_price = calculate_order_total(item_totals)
        order.items = order_items

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return self.get_by_id(order.id)

    def list(self, skip: int = 0, limit: int = 20) -> List[Order]:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items)
                .joinedload(OrderItem.product)
                .selectinload(Product.categories)
            )
            .offset(skip)
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.customer),
                selectinload(Order.items)
                .joinedload(OrderItem.product)
                .selectinload(Product.categories)
            )
            .where(Order.id == order_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def serialize(self, order: Order) -> dict:
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
            "customer": order.customer,
            "is_to_deliver": order.is_to_deliver,
            "payment_method": order.payment_method,
            "total_price": order.total_price,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
        }

    def _get_products_map(self, product_ids: List[uuid.UUID]) -> Dict[uuid.UUID, Product]:
        unique_ids = list(dict.fromkeys(product_ids))
        stmt = (
            select(Product)
            .options(selectinload(Product.categories))
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
