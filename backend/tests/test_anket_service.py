"""Anket servisi doğrudan test."""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.utils import now_utc_naive

from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models import Anket, AnketOyu, AnketOyHakki, AnketSecenegi
from app.services import anket_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik
        await db.execute(delete(AnketOyu))
        await db.execute(delete(AnketOyHakki))
        await db.execute(delete(AnketSecenegi))
        await db.execute(delete(Anket).where(Anket.site_no == 1))
        await db.commit()
        print("[i] Eski test anketleri temizlendi\n")

        # 1) Yeni anket olustur
        print("=" * 60)
        print("1) CREATE ANKET")
        print("=" * 60)
        a1 = await anket_service.create_anket(
            db, site_no=1,
            soru="Bahceye oyun parki yapalim mi?",
            aciklama="Tahmini maliyet aidattan karsilanacak.",
            baslangic_tarihi=now_utc_naive() - timedelta(hours=1),
            bitis_tarihi=now_utc_naive() + timedelta(days=30),
            secenekler=["EVET", "HAYIR", "KARARSIZIM"],
            olusturan_no=11,
            oy_hakki_kullanicilar=[1, 4, 5, 11],  # Manuel
        )
        print(f"  Anket #{a1.anket_no}: {a1.soru}")

        # 2) Liste
        print()
        print("=" * 60)
        print("2) LISTE (kullanici=11)")
        print("=" * 60)
        liste = await anket_service.list_anketler(db, site_no=1, kullanici_no=11)
        for a in liste:
            print(f"  [{a['anket_no']}] {a['soru'][:40]}")
            print(f"      Aktif: {a['su_an_aktif_mi']}, oy: {a['toplam_oy']}/{a['toplam_oy_hakki']}, katilim: %{a['katilim_orani']}")
            print(f"      Oy kullandi mi: {a['oy_kullandi_mi']}")

        # 3) Detay
        print()
        print("=" * 60)
        print("3) DETAY")
        print("=" * 60)
        detay = await anket_service.get_anket(db, a1.anket_no, site_no=1, kullanici_no=11)
        print(f"  Soru: {detay['soru']}")
        print(f"  Secenekler: {[s['secenek_metni'] for s in detay['secenekler']]}")
        print(f"  Aktif: {detay['su_an_aktif_mi']}")

        # 4) Oy kullan
        print()
        print("=" * 60)
        print("4) OY KULLAN (kullanici=11 -> secenek 1)")
        print("=" * 60)
        secenek_1 = detay["secenekler"][0]["secenek_no"]
        sonuc = await anket_service.oy_kullan(
            db, a1.anket_no, site_no=1, kullanici_no=11,
            secenek_no=secenek_1,
        )
        print(f"  {sonuc['mesaj']}")

        # Idempotency
        try:
            await anket_service.oy_kullan(
                db, a1.anket_no, site_no=1, kullanici_no=11,
                secenek_no=secenek_1,
            )
            print("  [FAIL] Ikinci oy kabul edildi!")
        except Exception as e:
            print(f"  [OK] Ikinci oy reddedildi: {type(e).__name__}")

        # 5) Baska kullanici oy versin
        print()
        print("=" * 60)
        print("5) DIGER KULLANICILAR OY VERSIN")
        print("=" * 60)
        await anket_service.oy_kullan(db, a1.anket_no, site_no=1, kullanici_no=1, secenek_no=secenek_1)
        await anket_service.oy_kullan(db, a1.anket_no, site_no=1, kullanici_no=4, secenek_no=detay["secenekler"][1]["secenek_no"])
        await anket_service.oy_kullan(db, a1.anket_no, site_no=1, kullanici_no=5, secenek_no=detay["secenekler"][2]["secenek_no"])
        print("  3 oy daha kaydedildi")

        # 6) Sonuclar
        print()
        print("=" * 60)
        print("6) SONUCLAR")
        print("=" * 60)
        sonuc = await anket_service.get_sonuclar(db, a1.anket_no, site_no=1)
        print(f"  Soru: {sonuc['soru']}")
        print(f"  Toplam oy: {sonuc['toplam_oy']} / {sonuc['toplam_oy_hakki']} (%{sonuc['katilim_orani']})")
        for s in sonuc["secenekler"]:
            bar = "#" * int(s["yuzde"] / 5)
            print(f"    {s['secenek_metni']:12s} {s['oy_sayisi']:2d} oy (%{s['yuzde']:5.1f}) {bar}")

        # 7) Guncelle
        print()
        print("=" * 60)
        print("7) GUNCELLE")
        print("=" * 60)
        guncel = await anket_service.update_anket(
            db, a1.anket_no, site_no=1,
            soru="Bahceye oyun parki yapalim mi? (guncellendi)",
            aktif_mi=True,
        )
        print(f"  Yeni soru: {guncel.soru}")

        # 8) Sil
        print()
        print("=" * 60)
        print("8) SIL")
        print("=" * 60)
        await anket_service.delete_anket(db, a1.anket_no, site_no=1)
        print(f"  Anket #{a1.anket_no} silindi")

        # Dogrulama
        try:
            await anket_service.get_anket(db, a1.anket_no, site_no=1, kullanici_no=11)
            print("  [FAIL] Hala var!")
        except Exception:
            print("  [OK] Silindi dogrulandi (404)")

        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())