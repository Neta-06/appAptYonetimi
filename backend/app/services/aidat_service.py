"""Aidat ve ÃƒÂ¶deme iÃ…Å¸ mantÃ„Â±Ã„Å¸Ã„Â±."""

import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BulunamadiHatasi,
    IsKuraliHatasi,
)
from app.core.utils import now_utc_naive
from app.models import (
    Aidat,
    AidatTipi,
    Blok,
    Daire,
    Odeme,
    OdemeDetay,
    OdemeKanali,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI: Aidat durumunu gÃƒÂ¼ncelle
# ============================================================
def _durum_guncelle(aidat: Aidat) -> None:
    """Ãƒâ€“denen tutara gÃƒÂ¶re aidat durumunu yeniden hesaplar."""
    if aidat.durum == "IPTAL":
        return  # iptal edilmiÃ…Å¸se dokunma

    kalan = aidat.tutar - aidat.odenen_tutar

    if kalan <= 0:
        aidat.durum = "ODENDI"
    elif aidat.odenen_tutar > 0:
        aidat.durum = "KISMI_ODENDI"
    else:
        # Ãƒâ€“denmemiÃ…Å¸ Ã¢â‚¬â€ son tarih geÃƒÂ§tiyse GECIKMIS
        if aidat.son_odeme_tarihi < date.today():
            aidat.durum = "GECIKMIS"
        else:
            aidat.durum = "BEKLIYOR"


# ============================================================
# LÃ„Â°STELEME
# ============================================================
async def list_aidatlar(
    db: AsyncSession,
    site_no: int,
    *,
    donem_yil: int | None = None,
    donem_ay: int | None = None,
    durum: str | None = None,
    daire_no: int | None = None,
    aidat_tipi_no: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Site aidatlarÃ„Â±nÃ„Â± filtreli listeler."""
    stmt = (
        select(Aidat, Daire, Blok, AidatTipi)
        .join(Daire, Daire.daire_no == Aidat.daire_no)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .join(AidatTipi, AidatTipi.tip_no == Aidat.aidat_tipi_no)
        .where(Aidat.site_no == site_no)
    )

    if donem_yil is not None:
        stmt = stmt.where(Aidat.donem_yil == donem_yil)
    if donem_ay is not None:
        stmt = stmt.where(Aidat.donem_ay == donem_ay)
    if durum is not None:
        stmt = stmt.where(Aidat.durum == durum)
    if daire_no is not None:
        stmt = stmt.where(Aidat.daire_no == daire_no)
    if aidat_tipi_no is not None:
        stmt = stmt.where(Aidat.aidat_tipi_no == aidat_tipi_no)

    stmt = stmt.order_by(
        Aidat.donem_yil.desc(),
        Aidat.donem_ay.desc(),
        Blok.blok_adi,
        Daire.daire_numarasi,
    ).limit(limit).offset(offset)

    sonuc = await db.execute(stmt)
    kayitlar = []
    for a, d, b, t in sonuc.all():
        kayitlar.append({
            "aidat_no": a.aidat_no,
            "daire_no": d.daire_no,
            "blok_adi": b.blok_adi,
            "daire_numarasi": d.daire_numarasi,
            "aidat_tipi": t.ad,
            "donem_yil": a.donem_yil,
            "donem_ay": a.donem_ay,
            "tutar": a.tutar,
            "odenen_tutar": a.odenen_tutar,
            "kalan_tutar": a.tutar - a.odenen_tutar,
            "son_odeme_tarihi": a.son_odeme_tarihi,
            "durum": a.durum,
        })
    return kayitlar


async def get_aidat(db: AsyncSession, aidat_no: int, site_no: int) -> Aidat:
    """Tek aidat detayÃ„Â± (site kontrolÃƒÂ¼ zorunlu)."""
    sonuc = await db.execute(
        select(Aidat).where(
            Aidat.aidat_no == aidat_no,
            Aidat.site_no == site_no,
        )
    )
    aidat = sonuc.scalar_one_or_none()
    if aidat is None:
        raise BulunamadiHatasi("Aidat", kaynak_id=aidat_no)
    return aidat


# ============================================================
# Ãƒâ€“ZET Ã„Â°STATÃ„Â°STÃ„Â°KLER
# ============================================================
async def get_ozet(
    db: AsyncSession,
    site_no: int,
    *,
    donem_yil: int | None = None,
    donem_ay: int | None = None,
) -> dict:
    """Site geneli aidat ÃƒÂ¶zet istatistikleri."""
    stmt = select(
        func.count(Aidat.aidat_no).label("toplam_sayi"),
        func.coalesce(func.sum(Aidat.tutar), 0).label("toplam_tahakkuk"),
        func.coalesce(func.sum(Aidat.odenen_tutar), 0).label("toplam_tahsilat"),
        func.sum(
            case((Aidat.durum == "ODENDI", 1), else_=0)
        ).label("odenmis"),
        func.sum(
            case((Aidat.durum == "BEKLIYOR", 1), else_=0)
        ).label("bekleyen"),
        func.sum(
            case((Aidat.durum == "GECIKMIS", 1), else_=0)
        ).label("gecikmis"),
        func.sum(
            case((Aidat.durum == "KISMI_ODENDI", 1), else_=0)
        ).label("kismi"),
    ).where(Aidat.site_no == site_no, Aidat.durum != "IPTAL")

    if donem_yil is not None:
        stmt = stmt.where(Aidat.donem_yil == donem_yil)
    if donem_ay is not None:
        stmt = stmt.where(Aidat.donem_ay == donem_ay)

    row = (await db.execute(stmt)).first()

    toplam_tahakkuk = Decimal(str(row.toplam_tahakkuk or 0))
    toplam_tahsilat = Decimal(str(row.toplam_tahsilat or 0))
    toplam_kalan = toplam_tahakkuk - toplam_tahsilat

    oran = 0.0
    if toplam_tahakkuk > 0:
        oran = float(toplam_tahsilat / toplam_tahakkuk * 100)

    return {
        "toplam_tahakkuk": toplam_tahakkuk,
        "toplam_tahsilat": toplam_tahsilat,
        "toplam_kalan": toplam_kalan,
        "odenmis_sayisi": int(row.odenmis or 0),
        "bekleyen_sayisi": int(row.bekleyen or 0),
        "gecikmis_sayisi": int(row.gecikmis or 0),
        "kismi_odenmis_sayisi": int(row.kismi or 0),
        "tahsilat_orani": round(oran, 2),
    }


# ============================================================
# DAÃ„Â°RE AÃ„Â°DAT GEÃƒâ€¡MÃ„Â°Ã…ÂÃ„Â°
# ============================================================
async def list_daire_aidat_gecmisi(
    db: AsyncSession, daire_no: int, site_no: int
) -> dict:
    """Bir dairenin tÃƒÂ¼m aidat geÃƒÂ§miÃ…Å¸i + ÃƒÂ¶zet."""
    # Daire bilgisi
    d_sonuc = await db.execute(
        select(Daire, Blok)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .where(Daire.daire_no == daire_no, Daire.site_no == site_no)
    )
    d_row = d_sonuc.first()
    if d_row is None:
        raise BulunamadiHatasi("Daire", kaynak_id=daire_no)
    daire, blok = d_row

    # Aidatlar
    a_sonuc = await db.execute(
        select(Aidat, AidatTipi)
        .join(AidatTipi, AidatTipi.tip_no == Aidat.aidat_tipi_no)
        .where(Aidat.daire_no == daire_no, Aidat.durum != "IPTAL")
        .order_by(Aidat.donem_yil.desc(), Aidat.donem_ay.desc())
    )
    aidatlar = []
    toplam_borc = Decimal("0.00")
    toplam_odenen = Decimal("0.00")

    for a, t in a_sonuc.all():
        toplam_borc += a.tutar
        toplam_odenen += a.odenen_tutar
        aidatlar.append({
            "aidat_no": a.aidat_no,
            "daire_no": daire.daire_no,
            "blok_adi": blok.blok_adi,
            "daire_numarasi": daire.daire_numarasi,
            "aidat_tipi": t.ad,
            "donem_yil": a.donem_yil,
            "donem_ay": a.donem_ay,
            "tutar": a.tutar,
            "odenen_tutar": a.odenen_tutar,
            "kalan_tutar": a.tutar - a.odenen_tutar,
            "son_odeme_tarihi": a.son_odeme_tarihi,
            "durum": a.durum,
        })

    return {
        "daire_no": daire.daire_no,
        "blok_adi": blok.blok_adi,
        "daire_numarasi": daire.daire_numarasi,
        "toplam_borc": toplam_borc,
        "toplam_odenen": toplam_odenen,
        "kalan": toplam_borc - toplam_odenen,
        "aidatlar": aidatlar,
    }


# ============================================================
# GECÃ„Â°KMÃ„Â°Ã…Â AÃ„Â°DATLAR
# ============================================================
async def list_gecikmis(db: AsyncSession, site_no: int) -> list[dict]:
    """GecikmiÃ…Å¸ veya kÃ„Â±smi ÃƒÂ¶denmiÃ…Å¸ aidatlar."""
    sonuc = await db.execute(
        select(Aidat, Daire, Blok, AidatTipi)
        .join(Daire, Daire.daire_no == Aidat.daire_no)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .join(AidatTipi, AidatTipi.tip_no == Aidat.aidat_tipi_no)
        .where(
            Aidat.site_no == site_no,
            Aidat.durum.in_(["BEKLIYOR", "GECIKMIS", "KISMI_ODENDI"]),
            Aidat.son_odeme_tarihi < date.today(),
        )
        .order_by(Aidat.son_odeme_tarihi)
    )
    kayitlar = []
    for a, d, b, t in sonuc.all():
        gecikme_gun = (date.today() - a.son_odeme_tarihi).days
        kayitlar.append({
            "aidat_no": a.aidat_no,
            "daire_no": d.daire_no,
            "blok_adi": b.blok_adi,
            "daire_numarasi": d.daire_numarasi,
            "aidat_tipi": t.ad,
            "donem_yil": a.donem_yil,
            "donem_ay": a.donem_ay,
            "tutar": a.tutar,
            "odenen_tutar": a.odenen_tutar,
            "kalan_tutar": a.tutar - a.odenen_tutar,
            "son_odeme_tarihi": a.son_odeme_tarihi,
            "durum": a.durum,
            "gecikme_gun": gecikme_gun,
        })
    return kayitlar


# ============================================================
# Ãƒâ€“DEME OLUÃ…ÂTURMA
# ============================================================
async def create_odeme(
    db: AsyncSession,
    site_no: int,
    *,
    odeme_kanali_no: int,
    detaylar: list[dict],
    olusturan_no: int,
    dekont_no: str | None = None,
    referans_no: str | None = None,
    aciklama: str | None = None,
) -> Odeme:
    """
    Yeni tahsilat kaydÃ„Â± oluÃ…Å¸turur.

    AdÃ„Â±mlar:
      1. Kanal ve onay durumunu doÃ„Å¸rula
      2. Her detay iÃƒÂ§in aidatÃ„Â± bul, site kontrolÃƒÂ¼ yap
      3. Kalan tutarÃ„Â± kontrol et
      4. Ãƒâ€“deme + detaylarÃ„Â± oluÃ…Å¸tur
      5. Her aidatÃ„Â±n odenen_tutar ve durumunu gÃƒÂ¼ncelle
      6. Commit
    """
    if not detaylar:
        raise IsKuraliHatasi("En az bir aidat detayÃ„Â± gerekli.")

    # 1) Kanal kontrolÃƒÂ¼
    kanal = await db.get(OdemeKanali, odeme_kanali_no)
    if kanal is None:
        raise BulunamadiHatasi("OdemeKanali", kaynak_id=odeme_kanali_no)

    # 2) DetaylarÃ„Â± hazÃ„Â±rla
    toplam = Decimal("0.00")
    aidat_nesneleri: list[tuple[OdemeDetay, Aidat]] = []

    for d in detaylar:
        aidat_no = d.get("aidat_no")
        tutar = Decimal(str(d.get("tutar", 0)))
        if tutar <= 0:
            raise IsKuraliHatasi(f"Aidat {aidat_no} iÃƒÂ§in tutar 0'dan bÃƒÂ¼yÃƒÂ¼k olmalÃ„Â±.")

        aidat = await db.get(Aidat, aidat_no)
        if aidat is None:
            raise BulunamadiHatasi("Aidat", kaynak_id=aidat_no)
        if aidat.site_no != site_no:
            # Cross-tenant
            raise BulunamadiHatasi("Aidat", kaynak_id=aidat_no)
        if aidat.durum == "IPTAL":
            raise IsKuraliHatasi(f"Aidat {aidat_no} iptal edilmiÃ…Å¸.")
        if aidat.durum == "ODENDI":
            raise IsKuraliHatasi(f"Aidat {aidat_no} zaten tamamen ÃƒÂ¶denmiÃ…Å¸.")

        kalan = aidat.tutar - aidat.odenen_tutar
        if tutar > kalan:
            raise IsKuraliHatasi(
                f"Aidat {aidat_no} iÃƒÂ§in kalan {kalan} TL; {tutar} TL ÃƒÂ¶denemez."
            )

        toplam += tutar
        detay = OdemeDetay(aidat_no=aidat_no, tutar=tutar)
        aidat_nesneleri.append((detay, aidat))

    # 3) Ãƒâ€“deme baÃ…Å¸lÃ„Â±Ã„Å¸Ã„Â±
    odeme = Odeme(
        site_no=site_no,
        odeme_tarihi=now_utc_naive(),
        toplam_tutar=toplam,
        odeme_kanali_no=odeme_kanali_no,
        dekont_no=dekont_no,
        referans_no=referans_no,
        onay_durum_no=1,  # ONAYLANDI
        onaylayan_no=olusturan_no,
        onay_tarihi=now_utc_naive(),
        aciklama=aciklama,
        olusturan_no=olusturan_no,
    )
    db.add(odeme)

    # 4) DetaylarÃ„Â± ve aidat gÃƒÂ¼ncellemelerini baÃ„Å¸la
    for detay, aidat in aidat_nesneleri:
        db.add(detay)
        detay.odeme = odeme
        aidat.odenen_tutar += detay.tutar
        _durum_guncelle(aidat)

    try:
        await db.commit()
        await db.refresh(odeme)
    except Exception as exc:
        await db.rollback()
        logger.error("Odeme olusturma hatasi: %s", exc, exc_info=True)
        raise

    logger.info(
        "Yeni odeme: no=%s site=%s tutar=%s aidat_sayisi=%s",
        odeme.odeme_no, site_no, toplam, len(aidat_nesneleri),
    )
    return odeme


# ============================================================
# Ãƒâ€“DEME Ã„Â°PTAL
# ============================================================
async def iptal_odeme(
    db: AsyncSession,
    odeme_no: int,
    site_no: int,
    *,
    iptal_nedeni: str,
) -> Odeme:
    """
    Ãƒâ€“demeyi iptal eder ve baÃ„Å¸lÃ„Â± aidatlarÃ„Â± geri alÃ„Â±r.

    AdÃ„Â±mlar:
      1. Ãƒâ€“demeyi bul, site kontrolÃƒÂ¼
      2. Zaten iptal mi?
      3. Her detay iÃƒÂ§in aidatÃ„Â±n odenen_tutar'Ã„Â±nÃ„Â± azalt
      4. Aidat durumunu yeniden hesapla
      5. Ãƒâ€“demeyi REDDEDILDI olarak iÃ…Å¸aretle
      6. Commit
    """
    # 1) Ãƒâ€“demeyi bul
    sonuc = await db.execute(
        select(Odeme).where(Odeme.odeme_no == odeme_no, Odeme.site_no == site_no)
    )
    odeme = sonuc.scalar_one_or_none()
    if odeme is None:
        raise BulunamadiHatasi("Odeme", kaynak_id=odeme_no)

    # 2) Zaten iptal mi? (onay_durum_no=3 = REDDEDILDI)
    if odeme.onay_durum_no == 3:
        raise IsKuraliHatasi("Bu odeme zaten iptal edilmis.")

    # 3) DetaylarÃ„Â± ÃƒÂ§ek
    d_sonuc = await db.execute(
        select(OdemeDetay).where(OdemeDetay.odeme_no == odeme_no)
    )
    detaylar = list(d_sonuc.scalars().all())

    # 4) AidatlarÃ„Â± geri al
    for detay in detaylar:
        if detay.aidat_no is None:
            continue
        aidat = await db.get(Aidat, detay.aidat_no)
        if aidat is None:
            continue
        aidat.odenen_tutar = max(
            Decimal("0.00"), aidat.odenen_tutar - detay.tutar
        )
        _durum_guncelle(aidat)

    # 5) Ãƒâ€“demeyi iptal et
    odeme.onay_durum_no = 3  # REDDEDILDI
    odeme.aciklama = (
        (odeme.aciklama or "") + f" | IPTAL: {iptal_nedeni}"
    )[:255]

    await db.commit()
    await db.refresh(odeme)

    logger.info("Odeme iptal: no=%s site=%s", odeme_no, site_no)
    return odeme


# ============================================================
# TOPLU AÃ„Â°DAT OLUÃ…ÂTURMA
# ============================================================
async def toplu_aidat_olustur(
    db: AsyncSession,
    site_no: int,
    *,
    aidat_tipi_no: int,
    donem_yil: int,
    donem_ay: int,
    son_odeme_tarihi: date,
    blok_no: int | None = None,
    tutar_override: Decimal | None = None,
) -> dict:
    """
    Site geneli toplu aidat borÃƒÂ§landÃ„Â±rma.

    AdÃ„Â±mlar:
      1. Aidat tipi kontrolÃƒÂ¼
      2. Daileleri seÃƒÂ§ (blok filtreli olabilir)
      3. Her daire iÃƒÂ§in aidat tutarÃ„Â±nÃ„Â± belirle (ozel_aidat varsa onu kullan)
      4. Zaten var olan aidatlarÃ„Â± atla
      5. Commit
    """
    # 1) Tip kontrolÃƒÂ¼
    tip = await db.get(AidatTipi, aidat_tipi_no)
    if tip is None:
        raise BulunamadiHatasi("AidatTipi", kaynak_id=aidat_tipi_no)

    # 2) Daireleri seÃƒÂ§
    stmt = select(Daire).where(Daire.site_no == site_no)
    if blok_no is not None:
        stmt = stmt.where(Daire.blok_no == blok_no)
    d_sonuc = await db.execute(stmt)
    daireler = list(d_sonuc.scalars().all())

    if not daireler:
        raise IsKuraliHatasi("Bu filtreye uygun daire bulunamadi.")

    # 3) Site varsayÃ„Â±lan aidat tutarÃ„Â±nÃ„Â± al
    from app.models import Site
    site = await db.get(Site, site_no)
    varsayilan_tutar = site.aylik_aidat if site else Decimal("0.00")

    # 4) Mevcut aidatlarÃ„Â± ÃƒÂ¶nceden yÃƒÂ¼kle (verimlilik)
    mevcut_sonuc = await db.execute(
        select(Aidat.daire_no).where(
            Aidat.site_no == site_no,
            Aidat.donem_yil == donem_yil,
            Aidat.donem_ay == donem_ay,
            Aidat.aidat_tipi_no == aidat_tipi_no,
        )
    )
    mevcut_daireler = {row[0] for row in mevcut_sonuc.all()}

    olusturulan: list[int] = []
    atlanan = 0
    toplam = Decimal("0.00")

    for daire in daireler:
        if daire.daire_no in mevcut_daireler:
            atlanan += 1
            continue

        # Ãƒâ€“zel aidat varsa onu kullan
        if tutar_override is not None:
            tutar = tutar_override
        elif daire.ozel_aidat is not None:
            tutar = daire.ozel_aidat
        else:
            tutar = varsayilan_tutar

        aidat = Aidat(
            site_no=site_no,
            daire_no=daire.daire_no,
            aidat_tipi_no=aidat_tipi_no,
            donem_yil=donem_yil,
            donem_ay=donem_ay,
            tutar=tutar,
            odenen_tutar=Decimal("0.00"),
            son_odeme_tarihi=son_odeme_tarihi,
            durum="BEKLIYOR",
            otomatik_islendi_mi=True,
        )
        db.add(aidat)
        await db.flush()
        olusturulan.append(aidat.aidat_no)
        toplam += tutar

    await db.commit()

    logger.info(
        "Toplu aidat: site=%s donem=%s/%s olusturulan=%s atlanan=%s",
        site_no, donem_yil, donem_ay, len(olusturulan), atlanan,
    )
    return {
        "olusturulan_sayisi": len(olusturulan),
        "atlanan_sayisi": atlanan,
        "toplam_tutar": toplam,
        "aidat_nolar": olusturulan,
    }