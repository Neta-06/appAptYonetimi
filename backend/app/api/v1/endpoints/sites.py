"""
Site yönetimi HTTP endpoint'leri.

Endpoint'ler:
  GET  /sites                    - Kullanıcının üye olduğu siteler
  GET  /sites/current            - X-Site-Id ile aktif site bilgisi
  GET  /sites/{site_no}          - Site detayı
  GET  /sites/{site_no}/uyeler   - Site üyeleri
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.site import (
    AktifSiteResponse,
    KullaniciSiteOzet,
    SiteResponse,
    SiteUyeResponse,
)
from app.services import site_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sites", tags=["Site Yonetimi"])


# ============================================================
# GET /sites — Kullanıcının üye olduğu siteler
# ============================================================
@router.get(
    "",
    response_model=list[KullaniciSiteOzet],
    summary="Üye olunan siteler",
    description=(
        "Giriş yapan kullanıcının aktif üye olduğu tüm siteleri listeler. "
        "Frontend bu listeyi site seçim ekranında kullanır."
    ),
)
async def list_sites(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[KullaniciSiteOzet]:
    uyelikler = await site_service.list_user_sites(db, kullanici.kullanici_no)
    return [KullaniciSiteOzet(**u) for u in uyelikler]


# ============================================================
# GET /sites/current — Aktif site bilgisi + yetkiler
# ============================================================
@router.get(
    "/current",
    response_model=AktifSiteResponse,
    summary="Aktif site bilgisi",
    description=(
        "X-Site-Id header'ı ile gelen aktif site için: "
        "site bilgisi + kullanıcının rolü + yetki kodları."
    ),
)
async def get_current_site_info(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_site_id: Annotated[int | None, Header(alias="X-Site-Id")] = None,
) -> AktifSiteResponse:
    from app.core.exceptions import IsKuraliHatasi

    if x_site_id is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")

    bilgi = await site_service.get_active_site_info(
        db, kullanici.kullanici_no, x_site_id
    )
    return AktifSiteResponse(**bilgi)


# ============================================================
# GET /sites/{site_no} — Site detayı
# ============================================================
@router.get(
    "/{site_no}",
    response_model=SiteResponse,
    summary="Site detayı",
    description="Kullanıcının üye olduğu bir sitenin detaylarını döner.",
)
async def get_site_detail(
    site_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SiteResponse:
    site = await site_service.get_site(
        db, site_no, kullanici_no=kullanici.kullanici_no
    )
    return SiteResponse.model_validate(site)


# ============================================================
# GET /sites/{site_no}/uyeler — Site üyeleri
# ============================================================
@router.get(
    "/{site_no}/uyeler",
    response_model=list[SiteUyeResponse],
    summary="Site üyeleri",
    description="Sitenin tüm üyelerini (kullanıcı + rol) listeler.",
)
async def list_site_members(
    site_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SiteUyeResponse]:
    uyeler = await site_service.list_site_members(
        db, site_no, kullanici_no=kullanici.kullanici_no
    )
    return [SiteUyeResponse(**u) for u in uyeler]
