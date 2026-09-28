"""Sakin HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.sakin import (
    SakinCikisRequest,
    SakinCikisSonuc,
    SakinCreateRequest,
    SakinDetayResponse,
    SakinOzetResponse,
    SakinOzetStats,
    SakinResponse,
    SakinTasindiRequest,
    SakinTasindiSonuc,
    SakinUpdateRequest,
)
from app.services import sakin_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sakinler", tags=["Sakin Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# ÖZET (statik — {kayit_no}'dan önce)
# ============================================================
@router.get("/ozet", response_model=SakinOzetStats)
async def get_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SakinOzetStats:
    s = await _require_site(site_no)
    veri = await sakin_service.get_ozet(db, s)
    return SakinOzetStats(**veri)


# ============================================================
# DAİRE SAKİNLERİ (statik prefix)
# ============================================================
@router.get("/daire/{daire_no}", response_model=list[SakinOzetResponse])
async def list_daire_sakinleri(
    daire_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[SakinOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await sakin_service.list_daire_sakinleri(db, s, daire_no)
    return [SakinOzetResponse(**k) for k in kayitlar]


# ============================================================
# LİSTE
# ============================================================
@router.get("", response_model=list[SakinOzetResponse])
async def list_sakinler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    aktif_only: Annotated[bool, Query()] = True,
    mulk_sahibi_mi: Annotated[bool | None, Query()] = None,
    daire_no: Annotated[int | None, Query(ge=1)] = None,
    arama: Annotated[str | None, Query(min_length=2, max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SakinOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await sakin_service.list_sakinler(
        db, s,
        aktif_only=aktif_only,
        mulk_sahibi_mi=mulk_sahibi_mi,
        daire_no=daire_no,
        arama=arama,
        limit=limit,
        offset=offset,
    )
    return [SakinOzetResponse(**k) for k in kayitlar]


@router.post(
    "",
    response_model=SakinDetayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sakin(
    data: SakinCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SakinDetayResponse:
    s = await _require_site(site_no)
    kayit = await sakin_service.create_sakin(
        db, s,
        daire_no=data.daire_no,
        kullanici_no=data.kullanici_no,
        mulk_sahibi_mi=data.mulk_sahibi_mi,
        giris_tarihi=data.giris_tarihi,
        kullanici_site_rolu=data.kullanici_site_rolu,
        kullanici_site_olustur=data.kullanici_site_olustur,
    )
    detay = await sakin_service.get_sakin(db, kayit.kayit_no, s)
    return SakinDetayResponse(**detay)


# ============================================================
# DETAY / GÜNCELLE
# ============================================================
@router.get("/{kayit_no}", response_model=SakinDetayResponse)
async def get_sakin(
    kayit_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SakinDetayResponse:
    s = await _require_site(site_no)
    veri = await sakin_service.get_sakin(db, kayit_no, s)
    return SakinDetayResponse(**veri)


@router.patch("/{kayit_no}", response_model=SakinResponse)
async def update_sakin(
    kayit_no: int,
    data: SakinUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SakinResponse:
    s = await _require_site(site_no)
    kayit = await sakin_service.update_sakin(
        db, kayit_no, s,
        mulk_sahibi_mi=data.mulk_sahibi_mi,
        giris_tarihi=data.giris_tarihi,
        cikis_tarihi=data.cikis_tarihi,
    )
    return SakinResponse.model_validate(kayit)


# ============================================================
# ÇIKIŞ
# ============================================================
@router.post("/{kayit_no}/cikis", response_model=SakinCikisSonuc)
async def cikis_yap(
    kayit_no: int,
    data: SakinCikisRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SakinCikisSonuc:
    s = await _require_site(site_no)
    sonuc = await sakin_service.cikis_yap(
        db, kayit_no, s,
        cikis_tarihi=data.cikis_tarihi,
    )
    return SakinCikisSonuc(**sonuc)


# ============================================================
# TAŞINMA
# ============================================================
@router.post("/{kayit_no}/tasindi", response_model=SakinTasindiSonuc)
async def tasindi_yap(
    kayit_no: int,
    data: SakinTasindiRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SakinTasindiSonuc:
    s = await _require_site(site_no)
    sonuc = await sakin_service.tasindi_yap(
        db, kayit_no, s,
        yeni_daire_no=data.yeni_daire_no,
        tasinma_tarihi=data.tasinma_tarihi,
        mulk_sahibi_mi=data.mulk_sahibi_mi,
    )
    return SakinTasindiSonuc(**sonuc)