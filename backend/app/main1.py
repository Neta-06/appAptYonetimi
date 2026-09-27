"""
FastAPI uygulamasının giriş noktası.
Uygulamayı oluşturur, middleware'leri ve router'ları bağlar.
"""

# ============================================================
# Import'lar — HEPSİ EN ÜSTTE
# ============================================================
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.db.session import dispose_engine, engine

# ============================================================
# Loglama
# ============================================================
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# Yaşam döngüsü (lifespan)
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama başlarken ve kapanırken çalışacak kod.
    """
    # -------- STARTUP --------
    logger.info("=" * 60)
    logger.info("%s v%s başlatılıyor...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Ortam: %s", settings.ENVIRONMENT)
    logger.info("Debug: %s", settings.DEBUG)
    logger.info(
        "Veritabanı: %s:%s/%s",
        settings.DB_HOST, settings.DB_PORT, settings.DB_NAME,
    )
    logger.info("=" * 60)

    # Veritabanı bağlantısını test et
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("[OK] Veritabani baglantisi basarili.")
    except Exception as exc:
        logger.error("[FAIL] Veritabani baglanti hatasi: %s", exc)
        raise

    yield  # Uygulama burada çalışır

    # -------- SHUTDOWN --------
    logger.info("Uygulama kapatiliyor...")
    await dispose_engine()
    logger.info("Uygulama kapatildi.")


# ============================================================
# FastAPI uygulaması
# ============================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Çoklu apartman yönetim sistemi API'si",
    docs_url="/docs" if not settings.IS_PRODUCTION else None,
    redoc_url="/redoc" if not settings.IS_PRODUCTION else None,
    openapi_url="/openapi.json" if not settings.IS_PRODUCTION else None,
    lifespan=lifespan,
)


# ============================================================
# CORS middleware
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# ============================================================
# Request ID middleware
# ============================================================
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Her isteğe benzersiz bir ID atar.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ============================================================
# Güvenlik başlıkları middleware
# ============================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    OWASP önerisi güvenlik başlıklarını ekler.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"

    if settings.IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
    return response


# ============================================================
# Global hata yakalayıcıları
# ============================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Pydantic doğrulama hatalarını okunabilir JSON'a çevirir.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Gönderilen veriler geçersiz.",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ============================================================
# Sistem endpoint'leri
# ============================================================
@app.get("/", tags=["System"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Uygulama sağlık kontrolü.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ============================================================
# Router'lar (sonraki adımlarda eklenecek)
# ============================================================
# from app.api.v1.router import api_router
# app.include_router(api_router, prefix=settings.API_V1_PREFIX)