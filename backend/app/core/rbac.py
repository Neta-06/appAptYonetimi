"""
Rol ve yetki tabanlı erişim kontrolü (RBAC).

FastAPI dependency'leri sağlar:
  - get_current_user     : JWT'den kullanıcıyı çıkarır
  - get_current_site     : Aktif site bilgisini çıkarır (X-Site-Id header)
  - require_yetki(kod)   : Belirli bir yetkiyi zorunlu kılar
  - require_rol(ad)      : Belirli bir rolü zorunlu kılar
  - require_site_erisim  : Kullanıcının siteye erişimini doğrular
"""

import logging
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    KimlikDogrulanmadiHatasi,
    PasifKullaniciHatasi,
    SiteErisimYokHatasi,
    TokenGecersizHatasi,
    TokenSuresiDolmusHatasi,
    YetkiYokHatasi,
)
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Kullanici, KullaniciSite, Rol, RolYetki, Yetki

logger = logging.getLogger(__name__)


# ============================================================
# HTTP Bearer şeması — Swagger UI'da kilit ikonu gösterir
# ============================================================
bearer_scheme = HTTPBearer(auto_error=False)


# ============================================================
# get_current_user — JWT'den kullanıcıyı çıkarır
# ============================================================
async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Kullanici:
    """
    Authorization header'indaki access token'dan kullanıcıyı yükler.

    Adımlar:
      1. Token var mı?
      2. Token imzası ve süresi geçerli mi?
      3. Kullanıcı veritabanında var mı?
      4. Kullanıcı aktif mi?
      5. Hesabı kilitli mi?
    """
    if credentials is None:
        raise KimlikDogrulanmadiHatasi(
            "Yetkilendirme basligi eksik. 'Authorization: Bearer <token>' gonderin."
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ExpiredSignatureError as exc:
        raise TokenSuresiDolmusHatasi() from exc
    except JWTError as exc:
        raise TokenGecersizHatasi() from exc

    kullanici_no_str = payload.get("sub")
    if not kullanici_no_str:
        raise TokenGecersizHatasi("Token icinde kullanici bilgisi yok.")

    try:
        kullanici_no = int(kullanici_no_str)
    except (TypeError, ValueError) as exc:
        raise TokenGecersizHatasi("Token icindeki kullanici kimligi gecersiz.") from exc

    sonuc = await db.execute(
        select(Kullanici).where(Kullanici.kullanici_no == kullanici_no)
    )
    kullanici = sonuc.scalar_one_or_none()

    if kullanici is None:
        raise KimlikDogrulanmadiHatasi("Kullanici bulunamadi.")

    if not kullanici.aktif_mi:
        raise PasifKullaniciHatasi()

    if kullanici.hesap_kilitli_mi:
        raise KimlikDogrulanmadiHatasi("Hesabiniz kilitli. Yonetime basvurun.")
    
      # Audit context'e kullanici bilgisini ekle
    from app.core.audit import get_audit_context, set_audit_context
    ctx = get_audit_context()
    ctx["kullanici_no"] = kullanici.kullanici_no
    set_audit_context(**ctx)

    return kullanici


# ============================================================
# Aktif site bağlamı
# ============================================================
async def get_current_site(
    db: Annotated[AsyncSession, Depends(get_db)],
    kullanici: Annotated[Kullanici, Depends(get_current_user)],
    x_site_id: Annotated[int | None, Header(alias="X-Site-Id")] = None,
) -> int | None:
    """
    Multi-tenant bağlam: kullanıcı hangi site adına işlem yapıyor?

    - Header'da 'X-Site-Id' varsa onu kullanır.
    - Yoksa ve kullanıcı yalnızca 1 siteye üyeyse onu otomatik seçer.
    - Yoksa ve kullanıcı birden çok siteye üyeyse hata verir.

    Yan etki: Audit context'e site_no ekler.
    """
    # --- İç mantık: aktif site numarasını bul ---
    sonuc = await db.execute(
        select(KullaniciSite).where(
            KullaniciSite.kullanici_no == kullanici.kullanici_no,
            KullaniciSite.aktif_mi.is_(True),
        )
    )
    uyelikler = list(sonuc.scalars().all())

    secilen_site: int | None = None

    if not uyelikler:
        secilen_site = None
    elif x_site_id is not None:
        for u in uyelikler:
            if u.site_no == x_site_id:
                secilen_site = x_site_id
                break
        else:
            raise SiteErisimYokHatasi(f"Site {x_site_id} icin uyeligi yok.")
    elif len(uyelikler) == 1:
        secilen_site = uyelikler[0].site_no
    else:
        raise SiteErisimYokHatasi(
            "Birden fazla siteye uyesiniz. 'X-Site-Id' basligini gonderin."
        )

    # --- Audit context'e site bilgisini ekle (tek noktada) ---
    if secilen_site is not None:
        from app.core.audit import get_audit_context, set_audit_context

        ctx = get_audit_context()
        ctx["site_no"] = secilen_site
        set_audit_context(**ctx)

    return secilen_site
# ============================================================
# require_yetki — Belirli yetkiyi zorunlu kılar
# ============================================================
def require_yetki(yetki_kodu: str):
    """
    Belirli bir yetki kodunu zorunlu kılan dependency factory.

    Kullanım:
        @router.delete("/aidat/{aidat_no}")
        async def sil(
            aidat_no: int,
            user: Kullanici = Depends(require_yetki("aidat.sil")),
        ):
            ...

    Mantık:
      1. Kullanıcının aktif site üyeliğini bul.
      2. Üyeliğindeki rolün yetkilerini yükle.
      3. Aranan yetki kodunu kontrol et.
    """
    async def _kontrol(
        db: Annotated[AsyncSession, Depends(get_db)],
        kullanici: Annotated[Kullanici, Depends(get_current_user)],
        site_no: Annotated[int | None, Depends(get_current_site)],
    ) -> Kullanici:
        if site_no is None:
            # Site gerektirmeyen yetkiler (örn: kendi profilini düzenle)
            raise YetkiYokHatasi(
                f"'{yetki_kodu}' yetkisi icin aktif site gerekli."
            )

        # Kullanıcının bu sitedeki rolünü ve o rolün yetkilerini sorgula
        sonuc = await db.execute(
            select(Yetki.kod)
            .join(RolYetki, RolYetki.yetki_no == Yetki.yetki_no)
            .join(KullaniciSite, KullaniciSite.rol_no == RolYetki.rol_no)
            .where(
                KullaniciSite.kullanici_no == kullanici.kullanici_no,
                KullaniciSite.site_no == site_no,
                KullaniciSite.aktif_mi.is_(True),
            )
        )
        yetkiler = {row[0] for row in sonuc.all()}

        if yetki_kodu not in yetkiler:
            logger.warning(
                "Yetki reddi: kullanici=%s site=%s yetki=%s",
                kullanici.kullanici_no, site_no, yetki_kodu,
            )
            raise YetkiYokHatasi(f"'{yetki_kodu}' yetkisi gerekli.")

        return kullanici

    return _kontrol


# ============================================================
# require_rol — Belirli rolü zorunlu kılar
# ============================================================
def require_rol(*rol_adlari: str):
    """
    Belirli bir rolü (veya rollerden birini) zorunlu kılar.

    Kullanım:
        @router.get("/admin/rapor")
        async def rapor(
            user: Kullanici = Depends(require_rol("YONETICI", "MUHASEBECI")),
        ):
            ...
    """
    async def _kontrol(
        db: Annotated[AsyncSession, Depends(get_db)],
        kullanici: Annotated[Kullanici, Depends(get_current_user)],
        site_no: Annotated[int | None, Depends(get_current_site)],
    ) -> Kullanici:
        if site_no is None:
            raise YetkiYokHatasi("Aktif site gerekli.")

        sonuc = await db.execute(
            select(Rol.ad)
            .join(KullaniciSite, KullaniciSite.rol_no == Rol.rol_no)
            .where(
                KullaniciSite.kullanici_no == kullanici.kullanici_no,
                KullaniciSite.site_no == site_no,
                KullaniciSite.aktif_mi.is_(True),
            )
        )
        roller = {row[0] for row in sonuc.all()}

        if not roller.intersection(rol_adlari):
            raise YetkiYokHatasi(
                f"Bu islem icin su rollerden biri gerekli: {', '.join(rol_adlari)}"
            )

        return kullanici

    return _kontrol


# ============================================================
# Type alias'ları — endpoint imzalarını kısaltır
# ============================================================
CurrentUser = Annotated[Kullanici, Depends(get_current_user)]
CurrentSite = Annotated[int | None, Depends(get_current_site)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
