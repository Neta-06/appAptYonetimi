"""Sayaç ve tüketim iş mantığı."""

import logging
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.utils import now_utc_naive
from app.models import (
    Blok,
    Daire,
    DaireSayaci,
    Kullanici,
    SayacBirim,
    SayacFaturaPayi,
    SayacFaturasi,
    SayacOkuma,
    SayacTuru,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI
# ============================================================
def _yuvarla(deger: Decimal) -> Decimal:
    """2 haneye yuvarlar (banker's rounding yerine HALF_UP)."""
    return Decimal(deger).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ============================================================
# LOOKUP
# ============================================================
async def list_birimler(db: AsyncSession) -> list[dict]:
    sonuc = await db.execute(select(SayacBirim).order_by(SayacBirim.ad))
    return [
        {"birim_no": b.birim_no, "ad": b.ad}
        for b in sonuc.scalars().all()
    ]


async def list_sayac_turleri(db: AsyncSession) -> list[dict]:
    sonuc = await db.execute(
        select(SayacTuru, SayacBirim)
        .join(SayacBirim, SayacBirim.birim_no == SayacTuru.birim_no)
        .order_by(SayacTuru.adi)
    )
    return [
        {
            "sayac_turu_no": st.sayac_turu_no,
            "adi": st.adi,
            "birim_no": st.birim_no,
            "birim_ad": sb.ad,
        }
        for st, sb in sonuc.all()
    ]


# ============================================================
# DAİRE SAYAÇLARI
# ============================================================
async def list_daire_sayaclari(
    db: AsyncSession,
    site_no: int,
    daire_no: int,
) -> list[dict]:
    """Belirli bir dairenin sayaçlarını listeler."""
    # Daire site kontrolü
    daire = await db.get(Daire, daire_no)
    if daire is None or daire.site_no != site_no:
        raise BulunamadiHatasi("Daire", kaynak_id=daire_no)

    sonuc = await db.execute(
        select(DaireSayaci, SayacTuru, SayacBirim)
        .join(SayacTuru, SayacTuru.sayac_turu_no == DaireSayaci.sayac_turu_no)
        .join(SayacBirim, SayacBirim.birim_no == SayacTuru.birim_no)
        .where(DaireSayaci.daire_no == daire_no)
        .order_by(SayacTuru.adi)
    )
    sayaclar = list(sonuc.all())
    if not sayaclar:
        return []

    # Her sayaç için son okuma
    sayac_nolar = [s[0].daire_sayac_no for s in sayaclar]
    son_okuma_alt = (
        select(
            SayacOkuma.daire_sayac_no,
            func.max(SayacOkuma.okuma_tarihi).label("son_tarih"),
        )
        .where(SayacOkuma.daire_sayac_no.in_(sayac_nolar))
        .group_by(SayacOkuma.daire_sayac_no)
        .subquery()
    )
    okuma_sonuc = await db.execute(
        select(SayacOkuma)
        .join(
            son_okuma_alt,
            (SayacOkuma.daire_sayac_no == son_okuma_alt.c.daire_sayac_no)
            & (SayacOkuma.okuma_tarihi == son_okuma_alt.c.son_tarih),
        )
    )
    okuma_map = {o.daire_sayac_no: o for o in okuma_sonuc.scalars().all()}

    kayitlar = []
    for ds, st, sb in sayaclar:
        son = okuma_map.get(ds.daire_sayac_no)
        kayitlar.append({
            "daire_sayac_no": ds.daire_sayac_no,
            "daire_no": ds.daire_no,
            "sayac_turu_no": ds.sayac_turu_no,
            "sayac_turu": st.adi,
            "birim": sb.ad,
            "seri_no": ds.seri_no,
            "montaj_tarihi": ds.montaj_tarihi,
            "sokulme_tarihi": ds.sokulme_tarihi,
            "ilk_deger": ds.ilk_deger,
            "aktif_mi": ds.aktif_mi,
            "son_okuma_degeri": son.guncel_deger if son else None,
            "son_okuma_tarihi": son.okuma_tarihi if son else None,
        })
    return kayitlar


async def get_daire_sayaci(
    db: AsyncSession,
    daire_sayac_no: int,
    site_no: int,
) -> dict:
    """Tek sayaç detayı (site kontrolü)."""
    sonuc = await db.execute(
        select(DaireSayaci, SayacTuru, SayacBirim, Daire)
        .join(SayacTuru, SayacTuru.sayac_turu_no == DaireSayaci.sayac_turu_no)
        .join(SayacBirim, SayacBirim.birim_no == SayacTuru.birim_no)
        .join(Daire, Daire.daire_no == DaireSayaci.daire_no)
        .where(
            DaireSayaci.daire_sayac_no == daire_sayac_no,
            Daire.site_no == site_no,
        )
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("DaireSayaci", kaynak_id=daire_sayac_no)
    ds, st, sb, _ = row
    return {
        "daire_sayac_no": ds.daire_sayac_no,
        "daire_no": ds.daire_no,
        "sayac_turu_no": ds.sayac_turu_no,
        "sayac_turu": st.adi,
        "birim": sb.ad,
        "seri_no": ds.seri_no,
        "montaj_tarihi": ds.montaj_tarihi,
        "sokulme_tarihi": ds.sokulme_tarihi,
        "ilk_deger": ds.ilk_deger,
        "aktif_mi": ds.aktif_mi,
        "son_okuma_degeri": None,
        "son_okuma_tarihi": None,
    }


async def create_daire_sayaci(
    db: AsyncSession,
    site_no: int,
    daire_no: int,
    *,
    sayac_turu_no: int,
    seri_no: str,
    montaj_tarihi: date | None = None,
    ilk_deger: Decimal = Decimal("0.00"),
) -> DaireSayaci:
    """Daireye yeni sayaç ekler."""
    # Daire kontrolü
    daire = await db.get(Daire, daire_no)
    if daire is None or daire.site_no != site_no:
        raise BulunamadiHatasi("Daire", kaynak_id=daire_no)

    # Tür kontrolü
    tur = await db.get(SayacTuru, sayac_turu_no)
    if tur is None:
        raise BulunamadiHatasi("SayacTuru", kaynak_id=sayac_turu_no)

    # Seri no benzersizliği
    mevcut = await db.execute(
        select(DaireSayaci).where(DaireSayaci.seri_no == seri_no)
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi(f"'{seri_no}' seri numarali sayac zaten kayitli.")

    sayac = DaireSayaci(
        daire_no=daire_no,
        sayac_turu_no=sayac_turu_no,
        seri_no=seri_no,
        montaj_tarihi=montaj_tarihi,
        ilk_deger=ilk_deger,
        aktif_mi=True,
    )
    db.add(sayac)
    await db.commit()
    await db.refresh(sayac)
    logger.info(
        "Yeni sayac: no=%s daire=%s tur=%s seri=%s",
        sayac.daire_sayac_no, daire_no, tur.adi, seri_no,
    )
    return sayac


async def update_daire_sayaci(
    db: AsyncSession,
    daire_sayac_no: int,
    site_no: int,
    *,
    seri_no: str | None = None,
    montaj_tarihi: date | None = None,
    sokulme_tarihi: date | None = None,
    aktif_mi: bool | None = None,
) -> DaireSayaci:
    """Sayaç bilgilerini günceller."""
    # Site kontrolü ile sayacı bul
    sonuc = await db.execute(
        select(DaireSayaci)
        .join(Daire, Daire.daire_no == DaireSayaci.daire_no)
        .where(
            DaireSayaci.daire_sayac_no == daire_sayac_no,
            Daire.site_no == site_no,
        )
    )
    sayac = sonuc.scalar_one_or_none()
    if sayac is None:
        raise BulunamadiHatasi("DaireSayaci", kaynak_id=daire_sayac_no)

    if seri_no is not None and seri_no != sayac.seri_no:
        mevcut = await db.execute(
            select(DaireSayaci).where(DaireSayaci.seri_no == seri_no)
        )
        if mevcut.scalar_one_or_none() is not None:
            raise IsKuraliHatasi(f"'{seri_no}' seri numarali sayac zaten kayitli.")
        sayac.seri_no = seri_no

    if montaj_tarihi is not None:
        sayac.montaj_tarihi = montaj_tarihi
    if sokulme_tarihi is not None:
        sayac.sokulme_tarihi = sokulme_tarihi
        sayac.aktif_mi = False
    if aktif_mi is not None:
        sayac.aktif_mi = aktif_mi

    await db.commit()
    await db.refresh(sayac)
    return sayac


# ============================================================
# OKUMA
# ============================================================
async def list_okumalar(
    db: AsyncSession,
    daire_sayac_no: int,
    site_no: int,
    *,
    limit: int = 100,
) -> list[dict]:
    """Bir sayacın okuma geçmişi."""
    # Site kontrolü
    await get_daire_sayaci(db, daire_sayac_no, site_no)

    sonuc = await db.execute(
        select(SayacOkuma, Kullanici)
        .outerjoin(Kullanici, Kullanici.kullanici_no == SayacOkuma.okuyan_no)
        .where(SayacOkuma.daire_sayac_no == daire_sayac_no)
        .order_by(SayacOkuma.okuma_tarihi.desc())
        .limit(limit)
    )
    kayitlar = []
    for o, k in sonuc.all():
        kayitlar.append({
            "okuma_no": o.okuma_no,
            "daire_sayac_no": o.daire_sayac_no,
            "okuma_tarihi": o.okuma_tarihi,
            "guncel_deger": o.guncel_deger,
            "tuketim": o.tuketim,
            "okuyan_no": o.okuyan_no,
            "okuyan_ad": f"{k.ad} {k.soyad}" if k else None,
            "olusturma_tarihi": o.olusturma_tarihi,
        })
    return kayitlar


async def create_okuma(
    db: AsyncSession,
    daire_sayac_no: int,
    site_no: int,
    *,
    okuma_tarihi: date,
    guncel_deger: Decimal,
    okuyan_no: int,
) -> SayacOkuma:
    """
    Yeni okuma girişi.
    Trigger (trg_sayac_okuma_tuketim) tüketimi otomatik hesaplar.
    """
    # Site kontrolü
    await get_daire_sayaci(db, daire_sayac_no, site_no)

    # Aynı tarihte okuma var mı?
    mevcut = await db.execute(
        select(SayacOkuma).where(
            SayacOkuma.daire_sayac_no == daire_sayac_no,
            SayacOkuma.okuma_tarihi == okuma_tarihi,
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi(
            f"'{okuma_tarihi}' tarihinde bu sayac icin okuma zaten kayitli."
        )

    okuma = SayacOkuma(
        daire_sayac_no=daire_sayac_no,
        okuma_tarihi=okuma_tarihi,
        guncel_deger=guncel_deger,
        okuyan_no=okuyan_no,
        olusturma_tarihi=now_utc_naive(),
    )
    db.add(okuma)
    await db.commit()
    await db.refresh(okuma)
    logger.info(
        "Yeni okuma: no=%s sayac=%s deger=%s tuketim=%s",
        okuma.okuma_no, daire_sayac_no, guncel_deger, okuma.tuketim,
    )
    return okuma


async def delete_okuma(
    db: AsyncSession,
    okuma_no: int,
    site_no: int,
) -> None:
    """Okuma kaydını siler."""
    sonuc = await db.execute(
        select(SayacOkuma)
        .join(DaireSayaci, DaireSayaci.daire_sayac_no == SayacOkuma.daire_sayac_no)
        .join(Daire, Daire.daire_no == DaireSayaci.daire_no)
        .where(
            SayacOkuma.okuma_no == okuma_no,
            Daire.site_no == site_no,
        )
    )
    okuma = sonuc.scalar_one_or_none()
    if okuma is None:
        raise BulunamadiHatasi("SayacOkuma", kaynak_id=okuma_no)

    await db.delete(okuma)
    await db.commit()


# ============================================================
# FATURA
# ============================================================
async def list_faturalar(
    db: AsyncSession,
    site_no: int,
    *,
    sayac_turu_no: int | None = None,
    donem_yil: int | None = None,
    limit: int = 100,
) -> list[dict]:
    """Site faturalarını listeler."""
    stmt = (
        select(SayacFaturasi, SayacTuru)
        .join(SayacTuru, SayacTuru.sayac_turu_no == SayacFaturasi.sayac_turu_no)
        .where(SayacFaturasi.site_no == site_no)
    )
    if sayac_turu_no is not None:
        stmt = stmt.where(SayacFaturasi.sayac_turu_no == sayac_turu_no)
    if donem_yil is not None:
        stmt = stmt.where(SayacFaturasi.donem_yil == donem_yil)

    stmt = stmt.order_by(
        SayacFaturasi.donem_yil.desc(),
        SayacFaturasi.donem_ay.desc(),
    ).limit(limit)

    sonuc = await db.execute(stmt)
    faturalar = list(sonuc.all())
    if not faturalar:
        return []

    # Pay sayıları
    fatura_nolar = [f[0].fatura_no for f in faturalar]
    p_sonuc = await db.execute(
        select(SayacFaturaPayi.fatura_no, func.count(SayacFaturaPayi.pay_no))
        .where(SayacFaturaPayi.fatura_no.in_(fatura_nolar))
        .group_by(SayacFaturaPayi.fatura_no)
    )
    pay_map = dict(p_sonuc.all())

    return [
        {
            "fatura_no": f.fatura_no,
            "site_no": f.site_no,
            "sayac_turu_no": f.sayac_turu_no,
            "sayac_turu": st.adi,
            "donem_yil": f.donem_yil,
            "donem_ay": f.donem_ay,
            "toplam_tutar": f.toplam_tutar,
            "ortak_alan_tutar": f.ortak_alan_tutar,
            "dagitim_sekli": f.dagitim_sekli,
            "olusturma_tarihi": f.olusturma_tarihi,
            "pay_sayisi": pay_map.get(f.fatura_no, 0),
        }
        for f, st in faturalar
    ]


async def get_fatura(
    db: AsyncSession,
    fatura_no: int,
    site_no: int,
) -> dict:
    """Fatura detayı + paylar."""
    sonuc = await db.execute(
        select(SayacFaturasi, SayacTuru)
        .join(SayacTuru, SayacTuru.sayac_turu_no == SayacFaturasi.sayac_turu_no)
        .where(
            SayacFaturasi.fatura_no == fatura_no,
            SayacFaturasi.site_no == site_no,
        )
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("SayacFaturasi", kaynak_id=fatura_no)
    f, st = row

    # Paylar (daire bilgisiyle)
    p_sonuc = await db.execute(
        select(SayacFaturaPayi, Daire, Blok)
        .join(Daire, Daire.daire_no == SayacFaturaPayi.daire_no)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .where(SayacFaturaPayi.fatura_no == fatura_no)
        .order_by(Blok.blok_adi, Daire.daire_numarasi)
    )
    paylar = []
    toplam_tuketim = Decimal("0.00")
    toplam_dagitilan = Decimal("0.00")
    for p, d, b in p_sonuc.all():
        toplam_tuketim += p.tuketim
        toplam_dagitilan += p.daire_tutari
        paylar.append({
            "pay_no": p.pay_no,
            "fatura_no": p.fatura_no,
            "daire_no": d.daire_no,
            "daire_ozet": f"{b.blok_adi} - Daire {d.daire_numarasi}",
            "tuketim": p.tuketim,
            "daire_tutari": p.daire_tutari,
            "aidat_no": p.aidat_no,
        })

    return {
        "fatura_no": f.fatura_no,
        "site_no": f.site_no,
        "sayac_turu_no": f.sayac_turu_no,
        "sayac_turu": st.adi,
        "donem_yil": f.donem_yil,
        "donem_ay": f.donem_ay,
        "toplam_tutar": f.toplam_tutar,
        "ortak_alan_tutar": f.ortak_alan_tutar,
        "dagitim_sekli": f.dagitim_sekli,
        "olusturma_tarihi": f.olusturma_tarihi,
        "paylar": paylar,
        "toplam_tuketim": toplam_tuketim,
        "toplam_dagitilan": toplam_dagitilan,
    }


async def create_fatura(
    db: AsyncSession,
    site_no: int,
    *,
    sayac_turu_no: int,
    donem_yil: int,
    donem_ay: int,
    toplam_tutar: Decimal,
    ortak_alan_tutar: Decimal,
    dagitim_sekli: str,
) -> SayacFaturasi:
    """
    Fatura oluşturur ve dairelere dağıtır.

    Adımlar:
      1. Tür kontrolü, aynı dönem tekrarı engeli
      2. Dağıtılabilir tutarı hesapla (toplam - ortak_alan)
      3. Dağıtım şekline göre her daireye düşen tutarı hesapla:
         - TUKETIME_GORE: o dönem tüketim oranına göre
         - ESIT: eşit paylaşım
         - METREKARE: brut_metrekare oranına göre
      4. SayacFaturaPayi kayıtları oluştur
      5. Commit
    """
    # 1) Tür ve tekrar kontrolü
    tur = await db.get(SayacTuru, sayac_turu_no)
    if tur is None:
        raise BulunamadiHatasi("SayacTuru", kaynak_id=sayac_turu_no)

    mevcut = await db.execute(
        select(SayacFaturasi).where(
            SayacFaturasi.site_no == site_no,
            SayacFaturasi.sayac_turu_no == sayac_turu_no,
            SayacFaturasi.donem_yil == donem_yil,
            SayacFaturasi.donem_ay == donem_ay,
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliIhlaliHatasi(
            f"{donem_yil}/{donem_ay} donemi icin bu turde fatura zaten var."
        )

    if ortak_alan_tutar < 0 or ortak_alan_tutar > toplam_tutar:
        raise IsKuraliHatasi("Ortak alan tutari 0 ile toplam tutar arasinda olmali.")

    dagitilabilir = toplam_tutar - ortak_alan_tutar

    # 2) Sitedeki tüm aktif daireleri al
    d_sonuc = await db.execute(
        select(Daire).where(Daire.site_no == site_no).order_by(Daire.daire_no)
    )
    daireler = list(d_sonuc.scalars().all())
    if not daireler:
        raise IsKuraliHatasi("Sitede daire bulunamadi.")

    # 3) Her daire için ağırlık hesapla
    paylar: list[tuple[int, Decimal, Decimal]] = []  # (daire_no, tuketim, tutar)

    if dagitim_sekli == "TUKETIME_GORE":
        # O dönem her dairenin tüketimini bul
        # (Sayaç okumaları üzerinden: okuma_tarihi o döneme denk gelen)
        # Basit yaklaşım: son okuma - önceki okuma
        daire_tuketim: dict[int, Decimal] = {}
        for d in daireler:
            # Bu daireye ait bu türdeki sayaç
            s_sonuc = await db.execute(
                select(DaireSayaci.daire_sayac_no)
                .where(
                    DaireSayaci.daire_no == d.daire_no,
                    DaireSayaci.sayac_turu_no == sayac_turu_no,
                )
            )
            sayac_nolar = [r[0] for r in s_sonuc.all()]
            if not sayac_nolar:
                daire_tuketim[d.daire_no] = Decimal("0.00")
                continue

            # O dönem içindeki toplam tüketim = sum(tuketim) where ay=yil
            t_sonuc = await db.execute(
                select(func.coalesce(func.sum(SayacOkuma.tuketim), 0))
                .where(
                    SayacOkuma.daire_sayac_no.in_(sayac_nolar),
                    func.year(SayacOkuma.okuma_tarihi) == donem_yil,
                    func.month(SayacOkuma.okuma_tarihi) == donem_ay,
                )
            )
            daire_tuketim[d.daire_no] = Decimal(str(t_sonuc.scalar() or 0))

        toplam_tuketim = sum(daire_tuketim.values(), Decimal("0.00"))
        if toplam_tuketim <= 0:
            # Tüketim yoksa eşit dağıt
            esit = _yuvarla(dagitilabilir / Decimal(len(daireler)))
            for d in daireler:
                paylar.append((d.daire_no, Decimal("0.00"), esit))
        else:
            for d in daireler:
                t = daire_tuketim[d.daire_no]
                oran = t / toplam_tuketim
                tutar = _yuvarla(dagitilabilir * oran)
                paylar.append((d.daire_no, t, tutar))

    elif dagitim_sekli == "ESIT":
        esit = _yuvarla(dagitilabilir / Decimal(len(daireler)))
        for d in daireler:
            paylar.append((d.daire_no, Decimal("0.00"), esit))

    elif dagitim_sekli == "METREKARE":
        toplam_m2 = sum(
            (d.brut_metrekare or Decimal("0.00")) for d in daireler
        )
        if toplam_m2 <= 0:
            esit = _yuvarla(dagitilabilir / Decimal(len(daireler)))
            for d in daireler:
                paylar.append((d.daire_no, Decimal("0.00"), esit))
        else:
            for d in daireler:
                m2 = d.brut_metrekare or Decimal("0.00")
                oran = m2 / toplam_m2
                tutar = _yuvarla(dagitilabilir * oran)
                paylar.append((d.daire_no, Decimal("0.00"), tutar))
    else:
        raise IsKuraliHatasi(f"Bilinmeyen dagitim sekli: {dagitim_sekli}")

    # Yuvarlama farkını son daireye ekle (toplam tam tutsun)
    hesaplanan = sum((p[2] for p in paylar), Decimal("0.00"))
    fark = dagitilabilir - hesaplanan
    if fark != 0 and paylar:
        d_no, t, tutar = paylar[-1]
        paylar[-1] = (d_no, t, tutar + fark)

    # 4) Fatura + paylar
    fatura = SayacFaturasi(
        site_no=site_no,
        sayac_turu_no=sayac_turu_no,
        donem_yil=donem_yil,
        donem_ay=donem_ay,
        toplam_tutar=toplam_tutar,
        ortak_alan_tutar=ortak_alan_tutar,
        dagitim_sekli=dagitim_sekli,
        olusturma_tarihi=now_utc_naive(),
    )
    db.add(fatura)
    await db.flush()

    for daire_no, tuketim, tutar in paylar:
        db.add(SayacFaturaPayi(
            fatura_no=fatura.fatura_no,
            daire_no=daire_no,
            tuketim=tuketim,
            daire_tutari=tutar,
        ))

    await db.commit()
    await db.refresh(fatura)

    logger.info(
        "Yeni fatura: no=%s site=%s tur=%s donem=%s/%s toplam=%s dagitim=%s",
        fatura.fatura_no, site_no, tur.adi, donem_yil, donem_ay,
        toplam_tutar, dagitim_sekli,
    )
    return fatura


async def delete_fatura(
    db: AsyncSession,
    fatura_no: int,
    site_no: int,
) -> None:
    """Faturayı ve paylarını siler."""
    sonuc = await db.execute(
        select(SayacFaturasi).where(
            SayacFaturasi.fatura_no == fatura_no,
            SayacFaturasi.site_no == site_no,
        )
    )
    fatura = sonuc.scalar_one_or_none()
    if fatura is None:
        raise BulunamadiHatasi("SayacFaturasi", kaynak_id=fatura_no)

    await db.delete(fatura)
    await db.commit()
    logger.info("Fatura silindi: no=%s", fatura_no)


# ============================================================
# ÖZET
# ============================================================
async def get_ozet(db: AsyncSession, site_no: int) -> dict:
    """Site geneli sayaç özeti."""
    # Aktif sayaç sayısı
    s_sonuc = await db.execute(
        select(func.count(DaireSayaci.daire_sayac_no))
        .join(Daire, Daire.daire_no == DaireSayaci.daire_no)
        .where(Daire.site_no == site_no, DaireSayaci.aktif_mi.is_(True))
    )
    aktif_sayac = int(s_sonuc.scalar() or 0)

    # Toplam okuma sayısı
    o_sonuc = await db.execute(
        select(func.count(SayacOkuma.okuma_no))
        .join(DaireSayaci, DaireSayaci.daire_sayac_no == SayacOkuma.daire_sayac_no)
        .join(Daire, Daire.daire_no == DaireSayaci.daire_no)
        .where(Daire.site_no == site_no)
    )
    toplam_okuma = int(o_sonuc.scalar() or 0)

    # Toplam fatura sayısı + tutar
    f_sonuc = await db.execute(
        select(
            func.count(SayacFaturasi.fatura_no),
            func.coalesce(func.sum(SayacFaturasi.toplam_tutar), 0),
        ).where(SayacFaturasi.site_no == site_no)
    )
    f_row = f_sonuc.first()
    toplam_fatura = int(f_row[0] or 0)
    toplam_fatura_tutar = Decimal(str(f_row[1] or 0))

    # Tür bazlı tüketim
    t_sonuc = await db.execute(
        select(
            SayacTuru.sayac_turu_no,
            SayacTuru.adi,
            SayacBirim.ad,
            func.coalesce(func.sum(SayacOkuma.tuketim), 0),
            func.count(SayacOkuma.okuma_no),
        )
        .join(SayacBirim, SayacBirim.birim_no == SayacTuru.birim_no)
        .join(DaireSayaci, DaireSayaci.sayac_turu_no == SayacTuru.sayac_turu_no)
        .join(Daire, Daire.daire_no == DaireSayaci.daire_no)
        .outerjoin(SayacOkuma, SayacOkuma.daire_sayac_no == DaireSayaci.daire_sayac_no)
        .where(Daire.site_no == site_no)
        .group_by(SayacTuru.sayac_turu_no, SayacTuru.adi, SayacBirim.ad)
    )
    tuketim_ozetleri = [
        {
            "sayac_turu_no": r[0],
            "sayac_turu": r[1],
            "birim": r[2],
            "toplam_tuketim": Decimal(str(r[3] or 0)),
            "okuma_sayisi": int(r[4] or 0),
        }
        for r in t_sonuc.all()
    ]

    return {
        "site_no": site_no,
        "aktif_sayac_sayisi": aktif_sayac,
        "toplam_okuma_sayisi": toplam_okuma,
        "toplam_fatura_sayisi": toplam_fatura,
        "toplam_fatura_tutar": toplam_fatura_tutar,
        "tuketim_ozetleri": tuketim_ozetleri,
    }


# Yerel alias — IsKuraliIhlaliHatasi yerine IsKuraliHatasi kullan
IsKuraliIhlaliHatasi = IsKuraliHatasi