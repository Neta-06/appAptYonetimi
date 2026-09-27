"""Pydantic şemaları — API giriş/çıkış veri modelleri."""

from app.schemas.auth import (
    KullaniciRegisterRequest,
    KullaniciLoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    KullaniciResponse,
    KullaniciSiteResponse,
    LogoutRequest,
)
from app.schemas.site import (
    SiteTipiResponse,
    KullaniciSiteOzet,
    SiteResponse,
    SiteUyeResponse,
    AktifSiteResponse,
    UyeEkleRequest,
    UyeGuncelleRequest,
)
from app.schemas.daire import (
    DaireOzetResponse,
    DaireResponse,
    BlokResponse,
    DaireSakinResponse,
    DaireSayacResponse,
)
from app.schemas.aidat import (
    AidatOzetResponse,
    AidatResponse,
    AidatOzetIstatistik,
    DaireAidatGecmisi,
    OdemeDetayResponse,
    OdemeResponse,
    OdemeDetayliResponse,
    OdemeDetayCreate,
    OdemeCreateRequest,
    OdemeIptalRequest,
    AidatOlusturRequest,
    TopluAidatOlusturRequest,
    TopluAidatSonuc,
    AidatTipiResponse,
    OdemeKanaliResponse,
    OnayDurumResponse,
)
from app.schemas.gider import (
    GiderKategoriResponse,
    GiderKalemiResponse,
    CariHesapOzetResponse,
    GiderOzetResponse,
    GiderResponse,
    GiderKategoriOzet,
    GiderAylikOzet,
    GiderGenelOzet,
    GiderKarsilastirmaOzet,
    GiderCreateRequest,
    GiderUpdateRequest,
    GelirResponse,
    GelirCreateRequest,
    GelirUpdateRequest,
)

__all__ = [
    # Auth
    "KullaniciRegisterRequest", "KullaniciLoginRequest", "TokenResponse",
    "TokenRefreshRequest", "KullaniciResponse", "KullaniciSiteResponse",
    "LogoutRequest",
    # Site
    "SiteTipiResponse", "KullaniciSiteOzet", "SiteResponse",
    "SiteUyeResponse", "AktifSiteResponse", "UyeEkleRequest", "UyeGuncelleRequest",
    # Daire
    "DaireOzetResponse", "DaireResponse", "BlokResponse",
    "DaireSakinResponse", "DaireSayacResponse",
    # Aidat
    "AidatOzetResponse", "AidatResponse", "AidatOzetIstatistik",
    "DaireAidatGecmisi",
    "OdemeDetayResponse", "OdemeResponse", "OdemeDetayliResponse",
    "OdemeDetayCreate", "OdemeCreateRequest", "OdemeIptalRequest",
    "AidatOlusturRequest", "TopluAidatOlusturRequest", "TopluAidatSonuc",
    "AidatTipiResponse", "OdemeKanaliResponse", "OnayDurumResponse",
    # Gider
    "GiderKategoriResponse", "GiderKalemiResponse", "CariHesapOzetResponse",
    "GiderOzetResponse", "GiderResponse",
    "GiderKategoriOzet", "GiderAylikOzet", "GiderGenelOzet", "GiderKarsilastirmaOzet",
    "GiderCreateRequest", "GiderUpdateRequest",
    "GelirResponse", "GelirCreateRequest", "GelirUpdateRequest",
]