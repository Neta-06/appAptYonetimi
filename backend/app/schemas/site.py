"""
Site yönetimi Pydantic şemaları.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Site Tipi
# ============================================================
class SiteTipiResponse(BaseModel):
    """Site tipi — APARTMAN, SITE, REZIDANS, PLAZA."""

    model_config = ConfigDict(from_attributes=True)

    tip_no: int
    ad: str


# ============================================================
# Kullanıcının site üyeliği (liste görünümü)
# ============================================================
class KullaniciSiteOzet(BaseModel):
    """Kullanıcının bir sitedeki üyeliği — liste için."""

    model_config = ConfigDict(from_attributes=True)

    site_no: int
    site_adi: str
    site_tipi: str
    il: str | None
    ilce: str | None
    rol_no: int
    rol_adi: str
    aktif_mi: bool


# ============================================================
# Site detay
# ============================================================
class SiteResponse(BaseModel):
    """Site detay yanıtı."""

    model_config = ConfigDict(from_attributes=True)

    site_no: int
    firma_no: int
    site_adi: str
    site_tipi_no: int
    adres: str | None
    il: str | None
    ilce: str | None
    daire_sayisi: int
    aylik_aidat: Decimal
    aidat_gunu: int
    otomatik_borclandir: bool
    aktif_mi: bool


# ============================================================
# Site üyesi
# ============================================================
class SiteUyeResponse(BaseModel):
    """Bir siteye üye kullanıcı (yönetici görünümü)."""

    kullanici_no: int
    ad: str
    soyad: str
    e_posta: str
    rol_no: int
    rol_adi: str
    baslangic_tarihi: date
    bitis_tarihi: date | None
    aktif_mi: bool


# ============================================================
# Aktif site bilgisi (X-Site-Id ile gelen)
# ============================================================
class AktifSiteResponse(BaseModel):
    """X-Site-Id header'ı ile aktif site bilgisi."""

    site_no: int
    site_adi: str
    site_tipi: str
    rol_adi: str
    yetkiler: list[str] = Field(default_factory=list)


# ============================================================
# Kullanıcı-site güncelleme (yönetici)
# ============================================================
class UyeEkleRequest(BaseModel):
    """Siteye yeni üye ekleme."""

    e_posta: str
    rol_no: int
    baslangic_tarihi: date | None = None
    bitis_tarihi: date | None = None


class UyeGuncelleRequest(BaseModel):
    """Üye rolünü / aktifliğini güncelleme."""

    rol_no: int | None = None
    bitis_tarihi: date | None = None
    aktif_mi: bool | None = None
