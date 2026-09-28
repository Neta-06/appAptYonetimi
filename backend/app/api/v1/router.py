"""API v1 ana router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    aidat,
    anket,
    auth,
    daireler,
    demirbas,
    duyuru,
    gider,
    is_emri,
    raporlar,
    sakin,
    sayac,
    sites,
    toplanti,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(sites.router)
api_router.include_router(daireler.router)
api_router.include_router(aidat.router)
api_router.include_router(gider.router)
api_router.include_router(gider.gelir_router)
api_router.include_router(raporlar.router)
api_router.include_router(duyuru.router)
api_router.include_router(is_emri.router)
api_router.include_router(sayac.router)
api_router.include_router(sakin.router)
api_router.include_router(anket.router)
api_router.include_router(toplanti.router)
api_router.include_router(demirbas.router)