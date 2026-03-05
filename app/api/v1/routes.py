from fastapi import APIRouter

from app.api.v1.routers import product

api_router = APIRouter()

api_router.include_router(product.router, prefix="/products", tags=["Products"])