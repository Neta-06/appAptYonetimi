"""
Genel yardımcı fonksiyonlar.
"""

import ipaddress
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def ip_to_bytes(ip_str: str | None) -> bytes | None:
    """
    IP adres string'ini VARBINARY(16) formatina cevirir.

    IPv4 -> 4 byte
    IPv6 -> 16 byte
    Gecersiz/None -> None

    Kullanım:
        ip_to_bytes("192.168.1.1")   -> b'\\xc0\\xa8\\x01\\x01'
        ip_to_bytes("::1")           -> 16 byte
    """
    if not ip_str:
        return None
    try:
        ip = ipaddress.ip_address(ip_str.strip())
        return ip.packed
    except (ValueError, AttributeError) as exc:
        logger.debug("Gecersiz IP adresi: %s (%s)", ip_str, exc)
        return None


def bytes_to_ip(b: bytes | None) -> str | None:
    """VARBINARY'den okunan IP'yi string'e cevirir."""
    if not b:
        return None
    try:
        return str(ipaddress.ip_address(b))
    except (ValueError, TypeError):
        return None


def now_utc() -> datetime:
    """
    Timezone-aware UTC şimdiki zaman.
    DATETIME kolonlarına yazılırken .replace(tzinfo=None) kullanılabilir.
    """
    return datetime.now(timezone.utc)


def now_utc_naive() -> datetime:
    """MySQL DATETIME kolonları için timezone'suz UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
