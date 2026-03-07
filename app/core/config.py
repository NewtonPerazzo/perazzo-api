from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # APP
    APP_NAME: str = "Perazzo API"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # DATABASE
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/perazzo_db"

    # JWT
    SECRET_KEY: str
    EMAIL_SECRET_KEY: str
    RESET_SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_EXPIRE_MINUTES: int = 60
    EMAIL_EXPIRE_MINUTES: int = 60 * 24
    RESET_EXPIRE_MINUTES: int = 15

    # CORS
    BACKEND_CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()