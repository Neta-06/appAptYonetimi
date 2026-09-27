"""Gider servisi doğrudan test."""
import asyncio
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import AsyncSessionLocal
from app.services import gider_service


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("1) KATEGORILER")
        print("=" * 60)
        kategoriler = await gider_service.list_kategoriler(db)
        for k in kategoriler[:5]:
            print(f"  [{k['kategori_no']}] {k['ad']}")

        print()
        print("=" * 60)
        print("2) GIDER KALEMLERI (ilk 5)")
        print("=" * 60)
        kalemler = await gider_service.list_kalemler(db)
        for k in kalemler[:5]:
            print(f"  [{k['kalem_no']}] {k['kalem_adi']} ({k['kategori_adi']})")

        print()
        print("=" * 60)
        print("3) CARILER (site 1)")
        print("=" * 60)
        cariler = await gider_service.list_cariler(db, site_no=1)
        for c in cariler:
            print(f"  [{c['cari_no']}] {c['unvan']}")

        print()
        print("=" * 60)
        print("4) GIDER OZET (site 1)")
        print("=" * 60)
        ozet = await gider_service.get_genel_ozet(db, site_no=1)
        for k, v in ozet.items():
            print(f"  {k:20s}: {v}")

        print()
        print("=" * 60)
        print("5) GIDER LISTESI (site 1, ilk 5)")
        print("=" * 60)
        giderler = await gider_service.list_giderler(db, site_no=1, limit=5)
        for g in giderler:
            print(
                f"  [{g['gider_no']}] {g['gider_tarihi']} "
                f"{g['kategori_adi']}/{g['kalem_adi']} "
                f"-> {g['tutar']} TL (cari: {g['cari_unvan'] or '-'})"
            )

        print()
        print("=" * 60)
        print("6) KATEGORI OZET (site 1)")
        print("=" * 60)
        k_ozet = await gider_service.get_kategori_ozet(db, site_no=1)
        for k in k_ozet:
            print(
                f"  {k['kategori_adi']:25s} -> {k['toplam_tutar']:>10} TL "
                f"({k['yuzde']:5.2f}%) - {k['kayit_sayisi']} kayit"
            )

        print()
        print("=" * 60)
        print("7) AYLIK OZET (site 1)")
        print("=" * 60)
        aylik = await gider_service.get_aylik_ozet(db, site_no=1)
        for a in aylik:
            print(
                f"  {a['donem_yil']}/{a['donem_ay']:02d} -> "
                f"{a['toplam_tutar']} TL ({a['kayit_sayisi']} kayit)"
            )


if __name__ == "__main__":
    asyncio.run(main())