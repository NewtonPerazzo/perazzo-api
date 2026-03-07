from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.product import router as product_router
from app.api.v1.routers.store import router as store_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(product_router)
api_router.include_router(store_router)
