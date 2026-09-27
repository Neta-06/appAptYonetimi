"""
API v1 ana router.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, sites

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(sites.router)
