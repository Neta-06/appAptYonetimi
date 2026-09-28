"""Personel, izin, puantaj ve maaş iş mantığı."""

import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.security import encrypt_field
from app.core.utils import now_utc_naive
from app.models import (
    Kullanici,
    OnayDurum,
    Personel,
    PersonelIzin,
    PersonelMaasOdeme,
    PersonelPuantaj,
    PersonelSite,
    Site,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI
# ============================================================
async def _onay_durum_no(db: AsyncSession, ad: str) -> int | None:
    """Onay durumu lookup."""
    sonuc = await db.execute(select(OnayDurum).where(OnayDurum.ad == ad))
    d = sonuc.scalar_one_or_none()
    return d.durum_no if d else None


async def _toplam_izin_gun(db: AsyncSession, personel_no: int) -> int:
    """Personelin onaylı izin günleri toplamı."""
    sonuc = await db.execute(
        select(func.coalesce(func.sum(PersonelIzin.gun_sayisi), 0)).where(
            PersonelIzin.personel_no == personel_no,
            PersonelIzin.onay_durum_no == 1,  # ONAYLANDI
        )
    )
    return int(sonuc.scalar() or 0)


# ============================================================
# PERSONEL LİSTELEME
# ============================================================
async def list_personel(
    db: AsyncSession,
    firma_no: int,
    *,
    site_no: int | None = None,
    gorevi: str | None = None,
    aktif_only: bool = True,
    arama: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    """Personel listesini filtreli döner."""
    stmt = select(Personel).where(Personel.firma_no == firma_no)

    if aktif_only:
        stmt = stmt.where(Personel.aktif_mi.is_(True))
    if gorevi:
        stmt = stmt.where(Personel.gorevi == gorevi)
    if arama:
        pattern = f"%{arama.lower()}%"
        stmt = stmt.where(
            func.lower(Personel.ad).like(pattern)
            | func.lower(Personel.soyad).like(pattern)
            | func.lower(func.coalesce(Personel.e_posta, "")).like(pattern)
        )

    # Site filtresi (subquery ile)
    if site_no is not None:
        stmt = stmt.where(
            Personel.personel_no.in_(
                select(PersonelSite.personel_no).where(
                    PersonelSite.site_no == site_no,
                    PersonelSite.bitis_tarihi.is_(None),
                )
            )
        )

    stmt = stmt.order_by(Personel.ad, Personel.soyad).limit(limit).offset(offset)
    sonuc = await db.execute(stmt)
    personeller = list(sonuc.scalars().all())
    if not personeller:
        return []

    personel_nolar = [p.personel_no for p in personeller]

    # Site sayıları
    s_sonuc = await db.execute(
        select(PersonelSite.personel_no, func.count(PersonelSite.kayit_no))
        .where(
            PersonelSite.personel_no.in_(personel_nolar),
            PersonelSite.bitis_tarihi.is_(None),
        )
        .group_by(PersonelSite.personel_no)
    )
    site_map = dict(s_sonuc.all())

    # Aktif izin kontrolü
    bugun = date.today()
    i_sonuc = await db.execute(
        select(PersonelIzin.personel_no)
        .where(
            PersonelIzin.personel_no.in_(personel_nolar),
            PersonelIzin.onay_durum_no == 1,
            PersonelIzin.baslangic_tarihi <= bugun,
            PersonelIzin.bitis_tarihi >= bugun,
        )
        .distinct()
    )
    izinli_set = {row[0] for row in i_sonuc.all()}

    # Son izin tarihi
    si_sonuc = await db.execute(
        select(
            PersonelIzin.personel_no,
            func.max(PersonelIzin.bitis_tarihi),
        )
        .where(PersonelIzin.personel_no.in_(personel_nolar))
        .group_by(PersonelIzin.personel_no)
    )
    son_izin_map = dict(si_sonuc.all())

    kayitlar = []
    for p in personeller:
        kayitlar.append({
            "personel_no": p.personel_no,
            "firma_no": p.firma_no,
            "kullanici_no": p.kullanici_no,
            "ad": p.ad,
            "soyad": p.soyad,
            "gorevi": p.gorevi,
            "telefon": p.telefon,
            "e_posta": p.e_posta,
            "ise_baslama_tarihi": p.ise_baslama_tarihi,
            "isten_cikis_tarihi": p.isten_cikis_tarihi,
            "aktif_mi": p.aktif_mi,
            "site_sayisi": site_map.get(p.personel_no, 0),
            "aktif_izin_mi": p.personel_no in izinli_set,
            "son_izin_tarihi": son_izin_map.get(p.personel_no),
        })
    return kayitlar


# ============================================================
# DETAY
# ============================================================
async def get_personel(
    db: AsyncSession, personel_no: int, firma_no: int
) -> dict:
    """Personel detayı + siteler + izinler + son maaş."""
    sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    p = sonuc.scalar_one_or_none()
    if p is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    # Site atamaları
    s_sonuc = await db.execute(
        select(PersonelSite, Site)
        .join(Site, Site.site_no == PersonelSite.site_no)
        .where(PersonelSite.personel_no == personel_no)
        .order_by(PersonelSite.baslangic_tarihi.desc())
    )
    siteler = []
    for ps, s in s_sonuc.all():
        siteler.append({
            "kayit_no": ps.kayit_no,
            "personel_no": ps.personel_no,
            "site_no": ps.site_no,
            "site_adi": s.site_adi,
            "baslangic_tarihi": ps.baslangic_tarihi,
            "bitis_tarihi": ps.bitis_tarihi,
        })

    # İzinler (son 10)
    i_sonuc = await db.execute(
        select(PersonelIzin)
        .where(PersonelIzin.personel_no == personel_no)
        .order_by(PersonelIzin.baslangic_tarihi.desc())
        .limit(10)
    )
    izinler = []
    for i in i_sonuc.scalars().all():
        onay_ad = None
        if i.onay_durum_no:
            od = await db.get(OnayDurum, i.onay_durum_no)
            if od:
                onay_ad = od.ad
        onaylayan_ad = None
        if i.onaylayan_no:
            k = await db.get(Kullanici, i.onaylayan_no)
            if k:
                onaylayan_ad = f"{k.ad} {k.soyad}"

        izinler.append({
            "izin_no": i.izin_no,
            "personel_no": i.personel_no,
            "izin_tipi": i.izin_tipi,
            "baslangic_tarihi": i.baslangic_tarihi,
            "bitis_tarihi": i.bitis_tarihi,
            "gun_sayisi": i.gun_sayisi,
            "aciklama": i.aciklama,
            "onaylayan_no": i.onaylayan_no,
            "onaylayan_ad": onaylayan_ad,
            "onay_durum_no": i.onay_durum_no,
            "onay_durum_ad": onay_ad,
            "olusturma_tarihi": i.olusturma_tarihi,
        })

    toplam_izin = await _toplam_izin_gun(db, personel_no)

    # Son maaş
    m_sonuc = await db.execute(
        select(PersonelMaasOdeme)
        .where(PersonelMaasOdeme.personel_no == personel_no)
        .order_by(
            PersonelMaasOdeme.donem_yil.desc(),
            PersonelMaasOdeme.donem_ay.desc(),
        )
        .limit(1)
    )
    m = m_sonuc.scalar_one_or_none()
    son_maas_net = m.net_maas if m else None

    return {
        "personel_no": p.personel_no,
        "firma_no": p.firma_no,
        "kullanici_no": p.kullanici_no,
        "ad": p.ad,
        "soyad": p.soyad,
        "gorevi": p.gorevi,
        "telefon": p.telefon,
        "e_posta": p.e_posta,
        "ise_baslama_tarihi": p.ise_baslama_tarihi,
        "isten_cikis_tarihi": p.isten_cikis_tarihi,
        "aktif_mi": p.aktif_mi,
        "siteler": siteler,
        "izinler": izinler,
        "toplam_izin_gun": toplam_izin,
        "son_maas_net": son_maas_net,
    }


# ============================================================
# OLUŞTURMA
# ============================================================
async def create_personel(
    db: AsyncSession,
    firma_no: int,
    *,
    ad: str,
    soyad: str,
    gorevi: str,
    ise_baslama_tarihi: date,
    telefon: str | None = None,
    e_posta: str | None = None,
    kullanici_no: int | None = None,
    tc_kimlik: str | None = None,
    site_nolar: list[int] | None = None,
) -> Personel:
    """Yeni personel kaydı + opsiyonel site atamaları."""
    # Kullanıcı kontrolü (varsa)
    if kullanici_no is not None:
        k = await db.get(Kullanici, kullanici_no)
        if k is None:
            raise BulunamadiHatasi("Kullanici", kaynak_id=kullanici_no)

    # TC şifrele
    tc_sifreli = None
    if tc_kimlik:
        tc_sifreli = encrypt_field(tc_kimlik)

    p = Personel(
        firma_no=firma_no,
        kullanici_no=kullanici_no,
        ad=ad,
        soyad=soyad,
        gorevi=gorevi,
        telefon=telefon,
        e_posta=e_posta,
        tc_kimlik_sifreli=tc_sifreli,
        ise_baslama_tarihi=ise_baslama_tarihi,
        aktif_mi=True,
    )
    db.add(p)
    await db.flush()

    # Site atamaları
    if site_nolar:
        for s_no in set(site_nolar):
            site = await db.get(Site, s_no)
            if site is None:
                raise BulunamadiHatasi("Site", kaynak_id=s_no)
            db.add(PersonelSite(
                personel_no=p.personel_no,
                site_no=s_no,
                baslangic_tarihi=ise_baslama_tarihi,
            ))

    await db.commit()
    await db.refresh(p)
    logger.info(
        "Yeni personel: no=%s firma=%s ad=%s site=%d",
        p.personel_no, firma_no, f"{ad} {soyad}", len(site_nolar or []),
    )
    return p


# ============================================================
# GÜNCELLE / SİL
# ============================================================
async def update_personel(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    ad: str | None = None,
    soyad: str | None = None,
    gorevi: str | None = None,
    telefon: str | None = None,
    e_posta: str | None = None,
    kullanici_no: int | None = None,
    ise_baslama_tarihi: date | None = None,
    isten_cikis_tarihi: date | None = None,
    aktif_mi: bool | None = None,
) -> Personel:
    """Personel güncelleme."""
    sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    p = sonuc.scalar_one_or_none()
    if p is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    if ad is not None:
        p.ad = ad
    if soyad is not None:
        p.soyad = soyad
    if gorevi is not None:
        p.gorevi = gorevi
    if telefon is not None:
        p.telefon = telefon
    if e_posta is not None:
        p.e_posta = e_posta
    if kullanici_no is not None:
        k = await db.get(Kullanici, kullanici_no)
        if k is None:
            raise BulunamadiHatasi("Kullanici", kaynak_id=kullanici_no)
        p.kullanici_no = kullanici_no
    if ise_baslama_tarihi is not None:
        p.ise_baslama_tarihi = ise_baslama_tarihi
    if isten_cikis_tarihi is not None:
        p.isten_cikis_tarihi = isten_cikis_tarihi
        p.aktif_mi = False
    if aktif_mi is not None:
        p.aktif_mi = aktif_mi

    await db.commit()
    await db.refresh(p)
    logger.info("Personel guncellendi: no=%s", personel_no)
    return p


async def delete_personel(db: AsyncSession, personel_no: int, firma_no: int) -> None:
    """Personeli ve tüm ilişkili kayıtlarını siler (cascade)."""
    sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    p = sonuc.scalar_one_or_none()
    if p is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    await db.delete(p)
    await db.commit()
    logger.info("Personel silindi: no=%s", personel_no)


# ============================================================
# İŞTEN ÇIKIŞ
# ============================================================
async def isten_cikis(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    isten_cikis_tarihi: date | None = None,
    aciklama: str | None = None,
) -> Personel:
    """Personeli işten çıkar + tüm site atamalarını kapat."""
    cikis = isten_cikis_tarihi or date.today()

    sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    p = sonuc.scalar_one_or_none()
    if p is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    if not p.aktif_mi:
        raise IsKuraliHatasi("Personel zaten pasif durumda.")

    if cikis < p.ise_baslama_tarihi:
        raise IsKuraliHatasi("Cikis tarihi ise baslama tarihinden once olamaz.")

    p.isten_cikis_tarihi = cikis
    p.aktif_mi = False

    # Tüm aktif site atamalarını kapat
    s_sonuc = await db.execute(
        select(PersonelSite).where(
            PersonelSite.personel_no == personel_no,
            PersonelSite.bitis_tarihi.is_(None),
        )
    )
    for ps in s_sonuc.scalars().all():
        ps.bitis_tarihi = cikis

    await db.commit()
    await db.refresh(p)
    logger.info(
        "Personel isten cikti: no=%s tarih=%s aciklama=%s",
        personel_no, cikis, aciklama,
    )
    return p


# ============================================================
# SİTE ATAMA
# ============================================================
async def site_ata(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    site_no: int,
    baslangic_tarihi: date | None = None,
    bitis_tarihi: date | None = None,
) -> PersonelSite:
    """Personele yeni site ataması ekle."""
    # Personel kontrolü
    p_sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    p = p_sonuc.scalar_one_or_none()
    if p is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)
    if not p.aktif_mi:
        raise IsKuraliHatasi("Pasif personel siteye atanamaz.")

    # Site kontrolü
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    # Zaten aktif atama var mı?
    mevcut = await db.execute(
        select(PersonelSite).where(
            PersonelSite.personel_no == personel_no,
            PersonelSite.site_no == site_no,
            PersonelSite.bitis_tarihi.is_(None),
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi("Bu personel zaten bu siteye atanmis.")

    baslangic = baslangic_tarihi or date.today()

    ps = PersonelSite(
        personel_no=personel_no,
        site_no=site_no,
        baslangic_tarihi=baslangic,
        bitis_tarihi=bitis_tarihi,
    )
    db.add(ps)
    await db.commit()
    await db.refresh(ps)
    logger.info(
        "Personel site atamasi: personel=%s site=%s",
        personel_no, site_no,
    )
    return ps


# ============================================================
# İZİN
# ============================================================
async def list_izinler(
    db: AsyncSession,
    firma_no: int,
    *,
    personel_no: int | None = None,
    onay_durum_no: int | None = None,
    limit: int = 100,
) -> list[dict]:
    """İzin listesi."""
    stmt = (
        select(PersonelIzin, Personel)
        .join(Personel, Personel.personel_no == PersonelIzin.personel_no)
        .where(Personel.firma_no == firma_no)
    )
    if personel_no:
        stmt = stmt.where(PersonelIzin.personel_no == personel_no)
    if onay_durum_no:
        stmt = stmt.where(PersonelIzin.onay_durum_no == onay_durum_no)

    stmt = stmt.order_by(PersonelIzin.baslangic_tarihi.desc()).limit(limit)
    sonuc = await db.execute(stmt)
    kayitlar = []
    for i, p in sonuc.all():
        onay_ad = None
        if i.onay_durum_no:
            od = await db.get(OnayDurum, i.onay_durum_no)
            if od:
                onay_ad = od.ad

        onaylayan_ad = None
        if i.onaylayan_no:
            k = await db.get(Kullanici, i.onaylayan_no)
            if k:
                onaylayan_ad = f"{k.ad} {k.soyad}"

        kayitlar.append({
            "izin_no": i.izin_no,
            "personel_no": i.personel_no,
            "izin_tipi": i.izin_tipi,
            "baslangic_tarihi": i.baslangic_tarihi,
            "bitis_tarihi": i.bitis_tarihi,
            "gun_sayisi": i.gun_sayisi,
            "aciklama": i.aciklama,
            "onaylayan_no": i.onaylayan_no,
            "onaylayan_ad": onaylayan_ad,
            "onay_durum_no": i.onay_durum_no,
            "onay_durum_ad": onay_ad,
            "olusturma_tarihi": i.olusturma_tarihi,
        })
    return kayitlar


async def izin_talep_et(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    izin_tipi: str,
    baslangic_tarihi: date,
    bitis_tarihi: date,
    aciklama: str | None = None,
) -> PersonelIzin:
    """Yeni izin talebi oluştur."""
    if bitis_tarihi < baslangic_tarihi:
        raise IsKuraliHatasi("Bitis tarihi baslangic tarihinden once olamaz.")

    # Personel kontrolü
    p_sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    p = p_sonuc.scalar_one_or_none()
    if p is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    # Gün sayısı
    gun_sayisi = (bitis_tarihi - baslangic_tarihi).days + 1

    # Bekleyen onay durumu
    onay_no = await _onay_durum_no(db, "BEKLIYOR")

    izin = PersonelIzin(
        personel_no=personel_no,
        izin_tipi=izin_tipi,
        baslangic_tarihi=baslangic_tarihi,
        bitis_tarihi=bitis_tarihi,
        gun_sayisi=gun_sayisi,
        aciklama=aciklama,
        onay_durum_no=onay_no,
        olusturma_tarihi=now_utc_naive(),
    )
    db.add(izin)
    await db.commit()
    await db.refresh(izin)
    logger.info(
        "Izin talebi: personel=%s tip=%s gun=%d",
        personel_no, izin_tipi, gun_sayisi,
    )
    return izin


async def izin_onayla(
    db: AsyncSession,
    izin_no: int,
    firma_no: int,
    *,
    onay_durum_no: int,
    onaylayan_no: int,
    aciklama: str | None = None,
) -> PersonelIzin:
    """İzni onayla / reddet."""
    sonuc = await db.execute(
        select(PersonelIzin, Personel)
        .join(Personel, Personel.personel_no == PersonelIzin.personel_no)
        .where(
            PersonelIzin.izin_no == izin_no,
            Personel.firma_no == firma_no,
        )
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("PersonelIzin", kaynak_id=izin_no)
    izin, _ = row

    if izin.onay_durum_no == 1:
        raise IsKuraliHatasi("Bu izin zaten onaylanmis.")

    izin.onay_durum_no = onay_durum_no
    izin.onaylayan_no = onaylayan_no
    if aciklama:
        izin.aciklama = (izin.aciklama or "") + f" | {aciklama}"

    await db.commit()
    await db.refresh(izin)
    logger.info(
        "Izin onay durumu degisti: izin=%s durum=%d",
        izin_no, onay_durum_no,
    )
    return izin


# ============================================================
# PUANTAJ
# ============================================================
async def list_puantaj(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    baslangic: date | None = None,
    bitis: date | None = None,
    limit: int = 100,
) -> list[dict]:
    """Personel puantaj listesi."""
    # Personel firma kontrolü
    p_sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    if p_sonuc.scalar_one_or_none() is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    stmt = select(PersonelPuantaj).where(PersonelPuantaj.personel_no == personel_no)
    if baslangic:
        stmt = stmt.where(PersonelPuantaj.tarih >= baslangic)
    if bitis:
        stmt = stmt.where(PersonelPuantaj.tarih <= bitis)

    stmt = stmt.order_by(PersonelPuantaj.tarih.desc()).limit(limit)
    sonuc = await db.execute(stmt)
    return [
        {
            "puantaj_no": p.puantaj_no,
            "personel_no": p.personel_no,
            "tarih": p.tarih,
            "giris_saati": p.giris_saati,
            "cikis_saati": p.cikis_saati,
            "toplam_saat": p.toplam_saat,
            "devamsiz_mi": p.devamsiz_mi,
            "aciklama": p.aciklama,
        }
        for p in sonuc.scalars().all()
    ]


async def puantaj_ekle(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    tarih: date,
    giris_saati=None,
    cikis_saati=None,
    devamsiz_mi: bool = False,
    aciklama: str | None = None,
) -> PersonelPuantaj:
    """Puantaj kaydı ekle (giriş-çıkış)."""
    # Personel kontrolü
    p_sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    p = p_sonuc.scalar_one_or_none()
    if p is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    # Aynı gün kaydı var mı?
    mevcut = await db.execute(
        select(PersonelPuantaj).where(
            PersonelPuantaj.personel_no == personel_no,
            PersonelPuantaj.tarih == tarih,
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi(
            f"'{tarih}' tarihinde bu personel icin puantaj zaten kayitli."
        )

    # Toplam saat hesabı
    toplam_saat = None
    if giris_saati and cikis_saati:
        g = (
            giris_saati.hour
            + giris_saati.minute / 60
            + giris_saati.second / 3600
        )
        c = (
            cikis_saati.hour
            + cikis_saati.minute / 60
            + cikis_saati.second / 3600
        )
        if c > g:
            toplam_saat = Decimal(str(round(c - g, 2)))

    kayit = PersonelPuantaj(
        personel_no=personel_no,
        tarih=tarih,
        giris_saati=giris_saati,
        cikis_saati=cikis_saati,
        toplam_saat=toplam_saat,
        devamsiz_mi=devamsiz_mi,
        aciklama=aciklama,
    )
    db.add(kayit)
    await db.commit()
    await db.refresh(kayit)
    logger.info(
        "Puantaj eklendi: personel=%s tarih=%s saat=%s",
        personel_no, tarih, toplam_saat,
    )
    return kayit


async def puantaj_aylik_ozet(
    db: AsyncSession,
    firma_no: int,
    *,
    donem_yil: int,
    donem_ay: int,
    personel_no: int | None = None,
) -> list[dict]:
    """Aylık puantaj özeti — personel başına."""
    stmt = (
        select(
            Personel.personel_no,
            Personel.ad,
            Personel.soyad,
            func.count(PersonelPuantaj.puantaj_no).label("toplam_gun"),
            func.sum(
                case((PersonelPuantaj.devamsiz_mi.is_(False), 1), else_=0)
            ).label("calisilan_gun"),
            func.sum(
                case((PersonelPuantaj.devamsiz_mi.is_(True), 1), else_=0)
            ).label("devamsiz_gun"),
            func.coalesce(func.sum(PersonelPuantaj.toplam_saat), 0).label("toplam_saat"),
        )
        .join(PersonelPuantaj, PersonelPuantaj.personel_no == Personel.personel_no)
        .where(
            Personel.firma_no == firma_no,
            func.year(PersonelPuantaj.tarih) == donem_yil,
            func.month(PersonelPuantaj.tarih) == donem_ay,
        )
        .group_by(Personel.personel_no, Personel.ad, Personel.soyad)
        .order_by(Personel.ad, Personel.soyad)
    )
    if personel_no:
        stmt = stmt.where(Personel.personel_no == personel_no)

    sonuc = await db.execute(stmt)
    return [
        {
            "personel_no": r[0],
            "ad": r[1],
            "soyad": r[2],
            "donem_yil": donem_yil,
            "donem_ay": donem_ay,
            "toplam_gun": int(r[3] or 0),
            "calisilan_gun": int(r[4] or 0),
            "devamsiz_gun": int(r[5] or 0),
            "toplam_saat": Decimal(str(r[6] or 0)),
        }
        for r in sonuc.all()
    ]


# ============================================================
# MAAŞ
# ============================================================
async def list_maaslar(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    limit: int = 100,
) -> list[dict]:
    """Personel maaş ödeme geçmişi."""
    p_sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    if p_sonuc.scalar_one_or_none() is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    sonuc = await db.execute(
        select(PersonelMaasOdeme)
        .where(PersonelMaasOdeme.personel_no == personel_no)
        .order_by(
            PersonelMaasOdeme.donem_yil.desc(),
            PersonelMaasOdeme.donem_ay.desc(),
        )
        .limit(limit)
    )
    return [
        {
            "maas_odeme_no": m.maas_odeme_no,
            "personel_no": m.personel_no,
            "donem_yil": m.donem_yil,
            "donem_ay": m.donem_ay,
            "brut_maas": m.brut_maas,
            "kesintiler": m.kesintiler,
            "net_maas": m.net_maas,
            "odeme_tarihi": m.odeme_tarihi,
        }
        for m in sonuc.scalars().all()
    ]


async def maas_ekle(
    db: AsyncSession,
    personel_no: int,
    firma_no: int,
    *,
    donem_yil: int,
    donem_ay: int,
    brut_maas: Decimal,
    kesintiler: Decimal = Decimal("0.00"),
    odeme_tarihi: date | None = None,
) -> PersonelMaasOdeme:
    """Personel maaş ödemesi ekle."""
    # Personel kontrolü
    p_sonuc = await db.execute(
        select(Personel).where(
            Personel.personel_no == personel_no,
            Personel.firma_no == firma_no,
        )
    )
    if p_sonuc.scalar_one_or_none() is None:
        raise BulunamadiHatasi("Personel", kaynak_id=personel_no)

    # Aynı dönem var mı?
    mevcut = await db.execute(
        select(PersonelMaasOdeme).where(
            PersonelMaasOdeme.personel_no == personel_no,
            PersonelMaasOdeme.donem_yil == donem_yil,
            PersonelMaasOdeme.donem_ay == donem_ay,
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi(
            f"{donem_yil}/{donem_ay} donemi icin maas zaten kayitli."
        )

    # net_maas MySQL GENERATED COLUMN — otomatik hesaplanir, INSERT'te yer almaz
    m = PersonelMaasOdeme(
        personel_no=personel_no,
        donem_yil=donem_yil,
        donem_ay=donem_ay,
        brut_maas=brut_maas,
        kesintiler=kesintiler,
        odeme_tarihi=odeme_tarihi or date.today(),
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    logger.info(
        "Maas eklendi: personel=%s donem=%s/%s brut=%s",
        personel_no, donem_yil, donem_ay, brut_maas,
    )
    return m


# ============================================================
# ÖZET İSTATİSTİKLER
# ============================================================
async def get_ozet(
    db: AsyncSession, firma_no: int, *, site_no: int | None = None
) -> dict:
    """Firma/site geneli personel özeti."""
    stmt = select(Personel).where(Personel.firma_no == firma_no)
    if site_no is not None:
        stmt = stmt.where(
            Personel.personel_no.in_(
                select(PersonelSite.personel_no).where(
                    PersonelSite.site_no == site_no,
                    PersonelSite.bitis_tarihi.is_(None),
                )
            )
        )

    sonuc = await db.execute(stmt)
    personeller = list(sonuc.scalars().all())
    toplam = len(personeller)
    aktif = sum(1 for p in personeller if p.aktif_mi)
    pasif = toplam - aktif

    # Aktif izinli
    bugun = date.today()
    aktif_personel_nolar = [p.personel_no for p in personeller if p.aktif_mi]
    izinli = 0
    if aktif_personel_nolar:
        i_sonuc = await db.execute(
            select(func.count(func.distinct(PersonelIzin.personel_no))).where(
                PersonelIzin.personel_no.in_(aktif_personel_nolar),
                PersonelIzin.onay_durum_no == 1,
                PersonelIzin.baslangic_tarihi <= bugun,
                PersonelIzin.bitis_tarihi >= bugun,
            )
        )
        izinli = int(i_sonuc.scalar() or 0)

    # Görev dağılımı
    gorev_map: dict[str, int] = {}
    for p in personeller:
        gorev_map[p.gorevi] = gorev_map.get(p.gorevi, 0) + 1
    gorev_dagilimi = [
        {
            "gorevi": g,
            "sayi": s,
            "yuzde": round(s / toplam * 100, 2) if toplam > 0 else 0.0,
        }
        for g, s in sorted(gorev_map.items(), key=lambda x: -x[1])
    ]

    # Toplam yıllık izin günü
    toplam_izin = 0
    if personeller:
        ti_sonuc = await db.execute(
            select(func.coalesce(func.sum(PersonelIzin.gun_sayisi), 0)).where(
                PersonelIzin.personel_no.in_([p.personel_no for p in personeller]),
                PersonelIzin.izin_tipi == "YILLIK",
                PersonelIzin.onay_durum_no == 1,
            )
        )
        toplam_izin = int(ti_sonuc.scalar() or 0)

    # Ortalama hizmet yılı
    ort_hizmet = 0.0
    if aktif > 0:
        toplam_gun = sum(
            (bugun - p.ise_baslama_tarihi).days
            for p in personeller if p.aktif_mi
        )
        ort_hizmet = round(toplam_gun / aktif / 365.25, 1)

    return {
        "firma_no": firma_no,
        "toplam_personel": toplam,
        "aktif_personel": aktif,
        "pasif_personel": pasif,
        "aktif_izinli": izinli,
        "gorev_dagilimi": gorev_dagilimi,
        "toplam_yillik_izin_gun": toplam_izin,
        "ortalama_hizmet_yili": ort_hizmet,
    }