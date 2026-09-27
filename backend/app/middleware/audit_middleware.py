"""Audit log middleware — her istek icin context set eder."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.audit import clear_audit_context, set_audit_context


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    Her HTTP istegi icin audit context'i hazirlar.
    Kullanici bilgisi token'dan degil, request.state'ten alinir.
    (Auth dependency zaten kullaniciyi request.state'e koyacak sekilde
    ayarlanabilir; simdilik IP ve user-agent ile basliyoruz.)
    """

    async def dispatch(self, request: Request, call_next):
        # IP ve user-agent'i simdiden set et
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not ip:
            ip = request.client.host if request.client else None

        set_audit_context(
            kullanici_no=None,
            site_no=None,
            ip_adresi=ip,
            user_agent=request.headers.get("user-agent"),
        )
        request.state.audit_ip = ip
        request.state.audit_user_agent = request.headers.get("user-agent")

        try:
            response = await call_next(request)
        finally:
            clear_audit_context()

        return response
