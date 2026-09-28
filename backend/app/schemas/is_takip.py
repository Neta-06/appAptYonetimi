"""İş emri modülü Pydantic şemaları."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Lookup Şemaları
# ============================================================

class IsOncelikResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oncelik_no: int
    ad: str
    siralama: int


class IsDurumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    durum_no: int
    ad: str
    kapanis_mi: bool


# ============================================================
# Yanıt Şemaları
# ============================================================

class IsEmriOzetResponse(BaseModel):
    """İş emri liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    is_no: int
    site_no: int
    daire_no: int | None
    daire_ozet: str | None = Field(
        default=None,
        description="Ör: 'A Blok - Daire 1'",
    )
    acan_no: int
    acan_ad: str | None = None
    atanan_no: int
    atanan_ad: str | None = None
    baslik: str
    oncelik_no: int
    oncelik_ad: str
    oncelik_siralama: int
    durum_no: int
    durum_ad: str
    kapanis_mi: bool
    termin_tarihi: datetime | None
    olusturma_tarihi: datetime
    gecikti_mi: bool = Field(
        default=False,
        description="Termin geçti ve kapanmamış mı?",
    )
    malzeme_sayisi: int = 0
    guncelleme_sayisi: int = 0


class IsEmriGuncellemeResponse(BaseModel):
    """İş emri güncelleme kaydı."""

    model_config = ConfigDict(from_attributes=True)

    guncelleme_no: int
    is_no: int
    yazan_no: int
    yazan_ad: str | None = None
    durum_no: int
    durum_ad: str | None = None
    notlar: str | None
    guncelleme_tarihi: datetime


class IsEmriMalzemeResponse(BaseModel):
    """İş emri malzemesi."""

    model_config = ConfigDict(from_attributes=True)

    malzeme_no: int
    is_no: int
    ad: str
    adet: Decimal
    birim: str | None
    birim_fiyat: Decimal | None
    toplam: Decimal | None = None


class IsEmriDetayResponse(IsEmriOzetResponse):
    """İş emri detay görünümü — güncellemeler + malzemeler dahil."""

    aciklama: str | None = None
    tamamlanma_tarihi: datetime | None = None
    guncellenme_tarihi: datetime
    guncellemeler: list[IsEmriGuncellemeResponse] = Field(default_factory=list)
    malzemeler: list[IsEmriMalzemeResponse] = Field(default_factory=list)
    toplam_malzeme_tutar: Decimal = Field(
        default=Decimal("0.00"),
        description="Tüm malzemelerin toplam tutarı",
    )


# ============================================================
# Özet İstatistikler
# ============================================================

class IsEmriDurumOzet(BaseModel):
    """Durum bazlı iş emri özeti."""

    durum_no: int
    durum_ad: str
    adet: int
    yuzde: float = Field(..., description="Toplam içindeki yüzde")


class IsEmriOncelikOzet(BaseModel):
    """Öncelik bazlı iş emri özeti."""

    oncelik_no: int
    oncelik_ad: str
    adet: int
    yuzde: float


class IsEmriGenelOzet(BaseModel):
    """Site geneli iş emri özeti."""

    toplam: int
    acik: int = Field(..., description="Kapanmamış işler")
    kapali: int
    gecikmis: int = Field(..., description="Termin geçmiş açık işler")
    acil: int = Field(..., description="ACIL öncelikli açık işler")
    ortalama_tamamlama_gun: float | None = Field(
        default=None,
        description="Ortalama tamamlanma süresi (gün)",
    )
    durum_dagilimi: list[IsEmriDurumOzet] = Field(default_factory=list)
    oncelik_dagilimi: list[IsEmriOncelikOzet] = Field(default_factory=list)


# ============================================================
# İstek Şemaları
# ============================================================

class IsEmriCreateRequest(BaseModel):
    """Yeni iş emri oluşturma."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baslik": "Balkon Suyu Sızıntısı",
                "aciklama": "Daire 1 balkon drenaj kontrolü.",
                "daire_no": 1,
                "atanan_no": 3,
                "oncelik_no": 1,
                "termin_tarihi": "2026-10-05T18:00:00",
            }
        }
    )

    baslik: str = Field(..., min_length=3, max_length=150)
    aciklama: str | None = Field(default=None, max_length=5000)
    daire_no: int | None = Field(default=None, ge=1)
    atanan_no: int = Field(..., ge=1, description="İşi yapacak personel")
    oncelik_no: int = Field(..., ge=1)
    termin_tarihi: datetime | None = None


class IsEmriUpdateRequest(BaseModel):
    """İş emri güncelleme (PATCH)."""

    baslik: str | None = Field(default=None, min_length=3, max_length=150)
    aciklama: str | None = Field(default=None, max_length=5000)
    daire_no: int | None = Field(default=None, ge=1)
    atanan_no: int | None = Field(default=None, ge=1)
    oncelik_no: int | None = Field(default=None, ge=1)
    termin_tarihi: datetime | None = None


class IsEmriDurumDegistirRequest(BaseModel):
    """İş emri durum değiştirme."""

    durum_no: int = Field(..., ge=1)
    notlar: str | None = Field(default=None, max_length=500)


class IsEmriGuncellemeCreateRequest(BaseModel):
    """İş emrine not ekleme."""

    durum_no: int = Field(..., ge=1)
    notlar: str = Field(..., min_length=3, max_length=500)


class IsEmriMalzemeCreateRequest(BaseModel):
    """İş emrine malzeme ekleme."""

    ad: str = Field(..., min_length=2, max_length=150)
    adet: Decimal = Field(default=Decimal("1"), gt=0)
    birim: str | None = Field(default=None, max_length=20)
    birim_fiyat: Decimal | None = Field(default=None, ge=0)