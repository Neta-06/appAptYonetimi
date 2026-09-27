"""
Uygulama ayarlarını yönetir.
.env dosyasından okur, doğrular ve tip güvenli bir şekilde sunar.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

logger = logging.getLogger(__name__)

# .env dosyasının mutlak yolu (backend/.env)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Uygulama ---
    APP_NAME: str = "appApartman"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # --- API ---
    API_V1_PREFIX: str = "/api/v1"

    # --- Veritabanı ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "appApartman"
    DB_PASSWORD: str = ""
    DB_NAME: str = "appApartman_gelistirme"
    DB_ECHO: bool = False

    # --- Güvenlik ---
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AES_KEY: str = Field(..., min_length=32)

    # --- Redis & Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
        # --- Rate Limiting ---
    RATE_LIMIT_ENABLED: bool = True

    # --- CORS ---
    # NoDecode: pydantic-settings'in JSON parse etmesini engeller.
    # Böylece field_validator virgüllü string'i listeye çevirebilir.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:19006",
    ]

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    @computed_field
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == "production"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()