"""Personel HTTP endpoint'leri."""

import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IsKuraliHatasi
from app.core.rbac import CurrentUser
from app.db.session import get_db
from app.schemas.auth import MesajResponse
from app.schemas.personel import (
    PersonelCreateRequest,
    PersonelCikisRequest,
    PersonelDetayResponse,
    PersonelIzinCreateRequest,
    PersonelIzinOnayRequest,
    PersonelIzinResponse,
    PersonelMaasCreateRequest,
    PersonelMaasOdemeResponse,
    PersonelMaasUpdateRequest,
    PersonelOzetResponse,
    PersonelOzetStats,
    PersonelPuantajAylikOzet,
    PersonelPuantajCreateRequest,
    PersonelPuantajResponse,
    PersonelResponse,
    PersonelSiteEkleRequest,
    PersonelSiteResponse,
    PersonelUpdateRequest,
)
from app.services import personel_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personel", tags=["Personel Yonetimi"])


async def _require_firma(kullanici: CurrentUser) -> int:
    """Personel modülü firma bazlıdır."""
    if kullanici.firma_no is None:
        raise IsKuraliHatasi(
            "Personel modulu icin kullanicinin bir firmaya bagli olmasi gerekir."
        )
    return kullanici.firma_no


# ============================================================
# ÖZET (statik)
# ============================================================
@router.get("/ozet", response_model=PersonelOzetStats)
async def get_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Query(ge=1)] = None,
) -> PersonelOzetStats:
    firma_no = await _require_firma(kullanici)
    veri = await personel_service.get_ozet(db, firma_no, site_no=site_no)
    return PersonelOzetStats(**veri)


# ============================================================
# İZİN LİSTESİ (statik — {personel_no}'dan önce)
# ============================================================
@router.get("/izinler", response_model=list[PersonelIzinResponse])
async def list_izinler(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    personel_no: Annotated[int | None, Query(ge=1)] = None,
    onay_durum_no: Annotated[int | None, Query(ge=1, le=3)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PersonelIzinResponse]:
    firma_no = await _require_firma(kullanici)
    kayitlar = await personel_service.list_izinler(
        db, firma_no,
        personel_no=personel_no,
        onay_durum_no=onay_durum_no,
        limit=limit,
    )
    return [PersonelIzinResponse(**k) for k in kayitlar]


# ============================================================
# PUANTAJ AYLIK ÖZET (statik)
# ============================================================
@router.get("/puantaj-ozet", response_model=list[PersonelPuantajAylikOzet])
async def get_puantaj_aylik_ozet(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    donem_yil: Annotated[int, Query(ge=2020, le=2100)],
    donem_ay: Annotated[int, Query(ge=1, le=12)],
    personel_no: Annotated[int | None, Query(ge=1)] = None,
) -> list[PersonelPuantajAylikOzet]:
    firma_no = await _require_firma(kullanici)
    kayitlar = await personel_service.puantaj_aylik_ozet(
        db, firma_no,
        donem_yil=donem_yil,
        donem_ay=donem_ay,
        personel_no=personel_no,
    )
    return [PersonelPuantajAylikOzet(**k) for k in kayitlar]


# ============================================================
# İZİN ONAY (statik — post)
# ============================================================
@router.post(
    "/izin/{izin_no}/onay",
    response_model=PersonelIzinResponse,
)
async def izin_onayla(
    izin_no: int,
    data: PersonelIzinOnayRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelIzinResponse:
    firma_no = await _require_firma(kullanici)
    izin = await personel_service.izin_onayla(
        db, izin_no, firma_no,
        onay_durum_no=data.onay_durum_no,
        onaylayan_no=kullanici.kullanici_no,
        aciklama=data.aciklama,
    )
    detay = await personel_service.get_personel(db, izin.personel_no, firma_no)
    for i in detay["izinler"]:
        if i["izin_no"] == izin_no:
            return PersonelIzinResponse(**i)
    raise IsKuraliHatasi("Izin kaydi yuklenemedi.")


# ============================================================
# LİSTE
# ============================================================
@router.get("", response_model=list[PersonelOzetResponse])
async def list_personel(
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    site_no: Annotated[int | None, Query(ge=1)] = None,
    gorevi: Annotated[str | None, Query(max_length=50)] = None,
    aktif_only: Annotated[bool, Query()] = True,
    arama: Annotated[str | None, Query(min_length=2, max_length=50)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PersonelOzetResponse]:
    firma_no = await _require_firma(kullanici)
    kayitlar = await personel_service.list_personel(
        db, firma_no,
        site_no=site_no,
        gorevi=gorevi,
        aktif_only=aktif_only,
        arama=arama,
        limit=limit,
        offset=offset,
    )
    return [PersonelOzetResponse(**k) for k in kayitlar]


# ============================================================
# YENİ PERSONEL
# ============================================================
@router.post(
    "",
    response_model=PersonelDetayResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_personel(
    data: PersonelCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelDetayResponse:
    firma_no = await _require_firma(kullanici)
    p = await personel_service.create_personel(
        db, firma_no,
        ad=data.ad,
        soyad=data.soyad,
        gorevi=data.gorevi,
        ise_baslama_tarihi=data.ise_baslama_tarihi,
        telefon=data.telefon,
        e_posta=data.e_posta,
        kullanici_no=data.kullanici_no,
        tc_kimlik=data.tc_kimlik,
        site_nolar=data.site_nolar,
    )
    detay = await personel_service.get_personel(db, p.personel_no, firma_no)
    return PersonelDetayResponse(**detay)


# ============================================================
# DETAY / GÜNCELLE / SİL
# ============================================================
@router.get("/{personel_no}", response_model=PersonelDetayResponse)
async def get_personel(
    personel_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelDetayResponse:
    firma_no = await _require_firma(kullanici)
    detay = await personel_service.get_personel(db, personel_no, firma_no)
    return PersonelDetayResponse(**detay)


@router.patch("/{personel_no}", response_model=PersonelResponse)
async def update_personel(
    personel_no: int,
    data: PersonelUpdateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelResponse:
    firma_no = await _require_firma(kullanici)
    p = await personel_service.update_personel(
        db, personel_no, firma_no,
        ad=data.ad,
        soyad=data.soyad,
        gorevi=data.gorevi,
        telefon=data.telefon,
        e_posta=data.e_posta,
        kullanici_no=data.kullanici_no,
        ise_baslama_tarihi=data.ise_baslama_tarihi,
        isten_cikis_tarihi=data.isten_cikis_tarihi,
        aktif_mi=data.aktif_mi,
    )
    return PersonelResponse.model_validate(p)


@router.delete("/{personel_no}", response_model=MesajResponse)
async def delete_personel(
    personel_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MesajResponse:
    firma_no = await _require_firma(kullanici)
    await personel_service.delete_personel(db, personel_no, firma_no)
    return MesajResponse(mesaj="Personel silindi.")


# ============================================================
# İŞTEN ÇIKIŞ
# ============================================================
@router.post("/{personel_no}/cikis", response_model=PersonelResponse)
async def isten_cikis(
    personel_no: int,
    data: PersonelCikisRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelResponse:
    firma_no = await _require_firma(kullanici)
    p = await personel_service.isten_cikis(
        db, personel_no, firma_no,
        isten_cikis_tarihi=data.isten_cikis_tarihi,
        aciklama=data.aciklama,
    )
    return PersonelResponse.model_validate(p)


# ============================================================
# SİTE ATAMA
# ============================================================
@router.post(
    "/{personel_no}/site",
    response_model=PersonelSiteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def site_ata(
    personel_no: int,
    data: PersonelSiteEkleRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelSiteResponse:
    firma_no = await _require_firma(kullanici)
    ps = await personel_service.site_ata(
        db, personel_no, firma_no,
        site_no=data.site_no,
        baslangic_tarihi=data.baslangic_tarihi,
        bitis_tarihi=data.bitis_tarihi,
    )
    detay = await personel_service.get_personel(db, personel_no, firma_no)
    for s in detay["siteler"]:
        if s["kayit_no"] == ps.kayit_no:
            return PersonelSiteResponse(**s)
    raise IsKuraliHatasi("Site atamasi yuklenemedi.")


# ============================================================
# İZİN TALEP
# ============================================================
@router.post(
    "/{personel_no}/izin",
    response_model=PersonelIzinResponse,
    status_code=status.HTTP_201_CREATED,
)
async def izin_talep_et(
    personel_no: int,
    data: PersonelIzinCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelIzinResponse:
    firma_no = await _require_firma(kullanici)
    izin = await personel_service.izin_talep_et(
        db, personel_no, firma_no,
        izin_tipi=data.izin_tipi,
        baslangic_tarihi=data.baslangic_tarihi,
        bitis_tarihi=data.bitis_tarihi,
        aciklama=data.aciklama,
    )
    detay = await personel_service.get_personel(db, personel_no, firma_no)
    for i in detay["izinler"]:
        if i["izin_no"] == izin.izin_no:
            return PersonelIzinResponse(**i)
    raise IsKuraliHatasi("Izin kaydi yuklenemedi.")


# ============================================================
# PUANTAJ
# ============================================================
@router.get("/{personel_no}/puantaj", response_model=list[PersonelPuantajResponse])
async def list_puantaj(
    personel_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    baslangic: Annotated[date | None, Query()] = None,
    bitis: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PersonelPuantajResponse]:
    firma_no = await _require_firma(kullanici)
    kayitlar = await personel_service.list_puantaj(
        db, personel_no, firma_no,
        baslangic=baslangic,
        bitis=bitis,
        limit=limit,
    )
    return [PersonelPuantajResponse(**k) for k in kayitlar]


@router.post(
    "/{personel_no}/puantaj",
    response_model=PersonelPuantajResponse,
    status_code=status.HTTP_201_CREATED,
)
async def puantaj_ekle(
    personel_no: int,
    data: PersonelPuantajCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelPuantajResponse:
    firma_no = await _require_firma(kullanici)
    p = await personel_service.puantaj_ekle(
        db, personel_no, firma_no,
        tarih=data.tarih,
        giris_saati=data.giris_saati,
        cikis_saati=data.cikis_saati,
        devamsiz_mi=data.devamsiz_mi,
        aciklama=data.aciklama,
    )
    return PersonelPuantajResponse.model_validate(p)


# ============================================================
# MAAŞ
# ============================================================
@router.get("/{personel_no}/maaslar", response_model=list[PersonelMaasOdemeResponse])
async def list_maaslar(
    personel_no: int,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PersonelMaasOdemeResponse]:
    firma_no = await _require_firma(kullanici)
    kayitlar = await personel_service.list_maaslar(
        db, personel_no, firma_no, limit=limit
    )
    return [PersonelMaasOdemeResponse(**k) for k in kayitlar]


@router.post(
    "/{personel_no}/maas",
    response_model=PersonelMaasOdemeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def maas_ekle(
    personel_no: int,
    data: PersonelMaasCreateRequest,
    kullanici: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonelMaasOdemeResponse:
    firma_no = await _require_firma(kullanici)
    m = await personel_service.maas_ekle(
        db, personel_no, firma_no,
        donem_yil=data.donem_yil,
        donem_ay=data.donem_ay,
        brut_maas=data.brut_maas,
        kesintiler=data.kesintiler,
        odeme_tarihi=data.odeme_tarihi,
    )
    return PersonelMaasOdemeResponse.model_validate(m)