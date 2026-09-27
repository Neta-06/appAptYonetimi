"""Daire yönetimi HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.daire import (
    BlokResponse,
    DaireOzetResponse,
    DaireResponse,
    DaireSakinResponse,
    DaireSayacResponse,
)
from app.services import daire_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daireler", tags=["Daire Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    """Site bağlamı zorunlu."""
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# GET /daireler — Sitedeki tüm daireler
# ============================================================
@router.get("", response_model=list[DaireOzetResponse])
async def list_daireler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[DaireOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await daire_service.list_daireler(db, s)
    return [DaireOzetResponse(**k) for k in kayitlar]


# ============================================================
# GET /daireler/bloklar — Sitedeki bloklar
# ============================================================
@router.get("/bloklar", response_model=list[BlokResponse])
async def list_bloklar(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[BlokResponse]:
    s = await _require_site(site_no)
    kayitlar = await daire_service.list_bloklar(db, s)
    return [BlokResponse(**k) for k in kayitlar]


# ============================================================
# GET /daireler/{daire_no} — Daire detayı
# ============================================================
@router.get("/{daire_no}", response_model=DaireResponse)
async def get_daire(
    daire_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DaireResponse:
    s = await _require_site(site_no)
    kayit = await daire_service.get_daire(db, daire_no, s)
    return DaireResponse(**kayit)


# ============================================================
# GET /daireler/{daire_no}/sakinler — Daire sakinleri
# ============================================================
@router.get("/{daire_no}/sakinler", response_model=list[DaireSakinResponse])
async def list_sakinler(
    daire_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[DaireSakinResponse]:
    s = await _require_site(site_no)
    kayitlar = await daire_service.list_sakinler(db, daire_no, s)
    return [DaireSakinResponse(**k) for k in kayitlar]


# ============================================================
# GET /daireler/{daire_no}/sayaclar — Daire sayaçları
# ============================================================
@router.get("/{daire_no}/sayaclar", response_model=list[DaireSayacResponse])
async def list_sayaclar(
    daire_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[DaireSayacResponse]:
    s = await _require_site(site_no)
    kayitlar = await daire_service.list_sayaclar(db, daire_no, s)
    return [DaireSayacResponse(**k) for k in kayitlar]