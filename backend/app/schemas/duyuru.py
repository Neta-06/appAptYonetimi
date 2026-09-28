"""Duyuru modülü Pydantic şemaları."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Yanıt Şemaları
# ============================================================

class DuyuruOzetResponse(BaseModel):
    """Duyuru liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    duyuru_no: int
    baslik: str
    onem_derecesi: str
    yayin_tarihi: datetime
    bitis_tarihi: date | None
    yayinlayan_no: int
    okundu_mu: bool = Field(
        default=False,
        description="İstek yapan kullanıcı okudu mu?",
    )
    aktif_mi: bool = Field(
        default=True,
        description="Bitiş tarihi geçmemiş mi?",
    )


class DuyuruResponse(BaseModel):
    """Duyuru detay görünümü."""

    model_config = ConfigDict(from_attributes=True)

    duyuru_no: int
    site_no: int
    baslik: str
    icerik: str
    onem_derecesi: str
    yayin_tarihi: datetime
    bitis_tarihi: date | None
    yayinlayan_no: int


class DuyuruDetayResponse(DuyuruResponse):
    """Duyuru detay + okuma bilgisi."""

    okundu_mu: bool = False
    okuma_tarihi: datetime | None = None
    toplam_okuma: int = 0


# ============================================================
# Okuma Şemaları
# ============================================================

class DuyuruOkumaResponse(BaseModel):
    """Okuma kaydı — kim okudu bilgisi."""

    model_config = ConfigDict(from_attributes=True)

    okuma_no: int
    kullanici_no: int
    ad: str | None = None
    soyad: str | None = None
    e_posta: str | None = None
    okuma_tarihi: datetime


class DuyuruOkumaDurumResponse(BaseModel):
    """Duyuru okuma durumu (yönetici görünümü)."""

    duyuru_no: int
    baslik: str
    toplam_alici: int = Field(..., description="Toplam hedef kullanıcı")
    okuyan_sayisi: int
    okumayan_sayisi: int
    okuma_orani: float = Field(..., description="Yüzde")
    okumalar: list[DuyuruOkumaResponse] = Field(default_factory=list)


# ============================================================
# İstek Şemaları
# ============================================================

class DuyuruCreateRequest(BaseModel):
    """Yeni duyuru oluşturma."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baslik": "Su Kesintisi",
                "icerik": "25 Ekim 09:00-15:00 arası ana hat bakımı nedeniyle su kesintisi olacaktır.",
                "onem_derecesi": "ACIL",
                "bitis_tarihi": "2026-10-25",
            }
        }
    )

    baslik: str = Field(..., min_length=3, max_length=150)
    icerik: str = Field(..., min_length=10, max_length=5000)
    onem_derecesi: str = Field(
        default="NORMAL",
        pattern="^(NORMAL|ONEMLI|ACIL)$",
        description="NORMAL, ONEMLI veya ACIL",
    )
    bitis_tarihi: date | None = None


class DuyuruUpdateRequest(BaseModel):
    """Duyuru güncelleme (PATCH — tüm alanlar opsiyonel)."""

    baslik: str | None = Field(default=None, min_length=3, max_length=150)
    icerik: str | None = Field(default=None, min_length=10, max_length=5000)
    onem_derecesi: str | None = Field(
        default=None,
        pattern="^(NORMAL|ONEMLI|ACIL)$",
    )
    bitis_tarihi: date | None = None