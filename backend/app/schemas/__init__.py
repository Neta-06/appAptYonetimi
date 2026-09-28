"""Pydantic şemaları — API giriş/çıkış veri modelleri."""

from app.schemas.auth import (
    KullaniciRegisterRequest, KullaniciLoginRequest, TokenResponse,
    TokenRefreshRequest, KullaniciResponse, KullaniciSiteResponse, LogoutRequest,
)
from app.schemas.site import (
    SiteTipiResponse, KullaniciSiteOzet, SiteResponse,
    SiteUyeResponse, AktifSiteResponse, UyeEkleRequest, UyeGuncelleRequest,
)
from app.schemas.daire import (
    DaireOzetResponse, DaireResponse, BlokResponse,
    DaireSakinResponse, DaireSayacResponse,
)
from app.schemas.aidat import (
    AidatOzetResponse, AidatResponse, AidatOzetIstatistik, DaireAidatGecmisi,
    OdemeDetayResponse, OdemeResponse, OdemeDetayliResponse,
    OdemeDetayCreate, OdemeCreateRequest, OdemeIptalRequest,
    AidatOlusturRequest, TopluAidatOlusturRequest, TopluAidatSonuc,
    AidatTipiResponse, OdemeKanaliResponse, OnayDurumResponse,
)
from app.schemas.gider import (
    GiderKategoriResponse, GiderKalemiResponse, CariHesapOzetResponse,
    GiderOzetResponse, GiderResponse,
    GiderKategoriOzet, GiderAylikOzet, GiderGenelOzet, GiderKarsilastirmaOzet,
    GiderCreateRequest, GiderUpdateRequest,
    GelirResponse, GelirCreateRequest, GelirUpdateRequest,
)
from app.schemas.rapor import (
    DaireOzet, SakinOzet, AidatOzetDashboard, FinansalOzetDashboard,
    DashboardResponse, AylikFinansal, FinansalOzetResponse,
    AidatDurumResponse, GiderDagilimResponse,
    BlokDoluluk, DaireDolulukResponse,
    BorcluDaire, BorcluDairelerResponse,
    AylikTrend, TrendResponse,
)
from app.schemas.duyuru import (
    DuyuruOzetResponse, DuyuruResponse, DuyuruDetayResponse,
    DuyuruOkumaResponse, DuyuruOkumaDurumResponse,
    DuyuruCreateRequest, DuyuruUpdateRequest,
)
from app.schemas.is_takip import (
    IsOncelikResponse, IsDurumResponse,
    IsEmriOzetResponse, IsEmriGuncellemeResponse,
    IsEmriMalzemeResponse, IsEmriDetayResponse,
    IsEmriDurumOzet, IsEmriOncelikOzet, IsEmriGenelOzet,
    IsEmriCreateRequest, IsEmriUpdateRequest,
    IsEmriDurumDegistirRequest, IsEmriGuncellemeCreateRequest,
    IsEmriMalzemeCreateRequest,
)
from app.schemas.sayac import (
    SayacBirimResponse, SayacTuruResponse,
    DaireSayaciOzetResponse, DaireSayaciResponse,
    SayacOkumaOzetResponse, SayacOkumaResponse,
    SayacFaturaPayiResponse, SayacFaturasiOzetResponse, SayacFaturasiResponse,
    SayacTuketimOzet, SayacGenelOzet,
    DaireSayaciCreateRequest, DaireSayaciUpdateRequest,
    SayacOkumaCreateRequest, SayacFaturasiCreateRequest,
)
from app.schemas.sakin import (
    SakinOzetResponse, SakinResponse, SakinDetayResponse, SakinOzetStats,
    SakinCreateRequest, SakinUpdateRequest,
    SakinCikisRequest, SakinTasindiRequest,
    SakinCikisSonuc, SakinTasindiSonuc,
)
from app.schemas.anket import (
    AnketSecenekResponse, AnketSecenekSonuc,
    AnketOzetResponse, AnketDetayResponse, AnketSonucResponse,
    OyKullanSonuc,
    AnketCreateRequest, AnketUpdateRequest, OyKullanRequest,
)
from app.schemas.toplanti import (
    ToplantiKatilimciResponse, ToplantiKararResponse,
    ToplantiOzetResponse, ToplantiDetayResponse, ToplantiOzetStats,
    ToplantiCreateRequest, ToplantiUpdateRequest,
    ToplantiDurumDegistirRequest,
    KatilimciEkleRequest, KatilimciGuncelleRequest, KararEkleRequest,
)
from app.schemas.demirbas import (
    DemirbasHareketResponse, DemirbasOzetResponse,
    DemirbasResponse, DemirbasDetayResponse, DemirbasOzetStats,
    DemirbasCreateRequest, DemirbasUpdateRequest,
    DemirbasDurumDegistirRequest, HareketEkleRequest,
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
    "DaireAidatGecmisi", "OdemeDetayResponse", "OdemeResponse",
    "OdemeDetayliResponse", "OdemeDetayCreate", "OdemeCreateRequest",
    "OdemeIptalRequest", "AidatOlusturRequest", "TopluAidatOlusturRequest",
    "TopluAidatSonuc", "AidatTipiResponse", "OdemeKanaliResponse", "OnayDurumResponse",
    # Gider
    "GiderKategoriResponse", "GiderKalemiResponse", "CariHesapOzetResponse",
    "GiderOzetResponse", "GiderResponse",
    "GiderKategoriOzet", "GiderAylikOzet", "GiderGenelOzet", "GiderKarsilastirmaOzet",
    "GiderCreateRequest", "GiderUpdateRequest",
    "GelirResponse", "GelirCreateRequest", "GelirUpdateRequest",
    # Rapor
    "DaireOzet", "SakinOzet", "AidatOzetDashboard", "FinansalOzetDashboard",
    "DashboardResponse", "AylikFinansal", "FinansalOzetResponse",
    "AidatDurumResponse", "GiderDagilimResponse",
    "BlokDoluluk", "DaireDolulukResponse",
    "BorcluDaire", "BorcluDairelerResponse",
    "AylikTrend", "TrendResponse",
    # Duyuru
    "DuyuruOzetResponse", "DuyuruResponse", "DuyuruDetayResponse",
    "DuyuruOkumaResponse", "DuyuruOkumaDurumResponse",
    "DuyuruCreateRequest", "DuyuruUpdateRequest",
    # Is Takip
    "IsOncelikResponse", "IsDurumResponse",
    "IsEmriOzetResponse", "IsEmriGuncellemeResponse",
    "IsEmriMalzemeResponse", "IsEmriDetayResponse",
    "IsEmriDurumOzet", "IsEmriOncelikOzet", "IsEmriGenelOzet",
    "IsEmriCreateRequest", "IsEmriUpdateRequest",
    "IsEmriDurumDegistirRequest", "IsEmriGuncellemeCreateRequest",
    "IsEmriMalzemeCreateRequest",
    # Sayac
    "SayacBirimResponse", "SayacTuruResponse",
    "DaireSayaciOzetResponse", "DaireSayaciResponse",
    "SayacOkumaOzetResponse", "SayacOkumaResponse",
    "SayacFaturaPayiResponse", "SayacFaturasiOzetResponse", "SayacFaturasiResponse",
    "SayacTuketimOzet", "SayacGenelOzet",
    "DaireSayaciCreateRequest", "DaireSayaciUpdateRequest",
    "SayacOkumaCreateRequest", "SayacFaturasiCreateRequest",
    # Sakin
    "SakinOzetResponse", "SakinResponse", "SakinDetayResponse", "SakinOzetStats",
    "SakinCreateRequest", "SakinUpdateRequest",
    "SakinCikisRequest", "SakinTasindiRequest",
    "SakinCikisSonuc", "SakinTasindiSonuc",
    # Anket
    "AnketSecenekResponse", "AnketSecenekSonuc",
    "AnketOzetResponse", "AnketDetayResponse", "AnketSonucResponse",
    "OyKullanSonuc",
    "AnketCreateRequest", "AnketUpdateRequest", "OyKullanRequest",
    # Toplanti
    "ToplantiKatilimciResponse", "ToplantiKararResponse",
    "ToplantiOzetResponse", "ToplantiDetayResponse", "ToplantiOzetStats",
    "ToplantiCreateRequest", "ToplantiUpdateRequest",
    "ToplantiDurumDegistirRequest",
    "KatilimciEkleRequest", "KatilimciGuncelleRequest", "KararEkleRequest",
    # Demirbas
    "DemirbasHareketResponse", "DemirbasOzetResponse",
    "DemirbasResponse", "DemirbasDetayResponse", "DemirbasOzetStats",
    "DemirbasCreateRequest", "DemirbasUpdateRequest",
    "DemirbasDurumDegistirRequest", "HareketEkleRequest",
]