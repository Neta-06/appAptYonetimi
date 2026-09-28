"""Duyuru iş mantığı."""

import logging
from datetime import date, datetime

from sqlalchemy import delete as sa_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.utils import now_utc_naive
from app.models import (
    Duyuru,
    DuyuruOkuma,
    Kullanici,
    KullaniciSite,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI: Duyuru aktif mi?
# ============================================================
def _aktif_mi(duyuru: Duyuru) -> bool:
    if duyuru.bitis_tarihi is None:
        return True
    return duyuru.bitis_tarihi >= date.today()


# ============================================================
# LİSTELEME
# ============================================================
async def list_duyurular(
    db: AsyncSession,
    site_no: int,
    kullanici_no: int,
    *,
    aktif_only: bool = True,
    onem_derecesi: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """
    Site duyurularını listeler.
    Her duyuru için "okundu_mu" bilgisi eklenir.
    """
    # 1) Duyuruları çek
    stmt = select(Duyuru).where(Duyuru.site_no == site_no)

    if aktif_only:
        stmt = stmt.where(
            (Duyuru.bitis_tarihi.is_(None)) | (Duyuru.bitis_tarihi >= date.today())
        )
    if onem_derecesi is not None:
        stmt = stmt.where(Duyuru.onem_derecesi == onem_derecesi)

    stmt = stmt.order_by(
        Duyuru.yayin_tarihi.desc(),
        Duyuru.duyuru_no.desc(),
    ).limit(limit).offset(offset)

    sonuc = await db.execute(stmt)
    duyurular = list(sonuc.scalars().all())
    if not duyurular:
        return []

    # 2) Bu kullanıcının okuduğu duyuruların ID seti
    duyuru_nolar = [d.duyuru_no for d in duyurular]
    okuma_sonuc = await db.execute(
        select(DuyuruOkuma.duyuru_no).where(
            DuyuruOkuma.kullanici_no == kullanici_no,
            DuyuruOkuma.duyuru_no.in_(duyuru_nolar),
        )
    )
    okunan_set = {row[0] for row in okuma_sonuc.all()}

    # 3) Birleştir
    return [
        {
            "duyuru_no": d.duyuru_no,
            "baslik": d.baslik,
            "onem_derecesi": d.onem_derecesi,
            "yayin_tarihi": d.yayin_tarihi,
            "bitis_tarihi": d.bitis_tarihi,
            "yayinlayan_no": d.yayinlayan_no,
            "okundu_mu": d.duyuru_no in okunan_set,
            "aktif_mi": _aktif_mi(d),
        }
        for d in duyurular
    ]


async def get_duyuru(
    db: AsyncSession,
    duyuru_no: int,
    site_no: int,
    kullanici_no: int,
) -> dict:
    """
    Tek duyuru detayı + okuma bilgisi.
    Otomatik okundu işaretleme YAPMAZ — bunun için mark_okundu ayrı çağrılır.
    """
    sonuc = await db.execute(
        select(Duyuru).where(Duyuru.duyuru_no == duyuru_no, Duyuru.site_no == site_no)
    )
    duyuru = sonuc.scalar_one_or_none()
    if duyuru is None:
        raise BulunamadiHatasi("Duyuru", kaynak_id=duyuru_no)

    # Okuma kontrolü
    okuma_sonuc = await db.execute(
        select(DuyuruOkuma).where(
            DuyuruOkuma.duyuru_no == duyuru_no,
            DuyuruOkuma.kullanici_no == kullanici_no,
        )
    )
    okuma = okuma_sonuc.scalar_one_or_none()

    # Toplam okuma sayısı
    toplam_sonuc = await db.execute(
        select(func.count(DuyuruOkuma.okuma_no)).where(
            DuyuruOkuma.duyuru_no == duyuru_no
        )
    )
    toplam_okuma = int(toplam_sonuc.scalar() or 0)

    return {
        "duyuru_no": duyuru.duyuru_no,
        "site_no": duyuru.site_no,
        "baslik": duyuru.baslik,
        "icerik": duyuru.icerik,
        "onem_derecesi": duyuru.onem_derecesi,
        "yayin_tarihi": duyuru.yayin_tarihi,
        "bitis_tarihi": duyuru.bitis_tarihi,
        "yayinlayan_no": duyuru.yayinlayan_no,
        "okundu_mu": okuma is not None,
        "okuma_tarihi": okuma.okuma_tarihi if okuma else None,
        "toplam_okuma": toplam_okuma,
    }


# ============================================================
# CRUD
# ============================================================
async def create_duyuru(
    db: AsyncSession,
    site_no: int,
    *,
    baslik: str,
    icerik: str,
    yayinlayan_no: int,
    onem_derecesi: str = "NORMAL",
    bitis_tarihi: date | None = None,
) -> Duyuru:
    """Yeni duyuru oluşturur."""
    # Bitiş tarihi geçmişte olamaz
    if bitis_tarihi is not None and bitis_tarihi < date.today():
        raise IsKuraliHatasi("Bitis tarihi gecmis bir tarih olamaz.")

    duyuru = Duyuru(
        site_no=site_no,
        baslik=baslik,
        icerik=icerik,
        onem_derecesi=onem_derecesi,
        yayin_tarihi=now_utc_naive(),
        bitis_tarihi=bitis_tarihi,
        yayinlayan_no=yayinlayan_no,
    )
    db.add(duyuru)
    await db.commit()
    await db.refresh(duyuru)

    logger.info(
        "Yeni duyuru: no=%s site=%s baslik=%s",
        duyuru.duyuru_no, site_no, baslik[:50],
    )
    return duyuru


async def update_duyuru(
    db: AsyncSession,
    duyuru_no: int,
    site_no: int,
    *,
    baslik: str | None = None,
    icerik: str | None = None,
    onem_derecesi: str | None = None,
    bitis_tarihi: date | None = None,
) -> Duyuru:
    """Duyuruyu günceller."""
    sonuc = await db.execute(
        select(Duyuru).where(Duyuru.duyuru_no == duyuru_no, Duyuru.site_no == site_no)
    )
    duyuru = sonuc.scalar_one_or_none()
    if duyuru is None:
        raise BulunamadiHatasi("Duyuru", kaynak_id=duyuru_no)

    if baslik is not None:
        duyuru.baslik = baslik
    if icerik is not None:
        duyuru.icerik = icerik
    if onem_derecesi is not None:
        duyuru.onem_derecesi = onem_derecesi
    if bitis_tarihi is not None:
        if bitis_tarihi < date.today():
            raise IsKuraliHatasi("Bitis tarihi gecmis bir tarih olamaz.")
        duyuru.bitis_tarihi = bitis_tarihi

    await db.commit()
    await db.refresh(duyuru)
    logger.info("Duyuru guncellendi: no=%s", duyuru_no)
    return duyuru


async def delete_duyuru(db: AsyncSession, duyuru_no: int, site_no: int) -> None:
    """Duyuruyu ve tüm okuma kayıtlarını siler."""
    sonuc = await db.execute(
        select(Duyuru).where(Duyuru.duyuru_no == duyuru_no, Duyuru.site_no == site_no)
    )
    duyuru = sonuc.scalar_one_or_none()
    if duyuru is None:
        raise BulunamadiHatasi("Duyuru", kaynak_id=duyuru_no)

    # Okumaları da sil (cascade zaten var ama explicit)
    await db.execute(
        sa_delete(DuyuruOkuma).where(DuyuruOkuma.duyuru_no == duyuru_no)
    )
    await db.delete(duyuru)
    await db.commit()
    logger.info("Duyuru silindi: no=%s", duyuru_no)


# ============================================================
# OKUMA TAKİBİ
# ============================================================
async def mark_okundu(
    db: AsyncSession,
    duyuru_no: int,
    site_no: int,
    kullanici_no: int,
) -> dict:
    """
    Duyuruyu okundu olarak işaretler.
    Zaten okunmuşsa tekrar kayıt oluşturmaz (idempotent).
    """
    # Duyuru var mı?
    sonuc = await db.execute(
        select(Duyuru).where(Duyuru.duyuru_no == duyuru_no, Duyuru.site_no == site_no)
    )
    duyuru = sonuc.scalar_one_or_none()
    if duyuru is None:
        raise BulunamadiHatasi("Duyuru", kaynak_id=duyuru_no)

    # Zaten okundu mu?
    mevcut_sonuc = await db.execute(
        select(DuyuruOkuma).where(
            DuyuruOkuma.duyuru_no == duyuru_no,
            DuyuruOkuma.kullanici_no == kullanici_no,
        )
    )
    mevcut = mevcut_sonuc.scalar_one_or_none()

    if mevcut is not None:
        # Zaten okunmuş — idempotent
        return {
            "duyuru_no": duyuru_no,
            "kullanici_no": kullanici_no,
            "okuma_tarihi": mevcut.okuma_tarihi,
            "zaten_okunmus": True,
        }

    # Yeni okuma kaydı
    okuma = DuyuruOkuma(
        duyuru_no=duyuru_no,
        kullanici_no=kullanici_no,
        okuma_tarihi=now_utc_naive(),
    )
    db.add(okuma)
    await db.commit()
    await db.refresh(okuma)

    logger.info(
        "Duyuru okundu: duyuru=%s kullanici=%s",
        duyuru_no, kullanici_no,
    )
    return {
        "duyuru_no": duyuru_no,
        "kullanici_no": kullanici_no,
        "okuma_tarihi": okuma.okuma_tarihi,
        "zaten_okunmus": False,
    }


async def get_okuma_durumu(
    db: AsyncSession,
    duyuru_no: int,
    site_no: int,
) -> dict:
    """
    Bir duyurunun okuma durumu.
    Siteye üye tüm kullanıcılar hedef alıcı kabul edilir.
    """
    # Duyuru kontrolü
    sonuc = await db.execute(
        select(Duyuru).where(Duyuru.duyuru_no == duyuru_no, Duyuru.site_no == site_no)
    )
    duyuru = sonuc.scalar_one_or_none()
    if duyuru is None:
        raise BulunamadiHatasi("Duyuru", kaynak_id=duyuru_no)

    # Siteye üye toplam kullanıcı sayısı
    toplam_sonuc = await db.execute(
        select(func.count(KullaniciSite.kayit_no)).where(
            KullaniciSite.site_no == site_no,
            KullaniciSite.aktif_mi.is_(True),
        )
    )
    toplam_alici = int(toplam_sonuc.scalar() or 0)

    # Okuma kayıtları (kullanıcı bilgisiyle)
    okuma_sonuc = await db.execute(
        select(DuyuruOkuma, Kullanici)
        .join(Kullanici, Kullanici.kullanici_no == DuyuruOkuma.kullanici_no)
        .where(DuyuruOkuma.duyuru_no == duyuru_no)
        .order_by(DuyuruOkuma.okuma_tarihi.desc())
    )

    okumalar = []
    for o, k in okuma_sonuc.all():
        okumalar.append({
            "okuma_no": o.okuma_no,
            "kullanici_no": k.kullanici_no,
            "ad": k.ad,
            "soyad": k.soyad,
            "e_posta": k.e_posta,
            "okuma_tarihi": o.okuma_tarihi,
        })

    okuyan = len(okumalar)
    okumayan = max(0, toplam_alici - okuyan)
    oran = (okuyan / toplam_alici * 100) if toplam_alici > 0 else 0.0

    return {
        "duyuru_no": duyuru.duyuru_no,
        "baslik": duyuru.baslik,
        "toplam_alici": toplam_alici,
        "okuyan_sayisi": okuyan,
        "okumayan_sayisi": okumayan,
        "okuma_orani": round(oran, 2),
        "okumalar": okumalar,
    }