"""Gider ve gelir HTTP endpoint'leri."""

import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.auth import MesajResponse
from app.schemas.gider import (
    CariHesapOzetResponse,
    GelirCreateRequest,
    GelirResponse,
    GelirUpdateRequest,
    GiderAylikOzet,
    GiderCreateRequest,
    GiderGenelOzet,
    GiderKalemiResponse,
    GiderKarsilastirmaOzet,
    GiderKategoriOzet,
    GiderKategoriResponse,
    GiderOzetResponse,
    GiderResponse,
    GiderUpdateRequest,
)
from app.services import gider_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/giderler", tags=["Gider Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# LOOKUP ENDPOINT'LERI
# ============================================================
@router.get(
    "/kategoriler",
    response_model=list[GiderKategoriResponse],
    summary="Gider kategorileri",
)
async def list_kategoriler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[GiderKategoriResponse]:
    kayitlar = await gider_service.list_kategoriler(db)
    return [GiderKategoriResponse(**k) for k in kayitlar]


@router.get(
    "/kalemler",
    response_model=list[GiderKalemiResponse],
    summary="Gider kalemleri",
)
async def list_kalemler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    kategori_no: Annotated[int | None, Query(ge=1)] = None,
) -> list[GiderKalemiResponse]:
    kayitlar = await gider_service.list_kalemler(db, kategori_no)
    return [GiderKalemiResponse(**k) for k in kayitlar]


@router.get(
    "/cariler",
    response_model=list[CariHesapOzetResponse],
    summary="Site carileri",
)
async def list_cariler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[CariHesapOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await gider_service.list_cariler(db, s)
    return [CariHesapOzetResponse(**k) for k in kayitlar]


# ============================================================
# ÖZET ENDPOINT'LERİ
# ============================================================
@router.get(
    "/ozet",
    response_model=GiderGenelOzet,
    summary="Gider genel özet",
)
async def get_genel_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    tarih_baslangic: Annotated[date | None, Query()] = None,
    tarih_bitis: Annotated[date | None, Query()] = None,
) -> GiderGenelOzet:
    s = await _require_site(site_no)
    ozet = await gider_service.get_genel_ozet(
        db, s, tarih_baslangic=tarih_baslangic, tarih_bitis=tarih_bitis
    )
    return GiderGenelOzet(**ozet)


@router.get(
    "/ozet/kategori",
    response_model=list[GiderKategoriOzet],
    summary="Kategori bazlı gider özeti",
)
async def get_kategori_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    tarih_baslangic: Annotated[date | None, Query()] = None,
    tarih_bitis: Annotated[date | None, Query()] = None,
) -> list[GiderKategoriOzet]:
    s = await _require_site(site_no)
    kayitlar = await gider_service.get_kategori_ozet(
        db, s, tarih_baslangic=tarih_baslangic, tarih_bitis=tarih_bitis
    )
    return [GiderKategoriOzet(**k) for k in kayitlar]


@router.get(
    "/ozet/aylik",
    response_model=list[GiderAylikOzet],
    summary="Aylık gider trendi",
)
async def get_aylik_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    yil: Annotated[int | None, Query(ge=2020, le=2100)] = None,
) -> list[GiderAylikOzet]:
    s = await _require_site(site_no)
    kayitlar = await gider_service.get_aylik_ozet(db, s, yil=yil)
    return [GiderAylikOzet(**k) for k in kayitlar]


@router.get(
    "/ozet/karsilastirma",
    response_model=GiderKarsilastirmaOzet,
    summary="Aylık gider-gelir karşılaştırma",
)
async def get_karsilastirma(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    yil: Annotated[int, Query(ge=2020, le=2100)],
    ay: Annotated[int, Query(ge=1, le=12)],
) -> GiderKarsilastirmaOzet:
    s = await _require_site(site_no)
    sonuc = await gider_service.get_karsilastirma(db, s, yil=yil, ay=ay)
    return GiderKarsilastirmaOzet(**sonuc)


# ============================================================
# GİDER CRUD
# ============================================================
@router.get(
    "",
    response_model=list[GiderOzetResponse],
    summary="Gider listesi",
)
async def list_giderler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    kategori_no: Annotated[int | None, Query(ge=1)] = None,
    kalem_no: Annotated[int | None, Query(ge=1)] = None,
    cari_no: Annotated[int | None, Query(ge=1)] = None,
    tarih_baslangic: Annotated[date | None, Query()] = None,
    tarih_bitis: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[GiderOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await gider_service.list_giderler(
        db, s,
        kategori_no=kategori_no,
        kalem_no=kalem_no,
        cari_no=cari_no,
        tarih_baslangic=tarih_baslangic,
        tarih_bitis=tarih_bitis,
        limit=limit,
        offset=offset,
    )
    return [GiderOzetResponse(**k) for k in kayitlar]


@router.post(
    "",
    response_model=GiderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni gider kaydı",
)
async def create_gider(
    data: GiderCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> GiderResponse:
    s = await _require_site(site_no)
    gider = await gider_service.create_gider(
        db, s,
        kalem_no=data.kalem_no,
        tutar=data.tutar,
        gider_tarihi=data.gider_tarihi,
        kaydeden_no=kullanici.kullanici_no,
        cari_no=data.cari_no,
        kdv_tutar=data.kdv_tutar,
        belge_no=data.belge_no,
        aciklama=data.aciklama,
    )
    return GiderResponse.model_validate(gider)


@router.get(
    "/{gider_no}",
    response_model=GiderResponse,
    summary="Gider detayı",
)
async def get_gider(
    gider_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> GiderResponse:
    s = await _require_site(site_no)
    gider = await gider_service.get_gider(db, gider_no, s)
    return GiderResponse.model_validate(gider)


@router.patch(
    "/{gider_no}",
    response_model=GiderResponse,
    summary="Gider güncelle",
)
async def update_gider(
    gider_no: int,
    data: GiderUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> GiderResponse:
    s = await _require_site(site_no)
    gider = await gider_service.update_gider(
        db, gider_no, s,
        kalem_no=data.kalem_no,
        cari_no=data.cari_no,
        tutar=data.tutar,
        kdv_tutar=data.kdv_tutar,
        gider_tarihi=data.gider_tarihi,
        belge_no=data.belge_no,
        aciklama=data.aciklama,
    )
    return GiderResponse.model_validate(gider)


@router.delete(
    "/{gider_no}",
    response_model=MesajResponse,
    summary="Gider sil",
)
async def delete_gider(
    gider_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await gider_service.delete_gider(db, gider_no, s)
    return MesajResponse(mesaj="Gider silindi.")


# ============================================================
# GELİR ENDPOINT'LERİ
# ============================================================
gelir_router = APIRouter(prefix="/gelirler", tags=["Gelir Yonetimi"])


@gelir_router.get("", response_model=list[GelirResponse])
async def list_gelirler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    tarih_baslangic: Annotated[date | None, Query()] = None,
    tarih_bitis: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[GelirResponse]:
    s = await _require_site(site_no)
    kayitlar = await gider_service.list_gelirler(
        db, s,
        tarih_baslangic=tarih_baslangic,
        tarih_bitis=tarih_bitis,
        limit=limit,
        offset=offset,
    )
    return [GelirResponse(**k) for k in kayitlar]


@gelir_router.post("", response_model=GelirResponse, status_code=status.HTTP_201_CREATED)
async def create_gelir(
    data: GelirCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> GelirResponse:
    s = await _require_site(site_no)
    gelir = await gider_service.create_gelir(
        db, s,
        kaynak=data.kaynak,
        tutar=data.tutar,
        gelir_tarihi=data.gelir_tarihi,
        kaydeden_no=kullanici.kullanici_no,
        aciklama=data.aciklama,
    )
    return GelirResponse.model_validate(gelir)


@gelir_router.get("/{gelir_no}", response_model=GelirResponse)
async def get_gelir(
    gelir_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> GelirResponse:
    s = await _require_site(site_no)
    gelir = await gider_service.get_gelir(db, gelir_no, s)
    return GelirResponse.model_validate(gelir)


@gelir_router.patch("/{gelir_no}", response_model=GelirResponse)
async def update_gelir(
    gelir_no: int,
    data: GelirUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> GelirResponse:
    s = await _require_site(site_no)
    gelir = await gider_service.update_gelir(
        db, gelir_no, s,
        kaynak=data.kaynak,
        tutar=data.tutar,
        gelir_tarihi=data.gelir_tarihi,
        aciklama=data.aciklama,
    )
    return GelirResponse.model_validate(gelir)


@gelir_router.delete("/{gelir_no}", response_model=MesajResponse)
async def delete_gelir(
    gelir_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await gider_service.delete_gelir(db, gelir_no, s)
    return MesajResponse(mesaj="Gelir silindi.")