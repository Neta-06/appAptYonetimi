"""Personel modülü Pydantic şemaları."""

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# Yanıt Şemaları
# ============================================================

class PersonelSiteResponse(BaseModel):
    """Personelin site ataması."""

    model_config = ConfigDict(from_attributes=True)

    kayit_no: int
    personel_no: int
    site_no: int
    site_adi: str | None = None
    baslangic_tarihi: date
    bitis_tarihi: date | None


class PersonelIzinResponse(BaseModel):
    """İzin kaydı."""

    model_config = ConfigDict(from_attributes=True)

    izin_no: int
    personel_no: int
    izin_tipi: str
    baslangic_tarihi: date
    bitis_tarihi: date
    gun_sayisi: int
    aciklama: str | None
    onaylayan_no: int | None
    onaylayan_ad: str | None = None
    onay_durum_no: int
    onay_durum_ad: str | None = None
    olusturma_tarihi: datetime


class PersonelPuantajResponse(BaseModel):
    """Puantaj kaydı."""

    model_config = ConfigDict(from_attributes=True)

    puantaj_no: int
    personel_no: int
    tarih: date
    giris_saati: time | None
    cikis_saati: time | None
    toplam_saat: Decimal | None
    devamsiz_mi: bool
    aciklama: str | None


class PersonelMaasOdemeResponse(BaseModel):
    """Maaş ödemesi."""

    model_config = ConfigDict(from_attributes=True)

    maas_odeme_no: int
    personel_no: int
    donem_yil: int
    donem_ay: int
    brut_maas: Decimal
    kesintiler: Decimal
    net_maas: Decimal | None
    odeme_tarihi: date | None


class PersonelOzetResponse(BaseModel):
    """Personel liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    personel_no: int
    firma_no: int
    kullanici_no: int | None
    ad: str
    soyad: str
    gorevi: str
    telefon: str | None
    e_posta: EmailStr | None
    ise_baslama_tarihi: date
    isten_cikis_tarihi: date | None
    aktif_mi: bool
    site_sayisi: int = 0
    aktif_izin_mi: bool = False
    son_izin_tarihi: date | None = None


class PersonelResponse(BaseModel):
    """Personel detayı (ilişkiler olmadan)."""

    model_config = ConfigDict(from_attributes=True)

    personel_no: int
    firma_no: int
    kullanici_no: int | None
    ad: str
    soyad: str
    gorevi: str
    telefon: str | None
    e_posta: EmailStr | None
    ise_baslama_tarihi: date
    isten_cikis_tarihi: date | None
    aktif_mi: bool


class PersonelDetayResponse(PersonelResponse):
    """Personel detayı + ilişkiler."""

    siteler: list[PersonelSiteResponse] = Field(default_factory=list)
    izinler: list[PersonelIzinResponse] = Field(default_factory=list)
    toplam_izin_gun: int = 0
    son_maas_net: Decimal | None = None


# ============================================================
# Özet İstatistikler
# ============================================================

class GorevDagilim(BaseModel):
    """Görev bazlı dağılım."""

    gorevi: str
    sayi: int
    yuzde: float


class PersonelOzetStats(BaseModel):
    """Firma/site geneli personel özeti."""

    firma_no: int | None = None
    toplam_personel: int
    aktif_personel: int
    pasif_personel: int
    aktif_izinli: int = Field(..., description="Şu an izinde olan")
    gorev_dagilimi: list[GorevDagilim] = Field(default_factory=list)
    toplam_yillik_izin_gun: int = 0
    ortalama_hizmet_yili: float = 0.0


# ============================================================
# İstek Şemaları — Personel
# ============================================================

class PersonelCreateRequest(BaseModel):
    """Yeni personel kaydı."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ad": "Mehmet",
                "soyad": "Demir",
                "gorevi": "TEKNIK PERSONEL",
                "telefon": "05011110003",
                "e_posta": "mehmet@ornek.com",
                "kullanici_no": 3,
                "ise_baslama_tarihi": "2025-01-01",
                "site_nolar": [1, 2],
            }
        }
    )

    ad: str = Field(..., min_length=2, max_length=50)
    soyad: str = Field(..., min_length=2, max_length=50)
    gorevi: str = Field(..., min_length=2, max_length=50)
    telefon: str | None = Field(default=None, max_length=15)
    e_posta: EmailStr | None = None
    kullanici_no: int | None = Field(default=None, ge=1)
    tc_kimlik: str | None = Field(
        default=None,
        min_length=11,
        max_length=11,
        description="Uygulama katmaninda AES ile sifrelenecek",
    )
    ise_baslama_tarihi: date
    site_nolar: list[int] | None = Field(
        default=None,
        description="Personelin atanacagi site numaralari",
    )


class PersonelUpdateRequest(BaseModel):
    """Personel güncelleme (PATCH)."""

    ad: str | None = Field(default=None, min_length=2, max_length=50)
    soyad: str | None = Field(default=None, min_length=2, max_length=50)
    gorevi: str | None = Field(default=None, min_length=2, max_length=50)
    telefon: str | None = Field(default=None, max_length=15)
    e_posta: EmailStr | None = None
    kullanici_no: int | None = Field(default=None, ge=1)
    ise_baslama_tarihi: date | None = None
    isten_cikis_tarihi: date | None = None
    aktif_mi: bool | None = None


class PersonelCikisRequest(BaseModel):
    """Personel işten çıkış."""

    isten_cikis_tarihi: date | None = Field(
        default=None,
        description="Boş bırakılırsa bugünün tarihi",
    )
    aciklama: str | None = Field(default=None, max_length=255)


# ============================================================
# İstek Şemaları — Site Atama
# ============================================================

class PersonelSiteEkleRequest(BaseModel):
    """Personele site atama."""

    site_no: int = Field(..., ge=1)
    baslangic_tarihi: date | None = None
    bitis_tarihi: date | None = None


# ============================================================
# İstek Şemaları — İzin
# ============================================================

class PersonelIzinCreateRequest(BaseModel):
    """Yeni izin talebi."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "izin_tipi": "YILLIK",
                "baslangic_tarihi": "2026-10-01",
                "bitis_tarihi": "2026-10-05",
                "aciklama": "Yillik izin",
            }
        }
    )

    izin_tipi: str = Field(
        ...,
        pattern="^(YILLIK|RAPOR|MAZERET|UCRETSIZ|DOGUM|EVLILIK)$",
    )
    baslangic_tarihi: date
    bitis_tarihi: date
    aciklama: str | None = Field(default=None, max_length=255)


class PersonelIzinOnayRequest(BaseModel):
    """İzin onaylama / reddetme."""

    onay_durum_no: int = Field(
        ...,
        ge=1,
        le=3,
        description="1=Onaylandi, 2=Bekliyor, 3=Reddedildi",
    )
    aciklama: str | None = Field(default=None, max_length=255)


# ============================================================
# İstek Şemaları — Puantaj
# ============================================================

class PersonelPuantajCreateRequest(BaseModel):
    """Puantaj kaydı (giriş-çıkış)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tarih": "2026-10-01",
                "giris_saati": "08:00:00",
                "cikis_saati": "17:00:00",
                "aciklama": "Normal mesai",
            }
        }
    )

    tarih: date
    giris_saati: time | None = None
    cikis_saati: time | None = None
    devamsiz_mi: bool = False
    aciklama: str | None = Field(default=None, max_length=255)


class PersonelPuantajAylikOzet(BaseModel):
    """Aylık puantaj özeti."""

    personel_no: int
    ad: str
    soyad: str
    donem_yil: int
    donem_ay: int
    toplam_gun: int
    calisilan_gun: int
    devamsiz_gun: int
    toplam_saat: Decimal


# ============================================================
# İstek Şemaları — Maaş
# ============================================================

class PersonelMaasCreateRequest(BaseModel):
    """Maaş ödemesi kaydı."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "donem_yil": 2026,
                "donem_ay": 10,
                "brut_maas": "30000.00",
                "kesintiler": "4500.00",
                "odeme_tarihi": "2026-10-31",
            }
        }
    )

    donem_yil: int = Field(..., ge=2020, le=2100)
    donem_ay: int = Field(..., ge=1, le=12)
    brut_maas: Decimal = Field(..., gt=0)
    kesintiler: Decimal = Field(default=Decimal("0.00"), ge=0)
    odeme_tarihi: date | None = None


class PersonelMaasUpdateRequest(BaseModel):
    """Maaş ödemesi güncelleme (PATCH)."""

    brut_maas: Decimal | None = Field(default=None, gt=0)
    kesintiler: Decimal | None = Field(default=None, ge=0)
    odeme_tarihi: date | None = None