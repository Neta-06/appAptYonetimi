"""İş emri HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.auth import MesajResponse
from app.schemas.is_takip import (
    IsDurumResponse,
    IsEmriCreateRequest,
    IsEmriDetayResponse,
    IsEmriDurumDegistirRequest,
    IsEmriGenelOzet,
    IsEmriGuncellemeCreateRequest,
    IsEmriGuncellemeResponse,
    IsEmriMalzemeCreateRequest,
    IsEmriMalzemeResponse,
    IsOncelikResponse,
    IsEmriOzetResponse,
    IsEmriUpdateRequest,
)
from app.services import is_takip_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/is-emirleri", tags=["Is Emri Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# LOOKUP
# ============================================================
@router.get("/oncelikler", response_model=list[IsOncelikResponse])
async def list_oncelikler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[IsOncelikResponse]:
    kayitlar = await is_takip_service.list_oncelikler(db)
    return [IsOncelikResponse(**k) for k in kayitlar]


@router.get("/durumlar", response_model=list[IsDurumResponse])
async def list_durumlar(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[IsDurumResponse]:
    kayitlar = await is_takip_service.list_durumlar(db)
    return [IsDurumResponse(**k) for k in kayitlar]


# ============================================================
# ÖZET ve BENİM İŞLERİM (özel path — {is_no}'dan önce)
# ============================================================
@router.get("/ozet", response_model=IsEmriGenelOzet)
async def get_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> IsEmriGenelOzet:
    s = await _require_site(site_no)
    veri = await is_takip_service.get_ozet(db, s)
    return IsEmriGenelOzet(**veri)


@router.get("/benim", response_model=list[IsEmriOzetResponse])
async def list_benim_islerim(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    acik_only: Annotated[bool, Query()] = True,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[IsEmriOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await is_takip_service.list_benim_islerim(
        db, s, kullanici.kullanici_no,
        acik_only=acik_only,
        limit=limit,
    )
    return [IsEmriOzetResponse(**k) for k in kayitlar]


# ============================================================
# LİSTE
# ============================================================
@router.get("", response_model=list[IsEmriOzetResponse])
async def list_is_emirleri(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    durum_no: Annotated[int | None, Query(ge=1)] = None,
    oncelik_no: Annotated[int | None, Query(ge=1)] = None,
    atanan_no: Annotated[int | None, Query(ge=1)] = None,
    daire_no: Annotated[int | None, Query(ge=1)] = None,
    acik_only: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[IsEmriOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await is_takip_service.list_is_emirleri(
        db, s,
        durum_no=durum_no,
        oncelik_no=oncelik_no,
        atanan_no=atanan_no,
        daire_no=daire_no,
        acik_only=acik_only,
        limit=limit,
        offset=offset,
    )
    return [IsEmriOzetResponse(**k) for k in kayitlar]


@router.post(
    "",
    response_model=IsEmriDetayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_is_emri(
    data: IsEmriCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> IsEmriDetayResponse:
    s = await _require_site(site_no)
    is_emri = await is_takip_service.create_is_emri(
        db, s,
        baslik=data.baslik,
        aciklama=data.aciklama,
        acan_no=kullanici.kullanici_no,
        atanan_no=data.atanan_no,
        oncelik_no=data.oncelik_no,
        daire_no=data.daire_no,
        termin_tarihi=data.termin_tarihi,
    )
    detay = await is_takip_service.get_is_emri(db, is_emri.is_no, s)
    return IsEmriDetayResponse(**detay)


# ============================================================
# DETAY / GÜNCELLE / SİL
# ============================================================
@router.get("/{is_no}", response_model=IsEmriDetayResponse)
async def get_is_emri(
    is_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> IsEmriDetayResponse:
    s = await _require_site(site_no)
    veri = await is_takip_service.get_is_emri(db, is_no, s)
    return IsEmriDetayResponse(**veri)


@router.patch("/{is_no}", response_model=IsEmriDetayResponse)
async def update_is_emri(
    is_no: int,
    data: IsEmriUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> IsEmriDetayResponse:
    s = await _require_site(site_no)
    await is_takip_service.update_is_emri(
        db, is_no, s,
        baslik=data.baslik,
        aciklama=data.aciklama,
        daire_no=data.daire_no,
        atanan_no=data.atanan_no,
        oncelik_no=data.oncelik_no,
        termin_tarihi=data.termin_tarihi,
    )
    detay = await is_takip_service.get_is_emri(db, is_no, s)
    return IsEmriDetayResponse(**detay)


@router.delete("/{is_no}", response_model=MesajResponse)
async def delete_is_emri(
    is_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await is_takip_service.delete_is_emri(db, is_no, s)
    return MesajResponse(mesaj="Is emri silindi.")


# ============================================================
# DURUM DEĞİŞTİR
# ============================================================
@router.post("/{is_no}/durum", response_model=IsEmriDetayResponse)
async def durum_degistir(
    is_no: int,
    data: IsEmriDurumDegistirRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> IsEmriDetayResponse:
    s = await _require_site(site_no)
    await is_takip_service.durum_degistir(
        db, is_no, s,
        durum_no=data.durum_no,
        degistiren_no=kullanici.kullanici_no,
        notlar=data.notlar,
    )
    detay = await is_takip_service.get_is_emri(db, is_no, s)
    return IsEmriDetayResponse(**detay)


# ============================================================
# GÜNCELLEME (NOT)
# ============================================================
@router.post(
    "/{is_no}/guncelleme",
    response_model=IsEmriGuncellemeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def guncelleme_ekle(
    is_no: int,
    data: IsEmriGuncellemeCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> IsEmriGuncellemeResponse:
    s = await _require_site(site_no)
    g = await is_takip_service.guncelleme_ekle(
        db, is_no, s,
        yazan_no=kullanici.kullanici_no,
        durum_no=data.durum_no,
        notlar=data.notlar,
    )
    return IsEmriGuncellemeResponse(
        guncelleme_no=g.guncelleme_no,
        is_no=g.is_no,
        yazan_no=g.yazan_no,
        yazan_ad=None,
        durum_no=g.durum_no,
        durum_ad=None,
        notlar=g.notlar,
        guncelleme_tarihi=g.guncelleme_tarihi,
    )


# ============================================================
# MALZEME
# ============================================================
@router.post(
    "/{is_no}/malzeme",
    response_model=IsEmriMalzemeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def malzeme_ekle(
    is_no: int,
    data: IsEmriMalzemeCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> IsEmriMalzemeResponse:
    s = await _require_site(site_no)
    m = await is_takip_service.malzeme_ekle(
        db, is_no, s,
        ad=data.ad,
        adet=data.adet,
        birim=data.birim,
        birim_fiyat=data.birim_fiyat,
    )
    ara_toplam = None
    if m.birim_fiyat is not None:
        ara_toplam = m.adet * m.birim_fiyat
    return IsEmriMalzemeResponse(
        malzeme_no=m.malzeme_no,
        is_no=m.is_no,
        ad=m.ad,
        adet=m.adet,
        birim=m.birim,
        birim_fiyat=m.birim_fiyat,
        toplam=ara_toplam,
    )


@router.delete("/{is_no}/malzeme/{malzeme_no}", response_model=MesajResponse)
async def malzeme_sil(
    is_no: int,
    malzeme_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await is_takip_service.malzeme_sil(db, is_no, malzeme_no, s)
    return MesajResponse(mesaj="Malzeme silindi.")