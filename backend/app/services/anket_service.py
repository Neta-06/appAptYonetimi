"""Anket ve oylama iş mantığı."""

import logging
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.utils import now_utc_naive
from app.models import (
    Anket,
    AnketOyu,
    AnketOyHakki,
    AnketSecenegi,
    Daire,
    DaireSakin,
    Kullanici,
    KullaniciSite,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI
# ============================================================
def _anket_aktif_mi(anket: Anket) -> bool:
    """Şu an oy kullanılabilir mi?"""
    if not anket.aktif_mi:
        return False
    simdi = now_utc_naive()
    return anket.baslangic_tarihi <= simdi <= anket.bitis_tarihi


async def _site_sakin_kullanici_nolar(db: AsyncSession, site_no: int) -> list[int]:
    """Sitede aktif sakin olan kullanıcı ID'leri."""
    sonuc = await db.execute(
        select(DaireSakin.kullanici_no)
        .distinct()
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            Daire.site_no == site_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    return [row[0] for row in sonuc.all()]


# ============================================================
# LİSTELEME
# ============================================================
async def list_anketler(
    db: AsyncSession,
    site_no: int,
    kullanici_no: int,
    *,
    aktif_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Site anketlerini listeler."""
    stmt = select(Anket).where(Anket.site_no == site_no)

    if aktif_only:
        simdi = now_utc_naive()
        stmt = stmt.where(
            Anket.aktif_mi.is_(True),
            Anket.baslangic_tarihi <= simdi,
            Anket.bitis_tarihi >= simdi,
        )

    stmt = stmt.order_by(Anket.bitis_tarihi.desc()).limit(limit).offset(offset)
    sonuc = await db.execute(stmt)
    anketler = list(sonuc.scalars().all())
    if not anketler:
        return []

    anket_nolar = [a.anket_no for a in anketler]

    # Toplam oy sayıları
    oy_sonuc = await db.execute(
        select(AnketOyu.secenek_no, func.count(AnketOyu.oy_no))
        .join(AnketSecenegi, AnketSecenegi.secenek_no == AnketOyu.secenek_no)
        .where(AnketSecenegi.anket_no.in_(anket_nolar))
        .group_by(AnketOyu.secenek_no)
    )
    # secenek_no -> anket_no eşlemesi
    s_sonuc = await db.execute(
        select(AnketSecenegi.secenek_no, AnketSecenegi.anket_no)
        .where(AnketSecenegi.anket_no.in_(anket_nolar))
    )
    secenek_anket = dict(s_sonuc.all())

    oy_sayilari: dict[int, int] = {}
    for secenek_no, adet in oy_sonuc.all():
        a_no = secenek_anket.get(secenek_no)
        if a_no:
            oy_sayilari[a_no] = oy_sayilari.get(a_no, 0) + adet

    # Oy hakları (toplam)
    hak_sonuc = await db.execute(
        select(AnketOyHakki.anket_no, func.count(AnketOyHakki.hak_no))
        .where(AnketOyHakki.anket_no.in_(anket_nolar))
        .group_by(AnketOyHakki.anket_no)
    )
    hak_sayilari = dict(hak_sonuc.all())

    # Kullanıcının oy kullanıp kullanmadığı
    k_oy_sonuc = await db.execute(
        select(AnketSecenegi.anket_no)
        .join(AnketOyu, AnketOyu.secenek_no == AnketSecenegi.secenek_no)
        .where(
            AnketSecenegi.anket_no.in_(anket_nolar),
            AnketOyu.kullanici_no == kullanici_no,
        )
    )
    kullanilan = {row[0] for row in k_oy_sonuc.all()}

    kayitlar = []
    for a in anketler:
        toplam_oy = oy_sayilari.get(a.anket_no, 0)
        toplam_hak = hak_sayilari.get(a.anket_no, 0)
        katilim = (toplam_oy / toplam_hak * 100) if toplam_hak > 0 else 0.0

        kayitlar.append({
            "anket_no": a.anket_no,
            "site_no": a.site_no,
            "soru": a.soru,
            "baslangic_tarihi": a.baslangic_tarihi,
            "bitis_tarihi": a.bitis_tarihi,
            "olusturan_no": a.olusturan_no,
            "aktif_mi": a.aktif_mi,
            "su_an_aktif_mi": _anket_aktif_mi(a),
            "toplam_oy": toplam_oy,
            "toplam_oy_hakki": toplam_hak,
            "oy_kullandi_mi": a.anket_no in kullanilan,
            "katilim_orani": round(katilim, 2),
        })
    return kayitlar


# ============================================================
# DETAY
# ============================================================
async def get_anket(
    db: AsyncSession,
    anket_no: int,
    site_no: int,
    kullanici_no: int,
) -> dict:
    """Anket detayı + seçenekler + oy bilgisi."""
    sonuc = await db.execute(
        select(Anket).where(
            Anket.anket_no == anket_no,
            Anket.site_no == site_no,
        )
    )
    anket = sonuc.scalar_one_or_none()
    if anket is None:
        raise BulunamadiHatasi("Anket", kaynak_id=anket_no)

    # Seçenekler
    s_sonuc = await db.execute(
        select(AnketSecenegi)
        .where(AnketSecenegi.anket_no == anket_no)
        .order_by(AnketSecenegi.secenek_no)
    )
    secenekler = [
        {"secenek_no": s.secenek_no, "secenek_metni": s.secenek_metni}
        for s in s_sonuc.scalars().all()
    ]

    # Toplam oy + oy hakkı
    oy_sonuc = await db.execute(
        select(func.count(AnketOyu.oy_no))
        .join(AnketSecenegi, AnketSecenegi.secenek_no == AnketOyu.secenek_no)
        .where(AnketSecenegi.anket_no == anket_no)
    )
    toplam_oy = int(oy_sonuc.scalar() or 0)

    hak_sonuc = await db.execute(
        select(func.count(AnketOyHakki.hak_no)).where(
            AnketOyHakki.anket_no == anket_no
        )
    )
    toplam_hak = int(hak_sonuc.scalar() or 0)
    katilim = (toplam_oy / toplam_hak * 100) if toplam_hak > 0 else 0.0

    # Kullanıcı oy kullandı mı?
    k_sonuc = await db.execute(
        select(AnketOyu.oy_no)
        .join(AnketSecenegi, AnketSecenegi.secenek_no == AnketOyu.secenek_no)
        .where(
            AnketSecenegi.anket_no == anket_no,
            AnketOyu.kullanici_no == kullanici_no,
        )
    )
    oy_kullandi = k_sonuc.scalar_one_or_none() is not None

    return {
        "anket_no": anket.anket_no,
        "site_no": anket.site_no,
        "soru": anket.soru,
        "aciklama": anket.aciklama,
        "baslangic_tarihi": anket.baslangic_tarihi,
        "bitis_tarihi": anket.bitis_tarihi,
        "olusturan_no": anket.olusturan_no,
        "aktif_mi": anket.aktif_mi,
        "su_an_aktif_mi": _anket_aktif_mi(anket),
        "toplam_oy": toplam_oy,
        "toplam_oy_hakki": toplam_hak,
        "oy_kullandi_mi": oy_kullandi,
        "katilim_orani": round(katilim, 2),
        "secenekler": secenekler,
    }


# ============================================================
# OLUŞTURMA
# ============================================================
async def create_anket(
    db: AsyncSession,
    site_no: int,
    *,
    soru: str,
    baslangic_tarihi: datetime,
    bitis_tarihi: datetime,
    secenekler: list[str],
    olusturan_no: int,
    aciklama: str | None = None,
    oy_hakki_kullanicilar: list[int] | None = None,
) -> Anket:
    """
    Yeni anket oluşturur.

    Adımlar:
      1. Tarih ve seçenek doğrulamaları
      2. Anket kaydı
      3. Seçenekler
      4. Oy hakları (boş bırakılırsa tüm site sakinleri)
      5. Commit
    """
    if bitis_tarihi <= baslangic_tarihi:
        raise IsKuraliHatasi("Bitis tarihi baslangic tarihinden sonra olmalidir.")
    if len(secenekler) < 2:
        raise IsKuraliHatasi("En az 2 secenek gerekli.")
    if len(set(secenekler)) != len(secenekler):
        raise IsKuraliHatasi("Secenekler benzersiz olmalidir.")

    # 1) Anket
    anket = Anket(
        site_no=site_no,
        soru=soru,
        aciklama=aciklama,
        baslangic_tarihi=baslangic_tarihi,
        bitis_tarihi=bitis_tarihi,
        olusturan_no=olusturan_no,
        aktif_mi=True,
    )
    db.add(anket)
    await db.flush()

    # 2) Seçenekler
    for metin in secenekler:
        db.add(AnketSecenegi(anket_no=anket.anket_no, secenek_metni=metin))

    # 3) Oy hakları
    if oy_hakki_kullanicilar:
        # Belirtilenler
        hedef_kullanicilar = list(set(oy_hakki_kullanicilar))
    else:
        # Otomatik: sitedeki tüm aktif sakinler
        hedef_kullanicilar = await _site_sakin_kullanici_nolar(db, site_no)

    for k_no in hedef_kullanicilar:
        db.add(AnketOyHakki(
            anket_no=anket.anket_no,
            kullanici_no=k_no,
            oy_kullandi_mi=False,
        ))

    await db.commit()
    await db.refresh(anket)
    logger.info(
        "Yeni anket: no=%s site=%s secenek=%d hak=%d",
        anket.anket_no, site_no, len(secenekler), len(hedef_kullanicilar),
    )
    return anket


# ============================================================
# GÜNCELLE / SİL
# ============================================================
async def update_anket(
    db: AsyncSession,
    anket_no: int,
    site_no: int,
    *,
    soru: str | None = None,
    aciklama: str | None = None,
    baslangic_tarihi: datetime | None = None,
    bitis_tarihi: datetime | None = None,
    aktif_mi: bool | None = None,
) -> Anket:
    """Anketi günceller."""
    sonuc = await db.execute(
        select(Anket).where(
            Anket.anket_no == anket_no,
            Anket.site_no == site_no,
        )
    )
    anket = sonuc.scalar_one_or_none()
    if anket is None:
        raise BulunamadiHatasi("Anket", kaynak_id=anket_no)

    if soru is not None:
        anket.soru = soru
    if aciklama is not None:
        anket.aciklama = aciklama
    if baslangic_tarihi is not None:
        anket.baslangic_tarihi = baslangic_tarihi
    if bitis_tarihi is not None:
        anket.bitis_tarihi = bitis_tarihi
    if aktif_mi is not None:
        anket.aktif_mi = aktif_mi

    if anket.bitis_tarihi <= anket.baslangic_tarihi:
        raise IsKuraliHatasi("Bitis tarihi baslangic tarihinden sonra olmalidir.")

    await db.commit()
    await db.refresh(anket)
    return anket


async def delete_anket(db: AsyncSession, anket_no: int, site_no: int) -> None:
    """Anketi ve tüm ilişkili kayıtları siler (cascade)."""
    sonuc = await db.execute(
        select(Anket).where(
            Anket.anket_no == anket_no,
            Anket.site_no == site_no,
        )
    )
    anket = sonuc.scalar_one_or_none()
    if anket is None:
        raise BulunamadiHatasi("Anket", kaynak_id=anket_no)

    await db.delete(anket)
    await db.commit()
    logger.info("Anket silindi: no=%s", anket_no)


# ============================================================
# OY KULLAN
# ============================================================
async def oy_kullan(
    db: AsyncSession,
    anket_no: int,
    site_no: int,
    kullanici_no: int,
    *,
    secenek_no: int,
) -> dict:
    """
    Oy kullanır.

    Kontroller:
      1. Anket var mı, site doğru mu?
      2. Anket aktif mi (tarih aralığı + aktif_mi)?
      3. Seçenek bu ankete mi ait?
      4. Kullanıcının oy hakkı var mı?
      5. Daha önce oy kullandı mı? (idempotency)
    """
    # 1) Anket
    sonuc = await db.execute(
        select(Anket).where(
            Anket.anket_no == anket_no,
            Anket.site_no == site_no,
        )
    )
    anket = sonuc.scalar_one_or_none()
    if anket is None:
        raise BulunamadiHatasi("Anket", kaynak_id=anket_no)

    # 2) Aktif mi?
    if not _anket_aktif_mi(anket):
        raise IsKuraliHatasi("Bu anket su an oy kullanmaya acik degil.")

    # 3) Seçenek kontrolü
    s_sonuc = await db.execute(
        select(AnketSecenegi).where(
            AnketSecenegi.secenek_no == secenek_no,
            AnketSecenegi.anket_no == anket_no,
        )
    )
    secenek = s_sonuc.scalar_one_or_none()
    if secenek is None:
        raise BulunamadiHatasi("AnketSecenegi", kaynak_id=secenek_no)

    # 4) Oy hakkı var mı?
    hak_sonuc = await db.execute(
        select(AnketOyHakki).where(
            AnketOyHakki.anket_no == anket_no,
            AnketOyHakki.kullanici_no == kullanici_no,
        )
    )
    hak = hak_sonuc.scalar_one_or_none()
    if hak is None:
        raise IsKuraliHatasi("Bu ankette oy kullanma hakkiniz yok.")

    # 5) Zaten oy kullandı mı?
    if hak.oy_kullandi_mi:
        raise IsKuraliHatasi("Bu ankette zaten oy kullandiniz.")

    # Oy kaydet
    oy = AnketOyu(
        secenek_no=secenek_no,
        kullanici_no=kullanici_no,
        oy_tarihi=now_utc_naive(),
    )
    db.add(oy)

    hak.oy_kullandi_mi = True
    await db.flush()
    await db.commit()
    await db.refresh(oy)

    logger.info(
        "Oy kullanildi: anket=%s kullanici=%s secenek=%s",
        anket_no, kullanici_no, secenek_no,
    )

    return {
        "oy_no": oy.oy_no,
        "anket_no": anket_no,
        "secenek_no": secenek_no,
        "secenek_metni": secenek.secenek_metni,
        "oy_tarihi": oy.oy_tarihi,
        "mesaj": f"Oyunuz kaydedildi: {secenek.secenek_metni}",
    }


# ============================================================
# SONUÇLAR
# ============================================================
async def get_sonuclar(
    db: AsyncSession,
    anket_no: int,
    site_no: int,
) -> dict:
    """Anket sonuçları — seçenek bazlı oy sayısı ve yüzde."""
    sonuc = await db.execute(
        select(Anket).where(
            Anket.anket_no == anket_no,
            Anket.site_no == site_no,
        )
    )
    anket = sonuc.scalar_one_or_none()
    if anket is None:
        raise BulunamadiHatasi("Anket", kaynak_id=anket_no)

    # Seçenek bazlı oy sayıları
    s_sonuc = await db.execute(
        select(
            AnketSecenegi.secenek_no,
            AnketSecenegi.secenek_metni,
            func.count(AnketOyu.oy_no).label("oy_sayisi"),
        )
        .outerjoin(AnketOyu, AnketOyu.secenek_no == AnketSecenegi.secenek_no)
        .where(AnketSecenegi.anket_no == anket_no)
        .group_by(AnketSecenegi.secenek_no, AnketSecenegi.secenek_metni)
        .order_by(AnketSecenegi.secenek_no)
    )
    satirlar = list(s_sonuc.all())
    toplam_oy = sum(r[2] for r in satirlar)

    secenekler = []
    for s_no, s_metin, adet in satirlar:
        yuzde = (adet / toplam_oy * 100) if toplam_oy > 0 else 0.0
        secenekler.append({
            "secenek_no": s_no,
            "secenek_metni": s_metin,
            "oy_sayisi": adet,
            "yuzde": round(yuzde, 2),
        })

    # Oy hakkı
    hak_sonuc = await db.execute(
        select(func.count(AnketOyHakki.hak_no)).where(
            AnketOyHakki.anket_no == anket_no
        )
    )
    toplam_hak = int(hak_sonuc.scalar() or 0)
    katilim = (toplam_oy / toplam_hak * 100) if toplam_hak > 0 else 0.0

    return {
        "anket_no": anket.anket_no,
        "soru": anket.soru,
        "toplam_oy": toplam_oy,
        "toplam_oy_hakki": toplam_hak,
        "katilim_orani": round(katilim, 2),
        "su_an_aktif_mi": _anket_aktif_mi(anket),
        "secenekler": secenekler,
    }