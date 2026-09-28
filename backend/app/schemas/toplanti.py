"""Toplantı modülü Pydantic şemaları."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Yanıt Şemaları
# ============================================================

class ToplantiKatilimciResponse(BaseModel):
    """Toplantı katılımcısı."""

    model_config = ConfigDict(from_attributes=True)

    katilim_no: int
    toplanti_no: int
    kullanici_no: int
    ad: str | None = None
    soyad: str | None = None
    e_posta: str | None = None
    katildi_mi: bool
    vekalet_kullanici_no: int | None = None
    vekalet_ad: str | None = None


class ToplantiKararResponse(BaseModel):
    """Toplantı kararı."""

    model_config = ConfigDict(from_attributes=True)

    karar_no: int
    toplanti_no: int
    karar_metni: str
    karar_tarihi: datetime


class ToplantiOzetResponse(BaseModel):
    """Toplantı liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    toplanti_no: int
    site_no: int
    baslik: str
    toplanti_tarihi: datetime
    yer: str | None
    olusturan_no: int
    durum: str
    katilimci_sayisi: int = 0
    katilan_sayisi: int = 0
    karar_sayisi: int = 0
    katilim_orani: float = 0.0


class ToplantiDetayResponse(ToplantiOzetResponse):
    """Toplantı detay + katılımcı + kararlar."""

    aciklama: str | None = None
    katilimcilar: list[ToplantiKatilimciResponse] = Field(default_factory=list)
    kararlar: list[ToplantiKararResponse] = Field(default_factory=list)


class ToplantiOzetStats(BaseModel):
    """Site geneli toplantı özeti."""

    site_no: int
    toplam: int
    planlanan: int
    yapilan: int
    iptal: int
    toplam_karar: int
    ortalama_katilim_orani: float


# ============================================================
# İstek Şemaları
# ============================================================

class ToplantiCreateRequest(BaseModel):
    """Yeni toplantı oluşturma."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baslik": "2026 Yili Olagan Toplantisi",
                "aciklama": "Yillik faaliyet raporu ve butce gorusulecek.",
                "toplanti_tarihi": "2026-11-15T19:00:00",
                "yer": "Site Toplanti Salonu",
                "katilimci_kullanicilar": [1, 4, 5],
            }
        }
    )

    baslik: str = Field(..., min_length=3, max_length=150)
    aciklama: str | None = Field(default=None, max_length=5000)
    toplanti_tarihi: datetime
    yer: str | None = Field(default=None, max_length=100)
    katilimci_kullanicilar: list[int] | None = Field(
        default=None,
        description="Boş bırakılırsa tüm site sakinleri eklenir",
    )


class ToplantiUpdateRequest(BaseModel):
    """Toplantı güncelleme (PATCH)."""

    baslik: str | None = Field(default=None, min_length=3, max_length=150)
    aciklama: str | None = Field(default=None, max_length=5000)
    toplanti_tarihi: datetime | None = None
    yer: str | None = Field(default=None, max_length=100)


class ToplantiDurumDegistirRequest(BaseModel):
    """Toplantı durum değiştirme."""

    durum: str = Field(
        ...,
        pattern="^(PLANLANDI|YAPILDI|IPTAL)$",
    )


class KatilimciEkleRequest(BaseModel):
    """Toplantıya katılımcı ekleme."""

    kullanici_no: int = Field(..., ge=1)
    vekalet_kullanici_no: int | None = Field(default=None, ge=1)


class KatilimciGuncelleRequest(BaseModel):
    """Katılımcı durumunu güncelleme."""

    katildi_mi: bool | None = None
    vekalet_kullanici_no: int | None = None


class KararEkleRequest(BaseModel):
    """Toplantı kararı ekleme."""

    karar_metni: str = Field(..., min_length=5, max_length=5000)