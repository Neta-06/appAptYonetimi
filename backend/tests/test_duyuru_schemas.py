"""Duyuru şemaları validation testi."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from app.schemas.duyuru import DuyuruCreateRequest, DuyuruUpdateRequest


print("=" * 60)
print("1) GECERLI DUYURU")
print("=" * 60)
try:
    d = DuyuruCreateRequest(
        baslik="Su Kesintisi",
        icerik="25 Ekim 09:00-15:00 arasi su kesintisi olacaktir.",
        onem_derecesi="ACIL",
        bitis_tarihi=date(2026, 10, 25),
    )
    print("[OK] Gecerli duyuru kabul edildi")
    print(f"     Baslik: {d.baslik}")
    print(f"     Onem: {d.onem_derecesi}")
    print(f"     Bitis: {d.bitis_tarihi}")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("2) VARSAYILAN ONEM")
print("=" * 60)
try:
    d = DuyuruCreateRequest(
        baslik="Test Duyuru",
        icerik="Bu bir test duyurusudur, yeterince uzun.",
    )
    print(f"[OK] Varsayilan onem: {d.onem_derecesi} (NORMAL olmali)")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("3) KISA BASLIK")
print("=" * 60)
try:
    DuyuruCreateRequest(baslik="AB", icerik="Yeterince uzun bir icerik metni.")
    print("[FAIL] Cok kisa baslik kabul edildi!")
except ValidationError:
    print("[OK] Kisa baslik reddedildi (min_length=3)")


print()
print("=" * 60)
print("4) KISA ICERIK")
print("=" * 60)
try:
    DuyuruCreateRequest(baslik="Test Baslik", icerik="kisa")
    print("[FAIL] Cok kisa icerik kabul edildi!")
except ValidationError:
    print("[OK] Kisa icerik reddedildi (min_length=10)")


print()
print("=" * 60)
print("5) GECERSIZ ONEM DERECESI")
print("=" * 60)
try:
    DuyuruCreateRequest(
        baslik="Test Baslik",
        icerik="Yeterince uzun bir icerik metni.",
        onem_derecesi="COK_ACIL",
    )
    print("[FAIL] Gecersiz onem kabul edildi!")
except ValidationError:
    print("[OK] Gecersiz onem reddedildi")


print()
print("=" * 60)
print("6) BOS PATCH")
print("=" * 60)
try:
    u = DuyuruUpdateRequest()
    print(f"[OK] Bos PATCH kabul edildi (baslik={u.baslik}, icerik={u.icerik})")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("[OK] Tum validation testleri tamamlandi.")