"""Duyuru HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.auth import MesajResponse
from app.schemas.duyuru import (
    DuyuruCreateRequest,
    DuyuruDetayResponse,
    DuyuruOkumaDurumResponse,
    DuyuruOzetResponse,
    DuyuruUpdateRequest,
)
from app.services import duyuru_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/duyurular", tags=["Duyuru Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# GET /duyurular — Liste
# ============================================================
@router.get(
    "",
    response_model=list[DuyuruOzetResponse],
    summary="Duyuru listesi",
    description=(
        "Sitenin duyurularını listeler. Varsayılan olarak sadece aktif "
        "(bitiş tarihi geçmemiş) duyurular döner."
    ),
)
async def list_duyurular(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    aktif_only: Annotated[bool, Query()] = True,
    onem_derecesi: Annotated[str | None, Query(pattern="^(NORMAL|ONEMLI|ACIL)$")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DuyuruOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await duyuru_service.list_duyurular(
        db, s, kullanici.kullanici_no,
        aktif_only=aktif_only,
        onem_derecesi=onem_derecesi,
        limit=limit,
        offset=offset,
    )
    return [DuyuruOzetResponse(**k) for k in kayitlar]


# ============================================================
# POST /duyurular — Yeni duyuru
# ============================================================
@router.post(
    "",
    response_model=DuyuruDetayResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni duyuru",
    description="Site yöneticisi yeni duyuru yayınlar.",
)
async def create_duyuru(
    data: DuyuruCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DuyuruDetayResponse:
    s = await _require_site(site_no)
    duyuru = await duyuru_service.create_duyuru(
        db, s,
        baslik=data.baslik,
        icerik=data.icerik,
        yayinlayan_no=kullanici.kullanici_no,
        onem_derecesi=data.onem_derecesi,
        bitis_tarihi=data.bitis_tarihi,
    )
    return DuyuruDetayResponse(
        duyuru_no=duyuru.duyuru_no,
        site_no=duyuru.site_no,
        baslik=duyuru.baslik,
        icerik=duyuru.icerik,
        onem_derecesi=duyuru.onem_derecesi,
        yayin_tarihi=duyuru.yayin_tarihi,
        bitis_tarihi=duyuru.bitis_tarihi,
        yayinlayan_no=duyuru.yayinlayan_no,
        okundu_mu=False,
        okuma_tarihi=None,
        toplam_okuma=0,
    )


# ============================================================
# GET /duyurular/{duyuru_no} — Detay
# ============================================================
@router.get(
    "/{duyuru_no}",
    response_model=DuyuruDetayResponse,
    summary="Duyuru detayı",
    description="Tek duyuru + okuma bilgisi.",
)
async def get_duyuru(
    duyuru_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DuyuruDetayResponse:
    s = await _require_site(site_no)
    veri = await duyuru_service.get_duyuru(
        db, duyuru_no, s, kullanici.kullanici_no
    )
    return DuyuruDetayResponse(**veri)


# ============================================================
# PATCH /duyurular/{duyuru_no} — Güncelle
# ============================================================
@router.patch(
    "/{duyuru_no}",
    response_model=DuyuruDetayResponse,
    summary="Duyuru güncelle",
)
async def update_duyuru(
    duyuru_no: int,
    data: DuyuruUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DuyuruDetayResponse:
    s = await _require_site(site_no)
    duyuru = await duyuru_service.update_duyuru(
        db, duyuru_no, s,
        baslik=data.baslik,
        icerik=data.icerik,
        onem_derecesi=data.onem_derecesi,
        bitis_tarihi=data.bitis_tarihi,
    )
    # Detay bilgisi + okuma bilgisi
    veri = await duyuru_service.get_duyuru(
        db, duyuru.duyuru_no, s, kullanici.kullanici_no
    )
    return DuyuruDetayResponse(**veri)


# ============================================================
# DELETE /duyurular/{duyuru_no} — Sil
# ============================================================
@router.delete(
    "/{duyuru_no}",
    response_model=MesajResponse,
    summary="Duyuru sil",
)
async def delete_duyuru(
    duyuru_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await duyuru_service.delete_duyuru(db, duyuru_no, s)
    return MesajResponse(mesaj="Duyuru silindi.")


# ============================================================
# POST /duyurular/{duyuru_no}/okundu — Okundu işaretle
# ============================================================
@router.post(
    "/{duyuru_no}/okundu",
    response_model=MesajResponse,
    summary="Okundu işaretle",
    description=(
        "İstek yapan kullanıcı için bu duyuruyu okundu olarak işaretler. "
        "Zaten okunmuşsa sessizce geçer (idempotent)."
    ),
)
async def mark_okundu(
    duyuru_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    sonuc = await duyuru_service.mark_okundu(
        db, duyuru_no, s, kullanici.kullanici_no
    )
    if sonuc["zaten_okunmus"]:
        return MesajResponse(mesaj="Duyuru zaten okunmus.")
    return MesajResponse(mesaj="Duyuru okundu olarak isaretlendi.")


# ============================================================
# GET /duyurular/{duyuru_no}/okuma-durumu — Kim okudu?
# ============================================================
@router.get(
    "/{duyuru_no}/okuma-durumu",
    response_model=DuyuruOkumaDurumResponse,
    summary="Okuma durumu (yönetici)",
    description=(
        "Duyuruyu kimlerin okuduğunu ve okuma oranını gösterir. "
        "Sadece yönetici/denetçi erişebilir."
    ),
)
async def get_okuma_durumu(
    duyuru_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DuyuruOkumaDurumResponse:
    s = await _require_site(site_no)
    veri = await duyuru_service.get_okuma_durumu(db, duyuru_no, s)
    return DuyuruOkumaDurumResponse(**veri)