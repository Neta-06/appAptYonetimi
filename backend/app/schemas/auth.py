"""
Kimlik doğrulama Pydantic şemaları.

Şemalar:
  - KullaniciRegisterRequest  : POST /auth/register gövdesi
  - KullaniciLoginRequest     : POST /auth/login gövdesi
  - TokenResponse             : Başarılı login/refresh yanıtı
  - TokenRefreshRequest       : POST /auth/refresh gövdesi
  - KullaniciResponse         : Kullanıcı bilgisi (parolasız)
  - KullaniciSiteResponse     : Kullanıcının site üyeliği
"""

import re
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

# ------------------------------------------------------------
# Ortak tipler ve doğrulamalar
# ------------------------------------------------------------

# Parola: en az 8 karakter, en az 1 büyük, 1 küçük, 1 rakam, 1 özel karakter
PAROLA_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>_\-\+=\[\]\\/;`~]).+$"
)


def _parola_dogrula(v: str) -> str:
    """Parola karmaşıklık kurallarını doğrular."""
    if len(v) < 8:
        raise ValueError("Parola en az 8 karakter olmalidir.")
    if len(v) > 128:
        raise ValueError("Parola en fazla 128 karakter olabilir.")
    if not PAROLA_REGEX.match(v):
        raise ValueError(
            "Parola en az bir kucuk harf, bir buyuk harf, bir rakam "
            "ve bir ozel karakter icermelidir."
        )
    return v


# ------------------------------------------------------------
# Kayıt (Register)
# ------------------------------------------------------------

class KullaniciRegisterRequest(BaseModel):
    """POST /auth/register gövdesi."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ad": "Ali",
                "soyad": "Yilmaz",
                "e_posta": "ali.yilmaz@mail.com",
                "telefon": "05011112233",
                "parola": "Guclu!Parola1",
                "parola_tekrar": "Guclu!Parola1",
                "kvkk_onay": True,
            }
        }
    )

    ad: Annotated[str, Field(min_length=2, max_length=50)]
    soyad: Annotated[str, Field(min_length=2, max_length=50)]
    e_posta: EmailStr
    telefon: Annotated[str | None, Field(default=None, max_length=15)] = None
    parola: Annotated[str, Field(min_length=8, max_length=128)]
    parola_tekrar: Annotated[str, Field(min_length=8, max_length=128)]
    kvkk_onay: bool = Field(
        ..., description="KVKK aydinlatma metnini okudum ve onayliyorum."
    )

    @field_validator("ad", "soyad")
    @classmethod
    def ad_soyad_temizle(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Ad ve soyad bos olamaz.")
        return v

    @field_validator("telefon")
    @classmethod
    def telefon_temizle(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # Sadece rakam ve + kalsın
        temiz = re.sub(r"[^\d+]", "", v)
        if not (10 <= len(temiz) <= 15):
            raise ValueError("Telefon 10-15 karakter arasinda olmalidir.")
        return temiz

    @field_validator("parola")
    @classmethod
    def parola_kontrol(cls, v: str) -> str:
        return _parola_dogrula(v)

    @field_validator("kvkk_onay")
    @classmethod
    def kvkk_zorunlu(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "KVKK aydinlatma metnini onaylamadan kayit olamazsiniz."
            )
        return v

    @model_validator(mode="after")
    def parola_eslesme(self) -> "KullaniciRegisterRequest":
        if self.parola != self.parola_tekrar:
            raise ValueError("Parolalar eslesmiyor.")
        return self


# ------------------------------------------------------------
# Giriş (Login)
# ------------------------------------------------------------

class KullaniciLoginRequest(BaseModel):
    """POST /auth/login gövdesi."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "e_posta": "ali.yilmaz@mail.com",
                "parola": "Guclu!Parola1",
                "mfa_kodu": "123456",
            }
        }
    )

    e_posta: EmailStr
    parola: Annotated[str, Field(min_length=1, max_length=128)]
    mfa_kodu: Annotated[str | None, Field(default=None, max_length=10)] = None


# ------------------------------------------------------------
# Token Yanıtı
# ------------------------------------------------------------

class TokenResponse(BaseModel):
    """Başarılı login/refresh yanıtı."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOi...",
                "refresh_token": "eyJhbGciOi...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    )

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        ..., description="Access token gecerlilik suresi (saniye)."
    )


class TokenRefreshRequest(BaseModel):
    """POST /auth/refresh gövdesi."""

    refresh_token: Annotated[str, Field(min_length=20)]


# ------------------------------------------------------------
# Kullanıcı Bilgisi (Yanıt)
# ------------------------------------------------------------

class KullaniciSiteResponse(BaseModel):
    """Kullanıcının bir sitedeki üyeliği."""

    model_config = ConfigDict(from_attributes=True)

    site_no: int
    site_adi: str
    rol_no: int
    rol_adi: str
    aktif_mi: bool


class KullaniciResponse(BaseModel):
    """GET /auth/me yanıtı — kullanıcı bilgisi (parolasız)."""

    model_config = ConfigDict(from_attributes=True)

    kullanici_no: int
    firma_no: int | None
    ad: str
    soyad: str
    e_posta: EmailStr
    mfa_aktif_mi: bool
    son_giris_tarihi: datetime | None
    aktif_mi: bool
    olusturma_tarihi: datetime


# ------------------------------------------------------------
# Şifre Değiştirme / Sıfırlama
# ------------------------------------------------------------

class SifreDegistirRequest(BaseModel):
    """POST /auth/sifre-degistir gövdesi."""

    eski_parola: Annotated[str, Field(min_length=1, max_length=128)]
    yeni_parola: Annotated[str, Field(min_length=8, max_length=128)]
    yeni_parola_tekrar: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("yeni_parola")
    @classmethod
    def yeni_parola_kontrol(cls, v: str) -> str:
        return _parola_dogrula(v)

    @model_validator(mode="after")
    def eslesme(self) -> "SifreDegistirRequest":
        if self.yeni_parola != self.yeni_parola_tekrar:
            raise ValueError("Yeni parolalar eslesmiyor.")
        return self


class SifreSifirlaTalebiRequest(BaseModel):
    """POST /auth/sifre-sifirla-talebi gövdesi."""

    e_posta: EmailStr


class SifreSifirlaRequest(BaseModel):
    """POST /auth/sifre-sifirla gövdesi."""

    token: Annotated[str, Field(min_length=20)]
    yeni_parola: Annotated[str, Field(min_length=8, max_length=128)]
    yeni_parola_tekrar: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("yeni_parola")
    @classmethod
    def yeni_parola_kontrol(cls, v: str) -> str:
        return _parola_dogrula(v)

    @model_validator(mode="after")
    def eslesme(self) -> "SifreSifirlaRequest":
        if self.yeni_parola != self.yeni_parola_tekrar:
            raise ValueError("Parolalar eslesmiyor.")
        return self


# ------------------------------------------------------------
# Mesaj Yanıtı (basit success)
# ------------------------------------------------------------

class MesajResponse(BaseModel):
    """Basit bilgi mesajı yanıtı."""

    mesaj: str


# ------------------------------------------------------------
# Çıkış (Logout)
# ------------------------------------------------------------

class LogoutRequest(BaseModel):
    """POST /auth/logout gövdesi (opsiyonel — cookie de kabul edilir)."""

    refresh_token: Annotated[str | None, Field(default=None, min_length=20)] = None
