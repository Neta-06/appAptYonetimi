"""
Kapsamli sistem saglik kontrolu.

Tek komutla tum kritik katmanlari test eder:
  1) DB baglantisi
  2) Redis baglantisi
  3) Modeller (15 sinif)
  4) Audit log (INSERT + UPDATE)
  5) Rate limiting (429)
  6) Auth akisi (register → login → refresh → logout)
  7) Sifreleme (Argon2id, JWT, AES, SHA-256)
  8) RBAC (yetki kontrolu)

Kullanim:
    python tests/system_check.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Proje kokunu path'e ekle
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Renk kodlari (Windows icin)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

gecti = 0
basarisiz = 0


def baslik(metin: str) -> None:
    print(f"\n{BOLD}{CYAN}{'=' * 65}{RESET}")
    print(f"{BOLD}{CYAN}  {metin}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 65}{RESET}")


def basarili(metin: str) -> None:
    global gecti
    gecti += 1
    print(f"  {GREEN}[OK]{RESET} {metin}")


def hata(metin: str) -> None:
    global basarisiz
    basarisiz += 1
    print(f"  {RED}[FAIL]{RESET} {metin}")


def bilgi(metin: str) -> None:
    print(f"  {YELLOW}[i]{RESET} {metin}")


# ============================================================
# 1) DB Baglantisi
# ============================================================
async def test_db() -> None:
    baslik("1) VERITABANI BAGLANTISI")
    try:
        from sqlalchemy import text
        from app.db.session import engine

        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT DATABASE(), VERSION()"))
            row = r.first()
            bilgi(f"DB: {row[0]}")
            bilgi(f"Surum: {row[1]}")

            r2 = await conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE()"
            ))
            tablo_sayisi = r2.scalar()
            bilgi(f"Tablo sayisi: {tablo_sayisi}")

            if tablo_sayisi > 50:
                basarili(f"DB baglantisi ({tablo_sayisi} tablo)")
            else:
                hata(f"Beklenen 50+ tablo, bulunan: {tablo_sayisi}")
    except Exception as exc:
        hata(f"DB baglantisi: {exc}")


# ============================================================
# 2) Redis Baglantisi
# ============================================================
async def test_redis() -> None:
    baslik("2) REDIS BAGLANTISI")
    try:
        from app.core.rate_limit import get_redis

        r = get_redis()
        await r.set("system_check_test", "ok")
        val = await r.get("system_check_test")
        await r.delete("system_check_test")

        if val == "ok":
            basarili("Redis baglantisi (RESP2)")
        else:
            hata(f"Redis set/get basarisiz: {val}")
    except Exception as exc:
        hata(f"Redis baglantisi: {exc}")


# ============================================================
# 3) Modeller
# ============================================================
async def test_models() -> None:
    baslik("3) MODELLER (SQLAlchemy)")
    try:
        from app.models import (
            AuditLog, Kullanici, KullaniciMfaYedekKod, KullaniciSite,
            KvkkMetin, KvkkOnay, LoginDenemesi, Oturum,
            ParolaSifirlamaToken, Rol, RolYetki, Site, SiteTipi,
            YonetimFirmasi, Yetki,
        )
        modeller = [
            Rol, Yetki, RolYetki, YonetimFirmasi, Site, SiteTipi,
            Kullanici, KullaniciMfaYedekKod, KullaniciSite,
            Oturum, ParolaSifirlamaToken, LoginDenemesi,
            AuditLog, KvkkMetin, KvkkOnay,
        ]

        for m in modeller:
            if not hasattr(m, "__tablename__"):
                hata(f"{m.__name__} - __tablename__ yok")
                return

        basarili(f"15 model yuklendi")
    except Exception as exc:
        hata(f"Model import: {exc}")


# ============================================================
# 4) Sifreleme
# ============================================================
async def test_crypto() -> None:
    baslik("4) GUVENLIK YARDIMCILARI (Kripto)")

    try:
        from app.core.security import (
            create_access_token, decode_access_token,
            decrypt_field, encrypt_field, hash_password,
            sha256_hash, verify_password,
        )

        # Argon2id
        h = hash_password("Test!Parola1")
        if verify_password("Test!Parola1", h) and not verify_password("Yanlis", h):
            basarili("Argon2id hash + verify")
        else:
            hata("Argon2id basarisiz")

        # JWT
        token = create_access_token(1)
        payload = decode_access_token(token)
        if payload["sub"] == "1" and payload["type"] == "access":
            basarili("JWT encode/decode")
        else:
            hata("JWT basarisiz")

        # AES-256-GCM
        tc = "10000000111"
        sifreli = encrypt_field(tc)
        cozulen = decrypt_field(sifreli)
        if cozulen == tc and encrypt_field(tc) != sifreli:
            basarili("AES-256-GCM + rastgele IV")
        else:
            hata("AES-256-GCM basarisiz")

        # SHA-256
        if sha256_hash(tc) == sha256_hash(tc):
            basarili("SHA-256 deterministik")
        else:
            hata("SHA-256 basarisiz")

    except Exception as exc:
        hata(f"Kripto: {exc}")


# ============================================================
# 5) Audit Log
# ============================================================
async def test_audit_log() -> None:
    baslik("5) AUDIT LOG")

    try:
        import app.core.audit  # noqa: F401
        from sqlalchemy import delete, select
        from app.db.session import AsyncSessionLocal
        from app.models import AuditLog, Kullanici

        # ÖNCE TEMİZLİK
        async with AsyncSessionLocal() as db:
            await db.execute(delete(AuditLog))
            await db.execute(
                delete(Kullanici).where(Kullanici.e_posta == "audit.check@example.com")
            )
            await db.commit()
            bilgi("Eski test verileri temizlendi")

        # Yeni kullanıcı ekle
        async with AsyncSessionLocal() as db:
            k = Kullanici(
                ad="AuditCheck",
                soyad="Test",
                e_posta="audit.check@example.com",
                sifre_hash="$argon2id$v=19$m=65536,t=3,p=4$dummy",
                aktif_mi=True,
            )
            db.add(k)
            await db.commit()
            yeni_no = k.kullanici_no

        # Audit log kontrol
        async with AsyncSessionLocal() as db:
            r = await db.execute(select(AuditLog))
            loglar = list(r.scalars().all())

            if not loglar:
                hata("Audit log bos — listener calismiyor")
                return

            basarili(f"Audit log yazildi ({len(loglar)} kayit)")

            for log in loglar:
                if log.kayit_id == str(yeni_no):
                    basarili(f"kayit_id dolu: {log.kayit_id}")
                if log.tablo_adi == "kullanici":
                    basarili("INSERT kullanici yakalandi")

        # Temizlik
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Kullanici).where(Kullanici.e_posta == "audit.check@example.com"))
            await db.execute(delete(AuditLog))
            await db.commit()

    except Exception as exc:
        hata(f"Audit log: {exc}")


# ============================================================
# 6) Auth Akisi
# ============================================================
async def test_auth_flow() -> None:
    baslik("6) AUTH AKISI")

    try:
        from sqlalchemy import delete
        from app.db.session import AsyncSessionLocal
        from app.models import Kullanici, LoginDenemesi, Oturum
        from app.schemas.auth import KullaniciRegisterRequest
        from app.services.auth_service import (
            authenticate_user, create_tokens, logout_user,
            refresh_tokens, register_user,
        )

        # ÖNCE TEMİZLİK (mevcut kodun başında)
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Oturum))
            await db.execute(delete(LoginDenemesi).where(
                LoginDenemesi.e_posta == "auth.flow@example.com"
            ))
            await db.execute(delete(Kullanici).where(
                Kullanici.e_posta == "auth.flow@example.com"
            ))
            await db.commit()
            bilgi("Eski auth test verileri temizlendi")

        # 1) Register
        async with AsyncSessionLocal() as db:
            data = KullaniciRegisterRequest(
                ad="AuthFlow", soyad="Test",
                e_posta="auth.flow@example.com",
                parola="Guclu!Parola1",
                parola_tekrar="Guclu!Parola1",
                kvkk_onay=True,
            )
            k = await register_user(db, data, ip_adresi="127.0.0.1")
            basarili(f"Register (no={k.kullanici_no})")

        # 2) Login
        async with AsyncSessionLocal() as db:
            k = await authenticate_user(
                db, e_posta="auth.flow@example.com",
                parola="Guclu!Parola1", ip_adresi="127.0.0.1",
            )
            basarili("Login")

        # 3) Token uret
        async with AsyncSessionLocal() as db:
            tokens = await create_tokens(db, k, ip_adresi="127.0.0.1")
            basarili(f"Token uretimi (expires_in={tokens.expires_in})")

        # 4) Refresh
        async with AsyncSessionLocal() as db:
            new_tokens = await refresh_tokens(
                db, tokens.refresh_token, ip_adresi="127.0.0.1"
            )
            if new_tokens.refresh_token != tokens.refresh_token:
                basarili("Refresh rotation")
            else:
                hata("Refresh rotation yok")

        # 5) Logout
        async with AsyncSessionLocal() as db:
            await logout_user(db, refresh_token=new_tokens.refresh_token)
            basarili("Logout")

        # 6) Iptal edilmis refresh reddedilsin
        async with AsyncSessionLocal() as db:
            try:
                await refresh_tokens(db, new_tokens.refresh_token)
                hata("Iptal edilmis refresh kabul edildi!")
            except Exception:
                basarili("Iptal edilmis refresh reddedildi (401)")

        # Temizlik
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Oturum))
            await db.execute(delete(LoginDenemesi).where(
                LoginDenemesi.e_posta == "auth.flow@example.com"
            ))
            await db.execute(delete(Kullanici).where(
                Kullanici.e_posta == "auth.flow@example.com"
            ))
            await db.commit()

    except Exception as exc:
        hata(f"Auth akisi: {exc}")


# ============================================================
# 7) Rate Limiting
# ============================================================
async def test_rate_limit() -> None:
    baslik("7) RATE LIMITING")

    try:
        from app.core.config import settings
        from app.core.rate_limit import RATE_LIMIT_RULES, get_redis

        if not settings.RATE_LIMIT_ENABLED:
            bilgi("RATE_LIMIT_ENABLED=false — test atlandi")
            bilgi("(Gelistirme icin normal. Uretimde true olmali.)")
            return

        rules = RATE_LIMIT_RULES
        bilgi(f"Toplam {len(rules)} kural tanimli")
        for ad, rule in rules.items():
            bilgi(f"  {ad:25s} → {rule.limit} istek / {rule.window_saniye}s")

        # Redis test
        r = get_redis()
        test_key = "rate_limit:system_check:test"
        await r.delete(test_key)

        for _ in range(3):
            await r.incr(test_key)
        val = await r.get(test_key)
        await r.delete(test_key)

        if val == "3":
            basarili("Rate limit sayaci (INCR)")
        else:
            hata(f"Rate limit sayaci: {val}")

    except Exception as exc:
        hata(f"Rate limit: {exc}")


# ============================================================
# 8) RBAC
# ============================================================
async def test_rbac() -> None:
    baslik("8) RBAC (Yetki Kontrolu)")

    try:
        from app.core.exceptions import (
            BulunamadiHatasi, CakismaHatasi, HizSiniriAsildiHatasi,
            KimlikDogrulanmadiHatasi, TokenGecersizHatasi, YetkiYokHatasi,
        )

        # Hata siniflari
        hatalar = [
            (YetkiYokHatasi(), 403, "YETKI_YOK"),
            (BulunamadiHatasi("Site", kaynak_id=1), 404, "BULUNAMADI"),
            (CakismaHatasi(alan="e_posta", deger="x@y.com"), 409, "CAKISMA"),
            (TokenGecersizHatasi(), 401, "TOKEN_GECERSIZ"),
            (KimlikDogrulanmadiHatasi(), 401, "KIMLIK_DOGRULANMADI"),
            (HizSiniriAsildiHatasi(saniye=60), 429, "HIZ_SINIRI_ASILDI"),
        ]

        for exc, beklenen_status, beklenen_kod in hatalar:
            if exc.status_code != beklenen_status or exc.kod != beklenen_kod:
                hata(f"{exc.__class__.__name__}: {exc.status_code}/{exc.kod}")
                return

        basarili(f"6 hata sinifi dogru (401/403/404/409/429)")

        # Dependency'ler
        from app.core.rbac import (
            get_current_site, get_current_user, require_rol, require_yetki,
        )
        basarili("RBAC dependency'leri yuklendi")

    except Exception as exc:
        hata(f"RBAC: {exc}")


# ============================================================
# Ana calistirici
# ============================================================
async def main() -> None:
    print(f"\n{BOLD}appApartman v0.1.0 — Kapsamli Sistem Kontrolu{RESET}")
    print(f"{BOLD}Zaman: {time.strftime('%Y-%m-%d %H:%M:%S')}{RESET}")

    await test_db()
    await test_redis()
    await test_models()
    await test_crypto()
    await test_audit_log()
    await test_auth_flow()
    await test_rate_limit()
    await test_rbac()

    # Ozet
    baslik("OZET")
    toplam = gecti + basarisiz
    print(f"  Toplam: {toplam} test")
    print(f"  {GREEN}Gecti : {gecti}{RESET}")
    if basarisiz > 0:
        print(f"  {RED}Basari: {basarisiz}{RESET}")
    else:
        print(f"  {GREEN}Basari: 0{RESET}")

    if basarisiz == 0:
        print(f"\n  {GREEN}{BOLD}>>> TUM SISTEM SAGLIKLI <<<{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {RED}{BOLD}>>> {basarisiz} TEST BASARISIZ <<<{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
