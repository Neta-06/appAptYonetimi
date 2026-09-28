"""Rapor modülü Pydantic şemaları."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


# ============================================================
# Dashboard
# ============================================================
class DaireOzet(BaseModel):
    """Daire sayıları özeti."""

    toplam: int
    dolu: int
    bos: int
    doluluk_orani: float = Field(..., description="Yüzde")


class SakinOzet(BaseModel):
    """Sakin sayıları özeti."""

    toplam_aktif: int
    malik: int
    kiraci: int


class AidatOzetDashboard(BaseModel):
    """Bu ayın aidat özeti."""

    donem_yil: int
    donem_ay: int
    tahakkuk: Decimal
    tahsilat: Decimal
    kalan: Decimal
    tahsilat_orani: float
    odenmis: int
    bekleyen: int
    gecikmis: int


class FinansalOzetDashboard(BaseModel):
    """Bu ayın gider/gelir özeti."""

    donem_yil: int
    donem_ay: int
    toplam_gider: Decimal
    toplam_gelir: Decimal
    net_durum: Decimal
    kar_zarar: str


class DashboardResponse(BaseModel):
    """Ana dashboard panel."""

    site_no: int
    site_adi: str
    daire: DaireOzet
    sakin: SakinOzet
    aidat: AidatOzetDashboard
    finansal: FinansalOzetDashboard


# ============================================================
# Finansal Özet
# ============================================================
class AylikFinansal(BaseModel):
    """Tek aylık finansal özet."""

    donem_yil: int
    donem_ay: int
    toplam_gelir: Decimal
    toplam_gider: Decimal
    net: Decimal
    kar_zarar: str


class FinansalOzetResponse(BaseModel):
    """Belirli bir dönem için finansal özet."""

    site_no: int
    site_adi: str
    donem_yil: int
    donem_ay: int
    toplam_gelir: Decimal
    toplam_gider: Decimal
    net: Decimal
    kar_zarar: str
    gelir_kaynaklari: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Gelir kaynağı -> tutar",
    )
    gider_kategorileri: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Gider kategorisi -> tutar",
    )


# ============================================================
# Aidat Durumu
# ============================================================
class AidatDurumResponse(BaseModel):
    """Aidat durum özeti."""

    site_no: int
    site_adi: str
    toplam_tahakkuk: Decimal
    toplam_tahsilat: Decimal
    toplam_kalan: Decimal
    tahsilat_orani: float
    odenmis_sayisi: int
    bekleyen_sayisi: int
    gecikmis_sayisi: int
    kismi_odenmis_sayisi: int
    daire_bazli_ortalama_borc: Decimal


# ============================================================
# Gider Dağılımı
# ============================================================
class GiderDagilimResponse(BaseModel):
    """Kategori bazlı gider dağılımı."""

    site_no: int
    toplam_gider: Decimal
    kategoriler: list[dict]  # [{kategori_no, kategori_adi, toplam, yuzde, kayit_sayisi}]
    aylik_trend: list[dict] = Field(default_factory=list)


# ============================================================
# Daire Doluluk
# ============================================================
class BlokDoluluk(BaseModel):
    """Blok bazlı doluluk."""

    blok_no: int
    blok_adi: str
    toplam: int
    dolu: int
    bos: int
    doluluk_orani: float


class DaireDolulukResponse(BaseModel):
    """Site daire doluluk özeti."""

    site_no: int
    site_adi: str
    toplam_daire: int
    dolu: int
    bos: int
    kiralik: int
    doluluk_orani: float
    bloklar: list[BlokDoluluk]


# ============================================================
# Borçlu Daireler
# ============================================================
class BorcluDaire(BaseModel):
    """Borçlu daire satırı."""

    daire_no: int
    blok_adi: str
    daire_numarasi: str
    toplam_borc: Decimal
    gecikmis_borc: Decimal
    gecikmis_aidat_sayisi: int


class BorcluDairelerResponse(BaseModel):
    """En çok borçlu daireler."""

    site_no: int
    toplam_borclu_daire: int
    toplam_borc: Decimal
    daireler: list[BorcluDaire]


# ============================================================
# Trend
# ============================================================
class AylikTrend(BaseModel):
    """Tek ay trend verisi."""

    donem_yil: int
    donem_ay: int
    gelir: Decimal
    gider: Decimal
    net: Decimal


class TrendResponse(BaseModel):
    """Son N ay trend."""

    site_no: int
    ay_sayisi: int
    trend: list[AylikTrend]
    toplam_gelir: Decimal
    toplam_gider: Decimal
    ortalama_aylik_gelir: Decimal
    ortalama_aylik_gider: Decimal