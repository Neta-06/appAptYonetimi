"""Rapor HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.rapor import (
    AidatDurumResponse,
    BorcluDairelerResponse,
    DashboardResponse,
    DaireDolulukResponse,
    FinansalOzetResponse,
    GiderDagilimResponse,
    TrendResponse,
)
from app.services import rapor_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/raporlar", tags=["Raporlar"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DashboardResponse:
    s = await _require_site(site_no)
    veri = await rapor_service.get_dashboard(db, s)
    return DashboardResponse(**veri)


@router.get("/finansal-ozet", response_model=FinansalOzetResponse)
async def get_finansal_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    yil: Annotated[int, Query(ge=2020, le=2100)],
    ay: Annotated[int, Query(ge=1, le=12)],
) -> FinansalOzetResponse:
    s = await _require_site(site_no)
    veri = await rapor_service.get_finansal_ozet(db, s, yil=yil, ay=ay)
    return FinansalOzetResponse(**veri)


@router.get("/aidat-durumu", response_model=AidatDurumResponse)
async def get_aidat_durumu(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> AidatDurumResponse:
    s = await _require_site(site_no)
    veri = await rapor_service.get_aidat_durumu(db, s)
    return AidatDurumResponse(**veri)


@router.get("/gider-dagilim", response_model=GiderDagilimResponse)
async def get_gider_dagilim(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> GiderDagilimResponse:
    s = await _require_site(site_no)
    veri = await rapor_service.get_gider_dagilim(db, s)
    return GiderDagilimResponse(**veri)


@router.get("/daire-doluluk", response_model=DaireDolulukResponse)
async def get_daire_doluluk(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DaireDolulukResponse:
    s = await _require_site(site_no)
    veri = await rapor_service.get_daire_doluluk(db, s)
    return DaireDolulukResponse(**veri)


@router.get("/borclu-daireler", response_model=BorcluDairelerResponse)
async def get_borclu_daireler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> BorcluDairelerResponse:
    s = await _require_site(site_no)
    veri = await rapor_service.get_borclu_daireler(db, s, limit=limit)
    return BorcluDairelerResponse(**veri)


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    ay_sayisi: Annotated[int, Query(ge=1, le=36)] = 12,
) -> TrendResponse:
    s = await _require_site(site_no)
    veri = await rapor_service.get_trend(db, s, ay_sayisi=ay_sayisi)
    return TrendResponse(**veri)