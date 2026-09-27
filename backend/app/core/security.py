"""
Güvenlik yardımcıları.

Görevler:
  - Argon2id parola hash ve doğrulama
  - JWT access/refresh token üretme ve doğrulama
  - AES-256-GCM alan şifreleme/çözme
  - SHA-256 arama hash'i
  - Güvenli rastgele token üretme
"""

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Argon2id — Parola Hash
# ============================================================
# OWASP 2024 önerisi:
#   - time_cost=2-3
#   - memory_cost=19 MiB (19456 KiB) minimum, biz 64 MiB kullanıyoruz
#   - parallelism=1-4
# Bu ayarlar hem güvenli hem de hızlı (~50ms/hash).
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,   # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(parola: str) -> str:
    """
    Parolayı Argon2id ile hash'ler.

    Dönen değer şifreli bir string'dir, kullanıcıya asla gösterilmez.
    Veritabanına kullanici.sifre_hash olarak yazılır.

    Örnek çıktı:
        $argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>
    """
    if not parola:
        raise ValueError("Parola boş olamaz.")
    return _ph.hash(parola)


def verify_password(parola: str, hash_degeri: str) -> bool:
    """
    Girilen parolayı hash ile doğrular.

    True: parola doğru
    False: parola yanlış veya hash bozuk
    """
    try:
        _ph.verify(hash_degeri, parola)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hash_degeri: str) -> bool:
    """
    Hash eski parametrelerle üretilmişse True döner.
    Parametre güncellemesi sonrası kullanıcı giriş yaptığında
    hash'i yeni parametrelerle yeniden üretmek için kullanılır.
    """
    return _ph.check_needs_rehash(hash_degeri)


# ============================================================
# JWT — Access & Refresh Token
# ============================================================

def _create_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """
    İç fonksiyon: JWT token üretir.

    data: Payload'a yazılacak veriler (örn. {"sub": "1"})
    expires_delta: Ne kadar sonra sona erecek
    token_type: "access" veya "refresh"
    """
    simdi = datetime.now(timezone.utc)
    payload = {
        **data,
        "iat": int(simdi.timestamp()),                        # issued at
        "exp": int((simdi + expires_delta).timestamp()),      # expiration
        "type": token_type,                                    # token tipi
        "jti": secrets.token_urlsafe(16),                      # unique id
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    kullanici_no: int,
    ek_bilgi: dict[str, Any] | None = None,
) -> str:
    """
    Kısa ömürlü access token üretir.
    Her API isteğinde Authorization: Bearer <token> olarak gönderilir.
    """
    data = {"sub": str(kullanici_no)}
    if ek_bilgi:
        data.update(ek_bilgi)
    return _create_token(
        data,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(kullanici_no: int) -> str:
    """
    Uzun ömürlü refresh token üretir.
    Yalnızca /auth/refresh endpoint'inde kullanılır.
    Veritabanında oturum tablosunda hash'lenmiş olarak saklanır.
    """
    return _create_token(
        {"sub": str(kullanici_no)},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    JWT token'ı doğrular ve payload'ı döner.

    Raises:
        JWTError: Token geçersiz, süresi dolmuş veya imza yanlış.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode hatasi: %s", exc)
        raise


def decode_access_token(token: str) -> dict[str, Any]:
    """Access token'ı doğrular ve tip kontrolü yapar."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Token tipi 'access' degil.")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Refresh token'ı doğrular ve tip kontrolü yapar."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Token tipi 'refresh' degil.")
    return payload


# ============================================================
# AES-256-GCM — Alan Şifreleme
# ============================================================
# settings.AES_KEY base64 ile kodlanmış 32 byte'lık anahtardır.
# AESGCM nesnesi her kullanımda yeniden oluşturulur.
def _get_aes() -> AESGCM:
    try:
        anahtar = base64.b64decode(settings.AES_KEY)
    except Exception as exc:
        raise ValueError(f"AES_KEY base64 decode edilemedi: {exc}") from exc
    if len(anahtar) != 32:
        raise ValueError("AES_KEY 32 byte olmalidir (base64 ile 44 karakter).")
    return AESGCM(anahtar)


def encrypt_field(deger: str | None) -> bytes | None:
    """
    Hassas veriyi AES-256-GCM ile şifreler.

    Format: <12-byte nonce> + <ciphertext + 16-byte tag>
    Çıktı VARBINARY kolonuna yazılır.

    None girdi → None döner (nullable kolonlar için).
    """
    if deger is None:
        return None
    if not isinstance(deger, str):
        raise TypeError("Sifrelenecek deger string olmalidir.")

    aes = _get_aes()
    nonce = secrets.token_bytes(12)   # GCM için 96-bit nonce ideal
    sifreli = aes.encrypt(nonce, deger.encode("utf-8"), None)
    return nonce + sifreli


def decrypt_field(sifreli: bytes | None) -> str | None:
    """
    AES-256-GCM ile şifrelenmiş veriyi çözer.

    None → None
    Geçersiz veya kurcalanmış veri → ValueError
    """
    if sifreli is None:
        return None
    if not isinstance(sifreli, (bytes, bytearray)):
        raise TypeError("Cozulecek deger bytes olmalidir.")

    aes = _get_aes()
    nonce, ciphertext = sifreli[:12], sifreli[12:]
    try:
        duz = aes.decrypt(nonce, ciphertext, None)
        return duz.decode("utf-8")
    except Exception as exc:
        logger.error("AES decrypt hatasi: %s", exc)
        raise ValueError("Sifreli veri cozulemedi veya kurcalanmis.") from exc


# ============================================================
# SHA-256 — Arama Hash'i
# ============================================================

def sha256_hash(deger: str | None) -> str | None:
    """
    Şifreli veri için arama hash'i üretir.

    - Aynı girdi her zaman aynı çıktıyı verir (deterministik).
    - Şifreli veri aranamaz; ama hash'i aranabilir.
    - Kullanıcı girişlerinde (login, TC ile sorgu) kullanılır.

    Örnek:
        tc_kimlik_hash = sha256_hash("10000000111")
    """
    if deger is None:
        return None
    return hashlib.sha256(deger.encode("utf-8")).hexdigest()


# ============================================================
# Rastgele Token Üretimi
# ============================================================

def generate_url_safe_token(nbytes: int = 32) -> str:
    """
    URL-safe rastgele token üretir.
    Şifre sıfırlama, e-posta doğrulama için kullanılır.
    """
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """
    Token'ı SHA-256 ile hash'ler.
    Veritabanında token'ın kendisi değil, hash'i saklanır.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
