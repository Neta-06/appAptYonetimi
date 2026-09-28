"""Toplantı servisi doğrudan test."""
import asyncio
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.core.utils import now_utc_naive
from app.db.session import AsyncSessionLocal
from app.models import Toplanti, ToplantiKarar, ToplantiKatilimci
from app.services import toplanti_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik
        await db.execute(delete(ToplantiKarar))
        await db.execute(delete(ToplantiKatilimci))
        await db.execute(delete(Toplanti).where(Toplanti.site_no == 1))
        await db.commit()
        print("[i] Eski test toplantilari temizlendi\n")

        # 1) Yeni toplanti
        print("=" * 60)
        print("1) CREATE TOPLANTI")
        print("=" * 60)
        t1 = await toplanti_service.create_toplanti(
            db, site_no=1,
            baslik="2026 Yili Olagan Toplantisi",
            aciklama="Yillik faaliyet raporu ve butce gorusulecek.",
            toplanti_tarihi=now_utc_naive() + timedelta(days=7),
            yer="Site Toplanti Salonu",
            olusturan_no=11,
            katilimci_kullanicilar=[1, 4, 5, 11],
        )
        print(f"  Toplanti #{t1.toplanti_no}: {t1.baslik}")
        print(f"  Durum: {t1.durum}")

        # 2) Liste
        print()
        print("=" * 60)
        print("2) LISTE")
        print("=" * 60)
        liste = await toplanti_service.list_toplantilar(db, site_no=1)
        for t in liste:
            print(f"  [{t['toplanti_no']}] {t['baslik']}")
            print(f"      Durum: {t['durum']}, katilimci: {t['katilimci_sayisi']}, karar: {t['karar_sayisi']}")

        # 3) Detay
        print()
        print("=" * 60)
        print("3) DETAY")
        print("=" * 60)
        detay = await toplanti_service.get_toplanti(db, t1.toplanti_no, site_no=1)
        print(f"  Baslik: {detay['baslik']}")
        print(f"  Katilimcilar: {len(detay['katilimcilar'])}")
        for k in detay["katilimcilar"]:
            print(f"    [{k['katilim_no']}] {k['ad']} {k['soyad']} - katildi: {k['katildi_mi']}")

        # 4) Katilimci isaretle
        print()
        print("=" * 60)
        print("4) KATILIMCI ISARETLE")
        print("=" * 60)
        for k in detay["katilimcilar"][:3]:
            await toplanti_service.katilimci_guncelle(
                db, t1.toplanti_no, k["katilim_no"], site_no=1,
                katildi_mi=True,
            )
        print("  3 kisi katildi olarak isaretlendi")

        # 5) Karar ekle
        print()
        print("=" * 60)
        print("5) KARAR EKLE")
        print("=" * 60)
        k1 = await toplanti_service.karar_ekle(
            db, t1.toplanti_no, site_no=1,
            karar_metni="Asansor bakim sozlesmesi 2 yil uzatilacaktir.",
        )
        k2 = await toplanti_service.karar_ekle(
            db, t1.toplanti_no, site_no=1,
            karar_metni="Ortak alan elektrik faturalari icin otomatik odeme talimati verilecektir.",
        )
        print(f"  Karar #{k1.karar_no} ve #{k2.karar_no} eklendi")

        # 6) Durum degistir
        print()
        print("=" * 60)
        print("6) DURUM DEGISTIR (YAPILDI)")
        print("=" * 60)
        guncel = await toplanti_service.durum_degistir(
            db, t1.toplanti_no, site_no=1, yeni_durum="YAPILDI"
        )
        print(f"  Yeni durum: {guncel.durum}")

        # 7) Detay tekrar
        print()
        print("=" * 60)
        print("7) DETAY (guncel)")
        print("=" * 60)
        detay2 = await toplanti_service.get_toplanti(db, t1.toplanti_no, site_no=1)
        print(f"  Katilimci: {detay2['katilimci_sayisi']}, katilan: {detay2['katilan_sayisi']} (%{detay2['katilim_orani']})")
        print(f"  Karar sayisi: {detay2['karar_sayisi']}")

        # 8) Ozet
        print()
        print("=" * 60)
        print("8) OZET")
        print("=" * 60)
        ozet = await toplanti_service.get_ozet(db, site_no=1)
        for k, v in ozet.items():
            print(f"  {k:25s}: {v}")

        # 9) Sil
        print()
        print("=" * 60)
        print("9) SIL")
        print("=" * 60)
        await toplanti_service.delete_toplanti(db, t1.toplanti_no, site_no=1)
        print(f"  Toplanti #{t1.toplanti_no} silindi")

        try:
            await toplanti_service.get_toplanti(db, t1.toplanti_no, site_no=1)
            print("  [FAIL] Hala var!")
        except Exception:
            print("  [OK] Silindi dogrulandi (404)")

        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())