"""API v1 ana router."""

from fastapi import APIRouter

from app.api.v1.endpoints import aidat, auth, daireler, gider, sites

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(sites.router)
api_router.include_router(daireler.router)
api_router.include_router(aidat.router)
api_router.include_router(gider.router)
api_router.include_router(gider.gelir_router)