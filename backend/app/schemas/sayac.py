"""Sayaç modülü Pydantic şemaları."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Lookup Şemaları
# ============================================================

class SayacBirimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    birim_no: int
    ad: str


class SayacTuruResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sayac_turu_no: int
    adi: str
    birim_no: int
    birim_ad: str


# ============================================================
# Daire Sayacı
# ============================================================

class DaireSayaciOzetResponse(BaseModel):
    """Daire sayacı liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    daire_sayac_no: int
    daire_no: int
    sayac_turu_no: int
    sayac_turu: str
    birim: str
    seri_no: str
    montaj_tarihi: date | None
    sokulme_tarihi: date | None
    ilk_deger: Decimal
    aktif_mi: bool
    son_okuma_degeri: Decimal | None = Field(
        default=None,
        description="En son okuma değeri",
    )
    son_okuma_tarihi: date | None = None


class DaireSayaciResponse(BaseModel):
    """Daire sayacı detay."""

    model_config = ConfigDict(from_attributes=True)

    daire_sayac_no: int
    daire_no: int
    sayac_turu_no: int
    seri_no: str
    montaj_tarihi: date | None
    sokulme_tarihi: date | None
    ilk_deger: Decimal
    aktif_mi: bool


# ============================================================
# Okuma
# ============================================================

class SayacOkumaOzetResponse(BaseModel):
    """Okuma liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    okuma_no: int
    daire_sayac_no: int
    okuma_tarihi: date
    guncel_deger: Decimal
    tuketim: Decimal | None
    okuyan_no: int | None
    okuyan_ad: str | None = None
    olusturma_tarihi: datetime


class SayacOkumaResponse(BaseModel):
    """Okuma detayı."""

    model_config = ConfigDict(from_attributes=True)

    okuma_no: int
    daire_sayac_no: int
    okuma_tarihi: date
    guncel_deger: Decimal
    tuketim: Decimal | None
    okuyan_no: int | None
    olusturma_tarihi: datetime


# ============================================================
# Fatura
# ============================================================

class SayacFaturaPayiResponse(BaseModel):
    """Fatura payı — bir daireye düşen."""

    model_config = ConfigDict(from_attributes=True)

    pay_no: int
    fatura_no: int
    daire_no: int
    daire_ozet: str | None = None
    tuketim: Decimal
    daire_tutari: Decimal
    aidat_no: int | None


class SayacFaturasiOzetResponse(BaseModel):
    """Fatura liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    fatura_no: int
    site_no: int
    sayac_turu_no: int
    sayac_turu: str
    donem_yil: int
    donem_ay: int
    toplam_tutar: Decimal
    ortak_alan_tutar: Decimal
    dagitim_sekli: str
    olusturma_tarihi: datetime
    pay_sayisi: int = 0


class SayacFaturasiResponse(BaseModel):
    """Fatura detay — paylar dahil."""

    model_config = ConfigDict(from_attributes=True)

    fatura_no: int
    site_no: int
    sayac_turu_no: int
    sayac_turu: str
    donem_yil: int
    donem_ay: int
    toplam_tutar: Decimal
    ortak_alan_tutar: Decimal
    dagitim_sekli: str
    olusturma_tarihi: datetime
    paylar: list[SayacFaturaPayiResponse] = Field(default_factory=list)
    toplam_tuketim: Decimal = Decimal("0.00")
    toplam_dagitilan: Decimal = Decimal("0.00")


# ============================================================
# Özet
# ============================================================

class SayacTuketimOzet(BaseModel):
    """Sayaç türü bazlı tüketim özeti."""

    sayac_turu_no: int
    sayac_turu: str
    birim: str
    toplam_tuketim: Decimal
    okuma_sayisi: int


class SayacGenelOzet(BaseModel):
    """Site geneli sayaç özeti."""

    site_no: int
    aktif_sayac_sayisi: int
    toplam_okuma_sayisi: int
    toplam_fatura_sayisi: int
    toplam_fatura_tutar: Decimal
    tuketim_ozetleri: list[SayacTuketimOzet] = Field(default_factory=list)


# ============================================================
# İstek Şemaları
# ============================================================

class DaireSayaciCreateRequest(BaseModel):
    """Yeni daire sayacı."""

    sayac_turu_no: int = Field(..., ge=1)
    seri_no: str = Field(..., min_length=2, max_length=50)
    montaj_tarihi: date | None = None
    ilk_deger: Decimal = Field(default=Decimal("0.00"), ge=0)


class DaireSayaciUpdateRequest(BaseModel):
    """Daire sayacı güncelleme (PATCH)."""

    seri_no: str | None = Field(default=None, min_length=2, max_length=50)
    montaj_tarihi: date | None = None
    sokulme_tarihi: date | None = None
    aktif_mi: bool | None = None


class SayacOkumaCreateRequest(BaseModel):
    """Yeni okuma girişi."""

    okuma_tarihi: date
    guncel_deger: Decimal = Field(..., ge=0)


class SayacFaturasiCreateRequest(BaseModel):
    """Yeni fatura + dairelere dağıtım."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sayac_turu_no": 1,
                "donem_yil": 2026,
                "donem_ay": 10,
                "toplam_tutar": "3000.00",
                "ortak_alan_tutar": "300.00",
                "dagitim_sekli": "TUKETIME_GORE",
            }
        }
    )

    sayac_turu_no: int = Field(..., ge=1)
    donem_yil: int = Field(..., ge=2020, le=2100)
    donem_ay: int = Field(..., ge=1, le=12)
    toplam_tutar: Decimal = Field(..., gt=0)
    ortak_alan_tutar: Decimal = Field(default=Decimal("0.00"), ge=0)
    dagitim_sekli: str = Field(
        default="TUKETIME_GORE",
        pattern="^(TUKETIME_GORE|ESIT|METREKARE)$",
    )