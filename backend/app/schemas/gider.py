"""Gider ve gelir modülü Pydantic şemaları."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Lookup Şemaları
# ============================================================

class GiderKategoriResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kategori_no: int
    ad: str


class GiderKalemiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kalem_no: int
    kalem_adi: str
    kategori_no: int
    kategori_adi: str


class CariHesapOzetResponse(BaseModel):
    """Cari hesap özet (gider formunda dropdown için)."""

    model_config = ConfigDict(from_attributes=True)

    cari_no: int
    unvan: str
    vergi_no: str | None
    telefon: str | None
    aktif_mi: bool


# ============================================================
# Gider Yanıt Şemaları
# ============================================================

class GiderOzetResponse(BaseModel):
    """Gider liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    gider_no: int
    gider_tarihi: date
    kalem_no: int
    kalem_adi: str
    kategori_no: int
    kategori_adi: str
    cari_no: int | None
    cari_unvan: str | None
    tutar: Decimal
    kdv_tutar: Decimal
    toplam_tutar: Decimal
    belge_no: str | None
    aciklama: str | None


class GiderResponse(BaseModel):
    """Gider detay görünümü."""

    model_config = ConfigDict(from_attributes=True)

    gider_no: int
    site_no: int
    kalem_no: int
    cari_no: int | None
    tutar: Decimal
    kdv_tutar: Decimal
    gider_tarihi: date
    belge_no: str | None
    aciklama: str | None
    kaydeden_no: int
    olusturma_tarihi: datetime
    guncellenme_tarihi: datetime


class GiderKategoriOzet(BaseModel):
    """Kategori bazlı gider özeti."""

    kategori_no: int
    kategori_adi: str
    toplam_tutar: Decimal
    kayit_sayisi: int
    yuzde: float = Field(..., description="Toplam içindeki yüzde pay")


class GiderAylikOzet(BaseModel):
    """Aylık gider özeti (trend analizi için)."""

    donem_yil: int
    donem_ay: int
    toplam_tutar: Decimal
    kayit_sayisi: int


class GiderGenelOzet(BaseModel):
    """Site geneli gider özeti."""

    toplam_gider: Decimal
    toplam_kdv: Decimal
    toplam_genel: Decimal
    kayit_sayisi: int
    ortalama_gider: Decimal
    en_yuksek_gider: Decimal
    en_dusuk_gider: Decimal


class GiderKarsilastirmaOzet(BaseModel):
    """Aylık gider-gelir karşılaştırma özeti."""

    donem_yil: int
    donem_ay: int
    toplam_gider: Decimal
    toplam_gelir: Decimal
    net_durum: Decimal = Field(..., description="Gelir - Gider")
    kar_zarar: str = Field(..., description="KAR veya ZARAR")


# ============================================================
# Gider İstek Şemaları
# ============================================================

class GiderCreateRequest(BaseModel):
    """Yeni gider kaydı oluşturma."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "kalem_no": 1,
                "cari_no": 1,
                "tutar": "2500.00",
                "kdv_tutar": "450.00",
                "gider_tarihi": "2026-10-01",
                "belge_no": "FTR-1001",
                "aciklama": "Ekim asansör bakımı",
            }
        }
    )

    kalem_no: int = Field(..., ge=1)
    cari_no: int | None = Field(default=None, ge=1)
    tutar: Decimal = Field(..., gt=0, description="KDV hariç tutar")
    kdv_tutar: Decimal = Field(
        default=Decimal("0.00"), ge=0, description="KDV tutarı"
    )
    gider_tarihi: date
    belge_no: str | None = Field(default=None, max_length=50)
    aciklama: str | None = Field(default=None, max_length=255)


class GiderUpdateRequest(BaseModel):
    """Gider güncelleme (PATCH — tüm alanlar opsiyonel)."""

    kalem_no: int | None = Field(default=None, ge=1)
    cari_no: int | None = Field(default=None, ge=1)
    tutar: Decimal | None = Field(default=None, gt=0)
    kdv_tutar: Decimal | None = Field(default=None, ge=0)
    gider_tarihi: date | None = None
    belge_no: str | None = Field(default=None, max_length=50)
    aciklama: str | None = Field(default=None, max_length=255)


# ============================================================
# Gelir Şemaları
# ============================================================

class GelirResponse(BaseModel):
    """Gelir görünümü."""

    model_config = ConfigDict(from_attributes=True)

    gelir_no: int
    site_no: int
    kaynak: str
    tutar: Decimal
    gelir_tarihi: date
    aciklama: str | None
    kaydeden_no: int
    olusturma_tarihi: datetime


class GelirCreateRequest(BaseModel):
    """Yeni gelir kaydı."""

    kaynak: str = Field(..., min_length=2, max_length=100)
    tutar: Decimal = Field(..., gt=0)
    gelir_tarihi: date
    aciklama: str | None = Field(default=None, max_length=255)


class GelirUpdateRequest(BaseModel):
    """Gelir güncelleme."""

    kaynak: str | None = Field(default=None, min_length=2, max_length=100)
    tutar: Decimal | None = Field(default=None, gt=0)
    gelir_tarihi: date | None = None
    aciklama: str | None = Field(default=None, max_length=255)