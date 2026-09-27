"""Gider şemaları validation testi."""
import sys
from decimal import Decimal
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from app.schemas.gider import (
    GiderCreateRequest, GiderUpdateRequest,
    GelirCreateRequest,
)


print("=" * 60)
print("1) GECERLI GIDER")
print("=" * 60)
try:
    g = GiderCreateRequest(
        kalem_no=1,
        cari_no=1,
        tutar=Decimal("2500.00"),
        kdv_tutar=Decimal("450.00"),
        gider_tarihi=date(2026, 10, 1),
        belge_no="FTR-1001",
        aciklama="Test gider",
    )
    print("[OK] Gecerli gider kabul edildi")
    print(f"     Kalem: {g.kalem_no}, Tutar: {g.tutar}, KDV: {g.kdv_tutar}")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("2) NEGATIF TUTAR")
print("=" * 60)
try:
    GiderCreateRequest(
        kalem_no=1,
        tutar=Decimal("-100"),
        gider_tarihi=date.today(),
    )
    print("[FAIL] Negatif tutar kabul edildi!")
except ValidationError:
    print("[OK] Negatif tutar reddedildi")


print()
print("=" * 60)
print("3) SIFIR TUTAR")
print("=" * 60)
try:
    GiderCreateRequest(
        kalem_no=1,
        tutar=Decimal("0"),
        gider_tarihi=date.today(),
    )
    print("[FAIL] Sifir tutar kabul edildi!")
except ValidationError:
    print("[OK] Sifir tutar reddedildi (gt=0)")


print()
print("=" * 60)
print("4) KDV OPSIYONEL (default 0)")
print("=" * 60)
try:
    g = GiderCreateRequest(
        kalem_no=1,
        tutar=Decimal("1000"),
        gider_tarihi=date.today(),
    )
    print(f"[OK] KDV default: {g.kdv_tutar}")


except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("5) PATCH BOS BODY")
print("=" * 60)
try:
    u = GiderUpdateRequest()
    print("[OK] Bos PATCH kabul edildi (tum alanlar None)")
    print(f"     tutar={u.tutar}, kalem_no={u.kalem_no}")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("6) GELIR VALIDASYON")
print("=" * 60)
try:
    gl = GelirCreateRequest(
        kaynak="Kira Geliri",
        tutar=Decimal("1500"),
        gelir_tarihi=date.today(),
    )
    print("[OK] Gecerli gelir kabul edildi")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("7) KISA KAYNAK ADI")
print("=" * 60)
try:
    GelirCreateRequest(
        kaynak="A",
        tutar=Decimal("100"),
        gelir_tarihi=date.today(),
    )
    print("[FAIL] 1 karakterli kaynak kabul edildi!")
except ValidationError:
    print("[OK] Cok kisa kaynak reddedildi (min_length=2)")


print()
print("[OK] Tum validation testleri tamamlandi.")