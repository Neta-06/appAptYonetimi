"""Demirbaş servisi doğrudan test."""
import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete
from app.db.session import AsyncSessionLocal
from app.models import Demirbas, DemirbasHareket
from app.services import demirbas_service


async def main():
    async with AsyncSessionLocal() as db:
        # Temizlik
        await db.execute(delete(DemirbasHareket))
        await db.execute(delete(Demirbas).where(Demirbas.site_no == 1))
        await db.commit()
        print("[i] Eski test demirbaslari temizlendi\n")

        # 1) Yeni demirbas
        print("=" * 60)
        print("1) CREATE DEMIRBAS")
        print("=" * 60)
        d1 = await demirbas_service.create_demirbas(
            db, site_no=1,
            ad="Asansor",
            kategori="TASIMA",
            adet=2,
            alis_fiyati=Decimal("800000.00"),
            alis_tarihi=date(2020, 5, 1),
            bulundugu_yer="Bloklar",
            durum="CALISIYOR",
            olusturan_no=11,
        )
        print(f"  Demirbas #{d1.demirbas_no}: {d1.ad} (adet={d1.adet}, durum={d1.durum})")

        d2 = await demirbas_service.create_demirbas(
            db, site_no=1,
            ad="Jenerator",
            kategori="ENERJI",
            adet=1,
            alis_fiyati=Decimal("350000.00"),
            bulundugu_yer="Bodrum",
            olusturan_no=11,
        )
        print(f"  Demirbas #{d2.demirbas_no}: {d2.ad}")

        # 2) Liste
        print()
        print("=" * 60)
        print("2) LISTE")
        print("=" * 60)
        liste = await demirbas_service.list_demirbaslar(db, site_no=1)
        for d in liste:
            print(f"  [{d['demirbas_no']}] {d['ad']:20s} adet={d['adet']} durum={d['durum']} deger={d['toplam_deger']}")

        # 3) Detay
        print()
        print("=" * 60)
        print("3) DETAY")
        print("=" * 60)
        detay = await demirbas_service.get_demirbas(db, d1.demirbas_no, site_no=1)
        print(f"  Ad: {detay['ad']}")
        print(f"  Adet: {detay['adet']}")
        print(f"  Toplam deger: {detay['toplam_deger']} TL")
        print(f"  Hareketler: {len(detay['hareketler'])}")

        # 4) Hareket ekle (BAKIM)
        print()
        print("=" * 60)
        print("4) HAREKET EKLE (BAKIM)")
        print("=" * 60)
        h = await demirbas_service.hareket_ekle(
            db, d1.demirbas_no, site_no=1,
            hareket_tipi="BAKIM",
            kullanici_no=3,
            aciklama="Aylik periyodik bakim",
            maliyet=Decimal("2500.00"),
        )
        print(f"  Hareket #{h.hareket_no}: {h.hareket_tipi}, maliyet={h.maliyet}")

        # İkinci bakım
        h2 = await demirbas_service.hareket_ekle(
            db, d1.demirbas_no, site_no=1,
            hareket_tipi="ONARIM",
            kullanici_no=3,
            aciklama="Motor kayisi degisimi",
            maliyet=Decimal("1800.00"),
        )
        print(f"  Hareket #{h2.hareket_no}: {h2.hareket_tipi}, maliyet={h2.maliyet}")

        # 5) Durum degistir (ARIZALI)
        print()
        print("=" * 60)
        print("5) DURUM DEGISTIR (ARIZALI)")
        print("=" * 60)
        d_guncel = await demirbas_service.durum_degistir(
            db, d2.demirbas_no, site_no=1,
            yeni_durum="ARIZALI",
            kullanici_no=11,
            aciklama="Motor calismyor",
        )
        print(f"  Yeni durum: {d_guncel.durum}")

        # 6) Detay tekrar (bakim maliyeti toplami)
        print()
        print("=" * 60)
        print("6) DETAY (bakim maliyeti)")
        print("=" * 60)
        detay2 = await demirbas_service.get_demirbas(db, d1.demirbas_no, site_no=1)
        print(f"  Toplam bakim maliyeti: {detay2['toplam_bakim_maliyeti']} TL")
        print(f"  Hareket sayisi: {len(detay2['hareketler'])}")

        # 7) Ozet
        print()
        print("=" * 60)
        print("7) OZET")
        print("=" * 60)
        ozet = await demirbas_service.get_ozet(db, site_no=1)
        print(f"  Toplam kalem: {ozet['toplam_kalem']}")
        print(f"  Toplam adet: {ozet['toplam_adet']}")
        print(f"  Calisiyor: {ozet['calisiyor']}, Arizali: {ozet['arizali']}, Hurda: {ozet['hurda']}")
        print(f"  Toplam deger: {ozet['toplam_deger']} TL")
        print(f"  Toplam bakim: {ozet['toplam_bakim_maliyeti']} TL")
        print(f"  Kategoriler:")
        for k in ozet["kategoriler"]:
            print(f"    {k['kategori']:12s} {k['kalem']} kalem, {k['adet']} adet, {k['deger']} TL")

        # 8) Guncelle
        print()
        print("=" * 60)
        print("8) GUNCELLE")
        print("=" * 60)
        d_upd = await demirbas_service.update_demirbas(
            db, d2.demirbas_no, site_no=1,
            bulundugu_yer="Yeni Bodrum",
            alis_fiyati=Decimal("360000.00"),
        )
        print(f"  Yeni yer: {d_upd.bulundugu_yer}, yeni fiyat: {d_upd.alis_fiyati}")

        # 9) Sil
        print()
        print("=" * 60)
        print("9) SIL")
        print("=" * 60)
        await demirbas_service.delete_demirbas(db, d2.demirbas_no, site_no=1)
        print(f"  Demirbas #{d2.demirbas_no} silindi")

        try:
            await demirbas_service.get_demirbas(db, d2.demirbas_no, site_no=1)
            print("  [FAIL] Hala var!")
        except Exception:
            print("  [OK] Silindi dogrulandi (404)")

        # Temizlik
        await db.execute(delete(DemirbasHareket))
        await db.execute(delete(Demirbas).where(Demirbas.site_no == 1))
        await db.commit()
        print()
        print("[DONE] Tum testler tamamlandi")


if __name__ == "__main__":
    asyncio.run(main())