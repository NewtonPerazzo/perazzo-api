from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.cart import router as cart_router
from app.api.v1.routers.category import router as category_router
from app.api.v1.routers.customer import router as customer_router
from app.api.v1.routers.order import router as order_router
from app.api.v1.routers.payment_method import router as payment_method_router
from app.api.v1.routers.product import router as product_router
from app.api.v1.routers.store import router as store_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(cart_router)
api_router.include_router(category_router)
api_router.include_router(customer_router)
api_router.include_router(order_router)
api_router.include_router(payment_method_router)
api_router.include_router(product_router)
api_router.include_router(store_router)
