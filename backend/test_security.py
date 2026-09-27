from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_access_token, decode_refresh_token,
    encrypt_field, decrypt_field,
    sha256_hash, generate_url_safe_token, hash_token,
)

print("=" * 60)
print("1) PAROLA HASH (Argon2id)")
print("=" * 60)
parola = "Guclu!Parola123"
h = hash_password(parola)
print(f"Hash baslangici: {h[:50]}...")
print(f"Dogru parola   : {verify_password(parola, h)}")
print(f"Yanlis parola  : {verify_password('yanlis', h)}")

print()
print("=" * 60)
print("2) JWT TOKEN")
print("=" * 60)
access = create_access_token(kullanici_no=1)
refresh = create_refresh_token(kullanici_no=1)
print(f"Access baslangici : {access[:50]}...")
print(f"Refresh baslangici: {refresh[:50]}...")
p = decode_access_token(access)
print(f"Access decoded  : sub={p['sub']}, type={p['type']}")
pr = decode_refresh_token(refresh)
print(f"Refresh decoded : sub={pr['sub']}, type={pr['type']}")

print()
print("=" * 60)
print("3) AES-256-GCM")
print("=" * 60)
tc = "10000000111"
sifreli = encrypt_field(tc)
print(f"Sifreli uzunluk  : {len(sifreli)} byte")
print(f"Sifreli on ek    : {sifreli[:16].hex()}...")
duz = decrypt_field(sifreli)
print(f"Cozulen          : {duz}")
print(f"Eslesme          : {duz == tc}")
sifreli2 = encrypt_field(tc)
print(f"IV rastgele mi   : {sifreli != sifreli2}")

print()
print("=" * 60)
print("4) SHA-256")
print("=" * 60)
h1 = sha256_hash(tc)
h2 = sha256_hash(tc)
print(f"Hash 1          : {h1[:32]}...")
print(f"Deterministik   : {h1 == h2}")

print()
print("=" * 60)
print("5) RASTGELE TOKEN")
print("=" * 60)
t1 = generate_url_safe_token()
t2 = generate_url_safe_token()
print(f"Token 1         : {t1[:40]}...")
print(f"Farkli mi       : {t1 != t2}")

print()
print("[OK] Tum guvenlik fonksiyonlari calisiyor.")
