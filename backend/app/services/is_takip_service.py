"""İş emri ve takip iş mantığı."""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.utils import now_utc_naive
from app.models import (
    Blok,
    Daire,
    IsDurum,
    IsEmri,
    IsEmriGuncelleme,
    IsEmriMalzeme,
    IsOncelik,
    Kullanici,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI: Kapanış durumları
# ============================================================
async def _kapanis_durum_nolar(db: AsyncSession) -> set[int]:
    """Kapanış durumu olan durum_no setini döner."""
    sonuc = await db.execute(
        select(IsDurum.durum_no).where(IsDurum.kapanis_mi.is_(True))
    )
    return {row[0] for row in sonuc.all()}


def _gecikti_mi(termin: datetime | None, kapanis_mi: bool) -> bool:
    if termin is None or kapanis_mi:
        return False
    return termin < now_utc_naive()


# ============================================================
# LİSTELEME
# ============================================================
async def list_is_emirleri(
    db: AsyncSession,
    site_no: int,
    *,
    durum_no: int | None = None,
    oncelik_no: int | None = None,
    atanan_no: int | None = None,
    daire_no: int | None = None,
    acik_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """İş emirlerini filtreli listeler."""
    stmt = (
        select(IsEmri, IsOncelik, IsDurum, Kullanici)
        .join(IsOncelik, IsOncelik.oncelik_no == IsEmri.oncelik_no)
        .join(IsDurum, IsDurum.durum_no == IsEmri.durum_no)
        .join(Kullanici, Kullanici.kullanici_no == IsEmri.atanan_no)
        .where(IsEmri.site_no == site_no)
    )

    if durum_no is not None:
        stmt = stmt.where(IsEmri.durum_no == durum_no)
    if oncelik_no is not None:
        stmt = stmt.where(IsEmri.oncelik_no == oncelik_no)
    if atanan_no is not None:
        stmt = stmt.where(IsEmri.atanan_no == atanan_no)
    if daire_no is not None:
        stmt = stmt.where(IsEmri.daire_no == daire_no)
    if acik_only:
        stmt = stmt.where(IsDurum.kapanis_mi.is_(False))

    stmt = stmt.order_by(
        IsOncelik.siralama.asc(),
        IsEmri.olusturma_tarihi.desc(),
    ).limit(limit).offset(offset)

    sonuc = await db.execute(stmt)
    satirlar = list(sonuc.all())

    # Daire bilgilerini topluca yükle
    daire_nolar = {s[0].daire_no for s in satirlar if s[0].daire_no}
    daire_map: dict[int, str] = {}
    if daire_nolar:
        d_sonuc = await db.execute(
            select(Daire.daire_no, Blok.blok_adi, Daire.daire_numarasi)
            .join(Blok, Blok.blok_no == Daire.blok_no)
            .where(Daire.daire_no.in_(daire_nolar))
        )
        for d_no, b_adi, d_num in d_sonuc.all():
            daire_map[d_no] = f"{b_adi} - Daire {d_num}"

    # Malzeme ve güncelleme sayıları (toplu)
    is_nolar = [s[0].is_no for s in satirlar]
    malzeme_sayilari: dict[int, int] = {}
    guncelleme_sayilari: dict[int, int] = {}
    if is_nolar:
        m_sonuc = await db.execute(
            select(IsEmriMalzeme.is_no, func.count(IsEmriMalzeme.malzeme_no))
            .where(IsEmriMalzeme.is_no.in_(is_nolar))
            .group_by(IsEmriMalzeme.is_no)
        )
        malzeme_sayilari = dict(m_sonuc.all())

        g_sonuc = await db.execute(
            select(IsEmriGuncelleme.is_no, func.count(IsEmriGuncelleme.guncelleme_no))
            .where(IsEmriGuncelleme.is_no.in_(is_nolar))
            .group_by(IsEmriGuncelleme.is_no)
        )
        guncelleme_sayilari = dict(g_sonuc.all())

    kayitlar = []
    for ie, oncelik, durum, atanan in satirlar:
        kayitlar.append({
            "is_no": ie.is_no,
            "site_no": ie.site_no,
            "daire_no": ie.daire_no,
            "daire_ozet": daire_map.get(ie.daire_no) if ie.daire_no else None,
            "acan_no": ie.acan_no,
            "acan_ad": None,  # istenirse ayrıca yüklenebilir
            "atanan_no": ie.atanan_no,
            "atanan_ad": f"{atanan.ad} {atanan.soyad}",
            "baslik": ie.baslik,
            "oncelik_no": oncelik.oncelik_no,
            "oncelik_ad": oncelik.ad,
            "oncelik_siralama": oncelik.siralama,
            "durum_no": durum.durum_no,
            "durum_ad": durum.ad,
            "kapanis_mi": durum.kapanis_mi,
            "termin_tarihi": ie.termin_tarihi,
            "olusturma_tarihi": ie.olusturma_tarihi,
            "gecikti_mi": _gecikti_mi(ie.termin_tarihi, durum.kapanis_mi),
            "malzeme_sayisi": malzeme_sayilari.get(ie.is_no, 0),
            "guncelleme_sayisi": guncelleme_sayilari.get(ie.is_no, 0),
        })
    return kayitlar


async def list_benim_islerim(
    db: AsyncSession,
    site_no: int,
    kullanici_no: int,
    *,
    acik_only: bool = True,
    limit: int = 100,
) -> list[dict]:
    """İstek yapan kullanıcıya atanan işler."""
    return await list_is_emirleri(
        db, site_no,
        atanan_no=kullanici_no,
        acik_only=acik_only,
        limit=limit,
    )


# ============================================================
# DETAY
# ============================================================
async def get_is_emri(
    db: AsyncSession,
    is_no: int,
    site_no: int,
) -> dict:
    """İş emri detayı — güncellemeler + malzemeler dahil."""
    # Ana kayıt
    sonuc = await db.execute(
        select(IsEmri, IsOncelik, IsDurum, Kullanici)
        .join(IsOncelik, IsOncelik.oncelik_no == IsEmri.oncelik_no)
        .join(IsDurum, IsDurum.durum_no == IsEmri.durum_no)
        .join(Kullanici, Kullanici.kullanici_no == IsEmri.atanan_no)
        .where(IsEmri.is_no == is_no, IsEmri.site_no == site_no)
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("IsEmri", kaynak_id=is_no)

    ie, oncelik, durum, atanan = row

    # Daire bilgisi
    daire_ozet = None
    if ie.daire_no:
        d_sonuc = await db.execute(
            select(Blok.blok_adi, Daire.daire_numarasi)
            .join(Blok, Blok.blok_no == Daire.blok_no)
            .where(Daire.daire_no == ie.daire_no)
        )
        d_row = d_sonuc.first()
        if d_row:
            daire_ozet = f"{d_row[0]} - Daire {d_row[1]}"

    # Güncellemeler
    g_sonuc = await db.execute(
        select(IsEmriGuncelleme, Kullanici, IsDurum)
        .join(Kullanici, Kullanici.kullanici_no == IsEmriGuncelleme.yazan_no)
        .join(IsDurum, IsDurum.durum_no == IsEmriGuncelleme.durum_no)
        .where(IsEmriGuncelleme.is_no == is_no)
        .order_by(IsEmriGuncelleme.guncelleme_tarihi.desc())
    )
    guncellemeler = []
    for g, yazan, g_durum in g_sonuc.all():
        guncellemeler.append({
            "guncelleme_no": g.guncelleme_no,
            "is_no": g.is_no,
            "yazan_no": g.yazan_no,
            "yazan_ad": f"{yazan.ad} {yazan.soyad}",
            "durum_no": g.durum_no,
            "durum_ad": g_durum.ad,
            "notlar": g.notlar,
            "guncelleme_tarihi": g.guncelleme_tarihi,
        })

    # Malzemeler
    m_sonuc = await db.execute(
        select(IsEmriMalzeme)
        .where(IsEmriMalzeme.is_no == is_no)
        .order_by(IsEmriMalzeme.malzeme_no)
    )
    malzemeler = []
    toplam_tutar = Decimal("0.00")
    for m in m_sonuc.scalars().all():
        ara_toplam = None
        if m.birim_fiyat is not None:
            ara_toplam = (m.adet * m.birim_fiyat).quantize(Decimal("0.01"))
            toplam_tutar += ara_toplam
        malzemeler.append({
            "malzeme_no": m.malzeme_no,
            "is_no": m.is_no,
            "ad": m.ad,
            "adet": m.adet,
            "birim": m.birim,
            "birim_fiyat": m.birim_fiyat,
            "toplam": ara_toplam,
        })

    return {
        "is_no": ie.is_no,
        "site_no": ie.site_no,
        "daire_no": ie.daire_no,
        "daire_ozet": daire_ozet,
        "acan_no": ie.acan_no,
        "acan_ad": None,
        "atanan_no": ie.atanan_no,
        "atanan_ad": f"{atanan.ad} {atanan.soyad}",
        "baslik": ie.baslik,
        "aciklama": ie.aciklama,
        "oncelik_no": oncelik.oncelik_no,
        "oncelik_ad": oncelik.ad,
        "oncelik_siralama": oncelik.siralama,
        "durum_no": durum.durum_no,
        "durum_ad": durum.ad,
        "kapanis_mi": durum.kapanis_mi,
        "termin_tarihi": ie.termin_tarihi,
        "tamamlanma_tarihi": ie.tamamlanma_tarihi,
        "olusturma_tarihi": ie.olusturma_tarihi,
        "guncellenme_tarihi": ie.guncellenme_tarihi,
        "gecikti_mi": _gecikti_mi(ie.termin_tarihi, durum.kapanis_mi),
        "malzeme_sayisi": len(malzemeler),
        "guncelleme_sayisi": len(guncellemeler),
        "guncellemeler": guncellemeler,
        "malzemeler": malzemeler,
        "toplam_malzeme_tutar": toplam_tutar,
    }


# ============================================================
# CRUD
# ============================================================
async def create_is_emri(
    db: AsyncSession,
    site_no: int,
    *,
    baslik: str,
    acan_no: int,
    atanan_no: int,
    oncelik_no: int,
    aciklama: str | None = None,
    daire_no: int | None = None,
    termin_tarihi: datetime | None = None,
) -> IsEmri:
    """Yeni iş emri oluşturur."""
    # Oncelik kontrolü
    oncelik = await db.get(IsOncelik, oncelik_no)
    if oncelik is None:
        raise BulunamadiHatasi("IsOncelik", kaynak_id=oncelik_no)

    # Atanan kişi var mı?
    atanan = await db.get(Kullanici, atanan_no)
    if atanan is None or not atanan.aktif_mi:
        raise BulunamadiHatasi("Kullanici", kaynak_id=atanan_no)

    # Daire site kontrolü
    if daire_no is not None:
        daire = await db.get(Daire, daire_no)
        if daire is None or daire.site_no != site_no:
            raise BulunamadiHatasi("Daire", kaynak_id=daire_no)

    # Varsayılan durum: ACIK
    varsayilan = await db.execute(
        select(IsDurum).where(IsDurum.ad == "ACIK")
    )
    varsayilan_durum = varsayilan.scalar_one_or_none()
    if varsayilan_durum is None:
        raise IsKuraliHatasi(
            "Sistemde 'ACIK' durum tanimli degil. Lookup tabloyu kontrol edin."
        )

    is_emri = IsEmri(
        site_no=site_no,
        daire_no=daire_no,
        acan_no=acan_no,
        atanan_no=atanan_no,
        baslik=baslik,
        aciklama=aciklama,
        oncelik_no=oncelik_no,
        durum_no=varsayilan_durum.durum_no,
        termin_tarihi=termin_tarihi,
        olusturma_tarihi=now_utc_naive(),
        guncellenme_tarihi=now_utc_naive(),
    )
    db.add(is_emri)
    await db.commit()
    await db.refresh(is_emri)

    logger.info(
        "Yeni is emri: no=%s site=%s baslik=%s",
        is_emri.is_no, site_no, baslik[:50],
    )
    return is_emri


async def update_is_emri(
    db: AsyncSession,
    is_no: int,
    site_no: int,
    *,
    baslik: str | None = None,
    aciklama: str | None = None,
    daire_no: int | None = None,
    atanan_no: int | None = None,
    oncelik_no: int | None = None,
    termin_tarihi: datetime | None = None,
) -> IsEmri:
    """İş emrini günceller."""
    sonuc = await db.execute(
        select(IsEmri).where(IsEmri.is_no == is_no, IsEmri.site_no == site_no)
    )
    is_emri = sonuc.scalar_one_or_none()
    if is_emri is None:
        raise BulunamadiHatasi("IsEmri", kaynak_id=is_no)

    if baslik is not None:
        is_emri.baslik = baslik
    if aciklama is not None:
        is_emri.aciklama = aciklama
    if daire_no is not None:
        daire = await db.get(Daire, daire_no)
        if daire is None or daire.site_no != site_no:
            raise BulunamadiHatasi("Daire", kaynak_id=daire_no)
        is_emri.daire_no = daire_no
    if atanan_no is not None:
        atanan = await db.get(Kullanici, atanan_no)
        if atanan is None or not atanan.aktif_mi:
            raise BulunamadiHatasi("Kullanici", kaynak_id=atanan_no)
        is_emri.atanan_no = atanan_no
    if oncelik_no is not None:
        oncelik = await db.get(IsOncelik, oncelik_no)
        if oncelik is None:
            raise BulunamadiHatasi("IsOncelik", kaynak_id=oncelik_no)
        is_emri.oncelik_no = oncelik_no
    if termin_tarihi is not None:
        is_emri.termin_tarihi = termin_tarihi

    is_emri.guncellenme_tarihi = now_utc_naive()
    await db.commit()
    await db.refresh(is_emri)
    logger.info("Is emri guncellendi: no=%s", is_no)
    return is_emri


async def delete_is_emri(db: AsyncSession, is_no: int, site_no: int) -> None:
    """İş emrini siler (güncellemeler + malzemeler cascade)."""
    sonuc = await db.execute(
        select(IsEmri).where(IsEmri.is_no == is_no, IsEmri.site_no == site_no)
    )
    is_emri = sonuc.scalar_one_or_none()
    if is_emri is None:
        raise BulunamadiHatasi("IsEmri", kaynak_id=is_no)

    await db.delete(is_emri)
    await db.commit()
    logger.info("Is emri silindi: no=%s", is_no)


# ============================================================
# DURUM DEĞİŞTİRME
# ============================================================
async def durum_degistir(
    db: AsyncSession,
    is_no: int,
    site_no: int,
    *,
    durum_no: int,
    degistiren_no: int,
    notlar: str | None = None,
) -> IsEmri:
    """
    İş emri durumunu değiştirir ve güncelleme kaydı oluşturur.
    Kapanış durumuna geçişte `tamamlanma_tarihi` otomatik set edilir.
    """
    sonuc = await db.execute(
        select(IsEmri).where(IsEmri.is_no == is_no, IsEmri.site_no == site_no)
    )
    is_emri = sonuc.scalar_one_or_none()
    if is_emri is None:
        raise BulunamadiHatasi("IsEmri", kaynak_id=is_no)

    yeni_durum = await db.get(IsDurum, durum_no)
    if yeni_durum is None:
        raise BulunamadiHatasi("IsDurum", kaynak_id=durum_no)

    # Aynı duruma geçişse hata
    if is_emri.durum_no == durum_no:
        raise IsKuraliHatasi(f"Is zaten '{yeni_durum.ad}' durumunda.")

    # Güncelle
    is_emri.durum_no = durum_no
    is_emri.guncellenme_tarihi = now_utc_naive()

    if yeni_durum.kapanis_mi:
        is_emri.tamamlanma_tarihi = now_utc_naive()
    else:
        # Kapanıştan açığa dönüş
        is_emri.tamamlanma_tarihi = None

    # Güncelleme kaydı
    guncelleme = IsEmriGuncelleme(
        is_no=is_no,
        yazan_no=degistiren_no,
        durum_no=durum_no,
        notlar=notlar,
        guncelleme_tarihi=now_utc_naive(),
    )
    db.add(guncelleme)

    await db.commit()
    await db.refresh(is_emri)
    logger.info(
        "Is emri durum degisti: no=%s yeni_durum=%s",
        is_no, yeni_durum.ad,
    )
    return is_emri


async def guncelleme_ekle(
    db: AsyncSession,
    is_no: int,
    site_no: int,
    *,
    yazan_no: int,
    durum_no: int,
    notlar: str,
) -> IsEmriGuncelleme:
    """İş emrine manuel güncelleme notu ekler."""
    sonuc = await db.execute(
        select(IsEmri).where(IsEmri.is_no == is_no, IsEmri.site_no == site_no)
    )
    is_emri = sonuc.scalar_one_or_none()
    if is_emri is None:
        raise BulunamadiHatasi("IsEmri", kaynak_id=is_no)

    durum = await db.get(IsDurum, durum_no)
    if durum is None:
        raise BulunamadiHatasi("IsDurum", kaynak_id=durum_no)

    guncelleme = IsEmriGuncelleme(
        is_no=is_no,
        yazan_no=yazan_no,
        durum_no=durum_no,
        notlar=notlar,
        guncelleme_tarihi=now_utc_naive(),
    )
    db.add(guncelleme)
    await db.commit()
    await db.refresh(guncelleme)
    return guncelleme


# ============================================================
# MALZEME
# ============================================================
async def malzeme_ekle(
    db: AsyncSession,
    is_no: int,
    site_no: int,
    *,
    ad: str,
    adet: Decimal = Decimal("1"),
    birim: str | None = None,
    birim_fiyat: Decimal | None = None,
) -> IsEmriMalzeme:
    """İş emrine malzeme ekler."""
    sonuc = await db.execute(
        select(IsEmri).where(IsEmri.is_no == is_no, IsEmri.site_no == site_no)
    )
    is_emri = sonuc.scalar_one_or_none()
    if is_emri is None:
        raise BulunamadiHatasi("IsEmri", kaynak_id=is_no)

    malzeme = IsEmriMalzeme(
        is_no=is_no,
        ad=ad,
        adet=adet,
        birim=birim,
        birim_fiyat=birim_fiyat,
    )
    db.add(malzeme)
    await db.commit()
    await db.refresh(malzeme)
    return malzeme


async def malzeme_sil(
    db: AsyncSession,
    is_no: int,
    malzeme_no: int,
    site_no: int,
) -> None:
    """İş emrinden malzeme siler."""
    # Önce iş emrini doğrula
    sonuc = await db.execute(
        select(IsEmri).where(IsEmri.is_no == is_no, IsEmri.site_no == site_no)
    )
    if sonuc.scalar_one_or_none() is None:
        raise BulunamadiHatasi("IsEmri", kaynak_id=is_no)

    m_sonuc = await db.execute(
        select(IsEmriMalzeme).where(
            IsEmriMalzeme.malzeme_no == malzeme_no,
            IsEmriMalzeme.is_no == is_no,
        )
    )
    malzeme = m_sonuc.scalar_one_or_none()
    if malzeme is None:
        raise BulunamadiHatasi("IsEmriMalzeme", kaynak_id=malzeme_no)

    await db.delete(malzeme)
    await db.commit()


# ============================================================
# ÖZET İSTATİSTİKLER
# ============================================================
async def get_ozet(db: AsyncSession, site_no: int) -> dict:
    """Site geneli iş emri özeti."""
    # Toplam ve durum dağılımı
    d_sonuc = await db.execute(
        select(
            IsDurum.durum_no,
            IsDurum.ad,
            IsDurum.kapanis_mi,
            func.count(IsEmri.is_no),
        )
        .join(IsEmri, IsEmri.durum_no == IsDurum.durum_no)
        .where(IsEmri.site_no == site_no)
        .group_by(IsDurum.durum_no, IsDurum.ad, IsDurum.kapanis_mi)
    )
    durum_satirlar = list(d_sonuc.all())
    toplam = sum(r[3] for r in durum_satirlar)
    kapali = sum(r[3] for r in durum_satirlar if r[2])
    acik = toplam - kapali

    durum_dagilimi = [
        {
            "durum_no": r[0],
            "durum_ad": r[1],
            "adet": r[3],
            "yuzde": round(r[3] / toplam * 100, 2) if toplam > 0 else 0.0,
        }
        for r in durum_satirlar
    ]

    # Öncelik dağılımı
    o_sonuc = await db.execute(
        select(IsOncelik.oncelik_no, IsOncelik.ad, func.count(IsEmri.is_no))
        .join(IsEmri, IsEmri.oncelik_no == IsOncelik.oncelik_no)
        .where(IsEmri.site_no == site_no)
        .group_by(IsOncelik.oncelik_no, IsOncelik.ad, IsOncelik.siralama)
        .order_by(IsOncelik.siralama)
    )
    oncelik_dagilimi = [
        {
            "oncelik_no": r[0],
            "oncelik_ad": r[1],
            "adet": r[2],
            "yuzde": round(r[2] / toplam * 100, 2) if toplam > 0 else 0.0,
        }
        for r in o_sonuc.all()
    ]

    # Gecikmiş açık işler
    simdi = now_utc_naive()
    gecikmis_sonuc = await db.execute(
        select(func.count(IsEmri.is_no))
        .join(IsDurum, IsDurum.durum_no == IsEmri.durum_no)
        .where(
            IsEmri.site_no == site_no,
            IsDurum.kapanis_mi.is_(False),
            IsEmri.termin_tarihi.is_not(None),
            IsEmri.termin_tarihi < simdi,
        )
    )
    gecikmis = int(gecikmis_sonuc.scalar() or 0)

    # Acil açık işler
    acil_sonuc = await db.execute(
        select(func.count(IsEmri.is_no))
        .join(IsDurum, IsDurum.durum_no == IsEmri.durum_no)
        .join(IsOncelik, IsOncelik.oncelik_no == IsEmri.oncelik_no)
        .where(
            IsEmri.site_no == site_no,
            IsDurum.kapanis_mi.is_(False),
            IsOncelik.ad == "ACIL",
        )
    )
    acil = int(acil_sonuc.scalar() or 0)

    # Ortalama tamamlanma süresi (gün cinsinden)
    ortalama_sonuc = await db.execute(
        select(
            func.avg(
                func.datediff(IsEmri.tamamlanma_tarihi, IsEmri.olusturma_tarihi)
            )
        )
        .where(
            IsEmri.site_no == site_no,
            IsEmri.tamamlanma_tarihi.is_not(None),
        )
    )
    ortalama = ortalama_sonuc.scalar()
    ortalama_gun = float(ortalama) if ortalama is not None else None

    return {
        "toplam": toplam,
        "acik": acik,
        "kapali": kapali,
        "gecikmis": gecikmis,
        "acil": acil,
        "ortalama_tamamlama_gun": (
            round(ortalama_gun, 1) if ortalama_gun is not None else None
        ),
        "durum_dagilimi": durum_dagilimi,
        "oncelik_dagilimi": oncelik_dagilimi,
    }


# ============================================================
# LOOKUP
# ============================================================
async def list_oncelikler(db: AsyncSession) -> list[dict]:
    sonuc = await db.execute(select(IsOncelik).order_by(IsOncelik.siralama))
    return [
        {"oncelik_no": o.oncelik_no, "ad": o.ad, "siralama": o.siralama}
        for o in sonuc.scalars().all()
    ]


async def list_durumlar(db: AsyncSession) -> list[dict]:
    sonuc = await db.execute(select(IsDurum).order_by(IsDurum.durum_no))
    return [
        {"durum_no": d.durum_no, "ad": d.ad, "kapanis_mi": d.kapanis_mi}
        for d in sonuc.scalars().all()
    ]