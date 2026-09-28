"""Demirbaş modülü Pydantic şemaları."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Yanıt Şemaları
# ============================================================

class DemirbasHareketResponse(BaseModel):
    """Demirbaş hareket kaydı."""

    model_config = ConfigDict(from_attributes=True)

    hareket_no: int
    demirbas_no: int
    hareket_tipi: str
    kullanici_no: int | None
    kullanici_ad: str | None = None
    tarih: datetime
    aciklama: str | None
    maliyet: Decimal | None


class DemirbasOzetResponse(BaseModel):
    """Demirbaş liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    demirbas_no: int
    site_no: int
    ad: str
    kategori: str | None
    adet: int
    alis_fiyati: Decimal | None
    alis_tarihi: date | None
    bulundugu_yer: str | None
    durum: str
    toplam_deger: Decimal | None = Field(
        default=None,
        description="alis_fiyati * adet",
    )
    hareket_sayisi: int = 0
    son_hareket_tarihi: datetime | None = None
    son_hareket_tipi: str | None = None


class DemirbasResponse(BaseModel):
    """Demirbaş detayı (hareketsiz)."""

    model_config = ConfigDict(from_attributes=True)

    demirbas_no: int
    site_no: int
    ad: str
    kategori: str | None
    adet: int
    alis_fiyati: Decimal | None
    alis_tarihi: date | None
    bulundugu_yer: str | None
    durum: str


class DemirbasDetayResponse(DemirbasResponse):
    """Demirbaş detayı + hareket geçmişi."""

    toplam_deger: Decimal | None = None
    toplam_bakim_maliyeti: Decimal = Field(default=Decimal("0.00"))
    hareketler: list[DemirbasHareketResponse] = Field(default_factory=list)


class DemirbasOzetStats(BaseModel):
    """Site geneli demirbaş özeti."""

    site_no: int
    toplam_kalem: int = Field(..., description="Toplam demirbaş kalemi")
    toplam_adet: int
    calisiyor: int
    arizali: int
    hurda: int
    toplam_deger: Decimal
    toplam_bakim_maliyeti: Decimal
    kategoriler: list[dict] = Field(
        default_factory=list,
        description="[{kategori, kalem, adet, deger}]",
    )


# ============================================================
# İstek Şemaları
# ============================================================

class DemirbasCreateRequest(BaseModel):
    """Yeni demirbaş kaydı."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ad": "Asansor",
                "kategori": "TASIMA",
                "adet": 2,
                "alis_fiyati": "800000.00",
                "alis_tarihi": "2020-05-01",
                "bulundugu_yer": "Bloklar",
                "durum": "CALISIYOR",
            }
        }
    )

    ad: str = Field(..., min_length=2, max_length=100)
    kategori: str | None = Field(default=None, max_length=50)
    adet: int = Field(default=1, ge=1, le=10000)
    alis_fiyati: Decimal | None = Field(default=None, ge=0)
    alis_tarihi: date | None = None
    bulundugu_yer: str | None = Field(default=None, max_length=100)
    durum: str = Field(
        default="CALISIYOR",
        pattern="^(CALISIYOR|ARIZALI|HURDA)$",
    )


class DemirbasUpdateRequest(BaseModel):
    """Demirbaş güncelleme (PATCH)."""

    ad: str | None = Field(default=None, min_length=2, max_length=100)
    kategori: str | None = Field(default=None, max_length=50)
    adet: int | None = Field(default=None, ge=1, le=10000)
    alis_fiyati: Decimal | None = Field(default=None, ge=0)
    alis_tarihi: date | None = None
    bulundugu_yer: str | None = Field(default=None, max_length=100)
    durum: str | None = Field(
        default=None,
        pattern="^(CALISIYOR|ARIZALI|HURDA)$",
    )


class DemirbasDurumDegistirRequest(BaseModel):
    """Demirbaş durum değiştirme."""

    durum: str = Field(..., pattern="^(CALISIYOR|ARIZALI|HURDA)$")
    aciklama: str | None = Field(default=None, max_length=255)


class HareketEkleRequest(BaseModel):
    """Demirbaşa hareket ekleme."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hareket_tipi": "BAKIM",
                "kullanici_no": 3,
                "aciklama": "Aylik periyodik bakim",
                "maliyet": "2500.00",
            }
        }
    )

    hareket_tipi: str = Field(
        ...,
        pattern="^(ZIMBET|BAKIM|ONARIM|YER_DEGISIKLIGI|HURDA)$",
    )
    kullanici_no: int | None = Field(default=None, ge=1)
    aciklama: str | None = Field(default=None, max_length=255)
    maliyet: Decimal | None = Field(default=None, ge=0)