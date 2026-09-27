"""
Kimlik doğrulama HTTP endpoint'leri.

Endpoint'ler:
  POST /register              - Yeni kullanıcı kaydı
  POST /login                 - Giriş yap, token al
  POST /refresh               - Access token yenile
  POST /logout                - Çıkış yap
  GET  /me                    - Aktif kullanıcı bilgisi
  POST /sifre-degistir        - Şifre değiştir (giriş yapmış)
  POST /sifre-sifirla-talebi  - E-posta ile sıfırlama linki
  POST /sifre-sifirla         - Token ile şifreyi sıfırla
"""

import logging

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rate_limit import rate_limit

from app.core.config import settings
from app.core.rbac import CurrentUser
from app.db.session import get_db
from app.schemas.auth import (
    KullaniciLoginRequest,
    KullaniciRegisterRequest,
    KullaniciResponse,
    LogoutRequest,
    MesajResponse,
    SifreDegistirRequest,
    SifreSifirlaRequest,
    SifreSifirlaTalebiRequest,
    TokenRefreshRequest,
    TokenResponse,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Kimlik Dogrulama"])


# ============================================================
# Yardımcılar
# ============================================================
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


def _set_refresh_cookie(response: Response, token: str) -> None:
    """
    Refresh token'ı HttpOnly cookie olarak ayarlar.
    Sadece web tarayıcı için — mobil uygulama body'deki token'ı kullanır.
    """
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True,             # JavaScript erişemez (XSS koruması)
        secure=settings.IS_PRODUCTION,  # Sadece HTTPS'de gönder (production)
        samesite="strict",         # CSRF koruması
        path="/api/v1/auth",       # Sadece auth endpoint'lerine gider
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Cookie'yi sil."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
    )


def _client_ip(request: Request) -> str | None:
    """Proxy arkasında gerçek IP'yi al."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


# ============================================================
# POST /register — Yeni kullanıcı kaydı
# ============================================================
@router.post(
    "/register",
    response_model=KullaniciResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanıcı kaydı",
    description=(
        "Yeni bir kullanıcı oluşturur. "
        "E-posta benzersiz olmalı, parola güçlü olmalı, KVKK onayı zorunlu."
    ),
)
async def register(
    data: KullaniciRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit("register")),
) -> KullaniciResponse:
    kullanici = await auth_service.register_user(
        db,
        data,
        ip_adresi=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return KullaniciResponse.model_validate(kullanici)


# ============================================================
# POST /login — Giriş
# ============================================================
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Giriş yap",
    description=(
        "E-posta + parola ile giriş yapar. "
        "Başarılıysa access + refresh token döner. "
        "Refresh token ayrıca HttpOnly cookie olarak da set edilir (web için)."
    ),
)
async def login(
    data: KullaniciLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit("login")),
) -> TokenResponse:
    kullanici = await auth_service.authenticate_user(
        db,
        e_posta=str(data.e_posta),
        parola=data.parola,
        ip_adresi=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    tokens = await auth_service.create_tokens(
        db,
        kullanici,
        ip_adresi=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return tokens


# ============================================================
# POST /refresh — Token yenile
# ============================================================
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Access token yenile",
    description=(
        "Refresh token ile yeni access + refresh token üretir. "
        "Refresh token rotation uygulanır: eski token iptal olur."
    ),
)
async def refresh(
    request: Request,
    response: Response,
    data: TokenRefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit("refresh")),
) -> TokenResponse:
    # Token body'den mi cookie'den mi?
    refresh_token: str | None = None
    if data and data.refresh_token:
        refresh_token = data.refresh_token
    else:
        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        from app.core.exceptions import KimlikDogrulanmadiHatasi
        raise KimlikDogrulanmadiHatasi(
            "Refresh token bulunamadi (ne body ne cookie)."
        )

    tokens = await auth_service.refresh_tokens(
        db,
        refresh_token,
        ip_adresi=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, tokens.refresh_token)
    return tokens


# ============================================================
# POST /logout — Çıkış
# ============================================================
@router.post(
    "/logout",
    response_model=MesajResponse,
    summary="Çıkış yap",
    description="Refresh token'ı iptal eder, cookie'yi temizler.",
)
@router.post(
    "/logout",
    response_model=MesajResponse,
    summary="Çıkış yap",
    description=(
        "Refresh token'ı iptal eder. Token hem body'den hem cookie'den kabul edilir. "
        "(Body → mobil uygulama, cookie → web tarayıcı)"
    ),
)
async def logout(
    request: Request,
    response: Response,
    data: LogoutRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> MesajResponse:
    refresh_token: str | None = None
    if data and data.refresh_token:
        refresh_token = data.refresh_token
    else:
        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token:
        from app.core.exceptions import KimlikDogrulanmadiHatasi
        raise KimlikDogrulanmadiHatasi(
            "Refresh token gerekli (body veya cookie)."
        )

    await auth_service.logout_user(db, refresh_token=refresh_token)
    _clear_refresh_cookie(response)
    return MesajResponse(mesaj="Cikis yapildi.")

# ============================================================
# GET /me — Aktif kullanıcı
# ============================================================
@router.get(
    "/me",
    response_model=KullaniciResponse,
    summary="Aktif kullanıcı bilgisi",
    description="Access token sahibi kullanıcının profilini döner.",
)
async def me(kullanici: CurrentUser) -> KullaniciResponse:
    return KullaniciResponse.model_validate(kullanici)


# ============================================================
# POST /sifre-degistir — Şifre değiştir
# ============================================================
@router.post(
    "/sifre-degistir",
    response_model=MesajResponse,
    summary="Şifre değiştir",
    description=(
        "Giriş yapmış kullanıcı eski parolasını doğrulayıp yenisini belirler. "
        "Tüm aktif oturumlar iptal edilir (güvenlik)."
    ),
)
async def sifre_degistir(
    data: SifreDegistirRequest,
    kullanici: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> MesajResponse:
    await auth_service.change_password(
        db,
        kullanici,
        eski_parola=data.eski_parola,
        yeni_parola=data.yeni_parola,
    )
    return MesajResponse(
        mesaj="Parolaniz degistirildi. Tum oturumlar kapatildi."
    )


# ============================================================
# POST /sifre-sifirla-talebi — E-posta ile sıfırlama
# ============================================================
@router.post(
    "/sifre-sifirla-talebi",
    response_model=MesajResponse,
    summary="Şifre sıfırlama talebi",
    description=(
        "Kayıtlı e-posta için sıfırlama token'ı üretir. "
        "Güvenlik: E-posta kayıtlı olsun veya olmasın aynı yanıt döner. "
        "(User enumeration önleme.)"
    ),
)
async def sifre_sifirla_talebi(
    data: SifreSifirlaTalebiRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MesajResponse:
    token = await auth_service.request_password_reset(
        db,
        e_posta=str(data.e_posta),
        ip_adresi=_client_ip(request),
    )

    # Token varsa e-posta ile gönderilir (sonraki adımda Celery task).
    if token:
        logger.info(
            "Sifre sifirlama token uretildi (email=%s). "
            "E-posta gonderimi Celery ile yapilacak.",
            data.e_posta,
        )
        # TODO: send_reset_email.delay(data.e_posta, token)

    return MesajResponse(
        mesaj=(
            "Eger bu e-posta sistemde kayitliysa sifirlama baglantisi gonderildi."
        )
    )


# ============================================================
# POST /sifre-sifirla — Token ile sıfırla
# ============================================================
@router.post(
    "/sifre-sifirla",
    response_model=MesajResponse,
    summary="Token ile şifre sıfırla",
    description=(
        "E-posta ile gelen token'ı kullanarak yeni parola belirler. "
        "Token tek kullanımlıktır."
    ),
)
async def sifre_sifirla(
    data: SifreSifirlaRequest,
    db: AsyncSession = Depends(get_db),
) -> MesajResponse:
    await auth_service.reset_password(
        db,
        token=data.token,
        yeni_parola=data.yeni_parola,
    )
    return MesajResponse(mesaj="Parolaniz sifirlandi. Giris yapabilirsiniz.")
