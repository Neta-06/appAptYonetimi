"""Toplantı HTTP endpoint'leri."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.auth import MesajResponse
from app.schemas.toplanti import (
    KararEkleRequest,
    KatilimciEkleRequest,
    KatilimciGuncelleRequest,
    ToplantiCreateRequest,
    ToplantiDetayResponse,
    ToplantiDurumDegistirRequest,
    ToplantiKatilimciResponse,
    ToplantiKararResponse,
    ToplantiOzetResponse,
    ToplantiOzetStats,
    ToplantiUpdateRequest,
)
from app.services import toplanti_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/toplantilar", tags=["Toplanti Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# ÖZET (statik — {toplanti_no}'dan önce)
# ============================================================
@router.get("/ozet", response_model=ToplantiOzetStats)
async def get_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiOzetStats:
    s = await _require_site(site_no)
    veri = await toplanti_service.get_ozet(db, s)
    return ToplantiOzetStats(**veri)


# ============================================================
# LİSTE
# ============================================================
@router.get("", response_model=list[ToplantiOzetResponse])
async def list_toplantilar(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    durum: Annotated[str | None, Query(pattern="^(PLANLANDI|YAPILDI|IPTAL)$")] = None,
    tarih_baslangic: Annotated[datetime | None, Query()] = None,
    tarih_bitis: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ToplantiOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await toplanti_service.list_toplantilar(
        db, s,
        durum=durum,
        tarih_baslangic=tarih_baslangic,
        tarih_bitis=tarih_bitis,
        limit=limit,
        offset=offset,
    )
    return [ToplantiOzetResponse(**k) for k in kayitlar]


# ============================================================
# YENİ
# ============================================================
@router.post(
    "",
    response_model=ToplantiDetayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_toplanti(
    data: ToplantiCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiDetayResponse:
    s = await _require_site(site_no)
    toplanti = await toplanti_service.create_toplanti(
        db, s,
        baslik=data.baslik,
        aciklama=data.aciklama,
        toplanti_tarihi=data.toplanti_tarihi,
        yer=data.yer,
        olusturan_no=kullanici.kullanici_no,
        katilimci_kullanicilar=data.katilimci_kullanicilar,
    )
    detay = await toplanti_service.get_toplanti(db, toplanti.toplanti_no, s)
    return ToplantiDetayResponse(**detay)


# ============================================================
# DETAY / GÜNCELLE / SİL
# ============================================================
@router.get("/{toplanti_no}", response_model=ToplantiDetayResponse)
async def get_toplanti(
    toplanti_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiDetayResponse:
    s = await _require_site(site_no)
    detay = await toplanti_service.get_toplanti(db, toplanti_no, s)
    return ToplantiDetayResponse(**detay)


@router.patch("/{toplanti_no}", response_model=ToplantiDetayResponse)
async def update_toplanti(
    toplanti_no: int,
    data: ToplantiUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiDetayResponse:
    s = await _require_site(site_no)
    await toplanti_service.update_toplanti(
        db, toplanti_no, s,
        baslik=data.baslik,
        aciklama=data.aciklama,
        toplanti_tarihi=data.toplanti_tarihi,
        yer=data.yer,
    )
    detay = await toplanti_service.get_toplanti(db, toplanti_no, s)
    return ToplantiDetayResponse(**detay)


@router.delete("/{toplanti_no}", response_model=MesajResponse)
async def delete_toplanti(
    toplanti_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await toplanti_service.delete_toplanti(db, toplanti_no, s)
    return MesajResponse(mesaj="Toplanti silindi.")


# ============================================================
# DURUM DEĞİŞTİR
# ============================================================
@router.post("/{toplanti_no}/durum", response_model=ToplantiDetayResponse)
async def durum_degistir(
    toplanti_no: int,
    data: ToplantiDurumDegistirRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiDetayResponse:
    s = await _require_site(site_no)
    await toplanti_service.durum_degistir(
        db, toplanti_no, s, yeni_durum=data.durum
    )
    detay = await toplanti_service.get_toplanti(db, toplanti_no, s)
    return ToplantiDetayResponse(**detay)


# ============================================================
# KATILIMCI
# ============================================================
@router.post(
    "/{toplanti_no}/katilimcilar",
    response_model=ToplantiKatilimciResponse,
    status_code=status.HTTP_201_CREATED,
)
async def katilimci_ekle(
    toplanti_no: int,
    data: KatilimciEkleRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiKatilimciResponse:
    s = await _require_site(site_no)
    k = await toplanti_service.katilimci_ekle(
        db, toplanti_no, s,
        kullanici_no=data.kullanici_no,
        vekalet_kullanici_no=data.vekalet_kullanici_no,
    )
    # Kullanıcı bilgisini yükle
    detay = await toplanti_service.get_toplanti(db, toplanti_no, s)
    for kk in detay["katilimcilar"]:
        if kk["katilim_no"] == k.katilim_no:
            return ToplantiKatilimciResponse(**kk)
    # Güvenlik ağı
    return ToplantiKatilimciResponse(
        katilim_no=k.katilim_no,
        toplanti_no=k.toplanti_no,
        kullanici_no=k.kullanici_no,
        ad=None,
        soyad=None,
        e_posta=None,
        katildi_mi=k.katildi_mi,
        vekalet_kullanici_no=k.vekalet_kullanici_no,
        vekalet_ad=None,
    )


@router.patch(
    "/{toplanti_no}/katilimcilar/{katilim_no}",
    response_model=ToplantiKatilimciResponse,
)
async def katilimci_guncelle(
    toplanti_no: int,
    katilim_no: int,
    data: KatilimciGuncelleRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiKatilimciResponse:
    s = await _require_site(site_no)
    await toplanti_service.katilimci_guncelle(
        db, toplanti_no, katilim_no, s,
        katildi_mi=data.katildi_mi,
        vekalet_kullanici_no=data.vekalet_kullanici_no,
    )
    detay = await toplanti_service.get_toplanti(db, toplanti_no, s)
    for kk in detay["katilimcilar"]:
        if kk["katilim_no"] == katilim_no:
            return ToplantiKatilimciResponse(**kk)
    raise IsKuraliHatasi("Katilimci bulunamadi.")


# ============================================================
# KARAR
# ============================================================
@router.post(
    "/{toplanti_no}/kararlar",
    response_model=ToplantiKararResponse,
    status_code=status.HTTP_201_CREATED,
)
async def karar_ekle(
    toplanti_no: int,
    data: KararEkleRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> ToplantiKararResponse:
    s = await _require_site(site_no)
    karar = await toplanti_service.karar_ekle(
        db, toplanti_no, s, karar_metni=data.karar_metni
    )
    return ToplantiKararResponse.model_validate(karar)