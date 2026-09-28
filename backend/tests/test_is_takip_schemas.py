"""İş emri şemaları validation testi."""
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from app.schemas.is_takip import (
    IsEmriCreateRequest, IsEmriUpdateRequest,
    IsEmriDurumDegistirRequest, IsEmriMalzemeCreateRequest,
    IsEmriGuncellemeCreateRequest,
)


print("=" * 60)
print("1) GECERLI IS EMRi")
print("=" * 60)
try:
    i = IsEmriCreateRequest(
        baslik="Balkon Suyu Sizintisi",
        aciklama="Daire 1 balkon drenaj kontrolu.",
        daire_no=1,
        atanan_no=3,
        oncelik_no=1,
        termin_tarihi=datetime.now() + timedelta(days=7),
    )
    print("[OK] Gecerli is emri kabul edildi")
    print(f"     Baslik: {i.baslik}")
    print(f"     Daire: {i.daire_no}, Atanan: {i.atanan_no}")
    print(f"     Oncelik: {i.oncelik_no}")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("2) KISA BASLIK")
print("=" * 60)
try:
    IsEmriCreateRequest(baslik="AB", atanan_no=3, oncelik_no=1)
    print("[FAIL] Cok kisa baslik kabul edildi!")
except ValidationError:
    print("[OK] Kisa baslik reddedildi (min_length=3)")


print()
print("=" * 60)
print("3) ATANAN GEREKLI")
print("=" * 60)
try:
    IsEmriCreateRequest(baslik="Test Baslik", oncelik_no=1)
    print("[FAIL] Atanan olmadan kabul edildi!")
except ValidationError:
    print("[OK] Atanan_no zorunlu (required)")


print()
print("=" * 60)
print("4) BOS PATCH")
print("=" * 60)
try:
    u = IsEmriUpdateRequest()
    print(f"[OK] Bos PATCH kabul edildi (baslik={u.baslik}, atanan_no={u.atanan_no})")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("5) DURUM DEGISTIR")
print("=" * 60)
try:
    d = IsEmriDurumDegistirRequest(durum_no=2, notlar="Is uzerinde calisiliyor")
    print(f"[OK] Durum degistir: durum_no={d.durum_no}, notlar={d.notlar[:30]}")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("6) MALZEME EKLE")
print("=" * 60)
try:
    m = IsEmriMalzemeCreateRequest(
        ad="PVC Boru 50mm",
        adet=Decimal("2.5"),
        birim="m",
        birim_fiyat=Decimal("80.00"),
    )
    print(f"[OK] Malzeme: {m.ad}, adet={m.adet} {m.birim}, fiyat={m.birim_fiyat}")
except ValidationError as e:
    print(f"[FAIL] {e}")


print()
print("=" * 60)
print("7) NEGATIF ADET")
print("=" * 60)
try:
    IsEmriMalzemeCreateRequest(ad="Test", adet=Decimal("-1"))
    print("[FAIL] Negatif adet kabul edildi!")
except ValidationError:
    print("[OK] Negatif adet reddedildi (gt=0)")


print()
print("=" * 60)
print("8) KISA NOT")
print("=" * 60)
try:
    IsEmriGuncellemeCreateRequest(durum_no=2, notlar="A")
    print("[FAIL] Cok kisa not kabul edildi!")
except ValidationError:
    print("[OK] Kisa not reddedildi (min_length=3)")


print()
print("[OK] Tum validation testleri tamamlandi.")