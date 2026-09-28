"""Toplantı iş mantığı."""

import logging
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.utils import now_utc_naive
from app.models import (
    Daire,
    DaireSakin,
    Kullanici,
    Toplanti,
    ToplantiKarar,
    ToplantiKatilimci,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI
# ============================================================
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


async def _toplanti_istatistik(
    db: AsyncSession, toplanti_no: int
) -> dict:
    """Toplantı için katılımcı/karar sayıları."""
    k_sonuc = await db.execute(
        select(
            func.count(ToplantiKatilimci.katilim_no),
            func.sum(
                case((ToplantiKatilimci.katildi_mi.is_(True), 1), else_=0)
            ),
        ).where(ToplantiKatilimci.toplanti_no == toplanti_no)
    )
    row = k_sonuc.first()
    toplam = int(row[0] or 0)
    katilan = int(row[1] or 0)

    karar_sonuc = await db.execute(
        select(func.count(ToplantiKarar.karar_no)).where(
            ToplantiKarar.toplanti_no == toplanti_no
        )
    )
    karar = int(karar_sonuc.scalar() or 0)

    oran = (katilan / toplam * 100) if toplam > 0 else 0.0

    return {
        "katilimci_sayisi": toplam,
        "katilan_sayisi": katilan,
        "karar_sayisi": karar,
        "katilim_orani": round(oran, 2),
    }


# ============================================================
# LİSTELEME
# ============================================================
async def list_toplantilar(
    db: AsyncSession,
    site_no: int,
    *,
    durum: str | None = None,
    tarih_baslangic: datetime | None = None,
    tarih_bitis: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Site toplantılarını filtreli listeler."""
    stmt = select(Toplanti).where(Toplanti.site_no == site_no)

    if durum is not None:
        stmt = stmt.where(Toplanti.durum == durum)
    if tarih_baslangic is not None:
        stmt = stmt.where(Toplanti.toplanti_tarihi >= tarih_baslangic)
    if tarih_bitis is not None:
        stmt = stmt.where(Toplanti.toplanti_tarihi <= tarih_bitis)

    stmt = stmt.order_by(Toplanti.toplanti_tarihi.desc()).limit(limit).offset(offset)
    sonuc = await db.execute(stmt)
    toplantilar = list(sonuc.scalars().all())
    if not toplantilar:
        return []

    toplanti_nolar = [t.toplanti_no for t in toplantilar]

    # Katılımcı sayıları (toplu)
    k_sonuc = await db.execute(
        select(
            ToplantiKatilimci.toplanti_no,
            func.count(ToplantiKatilimci.katilim_no),
            func.sum(
                case((ToplantiKatilimci.katildi_mi.is_(True), 1), else_=0)
            ),
        )
        .where(ToplantiKatilimci.toplanti_no.in_(toplanti_nolar))
        .group_by(ToplantiKatilimci.toplanti_no)
    )
    katilim_map = {
        row[0]: (int(row[1] or 0), int(row[2] or 0))
        for row in k_sonuc.all()
    }

    # Karar sayıları (toplu)
    ka_sonuc = await db.execute(
        select(ToplantiKarar.toplanti_no, func.count(ToplantiKarar.karar_no))
        .where(ToplantiKarar.toplanti_no.in_(toplanti_nolar))
        .group_by(ToplantiKarar.toplanti_no)
    )
    karar_map = dict(ka_sonuc.all())

    kayitlar = []
    for t in toplantilar:
        toplam, katilan = katilim_map.get(t.toplanti_no, (0, 0))
        oran = (katilan / toplam * 100) if toplam > 0 else 0.0
        kayitlar.append({
            "toplanti_no": t.toplanti_no,
            "site_no": t.site_no,
            "baslik": t.baslik,
            "toplanti_tarihi": t.toplanti_tarihi,
            "yer": t.yer,
            "olusturan_no": t.olusturan_no,
            "durum": t.durum,
            "katilimci_sayisi": toplam,
            "katilan_sayisi": katilan,
            "karar_sayisi": karar_map.get(t.toplanti_no, 0),
            "katilim_orani": round(oran, 2),
        })
    return kayitlar


# ============================================================
# DETAY
# ============================================================
async def get_toplanti(
    db: AsyncSession, toplanti_no: int, site_no: int
) -> dict:
    """Toplantı detayı + katılımcılar + kararlar."""
    sonuc = await db.execute(
        select(Toplanti).where(
            Toplanti.toplanti_no == toplanti_no,
            Toplanti.site_no == site_no,
        )
    )
    toplanti = sonuc.scalar_one_or_none()
    if toplanti is None:
        raise BulunamadiHatasi("Toplanti", kaynak_id=toplanti_no)

    # Katılımcılar (kullanıcı bilgisiyle)
    k_sonuc = await db.execute(
        select(ToplantiKatilimci, Kullanici)
        .join(Kullanici, Kullanici.kullanici_no == ToplantiKatilimci.kullanici_no)
        .where(ToplantiKatilimci.toplanti_no == toplanti_no)
        .order_by(Kullanici.ad, Kullanici.soyad)
    )
    katilimcilar = []
    for k, u in k_sonuc.all():
        # Vekalet eden kişi
        vekalet_ad = None
        if k.vekalet_kullanici_no:
            v = await db.get(Kullanici, k.vekalet_kullanici_no)
            if v:
                vekalet_ad = f"{v.ad} {v.soyad}"
        katilimcilar.append({
            "katilim_no": k.katilim_no,
            "toplanti_no": k.toplanti_no,
            "kullanici_no": u.kullanici_no,
            "ad": u.ad,
            "soyad": u.soyad,
            "e_posta": u.e_posta,
            "katildi_mi": k.katildi_mi,
            "vekalet_kullanici_no": k.vekalet_kullanici_no,
            "vekalet_ad": vekalet_ad,
        })

    # Kararlar
    ka_sonuc = await db.execute(
        select(ToplantiKarar)
        .where(ToplantiKarar.toplanti_no == toplanti_no)
        .order_by(ToplantiKarar.karar_tarihi)
    )
    kararlar = [
        {
            "karar_no": k.karar_no,
            "toplanti_no": k.toplanti_no,
            "karar_metni": k.karar_metni,
            "karar_tarihi": k.karar_tarihi,
        }
        for k in ka_sonuc.scalars().all()
    ]

    # İstatistikler
    stats = await _toplanti_istatistik(db, toplanti_no)

    return {
        "toplanti_no": toplanti.toplanti_no,
        "site_no": toplanti.site_no,
        "baslik": toplanti.baslik,
        "aciklama": toplanti.aciklama,
        "toplanti_tarihi": toplanti.toplanti_tarihi,
        "yer": toplanti.yer,
        "olusturan_no": toplanti.olusturan_no,
        "durum": toplanti.durum,
        "katilimci_sayisi": stats["katilimci_sayisi"],
        "katilan_sayisi": stats["katilan_sayisi"],
        "karar_sayisi": stats["karar_sayisi"],
        "katilim_orani": stats["katilim_orani"],
        "katilimcilar": katilimcilar,
        "kararlar": kararlar,
    }


# ============================================================
# OLUŞTURMA
# ============================================================
async def create_toplanti(
    db: AsyncSession,
    site_no: int,
    *,
    baslik: str,
    toplanti_tarihi: datetime,
    olusturan_no: int,
    aciklama: str | None = None,
    yer: str | None = None,
    katilimci_kullanicilar: list[int] | None = None,
) -> Toplanti:
    """
    Yeni toplantı oluşturur.

    Adımlar:
      1. Toplantı kaydı
      2. Katılımcılar (belirtilmişse veya tüm site sakinleri)
      3. Commit
    """
    # 1) Toplantı
    toplanti = Toplanti(
        site_no=site_no,
        baslik=baslik,
        aciklama=aciklama,
        toplanti_tarihi=toplanti_tarihi,
        yer=yer,
        olusturan_no=olusturan_no,
        durum="PLANLANDI",
    )
    db.add(toplanti)
    await db.flush()

    # 2) Katılımcılar
    if katilimci_kullanicilar:
        hedef = list(set(katilimci_kullanicilar))
    else:
        hedef = await _site_sakin_kullanici_nolar(db, site_no)

    # Kullanıcı var mı doğrulaması
    if hedef:
        k_sonuc = await db.execute(
            select(Kullanici.kullanici_no).where(
                Kullanici.kullanici_no.in_(hedef),
                Kullanici.aktif_mi.is_(True),
            )
        )
        gecerli = [row[0] for row in k_sonuc.all()]
        for k_no in gecerli:
            db.add(ToplantiKatilimci(
                toplanti_no=toplanti.toplanti_no,
                kullanici_no=k_no,
                katildi_mi=False,
            ))

    await db.commit()
    await db.refresh(toplanti)
    logger.info(
        "Yeni toplanti: no=%s site=%s baslik=%s katilimci=%d",
        toplanti.toplanti_no, site_no, baslik[:50], len(hedef),
    )
    return toplanti


# ============================================================
# GÜNCELLE / SİL
# ============================================================
async def update_toplanti(
    db: AsyncSession,
    toplanti_no: int,
    site_no: int,
    *,
    baslik: str | None = None,
    aciklama: str | None = None,
    toplanti_tarihi: datetime | None = None,
    yer: str | None = None,
) -> Toplanti:
    """Toplantıyı günceller."""
    sonuc = await db.execute(
        select(Toplanti).where(
            Toplanti.toplanti_no == toplanti_no,
            Toplanti.site_no == site_no,
        )
    )
    toplanti = sonuc.scalar_one_or_none()
    if toplanti is None:
        raise BulunamadiHatasi("Toplanti", kaynak_id=toplanti_no)

    if baslik is not None:
        toplanti.baslik = baslik
    if aciklama is not None:
        toplanti.aciklama = aciklama
    if toplanti_tarihi is not None:
        toplanti.toplanti_tarihi = toplanti_tarihi
    if yer is not None:
        toplanti.yer = yer

    await db.commit()
    await db.refresh(toplanti)
    logger.info("Toplanti guncellendi: no=%s", toplanti_no)
    return toplanti


async def delete_toplanti(db: AsyncSession, toplanti_no: int, site_no: int) -> None:
    """Toplantıyı ve ilişkili kayıtları siler (cascade)."""
    sonuc = await db.execute(
        select(Toplanti).where(
            Toplanti.toplanti_no == toplanti_no,
            Toplanti.site_no == site_no,
        )
    )
    toplanti = sonuc.scalar_one_or_none()
    if toplanti is None:
        raise BulunamadiHatasi("Toplanti", kaynak_id=toplanti_no)

    await db.delete(toplanti)
    await db.commit()
    logger.info("Toplanti silindi: no=%s", toplanti_no)


# ============================================================
# DURUM DEĞİŞTİR
# ============================================================
async def durum_degistir(
    db: AsyncSession,
    toplanti_no: int,
    site_no: int,
    *,
    yeni_durum: str,
) -> Toplanti:
    """Toplantı durumunu değiştirir."""
    if yeni_durum not in ("PLANLANDI", "YAPILDI", "IPTAL"):
        raise IsKuraliHatasi(f"Gecersiz durum: {yeni_durum}")

    sonuc = await db.execute(
        select(Toplanti).where(
            Toplanti.toplanti_no == toplanti_no,
            Toplanti.site_no == site_no,
        )
    )
    toplanti = sonuc.scalar_one_or_none()
    if toplanti is None:
        raise BulunamadiHatasi("Toplanti", kaynak_id=toplanti_no)

    if toplanti.durum == yeni_durum:
        raise IsKuraliHatasi(f"Toplanti zaten '{yeni_durum}' durumunda.")

    # İptal edilmiş toplantı tekrar açılabilir mi? — Hayır
    if toplanti.durum == "IPTAL" and yeni_durum != "IPTAL":
        raise IsKuraliHatasi("Iptal edilmis toplanti tekrar acilamaz.")

    toplanti.durum = yeni_durum
    await db.commit()
    await db.refresh(toplanti)
    logger.info(
        "Toplanti durum degisti: no=%s -> %s", toplanti_no, yeni_durum
    )
    return toplanti


# ============================================================
# KATILIMCI
# ============================================================
async def katilimci_ekle(
    db: AsyncSession,
    toplanti_no: int,
    site_no: int,
    *,
    kullanici_no: int,
    vekalet_kullanici_no: int | None = None,
) -> ToplantiKatilimci:
    """Toplantıya yeni katılımcı ekler."""
    # Toplantı kontrolü
    t_sonuc = await db.execute(
        select(Toplanti).where(
            Toplanti.toplanti_no == toplanti_no,
            Toplanti.site_no == site_no,
        )
    )
    toplanti = t_sonuc.scalar_one_or_none()
    if toplanti is None:
        raise BulunamadiHatasi("Toplanti", kaynak_id=toplanti_no)

    if toplanti.durum == "IPTAL":
        raise IsKuraliHatasi("Iptal edilmis toplantiya katilimci eklenemez.")

    # Kullanıcı kontrolü
    k = await db.get(Kullanici, kullanici_no)
    if k is None or not k.aktif_mi:
        raise BulunamadiHatasi("Kullanici", kaynak_id=kullanici_no)

    # Zaten katılımcı mı?
    mevcut = await db.execute(
        select(ToplantiKatilimci).where(
            ToplantiKatilimci.toplanti_no == toplanti_no,
            ToplantiKatilimci.kullanici_no == kullanici_no,
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi("Bu kullanici zaten toplanti katilimcisi.")

    # Vekalet kontrolü
    if vekalet_kullanici_no:
        v = await db.get(Kullanici, vekalet_kullanici_no)
        if v is None or not v.aktif_mi:
            raise BulunamadiHatasi("Kullanici", kaynak_id=vekalet_kullanici_no)

    katilimci = ToplantiKatilimci(
        toplanti_no=toplanti_no,
        kullanici_no=kullanici_no,
        katildi_mi=False,
        vekalet_kullanici_no=vekalet_kullanici_no,
    )
    db.add(katilimci)
    await db.commit()
    await db.refresh(katilimci)
    logger.info(
        "Toplanti katilimcisi eklendi: toplanti=%s kullanici=%s",
        toplanti_no, kullanici_no,
    )
    return katilimci


async def katilimci_guncelle(
    db: AsyncSession,
    toplanti_no: int,
    katilim_no: int,
    site_no: int,
    *,
    katildi_mi: bool | None = None,
    vekalet_kullanici_no: int | None = None,
) -> ToplantiKatilimci:
    """Katılımcı durumunu günceller."""
    # Toplantı site kontrolü
    t_sonuc = await db.execute(
        select(Toplanti).where(
            Toplanti.toplanti_no == toplanti_no,
            Toplanti.site_no == site_no,
        )
    )
    if t_sonuc.scalar_one_or_none() is None:
        raise BulunamadiHatasi("Toplanti", kaynak_id=toplanti_no)

    k_sonuc = await db.execute(
        select(ToplantiKatilimci).where(
            ToplantiKatilimci.katilim_no == katilim_no,
            ToplantiKatilimci.toplanti_no == toplanti_no,
        )
    )
    katilimci = k_sonuc.scalar_one_or_none()
    if katilimci is None:
        raise BulunamadiHatasi("ToplantiKatilimci", kaynak_id=katilim_no)

    if katildi_mi is not None:
        katilimci.katildi_mi = katildi_mi
    if vekalet_kullanici_no is not None:
        if vekalet_kullanici_no == 0:
            katilimci.vekalet_kullanici_no = None
        else:
            v = await db.get(Kullanici, vekalet_kullanici_no)
            if v is None or not v.aktif_mi:
                raise BulunamadiHatasi("Kullanici", kaynak_id=vekalet_kullanici_no)
            katilimci.vekalet_kullanici_no = vekalet_kullanici_no

    await db.commit()
    await db.refresh(katilimci)
    return katilimci


# ============================================================
# KARAR
# ============================================================
async def karar_ekle(
    db: AsyncSession,
    toplanti_no: int,
    site_no: int,
    *,
    karar_metni: str,
) -> ToplantiKarar:
    """Toplantıya karar ekler."""
    # Toplantı site kontrolü
    t_sonuc = await db.execute(
        select(Toplanti).where(
            Toplanti.toplanti_no == toplanti_no,
            Toplanti.site_no == site_no,
        )
    )
    toplanti = t_sonuc.scalar_one_or_none()
    if toplanti is None:
        raise BulunamadiHatasi("Toplanti", kaynak_id=toplanti_no)

    if toplanti.durum == "IPTAL":
        raise IsKuraliHatasi("Iptal edilmis toplantiya karar eklenemez.")

    karar = ToplantiKarar(
        toplanti_no=toplanti_no,
        karar_metni=karar_metni,
        karar_tarihi=now_utc_naive(),
    )
    db.add(karar)
    await db.commit()
    await db.refresh(karar)
    logger.info("Karar eklendi: toplanti=%s karar=%s", toplanti_no, karar.karar_no)
    return karar


# ============================================================
# ÖZET İSTATİSTİKLER
# ============================================================
async def get_ozet(db: AsyncSession, site_no: int) -> dict:
    """Site geneli toplantı özeti."""
    # Durum dağılımı
    d_sonuc = await db.execute(
        select(Toplanti.durum, func.count(Toplanti.toplanti_no))
        .where(Toplanti.site_no == site_no)
        .group_by(Toplanti.durum)
    )
    durum_map = dict(d_sonuc.all())
    toplam = sum(durum_map.values())

    # Toplam karar sayısı
    ka_sonuc = await db.execute(
        select(func.count(ToplantiKarar.karar_no))
        .join(Toplanti, Toplanti.toplanti_no == ToplantiKarar.toplanti_no)
        .where(Toplanti.site_no == site_no)
    )
    toplam_karar = int(ka_sonuc.scalar() or 0)

    # Ortalama katılım oranı (tüm toplantılar)
    # Her toplantı için katılımcı/katılan sayıları
    k_sonuc = await db.execute(
        select(
            ToplantiKatilimci.toplanti_no,
            func.count(ToplantiKatilimci.katilim_no),
            func.sum(
                case((ToplantiKatilimci.katildi_mi.is_(True), 1), else_=0)
            ),
        )
        .join(Toplanti, Toplanti.toplanti_no == ToplantiKatilimci.toplanti_no)
        .where(Toplanti.site_no == site_no)
        .group_by(ToplantiKatilimci.toplanti_no)
    )
    oranlar = []
    for _no, top, kat in k_sonuc.all():
        top = int(top or 0)
        kat = int(kat or 0)
        if top > 0:
            oranlar.append(kat / top * 100)
    ort_oran = (sum(oranlar) / len(oranlar)) if oranlar else 0.0

    return {
        "site_no": site_no,
        "toplam": toplam,
        "planlanan": durum_map.get("PLANLANDI", 0),
        "yapilan": durum_map.get("YAPILDI", 0),
        "iptal": durum_map.get("IPTAL", 0),
        "toplam_karar": toplam_karar,
        "ortalama_katilim_orani": round(ort_oran, 2),
    }