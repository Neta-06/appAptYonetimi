"""Anket modülü Pydantic şemaları."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Yanıt Şemaları
# ============================================================

class AnketSecenekResponse(BaseModel):
    """Anket seçeneği."""

    model_config = ConfigDict(from_attributes=True)

    secenek_no: int
    secenek_metni: str


class AnketSecenekSonuc(BaseModel):
    """Seçenek + oy sayısı + yüzde."""

    secenek_no: int
    secenek_metni: str
    oy_sayisi: int
    yuzde: float


class AnketOzetResponse(BaseModel):
    """Anket liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    anket_no: int
    site_no: int
    soru: str
    baslangic_tarihi: datetime
    bitis_tarihi: datetime
    olusturan_no: int
    aktif_mi: bool
    su_an_aktif_mi: bool = Field(
        ...,
        description="Şu an oy kullanılabilir mi?",
    )
    toplam_oy: int = 0
    toplam_oy_hakki: int = 0
    oy_kullandi_mi: bool = Field(
        default=False,
        description="İstek yapan kullanıcı oy kullandı mı?",
    )
    katilim_orani: float = 0.0


class AnketDetayResponse(AnketOzetResponse):
    """Anket detay + seçenekler."""

    aciklama: str | None = None
    secenekler: list[AnketSecenekResponse] = Field(default_factory=list)


class AnketSonucResponse(BaseModel):
    """Anket sonuçları."""

    anket_no: int
    soru: str
    toplam_oy: int
    toplam_oy_hakki: int
    katilim_orani: float = Field(..., description="Yüzde olarak katılım")
    su_an_aktif_mi: bool
    secenekler: list[AnketSecenekSonuc]


class OyKullanSonuc(BaseModel):
    """Oy kullanma sonucu."""

    oy_no: int
    anket_no: int
    secenek_no: int
    secenek_metni: str
    oy_tarihi: datetime
    mesaj: str


# ============================================================
# İstek Şemaları
# ============================================================

class AnketCreateRequest(BaseModel):
    """Yeni anket oluşturma."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "soru": "Bahceye oyun parki yapalim mi?",
                "aciklama": "Tahmini maliyet aidattan karsilanacak.",
                "baslangic_tarihi": "2026-10-01T00:00:00",
                "bitis_tarihi": "2026-10-30T23:59:59",
                "secenekler": ["EVET", "HAYIR", "KARARSIZIM"],
                "oy_hakki_kullanicilar": [4, 5, 6],
            }
        }
    )

    soru: str = Field(..., min_length=5, max_length=300)
    aciklama: str | None = Field(default=None, max_length=500)
    baslangic_tarihi: datetime
    bitis_tarihi: datetime
    secenekler: list[str] = Field(..., min_length=2, max_length=10)
    oy_hakki_kullanicilar: list[int] | None = Field(
        default=None,
        description="Boş bırakılırsa tüm site sakinleri oy kullanabilir",
    )

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()

    def model_post_init(self, __context):
        """Alanlar arası doğrulama."""
        if self.bitis_tarihi <= self.baslangic_tarihi:
            raise ValueError("Bitis tarihi baslangic tarihinden sonra olmalidir.")
        if len(self.secenekler) < 2:
            raise ValueError("En az 2 secenek gerekli.")
        if len(set(self.secenekler)) != len(self.secenekler):
            raise ValueError("Secenekler benzersiz olmalidir.")


class AnketUpdateRequest(BaseModel):
    """Anket güncelleme (PATCH)."""

    soru: str | None = Field(default=None, min_length=5, max_length=300)
    aciklama: str | None = Field(default=None, max_length=500)
    baslangic_tarihi: datetime | None = None
    bitis_tarihi: datetime | None = None
    aktif_mi: bool | None = None


class OyKullanRequest(BaseModel):
    """Oy verme isteği."""

    secenek_no: int = Field(..., ge=1)