from fastapi import FastAPI

from app.api.v1.routes import product


app = FastAPI(
    title="Perazzo API",
    version="1.0.0"
)

app.include_router(
    product.router,
    prefix="/api/v1"
)