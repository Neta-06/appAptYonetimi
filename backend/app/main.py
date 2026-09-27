"""
FastAPI uygulamasının giriş noktası.
"""

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text


from app.core.config import settings
from app.core.exceptions import AppException
from app.core.rate_limit import close_redis
from app.db.session import dispose_engine, engine
from app.middleware.audit_middleware import AuditContextMiddleware
from app.models import *  # noqa: F401, F403

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("%s v%s başlatılıyor...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Ortam: %s", settings.ENVIRONMENT)
    logger.info("Debug: %s", settings.DEBUG)
    logger.info("Veritabanı: %s:%s/%s", settings.DB_HOST, settings.DB_PORT, settings.DB_NAME)
    logger.info("=" * 60)

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("[OK] Veritabani baglantisi basarili.")
    except Exception as exc:
        logger.error("[FAIL] Veritabani baglanti hatasi: %s", exc)
        raise

    yield

    logger.info("Uygulama kapatiliyor...")
    await close_redis()
    await dispose_engine()
    logger.info("Uygulama kapatildi.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Çoklu apartman yönetim sistemi API'si",
    docs_url="/docs" if not settings.IS_PRODUCTION else None,
    redoc_url="/redoc" if not settings.IS_PRODUCTION else None,
    openapi_url="/openapi.json" if not settings.IS_PRODUCTION else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Audit context middleware
app.add_middleware(AuditContextMiddleware)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
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
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "AppException: %s %s -> %s (request_id=%s)",
        exc.status_code, exc.kod, exc.mesaj, request_id,
    )
    body = exc.to_dict()
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Gönderilen veriler geçersiz.",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Beklenmeyen hata (request_id=%s): %s", request_id, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "Beklenmeyen bir hata oluştu.",
            "request_id": request_id,
        },
    )


# ============================================================
# Sistem endpoint'leri
# ============================================================
@app.get("/", tags=["System"])
async def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ============================================================
# Router'lar
# ============================================================
from app.api.v1.router import api_router  # noqa: E402

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
