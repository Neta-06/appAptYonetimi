"""Sakin yönetimi iş mantığı."""

import logging
from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, IsKuraliHatasi
from app.core.security import decrypt_field
from app.core.utils import now_utc_naive
from app.models import (
    Blok,
    Daire,
    DaireDoluluk,
    DaireKullanim,
    DaireSakin,
    DaireTipi,
    Kullanici,
    KullaniciSite,
    Rol,
    Site,
)

logger = logging.getLogger(__name__)


# ============================================================
# YARDIMCI: Daire doluluk güncelle
# ============================================================
async def _daire_doluluk_guncelle(db: AsyncSession, daire_no: int) -> None:
    """
    Dairedeki aktif sakin sayısına göre doluluk durumunu günceller.
    Aktif sakin var → DOLU, yok → BOS.
    """

    # KRITIK: once flush — bekleyen degisiklikler DB'ye yazilsin
    await db.flush()
    # Aktif sakin sayısı
    sayi_sonuc = await db.execute(
        select(func.count(DaireSakin.kayit_no)).where(
            DaireSakin.daire_no == daire_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    aktif_sayi = int(sayi_sonuc.scalar() or 0)

    # Daireyi bul
    daire = await db.get(Daire, daire_no)
    if daire is None:
        return

    # DOLU ve BOS doluluk_no'larını bul
    d_sonuc = await db.execute(
        select(DaireDoluluk).where(DaireDoluluk.ad.in_(["DOLU", "BOS"]))
    )
    doluluk_map = {d.ad: d.doluluk_no for d in d_sonuc.scalars().all()}

    yeni_doluluk = (
        doluluk_map.get("DOLU") if aktif_sayi > 0 else doluluk_map.get("BOS")
    )
    if yeni_doluluk and daire.doluluk_no != yeni_doluluk:
        daire.doluluk_no = yeni_doluluk
        logger.info(
            "Daire %s doluluk guncellendi: aktif_sakin=%s",
            daire_no, aktif_sayi,
        )


# ============================================================
# YARDIMCI: Daire bilgisi (ozet + detay)
# ============================================================
async def _daire_bilgi(db: AsyncSession, daire_no: int) -> dict | None:
    sonuc = await db.execute(
        select(Daire, Blok, Site, DaireTipi)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .join(Site, Site.site_no == Daire.site_no)
        .join(DaireTipi, DaireTipi.tip_no == Daire.daire_tipi_no)
        .where(Daire.daire_no == daire_no)
    )
    row = sonuc.first()
    if row is None:
        return None
    d, b, s, dt = row
    return {
        "site_no": s.site_no,
        "site_adi": s.site_adi,
        "blok_adi": b.blok_adi,
        "daire_numarasi": d.daire_numarasi,
        "kat": d.kat,
        "daire_tipi": dt.ad,
        "brut_metrekare": d.brut_metrekare,
        "ozet": f"{b.blok_adi} - Daire {d.daire_numarasi}",
    }


# ============================================================
# LİSTELEME
# ============================================================
async def list_sakinler(
    db: AsyncSession,
    site_no: int,
    *,
    aktif_only: bool = True,
    mulk_sahibi_mi: bool | None = None,
    daire_no: int | None = None,
    arama: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    """Site sakinlerini filtreli listeler."""
    stmt = (
        select(DaireSakin, Daire, Blok, Kullanici)
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .join(Kullanici, Kullanici.kullanici_no == DaireSakin.kullanici_no)
        .where(Daire.site_no == site_no)
    )

    if aktif_only:
        stmt = stmt.where(DaireSakin.cikis_tarihi.is_(None))
    if mulk_sahibi_mi is not None:
        stmt = stmt.where(DaireSakin.mulk_sahibi_mi == mulk_sahibi_mi)
    if daire_no is not None:
        stmt = stmt.where(DaireSakin.daire_no == daire_no)
    if arama:
        # Ad, soyad veya e-posta ile ara
        pattern = f"%{arama.lower()}%"
        stmt = stmt.where(
            func.lower(Kullanici.ad).like(pattern)
            | func.lower(Kullanici.soyad).like(pattern)
            | func.lower(Kullanici.e_posta).like(pattern)
        )

    stmt = stmt.order_by(
        Blok.blok_adi,
        Daire.daire_numarasi,
        DaireSakin.giris_tarihi,
    ).limit(limit).offset(offset)

    sonuc = await db.execute(stmt)
    satirlar = list(sonuc.all())
    if not satirlar:
        return []

    # Kullanıcı-site rollerini toplu yükle
    kullanici_nolar = [s[0].kullanici_no for s in satirlar]
    rol_sonuc = await db.execute(
        select(KullaniciSite.kullanici_no, Rol.ad)
        .join(Rol, Rol.rol_no == KullaniciSite.rol_no)
        .where(
            KullaniciSite.kullanici_no.in_(kullanici_nolar),
            KullaniciSite.site_no == site_no,
            KullaniciSite.aktif_mi.is_(True),
        )
    )
    rol_map = {k_no: ad for k_no, ad in rol_sonuc.all()}

    kayitlar = []
    for ds, d, b, k in satirlar:
        # Telefonu çöz (şifreliyse)
        telefon = None
        if k.telefon_sifreli:
            try:
                telefon = decrypt_field(k.telefon_sifreli)
            except Exception:
                telefon = None

        kayitlar.append({
            "kayit_no": ds.kayit_no,
            "daire_no": ds.daire_no,
            "daire_ozet": f"{b.blok_adi} - Daire {d.daire_numarasi}",
            "blok_adi": b.blok_adi,
            "daire_numarasi": d.daire_numarasi,
            "kullanici_no": k.kullanici_no,
            "ad": k.ad,
            "soyad": k.soyad,
            "e_posta": k.e_posta,
            "telefon": telefon,
            "mulk_sahibi_mi": ds.mulk_sahibi_mi,
            "giris_tarihi": ds.giris_tarihi,
            "cikis_tarihi": ds.cikis_tarihi,
            "aktif_mi": ds.cikis_tarihi is None,
            "kullanici_site_rolu": rol_map.get(k.kullanici_no),
        })
    return kayitlar


async def list_daire_sakinleri(
    db: AsyncSession,
    site_no: int,
    daire_no: int,
) -> list[dict]:
    """Bir dairenin tüm sakinleri (aktif + geçmiş)."""
    # Daire site kontrolü
    daire = await db.get(Daire, daire_no)
    if daire is None or daire.site_no != site_no:
        raise BulunamadiHatasi("Daire", kaynak_id=daire_no)

    return await list_sakinler(
        db, site_no,
        aktif_only=False,
        daire_no=daire_no,
    )


# ============================================================
# DETAY
# ============================================================
async def get_sakin(
    db: AsyncSession,
    kayit_no: int,
    site_no: int,
) -> dict:
    """Tek sakin detayı."""
    sonuc = await db.execute(
        select(DaireSakin, Kullanici, Daire)
        .join(Kullanici, Kullanici.kullanici_no == DaireSakin.kullanici_no)
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            DaireSakin.kayit_no == kayit_no,
            Daire.site_no == site_no,
        )
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("DaireSakin", kaynak_id=kayit_no)
    ds, k, d = row

    # Daire bilgisi
    bilgi = await _daire_bilgi(db, d.daire_no)
    if bilgi is None:
        raise BulunamadiHatasi("Daire", kaynak_id=d.daire_no)

    # Telefon çöz
    telefon = None
    if k.telefon_sifreli:
        try:
            telefon = decrypt_field(k.telefon_sifreli)
        except Exception:
            telefon = None

    # Bu dairedeki diğer aktif sakin sayısı
    diger_sonuc = await db.execute(
        select(func.count(DaireSakin.kayit_no)).where(
            DaireSakin.daire_no == d.daire_no,
            DaireSakin.kayit_no != kayit_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    diger_sayi = int(diger_sonuc.scalar() or 0)

    return {
        "kayit_no": ds.kayit_no,
        "daire_no": ds.daire_no,
        "kullanici_no": ds.kullanici_no,
        "mulk_sahibi_mi": ds.mulk_sahibi_mi,
        "giris_tarihi": ds.giris_tarihi,
        "cikis_tarihi": ds.cikis_tarihi,
        "olusturma_tarihi": ds.olusturma_tarihi,
        "guncellenme_tarihi": ds.guncellenme_tarihi,
        # Kullanıcı
        "ad": k.ad,
        "soyad": k.soyad,
        "e_posta": k.e_posta,
        "telefon": telefon,
        # Daire
        "site_no": bilgi["site_no"],
        "site_adi": bilgi["site_adi"],
        "blok_adi": bilgi["blok_adi"],
        "daire_numarasi": bilgi["daire_numarasi"],
        "kat": bilgi["kat"],
        "daire_tipi": bilgi["daire_tipi"],
        "brut_metrekare": bilgi["brut_metrekare"],
        # Durum
        "aktif_mi": ds.cikis_tarihi is None,
        "diger_aktif_sakin_sayisi": diger_sayi,
    }


# ============================================================
# YENİ SAKİN
# ============================================================
async def create_sakin(
    db: AsyncSession,
    site_no: int,
    *,
    daire_no: int,
    kullanici_no: int,
    mulk_sahibi_mi: bool = False,
    giris_tarihi: date | None = None,
    kullanici_site_rolu: str = "SAKIN",
    kullanici_site_olustur: bool = True,
) -> DaireSakin:
    """
    Yeni sakin ekler.

    Adımlar:
      1. Daire, kullanıcı, rol kontrolleri
      2. Kullanıcı zaten aktif sakin mi kontrolü
      3. daire_sakin kaydı oluştur
      4. kullanici_site yoksa (ve istenirse) otomatik oluştur
      5. Daire doluluk güncelle (BOS → DOLU)
      6. Commit
    """
    giris = giris_tarihi or date.today()

    # 1) Daire kontrolü
    daire = await db.get(Daire, daire_no)
    if daire is None or daire.site_no != site_no:
        raise BulunamadiHatasi("Daire", kaynak_id=daire_no)

    # 2) Kullanıcı kontrolü
    kullanici = await db.get(Kullanici, kullanici_no)
    if kullanici is None:
        raise BulunamadiHatasi("Kullanici", kaynak_id=kullanici_no)
    if not kullanici.aktif_mi:
        raise IsKuraliHatasi("Pasif kullanici sakin olarak eklenemez.")

    # 3) Bu dairede zaten aktif sakin mi?
    mevcut = await db.execute(
        select(DaireSakin).where(
            DaireSakin.daire_no == daire_no,
            DaireSakin.kullanici_no == kullanici_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi(
            "Bu kullanici zaten bu dairede aktif sakin olarak kayitli."
        )

    # 4) daire_sakin kaydı
    kayit = DaireSakin(
        daire_no=daire_no,
        kullanici_no=kullanici_no,
        mulk_sahibi_mi=mulk_sahibi_mi,
        giris_tarihi=giris,
        olusturma_tarihi=now_utc_naive(),
        guncellenme_tarihi=now_utc_naive(),
    )
    db.add(kayit)

    # 5) Kullanıcı-site üyeliği
    if kullanici_site_olustur:
        ks_sonuc = await db.execute(
            select(KullaniciSite).where(
                KullaniciSite.kullanici_no == kullanici_no,
                KullaniciSite.site_no == site_no,
            )
        )
        ks = ks_sonuc.scalar_one_or_none()
        if ks is None:
            # Rolü bul
            rol_sonuc = await db.execute(
                select(Rol).where(Rol.ad == kullanici_site_rolu)
            )
            rol = rol_sonuc.scalar_one_or_none()
            if rol is None:
                raise IsKuraliHatasi(
                    f"'{kullanici_site_rolu}' rol tanimi bulunamadi."
                )
            db.add(KullaniciSite(
                kullanici_no=kullanici_no,
                site_no=site_no,
                rol_no=rol.rol_no,
                baslangic_tarihi=giris,
                aktif_mi=True,
                olusturma_tarihi=now_utc_naive(),
                guncellenme_tarihi=now_utc_naive(),
            ))
        elif not ks.aktif_mi:
            ks.aktif_mi = True
            ks.baslangic_tarihi = giris

    await db.flush()

    # 6) Doluluk güncelle
    await _daire_doluluk_guncelle(db, daire_no)

    await db.commit()
    await db.refresh(kayit)
    logger.info(
        "Yeni sakin: kayit=%s daire=%s kullanici=%s mulk=%s",
        kayit.kayit_no, daire_no, kullanici_no, mulk_sahibi_mi,
    )
    return kayit


# ============================================================
# GÜNCELLE
# ============================================================
async def update_sakin(
    db: AsyncSession,
    kayit_no: int,
    site_no: int,
    *,
    mulk_sahibi_mi: bool | None = None,
    giris_tarihi: date | None = None,
    cikis_tarihi: date | None = None,
) -> DaireSakin:
    """Sakin kaydını günceller."""
    sonuc = await db.execute(
        select(DaireSakin, Daire)
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            DaireSakin.kayit_no == kayit_no,
            Daire.site_no == site_no,
        )
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("DaireSakin", kaynak_id=kayit_no)
    kayit, daire = row

    if mulk_sahibi_mi is not None:
        kayit.mulk_sahibi_mi = mulk_sahibi_mi
    if giris_tarihi is not None:
        kayit.giris_tarihi = giris_tarihi
    if cikis_tarihi is not None:
        if cikis_tarihi < kayit.giris_tarihi:
            raise IsKuraliHatasi(
                "Cikis tarihi giris tarihinden once olamaz."
            )
        kayit.cikis_tarihi = cikis_tarihi
        # Doluluk güncelle
        await _daire_doluluk_guncelle(db, daire.daire_no)

    kayit.guncellenme_tarihi = now_utc_naive()
    await db.commit()
    await db.refresh(kayit)
    logger.info("Sakin guncellendi: kayit=%s", kayit_no)
    return kayit


# ============================================================
# ÇIKIŞ (taşınma)
# ============================================================
async def cikis_yap(
    db: AsyncSession,
    kayit_no: int,
    site_no: int,
    *,
    cikis_tarihi: date | None = None,
) -> dict:
    """
    Sakini çıkış yapar (daireden ayrılır).
    Daire boş kalırsa doluluk BOS olur.
    """
    cikis = cikis_tarihi or date.today()

    sonuc = await db.execute(
        select(DaireSakin, Daire)
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            DaireSakin.kayit_no == kayit_no,
            Daire.site_no == site_no,
        )
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("DaireSakin", kaynak_id=kayit_no)
    kayit, daire = row

    if kayit.cikis_tarihi is not None:
        raise IsKuraliHatasi("Bu sakin zaten cikis yapmis.")

    if cikis < kayit.giris_tarihi:
        raise IsKuraliHatasi("Cikis tarihi giris tarihinden once olamaz.")

    kayit.cikis_tarihi = cikis
    kayit.guncellenme_tarihi = now_utc_naive()

    # Doluluk güncelle
    await _daire_doluluk_guncelle(db, daire.daire_no)

    await db.commit()

    # Kontrol: daire boş kaldı mı?
    aktif_sonuc = await db.execute(
        select(func.count(DaireSakin.kayit_no)).where(
            DaireSakin.daire_no == daire.daire_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    aktif_sayi = int(aktif_sonuc.scalar() or 0)
    daire_bos = aktif_sayi == 0

    logger.info(
        "Sakin cikis: kayit=%s daire=%s cikis=%s daire_bos=%s",
        kayit_no, daire.daire_no, cikis, daire_bos,
    )

    return {
        "kayit_no": kayit_no,
        "cikis_tarihi": cikis,
        "daire_no": daire.daire_no,
        "daire_bos_kaldi_mi": daire_bos,
        "mesaj": (
            f"Sakin cikis yapti. Daire {'bos kaldi' if daire_bos else 'hala dolu'}."
        ),
    }


# ============================================================
# TAŞINMA (daire değişikliği)
# ============================================================
async def tasindi_yap(
    db: AsyncSession,
    kayit_no: int,
    site_no: int,
    *,
    yeni_daire_no: int,
    tasinma_tarihi: date | None = None,
    mulk_sahibi_mi: bool | None = None,
) -> dict:
    """
    Sakini başka bir daireye taşır.

    Adımlar:
      1. Eski kaydı bul, aktif mi kontrol
      2. Yeni daire kontrolü (aynı sitede mi)
      3. Eski kaydı kapat (cikis_tarihi)
      4. Yeni kayıt aç
      5. İki dairenin doluluğunu güncelle
    """
    tarih = tasinma_tarihi or date.today()

    # 1) Eski kayıt
    sonuc = await db.execute(
        select(DaireSakin, Daire)
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            DaireSakin.kayit_no == kayit_no,
            Daire.site_no == site_no,
        )
    )
    row = sonuc.first()
    if row is None:
        raise BulunamadiHatasi("DaireSakin", kaynak_id=kayit_no)
    eski_kayit, eski_daire = row

    if eski_kayit.cikis_tarihi is not None:
        raise IsKuraliHatasi("Bu sakin zaten cikis yapmis, tasinamaz.")

    if tarih < eski_kayit.giris_tarihi:
        raise IsKuraliHatasi("Tasinma tarihi giris tarihinden once olamaz.")

    # 2) Yeni daire
    if yeni_daire_no == eski_daire.daire_no:
        raise IsKuraliHatasi("Sakin zaten bu dairede kayitli.")

    yeni_daire = await db.get(Daire, yeni_daire_no)
    if yeni_daire is None or yeni_daire.site_no != site_no:
        raise BulunamadiHatasi("Daire", kaynak_id=yeni_daire_no)

    # Aynı kullanıcı yeni dairede aktif mi?
    mevcut = await db.execute(
        select(DaireSakin).where(
            DaireSakin.daire_no == yeni_daire_no,
            DaireSakin.kullanici_no == eski_kayit.kullanici_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    if mevcut.scalar_one_or_none() is not None:
        raise IsKuraliHatasi(
            "Bu kullanici zaten hedef dairede aktif sakin olarak kayitli."
        )

    # 3) Eski kaydı kapat
    eski_kayit.cikis_tarihi = tarih
    eski_kayit.guncellenme_tarihi = now_utc_naive()

    # 4) Yeni kayıt
    yeni_mulk = (
        mulk_sahibi_mi if mulk_sahibi_mi is not None else eski_kayit.mulk_sahibi_mi
    )
    yeni_kayit = DaireSakin(
        daire_no=yeni_daire_no,
        kullanici_no=eski_kayit.kullanici_no,
        mulk_sahibi_mi=yeni_mulk,
        giris_tarihi=tarih,
        olusturma_tarihi=now_utc_naive(),
        guncellenme_tarihi=now_utc_naive(),
    )
    db.add(yeni_kayit)
    await db.flush()

    # 5) Her iki dairenin doluluğunu güncelle
    await _daire_doluluk_guncelle(db, eski_daire.daire_no)
    await _daire_doluluk_guncelle(db, yeni_daire_no)

    await db.commit()
    await db.refresh(yeni_kayit)

    # Eski daire boş kaldı mı?
    aktif_sonuc = await db.execute(
        select(func.count(DaireSakin.kayit_no)).where(
            DaireSakin.daire_no == eski_daire.daire_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    eski_bos = int(aktif_sonuc.scalar() or 0) == 0

    logger.info(
        "Sakin tasindi: eski_kayit=%s yeni_kayit=%s eski=%s yeni=%s",
        kayit_no, yeni_kayit.kayit_no, eski_daire.daire_no, yeni_daire_no,
    )

    return {
        "eski_kayit_no": kayit_no,
        "yeni_kayit_no": yeni_kayit.kayit_no,
        "eski_daire_no": eski_daire.daire_no,
        "yeni_daire_no": yeni_daire_no,
        "tasinma_tarihi": tarih,
        "eski_daire_bos_kaldi_mi": eski_bos,
        "mesaj": (
            f"Sakin basariyla tasindi. "
            f"Eski daire {'bos kaldi' if eski_bos else 'hala dolu'}."
        ),
    }


# ============================================================
# ÖZET İSTATİSTİKLER
# ============================================================
async def get_ozet(db: AsyncSession, site_no: int) -> dict:
    """Site geneli sakin istatistikleri."""
    site = await db.get(Site, site_no)
    if site is None:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)

    # Aktif sakinler
    aktif_sonuc = await db.execute(
        select(
            func.count(DaireSakin.kayit_no),
            func.sum(
                case((DaireSakin.mulk_sahibi_mi.is_(True), 1), else_=0)
            ),
        )
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            Daire.site_no == site_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
    )
    aktif_row = aktif_sonuc.first()
    toplam_aktif = int(aktif_row[0] or 0)
    toplam_malik = int(aktif_row[1] or 0)
    toplam_kiraci = toplam_aktif - toplam_malik

    # Geçmiş (çıkış yapmış)
    gecmis_sonuc = await db.execute(
        select(func.count(DaireSakin.kayit_no))
        .join(Daire, Daire.daire_no == DaireSakin.daire_no)
        .where(
            Daire.site_no == site_no,
            DaireSakin.cikis_tarihi.is_not(None),
        )
    )
    toplam_gecmis = int(gecmis_sonuc.scalar() or 0)

    # Daire sayısı
    daire_sonuc = await db.execute(
        select(func.count(Daire.daire_no)).where(Daire.site_no == site_no)
    )
    toplam_daire = int(daire_sonuc.scalar() or 0)
    ortalama = (toplam_aktif / toplam_daire) if toplam_daire > 0 else 0.0

    # En kalabalık daire
    kalabalik_sonuc = await db.execute(
        select(
            Daire.daire_no,
            Blok.blok_adi,
            Daire.daire_numarasi,
            func.count(DaireSakin.kayit_no).label("sayi"),
        )
        .join(Blok, Blok.blok_no == Daire.blok_no)
        .join(DaireSakin, DaireSakin.daire_no == Daire.daire_no)
        .where(
            Daire.site_no == site_no,
            DaireSakin.cikis_tarihi.is_(None),
        )
        .group_by(Daire.daire_no, Blok.blok_adi, Daire.daire_numarasi)
        .order_by(func.count(DaireSakin.kayit_no).desc())
        .limit(1)
    )
    kalabalik_row = kalabalik_sonuc.first()
    en_kalabalik = None
    en_kalabalik_sayi = 0
    if kalabalik_row:
        en_kalabalik = f"{kalabalik_row[1]} - Daire {kalabalik_row[2]}"
        en_kalabalik_sayi = int(kalabalik_row[3] or 0)

    return {
        "site_no": site.site_no,
        "toplam_aktif": toplam_aktif,
        "toplam_malik": toplam_malik,
        "toplam_kiraci": toplam_kiraci,
        "toplam_gecmis": toplam_gecmis,
        "daire_basina_ortalama_sakin": round(ortalama, 2),
        "en_kalabalik_daire": en_kalabalik,
        "en_kalabalik_sayi": en_kalabalik_sayi,
    }