"""Sayaç HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.auth import MesajResponse
from app.schemas.sayac import (
    DaireSayaciCreateRequest,
    DaireSayaciOzetResponse,
    DaireSayaciResponse,
    DaireSayaciUpdateRequest,
    SayacBirimResponse,
    SayacFaturasiCreateRequest,
    SayacFaturasiOzetResponse,
    SayacFaturasiResponse,
    SayacGenelOzet,
    SayacOkumaCreateRequest,
    SayacOkumaOzetResponse,
    SayacOkumaResponse,
    SayacTuruResponse,
)
from app.services import sayac_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sayaclar", tags=["Sayac Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# LOOKUP
# ============================================================
@router.get("/birimler", response_model=list[SayacBirimResponse])
async def list_birimler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SayacBirimResponse]:
    kayitlar = await sayac_service.list_birimler(db)
    return [SayacBirimResponse(**k) for k in kayitlar]


@router.get("/turler", response_model=list[SayacTuruResponse])
async def list_turler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SayacTuruResponse]:
    kayitlar = await sayac_service.list_sayac_turleri(db)
    return [SayacTuruResponse(**k) for k in kayitlar]


# ============================================================
# ÖZET (dinamik yollardan önce)
# ============================================================
@router.get("/ozet", response_model=SayacGenelOzet)
async def get_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SayacGenelOzet:
    s = await _require_site(site_no)
    veri = await sayac_service.get_ozet(db, s)
    return SayacGenelOzet(**veri)


# ============================================================
# FATURA (statik — {sayac_no}'dan önce)
# ============================================================
@router.get("/faturalar", response_model=list[SayacFaturasiOzetResponse])
async def list_faturalar(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    sayac_turu_no: Annotated[int | None, Query(ge=1)] = None,
    donem_yil: Annotated[int | None, Query(ge=2020, le=2100)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[SayacFaturasiOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await sayac_service.list_faturalar(
        db, s,
        sayac_turu_no=sayac_turu_no,
        donem_yil=donem_yil,
        limit=limit,
    )
    return [SayacFaturasiOzetResponse(**k) for k in kayitlar]


@router.post(
    "/faturalar",
    response_model=SayacFaturasiResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_fatura(
    data: SayacFaturasiCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SayacFaturasiResponse:
    s = await _require_site(site_no)
    fatura = await sayac_service.create_fatura(
        db, s,
        sayac_turu_no=data.sayac_turu_no,
        donem_yil=data.donem_yil,
        donem_ay=data.donem_ay,
        toplam_tutar=data.toplam_tutar,
        ortak_alan_tutar=data.ortak_alan_tutar,
        dagitim_sekli=data.dagitim_sekli,
    )
    detay = await sayac_service.get_fatura(db, fatura.fatura_no, s)
    return SayacFaturasiResponse(**detay)


@router.get("/faturalar/{fatura_no}", response_model=SayacFaturasiResponse)
async def get_fatura(
    fatura_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SayacFaturasiResponse:
    s = await _require_site(site_no)
    detay = await sayac_service.get_fatura(db, fatura_no, s)
    return SayacFaturasiResponse(**detay)


@router.delete("/faturalar/{fatura_no}", response_model=MesajResponse)
async def delete_fatura(
    fatura_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await sayac_service.delete_fatura(db, fatura_no, s)
    return MesajResponse(mesaj="Fatura silindi.")


# ============================================================
# OKUMA SİLME (statik prefix)
# ============================================================
@router.delete("/okuma/{okuma_no}", response_model=MesajResponse)
async def delete_okuma(
    okuma_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await sayac_service.delete_okuma(db, okuma_no, s)
    return MesajResponse(mesaj="Okuma silindi.")


# ============================================================
# DAİRE SAYAÇLARI
# ============================================================
@router.get("/daire/{daire_no}", response_model=list[DaireSayaciOzetResponse])
async def list_daire_sayaclari(
    daire_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[DaireSayaciOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await sayac_service.list_daire_sayaclari(db, s, daire_no)
    return [DaireSayaciOzetResponse(**k) for k in kayitlar]


@router.post(
    "/daire/{daire_no}",
    response_model=DaireSayaciResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_daire_sayaci(
    daire_no: int,
    data: DaireSayaciCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DaireSayaciResponse:
    s = await _require_site(site_no)
    sayac = await sayac_service.create_daire_sayaci(
        db, s, daire_no,
        sayac_turu_no=data.sayac_turu_no,
        seri_no=data.seri_no,
        montaj_tarihi=data.montaj_tarihi,
        ilk_deger=data.ilk_deger,
    )
    return DaireSayaciResponse.model_validate(sayac)


# ============================================================
# SAYAÇ DETAY / GÜNCELLE
# ============================================================
@router.get("/{sayac_no}", response_model=DaireSayaciOzetResponse)
async def get_daire_sayaci(
    sayac_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DaireSayaciOzetResponse:
    s = await _require_site(site_no)
    veri = await sayac_service.get_daire_sayaci(db, sayac_no, s)
    return DaireSayaciOzetResponse(**veri)


@router.patch("/{sayac_no}", response_model=DaireSayaciResponse)
async def update_daire_sayaci(
    sayac_no: int,
    data: DaireSayaciUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DaireSayaciResponse:
    s = await _require_site(site_no)
    sayac = await sayac_service.update_daire_sayaci(
        db, sayac_no, s,
        seri_no=data.seri_no,
        montaj_tarihi=data.montaj_tarihi,
        sokulme_tarihi=data.sokulme_tarihi,
        aktif_mi=data.aktif_mi,
    )
    return DaireSayaciResponse.model_validate(sayac)


# ============================================================
# OKUMA (sayaç altında)
# ============================================================
@router.get("/{sayac_no}/okumalar", response_model=list[SayacOkumaOzetResponse])
async def list_okumalar(
    sayac_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[SayacOkumaOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await sayac_service.list_okumalar(db, sayac_no, s, limit=limit)
    return [SayacOkumaOzetResponse(**k) for k in kayitlar]


@router.post(
    "/{sayac_no}/okuma",
    response_model=SayacOkumaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_okuma(
    sayac_no: int,
    data: SayacOkumaCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> SayacOkumaResponse:
    s = await _require_site(site_no)
    okuma = await sayac_service.create_okuma(
        db, sayac_no, s,
        okuma_tarihi=data.okuma_tarihi,
        guncel_deger=data.guncel_deger,
        okuyan_no=kullanici.kullanici_no,
    )
    return SayacOkumaResponse.model_validate(okuma)