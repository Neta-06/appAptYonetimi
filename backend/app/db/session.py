"""
Async veritabanı bağlantı yönetimi.
Engine, session factory ve FastAPI dependency'sini tanımlar.
"""

import logging
import app.core.audit  # noqa: F401 — audit event listener'larını yükle
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Async engine
# ------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    future=True,
)


# ------------------------------------------------------------
# Session factory
# ------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ------------------------------------------------------------
# FastAPI dependency
# ------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Her HTTP isteği için yeni bir veritabanı oturumu sağlar.
    İstek tamamlandığında oturum otomatik kapanır.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ------------------------------------------------------------
# Yardımcı fonksiyonlar
# ------------------------------------------------------------
async def dispose_engine() -> None:
    """
    Uygulama kapanırken bağlantı havuzunu temizler.
    """
    logger.info("Veritabanı bağlantı havuzu kapatılıyor...")
    await engine.dispose()
    logger.info("Veritabanı bağlantı havuzu kapatıldı.")