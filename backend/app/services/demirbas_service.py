"""Demirbaş ve zimmet iş mantığı."""

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.utils import now_utc_naive
from app.models import (
    Demirbas,
    DemirbasHareket,
    Kullanici,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI: Hareket kaydı
# ============================================================
async def _hareket_kaydet(
    db: AsyncSession,
    *,
    demirbas_no: int,
    hareket_tipi: str,
    kullanici_no: int | None = None,
    aciklama: str | None = None,
    maliyet: Decimal | None = None,
) -> DemirbasHareket:
    """Demirbaşa hareket kaydı ekler."""
    hareket = DemirbasHareket(
        demirbas_no=demirbas_no,
        hareket_tipi=hareket_tipi,
        kullanici_no=kullanici_no,
        tarih=now_utc_naive(),
        aciklama=aciklama,
        maliyet=maliyet,
    )
    db.add(hareket)
    return hareket


# ============================================================
# LİSTELEME
# ============================================================
async def list_demirbaslar(
    db: AsyncSession,
    site_no: int,
    *,
    kategori: str | None = None,
    durum: str | None = None,
    arama: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    """Site demirbaşlarını filtreli listeler."""
    stmt = select(Demirbas).where(Demirbas.site_no == site_no)

    if kategori:
        stmt = stmt.where(Demirbas.kategori == kategori)
    if durum:
        stmt = stmt.where(Demirbas.durum == durum)
    if arama:
        pattern = f"%{arama.lower()}%"
        stmt = stmt.where(
            func.lower(Demirbas.ad).like(pattern)
            | func.lower(func.coalesce(Demirbas.bulundugu_yer, "")).like(pattern)
        )

    stmt = stmt.order_by(Demirbas.ad).limit(limit).offset(offset)
    sonuc = await db.execute(stmt)
    demirbaslar = list(sonuc.scalars().all())
    if not demirbaslar:
        return []

    demirbas_nolar = [d.demirbas_no for d in demirbaslar]

    # Hareket sayıları + son hareket
    h_sonuc = await db.execute(
        select(
            DemirbasHareket.demirbas_no,
            func.count(DemirbasHareket.hareket_no),
            func.max(DemirbasHareket.tarih),
        )
        .where(DemirbasHareket.demirbas_no.in_(demirbas_nolar))
        .group_by(DemirbasHareket.demirbas_no)
    )
    hareket_map = {row[0]: (int(row[1]), row[2]) for row in h_sonuc.all()}

    # Son hareketin tipi
    son_hareket_tipi: dict[int, str] = {}
    if demirbas_nolar:
        # Her demirbaş için en son hareket
        for d_no in demirbas_nolar:
            son_sonuc = await db.execute(
                select(DemirbasHareket.hareket_tipi)
                .where(DemirbasHareket.demirbas_no == d_no)
                .order_by(DemirbasHareket.tarih.desc())
                .limit(1)
            )
            tip = son_sonuc.scalar_one_or_none()
            if tip:
                son_hareket_tipi[d_no] = tip

    kayitlar = []
    for d in demirbaslar:
        h_sayi, h_tarih = hareket_map.get(d.demirbas_no, (0, None))
        toplam_deger = None
        if d.alis_fiyati is not None:
            toplam_deger = (d.alis_fiyati * d.adet).quantize(Decimal("0.01"))

        kayitlar.append({
            "demirbas_no": d.demirbas_no,
            "site_no": d.site_no,
            "ad": d.ad,
            "kategori": d.kategori,
            "adet": d.adet,
            "alis_fiyati": d.alis_fiyati,
            "alis_tarihi": d.alis_tarihi,
            "bulundugu_yer": d.bulundugu_yer,
            "durum": d.durum,
            "toplam_deger": toplam_deger,
            "hareket_sayisi": h_sayi,
            "son_hareket_tarihi": h_tarih,
            "son_hareket_tipi": son_hareket_tipi.get(d.demirbas_no),
        })
    return kayitlar


# ============================================================
# DETAY
# ============================================================
async def get_demirbas(
    db: AsyncSession, demirbas_no: int, site_no: int
) -> dict:
    """Demirbaş detayı + hareket geçmişi + bakım maliyeti."""
    sonuc = await db.execute(
        select(Demirbas).where(
            Demirbas.demirbas_no == demirbas_no,
            Demirbas.site_no == site_no,
        )
    )
    d = sonuc.scalar_one_or_none()
    if d is None:
        raise BulunamadiHatasi("Demirbas", kaynak_id=demirbas_no)

    # Hareket geçmişi (kullanıcı bilgisiyle)
    h_sonuc = await db.execute(
        select(DemirbasHareket, Kullanici)
        .outerjoin(Kullanici, Kullanici.kullanici_no == DemirbasHareket.kullanici_no)
        .where(DemirbasHareket.demirbas_no == demirbas_no)
        .order_by(DemirbasHareket.tarih.desc())
    )
    hareketler = []
    toplam_bakim = Decimal("0.00")
    for h, k in h_sonuc.all():
        kullanici_ad = f"{k.ad} {k.soyad}" if k else None
        if h.maliyet is not None and h.hareket_tipi in ("BAKIM", "ONARIM"):
            toplam_bakim += h.maliyet

        hareketler.append({
            "hareket_no": h.hareket_no,
            "demirbas_no": h.demirbas_no,
            "hareket_tipi": h.hareket_tipi,
            "kullanici_no": h.kullanici_no,
            "kullanici_ad": kullanici_ad,
            "tarih": h.tarih,
            "aciklama": h.aciklama,
            "maliyet": h.maliyet,
        })

    toplam_deger = None
    if d.alis_fiyati is not None:
        toplam_deger = (d.alis_fiyati * d.adet).quantize(Decimal("0.01"))

    return {
        "demirbas_no": d.demirbas_no,
        "site_no": d.site_no,
        "ad": d.ad,
        "kategori": d.kategori,
        "adet": d.adet,
        "alis_fiyati": d.alis_fiyati,
        "alis_tarihi": d.alis_tarihi,
        "bulundugu_yer": d.bulundugu_yer,
        "durum": d.durum,
        "toplam_deger": toplam_deger,
        "toplam_bakim_maliyeti": toplam_bakim,
        "hareketler": hareketler,
    }


# ============================================================
# OLUŞTURMA
# ============================================================
async def create_demirbas(
    db: AsyncSession,
    site_no: int,
    *,
    ad: str,
    adet: int = 1,
    kategori: str | None = None,
    alis_fiyati: Decimal | None = None,
    alis_tarihi: date | None = None,
    bulundugu_yer: str | None = None,
    durum: str = "CALISIYOR",
    olusturan_no: int | None = None,
) -> Demirbas:
    """Yeni demirbaş kaydı."""
    if durum not in ("CALISIYOR", "ARIZALI", "HURDA"):
        raise IsKuraliHatasi(f"Gecersiz durum: {durum}")
    if adet < 1:
        raise IsKuraliHatasi("Adet en az 1 olmalidir.")

    d = Demirbas(
        site_no=site_no,
        ad=ad,
        kategori=kategori,
        adet=adet,
        alis_fiyati=alis_fiyati,
        alis_tarihi=alis_tarihi,
        bulundugu_yer=bulundugu_yer,
        durum=durum,
    )
    db.add(d)
    await db.flush()

    # İlk kayıt hareketi (YER_DEGISIKLIGI olarak)
    if olusturan_no is not None:
        await _hareket_kaydet(
            db,
            demirbas_no=d.demirbas_no,
            hareket_tipi="YER_DEGISIKLIGI",
            kullanici_no=olusturan_no,
            aciklama=f"Kayit olusturuldu: {bulundugu_yer or 'yer belirtilmedi'}",
            maliyet=None,
        )

    await db.commit()
    await db.refresh(d)
    logger.info(
        "Yeni demirbas: no=%s site=%s ad=%s adet=%d",
        d.demirbas_no, site_no, ad[:50], adet,
    )
    return d


# ============================================================
# GÜNCELLE / SİL
# ============================================================
async def update_demirbas(
    db: AsyncSession,
    demirbas_no: int,
    site_no: int,
    *,
    ad: str | None = None,
    kategori: str | None = None,
    adet: int | None = None,
    alis_fiyati: Decimal | None = None,
    alis_tarihi: date | None = None,
    bulundugu_yer: str | None = None,
    durum: str | None = None,
) -> Demirbas:
    """Demirbaşı günceller."""
    sonuc = await db.execute(
        select(Demirbas).where(
            Demirbas.demirbas_no == demirbas_no,
            Demirbas.site_no == site_no,
        )
    )
    d = sonuc.scalar_one_or_none()
    if d is None:
        raise BulunamadiHatasi("Demirbas", kaynak_id=demirbas_no)

    if ad is not None:
        d.ad = ad
    if kategori is not None:
        d.kategori = kategori
    if adet is not None:
        if adet < 1:
            raise IsKuraliHatasi("Adet en az 1 olmalidir.")
        d.adet = adet
    if alis_fiyati is not None:
        d.alis_fiyati = alis_fiyati
    if alis_tarihi is not None:
        d.alis_tarihi = alis_tarihi
    if bulundugu_yer is not None:
        d.bulundugu_yer = bulundugu_yer
    if durum is not None:
        if durum not in ("CALISIYOR", "ARIZALI", "HURDA"):
            raise IsKuraliHatasi(f"Gecersiz durum: {durum}")
        d.durum = durum

    await db.commit()
    await db.refresh(d)
    logger.info("Demirbas guncellendi: no=%s", demirbas_no)
    return d


async def delete_demirbas(
    db: AsyncSession, demirbas_no: int, site_no: int
) -> None:
    """Demirbaşı ve tüm hareketlerini siler (cascade)."""
    sonuc = await db.execute(
        select(Demirbas).where(
            Demirbas.demirbas_no == demirbas_no,
            Demirbas.site_no == site_no,
        )
    )
    d = sonuc.scalar_one_or_none()
    if d is None:
        raise BulunamadiHatasi("Demirbas", kaynak_id=demirbas_no)

    await db.delete(d)
    await db.commit()
    logger.info("Demirbas silindi: no=%s", demirbas_no)


# ============================================================
# DURUM DEĞİŞTİR
# ============================================================
async def durum_degistir(
    db: AsyncSession,
    demirbas_no: int,
    site_no: int,
    *,
    yeni_durum: str,
    kullanici_no: int | None = None,
    aciklama: str | None = None,
) -> Demirbas:
    """
    Demirbaşın durumunu değiştirir ve otomatik hareket kaydı oluşturur.
    HURDA'ya geçişte hareket tipi HURDA olur.
    """
    if yeni_durum not in ("CALISIYOR", "ARIZALI", "HURDA"):
        raise IsKuraliHatasi(f"Gecersiz durum: {yeni_durum}")

    sonuc = await db.execute(
        select(Demirbas).where(
            Demirbas.demirbas_no == demirbas_no,
            Demirbas.site_no == site_no,
        )
    )
    d = sonuc.scalar_one_or_none()
    if d is None:
        raise BulunamadiHatasi("Demirbas", kaynak_id=demirbas_no)

    if d.durum == yeni_durum:
        raise IsKuraliHatasi(f"Demirbas zaten '{yeni_durum}' durumunda.")

    # Hareket tipi eşleşmesi
    hareket_tipi = {
        "CALISIYOR": "ONARIM",
        "ARIZALI": "ONARIM",
        "HURDA": "HURDA",
    }.get(yeni_durum, "YER_DEGISIKLIGI")

    d.durum = yeni_durum

    await _hareket_kaydet(
        db,
        demirbas_no=demirbas_no,
        hareket_tipi=hareket_tipi,
        kullanici_no=kullanici_no,
        aciklama=aciklama or f"Durum degistirildi: {yeni_durum}",
        maliyet=None,
    )

    await db.commit()
    await db.refresh(d)
    logger.info(
        "Demirbas durum degisti: no=%s -> %s", demirbas_no, yeni_durum
    )
    return d


# ============================================================
# HAREKET
# ============================================================
async def hareket_ekle(
    db: AsyncSession,
    demirbas_no: int,
    site_no: int,
    *,
    hareket_tipi: str,
    kullanici_no: int | None = None,
    aciklama: str | None = None,
    maliyet: Decimal | None = None,
) -> DemirbasHareket:
    """Demirbaşa manuel hareket ekler (zimmet, bakım, onarım vb.)."""
    if hareket_tipi not in ("ZIMBET", "BAKIM", "ONARIM", "YER_DEGISIKLIGI", "HURDA"):
        raise IsKuraliHatasi(f"Gecersiz hareket tipi: {hareket_tipi}")

    # Site kontrolü
    sonuc = await db.execute(
        select(Demirbas).where(
            Demirbas.demirbas_no == demirbas_no,
            Demirbas.site_no == site_no,
        )
    )
    d = sonuc.scalar_one_or_none()
    if d is None:
        raise BulunamadiHatasi("Demirbas", kaynak_id=demirbas_no)

    if d.durum == "HURDA":
        raise IsKuraliHatasi("Hurda durumundaki demirbasa hareket eklenemez.")

    # Kullanıcı kontrolü (varsa)
    if kullanici_no is not None:
        k = await db.get(Kullanici, kullanici_no)
        if k is None or not k.aktif_mi:
            raise BulunamadiHatasi("Kullanici", kaynak_id=kullanici_no)

    # Zimmet ise: demirbaş zaten birine zimmetli mi?
    if hareket_tipi == "ZIMBET":
        mevcut_sonuc = await db.execute(
            select(DemirbasHareket)
            .where(DemirbasHareket.demirbas_no == demirbas_no)
            .order_by(DemirbasHareket.tarih.desc())
            .limit(1)
        )
        son = mevcut_sonuc.scalar_one_or_none()
        if son and son.hareket_tipi == "ZIMBET":
            # Aynı kişiye tekrar zimmet?
            if son.kullanici_no == kullanici_no:
                raise IsKuraliHatasi(
                    "Bu demirbas zaten bu kullaniciya zimmetli."
                )

    hareket = await _hareket_kaydet(
        db,
        demirbas_no=demirbas_no,
        hareket_tipi=hareket_tipi,
        kullanici_no=kullanici_no,
        aciklama=aciklama,
        maliyet=maliyet,
    )

    await db.commit()
    await db.refresh(hareket)
    logger.info(
        "Demirbas hareketi: no=%s demirbas=%s tip=%s",
        hareket.hareket_no, demirbas_no, hareket_tipi,
    )
    return hareket


# ============================================================
# ÖZET İSTATİSTİKLER
# ============================================================
async def get_ozet(db: AsyncSession, site_no: int) -> dict:
    """Site geneli demirbaş özeti."""
    # Toplam kalem, adet, durum dağılımı, toplam değer
    genel_sonuc = await db.execute(
        select(
            func.count(Demirbas.demirbas_no),
            func.coalesce(func.sum(Demirbas.adet), 0),
            func.sum(case((Demirbas.durum == "CALISIYOR", 1), else_=0)),
            func.sum(case((Demirbas.durum == "ARIZALI", 1), else_=0)),
            func.sum(case((Demirbas.durum == "HURDA", 1), else_=0)),
            func.coalesce(
                func.sum(Demirbas.alis_fiyati * Demirbas.adet), 0
            ),
        ).where(Demirbas.site_no == site_no)
    )
    row = genel_sonuc.first()
    toplam_kalem = int(row[0] or 0)
    toplam_adet = int(row[1] or 0)
    calisiyor = int(row[2] or 0)
    arizali = int(row[3] or 0)
    hurda = int(row[4] or 0)
    toplam_deger = Decimal(str(row[5] or 0))

    # Toplam bakım maliyeti
    bakim_sonuc = await db.execute(
        select(func.coalesce(func.sum(DemirbasHareket.maliyet), 0))
        .join(Demirbas, Demirbas.demirbas_no == DemirbasHareket.demirbas_no)
        .where(
            Demirbas.site_no == site_no,
            DemirbasHareket.hareket_tipi.in_(["BAKIM", "ONARIM"]),
        )
    )
    toplam_bakim = Decimal(str(bakim_sonuc.scalar() or 0))

    # Kategori bazlı dağılım
    kat_sonuc = await db.execute(
        select(
            func.coalesce(Demirbas.kategori, "DIGER"),
            func.count(Demirbas.demirbas_no),
            func.coalesce(func.sum(Demirbas.adet), 0),
            func.coalesce(func.sum(Demirbas.alis_fiyati * Demirbas.adet), 0),
        )
        .where(Demirbas.site_no == site_no)
        .group_by(Demirbas.kategori)
        .order_by(func.count(Demirbas.demirbas_no).desc())
    )
    kategoriler = [
        {
            "kategori": r[0],
            "kalem": int(r[1] or 0),
            "adet": int(r[2] or 0),
            "deger": Decimal(str(r[3] or 0)),
        }
        for r in kat_sonuc.all()
    ]

    return {
        "site_no": site_no,
        "toplam_kalem": toplam_kalem,
        "toplam_adet": toplam_adet,
        "calisiyor": calisiyor,
        "arizali": arizali,
        "hurda": hurda,
        "toplam_deger": toplam_deger,
        "toplam_bakim_maliyeti": toplam_bakim,
        "kategoriler": kategoriler,
    }