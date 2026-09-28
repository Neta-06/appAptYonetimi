"""Anket HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.anket import (
    AnketCreateRequest,
    AnketDetayResponse,
    AnketOzetResponse,
    AnketSonucResponse,
    AnketUpdateRequest,
    OyKullanRequest,
    OyKullanSonuc,
)
from app.schemas.auth import MesajResponse
from app.services import anket_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/anketler", tags=["Anket Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


@router.get("", response_model=list[AnketOzetResponse])
async def list_anketler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    aktif_only: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AnketOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await anket_service.list_anketler(
        db, s, kullanici.kullanici_no,
        aktif_only=aktif_only,
        limit=limit,
        offset=offset,
    )
    return [AnketOzetResponse(**k) for k in kayitlar]


@router.post("", response_model=AnketDetayResponse, status_code=status.HTTP_201_CREATED)
async def create_anket(
    data: AnketCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> AnketDetayResponse:
    s = await _require_site(site_no)
    anket = await anket_service.create_anket(
        db, s,
        soru=data.soru,
        aciklama=data.aciklama,
        baslangic_tarihi=data.baslangic_tarihi,
        bitis_tarihi=data.bitis_tarihi,
        secenekler=data.secenekler,
        olusturan_no=kullanici.kullanici_no,
        oy_hakki_kullanicilar=data.oy_hakki_kullanicilar,
    )
    detay = await anket_service.get_anket(db, anket.anket_no, s, kullanici.kullanici_no)
    return AnketDetayResponse(**detay)


@router.get("/{anket_no}", response_model=AnketDetayResponse)
async def get_anket(
    anket_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> AnketDetayResponse:
    s = await _require_site(site_no)
    detay = await anket_service.get_anket(db, anket_no, s, kullanici.kullanici_no)
    return AnketDetayResponse(**detay)


@router.patch("/{anket_no}", response_model=AnketDetayResponse)
async def update_anket(
    anket_no: int,
    data: AnketUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> AnketDetayResponse:
    s = await _require_site(site_no)
    await anket_service.update_anket(
        db, anket_no, s,
        soru=data.soru,
        aciklama=data.aciklama,
        baslangic_tarihi=data.baslangic_tarihi,
        bitis_tarihi=data.bitis_tarihi,
        aktif_mi=data.aktif_mi,
    )
    detay = await anket_service.get_anket(db, anket_no, s, kullanici.kullanici_no)
    return AnketDetayResponse(**detay)


@router.delete("/{anket_no}", response_model=MesajResponse)
async def delete_anket(
    anket_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await anket_service.delete_anket(db, anket_no, s)
    return MesajResponse(mesaj="Anket silindi.")


@router.post("/{anket_no}/oy", response_model=OyKullanSonuc)
async def oy_kullan(
    anket_no: int,
    data: OyKullanRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> OyKullanSonuc:
    s = await _require_site(site_no)
    sonuc = await anket_service.oy_kullan(
        db, anket_no, s, kullanici.kullanici_no,
        secenek_no=data.secenek_no,
    )
    return OyKullanSonuc(**sonuc)


@router.get("/{anket_no}/sonuclar", response_model=AnketSonucResponse)
async def get_sonuclar(
    anket_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> AnketSonucResponse:
    s = await _require_site(site_no)
    sonuc = await anket_service.get_sonuclar(db, anket_no, s)
    return AnketSonucResponse(**sonuc)