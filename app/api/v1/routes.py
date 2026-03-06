from fastapi import APIRouter

from app.api.v1.routers import product
from app.api.v1.routers import auth


api_router = APIRouter()

api_router.include_router(product.router, prefix="/products", tags=["Products"])
api_router.include_router(auth.router)