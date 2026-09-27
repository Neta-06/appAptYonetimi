"""Gider ve gelir iş mantığı."""

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import case, delete as sa_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.utils import now_utc_naive
from app.models import (
    CariHareket,
    CariHesap,
    CariIslemTipi,
    Gelir,
    Gider,
    GiderKalemi,
    GiderKategori,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI: Cari hareket yaz
# ============================================================
async def _cari_hareket_ekle(
    db: AsyncSession,
    *,
    cari_no: int,
    gider_no: int | None,
    tutar: Decimal,
    aciklama: str,
    belge_no: str | None,
    olusturan_no: int,
    islem_tipi: str = "BORC",
) -> None:
    """Gider kaydı için cari hareket oluşturur (BORÇ)."""
    # İşlem tipini bul
    tip_sonuc = await db.execute(
        select(CariIslemTipi).where(CariIslemTipi.ad == islem_tipi)
    )
    tip = tip_sonuc.scalar_one_or_none()
    if tip is None:
        return  # lookup yoksa sessizce atla

    hareket = CariHareket(
        cari_no=cari_no,
        hareket_tarihi=date.today(),
        islem_tipi_no=tip.tip_no,
        tutar=tutar,
        aciklama=aciklama[:255] if aciklama else None,
        belge_no=belge_no,
        gider_no=gider_no,
        olusturan_no=olusturan_no,
    )
    db.add(hareket)


# ============================================================
# LİSTELEME
# ============================================================
async def list_giderler(
    db: AsyncSession,
    site_no: int,
    *,
    kategori_no: int | None = None,
    kalem_no: int | None = None,
    cari_no: int | None = None,
    tarih_baslangic: date | None = None,
    tarih_bitis: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Site giderlerini filtreli listeler."""
    stmt = (
        select(Gider, GiderKalemi, GiderKategori, CariHesap)
        .join(GiderKalemi, GiderKalemi.kalem_no == Gider.kalem_no)
        .join(GiderKategori, GiderKategori.kategori_no == GiderKalemi.kategori_no)
        .outerjoin(CariHesap, CariHesap.cari_no == Gider.cari_no)
        .where(Gider.site_no == site_no)
    )

    if kategori_no is not None:
        stmt = stmt.where(GiderKalemi.kategori_no == kategori_no)
    if kalem_no is not None:
        stmt = stmt.where(Gider.kalem_no == kalem_no)
    if cari_no is not None:
        stmt = stmt.where(Gider.cari_no == cari_no)
    if tarih_baslangic is not None:
        stmt = stmt.where(Gider.gider_tarihi >= tarih_baslangic)
    if tarih_bitis is not None:
        stmt = stmt.where(Gider.gider_tarihi <= tarih_bitis)

    stmt = stmt.order_by(Gider.gider_tarihi.desc(), Gider.gider_no.desc())
    stmt = stmt.limit(limit).offset(offset)

    sonuc = await db.execute(stmt)
    kayitlar = []
    for g, kalem, kategori, cari in sonuc.all():
        kayitlar.append({
            "gider_no": g.gider_no,
            "gider_tarihi": g.gider_tarihi,
            "kalem_no": kalem.kalem_no,
            "kalem_adi": kalem.kalem_adi,
            "kategori_no": kategori.kategori_no,
            "kategori_adi": kategori.ad,
            "cari_no": cari.cari_no if cari else None,
            "cari_unvan": cari.unvan if cari else None,
            "tutar": g.tutar,
            "kdv_tutar": g.kdv_tutar,
            "toplam_tutar": g.tutar + g.kdv_tutar,
            "belge_no": g.belge_no,
            "aciklama": g.aciklama,
        })
    return kayitlar


async def get_gider(db: AsyncSession, gider_no: int, site_no: int) -> Gider:
    """Tek gider detayı (site kontrolü)."""
    sonuc = await db.execute(
        select(Gider).where(Gider.gider_no == gider_no, Gider.site_no == site_no)
    )
    gider = sonuc.scalar_one_or_none()
    if gider is None:
        raise BulunamadiHatasi("Gider", kaynak_id=gider_no)
    return gider


# ============================================================
# OLUŞTURMA
# ============================================================
async def create_gider(
    db: AsyncSession,
    site_no: int,
    *,
    kalem_no: int,
    tutar: Decimal,
    gider_tarihi: date,
    kaydeden_no: int,
    cari_no: int | None = None,
    kdv_tutar: Decimal = Decimal("0.00"),
    belge_no: str | None = None,
    aciklama: str | None = None,
) -> Gider:
    """
    Yeni gider kaydı oluşturur.

    Adımlar:
      1. Kalem ve cari kontrolü
      2. Gideri oluştur (flush → gider_no)
      3. Cari seçiliyse otomatik cari hareket (BORÇ)
      4. Commit
    """
    # 1) Kalem kontrolü
    kalem = await db.get(GiderKalemi, kalem_no)
    if kalem is None:
        raise BulunamadiHatasi("GiderKalemi", kaynak_id=kalem_no)

    # 2) Cari kontrolü (varsa)
    if cari_no is not None:
        cari = await db.get(CariHesap, cari_no)
        if cari is None:
            raise BulunamadiHatasi("CariHesap", kaynak_id=cari_no)
        if cari.site_no != site_no:
            # Cross-tenant
            raise BulunamadiHatasi("CariHesap", kaynak_id=cari_no)

    # 3) Gider kaydı
    gider = Gider(
        site_no=site_no,
        kalem_no=kalem_no,
        cari_no=cari_no,
        tutar=tutar,
        kdv_tutar=kdv_tutar,
        gider_tarihi=gider_tarihi,
        belge_no=belge_no,
        aciklama=aciklama,
        kaydeden_no=kaydeden_no,
    )
    db.add(gider)
    await db.flush()  # gider_no üretilsin

    # 4) Cari hareket
    if cari_no is not None:
        await _cari_hareket_ekle(
            db,
            cari_no=cari_no,
            gider_no=gider.gider_no,
            tutar=tutar + kdv_tutar,
            aciklama=f"Gider: {kalem.kalem_adi}",
            belge_no=belge_no,
            olusturan_no=kaydeden_no,
            islem_tipi="BORC",
        )

    await db.commit()
    await db.refresh(gider)

    logger.info(
        "Yeni gider: no=%s site=%s tutar=%s",
        gider.gider_no, site_no, tutar,
    )
    return gider


# ============================================================
# GÜNCELLEME
# ============================================================
async def update_gider(
    db: AsyncSession,
    gider_no: int,
    site_no: int,
    *,
    kalem_no: int | None = None,
    cari_no: int | None = None,
    tutar: Decimal | None = None,
    kdv_tutar: Decimal | None = None,
    gider_tarihi: date | None = None,
    belge_no: str | None = None,
    aciklama: str | None = None,
) -> Gider:
    """Gider kaydını günceller (PATCH)."""
    gider = await get_gider(db, gider_no, site_no)

    if kalem_no is not None:
        kalem = await db.get(GiderKalemi, kalem_no)
        if kalem is None:
            raise BulunamadiHatasi("GiderKalemi", kaynak_id=kalem_no)
        gider.kalem_no = kalem_no

    if cari_no is not None:
        if cari_no != 0:  # 0 gönderilirse cari temizlenir
            cari = await db.get(CariHesap, cari_no)
            if cari is None or cari.site_no != site_no:
                raise BulunamadiHatasi("CariHesap", kaynak_id=cari_no)
            gider.cari_no = cari_no
        else:
            gider.cari_no = None

    if tutar is not None:
        gider.tutar = tutar
    if kdv_tutar is not None:
        gider.kdv_tutar = kdv_tutar
    if gider_tarihi is not None:
        gider.gider_tarihi = gider_tarihi
    if belge_no is not None:
        gider.belge_no = belge_no
    if aciklama is not None:
        gider.aciklama = aciklama

    await db.commit()
    await db.refresh(gider)
    logger.info("Gider guncellendi: no=%s", gider_no)
    return gider


# ============================================================
# SİLME
# ============================================================
async def delete_gider(db: AsyncSession, gider_no: int, site_no: int) -> None:
    """Gider kaydını siler (ilişkili cari hareket varsa bağlantı keser)."""
    gider = await get_gider(db, gider_no, site_no)

    # Bağlı cari hareketleri sil
    await db.execute(
        sa_delete(CariHareket).where(CariHareket.gider_no == gider_no)
    )

    await db.delete(gider)
    await db.commit()
    logger.info("Gider silindi: no=%s", gider_no)


# ============================================================
# ÖZET İSTATİSTİKLER
# ============================================================
async def get_genel_ozet(
    db: AsyncSession,
    site_no: int,
    *,
    tarih_baslangic: date | None = None,
    tarih_bitis: date | None = None,
) -> dict:
    """Site geneli gider özeti."""
    stmt = select(
        func.count(Gider.gider_no).label("kayit_sayisi"),
        func.coalesce(func.sum(Gider.tutar), 0).label("toplam_tutar"),
        func.coalesce(func.sum(Gider.kdv_tutar), 0).label("toplam_kdv"),
        func.coalesce(func.avg(Gider.tutar), 0).label("ortalama"),
        func.coalesce(func.max(Gider.tutar), 0).label("en_yuksek"),
        func.coalesce(func.min(Gider.tutar), 0).label("en_dusuk"),
    ).where(Gider.site_no == site_no)

    if tarih_baslangic is not None:
        stmt = stmt.where(Gider.gider_tarihi >= tarih_baslangic)
    if tarih_bitis is not None:
        stmt = stmt.where(Gider.gider_tarihi <= tarih_bitis)

    row = (await db.execute(stmt)).first()

    toplam = Decimal(str(row.toplam_tutar or 0))
    kdv = Decimal(str(row.toplam_kdv or 0))

    return {
        "toplam_gider": toplam,
        "toplam_kdv": kdv,
        "toplam_genel": toplam + kdv,
        "kayit_sayisi": int(row.kayit_sayisi or 0),
        "ortalama_gider": Decimal(str(row.ortalama or 0)).quantize(Decimal("0.01")),
        "en_yuksek_gider": Decimal(str(row.en_yuksek or 0)),
        "en_dusuk_gider": Decimal(str(row.en_dusuk or 0)),
    }


async def get_kategori_ozet(
    db: AsyncSession,
    site_no: int,
    *,
    tarih_baslangic: date | None = None,
    tarih_bitis: date | None = None,
) -> list[dict]:
    """Kategori bazlı gider özeti."""
    stmt = (
        select(
            GiderKategori.kategori_no,
            GiderKategori.ad,
            func.coalesce(func.sum(Gider.tutar), 0).label("toplam"),
            func.count(Gider.gider_no).label("sayi"),
        )
        .join(GiderKalemi, GiderKalemi.kategori_no == GiderKategori.kategori_no)
        .join(Gider, Gider.kalem_no == GiderKalemi.kalem_no)
        .where(Gider.site_no == site_no)
        .group_by(GiderKategori.kategori_no)
        .order_by(func.sum(Gider.tutar).desc())
    )

    if tarih_baslangic is not None:
        stmt = stmt.where(Gider.gider_tarihi >= tarih_baslangic)
    if tarih_bitis is not None:
        stmt = stmt.where(Gider.gider_tarihi <= tarih_bitis)

    rows = list((await db.execute(stmt)).all())
    genel_toplam = sum((Decimal(str(r.toplam or 0)) for r in rows), Decimal("0.00"))

    sonuclar = []
    for r in rows:
        tutar = Decimal(str(r.toplam or 0))
        yuzde = float(tutar / genel_toplam * 100) if genel_toplam > 0 else 0.0
        sonuclar.append({
            "kategori_no": r.kategori_no,
            "kategori_adi": r.ad,
            "toplam_tutar": tutar,
            "kayit_sayisi": int(r.sayi or 0),
            "yuzde": round(yuzde, 2),
        })
    return sonuclar


async def get_aylik_ozet(
    db: AsyncSession,
    site_no: int,
    *,
    yil: int | None = None,
) -> list[dict]:
    """Aylık gider trendi (yıl bazlı)."""
    stmt = (
        select(
            func.year(Gider.gider_tarihi).label("yil"),
            func.month(Gider.gider_tarihi).label("ay"),
            func.coalesce(func.sum(Gider.tutar), 0).label("toplam"),
            func.count(Gider.gider_no).label("sayi"),
        )
        .where(Gider.site_no == site_no)
        .group_by(func.year(Gider.gider_tarihi), func.month(Gider.gider_tarihi))
        .order_by(
            func.year(Gider.gider_tarihi).desc(),
            func.month(Gider.gider_tarihi).desc(),
        )
    )

    if yil is not None:
        stmt = stmt.where(func.year(Gider.gider_tarihi) == yil)

    rows = list((await db.execute(stmt)).all())
    return [
        {
            "donem_yil": int(r.yil),
            "donem_ay": int(r.ay),
            "toplam_tutar": Decimal(str(r.toplam or 0)),
            "kayit_sayisi": int(r.sayi or 0),
        }
        for r in rows
    ]


async def get_karsilastirma(
    db: AsyncSession,
    site_no: int,
    *,
    yil: int,
    ay: int,
) -> dict:
    """Belirli bir dönem için gider-gelir karşılaştırması."""
    # Gider toplamı
    gider_stmt = select(func.coalesce(func.sum(Gider.tutar + Gider.kdv_tutar), 0)).where(
        Gider.site_no == site_no,
        func.year(Gider.gider_tarihi) == yil,
        func.month(Gider.gider_tarihi) == ay,
    )
    toplam_gider = Decimal(str((await db.execute(gider_stmt)).scalar() or 0))

    # Gelir toplamı
    gelir_stmt = select(func.coalesce(func.sum(Gelir.tutar), 0)).where(
        Gelir.site_no == site_no,
        func.year(Gelir.gelir_tarihi) == yil,
        func.month(Gelir.gelir_tarihi) == ay,
    )
    toplam_gelir = Decimal(str((await db.execute(gelir_stmt)).scalar() or 0))

    net = toplam_gelir - toplam_gider
    return {
        "donem_yil": yil,
        "donem_ay": ay,
        "toplam_gider": toplam_gider,
        "toplam_gelir": toplam_gelir,
        "net_durum": net,
        "kar_zarar": "KAR" if net >= 0 else "ZARAR",
    }


# ============================================================
# LOOKUP LİSTELERİ
# ============================================================
async def list_kategoriler(db: AsyncSession) -> list[dict]:
    sonuc = await db.execute(select(GiderKategori).order_by(GiderKategori.ad))
    return [
        {"kategori_no": k.kategori_no, "ad": k.ad}
        for k in sonuc.scalars().all()
    ]


async def list_kalemler(db: AsyncSession, kategori_no: int | None = None) -> list[dict]:
    stmt = (
        select(GiderKalemi, GiderKategori)
        .join(GiderKategori, GiderKategori.kategori_no == GiderKalemi.kategori_no)
        .order_by(GiderKategori.ad, GiderKalemi.kalem_adi)
    )
    if kategori_no is not None:
        stmt = stmt.where(GiderKalemi.kategori_no == kategori_no)

    sonuc = await db.execute(stmt)
    return [
        {
            "kalem_no": k.kalem_no,
            "kalem_adi": k.kalem_adi,
            "kategori_no": k.kategori_no,
            "kategori_adi": ka.ad,
        }
        for k, ka in sonuc.all()
    ]


async def list_cariler(db: AsyncSession, site_no: int) -> list[dict]:
    sonuc = await db.execute(
        select(CariHesap)
        .where(CariHesap.site_no == site_no, CariHesap.aktif_mi.is_(True))
        .order_by(CariHesap.unvan)
    )
    return [
        {
            "cari_no": c.cari_no,
            "unvan": c.unvan,
            "vergi_no": c.vergi_no,
            "telefon": c.telefon,
            "aktif_mi": c.aktif_mi,
        }
        for c in sonuc.scalars().all()
    ]


# ============================================================
# GELİR İŞLEMLERİ
# ============================================================
async def list_gelirler(
    db: AsyncSession,
    site_no: int,
    *,
    tarih_baslangic: date | None = None,
    tarih_bitis: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    stmt = select(Gelir).where(Gelir.site_no == site_no)
    if tarih_baslangic is not None:
        stmt = stmt.where(Gelir.gelir_tarihi >= tarih_baslangic)
    if tarih_bitis is not None:
        stmt = stmt.where(Gelir.gelir_tarihi <= tarih_bitis)
    stmt = stmt.order_by(Gelir.gelir_tarihi.desc()).limit(limit).offset(offset)

    sonuc = await db.execute(stmt)
    return [
        {
            "gelir_no": g.gelir_no,
            "site_no": g.site_no,
            "kaynak": g.kaynak,
            "tutar": g.tutar,
            "gelir_tarihi": g.gelir_tarihi,
            "aciklama": g.aciklama,
            "kaydeden_no": g.kaydeden_no,
            "olusturma_tarihi": g.olusturma_tarihi,
        }
        for g in sonuc.scalars().all()
    ]


async def get_gelir(db: AsyncSession, gelir_no: int, site_no: int) -> Gelir:
    sonuc = await db.execute(
        select(Gelir).where(Gelir.gelir_no == gelir_no, Gelir.site_no == site_no)
    )
    g = sonuc.scalar_one_or_none()
    if g is None:
        raise BulunamadiHatasi("Gelir", kaynak_id=gelir_no)
    return g


async def create_gelir(
    db: AsyncSession,
    site_no: int,
    *,
    kaynak: str,
    tutar: Decimal,
    gelir_tarihi: date,
    kaydeden_no: int,
    aciklama: str | None = None,
) -> Gelir:
    gelir = Gelir(
        site_no=site_no,
        kaynak=kaynak,
        tutar=tutar,
        gelir_tarihi=gelir_tarihi,
        aciklama=aciklama,
        kaydeden_no=kaydeden_no,
    )
    db.add(gelir)
    await db.commit()
    await db.refresh(gelir)
    logger.info("Yeni gelir: no=%s site=%s tutar=%s", gelir.gelir_no, site_no, tutar)
    return gelir


async def update_gelir(
    db: AsyncSession,
    gelir_no: int,
    site_no: int,
    *,
    kaynak: str | None = None,
    tutar: Decimal | None = None,
    gelir_tarihi: date | None = None,
    aciklama: str | None = None,
) -> Gelir:
    gelir = await get_gelir(db, gelir_no, site_no)
    if kaynak is not None:
        gelir.kaynak = kaynak
    if tutar is not None:
        gelir.tutar = tutar
    if gelir_tarihi is not None:
        gelir.gelir_tarihi = gelir_tarihi
    if aciklama is not None:
        gelir.aciklama = aciklama
    await db.commit()
    await db.refresh(gelir)
    return gelir


async def delete_gelir(db: AsyncSession, gelir_no: int, site_no: int) -> None:
    gelir = await get_gelir(db, gelir_no, site_no)
    await db.delete(gelir)
    await db.commit()