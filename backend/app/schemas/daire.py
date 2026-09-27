"""Daire modülü Pydantic şemaları."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class DaireOzetResponse(BaseModel):
    """Daire liste görünümü."""

    model_config = ConfigDict(from_attributes=True)

    daire_no: int
    blok_no: int
    blok_adi: str
    daire_numarasi: str
    kat: int
    daire_tipi: str
    brut_metrekare: Decimal | None
    doluluk: str
    kullanim: str


class DaireResponse(BaseModel):
    """Daire detay görünümü."""

    model_config = ConfigDict(from_attributes=True)

    daire_no: int
    site_no: int
    blok_no: int
    blok_adi: str
    daire_numarasi: str
    kat: int
    daire_tipi: str
    brut_metrekare: Decimal | None
    ozel_aidat: Decimal | None
    doluluk: str
    kullanim: str


class BlokResponse(BaseModel):
    """Blok bilgisi."""

    model_config = ConfigDict(from_attributes=True)

    blok_no: int
    blok_adi: str
    kat_sayisi: int
    daire_sayisi: int


class DaireSakinResponse(BaseModel):
    """Daire sakini (aktif veya geçmiş)."""

    kayit_no: int
    kullanici_no: int
    ad: str
    soyad: str
    e_posta: EmailStr
    mulk_sahibi_mi: bool
    giris_tarihi: date
    cikis_tarihi: date | None
    aktif_mi: bool


class DaireSayacResponse(BaseModel):
    """Daire sayacı."""

    daire_sayac_no: int
    sayac_turu: str
    birim: str
    seri_no: str
    montaj_tarihi: date | None
    aktif_mi: bool