import asyncio
from app.db.session import AsyncSessionLocal
from app.schemas.auth import KullaniciRegisterRequest
from app.services.auth_service import (
    register_user, authenticate_user, create_tokens,
    refresh_tokens, logout_user,
)

async def t():
    async with AsyncSessionLocal() as db:
        # 1) Kayıt
        print("=" * 60)
        print("1) KAYIT")
        print("=" * 60)
        data = KullaniciRegisterRequest(
            ad="Test",
            soyad="Kullanici",
            e_posta="test.user@example.com",
            telefon="05001112233",
            parola="Guclu!Parola1",
            parola_tekrar="Guclu!Parola1",
            kvkk_onay=True,
        )
        try:
            k = await register_user(db, data, ip_adresi="127.0.0.1")
            print(f"[OK] Kayit basarili: kullanici_no={k.kullanici_no}")
        except Exception as e:
            print(f"[INFO] Kayit atlandi: {type(e).__name__}: {e}")

        # 2) Giriş
        print()
        print("=" * 60)
        print("2) GIRIS")
        print("=" * 60)
        k = await authenticate_user(
            db,
            e_posta="test.user@example.com",
            parola="Guclu!Parola1",
            ip_adresi="127.0.0.1",
        )
        print(f"[OK] Giris basarili: {k.ad} {k.soyad}")

        # 3) Token üret
        print()
        print("=" * 60)
        print("3) TOKEN URETIMI")
        print("=" * 60)
        tokens = await create_tokens(db, k, ip_adresi="127.0.0.1")
        print(f"Access : {tokens.access_token[:50]}...")
        print(f"Refresh: {tokens.refresh_token[:50]}...")
        print(f"Expires: {tokens.expires_in} sn")

        # 4) Refresh
        print()
        print("=" * 60)
        print("4) TOKEN YENILEME")
        print("=" * 60)
        new_tokens = await refresh_tokens(
            db, tokens.refresh_token, ip_adresi="127.0.0.1"
        )
        print(f"[OK] Yeni access : {new_tokens.access_token[:50]}...")
        print(f"[OK] Yeni refresh: {new_tokens.refresh_token[:50]}...")

        # 5) Çıkış
        print()
        print("=" * 60)
        print("5) CIKIS")
        print("=" * 60)
        await logout_user(db, refresh_token=new_tokens.refresh_token)
        print("[OK] Cikis yapildi")

        print()
        print("[OK] Tum auth akisi test edildi.")

asyncio.run(t())
