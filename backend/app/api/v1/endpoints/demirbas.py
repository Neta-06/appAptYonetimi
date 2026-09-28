"""Demirbaş HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.models import Demirbas
from app.schemas.auth import MesajResponse
from app.schemas.demirbas import (
    DemirbasCreateRequest,
    DemirbasDetayResponse,
    DemirbasDurumDegistirRequest,
    DemirbasHareketResponse,
    DemirbasOzetResponse,
    DemirbasOzetStats,
    DemirbasResponse,
    DemirbasUpdateRequest,
    HareketEkleRequest,
)
from app.services import demirbas_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demirbaslar", tags=["Demirbas Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# ÖZET ve KATEGORİ (statik — {demirbas_no}'dan önce)
# ============================================================
@router.get("/ozet", response_model=DemirbasOzetStats)
async def get_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DemirbasOzetStats:
    s = await _require_site(site_no)
    veri = await demirbas_service.get_ozet(db, s)
    return DemirbasOzetStats(**veri)


@router.get("/kategoriler", response_model=list[str])
async def list_kategoriler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[str]:
    """Sitede kullanılan demirbaş kategorileri (distinct)."""
    s = await _require_site(site_no)
    sonuc = await db.execute(
        select(Demirbas.kategori)
        .distinct()
        .where(Demirbas.site_no == s, Demirbas.kategori.is_not(None))
        .order_by(Demirbas.kategori)
    )
    return [row[0] for row in sonuc.all()]


# ============================================================
# LİSTE
# ============================================================
@router.get("", response_model=list[DemirbasOzetResponse])
async def list_demirbaslar(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    kategori: Annotated[str | None, Query(max_length=50)] = None,
    durum: Annotated[str | None, Query(pattern="^(CALISIYOR|ARIZALI|HURDA)$")] = None,
    arama: Annotated[str | None, Query(min_length=2, max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DemirbasOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await demirbas_service.list_demirbaslar(
        db, s,
        kategori=kategori,
        durum=durum,
        arama=arama,
        limit=limit,
        offset=offset,
    )
    return [DemirbasOzetResponse(**k) for k in kayitlar]


# ============================================================
# YENİ
# ============================================================
@router.post(
    "",
    response_model=DemirbasDetayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_demirbas(
    data: DemirbasCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DemirbasDetayResponse:
    s = await _require_site(site_no)
    d = await demirbas_service.create_demirbas(
        db, s,
        ad=data.ad,
        adet=data.adet,
        kategori=data.kategori,
        alis_fiyati=data.alis_fiyati,
        alis_tarihi=data.alis_tarihi,
        bulundugu_yer=data.bulundugu_yer,
        durum=data.durum,
        olusturan_no=kullanici.kullanici_no,
    )
    detay = await demirbas_service.get_demirbas(db, d.demirbas_no, s)
    return DemirbasDetayResponse(**detay)


# ============================================================
# DETAY / GÜNCELLE / SİL
# ============================================================
@router.get("/{demirbas_no}", response_model=DemirbasDetayResponse)
async def get_demirbas(
    demirbas_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DemirbasDetayResponse:
    s = await _require_site(site_no)
    detay = await demirbas_service.get_demirbas(db, demirbas_no, s)
    return DemirbasDetayResponse(**detay)


@router.patch("/{demirbas_no}", response_model=DemirbasResponse)
async def update_demirbas(
    demirbas_no: int,
    data: DemirbasUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DemirbasResponse:
    s = await _require_site(site_no)
    d = await demirbas_service.update_demirbas(
        db, demirbas_no, s,
        ad=data.ad,
        kategori=data.kategori,
        adet=data.adet,
        alis_fiyati=data.alis_fiyati,
        alis_tarihi=data.alis_tarihi,
        bulundugu_yer=data.bulundugu_yer,
        durum=data.durum,
    )
    return DemirbasResponse.model_validate(d)


@router.delete("/{demirbas_no}", response_model=MesajResponse)
async def delete_demirbas(
    demirbas_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await demirbas_service.delete_demirbas(db, demirbas_no, s)
    return MesajResponse(mesaj="Demirbas silindi.")


# ============================================================
# DURUM DEĞİŞTİR
# ============================================================
@router.post("/{demirbas_no}/durum", response_model=DemirbasResponse)
async def durum_degistir(
    demirbas_no: int,
    data: DemirbasDurumDegistirRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DemirbasResponse:
    s = await _require_site(site_no)
    d = await demirbas_service.durum_degistir(
        db, demirbas_no, s,
        yeni_durum=data.durum,
        kullanici_no=kullanici.kullanici_no,
        aciklama=data.aciklama,
    )
    return DemirbasResponse.model_validate(d)


# ============================================================
# HAREKET
# ============================================================
@router.post(
    "/{demirbas_no}/hareket",
    response_model=DemirbasHareketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def hareket_ekle(
    demirbas_no: int,
    data: HareketEkleRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DemirbasHareketResponse:
    s = await _require_site(site_no)
    h = await demirbas_service.hareket_ekle(
        db, demirbas_no, s,
        hareket_tipi=data.hareket_tipi,
        kullanici_no=data.kullanici_no,
        aciklama=data.aciklama,
        maliyet=data.maliyet,
    )
    # Kullanıcı adını da doldur
    kullanici_ad = None
    if h.kullanici_no:
        from app.models import Kullanici
        k = await db.get(Kullanici, h.kullanici_no)
        if k:
            kullanici_ad = f"{k.ad} {k.soyad}"

    return DemirbasHareketResponse(
        hareket_no=h.hareket_no,
        demirbas_no=h.demirbas_no,
        hareket_tipi=h.hareket_tipi,
        kullanici_no=h.kullanici_no,
        kullanici_ad=kullanici_ad,
        tarih=h.tarih,
        aciklama=h.aciklama,
        maliyet=h.maliyet,
    )