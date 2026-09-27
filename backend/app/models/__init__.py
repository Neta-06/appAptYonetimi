"""
SQLAlchemy modelleri.

Tüm modeller burada toplanır. Böylece:
  - Alembic autogenerate tüm modelleri görür
  - Uygulama `from app.models import Kullanici` diyebilir
"""

from app.models.identity import (
    # RBAC
    Rol,
    RolYetki,
    Yetki,
    # Firma
    YonetimFirmasi,
    # Site
    Site,
    SiteTipi,
    # Kullanıcı ve güvenlik
    AuditLog,
    Kullanici,
    KullaniciMfaYedekKod,
    KullaniciSite,
    LoginDenemesi,
    Oturum,
    ParolaSifirlamaToken,
    # KVKK
    KvkkMetin,
    KvkkOnay,
)

__all__ = [
    # RBAC
    "Rol",
    "Yetki",
    "RolYetki",
    # Firma
    "YonetimFirmasi",
    # Site
    "Site",
    "SiteTipi",
    # Kullanıcı
    "Kullanici",
    "KullaniciMfaYedekKod",
    "KullaniciSite",
    "Oturum",
    "ParolaSifirlamaToken",
    "LoginDenemesi",
    "AuditLog",
    # KVKK
    "KvkkMetin",
    "KvkkOnay",
]