"""Sakin modülü Pydantic şemaları."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# Yanıt Şemaları
# ============================================================

class SakinOzetResponse(BaseModel):
    """Sakin liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    kayit_no: int
    daire_no: int
    daire_ozet: str | None = None
    blok_adi: str | None = None
    daire_numarasi: str | None = None
    kullanici_no: int
    ad: str
    soyad: str
    e_posta: EmailStr
    telefon: str | None = None
    mulk_sahibi_mi: bool
    giris_tarihi: date
    cikis_tarihi: date | None
    aktif_mi: bool
    kullanici_site_rolu: str | None = Field(
        default=None,
        description="Site üyeliğindeki rolü (SAKIN, YONETICI vb.)",
    )


class SakinResponse(BaseModel):
    """Sakin detay görünümü."""

    model_config = ConfigDict(from_attributes=True)

    kayit_no: int
    daire_no: int
    kullanici_no: int
    mulk_sahibi_mi: bool
    giris_tarihi: date
    cikis_tarihi: date | None
    olusturma_tarihi: datetime
    guncellenme_tarihi: datetime


class SakinDetayResponse(SakinResponse):
    """Sakin + kullanıcı + daire bilgileri."""

    # Kullanıcı bilgisi
    ad: str
    soyad: str
    e_posta: EmailStr
    telefon: str | None = None

    # Daire bilgisi
    site_no: int
    site_adi: str
    blok_adi: str
    daire_numarasi: str
    kat: int
    daire_tipi: str
    brut_metrekare: float | None = None

    # Durum
    aktif_mi: bool
    diger_aktif_sakin_sayisi: int = 0


class SakinOzetStats(BaseModel):
    """Site geneli sakin istatistikleri."""

    site_no: int
    toplam_aktif: int
    toplam_malik: int
    toplam_kiraci: int
    toplam_gecmis: int = Field(..., description="Çıkış yapmış eski sakinler")
    daire_basina_ortalama_sakin: float
    en_kalabalik_daire: str | None = None
    en_kalabalik_sayi: int = 0


# ============================================================
# İstek Şemaları
# ============================================================

class SakinCreateRequest(BaseModel):
    """Yeni sakin ekleme."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "daire_no": 1,
                "kullanici_no": 4,
                "mulk_sahibi_mi": True,
                "giris_tarihi": "2026-10-01",
                "kullanici_site_rolu": "SAKIN",
                "kullanici_site_olustur": True,
            }
        }
    )

    daire_no: int = Field(..., ge=1)
    kullanici_no: int = Field(..., ge=1)
    mulk_sahibi_mi: bool = False
    giris_tarihi: date | None = None

    kullanici_site_rolu: str = Field(
        default="SAKIN",
        pattern="^(YONETICI|MUHASEBECI|SAKIN|PERSONEL|DENETCI)$",
        description="Kullanıcının bu sitedeki rolü",
    )
    kullanici_site_olustur: bool = Field(
        default=True,
        description="Kullanıcının site üyeliği yoksa otomatik oluştur",
    )


class SakinUpdateRequest(BaseModel):
    """Sakin güncelleme (PATCH)."""

    mulk_sahibi_mi: bool | None = None
    giris_tarihi: date | None = None
    cikis_tarihi: date | None = None


class SakinCikisRequest(BaseModel):
    """Sakin çıkış (taşınma)."""

    cikis_tarihi: date | None = Field(
        default=None,
        description="Boş bırakılırsa bugünün tarihi kullanılır",
    )


class SakinTasindiRequest(BaseModel):
    """Sakini başka bir daireye taşı."""

    yeni_daire_no: int = Field(..., ge=1)
    tasinma_tarihi: date | None = Field(
        default=None,
        description="Boş bırakılırsa bugünün tarihi kullanılır",
    )
    mulk_sahibi_mi: bool | None = Field(
        default=None,
        description="None ise eski değeri korunur",
    )


class SakinCikisSonuc(BaseModel):
    """Çıkış sonrası özet."""

    kayit_no: int
    cikis_tarihi: date
    daire_no: int
    daire_bos_kaldi_mi: bool = Field(
        ...,
        description="Çıkış sonrası dairede başka sakin kalmadı mı?",
    )
    mesaj: str


class SakinTasindiSonuc(BaseModel):
    """Taşınma sonrası özet."""

    eski_kayit_no: int
    yeni_kayit_no: int
    eski_daire_no: int
    yeni_daire_no: int
    tasinma_tarihi: date
    eski_daire_bos_kaldi_mi: bool
    mesaj: str