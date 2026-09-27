"""
Site yönetimi iş mantığı.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BulunamadiHatasi, SiteErisimYokHatasi
from app.models import Kullanici, KullaniciSite, Rol, Site, SiteTipi

logger = logging.getLogger(__name__)


# ============================================================
# Kullanıcının üye olduğu siteler
# ============================================================
async def list_user_sites(
    db: AsyncSession,
    kullanici_no: int,
) -> list[dict]:
    """
    Kullanıcının aktif üyeliklerini site + rol bilgisiyle döner.
    """
    sonuc = await db.execute(
        select(KullaniciSite, Site, SiteTipi, Rol)
        .join(Site, Site.site_no == KullaniciSite.site_no)
        .join(SiteTipi, SiteTipi.tip_no == Site.site_tipi_no)
        .join(Rol, Rol.rol_no == KullaniciSite.rol_no)
        .where(
            KullaniciSite.kullanici_no == kullanici_no,
            KullaniciSite.aktif_mi.is_(True),
            Site.aktif_mi.is_(True),
        )
        .order_by(Site.site_adi)
    )
    uyelikler = []
    for ks, site, tip, rol in sonuc.all():
        uyelikler.append({
            "site_no": site.site_no,
            "site_adi": site.site_adi,
            "site_tipi": tip.ad,
            "il": site.il,
            "ilce": site.ilce,
            "rol_no": rol.rol_no,
            "rol_adi": rol.ad,
            "aktif_mi": ks.aktif_mi,
        })
    return uyelikler


# ============================================================
# Kullanıcının bir siteye erişimi var mı?
# ============================================================
async def get_user_site_membership(
    db: AsyncSession,
    kullanici_no: int,
    site_no: int,
) -> KullaniciSite | None:
    """Kullanıcının bu sitedeki aktif üyeliğini döner (yoksa None)."""
    sonuc = await db.execute(
        select(KullaniciSite).where(
            KullaniciSite.kullanici_no == kullanici_no,
            KullaniciSite.site_no == site_no,
            KullaniciSite.aktif_mi.is_(True),
        )
    )
    return sonuc.scalar_one_or_none()


# ============================================================
# Site detay
# ============================================================
async def get_site(
    db: AsyncSession,
    site_no: int,
    *,
    kullanici_no: int,
) -> Site:
    """
    Site detayını döner. Önce kullanıcının erişimini kontrol eder.
    """
    uyelik = await get_user_site_membership(db, kullanici_no, site_no)
    if uyelik is None:
        raise SiteErisimYokHatasi(f"Site {site_no} icin uyeligi yok.")

    site = await db.get(Site, site_no)
    if site is None or not site.aktif_mi:
        raise BulunamadiHatasi("Site", kaynak_id=site_no)
    return site


# ============================================================
# Site üyeleri
# ============================================================
async def list_site_members(
    db: AsyncSession,
    site_no: int,
    *,
    kullanici_no: int,
) -> list[dict]:
    """
    Sitenin tüm üyelerini (kullanıcı + rol) döner.
    Yalnızca o siteye üye kullanıcılar erişebilir.
    """
    # Erişim kontrolü
    uyelik = await get_user_site_membership(db, kullanici_no, site_no)
    if uyelik is None:
        raise SiteErisimYokHatasi(f"Site {site_no} icin uyeligi yok.")

    sonuc = await db.execute(
        select(KullaniciSite, Kullanici, Rol)
        .join(Kullanici, Kullanici.kullanici_no == KullaniciSite.kullanici_no)
        .join(Rol, Rol.rol_no == KullaniciSite.rol_no)
        .where(KullaniciSite.site_no == site_no)
        .order_by(Rol.ad, Kullanici.ad)
    )

    uyeler = []
    for ks, k, rol in sonuc.all():
        uyeler.append({
            "kullanici_no": k.kullanici_no,
            "ad": k.ad,
            "soyad": k.soyad,
            "e_posta": k.e_posta,
            "rol_no": rol.rol_no,
            "rol_adi": rol.ad,
            "baslangic_tarihi": ks.baslangic_tarihi,
            "bitis_tarihi": ks.bitis_tarihi,
            "aktif_mi": ks.aktif_mi,
        })
    return uyeler


# ============================================================
# Aktif site bilgisi + yetkiler
# ============================================================
async def get_active_site_info(
    db: AsyncSession,
    kullanici_no: int,
    site_no: int,
) -> dict:
    """
    X-Site-Id ile gelen aktif site için:
      - site bilgisi
      - kullanıcının rolü
      - kullanıcının yetki kodları listesi

    GÜVENLİK: Önce kullanıcının erişimini kontrol eder.
    Erişim yoksa 403 döner — site var mı yok mu bilgisi sızdırılmaz.
    """
    from app.models import RolYetki, Yetki

    # 1) ÖNCE erişim kontrolü
    uyelik_sonuc = await db.execute(
        select(KullaniciSite, Rol)
        .join(Rol, Rol.rol_no == KullaniciSite.rol_no)
        .where(
            KullaniciSite.kullanici_no == kullanici_no,
            KullaniciSite.site_no == site_no,
            KullaniciSite.aktif_mi.is_(True),
        )
    )
    uyelik_row = uyelik_sonuc.first()
    if uyelik_row is None:
        raise SiteErisimYokHatasi(f"Site {site_no} icin uyeligi yok.")

    uyelik, rol = uyelik_row

    # 2) SONRA site bilgisi (artık var olduğu kesin)
    sonuc = await db.execute(
        select(Site, SiteTipi).join(SiteTipi, SiteTipi.tip_no == Site.site_tipi_no)
        .where(Site.site_no == site_no)
    )
    row = sonuc.first()
    if row is None:
        # Teorik olarak buraya düşmemeli (üyelik var ama site yok = veri tutarsızlığı)
        raise SiteErisimYokHatasi(f"Site {site_no} icin uyeligi yok.")
    site, tip = row

    # 3) Yetkiler
    yetki_sonuc = await db.execute(
        select(Yetki.kod)
        .join(RolYetki, RolYetki.yetki_no == Yetki.yetki_no)
        .where(RolYetki.rol_no == rol.rol_no)
    )
    yetkiler = [row[0] for row in yetki_sonuc.all()]

    return {
        "site_no": site.site_no,
        "site_adi": site.site_adi,
        "site_tipi": tip.ad,
        "rol_adi": rol.ad,
        "yetkiler": yetkiler,
    }