"""Aidat modülü Pydantic şemaları."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Aidat Yanıt Şemaları
# ============================================================

class AidatOzetResponse(BaseModel):
    """Aidat liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    aidat_no: int
    daire_no: int
    blok_adi: str
    daire_numarasi: str
    aidat_tipi: str
    donem_yil: int
    donem_ay: int
    tutar: Decimal
    odenen_tutar: Decimal
    kalan_tutar: Decimal
    son_odeme_tarihi: date
    durum: str


class AidatResponse(BaseModel):
    """Aidat detay görünümü."""

    model_config = ConfigDict(from_attributes=True)

    aidat_no: int
    site_no: int
    daire_no: int
    aidat_tipi_no: int
    donem_yil: int
    donem_ay: int
    tutar: Decimal
    odenen_tutar: Decimal
    son_odeme_tarihi: date
    durum: str
    otomatik_islendi_mi: bool
    olusturma_tarihi: datetime
    guncellenme_tarihi: datetime


class AidatOzetIstatistik(BaseModel):
    """Site geneli aidat özet istatistikleri."""

    toplam_tahakkuk: Decimal = Field(..., description="Toplam borçlandırılan")
    toplam_tahsilat: Decimal = Field(..., description="Toplam tahsil edilen")
    toplam_kalan: Decimal = Field(..., description="Kalan bakiye")
    odenmis_sayisi: int
    bekleyen_sayisi: int
    gecikmis_sayisi: int
    kismi_odenmis_sayisi: int
    tahsilat_orani: float = Field(..., description="Yüzde olarak tahsilat oranı")


class DaireAidatGecmisi(BaseModel):
    """Bir dairenin aidat geçmişi (özet)."""

    daire_no: int
    blok_adi: str
    daire_numarasi: str
    toplam_borc: Decimal
    toplam_odenen: Decimal
    kalan: Decimal
    aidatlar: list[AidatOzetResponse] = Field(default_factory=list)


# ============================================================
# Ödeme Yanıt Şemaları
# ============================================================

class OdemeDetayResponse(BaseModel):
    """Ödeme detayı — hangi aidatı kapattı."""

    model_config = ConfigDict(from_attributes=True)

    detay_no: int
    aidat_no: int | None
    gider_no: int | None
    tutar: Decimal
    aciklama: str | None


class OdemeResponse(BaseModel):
    """Ödeme görünümü."""

    model_config = ConfigDict(from_attributes=True)

    odeme_no: int
    site_no: int
    odeme_tarihi: datetime
    toplam_tutar: Decimal
    odeme_kanali_no: int
    dekont_no: str | None
    referans_no: str | None
    onay_durum_no: int
    onay_tarihi: datetime | None
    aciklama: str | None
    olusturan_no: int


class OdemeDetayliResponse(OdemeResponse):
    """Ödeme detaylı görünüm — detayları içerir."""

    detaylar: list[OdemeDetayResponse] = Field(default_factory=list)


# ============================================================
# İstek Şemaları
# ============================================================

class OdemeDetayCreate(BaseModel):
    """Ödeme detayı oluşturma (hangi aidatı kapatıyor)."""

    aidat_no: int
    tutar: Decimal = Field(..., gt=0, description="Ödeme tutarı (0'dan büyük)")


class OdemeCreateRequest(BaseModel):
    """Yeni ödeme (tahsilat) kaydı oluşturma."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "odeme_kanali_no": 1,
                "dekont_no": "HB-2026-0001",
                "referans_no": None,
                "aciklama": "Aidat tahsilatı",
                "detaylar": [
                    {"aidat_no": 1, "tutar": "1500.00"},
                ],
            }
        }
    )

    odeme_kanali_no: int
    dekont_no: str | None = Field(default=None, max_length=50)
    referans_no: str | None = Field(default=None, max_length=50)
    aciklama: str | None = Field(default=None, max_length=255)
    detaylar: list[OdemeDetayCreate] = Field(..., min_length=1)


class OdemeIptalRequest(BaseModel):
    """Ödeme iptal talebi."""

    iptal_nedeni: str = Field(..., min_length=3, max_length=255)


class AidatOlusturRequest(BaseModel):
    """Manuel aidat oluşturma (tek daire)."""

    daire_no: int
    aidat_tipi_no: int
    donem_yil: int = Field(..., ge=2020, le=2100)
    donem_ay: int = Field(..., ge=1, le=12)
    tutar: Decimal = Field(..., gt=0)
    son_odeme_tarihi: date


class TopluAidatOlusturRequest(BaseModel):
    """Toplu aidat oluşturma (site geneli)."""

    aidat_tipi_no: int
    donem_yil: int = Field(..., ge=2020, le=2100)
    donem_ay: int = Field(..., ge=1, le=12)
    son_odeme_tarihi: date
    blok_no: int | None = Field(
        default=None,
        description="Belirli bir blok için; None ise tüm site",
    )


class TopluAidatSonuc(BaseModel):
    """Toplu aidat oluşturma sonucu."""

    olusturulan_sayisi: int
    atlanan_sayisi: int
    toplam_tutar: Decimal
    aidat_nolar: list[int] = Field(default_factory=list)


# ============================================================
# Lookup Şemaları
# ============================================================

class AidatTipiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tip_no: int
    ad: str
    aciklama: str | None
    periyodik_mi: bool


class OdemeKanaliResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kanal_no: int
    ad: str


class OnayDurumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    durum_no: int
    ad: str