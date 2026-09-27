"""Daire yönetimi iş mantığı."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi
from app.models import (
    Blok,
    Daire,
    DaireDoluluk,
    DaireKullanim,
    DaireSakin,
    DaireSayaci,
    DaireTipi,
    Kullanici,
    SayacTuru,
    SayacBirim,
)

logger = logging.getLogger(__name__)


async def list_daireler(db: AsyncSession, site_no: int) -> list[dict]:
    """Sitedeki tüm daireleri blok + tip + doluluk bilgisiyle listeler."""
    sonuc = await db.execute(
        select(Daire, Blok, DaireTipi, DaireDoluluk, DaireKullanim)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .join(DaireTipi, DaireTipi.tip_no == Daire.daire_tipi_no)
        .join(DaireDoluluk, DaireDoluluk.doluluk_no == Daire.doluluk_no)
        .join(DaireKullanim, DaireKullanim.kullanim_no == Daire.kullanim_no)
        .where(Daire.site_no == site_no)
        .order_by(Blok.blok_adi, Daire.kat, Daire.daire_numarasi)
    )
    return [
        {
            "daire_no": d.daire_no,
            "blok_no": b.blok_no,
            "blok_adi": b.blok_adi,
            "daire_numarasi": d.daire_numarasi,
            "kat": d.kat,
            "daire_tipi": dt.ad,
            "brut_metrekare": d.brut_metrekare,
            "doluluk": dd.ad,
            "kullanim": dk.ad,
        }
        for d, b, dt, dd, dk in sonuc.all()
    ]


async def list_bloklar(db: AsyncSession, site_no: int) -> list[dict]:
    """Sitedeki blokları daire sayısıyla birlikte listeler."""
    from sqlalchemy import func
    sonuc = await db.execute(
        select(Blok, func.count(Daire.daire_no))
        .outerjoin(Daire, Daire.blok_no == Blok.blok_no)
        .where(Blok.site_no == site_no)
        .group_by(Blok.blok_no)
        .order_by(Blok.blok_adi)
    )
    return [
        {
            "blok_no": b.blok_no,
            "blok_adi": b.blok_adi,
            "kat_sayisi": b.kat_sayisi,
            "daire_sayisi": adet,
        }
        for b, adet in sonuc.all()
    ]


async def get_daire(db: AsyncSession, daire_no: int, site_no: int) -> dict:
    """
    Daire detayını döner.
    GÜVENLİK: Site kontrolü zorunlu. Farklı siteden istek → 404.
    """
    sonuc = await db.execute(
        select(Daire, Blok, DaireTipi, DaireDoluluk, DaireKullanim)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .join(DaireTipi, DaireTipi.tip_no == Daire.daire_tipi_no)
        .join(DaireDoluluk, DaireDoluluk.doluluk_no == Daire.doluluk_no)
        .join(DaireKullanim, DaireKullanim.kullanim_no == Daire.kullanim_no)
        .where(Daire.daire_no == daire_no, Daire.site_no == site_no)
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("Daire", kaynak_id=daire_no)
    d, b, dt, dd, dk = row
    return {
        "daire_no": d.daire_no,
        "site_no": d.site_no,
        "blok_no": b.blok_no,
        "blok_adi": b.blok_adi,
        "daire_numarasi": d.daire_numarasi,
        "kat": d.kat,
        "daire_tipi": dt.ad,
        "brut_metrekare": d.brut_metrekare,
        "ozel_aidat": d.ozel_aidat,
        "doluluk": dd.ad,
        "kullanim": dk.ad,
    }


async def list_sakinler(db: AsyncSession, daire_no: int, site_no: int) -> list[dict]:
    """Dairenin tüm sakinlerini (aktif + geçmiş) listeler."""
    # Site kontrolü
    await get_daire(db, daire_no, site_no)

    sonuc = await db.execute(
        select(DaireSakin, Kullanici)
        .join(Kullanici, Kullanici.kullanici_no == DaireSakin.kullanici_no)
        .where(DaireSakin.daire_no == daire_no)
        .order_by(DaireSakin.giris_tarihi.desc())
    )
    return [
        {
            "kayit_no": ds.kayit_no,
            "kullanici_no": k.kullanici_no,
            "ad": k.ad,
            "soyad": k.soyad,
            "e_posta": k.e_posta,
            "mulk_sahibi_mi": ds.mulk_sahibi_mi,
            "giris_tarihi": ds.giris_tarihi,
            "cikis_tarihi": ds.cikis_tarihi,
            "aktif_mi": ds.cikis_tarihi is None,
        }
        for ds, k in sonuc.all()
    ]


async def list_sayaclar(db: AsyncSession, daire_no: int, site_no: int) -> list[dict]:
    """Dairenin sayaçlarını listeler."""
    # Site kontrolü
    await get_daire(db, daire_no, site_no)

    sonuc = await db.execute(
        select(DaireSayaci, SayacTuru, SayacBirim)
        .join(SayacTuru, SayacTuru.sayac_turu_no == DaireSayaci.sayac_turu_no)
        .join(SayacBirim, SayacBirim.birim_no == SayacTuru.birim_no)
        .where(DaireSayaci.daire_no == daire_no)
        .order_by(SayacTuru.adi)
    )
    return [
        {
            "daire_sayac_no": ds.daire_sayac_no,
            "sayac_turu": st.adi,
            "birim": sb.ad,
            "seri_no": ds.seri_no,
            "montaj_tarihi": ds.montaj_tarihi,
            "aktif_mi": ds.aktif_mi,
        }
        for ds, st, sb in sonuc.all()
    ]