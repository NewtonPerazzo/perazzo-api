from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import api_router


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG
)

cors_origins = [
    origin.strip().rstrip("/")
    for origin in settings.BACKEND_CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX
)


@app.get("/health")
def health():
    return {"status": "ok"}
