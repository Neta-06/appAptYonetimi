"""Aidat ve ödeme HTTP endpoint'leri."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser, get_current_site
from app.db.session import get_db
from app.schemas.aidat import (
    AidatOzetIstatistik,
    AidatOzetResponse,
    AidatResponse,
    DaireAidatGecmisi,
    OdemeCreateRequest,
    OdemeDetayliResponse,
    OdemeIptalRequest,
    TopluAidatOlusturRequest,
    TopluAidatSonuc,
)
from app.schemas.auth import MesajResponse
from app.services import aidat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/aidatlar", tags=["Aidat Yonetimi"])


async def _require_site(site_no: int | None) -> int:
    if site_no is None:
        raise IsKuraliHatasi("'X-Site-Id' basligi gerekli.")
    return site_no


# ============================================================
# GET /aidatlar — Site aidatları (filtreli)
# ============================================================
@router.get(
    "",
    response_model=list[AidatOzetResponse],
    summary="Aidat listesi",
    description=(
        "Sitenin aidatlarını listeler. "
        "Filtreler: dönem, durum, daire, aidat tipi."
    ),
)
async def list_aidatlar(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    donem_yil: Annotated[int | None, Query(ge=2020, le=2100)] = None,
    donem_ay: Annotated[int | None, Query(ge=1, le=12)] = None,
    durum: Annotated[str | None, Query(pattern="^(BEKLIYOR|ODENDI|GECIKMIS|KISMI_ODENDI|IPTAL)$")] = None,
    daire_no: Annotated[int | None, Query(ge=1)] = None,
    aidat_tipi_no: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AidatOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await aidat_service.list_aidatlar(
        db, s,
        donem_yil=donem_yil,
        donem_ay=donem_ay,
        durum=durum,
        daire_no=daire_no,
        aidat_tipi_no=aidat_tipi_no,
        limit=limit,
        offset=offset,
    )
    return [AidatOzetResponse(**k) for k in kayitlar]


# ============================================================
# GET /aidatlar/ozet — Özet istatistikler
# ============================================================
@router.get(
    "/ozet",
    response_model=AidatOzetIstatistik,
    summary="Aidat özet istatistikleri",
    description="Site geneli tahakkuk/tahsilat/kalan özetleri.",
)
async def get_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
    donem_yil: Annotated[int | None, Query(ge=2020, le=2100)] = None,
    donem_ay: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> AidatOzetIstatistik:
    s = await _require_site(site_no)
    ozet = await aidat_service.get_ozet(
        db, s, donem_yil=donem_yil, donem_ay=donem_ay
    )
    return AidatOzetIstatistik(**ozet)


# ============================================================
# GET /aidatlar/gecikmis — Gecikmiş aidatlar
# ============================================================
@router.get(
    "/gecikmis",
    response_model=list[AidatOzetResponse],
    summary="Gecikmiş aidatlar",
    description="Son ödeme tarihi geçmiş ve tam ödenmemiş aidatlar.",
)
async def list_gecikmis(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> list[AidatOzetResponse]:
    s = await _require_site(site_no)
    kayitlar = await aidat_service.list_gecikmis(db, s)
    return [AidatOzetResponse(**k) for k in kayitlar]


# ============================================================
# GET /aidatlar/daire/{daire_no} — Daire aidat geçmişi
# ============================================================
@router.get(
    "/daire/{daire_no}",
    response_model=DaireAidatGecmisi,
    summary="Daire aidat geçmişi",
    description="Bir dairenin tüm aidat kayıtları + borç özeti.",
)
async def get_daire_gecmisi(
    daire_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> DaireAidatGecmisi:
    s = await _require_site(site_no)
    gecmis = await aidat_service.list_daire_aidat_gecmisi(db, daire_no, s)
    return DaireAidatGecmisi(**gecmis)


# ============================================================
# GET /aidatlar/{aidat_no} — Aidat detayı
# ============================================================
@router.get(
    "/{aidat_no}",
    response_model=AidatResponse,
    summary="Aidat detayı",
)
async def get_aidat(
    aidat_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> AidatResponse:
    s = await _require_site(site_no)
    aidat = await aidat_service.get_aidat(db, aidat_no, s)
    return AidatResponse.model_validate(aidat)


# ============================================================
# POST /aidatlar/odeme — Tahsilat kaydı
# ============================================================
@router.post(
    "/odeme",
    response_model=OdemeDetayliResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tahsilat kaydı oluştur",
    description=(
        "Bir veya birden çok aidatı kapatan tahsilat kaydı oluşturur. "
        "Aidat durumları otomatik güncellenir (ODENDI / KISMI_ODENDI)."
    ),
)
async def create_odeme(
    data: OdemeCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> OdemeDetayliResponse:
    s = await _require_site(site_no)
    odeme = await aidat_service.create_odeme(
        db, s,
        odeme_kanali_no=data.odeme_kanali_no,
        detaylar=[d.model_dump() for d in data.detaylar],
        olusturan_no=kullanici.kullanici_no,
        dekont_no=data.dekont_no,
        referans_no=data.referans_no,
        aciklama=data.aciklama,
    )

    # Detayları yükle
    from sqlalchemy import select
    from app.models import OdemeDetay
    d_sonuc = await db.execute(
        select(OdemeDetay).where(OdemeDetay.odeme_no == odeme.odeme_no)
    )
    detaylar = list(d_sonuc.scalars().all())

    return OdemeDetayliResponse(
        odeme_no=odeme.odeme_no,
        site_no=odeme.site_no,
        odeme_tarihi=odeme.odeme_tarihi,
        toplam_tutar=odeme.toplam_tutar,
        odeme_kanali_no=odeme.odeme_kanali_no,
        dekont_no=odeme.dekont_no,
        referans_no=odeme.referans_no,
        onay_durum_no=odeme.onay_durum_no,
        onay_tarihi=odeme.onay_tarihi,
        aciklama=odeme.aciklama,
        olusturan_no=odeme.olusturan_no,
        detaylar=[{
            "detay_no": d.detay_no,
            "aidat_no": d.aidat_no,
            "gider_no": d.gider_no,
            "tutar": d.tutar,
            "aciklama": d.aciklama,
        } for d in detaylar],
    )


# ============================================================
# POST /aidatlar/odeme/{odeme_no}/iptal — Ödeme iptali
# ============================================================
@router.post(
    "/odeme/{odeme_no}/iptal",
    response_model=MesajResponse,
    summary="Ödeme iptali",
    description=(
        "Ödemeyi iptal eder, bağlı aidatların durumunu geri alır. "
        "Sadece yetkili kullanıcılar (aidat.sil yetkisi) kullanabilir."
    ),
)
async def iptal_odeme(
    odeme_no: int,
    data: OdemeIptalRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> MesajResponse:
    s = await _require_site(site_no)
    await aidat_service.iptal_odeme(
        db, odeme_no, s, iptal_nedeni=data.iptal_nedeni
    )
    return MesajResponse(mesaj="Odeme iptal edildi.")


# ============================================================
# POST /aidatlar/toplu-olustur — Toplu aidat
# ============================================================
@router.post(
    "/toplu-olustur",
    response_model=TopluAidatSonuc,
    status_code=status.HTTP_201_CREATED,
    summary="Toplu aidat oluştur",
    description=(
        "Belirtilen dönem için site genelinde (veya bir blokta) "
        "toplu aidat borçlandırması yapar. "
        "Zaten var olan aidatlar atlanır."
    ),
)
async def toplu_aidat_olustur(
    data: TopluAidatOlusturRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Depends(get_current_site)],
) -> TopluAidatSonuc:
    s = await _require_site(site_no)
    sonuc = await aidat_service.toplu_aidat_olustur(
        db, s,
        aidat_tipi_no=data.aidat_tipi_no,
        donem_yil=data.donem_yil,
        donem_ay=data.donem_ay,
        son_odeme_tarihi=data.son_odeme_tarihi,
        blok_no=data.blok_no,
    )
    return TopluAidatSonuc(**sonuc)