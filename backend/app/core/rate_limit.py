"""
Redis tabanli rate limiting (sliding window).

Her endpoint icin kural tanimlanir. Limit asilirsa HTTP 429 doner.
Redis 5.x ile uyumlu (protocol=2 / RESP2).
"""

import json
import logging
from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import HizSiniriAsildiHatasi

logger = logging.getLogger(__name__)


# ============================================================
# Redis baglantisi (singleton)
# ============================================================
_redis_client: Redis | None = None


def get_redis() -> Redis:
    """Redis singleton baglantisi (RESP2 - Redis 5 uyumlu)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            protocol=2,  # Redis 5 uyumlulugu icin RESP2
        )
    return _redis_client


async def close_redis() -> None:
    """Uygulama kapanirken baglantiyi temizler."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis baglantisi kapatildi.")


# ============================================================
# Kural tanimi
# ============================================================
@dataclass(frozen=True)
class RateLimitRule:
    limit: int
    window_saniye: int
    anahtar_tipi: str  # "ip" | "email"


RATE_LIMIT_RULES: dict[str, RateLimitRule] = {
    "login": RateLimitRule(limit=5, window_saniye=300, anahtar_tipi="ip"),
    "register": RateLimitRule(limit=3, window_saniye=3600, anahtar_tipi="ip"),
    "sifre_sifirla_talebi": RateLimitRule(limit=3, window_saniye=3600, anahtar_tipi="email"),
    "refresh": RateLimitRule(limit=30, window_saniye=60, anahtar_tipi="ip"),
    "default": RateLimitRule(limit=100, window_saniye=60, anahtar_tipi="ip"),
}


# ============================================================
# Yardimcilar
# ============================================================
def _client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _rate_limit_key(rule_adi: str, tanimlayici: str) -> str:
    return f"rate_limit:{rule_adi}:{tanimlayici}"


# ============================================================
# Kontrol
# ============================================================
async def check_rate_limit(
    request: Request,
    rule_adi: str,
    *,
    ek_anahtar: str | None = None,
) -> None:
    """Rate limit kontrolu. Asim varsa HizSiniriAsildiHatasi firlatir."""
    # Dev bypass
    if not settings.RATE_LIMIT_ENABLED:
        return

    rule = RATE_LIMIT_RULES.get(rule_adi, RATE_LIMIT_RULES["default"])
    # ... geri kalanı aynı

    if ek_anahtar:
        tanimlayici = ek_anahtar.lower().strip()
    else:
        tanimlayici = _client_ip(request)

    key = _rate_limit_key(rule_adi, tanimlayici)
    redis = get_redis()

    try:
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        sonuclar = await pipe.execute()

        mevcut = sonuclar[0]
        ttl = sonuclar[1]

        if mevcut == 1 or ttl < 0:
            await redis.expire(key, rule.window_saniye)
            ttl = rule.window_saniye

        if mevcut > rule.limit:
            logger.warning(
                "Rate limit asildi: rule=%s tanimlayici=%s mevcut=%d limit=%d",
                rule_adi, tanimlayici, mevcut, rule.limit,
            )
            raise HizSiniriAsildiHatasi(saniye=ttl)

    except HizSiniriAsildiHatasi:
        raise
    except Exception as exc:
        # Redis hatasi -> fail-open (hizmet kesintisi olmasin)
        logger.error("Redis rate limit hatasi: %s", exc)


# ============================================================
# FastAPI dependency'leri
# ============================================================
def rate_limit(rule_adi: str):
    """Endpoint seviyesinde rate limit (IP bazli)."""
    async def _kontrol(request: Request) -> None:
        await check_rate_limit(request, rule_adi)
    return _kontrol


def rate_limit_by_email(rule_adi: str, email_alani: str = "e_posta"):
    """E-posta bazli rate limit (body'den email okur)."""
    async def _kontrol(request: Request) -> None:
        email: str | None = None
        try:
            if hasattr(request, "_body"):
                body = json.loads(request._body)
                email = body.get(email_alani)
        except Exception:
            pass
        await check_rate_limit(request, rule_adi, ek_anahtar=email)
    return _kontrol
