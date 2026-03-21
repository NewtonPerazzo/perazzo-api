import uuid
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.models.cart import Cart
from app.domain.models.cart_item import CartItem
from app.domain.models.product import Product
from app.schemas.cart import CartCreate, CartPatch, ProductCartCreate
from app.schemas.order import OrderCreate, ProductOrderCreate
from app.services.order import OrderService
from app.util.calculations import calculate_order_item_total, calculate_order_total


class CartService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CartCreate) -> Cart:
        products_by_id = self._get_products_map([data.product.product_id])
        product = products_by_id.get(data.product.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product not found: {data.product.product_id}",
            )
        self._ensure_stock_available(product, data.product.amount)

        unit_price = float(product.price)
        item_total = calculate_order_item_total(data.product.amount, unit_price)

        cart = Cart(total_price=item_total)
        cart.items = [
            CartItem(
                product_id=product.id,
                amount=data.product.amount,
                unit_price=unit_price,
                price=item_total,
            )
        ]

        self.db.add(cart)
        self.db.commit()
        self.db.refresh(cart)
        return self.get_by_id(cart.id)

    def get_by_id(self, cart_id: uuid.UUID) -> Cart | None:
        stmt = (
            select(Cart)
            .options(
                selectinload(Cart.items)
                .joinedload(CartItem.product)
                .selectinload(Product.categories)
            )
            .where(Cart.id == cart_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, skip: int = 0, limit: int = 20) -> List[Cart]:
        stmt = (
            select(Cart)
            .options(
                selectinload(Cart.items)
                .joinedload(CartItem.product)
                .selectinload(Product.categories)
            )
            .offset(skip)
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def patch(self, cart: Cart, data: CartPatch) -> Cart:
        if data.products:
            self._append_products(cart, data.products)

        if data.customer is not None:
            cart.customer_name = data.customer.name
            cart.customer_phone = data.customer.phone
            cart.customer_address = data.customer.address
            cart.customer_email = data.customer.email

        if data.is_to_deliver is not None:
            cart.is_to_deliver = data.is_to_deliver

        if data.payment_method is not None:
            cart.payment_method = data.payment_method

        self._recalculate_total(cart)
        self.db.commit()
        self.db.refresh(cart)
        return self.get_by_id(cart.id)

    def replace_products(self, cart: Cart, products: List[ProductCartCreate]) -> Cart | None:
        if len(products) == 0:
            self.db.delete(cart)
            self.db.commit()
            return None

        cart.items = []
        self._append_products(cart, products)
        self._recalculate_total(cart)
        self.db.commit()
        self.db.refresh(cart)
        return self.get_by_id(cart.id)

    def delete(self, cart: Cart) -> None:
        self.db.delete(cart)
        self.db.commit()

    def checkout(self, cart: Cart) -> dict:
        if not cart.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart has no products")
        if not cart.customer_name or not cart.customer_phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart customer data is required")
        if not cart.payment_method:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart payment method is required")

        order_payload = OrderCreate(
            products=[
                ProductOrderCreate(product_id=item.product_id, amount=item.amount)
                for item in cart.items
            ],
            customer={
                "name": cart.customer_name,
                "phone": cart.customer_phone,
                "address": cart.customer_address,
                "email": cart.customer_email,
            },
            is_to_deliver=bool(cart.is_to_deliver),
            payment_method=cart.payment_method,
        )

        order_service = OrderService(self.db)
        order = order_service.create(data=order_payload)
        order_data = order_service.serialize(order)

        self.db.delete(cart)
        self.db.commit()

        return order_data

    def serialize(self, cart: Cart) -> dict:
        customer_data = None
        if cart.customer_name and cart.customer_phone:
            customer_data = {
                "name": cart.customer_name,
                "phone": cart.customer_phone,
                "address": cart.customer_address,
                "email": cart.customer_email,
            }

        return {
            "id": cart.id,
            "products": [
                {
                    "product": item.product,
                    "amount": item.amount,
                    "price": item.price,
                }
                for item in cart.items
            ],
            "customer": customer_data,
            "is_to_deliver": cart.is_to_deliver,
            "payment_method": cart.payment_method,
            "total_price": cart.total_price,
            "created_at": cart.created_at,
            "updated_at": cart.updated_at,
        }

    def _append_products(self, cart: Cart, products: List[ProductCartCreate]) -> None:
        products_by_id = self._get_products_map([item.product_id for item in products])
        existing_by_product: Dict[uuid.UUID, CartItem] = {item.product_id: item for item in cart.items}

        for product_item in products:
            product = products_by_id.get(product_item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product not found: {product_item.product_id}",
                )

            unit_price = float(product.price)
            if product_item.product_id in existing_by_product:
                existing_item = existing_by_product[product_item.product_id]
                next_amount = existing_item.amount + product_item.amount
                self._ensure_stock_available(product, next_amount)
                existing_item.amount = next_amount
                existing_item.unit_price = unit_price
                existing_item.price = calculate_order_item_total(existing_item.amount, unit_price)
            else:
                self._ensure_stock_available(product, product_item.amount)
                new_item = CartItem(
                    product_id=product.id,
                    amount=product_item.amount,
                    unit_price=unit_price,
                    price=calculate_order_item_total(product_item.amount, unit_price),
                )
                cart.items.append(new_item)
                existing_by_product[product_item.product_id] = new_item

    def _recalculate_total(self, cart: Cart) -> None:
        item_totals = [item.price for item in cart.items]
        cart.total_price = calculate_order_total(item_totals)

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

    def _ensure_stock_available(self, product: Product, requested_amount: int) -> None:
        if requested_amount <= 0:
            return
        if product.stock is None:
            return
        if int(requested_amount) > int(product.stock):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock: only {int(product.stock)} units",
            )
